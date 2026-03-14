# SafePassage — Danger Score Engine

## Overview

The danger score engine calculates a composite risk level for any geographic location by querying 4 independent intelligence sources simultaneously.

## Design Principles

**Conservative by design.** The engine requires multiple independent signals to reach HIGH or CRITICAL levels. A single source reporting activity is not enough to trigger a high alert. This prevents false positives that could cause unnecessary panic or dangerous decisions in the field.

**Transparent.** Every score response includes a full breakdown showing exactly how much each source contributed, allowing users and NGOs to evaluate the quality of the assessment.

**Resilient.** Each source is queried independently. If one source fails or times out, the others continue and a partial score is returned. A failure in one source never blocks the response.

## Score Breakdown

| Source | Max Points | Signal |
|---|---|---|
| NASA FIRMS | 3 | Satellite heat detections in radius (last 3 days) |
| ReliefWeb | 2 | Humanitarian reports for region |
| GDELT | 2 | Conflict-related news events (last 24h) |
| UCDP | 1 | Historical organised violence in area |

**Total maximum: 8 points**

## Risk Levels

| Score | Level | Meaning |
|---|---|---|
| 0–1 | LOW | No significant signals detected |
| 2–3 | MODERATE | Some activity, monitor situation |
| 4–6 | HIGH | Multiple signals, elevated risk |
| 7–8 | CRITICAL | Severe, immediate danger likely |

## FIRMS Scoring Detail

NASA FIRMS (Fire Information for Resource Management System) provides near-real-time satellite detections of thermal anomalies via VIIRS and MODIS sensors. In conflict zones, high-brightness anomalies often correspond to explosions, fires from strikes, or burning infrastructure.

| Detections in radius | Score |
|---|---|
| 0 | 0 |
| 1–2 | 1 |
| 3–9 | 2 |
| 10+ | 3 |

Radius for FIRMS queries: bounding box derived from `radius_km` parameter (~111km per degree).

## GDELT Scoring Detail

GDELT queries use conflict-related themes: `KILL`, `ATTACK`, `CONFLICT`, `PROTEST`, `EVACUATE`, `ARMED_CONFLICT`, `MILITARY`, `EXPLOSION`, `REFUGEE`. Tone score below -5 indicates strongly negative news.

| Signal | Score |
|---|---|
| No events | 0 |
| Events present OR 1+ negative tone | 1 |
| 5+ negative-tone events | 2 |

## Future Improvements

- Cache scores in Redis with 1h TTL to reduce API calls
- Add HDX/HAPI as a 5th source for humanitarian indicators
- Weighted scoring based on source recency
- Confidence interval based on source agreement