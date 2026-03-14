"""
GDELT Project - Global Database of Events, Language and Tone
Atualizado a cada 15 minutos. Sem registo necessário.
Usado para detectar sinais de conflito via cobertura de notícias geolocalizadas.
"""
import httpx
import structlog
from datetime import datetime, timedelta

log = structlog.get_logger()

GDELT_API = "https://api.gdeltproject.org/api/v2/geo/geo"

# Categorias de eventos relevantes para zonas de conflito
CONFLICT_THEMES = [
    "KILL", "ATTACK", "CONFLICT", "PROTEST", "EVACUATE",
    "ARMED_CONFLICT", "MILITARY", "EXPLOSION", "REFUGEE",
]

async def get_events_near(
    lat: float,
    lng: float,
    radius_km: float = 50,
    hours_back: int = 24,
) -> list[dict]:
    """
    Busca eventos GDELT próximos de uma localização.
    Retorna lista de eventos com score de relevância.
    """
    try:
        # GDELT GEO API — busca por tema + localização
        query_themes = " OR ".join(f"theme:{t}" for t in CONFLICT_THEMES)
        
        params = {
            "query": query_themes,
            "mode": "pointdata",
            "lat": lat,
            "lng": lng,
            "radius": f"{radius_km}km",
            "format": "json",
            "maxrecords": 50,
            "timespan": f"{hours_back}h",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(GDELT_API, params=params)
            res.raise_for_status()
            data = res.json()

        events = []
        for item in data.get("features", []):
            props = item.get("properties", {})
            geom  = item.get("geometry", {}).get("coordinates", [None, None])
            events.append({
                "title":      props.get("name", ""),
                "url":        props.get("url", ""),
                "tone":       float(props.get("tone", 0)),
                "date":       props.get("dateadded", ""),
                "lat":        geom[1] if len(geom) > 1 else lat,
                "lng":        geom[0] if len(geom) > 0 else lng,
                "source":     "GDELT",
            })

        log.info("gdelt_events_fetched", count=len(events), lat=lat, lng=lng)
        return events

    except Exception as e:
        log.error("gdelt_fetch_failed", error=str(e))
        return []


async def get_conflict_score(lat: float, lng: float, radius_km: float = 50) -> int:
    """
    Retorna score GDELT (0-2) baseado em eventos recentes.
    0 = sem eventos  |  1 = alguns eventos  |  2 = muitos/graves
    """
    events = await get_events_near(lat, lng, radius_km, hours_back=24)
    if not events:
        return 0
    # Tone negativo = notícia negativa (conflito, ataque, morte)
    negative = [e for e in events if e["tone"] < -5]
    if len(negative) >= 5:
        return 2
    if len(negative) >= 1 or len(events) >= 3:
        return 1
    return 0
