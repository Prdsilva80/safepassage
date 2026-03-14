"""
SafePassage — Real-Time Alert Manager (WebSocket + Redis Pub/Sub)

Architecture:
  - Each connected client registers with lat/lng
  - Redis pub/sub channel receives alert events
  - AlertManager fans out to all clients in the affected radius
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis
import structlog
from fastapi import WebSocket

from app.core.config import settings
from app.services.geo_service import haversine_km

logger = structlog.get_logger(__name__)


class ConnectedClient:
    def __init__(
        self,
        websocket: WebSocket,
        user_id: UUID | None,
        lat: float,
        lng: float,
        zone_id: UUID | None = None,
    ) -> None:
        self.websocket = websocket
        self.user_id = user_id
        self.lat = lat
        self.lng = lng
        self.zone_id = zone_id
        self.connected_at = datetime.now(timezone.utc)
        self.last_ping = datetime.now(timezone.utc)

    @property
    def client_id(self) -> str:
        return str(self.user_id) if self.user_id else id(self.websocket).__str__()


class AlertManager:
    """
    Manages all WebSocket connections and broadcasts alerts by geographic proximity.
    Thread-safe, handles disconnections gracefully.
    """

    def __init__(self) -> None:
        self._clients: dict[str, ConnectedClient] = {}
        self._lock = asyncio.Lock()
        self._redis: aioredis.Redis | None = None  # type: ignore
        self._pubsub_task: asyncio.Task | None = None  # type: ignore

    async def startup(self) -> None:
        """Connect to Redis and start pub/sub listener."""
        try:
            self._redis = aioredis.from_url(
                str(settings.REDIS_URL),
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._pubsub_task = asyncio.create_task(self._listen_redis())
            logger.info("alert_manager_started", redis_url=str(settings.REDIS_URL))
        except Exception as exc:
            logger.warning("alert_manager_redis_unavailable", error=str(exc))
            # Continue without Redis — direct in-process broadcasting only

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
        if self._redis:
            await self._redis.aclose()
        logger.info("alert_manager_shutdown")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: UUID | None,
        lat: float,
        lng: float,
        zone_id: UUID | None = None,
    ) -> ConnectedClient:
        await websocket.accept()
        client = ConnectedClient(websocket, user_id, lat, lng, zone_id)
        async with self._lock:
            self._clients[client.client_id] = client
        logger.info(
            "ws_client_connected",
            client_id=client.client_id,
            total_clients=len(self._clients),
            lat=lat, lng=lng,
        )
        return client

    async def disconnect(self, client: ConnectedClient) -> None:
        async with self._lock:
            self._clients.pop(client.client_id, None)
        logger.info(
            "ws_client_disconnected",
            client_id=client.client_id,
            total_clients=len(self._clients),
        )

    async def send_to_client(self, client: ConnectedClient, message: dict[str, Any]) -> bool:
        """Send message to a single client. Returns False if disconnected."""
        try:
            await client.websocket.send_json(message)
            return True
        except Exception:
            await self.disconnect(client)
            return False

    async def broadcast_to_area(
        self,
        message: dict[str, Any],
        lat: float,
        lng: float,
        radius_km: float,
        zone_id: UUID | None = None,
        exclude_user_id: UUID | None = None,
    ) -> int:
        """
        Broadcast a message to all clients within radius_km of (lat, lng).
        Returns number of clients reached.
        """
        # Publish to Redis for multi-instance support
        if self._redis:
            try:
                payload = json.dumps({
                    **message,
                    "_broadcast_lat": lat,
                    "_broadcast_lng": lng,
                    "_broadcast_radius_km": radius_km,
                    "_exclude_user_id": str(exclude_user_id) if exclude_user_id else None,
                })
                await self._redis.publish(settings.REDIS_ALERT_CHANNEL, payload)
            except Exception as exc:
                logger.warning("redis_publish_failed", error=str(exc))

        # Also broadcast directly to local clients (same process)
        return await self._local_broadcast(message, lat, lng, radius_km, zone_id, exclude_user_id)

    async def _local_broadcast(
        self,
        message: dict[str, Any],
        lat: float,
        lng: float,
        radius_km: float,
        zone_id: UUID | None = None,
        exclude_user_id: UUID | None = None,
    ) -> int:
        async with self._lock:
            clients = list(self._clients.values())

        reached = 0
        send_tasks = []

        for client in clients:
            if exclude_user_id and client.user_id == exclude_user_id:
                continue
            # Check geographic proximity
            dist = haversine_km(lat, lng, client.lat, client.lng)
            if dist <= radius_km:
                send_tasks.append(self.send_to_client(client, message))

        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            reached = sum(1 for r in results if r is True)

        logger.info(
            "alert_broadcast",
            lat=lat, lng=lng, radius_km=radius_km,
            targeted=len(send_tasks), reached=reached,
        )
        return reached

    async def broadcast_sos(
        self,
        sos_id: UUID,
        lat: float,
        lng: float,
        message: str | None,
        people_count: int,
        has_injured: bool,
    ) -> int:
        """Broadcast SOS alert to all nearby clients and NGO workers."""
        payload = {
            "type": "sos",
            "payload": {
                "sos_id": str(sos_id),
                "lat": lat,
                "lng": lng,
                "message": message,
                "people_count": people_count,
                "has_injured": has_injured,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        return await self.broadcast_to_area(
            payload, lat, lng,
            radius_km=settings.SOS_BROADCAST_RADIUS_KM,
        )

    async def _listen_redis(self) -> None:
        """Subscribe to Redis pub/sub and forward messages to local clients."""
        if not self._redis:
            return
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(settings.REDIS_ALERT_CHANNEL)
        logger.info("redis_pubsub_subscribed", channel=settings.REDIS_ALERT_CHANNEL)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    lat = data.pop("_broadcast_lat", None)
                    lng = data.pop("_broadcast_lng", None)
                    radius = data.pop("_broadcast_radius_km", 50.0)
                    exclude = data.pop("_exclude_user_id", None)
                    if lat and lng:
                        await self._local_broadcast(data, lat, lng, radius, exclude_user_id=exclude)
                except Exception as exc:
                    logger.error("redis_message_parse_error", error=str(exc))
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(settings.REDIS_ALERT_CHANNEL)

    @property
    def connected_count(self) -> int:
        return len(self._clients)


# Singleton — shared across the app
alert_manager = AlertManager()