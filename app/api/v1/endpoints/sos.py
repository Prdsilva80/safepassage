from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user, get_ngo_or_admin
from app.db.database import get_db
from app.models.models import SOSEvent, SOSStatus, User
from app.schemas.schemas import SOSCreateRequest, SOSResponse
from app.services.alert_manager import alert_manager

router = APIRouter()

@router.post("/", response_model=SOSResponse, status_code=201)
async def trigger_sos(body: SOSCreateRequest, db: AsyncSession = Depends(get_db), user: User | None = Depends(get_current_user)):
    sos = SOSEvent(user_id=user.id if user else None, status=SOSStatus.ACTIVE, lat=body.lat, lng=body.lng, message=body.message, people_count=body.people_count, has_injured=body.has_injured, has_children=body.has_children, notified_orgs=[])
    db.add(sos)
    await db.flush()
    reached = await alert_manager.broadcast_sos(sos_id=sos.id, lat=body.lat, lng=body.lng, message=body.message, people_count=body.people_count, has_injured=body.has_injured)
    sos.alerts_sent = reached
    return sos

@router.patch("/{sos_id}/acknowledge", response_model=SOSResponse)
async def acknowledge_sos(sos_id: UUID, org_name: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_ngo_or_admin)):
    result = await db.execute(select(SOSEvent).where(SOSEvent.id == sos_id))
    sos = result.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS not found")
    sos.status = SOSStatus.ACKNOWLEDGED
    sos.acknowledged_by = org_name
    sos.acknowledged_at = datetime.now(timezone.utc)
    db.add(sos)
    return sos

@router.patch("/{sos_id}/resolve", response_model=SOSResponse)
async def resolve_sos(sos_id: UUID, resolution_notes: str = "", db: AsyncSession = Depends(get_db), user: User = Depends(get_ngo_or_admin)):
    result = await db.execute(select(SOSEvent).where(SOSEvent.id == sos_id))
    sos = result.scalar_one_or_none()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS not found")
    sos.status = SOSStatus.RESOLVED
    sos.resolved_at = datetime.now(timezone.utc)
    sos.resolution_notes = resolution_notes
    db.add(sos)
    return sos

@router.get("/active", response_model=list[SOSResponse])
async def list_active_sos(db: AsyncSession = Depends(get_db), user: User = Depends(get_ngo_or_admin)):
    result = await db.execute(select(SOSEvent).where(SOSEvent.status == SOSStatus.ACTIVE).order_by(SOSEvent.created_at.desc()))
    return result.scalars().all()
