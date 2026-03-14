# SafePassage — Architecture

## Overview

SafePassage is built as a multi-layer platform combining real-time civilian reporting, satellite intelligence, and AI-assisted decision support.

## Backend

FastAPI async application running on Python 3.12. All I/O is non-blocking — database queries, external API calls, WebSocket broadcasting, and AI requests all run concurrently via asyncio.

Key design decisions:
- **Async SQLAlchemy 2.0** with asyncpg driver for PostgreSQL
- **Redis pub/sub** for real-time alert broadcasting to WebSocket clients
- **Circuit breakers** on all external dependencies (DB, Redis, AI, APIs)
- **Structured logging** via structlog with JSON output in production
- **Prometheus metrics** exposed at `/metrics`

## Frontend

React 18 with Vite, Leaflet.js for maps, i18next for multilingual support. Communicates with the backend via REST API and WebSocket.

## Data Flow — SOS Alert

```
Civilian triggers SOS (CivilPage)
        │
        ▼
POST /api/v1/sos/
        │
        ├── Save to PostgreSQL
        ├── Translate message to English (LibreTranslate)
        ├── Send SMS via Vonage (if configured)
        └── Publish to Redis channel safepassage:alerts
                │
                ▼
        WebSocket manager broadcasts to all
        connected clients in radius
```

## Data Flow — Danger Score

```
GET /api/v1/danger/score?lat=&lng=&radius_km=
        │
        ▼ (parallel via asyncio.gather)
┌───────┬───────┬───────┬───────┐
FIRMS  ReliefWeb GDELT  UCDP
  │        │       │      │
  └────────┴───────┴──────┘
                │
        Composite score (0–8)
                │
        Level: LOW / MODERATE / HIGH / CRITICAL
```

## Deployment

- **Development:** `docker compose up` with bind mount for hot reload
- **Production:** `docker compose -f docker-compose.prod.yml up --build`

In production, the Vite frontend should be built and served as static files via nginx or a CDN.