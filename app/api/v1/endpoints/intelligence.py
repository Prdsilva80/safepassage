from fastapi import APIRouter, Query
from app.services.reliefweb_service import get_crisis_reports, get_disasters

router = APIRouter()

@router.get("/reports")
async def humanitarian_reports(
    country: str | None = Query(None, description="Filter by country name"),
    limit: int = Query(10, ge=1, le=50),
):
    """Fetch real humanitarian crisis reports from ReliefWeb."""
    reports = await get_crisis_reports(country=country, limit=limit)
    return {
        "source": "ReliefWeb API v2 (OCHA)",
        "count": len(reports),
        "data": reports,
    }

@router.get("/disasters")
async def active_disasters(
    country: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Fetch active disasters and alerts from ReliefWeb."""
    disasters = await get_disasters(country=country, limit=limit)
    return {
        "source": "ReliefWeb API v2 (OCHA)",
        "count": len(disasters),
        "data": disasters,
    }
