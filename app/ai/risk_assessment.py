"""
SafePassage — AI Risk Assessment Service
Uses Anthropic Claude to generate personalised evacuation plans.
Includes retry logic, fallback, and structured output parsing.
"""
from datetime import datetime, timezone
from uuid import UUID

import anthropic
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.schemas.schemas import RiskAssessmentRequest, RiskAssessmentResponse

logger = structlog.get_logger(__name__)

# Lazy client — initialised once
_client: anthropic.AsyncAnthropic | None = None


def get_ai_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


RISK_SYSTEM_PROMPT = """You are a humanitarian AI assistant embedded in the SafePassage platform, 
used by civilians in active war zones. Your role is to provide clear, calm, and actionable 
safety guidance that can save lives.

RULES:
- Be concise and direct. People may be in immediate danger.
- Never cause panic. Use clear, calm language.
- Always prioritise immediate physical safety over documentation.
- Respond in the SAME LANGUAGE as the user request (detect from additional_context if provided).
- Structure your response EXACTLY as JSON matching the schema provided.
- If you cannot determine safe options, say so clearly and direct to international emergency contacts.

CONTEXT: You have access to real-time danger data for the user's area.
"""

RISK_ASSESSMENT_SCHEMA = """
Respond ONLY with a JSON object with these exact fields:
{
  "risk_level": "critical|high|medium|low|safe",
  "risk_score": <float 0.0-1.0>,
  "summary": "<2-3 sentence situation summary in user's language>",
  "evacuation_plan": "<step-by-step evacuation plan, numbered, clear>",
  "immediate_actions": ["<action 1>", "<action 2>", ...],
  "avoid_areas": ["<area/direction 1>", ...],
  "ai_confidence": <float 0.0-1.0>
}
"""


def _build_assessment_prompt(
    request: RiskAssessmentRequest,
    nearby_reports_summary: str,
    nearby_shelters_summary: str,
    zone_danger_score: float | None,
) -> str:
    profile_parts = [
        f"Group size: {request.group_size} person(s)",
    ]
    if request.has_children:
        profile_parts.append("Includes children")
    if request.has_elderly:
        profile_parts.append("Includes elderly")
    if request.mobility_impaired:
        profile_parts.append("⚠️ Mobility impaired — cannot walk long distances")
    if request.needs_medical_attention:
        profile_parts.append("⚠️ Requires medical attention urgently")
    if request.has_vehicle:
        profile_parts.append("Has vehicle available")
    else:
        profile_parts.append("No vehicle — on foot only")

    prompt = f"""EMERGENCY RISK ASSESSMENT REQUEST

Location: {request.lat:.4f}°, {request.lng:.4f}°
Language preference: {request.language}

PERSON/GROUP PROFILE:
{chr(10).join(f'- {p}' for p in profile_parts)}

ZONE DANGER SCORE: {f'{zone_danger_score:.2f}/1.00' if zone_danger_score is not None else 'Unknown'}

RECENT REPORTS IN AREA (last 24h):
{nearby_reports_summary or 'No reports available for this area.'}

NEARBY SHELTERS:
{nearby_shelters_summary or 'No shelter data available for this area.'}

ADDITIONAL CONTEXT FROM USER:
{request.additional_context or 'None provided.'}

Based on all available data, provide a personalised risk assessment and evacuation plan.

{RISK_ASSESSMENT_SCHEMA}
"""
    return prompt


