"""
SafePassage — Security Hardening Layer

Threats addressed:
  1. DDoS / volumetric attacks       → Adaptive rate limiting + IP blocking
  2. Brute force (auth endpoints)    → Exponential backoff + account lockout
  3. SQL injection                   → Parameterised queries (SQLAlchemy) + input sanitisation
  4. Geo-spoofing / fake reports     → Anomaly detection + credibility decay
  5. WebSocket flood                 → Connection limits + message rate limiting
  6. Replay attacks                  → JWT jti claims + token blacklist
  7. Data exfiltration               → Response size limits + field masking
  8. Insider / NGO abuse             → Audit trail on all privileged actions
  9. SSRF / header injection         → Strict input validation
 10. Timing attacks (auth)           → Constant-time comparisons
"""
import hashlib
import hmac
import ipaddress
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)


# ── 1. Input Sanitisation ─────────────────────────────────────────────────────

# Patterns that should NEVER appear in civilian reports or messages
_INJECTION_PATTERNS = [
    re.compile(r"(--|;|/\*|\*/|xp_|UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO)", re.IGNORECASE),
    re.compile(r"<script[\s\S]*?>[\s\S]*?</script>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=, etc.
    re.compile(r"\{\{.*?\}\}"),  # Template injection
    re.compile(r"\$\{.*?\}"),    # JS template literals
]

# Fields that accept any text (reports, messages) — sanitised but not blocked
_MAX_FIELD_LENGTHS = {
    "description": 2000,
    "message": 1000,
    "title": 256,
    "notes": 1000,
    "additional_context": 500,
    "resolution_notes": 1000,
}


def sanitise_text(value: str, field_name: str = "text") -> str:
    """
    Sanitise free-text input:
    - Strip null bytes and control characters (except newlines/tabs)
    - Truncate to field maximum
    - Strip leading/trailing whitespace
    Does NOT strip HTML (frontend handles rendering safely).
    """
    if not isinstance(value, str):
        return str(value)

    # Strip null bytes and dangerous control chars
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)

    # Truncate
    max_len = _MAX_FIELD_LENGTHS.get(field_name, 1000)
    cleaned = cleaned[:max_len]

    return cleaned.strip()


def check_injection(value: str) -> bool:
    """Returns True if the value contains suspicious injection patterns."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def validate_coordinates(lat: float, lng: float) -> tuple[bool, str]:
    """Validate coordinate plausibility (not just range, but also NaN/Inf)."""
    import math
    if math.isnan(lat) or math.isnan(lng) or math.isinf(lat) or math.isinf(lng):
        return False, "Coordinates contain NaN or Inf"
    if not (-90 <= lat <= 90):
        return False, f"Latitude {lat} out of range [-90, 90]"
    if not (-180 <= lng <= 180):
        return False, f"Longitude {lng} out of range [-180, 180]"
    # Reject (0.0, 0.0) — null island, likely a GPS failure
    if lat == 0.0 and lng == 0.0:
        return False, "Coordinates (0,0) rejected — likely GPS failure"
    return True, ""


# ── 2. Brute Force Protection ─────────────────────────────────────────────────

class BruteForceProtector:
    """
    In-memory brute force protection with exponential backoff.
    For production: back with Redis for multi-instance consistency.

    Tracks failed attempts per IP and per username.
    After N failures: temporary lockout with exponential delay.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,          # 5 min window
        lockout_seconds: int = 900,          # 15 min base lockout
        max_lockout_seconds: int = 86400,    # 24h max lockout
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self.max_lockout_seconds = max_lockout_seconds

        # {key: [(timestamp, ...), ...]}
        self._attempts: dict[str, list[float]] = defaultdict(list)
        # {key: (lockout_until, attempt_count)}
        self._lockouts: dict[str, tuple[float, int]] = {}

    def _key(self, ip: str, username: str | None = None) -> str:
        return f"{ip}:{username or '*'}"

    def is_locked_out(self, ip: str, username: str | None = None) -> tuple[bool, int]:
        """Returns (is_locked, seconds_remaining)."""
        key = self._key(ip, username)
        if key in self._lockouts:
            lockout_until, _ = self._lockouts[key]
            remaining = lockout_until - time.time()
            if remaining > 0:
                return True, int(remaining)
            else:
                del self._lockouts[key]
        return False, 0

    def record_failure(self, ip: str, username: str | None = None) -> None:
        """Record a failed auth attempt. May trigger lockout."""
        key = self._key(ip, username)
        now = time.time()

        # Clean old attempts outside window
        self._attempts[key] = [
            t for t in self._attempts[key]
            if now - t < self.window_seconds
        ]
        self._attempts[key].append(now)

        if len(self._attempts[key]) >= self.max_attempts:
            # Exponential backoff: lockout doubles each time
            _, prev_count = self._lockouts.get(key, (0, 0))
            new_count = prev_count + 1
            lockout_duration = min(
                self.lockout_seconds * (2 ** (new_count - 1)),
                self.max_lockout_seconds,
            )
            self._lockouts[key] = (now + lockout_duration, new_count)
            logger.warning(
                "brute_force_lockout",
                ip=ip,
                username=username,
                attempts=len(self._attempts[key]),
                lockout_seconds=int(lockout_duration),
            )
            self._attempts[key] = []  # Reset attempt window

    def record_success(self, ip: str, username: str | None = None) -> None:
        """Clear attempts on successful auth."""
        key = self._key(ip, username)
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)


