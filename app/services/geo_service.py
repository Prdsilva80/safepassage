"""
SafePassage — Geo Service
Haversine distance, bounding box queries, danger score aggregation.
"""
import math
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DangerLevel, Report, Route, Shelter, ShelterStatus

logger = structlog.get_logger(__name__)

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine formula — great-circle distance in km."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lng, max_lng) for a circle bounding box."""
    delta_lat = math.degrees(radius_km / EARTH_RADIUS_KM)
    delta_lng = math.degrees(radius_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat))))
    return (
        lat - delta_lat,
        lat + delta_lat,
        lng - delta_lng,
        lng + delta_lng,
    )


def danger_score_to_level(score: float) -> DangerLevel:
    """Convert 0-1 danger score to enum level."""
    if score >= 0.85:
        return DangerLevel.CRITICAL
    if score >= 0.65:
        return DangerLevel.HIGH
    if score >= 0.40:
        return DangerLevel.MEDIUM
    if score >= 0.20:
        return DangerLevel.LOW
    return DangerLevel.SAFE


def calculate_credibility_score(confirmations: int, contradictions: int) -> float:
    """
    Wilson score interval for credibility.
    More confirmations + fewer contradictions = higher score.
    """
    total = confirmations + contradictions
    if total == 0:
        return 0.5  # Unknown
    proportion = confirmations / total
    z = 1.96  # 95% confidence
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = (z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))) / denominator
    return max(0.0, min(1.0, centre - margin))


async def get_nearby_reports(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_km: float,
    hours_back: int = 24,
    danger_levels: list[str] | None = None,
    report_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch active reports within radius, sorted by recency + danger."""
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    stmt = select(Report).where(
        and_(
            Report.is_active == True,  # noqa: E712
            Report.created_at >= cutoff,
            Report.lat >= min_lat,
            Report.lat <= max_lat,
            Report.lng >= min_lng,
            Report.lng <= max_lng,
        )
    )

    if danger_levels:
        stmt = stmt.where(Report.danger_level.in_(danger_levels))  # type: ignore
    if report_types:
        stmt = stmt.where(Report.report_type.in_(report_types))  # type: ignore

    result = await db.execute(stmt)
    reports = result.scalars().all()

    # Filter by exact haversine distance + enrich with distance
    enriched = []
    for r in reports:
        dist = haversine_km(lat, lng, r.lat, r.lng)
        if dist <= radius_km:
            d = r.to_dict()
            d["distance_km"] = round(dist, 3)
            enriched.append(d)

    # Sort: critical first, then by recency
    danger_order = {
        "critical": 0, "high": 1, "medium": 2, "low": 3, "safe": 4
    }
    enriched.sort(key=lambda x: (
        danger_order.get(x["danger_level"], 5),
        -(x["created_at"].timestamp() if isinstance(x["created_at"], datetime) else 0)
    ))

    return enriched


async def get_nearby_shelters(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_km: float,
    shelter_types: list[str] | None = None,
    requires_medical: bool = False,
    requires_food: bool = False,
    requires_water: bool = False,
    open_only: bool = True,
) -> list[dict[str, Any]]:
    """Fetch shelters within radius sorted by distance."""
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)

    stmt = select(Shelter).where(
        and_(
            Shelter.lat >= min_lat,
            Shelter.lat <= max_lat,
            Shelter.lng >= min_lng,
            Shelter.lng <= max_lng,
        )
    )

    if open_only:
        stmt = stmt.where(Shelter.status != ShelterStatus.CLOSED)
    if shelter_types:
        stmt = stmt.where(Shelter.shelter_type.in_(shelter_types))  # type: ignore
    if requires_medical:
        stmt = stmt.where(Shelter.has_medical == True)  # noqa: E712
    if requires_food:
        stmt = stmt.where(Shelter.has_food == True)  # noqa: E712
    if requires_water:
        stmt = stmt.where(Shelter.has_water == True)  # noqa: E712

    result = await db.execute(stmt)
    shelters = result.scalars().all()

    enriched = []
    for s in shelters:
        dist = haversine_km(lat, lng, s.lat, s.lng)
        if dist <= radius_km:
            d = s.to_dict()
            d["distance_km"] = round(dist, 3)
            enriched.append(d)

    enriched.sort(key=lambda x: x["distance_km"])
    return enriched


async def get_safe_routes(
    db: AsyncSession,
    origin_lat: float,
    origin_lng: float,
    zone_id: UUID | None = None,
    max_danger_score: float = 0.6,
    requires_accessible: bool = False,
    requires_no_vehicle: bool = False,
) -> list[dict[str, Any]]:
    """Fetch active routes sorted by safety (lowest danger first)."""
    stmt = select(Route).where(
        and_(
            Route.is_active == True,  # noqa: E712
            Route.danger_score <= max_danger_score,
        )
    )

    if zone_id:
        stmt = stmt.where(Route.zone_id == zone_id)
    if requires_accessible:
        stmt = stmt.where(Route.accessible_for_disabled == True)  # noqa: E712
    if requires_no_vehicle:
        stmt = stmt.where(Route.requires_vehicle == False)  # noqa: E712

    result = await db.execute(stmt)
    routes = result.scalars().all()

    enriched = []
    for r in routes:
        dist_to_origin = haversine_km(origin_lat, origin_lng, r.origin_lat, r.origin_lng)
        d = r.to_dict()
        d["distance_to_origin_km"] = round(dist_to_origin, 3)
        enriched.append(d)

    # Sort: lowest danger first, then closest origin
    enriched.sort(key=lambda x: (x["danger_score"], x["distance_to_origin_km"]))
    return enriched


async def calculate_zone_danger_score(
    db: AsyncSession,
    zone_id: UUID,
) -> float:
    """
    Recalculate danger score for a zone based on recent reports.
    Weighted by: recency, danger level, credibility.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    stmt = select(Report).where(
        and_(
            Report.zone_id == zone_id,
            Report.is_active == True,  # noqa: E712
            Report.created_at >= cutoff,
        )
    )
    result = await db.execute(stmt)
    reports = result.scalars().all()

    if not reports:
        return 0.3  # Default: uncertain

    danger_weights = {
        "critical": 1.0,
        "high": 0.75,
        "medium": 0.5,
        "low": 0.25,
        "safe": 0.0,
    }

    now = datetime.now(timezone.utc)
    total_weight = 0.0
    weighted_sum = 0.0

    for r in reports:
        age_hours = (now - r.created_at).total_seconds() / 3600
        recency_weight = math.exp(-age_hours / 12)  # Decay over 12 hours
        danger_w = danger_weights.get(r.danger_level.value if hasattr(r.danger_level, 'value') else str(r.danger_level), 0.5)
        credibility_w = r.credibility_score

        weight = recency_weight * credibility_w
        weighted_sum += danger_w * weight
        total_weight += weight

    if total_weight == 0:
        return 0.3

    score = weighted_sum / total_weight
    logger.info("zone_danger_score_calculated", zone_id=str(zone_id), score=round(score, 3), report_count=len(reports))
    return round(score, 4)