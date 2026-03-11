import httpx
import structlog

log = structlog.get_logger()

RELIEFWEB_URL = "https://api.reliefweb.int/v2"
APP_NAME = "PRoberto-SafePassagehumanitariansafety-sp80"

async def get_crisis_reports(country: str = None, limit: int = 10) -> list[dict]:
    try:
        payload = {
            "limit": limit,
            "sort": ["date:desc"],
            "fields": {
                "include": ["title", "date", "country", "source", "url", "status"]
            }
        }
        if country:
            payload["filter"] = {
                "field": "country.name",
                "value": country
            }

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                f"{RELIEFWEB_URL}/reports?appname={APP_NAME}",
                json=payload
            )
            res.raise_for_status()
            return res.json().get("data", [])
    except Exception as e:
        log.error("reliefweb_fetch_failed", error=str(e))
        return []

async def get_disasters(country: str = None, limit: int = 10) -> list[dict]:
    try:
        payload = {
            "limit": limit,
            "sort": ["date:desc"],
            "fields": {
                "include": ["name", "date", "country", "type", "status", "url"]
            },
            "filter": {
                "field": "status",
                "value": ["current", "alert"]
            }
        }
        if country:
            payload["filter"] = {
                "operator": "AND",
                "conditions": [
                    {"field": "status", "value": ["current", "alert"]},
                    {"field": "country.name", "value": country}
                ]
            }

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                f"{RELIEFWEB_URL}/disasters?appname={APP_NAME}",
                json=payload
            )
            res.raise_for_status()
            return res.json().get("data", [])
    except Exception as e:
        log.error("reliefweb_disasters_failed", error=str(e))
        return []
