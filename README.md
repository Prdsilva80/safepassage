# 🛡️ SafePassage

> War zone civilian safety & evacuation coordination platform.  
> Real-time incident reports, safe routes, shelter discovery, SOS alerts, AI-powered evacuation plans, and satellite conflict intelligence.

SafePassage is designed to help civilians, NGOs and humanitarian organisations coordinate life-saving information during conflict or disaster situations.

---

## Mission

> *In crisis situations, information saves lives.*

SafePassage provides:

- 📍 Real-time conflict reports from civilians on the ground
- 🛰️ Satellite heat/explosion detection via NASA FIRMS (VIIRS/MODIS)
- 🌐 Humanitarian intelligence aggregation (ReliefWeb, GDELT, UCDP)
- ⚠️ Composite danger scoring engine (4-source intelligence fusion)
- 🆘 Civilian SOS alerts with multilingual support
- 🏠 Shelter discovery and capacity tracking
- 🤖 AI-assisted evacuation planning (Anthropic Claude)
- 📞 Emergency contacts directory (ICRC, UNHCR, MSF, IRC, OCHA)
- 🌍 Multilingual interface (EN, UK, AR, FR, ES, PT/BR)

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI (async) |
| Database | PostgreSQL 16 · SQLAlchemy 2.0 async |
| Cache / Pub-Sub | Redis 7 |
| AI | Anthropic Claude (claude-sonnet-4) |
| Auth | JWT (python-jose) + bcrypt |
| Real-time | WebSocket + Redis pub/sub |
| Frontend | React 18 · Vite · Leaflet.js |
| Translation | LibreTranslate (self-hosted, 6 languages) |
| Containerisation | Docker + Docker Compose |

---

## Intelligence Sources

SafePassage aggregates data from 4 independent sources to calculate a composite danger score:

