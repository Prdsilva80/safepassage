from fastapi import APIRouter
from app.api.v1.endpoints import ai, alerts, auth, contacts, danger, firms, intelligence, reports, routes, shelters, sos, zones, ws

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
api_router.include_router(zones.router,        prefix="/zones",        tags=["Zones"])
api_router.include_router(reports.router,      prefix="/reports",      tags=["Reports"])
api_router.include_router(shelters.router,     prefix="/shelters",     tags=["Shelters"])
api_router.include_router(routes.router,       prefix="/routes",       tags=["Routes"])
api_router.include_router(sos.router,          prefix="/sos",          tags=["SOS"])
api_router.include_router(ai.router,           prefix="/ai",           tags=["AI Assessment"])
api_router.include_router(alerts.router,       prefix="/alerts",       tags=["Alerts"])
api_router.include_router(ws.router,           prefix="/ws",           tags=["WebSocket"])
api_router.include_router(contacts.router,     prefix="/contacts",     tags=["Emergency Contacts"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Humanitarian Intelligence"])
api_router.include_router(firms.router,        prefix="/firms",        tags=["NASA FIRMS"])
api_router.include_router(danger.router, prefix="/danger", tags=["Danger Score"])
