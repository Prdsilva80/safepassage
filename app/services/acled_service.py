"""
ACLED API integration.
Provides real conflict event data with coordinates for map display.
Token expires every 24h — stored in .env and refreshed automatically.
"""
import httpx
import structlog
from app.core.config import settings

log = structlog.get_logger()

ACLED_URL = "https://acleddata.com/api/acled/read"

async def get_conflict_events(
    country: str = None,
    limit: int = 20,
    days_back: int = 30,
) -> list[dict]:
    """Fetch recent conflict events from ACLED."""
    if not settings.acled_token:
        log.warning("acled_token_missing")
        return []
    try:
        params = {
            "limit": limit,
            "_format": "json",
            "fields": "event_id_cnty|event_date|event_type|sub_event_type|location|country|latitude|longitude|fatalities|actor1|actor2|notes",
        }
        if country:
            params["country"] = country

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(
                ACLED_URL,
                params=params,
                headers={"Authorization": f"Bearer {settings.acled_token}"},
            )
            res.raise_for_status()
            data = res.json()
            if data.get("status") == 200:
                return data.get("data", [])
            log.error("acled_error", response=data)
            return []
    except Exception as e:
        log.error("acled_fetch_failed", error=str(e))
        return []
