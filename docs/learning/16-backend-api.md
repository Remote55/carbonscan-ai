# บท 16 — Backend API (FastAPI + PostgreSQL + PostGIS)

> 🎯 **เป้าหมาย:** เข้าใจ API stack + spatial queries + WebSocket
> 📚 **พื้นฐาน:** [บท 03 — Architecture](03-architecture.md)
> ⏱️ **เวลา:** ~25 นาที

---

## 1. API ทำอะไร

📂 **`services/api/`** — FastAPI service

**Endpoints หลัก:**

```
GET    /health                     → health check
POST   /api/v1/auth/login         → JWT login (via Supabase)
POST   /api/v1/jobs/las           → start .las upload
POST   /api/v1/jobs/photogrammetry → start photo upload
POST   /api/v1/jobs/{id}/confirm  → confirm upload + queue
GET    /api/v1/jobs/{id}          → poll job status
GET    /api/v1/trees              → list trees (spatial filter)
GET    /api/v1/trees/{id}         → tree detail
GET    /api/v1/marketplace/plots  → marketplace listings
POST   /api/v1/marketplace/checkout → buy carbon credits
WS     /api/v1/ws/jobs/{id}       → progress streaming
```

---

## 2. Tech Stack

### 2.1 Core

| Library | Purpose |
|---|---|
| **FastAPI** 0.111 | Web framework |
| **uvicorn** | ASGI server |
| **Python** 3.11+ | Language |

**ทำไม FastAPI:**
- ✅ **Native async** — ดี for I/O bound (database, HTTP)
- ✅ **Auto OpenAPI docs** — `/docs` พร้อมใช้
- ✅ **Pydantic v2** — type-safe input/output
- ✅ **Dependency injection** — clean code

### 2.2 Database

| Library | Purpose |
|---|---|
| **SQLAlchemy** 2.0 (async) | ORM |
| **asyncpg** | Postgres async driver (fastest) |
| **geoalchemy2** | PostGIS support |
| **alembic** | Migrations |

### 2.3 Auth + Storage

| Library | Purpose |
|---|---|
| **supabase-py** | Supabase client (auth, storage) |
| **python-jose** | JWT decode |
| **pydantic-settings** | Env var config |

### 2.4 Testing

| Library | Purpose |
|---|---|
| **pytest** | Test framework |
| **pytest-asyncio** | Async tests |
| **httpx** | Async HTTP client (for testing) |

---

## 3. Folder Structure

```
services/api/
├── app/
│   ├── main.py                 # FastAPI entry
│   ├── core/
│   │   ├── config.py          # Settings (Pydantic)
│   │   ├── security.py        # JWT helpers
│   │   ├── database.py        # SQLAlchemy session
│   │   └── exceptions.py
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── auth.py
│   │   ├── upload.py
│   │   ├── jobs.py
│   │   ├── trees.py
│   │   └── ws.py
│   ├── models/                # SQLAlchemy ORM
│   ├── schemas/               # Pydantic request/response
│   └── services/              # Business logic
├── migrations/                # Alembic
├── tests/
├── pyproject.toml
└── .env.example
```

---

## 4. Database Schema (PostGIS)

### 4.1 Tables Overview

```sql
-- 6 tables + 1 audit table
users           — accounts + role
plots           — แปลงป่า (POLYGON)
trees           — ต้นไม้ (POINT)
jobs            — ML jobs
transactions    — carbon credit sales
species_db      — allometric coefficients
audit_log       — immutable change log
```

### 4.2 Spatial Columns

```sql
CREATE TABLE plots (
    id UUID PRIMARY KEY,
    owner_id UUID REFERENCES users(id),
    name TEXT,
    geometry GEOMETRY(POLYGON, 4326),  -- WGS84
    created_at TIMESTAMP
);

CREATE TABLE trees (
    id UUID PRIMARY KEY,
    plot_id UUID REFERENCES plots(id),
    species TEXT,
    location GEOMETRY(POINT, 4326),
    dbh_cm FLOAT,
    height_m FLOAT,
    volume_m3 FLOAT,
    biomass_kg FLOAT,
    carbon_kg FLOAT,
    co2eq_kg FLOAT,
    point_cloud_url TEXT,
    scanned_at TIMESTAMP,
    last_verified_at TIMESTAMP
);

-- Spatial indexes (GIST = mandatory for performance)
CREATE INDEX idx_trees_location ON trees USING GIST(location);
CREATE INDEX idx_plots_geometry ON plots USING GIST(geometry);
```

### 4.3 Spatial Queries (ตัวอย่าง)

**Find trees within 1km of point:**
```sql
SELECT id, species, dbh_cm
FROM trees
WHERE ST_DWithin(
    location,
    ST_MakePoint(98.9853, 18.7883)::geography,
    1000  -- meters
);
```

**Trees inside a plot:**
```sql
SELECT t.*
FROM trees t
JOIN plots p ON t.plot_id = p.id
WHERE ST_Within(t.location, p.geometry)
  AND p.id = $plot_id;
```

**Distance between 2 trees:**
```sql
SELECT ST_Distance(
    a.location::geography,
    b.location::geography
) AS meters
FROM trees a, trees b
WHERE a.id = $a_id AND b.id = $b_id;
```

---

## 5. WebSocket (Real-time Progress)

```python
@router.websocket("/jobs/{job_id}")
async def job_progress(ws: WebSocket, job_id: UUID):
    await ws_manager.connect(job_id, ws)
    try:
        while True:
            data = await ws.receive_json()
            # Keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, ws)

# When GPU worker finishes a step:
await ws_manager.broadcast(job_id, {
    "type": "progress",
    "stage": 3,
    "stage_name": "tree_segmentation",
    "percent": 45,
})
```

---

## 6. Authentication Flow

```
1. User login on Web → POST /api/v1/auth/login (email, password)
2. Supabase Auth validates → returns JWT (15-min access + 30-day refresh)
3. Web stores JWT in HTTP-only cookie
4. Each API request includes: Authorization: Bearer <JWT>
5. API middleware decodes JWT → extract user_id, role
6. Endpoint uses user_id for queries (RLS in Postgres enforces access)
```

---

## 7. Row-Level Security (RLS)

Supabase Postgres = RLS enabled per table.

**Example policy:**
```sql
-- Users can only see their own trees
CREATE POLICY trees_owner_select ON trees
FOR SELECT
USING (
    plot_id IN (
        SELECT id FROM plots WHERE owner_id = auth.uid()
    )
);

-- Auditors see all
CREATE POLICY trees_auditor_select ON trees
FOR SELECT
USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'auditor')
);
```

> 💡 **RLS = enforce ที่ database** — แม้ API bug ก็ปลอดภัย

---

## 8. Job Queue Integration

```python
# services/api/app/services/job_dispatcher.py

class JobDispatcher:
    async def dispatch(self, job: Job):
        # Push to PGMQ queue
        await pgmq.send(
            queue='ml_pipeline',
            message={
                'job_id': str(job.id),
                'type': job.type,
                'input_url': job.input_url,
            }
        )
```

**On RunPod GPU worker side:**
```python
# services/ml/worker.py
while True:
    msg = pgmq.poll('ml_pipeline', timeout=30)
    if msg:
        process_job(msg)
        pgmq.ack(msg)
```

---

## 9. Running Locally

```bash
cd services/api
poetry install
poetry run alembic upgrade head    # apply migrations
poetry run uvicorn app.main:app --reload --port 8000

# Swagger UI: http://localhost:8000/docs
```

---

## 10. Tests

```bash
poetry run pytest -v --cov
# Target: 80% coverage on services/ layer
```

**Test database:** SQLite in-memory (fast) for unit tests, real Postgres for integration

---

## 11. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไม FastAPI ไม่ใช่ Django REST Framework?**
2. **asyncpg ดียังไงเทียบ psycopg2?**
3. **GIST index คืออะไร? ทำไม mandatory สำหรับ spatial queries?**
4. **RLS แก้ปัญหาอะไร ที่ API alone ทำไม่ได้?**
5. **PGMQ ดียังไงเทียบ Redis/RabbitMQ?**

---

## 12. อ่านต่อ

- [บท 17 — Data Flow End-to-End](17-data-flow.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
