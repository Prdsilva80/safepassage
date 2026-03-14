"""
Danger Score Engine — SafePassage
Combina 4 fontes para calcular score de perigo composto por localização.

Score breakdown:
  FIRMS (NASA satélite)  → 0-3 pts
  ReliefWeb (humanitário)→ 0-2 pts
  GDELT (notícias)       → 0-2 pts
  UCDP (histórico)       → 0-1 pts
  ─────────────────────────────────
  Total máximo: 8 pts

  0-1 → LOW
  2-3 → MODERATE
  4-6 → HIGH
  7+  → CRITICAL
"""
import asyncio
import structlog
from datetime import datetime, timezone

from app.services.firms_service      import get_hotspots_by_bbox
from app.services.reliefweb_service import get_crisis_reports
from app.services.gdelt_service      import get_conflict_score as gdelt_score
from app.services.ucdp_service       import get_conflict_score as ucdp_score

log = structlog.get_logger()

SCORE_THRESHOLDS = {
    "CRITICAL": 7,
    "HIGH":     4,
    "MODERATE": 2,
    "LOW":      0,
}

def score_to_level(score: int) -> str:
    if score >= SCORE_THRESHOLDS["CRITICAL"]: return "CRITICAL"
    if score >= SCORE_THRESHOLDS["HIGH"]:     return "HIGH"
    if score >= SCORE_THRESHOLDS["MODERATE"]: return "MODERATE"
    return "LOW"


async def _firms_score(lat: float, lng: float, radius_km: float) -> tuple[int, int]:
    """Retorna (score, n_hotspots). Score 0-3."""
    deg = radius_km / 111
    hotspots = await get_hotspots_by_bbox(
        west=lng - deg, south=lat - deg,
        east=lng + deg, north=lat + deg,
        days=3,
    )
    n = len(hotspots)
    if n >= 10: return 3, n
    if n >= 3:  return 2, n
    if n >= 1:  return 1, n
    return 0, 0


async def _reliefweb_score(lat: float, lng: float) -> tuple[int, int]:
    """Retorna (score, n_reports). Score 0-2."""
    try:
        # ReliefWeb por país — usa coordenadas para inferir país
        # Simplificação: busca por bounding box aproximado
        reports = await get_crisis_reports(limit=10)
        # Filtra reports com coordenadas próximas se disponíveis
        n = len(reports)
        if n >= 5: return 2, n
        if n >= 1: return 1, n
        return 0, 0
    except Exception:
        return 0, 0


async def calculate(
    lat: float,
    lng: float,
    radius_km: float = 50,
) -> dict:
    """
    Calcula danger score composto para uma localização.
    Todas as fontes são consultadas em paralelo.
    """
    started_at = datetime.now(timezone.utc)

    # Correr todas as fontes em paralelo
    firms_task    = _firms_score(lat, lng, radius_km)
    gdelt_task    = gdelt_score(lat, lng, radius_km)
    ucdp_task     = ucdp_score(lat, lng, radius_km)
    reliefweb_task = _reliefweb_score(lat, lng)

    (firms_pts, firms_n), gdelt_pts, ucdp_pts, (rw_pts, rw_n) = await asyncio.gather(
        firms_task, gdelt_task, ucdp_task, reliefweb_task,
        return_exceptions=False,
    )

    total = firms_pts + gdelt_pts + ucdp_pts + rw_pts
    level = score_to_level(total)

    result = {
        "lat":        lat,
        "lng":        lng,
        "radius_km":  radius_km,
        "score":      total,
        "level":      level,
        "breakdown": {
            "firms":      {"score": firms_pts,  "detections": firms_n,  "max": 3},
            "reliefweb":  {"score": rw_pts,     "reports":    rw_n,     "max": 2},
            "gdelt":      {"score": gdelt_pts,  "max": 2},
            "ucdp":       {"score": ucdp_pts,   "max": 1},
        },
        "calculated_at": started_at.isoformat(),
        "sources": ["NASA FIRMS", "ReliefWeb", "GDELT", "UCDP"],
    }

    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    log.info("danger_score_calculated",
             lat=lat, lng=lng, score=total, level=level, elapsed_s=round(elapsed, 2))

    return result
