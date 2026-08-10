# 🔧 API Service (FastAPI)

> [!CAUTION]
> **Mixed current/target service notes.** Source code and tests are authoritative;
> much of the example code below describes a shape this service does not have.
>
> Implemented: `/health`, `/health/pipeline`, synchronous `POST /upload/analyze`,
> `GET /upload/segmented/{id}`, `GET /upload/species`, and `GET /auth/me`.
> Analysis returns the whole result in one response.
>
> Removed rather than planned: the async job queue and worker (nothing called
> them and no deployment started the worker), and the tree/spatial/marketplace
> endpoints — `Tree.location` required WGS84 coordinates and nothing in this
> system produces one, so they could not be implemented as specified. See
> `alembic/versions/0003_drop_jobs.py` and `0004_drop_trees.py`.
>
> Still Planned: direct LAS/photo storage, WebSocket progress, GPU dispatch.

> **Owner:** User
> **Tech:** Python 3.11 + FastAPI + PostgreSQL/PostGIS + Supabase

---

## Overview

Backend API service ที่:
- รับ uploads (.las/.laz, photos)
- จัดการ Auth, Users, Trees, Plots, Transactions
- Push jobs ไปยัง GPU Worker
- ส่ง real-time updates ผ่าน WebSocket
- Spatial queries (PostGIS)

---

## Folder Structure

```
services/api/
├── README.md                         (this file)
├── pyproject.toml                    Dependencies + tool configs
├── alembic.ini
├── Dockerfile
├── .env.example
├── .env                              (gitignored)
├── app/
│   ├── __init__.py
│   ├── main.py                       FastAPI entry
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 Settings (Pydantic)
│   │   ├── security.py               JWT, password hashing
│   │   ├── database.py               SQLAlchemy async session
│   │   └── exceptions.py             Custom exception handlers
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                   FastAPI dependencies (auth, db)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py             Aggregator
│   │       ├── auth.py
│   │       ├── upload.py
│   │       ├── jobs.py
│   │       ├── trees.py
│   │       ├── plots.py
│   │       ├── marketplace.py
│   │       └── ws.py                 WebSocket endpoints
│   ├── models/                       SQLAlchemy ORM
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── tree.py
│   │   ├── plot.py
│   │   ├── job.py
│   │   ├── transaction.py
│   │   └── species.py
│   ├── schemas/                      Pydantic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── tree.py
│   │   └── ...
│   ├── services/                     Business logic
│   │   ├── __init__.py
│   │   ├── job_dispatcher.py         Push to GPU queue
│   │   ├── tree_service.py
│   │   ├── carbon_calculator.py
│   │   ├── marketplace_service.py
│   │   └── storage_service.py        Supabase Storage wrapper
│   └── workers/                      GPU job dispatch (RunPod / Supabase PGMQ)
│       └── __init__.py
├── alembic/                          Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_trees.py
    └── ...
```

---

## Setup

### Prerequisites
- Python 3.11
- PostgreSQL 16 + PostGIS (local or Supabase)

### Install
```bash
cd services/api

# Create virtualenv
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies (editable mode)
pip install -e ".[dev]"

# Copy env
cp .env.example .env
# Edit .env

# Database migrations
alembic upgrade head

# Run dev server
uvicorn app.main:app --reload
# → http://localhost:8000
# → Swagger: http://localhost:8000/docs
```

---

## pyproject.toml

```toml
[project]
name = "carbonscan-api"
version = "0.1.0"
description = "CarbonScan AI Backend API"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "geoalchemy2>=0.15.0",
    "alembic>=1.13.0",
    "supabase>=2.5.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "websockets>=12.0",
    "httpx>=0.27.0",
    "boto3>=1.34.0",
    "reportlab>=4.2.0",          # PDF generation
    "shapely>=2.0.0",            # geometry helpers
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",             # for TestClient
    "ruff>=0.4.0",
    "black>=24.4.0",
    "mypy>=1.10.0",
    "ipython>=8.24.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "B", "ASYNC"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## Key Patterns

### FastAPI Entry
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title="CarbonScan AI API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### Settings (Pydantic)
```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "carbonscan-uploads"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    RUNPOD_API_KEY: str | None = None
    RUNPOD_ENDPOINT_ID: str | None = None

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

settings = Settings()
```

### Async Database Session
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Endpoint Example
```python
# app/api/v1/trees.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.tree import TreeOut, TreeFilters
from app.services.tree_service import TreeService

router = APIRouter(prefix="/trees", tags=["trees"])

@router.get("/", response_model=list[TreeOut])
async def list_trees(
    filters: TreeFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    return await TreeService(db).list(user_id=user.id, **filters.dict())

@router.get("/{tree_id}", response_model=TreeOut)
async def get_tree(
    tree_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await TreeService(db).get(tree_id)
```

### Spatial Query (PostGIS)
```python
# app/services/tree_service.py
from sqlalchemy import select, func
from geoalchemy2 import Geography
from app.models.tree import Tree

class TreeService:
    async def find_nearby(self, lat: float, lon: float, radius_km: float):
        point = func.ST_MakePoint(lon, lat).cast(Geography)
        query = select(Tree).where(
            func.ST_DWithin(
                Tree.location.cast(Geography),
                point,
                radius_km * 1000,  # km to meters
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

### Job Dispatch
```python
# app/services/job_dispatcher.py
import httpx
from app.core.config import settings

class JobDispatcher:
    async def dispatch_las_processing(self, job_id: str, input_url: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.runpod.ai/v2/{settings.RUNPOD_ENDPOINT_ID}/run",
                headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"},
                json={
                    "input": {
                        "job_id": job_id,
                        "las_url": input_url,
                        "callback_url": f"{settings.API_URL}/api/v1/jobs/{job_id}/callback",
                    }
                },
            )
            return response.json()
```

### WebSocket Progress
```python
# app/api/v1/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, ws: WebSocket):
        await ws.accept()
        self.connections.setdefault(job_id, []).append(ws)

    async def broadcast(self, job_id: str, message: dict):
        for ws in self.connections.get(job_id, []):
            await ws.send_json(message)

manager = ConnectionManager()

@router.websocket("/jobs/{job_id}")
async def ws_jobs(ws: WebSocket, job_id: str):
    await manager.connect(job_id, ws)
    try:
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        manager.connections[job_id].remove(ws)
```

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_trees.py -v

# Async tests work automatically (pytest-asyncio)
```

Example test:
```python
# tests/test_trees.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_trees(client: AsyncClient, auth_token: str):
    response = await client.get(
        "/api/v1/trees",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Deployment (Railway)

ดู [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md) section "Backend API"

---

📖 **See also:**
- [docs/API.md](../../docs/API.md) — Full API reference
- [docs/DATA_MODEL.md](../../docs/DATA_MODEL.md) — Database schema
- [services/ml/README.md](../ml/README.md) — ML worker integration
