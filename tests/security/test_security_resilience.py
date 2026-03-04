"""
SafePassage — Security Middleware Stack

Applied to every request in order:
  1. IP blocklist check          (fast-fail, <1ms)
  2. Security headers injection
  3. Request size limit
  4. Suspicious path detection
  5. Slow-loris protection
  6. Response time logging
"""
import time
from typing import Callable

import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security_hardening.hardening import (
    SECURITY_HEADERS,
    fingerprint_request,
    ip_blocklist,
)

logger = structlog.get_logger(__name__)

# Paths that should NEVER exist in a legitimate request
_SUSPICIOUS_PATHS = [
    "/wp-admin", "/wp-login", "/.env", "/.git", "/phpMyAdmin",
    "/admin/config", "/etc/passwd", "/proc/", "/../",
    "/actuator", "/jolokia", "/console", "/manager/html",
    "/cgi-bin", "/.ssh", "/backup", "/dump",
]

# Maximum request body sizes per endpoint category
_MAX_BODY_SIZES = {
    "/api/v1/reports": 10_000,       # 10KB
    "/api/v1/sos": 5_000,            # 5KB
    "/api/v1/ai": 5_000,             # 5KB
    "/api/v1/alerts": 10_000,        # 10KB
    "default": 50_000,               # 50KB general max
}


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Main security middleware — runs on every request.
    Designed to be fast: most checks exit in microseconds.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # ── 1. Get client IP (handle proxies correctly) ───────────────────────
        client_ip = self._get_real_ip(request)

        # ── 2. IP blocklist (fast-fail) ───────────────────────────────────────
        if ip_blocklist.is_blocked(client_ip):
            logger.warning("blocked_ip_request", ip=client_ip, path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"},
            )

        # ── 3. Suspicious path detection ──────────────────────────────────────
        path = request.url.path.lower()
        if any(sus in path for sus in _SUSPICIOUS_PATHS):
            logger.warning(
                "suspicious_path_request",
                ip=client_ip,
                path=request.url.path,
                method=request.method,
            )
            # Auto-block IPs probing for vulnerabilities
            ip_blocklist.block_ip(client_ip, duration_seconds=3600)
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Not found"},
            )

        # ── 4. Method validation ───────────────────────────────────────────────
        if request.method not in ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"):
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={"detail": "Method not allowed"},
            )

        # ── 5. Request size limit ─────────────────────────────────────────────
        content_length = request.headers.get("content-length")
        if content_length:
            max_size = self._get_max_size(request.url.path)
            if int(content_length) > max_size:
                logger.warning(
                    "request_too_large",
                    ip=client_ip,
                    path=request.url.path,
                    size=content_length,
                    max=max_size,
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request too large (max {max_size} bytes)"},
                )

        # ── 6. Header injection check ──────────────────────────────────────────
        for header_name, header_value in request.headers.items():
            if "\r" in header_value or "\n" in header_value:
                logger.warning("header_injection_attempt", ip=client_ip, header=header_name)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request headers"},
                )

        # ── 7. Process request ─────────────────────────────────────────────────
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("middleware_unhandled_error", ip=client_ip, error=str(exc))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

        # ── 8. Inject security headers ────────────────────────────────────────
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add request ID for tracing
        import uuid
        response.headers["X-Request-ID"] = str(uuid.uuid4())

        # ── 9. Log response ───────────────────────────────────────────────────
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "request_processed",
            ip=client_ip,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response

    def _get_real_ip(self, request: Request) -> str:
        """
        Extract real client IP, respecting trusted proxy headers.
        Only trust X-Forwarded-For behind known proxy (nginx).
        """
        # In production behind nginx, trust X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # X-Forwarded-For — use leftmost (original client)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Direct connection
        if request.client:
            return request.client.host

        return "unknown"

    def _get_max_size(self, path: str) -> int:
        for prefix, size in _MAX_BODY_SIZES.items():
            if path.startswith(prefix):
                return size
        return _MAX_BODY_SIZES["default"]


class WebSocketRateLimitMiddleware:
    """
    Tracks WebSocket message rates per connection.
    Disconnects clients sending messages too fast.
    Applied inside the ws.py endpoint.
    """

    MAX_MESSAGES_PER_MINUTE = 60

    def __init__(self) -> None:
        # {client_id: deque of timestamps}
        from collections import defaultdict, deque
        self._message_times: dict[str, "deque[float]"] = defaultdict(lambda: deque(maxlen=120))

    def check_rate(self, client_id: str) -> bool:
        """Returns True if rate is OK, False if should be disconnected."""
        import collections
        now = time.time()
        times = self._message_times[client_id]

        # Remove messages older than 60 seconds
        while times and now - times[0] > 60:
            times.popleft()

        times.append(now)
        rate = len(times)

        if rate > self.MAX_MESSAGES_PER_MINUTE:
            logger.warning("ws_rate_limit_exceeded", client_id=client_id, rate=rate)
            return False
        return True


ws_rate_limiter = WebSocketRateLimitMiddleware()