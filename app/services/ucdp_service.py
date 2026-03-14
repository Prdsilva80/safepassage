"""
UCDP - Uppsala Conflict Data Program
GED (Georeferenced Event Dataset) v25.1
API REST oficial, sem registo necessário.
Usado como camada de baseline histórica de violência organizada.
"""
import httpx
import structlog

log = structlog.get_logger()

UCDP_API = "https://ucdpapi.pcr.uu.se/api"

async def get_events_near(
    lat: float,
    lng: float,
    radius_km: float = 100,
    year_from: int = 2020,
) -> list[dict]:
    """
    Busca eventos UCDP GED próximos de uma localização.
    UCDP não tem filtro geográfico directo — filtramos por país/região.
    """
    try:
        params = {
            "version":   "25.1",
            "pagesize":  100,
            "page":      1,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            # Busca eventos próximos via bounding box aproximado
            bbox_deg = radius_km / 111  # ~111km por grau
            params["latitude"]  = f"{lat - bbox_deg}:{lat + bbox_deg}"
            params["longitude"] = f"{lng - bbox_deg}:{lng + bbox_deg}"
            params["year"]      = f"{year_from}:2025"

            res = await client.get(f"{UCDP_API}/gedevents", params=params)
            res.raise_for_status()
            data = res.json()

        events = []
        for item in data.get("Result", []):
            events.append({
                "id":          item.get("id", ""),
                "date":        item.get("date_start", ""),
                "type":        item.get("type_of_violence", 0),
                "deaths":      int(item.get("best", 0) or 0),
                "description": item.get("source_article", ""),
                "lat":         float(item.get("latitude", lat)),
                "lng":         float(item.get("longitude", lng)),
                "country":     item.get("country", ""),
                "source":      "UCDP",
            })

        log.info("ucdp_events_fetched", count=len(events), lat=lat, lng=lng)
        return events

    except Exception as e:
        log.error("ucdp_fetch_failed", error=str(e))
        return []


async def get_conflict_score(lat: float, lng: float, radius_km: float = 100) -> int:
    """
    Retorna score UCDP (0-1) baseado em histórico de violência organizada.
    0 = sem histórico  |  1 = histórico presente
    """
    events = await get_events_near(lat, lng, radius_km)
    if not events:
        return 0
    total_deaths = sum(e["deaths"] for e in events)
    if total_deaths > 0 or len(events) >= 3:
        return 1
    return 0
