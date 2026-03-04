import time
import uuid
from typing import Callable
import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

SUSPICIOUS_PATHS = ["/.env", "/.git", "/wp-admin", "/wp-login", "/phpMyAdmin", "/etc/passwd", "/proc/"]

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        path = request.url.path.lower()

        if any(s in path for s in SUSPICIOUS_PATHS):
            logger.warning("suspicious_path", path=request.url.path)
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 100_000:
            return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content={"detail": "Request too large"})

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("unhandled_error", error=str(exc))
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = str(uuid.uuid4())

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("request", method=request.method, path=request.url.path, status=response.status_code, ms=round(duration_ms, 2))
        return response