| Source | Type | Update Frequency | Used For |
|---|---|---|---|
| [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) | Satellite (VIIRS/MODIS) | ~minutes | Heat anomalies, explosions, fires |
| [ReliefWeb](https://reliefweb.int/) | Humanitarian reports | Daily | Crisis reports, disaster alerts |
| [GDELT](https://www.gdeltproject.org/) | News events (300+ categories) | 15 minutes | Conflict signals, protests, attacks |
| [UCDP](https://ucdp.uu.se/) | Academic conflict dataset | Annual (GED 25.1) | Historical violence baseline |

---

## Danger Score Engine

SafePassage calculates a composite danger score for any location by querying all 4 sources in parallel:

```
GET /api/v1/danger/score?lat=48.5&lng=31.2&radius_km=50
```

**Score breakdown:**

| Source | Max Score | Criteria |
|---|---|---|
| NASA FIRMS | +3 | Hotspots in last 3 days within radius |
| ReliefWeb | +2 | Recent humanitarian reports for region |
| GDELT | +2 | Conflict events in last 24h |
| UCDP | +1 | Historical organised violence |

**Risk levels:**

```
0–1  → LOW
2–3  → MODERATE
4–6  → HIGH
7–8  → CRITICAL
```

**Example response:**

```json
{
  "lat": 48.5,
  "lng": 31.2,
  "score": 5,
  "level": "HIGH",
  "breakdown": {
    "firms":     { "score": 3, "detections": 12, "max": 3 },
    "reliefweb": { "score": 2, "reports": 10,    "max": 2 },
    "gdelt":     { "score": 0,                   "max": 2 },
    "ucdp":      { "score": 0,                   "max": 1 }
  },
  "sources": ["NASA FIRMS", "ReliefWeb", "GDELT", "UCDP"]
}
```

---

## System Architecture

```
Users (Mobile / Web)
        ↓
React Frontend (Leaflet Map + i18n)
        ↓
FastAPI Backend
        ↓
─────────────────────────────────────────
PostgreSQL     (persistent data)
Redis          (real-time pub/sub)
LibreTranslate (self-hosted translation)
─────────────────────────────────────────
        ↓
External Intelligence APIs
─────────────────────────────────────────
NASA FIRMS    (satellite hotspots)
ReliefWeb     (humanitarian reports)
GDELT         (news event stream)
UCDP          (conflict history)
─────────────────────────────────────────
        ↓
AI Engine (Anthropic Claude)
WebSocket alert broadcasting
```

---

## User Roles

### 👤 Civilian
- Submit incident reports
- Trigger SOS alerts with GPS location
- Request AI evacuation plans
- Discover nearby shelters
- Receive real-time alerts
- View satellite hotspots on map
- Use app in native language (8 languages)

### 🏥 NGO / Humanitarian Organisations
- Manage shelters and capacity
- Respond to SOS alerts
- Access emergency contacts directory
- Coordinate evacuations

### 🔧 Administrator
- Manage conflict zones
- Monitor system alerts
- Moderate reports
- Manage users and permissions

---

## Project Structure

```
safepassage/
├── app/                           # FastAPI backend
│   ├── main.py
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings + .env)
│   │   └── security.py            # JWT, password hashing, auth dependencies
│   ├── db/
│   │   ├── database.py            # Async SQLAlchemy engine + session
│   │   └── seed_contacts.py       # Emergency contacts seed data
│   ├── models/
│   │   └── models.py              # ORM models
│   ├── schemas/
│   │   └── schemas.py             # Pydantic schemas
│   ├── services/
│   │   ├── geo_service.py         # Geospatial calculations
│   │   ├── alert_manager.py       # WebSocket manager + Redis pub/sub
│   │   ├── firms_service.py       # NASA FIRMS satellite integration
│   │   ├── reliefweb_service.py   # ReliefWeb humanitarian reports
│   │   ├── gdelt_service.py       # GDELT news event stream
│   │   ├── ucdp_service.py        # UCDP conflict history
│   │   ├── danger_score_service.py# Composite danger score engine
│   │   ├── translation_service.py # LibreTranslate integration
│   │   └── sms_service.py         # Vonage SMS alerts
│   └── api/v1/
│       ├── router.py
│       └── endpoints/
│           ├── auth.py
│           ├── zones.py
│           ├── reports.py
│           ├── shelters.py
│           ├── routes.py
│           ├── sos.py
│           ├── ai.py
│           ├── alerts.py
│           ├── ws.py
│           ├── firms.py           # NASA FIRMS endpoints
│           ├── intelligence.py    # ReliefWeb endpoints
│           ├── contacts.py        # Emergency contacts
│           └── danger.py          # Danger score endpoints
├── frontend/                      # React 18 + Vite frontend
│   └── src/
│       ├── i18n/                  # Multilingual support
│       │   └── locales/           # EN, UK, AR, FR, ES, PT, PT-BR
│       ├── components/
│       │   ├── Navbar.jsx
│       │   └── LanguageSelector.jsx
│       └── pages/
│           ├── MapPage.jsx        # Interactive map with FIRMS layer
│           ├── CivilPage.jsx
│           ├── ContactsPage.jsx
│           └── AdminDashboard.jsx
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Node.js 18+

### 1. Clone repository

```bash
git clone https://github.com/Prdsilva80/safepassanger
cd safepassage
cp .env.example .env
```

Edit `.env` and configure:

```env
SECRET_KEY=your_secret_key_min_32_chars
ANTHROPIC_API_KEY=your_anthropic_key
FIRMS_MAP_KEY=your_nasa_firms_key      # free at firms.modaps.eosdis.nasa.gov/api/map_key/
VONAGE_API_KEY=optional
VONAGE_API_SECRET=optional
```

### 2. Start backend

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| LibreTranslate | http://localhost:5000 |

### 3. Seed emergency contacts

```bash
docker exec safepassage_api python -m app.db.seed_contacts
```

### 4. Start frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at: **http://localhost:5173**

---

## API Endpoints

### Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/anonymous` | Anonymous session |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get user profile |

### Reports

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/reports/` | Submit incident report |
| GET | `/api/v1/reports/nearby` | Retrieve nearby reports |
| POST | `/api/v1/reports/{id}/confirm` | Confirm / contradict report |

### Shelters

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/shelters/nearby` | Find nearby shelters |
| POST | `/api/v1/shelters/` | Create shelter (NGO only) |
| PATCH | `/api/v1/shelters/{id}` | Update shelter capacity |

### SOS

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/sos/` | Trigger SOS |
| PATCH | `/api/v1/sos/{id}/acknowledge` | NGO acknowledges |
| PATCH | `/api/v1/sos/{id}/resolve` | Resolve emergency |
| GET | `/api/v1/sos/active` | Active SOS incidents |

### NASA FIRMS (Satellite)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/firms/hotspots` | Hotspots by country |
| GET | `/api/v1/firms/hotspots/bbox` | Hotspots by bounding box |

**Supported conflict zones:** Ukraine, Gaza, Sudan, Syria, Yemen, Iran, Iraq, Lebanon, Myanmar, Somalia, Ethiopia

### Intelligence

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/intelligence/reports` | ReliefWeb humanitarian reports |
| GET | `/api/v1/intelligence/disasters` | ReliefWeb disaster alerts |

### Danger Score

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/danger/score` | Composite danger score for location |
| GET | `/api/v1/danger/grid` | Danger score grid (heatmap) |

### Emergency Contacts

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/contacts/` | List emergency contacts |

**Pre-seeded organisations:** ICRC, UNHCR, MSF, IRC, OCHA

### AI

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/ai/risk-assessment` | AI evacuation plan |

### WebSocket

```
ws://localhost:8000/api/v1/ws/connect?lat=48.5&lng=31.2&user_id=<uuid>
```

---

## Multilingual Support

SafePassage supports 8 languages with automatic detection:

| Code | Language | Translation Engine |
|---|---|---|
| en | English | Native |
| uk | Ukrainian | LibreTranslate |
| ar | Arabic | LibreTranslate |
| fr | French | LibreTranslate |
| es | Spanish | LibreTranslate |
| pt | Portuguese | LibreTranslate |
| pt-BR | Brazilian Portuguese | LibreTranslate |

SOS messages are automatically translated to English for NGO/admin review, and AI responses are translated back to the civilian's language.

---

## Map Features

The interactive Leaflet map includes:

- 🛰️ **SAT layer** — NASA FIRMS satellite hotspots, colour-coded by intensity (FRP/brightness)
- 🔴 **RPT layer** — Civilian incident reports, colour-coded by danger level
- 🟢 **SHL layer** — Nearby shelters with capacity info
- Layer toggles — each layer can be shown/hidden independently
- Country selector for FIRMS data (1–7 day range)
- Legend with intensity scale

---

## Environment Variables

```env
# Core
SECRET_KEY=                    # min 32 chars
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://safepassage:safepassage_dev@postgres:5432/safepassage

# Redis
REDIS_URL=redis://redis:6379/0

# AI
ANTHROPIC_API_KEY=

# NASA FIRMS (free registration)
FIRMS_MAP_KEY=                 # firms.modaps.eosdis.nasa.gov/api/map_key/

# SMS (optional)
VONAGE_API_KEY=
VONAGE_API_SECRET=
VONAGE_FROM=SafePassage
```

---

## Security

If you discover a vulnerability, please report it responsibly.  
**Do not open public issues for security vulnerabilities.**

---

## Contributing

Contributions from developers, NGOs and humanitarian organisations are welcome.

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

All contributions should follow the existing architecture and coding style.

---

## Ethical Use Disclaimer

This software is intended strictly for **humanitarian and civilian protection purposes**.  
It must not be used for military targeting, surveillance, or offensive operations.

---

## License

MIT License

---

*Built with the belief that the right information at the right moment saves lives.*  
*Open source. Non-profit. For humans.*