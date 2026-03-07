"""
ReliefWeb API v2 integration.
Fetches real humanitarian crisis reports and alerts.
"""
import httpx
import structlog

log = structlog.get_logger()

RELIEFWEB_URL = "https://api.reliefweb.int/v1"
APP_NAME = "SafePassage/1.0 (humanitarian-safety-platform)"

async def get_crisis_reports(country: str = None, limit: int = 10) -> list[dict]:
    """Fetch recent crisis reports from ReliefWeb."""
    try:
        payload = {
            "appname": APP_NAME,
            "limit": limit,
            "sort": ["date:desc"],
            "fields": {
                "include": ["title", "date", "country", "source", "url", "body-html", "status"]
            },
            "filter": {
                "operator": "AND",
                "conditions": [
                    {"field": "status", "value": "published"},
                ]
            }
        }
        if country:
            payload["filter"]["conditions"].append({
                "field": "country.name",
                "value": country,
                "operator": "OR"
            })

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(f"{RELIEFWEB_URL}/reports", json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("data", [])
    except Exception as e:
        log.error("reliefweb_fetch_failed", error=str(e))
        return []

async def get_disasters(country: str = None, limit: int = 10) -> list[dict]:
    """Fetch active disasters from ReliefWeb."""
    try:
        payload = {
            "appname": APP_NAME,
            "limit": limit,
            "sort": ["date:desc"],
            "fields": {
                "include": ["name", "date", "country", "type", "status", "url"]
            },
            "filter": {
                "field": "status",
                "value": ["current", "alert"],
            }
        }
        if country:
            payload["filter"] = {
                "operator": "AND",
                "conditions": [
                    {"field": "status", "value": ["current", "alert"]},
                    {"field": "country.name", "value": country},
                ]
            }

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(f"{RELIEFWEB_URL}/disasters", json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("data", [])
    except Exception as e:
        log.error("reliefweb_disasters_failed", error=str(e))
        return []
