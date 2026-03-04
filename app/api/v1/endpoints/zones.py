from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_admin_user
from app.db.database import get_db
from app.models.models import Zone, DangerLevel, User
from app.schemas.schemas import ZoneCreateRequest, ZoneResponse
from app.services.geo_service import calculate_zone_danger_score, danger_score_to_level

router = APIRouter()

@router.get("/", response_model=list[ZoneResponse])
async def list_zones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone).where(Zone.active_conflict == True))
    return result.scalars().all()

@router.post("/", response_model=ZoneResponse, status_code=201)
async def create_zone(body: ZoneCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_admin_user)):
    zone = Zone(**body.model_dump(), danger_level=DangerLevel.MEDIUM, danger_score=0.5)
    db.add(zone)
    await db.flush()
    return zone

@router.post("/{zone_id}/recalculate-danger", response_model=ZoneResponse)
async def recalculate_danger(zone_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_admin_user)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    score = await calculate_zone_danger_score(db, zone_id)
    zone.danger_score = score
    zone.danger_level = danger_score_to_level(score)
    db.add(zone)
    return zone

@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone
