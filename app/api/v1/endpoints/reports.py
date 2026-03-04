from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.models import Report, ReportType, DangerLevel, User
from app.schemas.schemas import ReportConfirmRequest, ReportCreateRequest, ReportResponse
from app.services.geo_service import calculate_credibility_score, get_nearby_reports
from app.services.alert_manager import alert_manager

router = APIRouter()

@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(body: ReportCreateRequest, db: AsyncSession = Depends(get_db), user: User | None = Depends(get_current_user)):
    try:
        report_type = ReportType(body.report_type)
        danger_level = DangerLevel(body.danger_level)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    report = Report(user_id=user.id if user else None, zone_id=body.zone_id, report_type=report_type, danger_level=danger_level, lat=body.lat, lng=body.lng, title=body.title, description=body.description, language=body.language, credibility_score=0.5)
    db.add(report)
    await db.flush()
    if danger_level in (DangerLevel.CRITICAL, DangerLevel.HIGH):
        await alert_manager.broadcast_to_area(message={"type": "alert", "payload": {"alert_type": "danger_nearby", "title": f"⚠️ {danger_level.value.upper()}", "message": body.description or body.title or "Danger reported nearby.", "danger_level": danger_level.value, "lat": body.lat, "lng": body.lng}}, lat=body.lat, lng=body.lng, radius_km=15.0)
    return report

@router.get("/nearby", response_model=list[ReportResponse])
async def nearby_reports(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180), radius_km: float = Query(default=10.0, ge=0.1, le=100), hours_back: int = Query(default=24, ge=1, le=168), db: AsyncSession = Depends(get_db)):
    return await get_nearby_reports(db, lat, lng, radius_km, hours_back)

@router.post("/{report_id}/confirm", response_model=ReportResponse)
async def confirm_report(report_id: UUID, body: ReportConfirmRequest, db: AsyncSession = Depends(get_db), user: User | None = Depends(get_current_user)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if body.confirms:
        report.confirmations += 1
    else:
        report.contradictions += 1
    report.credibility_score = calculate_credibility_score(report.confirmations, report.contradictions)
    if report.contradictions > 5 and report.credibility_score < 0.2:
        report.is_active = False
    db.add(report)
    return report

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
