from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    display_name: str | None = None
    language: str = "en"
    phone: str | None = None
    is_anonymous: bool = False
    role: str = "CIVILIAN"

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    language: str | None = None
    phone: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    needs_medical_attention: bool | None = None
    mobility_impaired: bool | None = None
    has_children: bool | None = None
    has_elderly: bool | None = None
    group_size: int | None = None

class UserProfileResponse(BaseModel):
    id: UUID
    username: str | None
    email: str | None
    display_name: str | None
    role: str
    language: str
    is_anonymous: bool
    is_active: bool
    group_size: int
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# ── Zones ─────────────────────────────────────────────────────────────────────

class ZoneCreateRequest(BaseModel):
    name: str
    country: str
    description: str | None = None
    center_lat: float = Field(..., ge=-90, le=90)
    center_lng: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=50.0, ge=1)
    active_conflict: bool = True

class ZoneResponse(BaseModel):
    id: UUID
    name: str
    country: str
    center_lat: float
    center_lng: float
    radius_km: float
    danger_level: str
    danger_score: float
    active_conflict: bool
    created_at: datetime
    model_config = {"from_attributes": True}

# ── Reports ───────────────────────────────────────────────────────────────────

class ReportCreateRequest(BaseModel):
    report_type: str
    danger_level: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    location_accuracy_m: float | None = None
    title: str | None = None
    description: str | None = None
    language: str = "en"
    zone_id: UUID | None = None

class ReportConfirmRequest(BaseModel):
    confirms: bool

class ReportResponse(BaseModel):
    id: UUID
    report_type: str
    danger_level: str
    lat: float
    lng: float
    title: str | None
    description: str | None
    confirmations: int
    contradictions: int
    credibility_score: float
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class NearbyReportsRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 10.0
    hours_back: int = 24

# ── Shelters ──────────────────────────────────────────────────────────────────

class ShelterCreateRequest(BaseModel):
    name: str
    shelter_type: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    address: str | None = None
    zone_id: UUID | None = None
    capacity_total: int | None = None
    has_medical: bool = False
    has_food: bool = False
    has_water: bool = False
    has_power: bool = False
    has_comms: bool = False
    accepts_families: bool = True
    accepts_injured: bool = True
    contact_phone: str | None = None
    operating_org: str | None = None
    notes: str | None = None

class ShelterUpdateRequest(BaseModel):
    status: str | None = None
    capacity_current: int | None = None
    has_medical: bool | None = None
    has_food: bool | None = None
    has_water: bool | None = None
    notes: str | None = None

class ShelterResponse(BaseModel):
    id: UUID
    name: str
    shelter_type: str
    status: str
    lat: float
    lng: float
    address: str | None
    capacity_total: int | None
    capacity_current: int | None
    has_medical: bool
    has_food: bool
    has_water: bool
    accepts_families: bool
    accepts_injured: bool
    operating_org: str | None
    verified: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class NearbySheltersRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 30.0

# ── Routes ────────────────────────────────────────────────────────────────────

class RouteSearchRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    max_danger_score: float = 0.6

class RouteResponse(BaseModel):
    id: UUID
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    origin_name: str | None
    destination_name: str | None
    danger_score: float
    danger_level: str
    distance_km: float | None
    estimated_duration_minutes: int | None
    requires_vehicle: bool
    accessible_for_disabled: bool
    is_active: bool
    waypoints: list[Any]
    created_at: datetime
    model_config = {"from_attributes": True}

# ── SOS ───────────────────────────────────────────────────────────────────────

class SOSCreateRequest(BaseModel):
    language: str = "auto"
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    message: str | None = None
    people_count: int = Field(default=1, ge=1)
    has_injured: bool = False
    has_children: bool = False

class SOSResponse(BaseModel):
    id: UUID
    status: str
    lat: float
    lng: float
    message: str | None
    people_count: int
    has_injured: bool
    has_children: bool
    alerts_sent: int
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}

# ── AI ────────────────────────────────────────────────────────────────────────

class RiskAssessmentRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    has_vehicle: bool = False
    needs_medical_attention: bool = False
    mobility_impaired: bool = False
    has_children: bool = False
    has_elderly: bool = False
    group_size: int = Field(default=1, ge=1)
    language: str = "en"
    additional_context: str | None = None

class RiskAssessmentResponse(BaseModel):
    risk_level: str
    risk_score: float
    summary: str
    immediate_actions: list[str]
    evacuation_plan: str
    avoid_areas: list[str]
    recommended_shelter_id: UUID | None
    recommended_route_id: UUID | None
    ai_confidence: float
    generated_at: datetime
    model_config = {"from_attributes": True}

# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertBroadcastRequest(BaseModel):
    alert_type: str
    title: str
    message: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=50.0, ge=1, le=500)
    danger_level: str | None = None
    zone_id: UUID | None = None
