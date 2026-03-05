# 🛡️ SafePassage

> War zone civilian safety & evacuation coordination platform.  
> Real-time incident reports, safe routes, shelter discovery, SOS alerts, and AI-powered personalised evacuation plans.

SafePassage is designed to help civilians, NGOs and humanitarian organisations coordinate life-saving information during conflict or disaster situations.

---

## Mission

> *In crisis situations, information saves lives.*

SafePassage provides:

- 📍 Real-time conflict reports
- 🆘 Civilian SOS alerts
- 🏠 Shelter discovery
- ⚠️ Risk analysis
- 🤖 AI-assisted evacuation planning

The goal is to help civilians reach safety faster and help organisations coordinate responses more effectively.

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
| Containerisation | Docker + Docker Compose |

---

## System Architecture

```
Users (Mobile / Web)
        ↓
React Frontend (Leaflet Map)
        ↓
FastAPI Backend
        ↓
────────────────────────────
PostgreSQL   (persistent data)
Redis        (real-time pub/sub)
AI Engine    (Anthropic Claude)
────────────────────────────
        ↓
WebSocket alert broadcasting
```

**Key architectural features:**
- Async FastAPI backend
- Real-time alert distribution
- AI-powered evacuation guidance
- Geospatial risk analysis
- Resilient fallback behaviour if AI fails

---

## User Roles

### 👤 Civilian
- Submit incident reports
- Trigger SOS alerts
- Request AI evacuation plans
- Discover nearby shelters
- Receive real-time alerts

### 🏥 NGO / Humanitarian Organisations
- Manage shelters
- Update shelter capacity and status
- Respond to SOS alerts
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
│   │   └── database.py            # Async SQLAlchemy engine + session
│   ├── models/
│   │   └── models.py              # ORM models
│   ├── schemas/
│   │   └── schemas.py             # Pydantic schemas
│   ├── services/
│   │   ├── geo_service.py         # Geospatial calculations
│   │   └── alert_manager.py       # WebSocket manager + Redis pub/sub
│   ├── ai/
│   │   └── risk_assessment.py     # Claude AI integration
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
│           └── ws.py
├── frontend/                      # React 18 + Vite frontend
├── tests/
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Node.js 18+

### 1. Clone repository

```bash
git clone https://github.com/Prdsilva80/safepassage
cd safepassage
cp .env.example .env
```

Edit `.env` and configure:

```
SECRET_KEY=
ANTHROPIC_API_KEY=
```

### 2. Start backend

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

### 3. Start frontend

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
| POST | `/api/v1/auth/refresh` | Refresh JWT |
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

### AI

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/ai/risk-assessment` | AI evacuation plan |

### WebSocket

```
ws://localhost:8000/api/v1/ws/connect?lat=48.5&lng=31.2&user_id=<uuid>
```

Used for real-time alerts, conflict updates and emergency notifications.

---

## AI Risk Assessment

**Example request:**

```json
{
  "lat": 48.5,
  "lng": 31.2,
  "group_size": 4,
  "has_children": true,
  "has_vehicle": true,
  "needs_medical_attention": false,
  "language": "en"
}
```

**Example response:**

```json
{
  "risk_level": "high",
  "risk_score": 0.78,
  "summary": "Active conflict zone. 3 artillery incidents reported in the last 6 hours.",
  "evacuation_plan": "1. Head south via main road...",
  "immediate_actions": [
    "Stay away from windows",
    "Keep documents ready",
    "Charge your phone"
  ],
  "avoid_areas": ["City centre", "Main bridge", "Northern highway"],
  "ai_confidence": 0.82
}
```

> If the Anthropic API is unavailable, the system automatically returns a safe fallback response.

---

## Danger Scoring

Reports dynamically affect the danger score of zones:

- Score decays over time (half-life: 12 hours)
- Weighted by report credibility (Wilson score interval)
- Critical reports trigger instant WebSocket alerts

```
0.0 ── 0.20 ── 0.40 ── 0.65 ── 0.85 ── 1.0
SAFE    LOW   MEDIUM   HIGH  CRITICAL
```

---

## Frontend Features

- 🗺️ Interactive Leaflet map with dark theme
- 🔴 Real-time danger visualisation (colour-coded by severity)
- 🆘 Civilian SOS trigger with GPS
- 🤖 AI evacuation planning
- 🏠 Shelter discovery
- 👥 Role-based dashboard (civilian / NGO / admin)
- 📱 Mobile responsive

---

## Running Tests

```bash
docker exec safepassage_api python -m pytest tests/ -v
```

---

## Roadmap

- [ ] PWA with offline support (Service Workers)
- [ ] Push notifications (FCM)
- [ ] Multi-language support (40+ languages)
- [ ] Mobile app (React Native)
- [ ] Mesh networking via WebRTC for low-connectivity zones
- [ ] Satellite communication integration

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