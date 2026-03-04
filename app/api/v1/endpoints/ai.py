from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import RiskAssessmentRequest, RiskAssessmentResponse
from app.services.geo_service import get_nearby_reports, get_nearby_shelters, get_safe_routes
from app.ai.risk_assessment import assess_risk

router = APIRouter()

@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def risk_assessment(body: RiskAssessmentRequest, db: AsyncSession = Depends(get_db), user: User | None = Depends(get_current_user)):
    reports = await get_nearby_reports(db, body.lat, body.lng, radius_km=15.0, hours_back=24)
    shelters = await get_nearby_shelters(db, body.lat, body.lng, radius_km=30.0, requires_medical=body.needs_medical_attention)
    routes = await get_safe_routes(db, body.lat, body.lng, max_danger_score=0.6)
    best_shelter_id = shelters[0]["id"] if shelters else None
    best_route_id = routes[0]["id"] if routes else None
    danger_score = None
    if reports:
        weights = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25, "safe": 0.0}
        scores = [weights.get(r.get("danger_level", "medium"), 0.5) for r in reports[:20]]
        danger_score = sum(scores) / len(scores) if scores else None
    return await assess_risk(request=body, nearby_reports=reports, nearby_shelters=shelters, zone_danger_score=danger_score, best_shelter_id=best_shelter_id, best_route_id=best_route_id)
