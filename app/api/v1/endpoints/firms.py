from fastapi import APIRouter, Query
from app.services.firms_service import get_hotspots, get_hotspots_by_bbox

router = APIRouter(tags=["NASA FIRMS"])

@router.get("/hotspots")
async def hotspots_by_country(
    country: str = Query(default="Ukraine"),
    days: int = Query(default=1, ge=1, le=7),
    source: str = Query(default="VIIRS_SNPP_NRT"),
):
    data = await get_hotspots(country=country, days=days, source=source)
    return {"count": len(data), "hotspots": data}

@router.get("/hotspots/bbox")
async def hotspots_by_bbox(
    west: float = Query(default=22.0),
    south: float = Query(default=44.0),
    east: float = Query(default=40.0),
    north: float = Query(default=52.0),
    days: int = Query(default=1, ge=1, le=7),
    source: str = Query(default="VIIRS_SNPP_NRT"),
):
    data = await get_hotspots_by_bbox(west, south, east, north, days=days, source=source)
    return {"count": len(data), "hotspots": data}
