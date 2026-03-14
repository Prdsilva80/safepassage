from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.models import EmergencyContact

router = APIRouter()

@router.get("/")
async def list_contacts(
    country: str | None = Query(None),
    sms_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    q = select(EmergencyContact).where(EmergencyContact.is_active == True)
    if country:
        q = q.where(EmergencyContact.country.ilike(f"%{country}%"))
    if sms_only:
        q = q.where(EmergencyContact.sms_confirmed == True)
    result = await db.execute(q.order_by(EmergencyContact.organisation))
    contacts = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "organisation": c.organisation,
            "acronym": c.acronym,
            "region": c.region,
            "country": c.country,
            "city": c.city,
            "phone": c.phone,
            "website": c.website,
            "contact_type": c.contact_type,
            "sms_confirmed": c.sms_confirmed,
            "whatsapp_confirmed": c.whatsapp_confirmed,
            "source_url": c.source_url,
            "last_verified_at": c.last_verified_at.isoformat() if c.last_verified_at else None,
            "notes": c.notes,
            "lat": c.lat,
            "lng": c.lng,
        }
        for c in contacts
    ]
