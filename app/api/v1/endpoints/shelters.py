from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_ngo_or_admin
from app.db.database import get_db
from app.models.models import Shelter, ShelterStatus, ShelterType, User
from app.schemas.schemas import ShelterCreateRequest, ShelterResponse, ShelterUpdateRequest
from app.services.geo_service import get_nearby_shelters

router = APIRouter()

@router.get("/nearby", response_model=list[ShelterResponse])
async def nearby_shelters(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180), radius_km: float = Query(default=30.0, ge=1, le=200), requires_medical: bool = False, requires_food: bool = False, requires_water: bool = False, open_only: bool = True, db: AsyncSession = Depends(get_db)):
    return await get_nearby_shelters(db, lat, lng, radius_km, requires_medical=requires_medical, requires_food=requires_food, requires_water=requires_water, open_only=open_only)

@router.post("/", response_model=ShelterResponse, status_code=201)
async def create_shelter(body: ShelterCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_ngo_or_admin)):
    try:
        shelter_type = ShelterType(body.shelter_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid shelter_type: {body.shelter_type}")
    shelter = Shelter(zone_id=body.zone_id, name=body.name, shelter_type=shelter_type, status=ShelterStatus.OPEN, lat=body.lat, lng=body.lng, address=body.address, capacity_total=body.capacity_total, has_medical=body.has_medical, has_food=body.has_food, has_water=body.has_water, has_power=body.has_power, has_comms=body.has_comms, accepts_families=body.accepts_families, accepts_injured=body.accepts_injured, contact_phone=body.contact_phone, operating_org=body.operating_org, verified=True, last_verified_at=datetime.now(timezone.utc))
    db.add(shelter)
    await db.flush()
    return shelter

@router.patch("/{shelter_id}", response_model=ShelterResponse)
async def update_shelter(shelter_id: UUID, body: ShelterUpdateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_ngo_or_admin)):
    result = await db.execute(select(Shelter).where(Shelter.id == shelter_id))
    shelter = result.scalar_one_or_none()
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(shelter, field, ShelterStatus(value) if field == "status" else value)
    db.add(shelter)
    return shelter

@router.get("/{shelter_id}", response_model=ShelterResponse)
async def get_shelter(shelter_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shelter).where(Shelter.id == shelter_id))
    shelter = result.scalar_one_or_none()
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    return shelter
