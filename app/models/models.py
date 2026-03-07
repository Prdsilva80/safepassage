"""
SafePassage — Database Models

Tables:
  users         → civilians, NGO workers, admins
  zones         → geographic conflict zones
  reports       → civilian danger/safety reports
  shelters      → verified shelters and medical posts
  routes        → safe evacuation routes
  sos_events    → SOS emergency events
  alert_log     → sent alerts history
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    CIVILIAN = "CIVILIAN"
    NGO_WORKER = "NGO_WORKER"
    ADMIN = "ADMIN"
    JOURNALIST = "JOURNALIST"


class ReportType(str, enum.Enum):
    BOMBARDMENT = "bombardment"
    GUNFIRE = "gunfire"
    ROAD_BLOCKED = "road_blocked"
    ROAD_CLEAR = "road_clear"
    CHECKPOINT = "checkpoint"
    SAFE_PASSAGE = "safe_passage"
    MEDICAL_EMERGENCY = "medical_emergency"
    FOOD_WATER = "food_water"


class DangerLevel(str, enum.Enum):
    CRITICAL = "critical"    # Active combat / immediate danger
    HIGH = "high"            # Recent activity / very dangerous
    MEDIUM = "medium"        # Unstable / proceed with caution
    LOW = "low"              # Relatively safe / monitor
    SAFE = "safe"            # Verified safe


class ShelterType(str, enum.Enum):
    EMERGENCY_SHELTER = "emergency_shelter"
    HOSPITAL = "hospital"
    MEDICAL_POST = "medical_post"
    FOOD_DISTRIBUTION = "food_distribution"
    WATER_POINT = "water_point"
    BORDER_CROSSING = "border_crossing"
    UN_COMPOUND = "un_compound"


class ShelterStatus(str, enum.Enum):
    OPEN = "open"
    FULL = "full"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class AlertType(str, enum.Enum):
    DANGER_NEARBY = "danger_nearby"
    ROUTE_UPDATE = "route_update"
    SHELTER_AVAILABLE = "shelter_available"
    SOS_RECEIVED = "sos_received"
    FAMILY_LOCATED = "family_located"
    SYSTEM = "system"


class SOSStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Identity (anonymous mode supported — all fields optional)
    username = Column(String(64), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    phone = Column(String(32), nullable=True)

    # Profile
    role = Column(Enum(UserRole), default=UserRole.CIVILIAN, nullable=False)
    display_name = Column(String(128), nullable=True)
    language = Column(String(8), default="en", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)

    # Location (last known, encrypted in production)
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Emergency contact (for SOS)
    emergency_contact_name = Column(String(128), nullable=True)
    emergency_contact_phone = Column(String(32), nullable=True)
    emergency_contact_email = Column(String(255), nullable=True)

    # Health / mobility flags (for personalised route planning)
    needs_medical_attention = Column(Boolean, default=False)
    mobility_impaired = Column(Boolean, default=False)
    has_children = Column(Boolean, default=False)
    has_elderly = Column(Boolean, default=False)
    group_size = Column(Integer, default=1)

    # Relationships
    reports = relationship("Report", back_populates="user", lazy="select")
    sos_events = relationship("SOSEvent", back_populates="user", lazy="select")

    __table_args__ = (
        Index("ix_users_last_location", "last_lat", "last_lng"),
    )


class Zone(Base):
    """Geographic conflict zone (city, district, region)."""
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    name = Column(String(256), nullable=False, index=True)
    country = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Bounding box
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius_km = Column(Float, nullable=False, default=25.0)

    danger_level = Column(Enum(DangerLevel), default=DangerLevel.UNKNOWN if hasattr(DangerLevel, 'UNKNOWN') else DangerLevel.MEDIUM, nullable=False)  # type: ignore
    danger_score = Column(Float, default=0.5)  # 0.0 (safe) → 1.0 (critical)
    danger_score_updated_at = Column(DateTime(timezone=True), nullable=True)

    active_conflict = Column(Boolean, default=True)
    population_estimate = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    reports = relationship("Report", back_populates="zone", lazy="select")
    shelters = relationship("Shelter", back_populates="zone", lazy="select")
    routes = relationship("Route", back_populates="zone", lazy="select")

    __table_args__ = (
        Index("ix_zones_location", "center_lat", "center_lng"),

    )


class Report(Base):
    """Civilian ground-truth report of a situation."""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-expire stale reports

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=True)

    report_type = Column(Enum(ReportType), nullable=False, index=True)
    danger_level = Column(Enum(DangerLevel), nullable=False)

    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location_accuracy_m = Column(Float, nullable=True)

    # Content
    title = Column(String(256), nullable=True)
    description = Column(Text, nullable=True)
    language = Column(String(8), default="en")

    # Credibility
    confirmations = Column(Integer, default=0)  # Upvotes from other civilians
    contradictions = Column(Integer, default=0)  # Downvotes
    credibility_score = Column(Float, default=0.5)  # Calculated: 0.0-1.0
    verified_by_ngo = Column(Boolean, default=False)

    # AI analysis
    ai_processed = Column(Boolean, default=False)
    ai_risk_score = Column(Float, nullable=True)
    ai_summary = Column(Text, nullable=True)

    # Media
    media_urls = Column(JSON, default=list)  # List of secure URLs

    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="reports")
    zone = relationship("Zone", back_populates="reports")

    __table_args__ = (
        Index("ix_reports_location", "lat", "lng"),
        Index("ix_reports_type_danger", "report_type", "danger_level"),
        Index("ix_reports_active_created", "is_active", "created_at"),
    )


class Shelter(Base):
    """Verified shelter, hospital, food/water point, or border crossing."""
    __tablename__ = "shelters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(256), nullable=False)
    shelter_type = Column(Enum(ShelterType), nullable=False, index=True)
    status = Column(Enum(ShelterStatus), default=ShelterStatus.UNKNOWN, nullable=False, index=True)

    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(Text, nullable=True)

    # Capacity
    capacity_total = Column(Integer, nullable=True)
    capacity_current = Column(Integer, nullable=True)
    capacity_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Services
    has_medical = Column(Boolean, default=False)
    has_food = Column(Boolean, default=False)
    has_water = Column(Boolean, default=False)
    has_power = Column(Boolean, default=False)
    has_comms = Column(Boolean, default=False)   # Satellite phone / internet
    accepts_families = Column(Boolean, default=True)
    accepts_injured = Column(Boolean, default=False)

    # Contact
    contact_name = Column(String(128), nullable=True)
    contact_phone = Column(String(32), nullable=True)
    operating_org = Column(String(256), nullable=True)  # UNHCR, MSF, etc.

    # Verification
    verified = Column(Boolean, default=False)
    verification_count = Column(Integer, default=0)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    zone = relationship("Zone", back_populates="shelters")

    __table_args__ = (
        Index("ix_shelters_location", "lat", "lng"),
        Index("ix_shelters_type_status", "shelter_type", "status"),
    )


class Route(Base):
    """Safe evacuation route through or out of a conflict zone."""
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)

    # Origin → Destination
    origin_name = Column(String(256), nullable=True)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    destination_name = Column(String(256), nullable=True)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)

    # Route geometry: list of [lat, lng] waypoints
    waypoints = Column(JSON, default=list)

    # Safety assessment
    danger_score = Column(Float, default=0.5)   # 0.0 safe → 1.0 critical
    danger_level = Column(Enum(DangerLevel), default=DangerLevel.MEDIUM)
    is_active = Column(Boolean, default=True)
    last_assessed_at = Column(DateTime(timezone=True), nullable=True)

    # Practical info
    distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    requires_vehicle = Column(Boolean, default=False)
    accessible_for_disabled = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Verification
    verified_by_ngo = Column(Boolean, default=False)
    confirmation_count = Column(Integer, default=0)

    # Relationships
    zone = relationship("Zone", back_populates="routes")

    __table_args__ = (
        Index("ix_routes_origin", "origin_lat", "origin_lng"),
        Index("ix_routes_danger", "danger_score", "is_active"),
    )


class SOSEvent(Base):
    """Emergency SOS event triggered by a civilian."""
    __tablename__ = "sos_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status = Column(Enum(SOSStatus), default=SOSStatus.ACTIVE, nullable=False, index=True)

    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Details
    message = Column(Text, nullable=True)
    people_count = Column(Integer, default=1)
    has_injured = Column(Boolean, default=False)
    has_children = Column(Boolean, default=False)

    # Response
    acknowledged_by = Column(String(256), nullable=True)   # NGO/org name
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Broadcast tracking
    alerts_sent = Column(Integer, default=0)
    notified_orgs = Column(JSON, default=list)  # List of org names notified

    # Relationships
    user = relationship("User", back_populates="sos_events")

    __table_args__ = (
        Index("ix_sos_status_created", "status", "created_at"),
        Index("ix_sos_location", "lat", "lng"),
    )


class AlertLog(Base):
    """Log of all alerts sent to users."""
    __tablename__ = "alert_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)

    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    danger_level = Column(Enum(DangerLevel), nullable=True)

    # Targeting
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    radius_km = Column(Float, nullable=True)
    target_count = Column(Integer, default=0)  # How many users were targeted

    delivered = Column(Boolean, default=False)
    delivery_channel = Column(String(32), default="websocket")  # websocket, push, sms
    metadata_ = Column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("ix_alert_log_user_created", "user_id", "created_at"),
        Index("ix_alert_log_type", "alert_type"),
    )

class ContactType(str, enum.Enum):
    HOTLINE = "hotline"
    OFFICE = "office"
    SWITCHBOARD = "switchboard"
    FIELD = "field"
    FORM = "form"

class EmergencyContact(Base):
    """Verified emergency contacts for humanitarian organisations."""
    __tablename__ = "emergency_contacts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Organisation
    organisation = Column(String(128), nullable=False)
    acronym = Column(String(16), nullable=True)
    region = Column(String(128), nullable=True)
    country = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    # Contact
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    contact_type = Column(Enum(ContactType, values_callable=lambda x: [e.value for e in x]), default=ContactType.OFFICE, nullable=False)
    # Verification
    sms_confirmed = Column(Boolean, default=False, nullable=False)
    whatsapp_confirmed = Column(Boolean, default=False, nullable=False)
    source_url = Column(String(512), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    # Location
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_emergency_contacts_country", "country"),
        Index("ix_emergency_contacts_org", "organisation"),
    )
