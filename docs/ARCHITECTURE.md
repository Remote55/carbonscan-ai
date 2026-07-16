# 🏛 Architecture

> [!CAUTION]
> **Target architecture, not current deployment.** แผนภาพ/ข้อความด้านล่างอาจแสดง WebSocket,
> RunPod Serverless, spatial/marketplace services และ object storage ซึ่งยังเป็น Planned.
> เส้นทางที่ตรวจสอบแล้วใช้ FastAPI async jobs + GET polling + local/shared filesystem และ local worker.
> สถานะปัจจุบันให้ยึด `docs/evidence/core_demo_manifest.json`, `docs/PROJECT_SPEC.md` และ
> `docs/CAPABILITY_MATRIX.md`.

> System architecture, design patterns, and rationale for CarbonScan AI

---

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Tech Stack Rationale](#tech-stack-rationale)
6. [Scalability Considerations](#scalability-considerations)
7. [Security](#security)

---

## System Overview

CarbonScan AI เป็น **distributed system** ที่ใช้ event-driven architecture เพื่อรองรับ:
- **Heterogeneous input** (.las/.laz files หรือ multiple RGB photos)
- **Long-running ML jobs** (5-30 นาที/ไฟล์)
- **Real-time visualization** (3D Viewer in browser)
- **Cost-controlled GPU** (serverless, scale-to-zero)

### Design Principles
1. **Decoupled** — แต่ละ service ทำงานอิสระ
2. **Event-driven** — Job Queue เป็นตัวกลาง
3. **Stateless services** — รัน scale horizontal ได้
4. **Cloud-native** — ไม่มี infra ที่ต้อง self-host
5. **Open standards** — LAS/LAZ, PLY, GeoJSON, COCO

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐         ┌──────────────────────────────┐    │
│  │  Mobile (Flutter)  │         │   Web (Next.js 14)           │    │
│  │  ┌──────────────┐  │         │   ┌──────────────────────┐   │    │
│  │  │ Camera UI    │  │         │   │ 3D Viewer (R3F)      │   │    │
│  │  │ GPS Capture  │  │         │   │ GIS Map (Leaflet)    │   │    │
│  │  │ Species ID   │  │         │   │ Carbon Marketplace   │   │    │
│  │  │ (TFLite)     │  │         │   │ Auth (Supabase)      │   │    │
│  │  └──────────────┘  │         │   └──────────────────────┘   │    │
│  └─────────┬──────────┘         └──────────────┬───────────────┘    │
└────────────┼─────────────────────────────────────┼─────────────────┘
             │  HTTPS / WebSocket                  │
             └────────────────┬────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  FastAPI Service (Railway)                                  │    │
│  │  ─ JWT Auth                                                 │    │
│  │  ─ /api/v1/upload (.las/.laz, photos)                      │    │
│  │  ─ /api/v1/jobs/{id} (status, results)                     │    │
│  │  ─ /api/v1/trees (CRUD + spatial queries)                  │    │
│  │  ─ /api/v1/marketplace (carbon credits)                    │    │
│  │  ─ WebSocket /ws/jobs (progress streaming)                 │    │
│  └─────────────┬───────────────────────────────────┬───────────┘    │
└────────────────┼───────────────────────────────────┼────────────────┘
                 ▼                                   ▼
┌────────────────────────────┐      ┌──────────────────────────────┐
│      DATA LAYER            │      │    QUEUE / WORKER LAYER      │
├────────────────────────────┤      ├──────────────────────────────┤
│  Supabase (PostgreSQL 16)  │      │  Job Queue (Supabase Queues) │
│  ┌────────────────────┐    │      │           │                  │
│  │ PostGIS Extension  │    │      │           ▼                  │
│  │ - trees (with geom)│    │      │  RunPod Serverless GPU       │
│  │ - plots            │    │      │  ┌────────────────────────┐  │
│  │ - users            │    │      │  │ ML Pipeline (PyTorch)  │  │
│  │ - transactions     │    │      │  │ 1. classify_ground     │  │
│  │ - carbon_records   │    │      │  │ 2. tree_segmentation   │  │
│  │ - species_db       │    │      │  │ 3. wood_leaf_seg (PCA) │  │
│  └────────────────────┘    │      │  │ 4. QSM cylinder fit    │  │
│  ┌────────────────────┐    │      │  │ 5. allometric → kgC    │  │
│  │ Supabase Storage   │    │      │  │ 6. species_classifier  │  │
│  │ - .las / .laz      │    │      │  └────────────────────────┘  │
│  │ - .ply (output)    │    │      │           │                  │
│  │ - photos           │    │      │           ▼                  │
│  │ - reports (PDF)    │    │      │  Photogrammetry Worker       │
│  └────────────────────┘    │      │  ┌────────────────────────┐  │
│  ┌────────────────────┐    │      │  │ COLMAP (SfM)           │  │
│  │ Supabase Auth      │    │      │  │ OpenMVS (Dense Recon)  │  │
│  └────────────────────┘    │      │  │ → output .ply file     │  │
└────────────────────────────┘      │  └────────────────────────┘  │
                                    └──────────────────────────────┘
```

---

## Component Details

### 1. Mobile App (Flutter)
**Location:** `apps/mobile/`

**Responsibilities:**
- ถ่ายภาพต้นไม้ multiple angles (30-50 frames)
- เก็บ GPS coordinates (6-decimal precision)
- Tree species classification on-device (TFLite, ResNet18 quantized)
- Upload photos to backend via chunked upload
- แสดงผลลัพธ์ (DBH, Height, Carbon) เมื่อ pipeline เสร็จ

**Key Libraries:**
- `camera` — Native camera access
- `geolocator` — GPS + EXIF metadata
- `tflite_flutter` — On-device ML inference
- `dio` — HTTP client with chunked upload
- `riverpod` — State management
- `freezed` — Immutable data classes

**Anti-fraud:**
- ห้าม upload จาก gallery (lock to live camera only)
- ฝัง EXIF metadata (GPS + timestamp)
- Backend-side dedup (radius 1-2 ม.)

---

### 2. Web Dashboard (Next.js)
**Location:** `apps/web/`

**Responsibilities:**
- B2B Marketplace UI (Industrial users browse + buy carbon credits)
- Community Dashboard (Tree owners เห็นรายได้, ประวัติ)
- 3D Point Cloud Viewer (แสดงต้นไม้ที่แยกใบ/ลำต้นแล้ว)
- GIS Map (GPS pins ทุกต้นที่สแกน, filter ตามภูมิภาค)
- File Upload (.las/.laz ขนาดใหญ่ — tus protocol)
- Auditor Panel (review + approve trees)
- PDF Report Generator

**Key Libraries:**
- `next` 14 (App Router + Server Actions)
- `tailwindcss` + `shadcn/ui`
- `three`, `@react-three/fiber`, `@react-three/drei` — 3D
- `potree-core` — Point cloud rendering
- `react-leaflet` + `leaflet` — GIS map
- `@tanstack/react-query` — Server state
- `zustand` — Client state
- `react-pdf` — PDF generation

**Performance:**
- Use React Server Components for static content
- Stream 3D viewer with progressive loading
- Image optimization (next/image)
- Edge caching for assets

---

### 3. Backend API (FastAPI)
**Location:** `services/api/`

**Responsibilities:**
- REST API + WebSocket
- Auth (JWT via Supabase Auth)
- Job orchestration (push to queue, poll status)
- CRUD for trees, plots, users, transactions
- Spatial queries (PostGIS — "find trees within 1km of X")
- Carbon credit ledger (transactions table)
- Real-time progress updates via WebSocket

**Structure:**
```
services/api/app/
├── main.py              # FastAPI entry
├── core/
│   ├── config.py        # Settings (Pydantic)
│   ├── security.py      # JWT helpers
│   └── database.py      # SQLAlchemy session
├── api/v1/
│   ├── auth.py
│   ├── upload.py
│   ├── jobs.py
│   ├── trees.py
│   ├── marketplace.py
│   └── ws.py            # WebSocket endpoints
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response
├── services/            # Business logic
│   ├── job_dispatcher.py
│   ├── tree_service.py
│   └── carbon_calculator.py
└── runpod_handler.py    # RunPod serverless GPU entry (no Celery)
```

**Key Libraries:**
- `fastapi` + `uvicorn`
- `sqlalchemy[asyncio]` + `asyncpg`
- `geoalchemy2` — PostGIS support
- `pydantic` v2
- `supabase-py` — Storage + Auth
- Supabase Queues (PGMQ) — Postgres-native job queue (no Celery/Redis)

---

### 4. ML Pipeline (Python on GPU)
**Location:** `services/ml/`

**Responsibilities:**
- รับไฟล์ .las/.laz หรือ .ply → output JSON (DBH, Height, Volume, Carbon per tree)
- รัน on RunPod Serverless GPU (A10G / RTX 4090)
- รัน on Google Colab สำหรับ Training/Dev

**Pipeline Steps:**
```python
# pipeline/main.py

def process_point_cloud(input_path, output_path):
    # 1. Read .las file
    cloud = laspy.read(input_path)

    # 2. Classify ground (CSF algorithm)
    cloud = ground_classification.run(cloud)

    # 3. Normalize height (DTM subtraction)
    cloud = normalize_height(cloud)

    # 4. Detect individual trees (Watershed on CHM)
    trees = tree_segmentation.detect(cloud)

    # 5. Wood-Leaf separation (PointNet++ per tree)
    for tree in trees:
        tree = wood_leaf_separation.predict(tree)

    # 6. QSM (cylinder fitting on wood points)
    for tree in trees:
        tree.volume = qsm.compute(tree.wood_points)

    # 7. Allometric carbon calculation
    for tree in trees:
        tree.carbon_kg = allometric.calculate(
            volume=tree.volume,
            species=tree.species,
            dbh=tree.dbh,
            height=tree.height,
        )

    # 8. Output results
    return TreeAnalysisResult(trees=trees)
```

**Photogrammetry Path:**
```python
# scripts/photogrammetry_worker.py

def photos_to_point_cloud(photo_paths, output_ply):
    # 1. COLMAP SfM
    subprocess.run(['colmap', 'automatic_reconstructor', ...])

    # 2. OpenMVS dense reconstruction
    subprocess.run(['DensifyPointCloud', ...])

    # 3. Output as .ply
    return output_ply
```

**Key Libraries:**
- `torch` + `torchvision`
- `open3d` + `open3d-ml`
- `laspy` + `pdal`
- `numpy`, `scipy`, `scikit-learn`
- `pandas` (for allometric DB)

---

### 5. Database (PostgreSQL + PostGIS)
**Hosted on:** Supabase

**Key Tables:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    role TEXT, -- 'community' | 'industrial' | 'auditor'
    created_at TIMESTAMP
);

CREATE TABLE plots (
    id UUID PRIMARY KEY,
    owner_id UUID REFERENCES users(id),
    name TEXT,
    geometry GEOMETRY(POLYGON, 4326),
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

CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    type TEXT, -- 'las_upload' | 'photogrammetry'
    status TEXT, -- 'queued' | 'processing' | 'completed' | 'failed'
    input_url TEXT,
    output_url TEXT,
    progress INT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    buyer_id UUID REFERENCES users(id),
    tree_id UUID REFERENCES trees(id),
    co2eq_kg FLOAT,
    price_thb FLOAT,
    created_at TIMESTAMP
);

CREATE TABLE species_db (
    name_th TEXT PRIMARY KEY,
    name_sci TEXT,
    wood_density_kg_m3 FLOAT,
    allometric_a FLOAT,  -- biomass = a * DBH^b * H^c
    allometric_b FLOAT,
    allometric_c FLOAT,
    source_reference TEXT
);

-- PostGIS indexes
CREATE INDEX idx_trees_location ON trees USING GIST(location);
CREATE INDEX idx_plots_geometry ON plots USING GIST(geometry);
```

📖 ละเอียด: [docs/DATA_MODEL.md](DATA_MODEL.md)

---

## Data Flow

### Flow 1: LAS Upload (Auditor Path)
```
1. User uploads .las file via Web Dashboard
2. Web → API /api/v1/upload (chunked)
3. API uploads file to Supabase Storage
4. API creates Job record (status='queued')
5. API pushes job to Queue
6. RunPod GPU Worker picks up job
7. Worker downloads .las from Storage
8. Worker runs pipeline (5-15 min)
9. Worker uploads .ply (visualization) + results JSON
10. Worker updates Job (status='completed')
11. API notifies Web via WebSocket
12. Web fetches results + renders 3D Viewer
```

### Flow 2: Mobile Photogrammetry (Community Path)
```
1. User opens Flutter App
2. App captures 30-50 photos around tree
3. App captures GPS coordinates
4. App runs on-device species classifier (TFLite)
5. App uploads photos + metadata to API
6. API creates 2 jobs: (a) photogrammetry, (b) processing
7. Worker A: COLMAP/OpenMVS → .ply (~3-5 min)
8. Worker B: ML pipeline on .ply → results
9. App polls Job status, receives results
10. App displays DBH, Height, Carbon kg/yr
```

---

## Tech Stack Rationale

| Choice | Alternative | Why |
|---|---|---|
| **Next.js 14** | Vite + React | App Router + Server Actions + SEO out-of-box |
| **Flutter** | React Native | Better camera/sensor performance, single codebase |
| **FastAPI** | Django REST | Native async, auto-Swagger, Pydantic v2 |
| **PostgreSQL + PostGIS** | MongoDB | Spatial queries critical, ACID for ledger |
| **Supabase** | AWS RDS + S3 + Cognito | All-in-one BaaS, free tier, faster dev |
| **RunPod Serverless** | AWS SageMaker | Cheaper, pay-per-second, simpler |
| **PointNet++** | Transformers (PCT) | Mature, good documentation, fits Colab |
| **COLMAP** | RealityCapture | Open-source, scriptable, free |

📖 ละเอียด: [docs/decisions/0003-tech-stack-selection.md](decisions/0003-tech-stack-selection.md)

---

## Scalability Considerations

### Prototype Phase (NSC submission)
- ~10 users, ~100 jobs/month
- Cost: ~$15/month total
- All free/hobby tiers

### Production Hypothetical
| Component | Scale Strategy |
|---|---|
| Web | Vercel auto-scale, ISR for static pages |
| API | Railway horizontal pods, Redis for cache |
| DB | Supabase Pro ($25/mo), 8GB included |
| ML Worker | RunPod serverless auto-scale (cold start ~30s) |
| Queue | Supabase Queues / Migrate to Redis Streams |
| Storage | S3-compatible, CDN for read-heavy |

---

## Security

### Authentication
- JWT tokens (Supabase Auth)
- Role-based access (community / industrial / auditor / admin)
- Token expiry: 1 hour access, 30 day refresh

### File Upload Security
- Max file size: 500 MB per upload (configurable)
- Allowed extensions: `.las`, `.laz`, `.ply`, `.jpg`, `.png`
- Virus scanning: ClamAV (optional, Phase 4)
- Pre-signed URLs สำหรับ download (15 min expiry)

### Anti-Fraud
- Mobile: camera-only (no gallery upload)
- GPS hash + EXIF validation
- Server-side dedup: trees within 1-2m radius = ตัด
- Audit log for all carbon transactions

### API Rate Limiting
- 60 req/min per user (REST)
- 5 uploads/hour per user
- WebSocket: 100 connections/user

---

## Future Enhancements (Post-NSC)

1. **4D Spatiotemporal Carbon** — Compare year-over-year (Carbon Delta)
2. **Drone Integration** — Direct LAS upload from DJI Matrice
3. **Blockchain Ledger** — Immutable carbon transaction record
4. **Mobile Web** — Progressive Web App สำหรับ users ไม่ install
5. **Multi-language** — English, Lao, Burmese (regional expansion)

---

📖 **See also:**
- [docs/decisions/](decisions/) — All architectural decisions
- [docs/ml/PIPELINE.md](ml/PIPELINE.md) — ML pipeline details
- [docs/API.md](API.md) — Full API reference
