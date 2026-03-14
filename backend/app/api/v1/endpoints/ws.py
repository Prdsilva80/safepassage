import asyncio
from uuid import UUID
import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from app.services.alert_manager import alert_manager

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.websocket("/connect")
async def websocket_connect(websocket: WebSocket, lat: float = Query(...), lng: float = Query(...), user_id: UUID | None = Query(default=None), zone_id: UUID | None = Query(default=None)):
    client = await alert_manager.connect(websocket, user_id, lat, lng, zone_id)
    await alert_manager.send_to_client(client, {"type": "connected", "payload": {"client_id": client.client_id, "lat": lat, "lng": lng}})

    async def heartbeat():
        from app.core.config import settings
        while True:
            await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            ok = await alert_manager.send_to_client(client, {"type": "ping", "payload": {}})
            if not ok:
                break

    heartbeat_task = asyncio.create_task(heartbeat())
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "location_update":
                new_lat = data.get("lat")
                new_lng = data.get("lng")
                if new_lat is not None and new_lng is not None:
                    client.lat = float(new_lat)
                    client.lng = float(new_lng)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("websocket_error", error=str(exc))
    finally:
        heartbeat_task.cancel()
        await alert_manager.disconnect(client)