# Singleton
brute_force_protector = BruteForceProtector()


# ── 3. Token Blacklist (Replay Attack Prevention) ─────────────────────────────

class TokenBlacklist:
    """
    Blacklist for revoked JWT tokens (logout, password change, account disable).
    Uses jti (JWT ID) claims.
    In-memory for single instance; replace with Redis SET for production clusters.
    """

    def __init__(self) -> None:
        # {jti: expires_at_timestamp}
        self._blacklist: dict[str, float] = {}
        self._last_cleanup = time.time()

    def revoke(self, jti: str, expires_at: datetime) -> None:
        self._blacklist[jti] = expires_at.timestamp()
        self._maybe_cleanup()
        logger.info("token_revoked", jti=jti[:8] + "...")

    def is_revoked(self, jti: str) -> bool:
        return jti in self._blacklist

    def _maybe_cleanup(self) -> None:
        """Remove expired tokens periodically."""
        now = time.time()
        if now - self._last_cleanup > 3600:  # Every hour
            before = len(self._blacklist)
            self._blacklist = {
                jti: exp for jti, exp in self._blacklist.items()
                if exp > now
            }
            logger.info("token_blacklist_cleanup", removed=before - len(self._blacklist))
            self._last_cleanup = now


token_blacklist = TokenBlacklist()


# ── 4. IP Blocklist ───────────────────────────────────────────────────────────

class IPBlocklist:
    """
    Dynamic IP blocklist for detected attack sources.
    Supports CIDR ranges and temporary bans.
    """

    def __init__(self) -> None:
        # {ip_str: expires_at} — None = permanent
        self._blocked: dict[str, float | None] = {}
        # Permanent CIDR blocks (e.g. known bad actors)
        self._cidr_blocks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []

    def block_ip(self, ip: str, duration_seconds: int | None = None) -> None:
        expires = time.time() + duration_seconds if duration_seconds else None
        self._blocked[ip] = expires
        logger.warning("ip_blocked", ip=ip, duration_seconds=duration_seconds)

    def unblock_ip(self, ip: str) -> None:
        self._blocked.pop(ip, None)

    def block_cidr(self, cidr: str) -> None:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            self._cidr_blocks.append(network)  # type: ignore
            logger.warning("cidr_blocked", cidr=cidr)
        except ValueError:
            logger.error("invalid_cidr", cidr=cidr)

    def is_blocked(self, ip: str) -> bool:
        # Check direct IP
        if ip in self._blocked:
            expires = self._blocked[ip]
            if expires is None or time.time() < expires:
                return True
            del self._blocked[ip]

        # Check CIDR
        try:
            addr = ipaddress.ip_address(ip)
            for network in self._cidr_blocks:
                if addr in network:
                    return True
        except ValueError:
            pass

        return False


ip_blocklist = IPBlocklist()


# ── 5. Geo-Spoofing / Report Anomaly Detection ────────────────────────────────

