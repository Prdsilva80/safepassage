# 🛡️ SafePassage

> War zone civilian safety & evacuation coordination platform.
> Real-time reports, safe routes, shelter finder, SOS, and AI-powered personalised evacuation plans.

---

## Stack

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
│   │   └── models.py              # ORM models (User, Zone, Report, Shelter, Route, SOS, AlertLog)
│   ├── schemas/
│   │   └── schemas.py             # Pydantic request/response schemas
│   ├── services/
│   │   ├── geo_service.py         # Haversine, bounding box, danger scoring
│   │   └── alert_manager.py       # WebSocket manager + Redis pub/sub
│   ├── ai/
│   │   └── risk_assessment.py     # Anthropic Claude integration with fallback
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
├── frontend/                      # React 18 + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   └── Map.jsx            # Leaflet map (dark theme, click-to-report)
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── MapPage.jsx        # Interactive map with reports + shelters
│   │   │   ├── civil/
│   │   │   │   └── CivilPage.jsx  # SOS trigger + AI risk assessment
│   │   │   └── admin/
│   │   │       ├── AdminDashboard.jsx
│   │   │       └── SheltersAdmin.jsx
│   │   ├── services/
│   │   │   └── api.js             # Axios client with JWT interceptors
│   │   └── context/
│   │       └── AuthContext.jsx
│   └── package.json
├── tests/
│   └── test_core.py
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Node.js 18+

### 1. Clone and configure

```bash
git clone https://github.com/Prdsilva80/pub_erp
cd safepassage
cp .env.example .env
# Edit .env — set SECRET_KEY and ANTHROPIC_API_KEY
```

### 2. Start backend

```bash
docker compose up --build
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

---

## API Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/anonymous` | Anonymous session |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh JWT |
| GET | `/api/v1/auth/me` | Get profile |

### Reports
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/reports/` | Submit incident report |
| GET | `/api/v1/reports/nearby` | Get nearby reports |
| POST | `/api/v1/reports/{id}/confirm` | Confirm / contradict |

### Shelters
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/shelters/nearby` | Find nearby shelters |
| POST | `/api/v1/shelters/` | Create shelter (NGO only) |
| PATCH | `/api/v1/shelters/{id}` | Update capacity/status (NGO only) |

### SOS
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/sos/` | Trigger SOS |
| PATCH | `/api/v1/sos/{id}/acknowledge` | NGO acknowledges |
| PATCH | `/api/v1/sos/{id}/resolve` | Mark resolved |
| GET | `/api/v1/sos/active` | List active SOS (NGO only) |

### AI
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/ai/risk-assessment` | AI evacuation plan |

### WebSocket
```
ws://localhost:8000/api/v1/ws/connect?lat=48.5&lng=31.2&user_id=<uuid>
```

---

## AI Risk Assessment

**Request:**
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

**Response:**
```json
{
  "risk_level": "high",
  "risk_score": 0.78,
  "summary": "Active conflict zone. 3 artillery incidents reported in the last 6 hours.",
  "evacuation_plan": "1. Head south via main road...\n2. Avoid city centre...",
  "immediate_actions": [
    "Stay away from windows",
    "Keep documents ready",
    "Charge your phone"
  ],
  "avoid_areas": ["City centre", "Main bridge", "Northern highway"],
  "ai_confidence": 0.82
}
```

> If the Anthropic API is unavailable, the system returns a safe fallback response automatically.

---

## Danger Scoring

Reports dynamically affect zone danger scores:
- Score decays over time (half-life: 12 hours)
- Weighted by report credibility (Wilson score interval)
- CRITICAL reports trigger immediate WebSocket alerts

```
0.0 ── 0.20 ── 0.40 ── 0.65 ── 0.85 ── 1.0
SAFE    LOW   MEDIUM   HIGH  CRITICAL
```

---

## Frontend Features

- **Map** — Dark Leaflet map · Click anywhere to submit a report · Reports and shelters displayed with colour-coded danger levels
- **Civilian Portal** — SOS trigger with GPS · AI risk assessment with evacuation plan
- **Admin Dashboard** — Active SOS management · Conflict zone creation · Shelter management
- **Auth** — Login · Register · Anonymous civilian access · Role-based routes (civilian / NGO / admin)
- **Mobile responsive** — Works on phones and tablets

---

## Running Tests

```bash
docker exec safepassage_api python -m pytest tests/ -v
```

---

## Roadmap

- [ ] PWA + offline support (Service Workers)
- [ ] Push notifications (FCM)
- [ ] 40+ language support (i18n)
- [ ] Mobile app (React Native)
- [ ] Mesh network via WebRTC for low-connectivity zones

---

*Built with the mission that the right information at the right moment saves lives.*  
*Open source. Non-profit. For humans.*