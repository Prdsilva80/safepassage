from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_ngo_or_admin
from app.db.database import get_db
from app.models.models import AlertLog, AlertType, DangerLevel, User
from app.schemas.schemas import AlertBroadcastRequest
from app.services.alert_manager import alert_manager

router = APIRouter()

@router.post("/broadcast", status_code=200)
async def broadcast_alert(body: AlertBroadcastRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_ngo_or_admin)):
    try:
        alert_type = AlertType(body.alert_type)
    except ValueError:
        alert_type = AlertType.SYSTEM
    danger_level = None
    if body.danger_level:
        try:
            danger_level = DangerLevel(body.danger_level)
        except ValueError:
            pass
    reached = await alert_manager.broadcast_to_area(message={"type": "alert", "payload": {"alert_type": alert_type.value, "title": body.title, "message": body.message, "danger_level": danger_level.value if danger_level else None, "lat": body.lat, "lng": body.lng, "radius_km": body.radius_km}}, lat=body.lat, lng=body.lng, radius_km=body.radius_km)
    log = AlertLog(user_id=user.id, zone_id=body.zone_id, alert_type=alert_type, title=body.title, message=body.message, danger_level=danger_level, lat=body.lat, lng=body.lng, radius_km=body.radius_km, target_count=reached, delivered=reached > 0, delivery_channel="websocket")
    db.add(log)
    return {"reached": reached, "message": "Alert broadcast sent"}
