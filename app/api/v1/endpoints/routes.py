from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.models import Route
from app.schemas.schemas import RouteResponse
from app.services.geo_service import get_safe_routes

router = APIRouter()

@router.get("/search", response_model=list[RouteResponse])
async def search_routes(origin_lat: float = Query(..., ge=-90, le=90), origin_lng: float = Query(..., ge=-180, le=180), zone_id: UUID | None = None, max_danger_score: float = Query(default=0.6, ge=0, le=1), requires_accessible: bool = False, requires_no_vehicle: bool = False, db: AsyncSession = Depends(get_db)):
    return await get_safe_routes(db, origin_lat, origin_lng, zone_id, max_danger_score, requires_accessible, requires_no_vehicle)

@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(route_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route