class ReportAnomalyDetector:
    """
    Detects suspicious report patterns that may indicate:
    - Coordinated disinformation (many reports from same source in same location)
    - GPS spoofing (impossible movement between reports)
    - Automated fake report flooding
    """

    MAX_REPORTS_PER_USER_PER_HOUR = 20
    MAX_REPORTS_PER_IP_PER_HOUR = 30
    MAX_SPEED_KMH = 300  # Max plausible human speed (helicopter) for geo-consistency

    def __init__(self) -> None:
        # {user_id: [(timestamp, lat, lng), ...]}
        self._user_reports: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
        # {ip: [timestamp, ...]}
        self._ip_reports: dict[str, list[float]] = defaultdict(list)

    def check_and_record(
        self,
        user_id: str | None,
        ip: str,
        lat: float,
        lng: float,
    ) -> tuple[bool, str]:
        """
        Returns (is_suspicious, reason).
        Records the report if not suspicious.
        """
        now = time.time()
        cutoff = now - 3600  # 1 hour window

        # IP rate check
        self._ip_reports[ip] = [t for t in self._ip_reports[ip] if t > cutoff]
        if len(self._ip_reports[ip]) >= self.MAX_REPORTS_PER_IP_PER_HOUR:
            logger.warning("report_ip_flood", ip=ip, count=len(self._ip_reports[ip]))
            return True, f"Too many reports from this IP ({len(self._ip_reports[ip])}/hour)"
        self._ip_reports[ip].append(now)

        if user_id:
            user_history = [(t, la, ln) for t, la, ln in self._user_reports[user_id] if t > cutoff]

            # User rate check
            if len(user_history) >= self.MAX_REPORTS_PER_USER_PER_HOUR:
                logger.warning("report_user_flood", user_id=user_id, count=len(user_history))
                return True, f"Too many reports from this user ({len(user_history)}/hour)"

            # Geo-consistency check (impossible movement)
            if user_history:
                last_time, last_lat, last_lng = user_history[-1]
                from app.services.geo_service import haversine_km
                dist_km = haversine_km(last_lat, last_lng, lat, lng)
                elapsed_h = (now - last_time) / 3600
                if elapsed_h > 0:
                    speed_kmh = dist_km / elapsed_h
                    if speed_kmh > self.MAX_SPEED_KMH:
                        logger.warning(
                            "geo_spoofing_detected",
                            user_id=user_id,
                            speed_kmh=round(speed_kmh, 1),
                            dist_km=round(dist_km, 1),
                        )
                        return True, f"Impossible movement detected ({speed_kmh:.0f} km/h)"

            self._user_reports[user_id].append((now, lat, lng))

        return False, ""


report_anomaly_detector = ReportAnomalyDetector()


# ── 6. Audit Trail ────────────────────────────────────────────────────────────

class AuditTrail:
    """
    Immutable audit log for all privileged actions.
    Writes to structured log (can be shipped to SIEM / ELK).
    """

    def log(
        self,
        action: str,
        actor_id: str | UUID | None,
        actor_role: str,
        target_type: str,
        target_id: str | UUID | None,
        ip: str,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        logger.info(
            "audit_event",
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            actor_id=str(actor_id) if actor_id else "anonymous",
            actor_role=actor_role,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            ip=ip,
            success=success,
            details=details or {},
        )


audit_trail = AuditTrail()


# ── 7. Constant-Time Auth Comparison ─────────────────────────────────────────

def constant_time_compare(val1: str, val2: str) -> bool:
    """Prevent timing attacks on token/password comparisons."""
    return hmac.compare_digest(
        val1.encode("utf-8"),
        val2.encode("utf-8"),
    )


# ── 8. Security Headers ───────────────────────────────────────────────────────

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(self), camera=(), microphone=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss:; "
        "frame-ancestors 'none';"
    ),
    "Cache-Control": "no-store",  # Never cache API responses
}


# ── 9. Request Fingerprinting ─────────────────────────────────────────────────

def fingerprint_request(ip: str, user_agent: str, accept_language: str) -> str:
    """
    Create a lightweight request fingerprint for anomaly detection.
    NOT stored — used transiently for rate limiting keys.
    """
    raw = f"{ip}:{user_agent[:100]}:{accept_language[:20]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]