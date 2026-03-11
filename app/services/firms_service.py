"""
NASA FIRMS - Fire Information for Resource Management System
Detects heat anomalies via satellite (VIIRS/MODIS).
In conflict zones, high brightness values indicate explosions/fires.
"""
import httpx
import csv
import io
import structlog
from app.core.config import settings

log = structlog.get_logger()
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api"

# Bounding boxes para zonas de conflito [west, south, east, north]
CONFLICT_ZONES = {
    "Ukraine":  (22.0, 44.0, 40.0, 52.0),
    "Gaza":     (34.2, 31.2, 34.6, 31.6),
    "Sudan":    (21.0, 8.0,  38.0, 22.0),
    "Syria":    (35.5, 32.5, 42.5, 37.5),
    "Yemen":    (42.5, 12.0, 54.0, 19.0),
    "Myanmar":  (92.0, 16.0, 101.0, 28.0),
    "Somalia":  (40.0, -2.0, 51.0, 12.0),
    "Ethiopia": (33.0, 3.0,  48.0, 15.0),
}

def _parse_csv(text: str, source: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    hotspots = []
    for row in reader:
        try:
            hotspots.append({
                "latitude":   float(row["latitude"]),
                "longitude":  float(row["longitude"]),
                "brightness": float(row.get("bright_ti4") or row.get("brightness") or 0),
                "frp":        float(row.get("frp") or 0),
                "confidence": row.get("confidence", "n"),
                "datetime":   f"{row.get('acq_date')} {row.get('acq_time', '')}".strip(),
                "satellite":  row.get("satellite", ""),
                "daynight":   row.get("daynight", ""),
            })
        except (ValueError, KeyError):
            continue
    return hotspots

async def get_hotspots(
    country: str = "Ukraine",
    days: int = 1,
    source: str = "VIIRS_SNPP_NRT",
) -> list[dict]:
    key = settings.firms_map_key
    if not key:
        log.warning("firms_map_key_missing")
        return []

    bbox = CONFLICT_ZONES.get(country)
    if not bbox:
        log.warning("firms_country_not_supported", country=country)
        return []

    west, south, east, north = bbox
    try:
        url = f"{FIRMS_BASE}/area/csv/{key}/{source}/{west},{south},{east},{north}/{days}"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(url)
            res.raise_for_status()
        hotspots = _parse_csv(res.text, source)
        log.info("firms_hotspots_fetched", country=country, count=len(hotspots))
        return hotspots
    except Exception as e:
        log.error("firms_fetch_failed", country=country, error=str(e))
        return []

async def get_hotspots_by_bbox(
    west: float, south: float, east: float, north: float,
    days: int = 1,
    source: str = "VIIRS_SNPP_NRT",
) -> list[dict]:
    """Para usar com o viewport do mapa."""
    key = settings.firms_map_key
    if not key:
        return []
    try:
        url = f"{FIRMS_BASE}/area/csv/{key}/{source}/{west},{south},{east},{north}/{days}"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(url)
            res.raise_for_status()
        return _parse_csv(res.text, source)
    except Exception as e:
        log.error("firms_bbox_failed", error=str(e))
        return []
