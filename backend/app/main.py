"""
SafePassage — Main Application (Hardened)

Security layers active:
  ✓ IP blocklist + suspicious path auto-blocking
  ✓ Security headers on every response
  ✓ Request size limits per endpoint
  ✓ Brute force protection (auth endpoints)
  ✓ Token blacklist (replay attack prevention)
  ✓ Audit trail for privileged actions
  ✓ Stack traces never leak to clients

Resilience layers active:
  ✓ Circuit breakers (DB, Redis, AI, external)
  ✓ Graceful degradation (AI/Redis down → safe fallbacks)
  ✓ Stale-while-revalidate cache for read-heavy safety data
  ✓ Bulkhead for AI calls
  ✓ Deep health checks (liveness + readiness + deep)
  ✓ Prometheus metrics
  ✓ Structured JSON logging
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.resilience.resilience import full_health_check
from app.db.database import create_all_tables, engine
from app.middleware.security_middleware import SecurityMiddleware
from app.services.alert_manager import alert_manager

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
        if not settings.is_production
        else structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("safepassage_starting", version=settings.APP_VERSION, env=settings.ENVIRONMENT)
    await create_all_tables()
    await alert_manager.startup()
    health = await full_health_check(engine, alert_manager._redis)
    logger.info("startup_health_check", status=health.get("status"))
    yield
    await alert_manager.shutdown()
    await engine.dispose()
    logger.info("safepassage_shutdown_complete")


app = FastAPI(
    title="SafePassage API",
    version=settings.APP_VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# Middleware stack
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_basic():
    """Liveness probe — fast, no DB."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "connected_clients": alert_manager.connected_count,
    }


@app.get("/health/ready", tags=["Health"], include_in_schema=False)
async def health_ready():
    """Kubernetes readiness probe — checks DB + Redis."""
    result = await full_health_check(engine, alert_manager._redis)
    db_ok = result.get("components", {}).get("database", {}).get("status") == "ok"
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={**result, "ready": False},
        )
    return {**result, "ready": True}


@app.get("/health/deep", tags=["Health"], include_in_schema=False)
async def health_deep():
    """Full deep health check — internal monitoring only."""
    if settings.is_production:
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    from app.core.resilience.resilience import check_ai_health
    base = await full_health_check(engine, alert_manager._redis)
    base["components"]["ai"] = await check_ai_health()
    return base


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=type(exc).__name__, detail=str(exc)[:200])
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An error occurred. Please try again."},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )