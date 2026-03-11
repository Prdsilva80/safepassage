"""
NASA FIRMS - Fire Information for Resource Management System
Detects heat anomalies via satellite (MODIS/VIIRS).
In conflict zones, high brightness values often indicate explosions/fires.
"""
import httpx
import csv
import io
import structlog
from app.core.config import settings

log = structlog.get_logger()

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api"

# ISO country codes for supported conflict zones
COUNTRY_CODES = {
    "Ukraine": "UKR",
    "Gaza": "PSE",
    "Sudan": "SDN",
    "Syria": "SYR",
    "Yemen": "YEM",
    "Myanmar": "MMR",
    "Somalia": "SOM",
    "Ethiopia": "ETH",
    "Mali": "MLI",
    "Niger": "NER",
}

async def get_hotspots_by_country(
    country: str = "Ukraine",
    days: int = 1,
    source: str = "VIIRS_SNPP_NRT",
) -> list[dict]:
    """
    Fetch heat/fire hotspots for a country.
    sources: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, MODIS_NRT
    days: 1-10
    """
    if not settings.firms_map_key:
        log.warning("firms_map_key_missing")
        return []

    iso = COUNTRY_CODES.get(country, country[:3].upper())

    try:
        url = f"{FIRMS_BASE}/country/csv/{settings.firms_map_key}/{source}/{iso}/{days}"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(url)
            res.raise_for_status()

        reader = csv.DictReader(io.StringIO(res.text))
        hotspots = []
        for row in reader:
            try:
                hotspots.append({
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "brightness": float(row.get("bright_ti4") or row.get("brightness") or 0),
                    "frp": float(row.get("frp") or 0),  # Fire Radiative Power (MW)
                    "confidence": row.get("confidence", "n"),
                    "datetime": f"{row.get('acq_date')} {row.get('acq_time', '')}",
                    "satellite": row.get("satellite", source),
                    "daynight": row.get("daynight", ""),
                })
            except (ValueError, KeyError):
                continue

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
    """Fetch hotspots for a bounding box (useful for map viewport)."""
    if not settings.firms_map_key:
        return []
    try:
        area = f"{west},{south},{east},{north}"
        url = f"{FIRMS_BASE}/area/csv/{settings.firms_map_key}/{source}/{area}/{days}"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(url)
            res.raise_for_status()

        reader = csv.DictReader(io.StringIO(res.text))
        hotspots = []
        for row in reader:
            try:
                hotspots.append({
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "brightness": float(row.get("bright_ti4") or row.get("brightness") or 0),
                    "frp": float(row.get("frp") or 0),
                    "confidence": row.get("confidence", "n"),
                    "datetime": f"{row.get('acq_date')} {row.get('acq_time', '')}",
                    "satellite": row.get("satellite", source),
                    "daynight": row.get("daynight", ""),
                })
            except (ValueError, KeyError):
                continue

        return hotspots
    except Exception as e:
        log.error("firms_bbox_failed", error=str(e))
        return []