@retry(
    retry=retry_if_exception_type((anthropic.APITimeoutError, anthropic.APIConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def _call_claude(prompt: str, language: str) -> str:
    """Call Claude API with retry on transient errors."""
    client = get_ai_client()
    message = await client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=settings.AI_MAX_TOKENS,
        system=RISK_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text  # type: ignore


def _parse_ai_response(raw: str) -> dict:  # type: ignore
    """Extract JSON from Claude response, stripping markdown fences if present."""
    import json
    import re

    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

    # Find the JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in AI response: {cleaned[:200]}")

    return json.loads(match.group())


def _fallback_assessment(request: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """Return a safe fallback when AI is unavailable."""
    logger.warning("ai_risk_assessment_fallback_used", lat=request.lat, lng=request.lng)
    return RiskAssessmentResponse(
        risk_level="high",
        risk_score=0.7,
        summary=(
            "AI assessment temporarily unavailable. "
            "Based on your location, treat situation as high risk until confirmed otherwise."
        ),
        evacuation_plan=(
            "1. Stay indoors if currently safe.\n"
            "2. Contact local emergency services or UNHCR (+41 22 739 8111).\n"
            "3. Use the shelter finder to locate the nearest verified safe location.\n"
            "4. Travel only during daylight hours if possible.\n"
            "5. Inform your emergency contact of your location."
        ),
        immediate_actions=[
            "Stay away from windows and exterior walls",
            "Keep phone charged and emergency contacts ready",
            "Check the SafePassage map for nearby shelters",
            "If moving, do so quickly and stay low",
        ],
        avoid_areas=["Unverified routes", "Areas with recent reports"],
        recommended_shelter_id=None,
        recommended_route_id=None,
        ai_confidence=0.0,
        generated_at=datetime.now(timezone.utc),
    )


async def assess_risk(
    request: RiskAssessmentRequest,
    nearby_reports: list[dict],  # type: ignore
    nearby_shelters: list[dict],  # type: ignore
    zone_danger_score: float | None,
    best_shelter_id: UUID | None = None,
    best_route_id: UUID | None = None,
) -> RiskAssessmentResponse:
    """
    Main entry point: generate a personalised AI risk assessment.
    Falls back gracefully if AI is unavailable.
    """
    # Build human-readable summaries for the AI
    if nearby_reports:
        report_lines = []
        for r in nearby_reports[:10]:  # Cap at 10 most relevant
            report_lines.append(
                f"- [{r.get('danger_level', '?').upper()}] "
                f"{r.get('report_type', '?')} — "
                f"{r.get('description') or r.get('title') or 'No details'} "
                f"({r.get('distance_km', '?')}km away, "
                f"{r.get('confirmations', 0)} confirmations)"
            )
        reports_summary = "\n".join(report_lines)
    else:
        reports_summary = "No recent reports in this area."

    if nearby_shelters:
        shelter_lines = []
        for s in nearby_shelters[:5]:
            services = ", ".join(filter(None, [
                "medical" if s.get("has_medical") else None,
                "food" if s.get("has_food") else None,
                "water" if s.get("has_water") else None,
            ])) or "basic"
            shelter_lines.append(
                f"- {s.get('name')} ({s.get('shelter_type')}) — "
                f"{s.get('distance_km')}km — "
                f"Status: {s.get('status')} — "
                f"Services: {services} — "
                f"Capacity: {s.get('capacity_current', '?')}/{s.get('capacity_total', '?')}"
            )
        shelters_summary = "\n".join(shelter_lines)
    else:
        shelters_summary = "No shelter data available."

    prompt = _build_assessment_prompt(
        request, reports_summary, shelters_summary, zone_danger_score
    )

    try:
        raw_response = await _call_claude(prompt, request.language)
        parsed = _parse_ai_response(raw_response)

        return RiskAssessmentResponse(
            risk_level=parsed.get("risk_level", "high"),
            risk_score=float(parsed.get("risk_score", 0.7)),
            summary=parsed.get("summary", "Assessment generated."),
            evacuation_plan=parsed.get("evacuation_plan", ""),
            immediate_actions=parsed.get("immediate_actions", []),
            avoid_areas=parsed.get("avoid_areas", []),
            recommended_shelter_id=best_shelter_id,
            recommended_route_id=best_route_id,
            ai_confidence=float(parsed.get("ai_confidence", 0.8)),
            generated_at=datetime.now(timezone.utc),
        )

    except anthropic.AuthenticationError:
        logger.error("ai_authentication_error")
        return _fallback_assessment(request)
    except anthropic.RateLimitError:
        logger.warning("ai_rate_limit_hit")
        return _fallback_assessment(request)
    except Exception as exc:
        logger.error("ai_assessment_failed", error=str(exc))
        return _fallback_assessment(request)