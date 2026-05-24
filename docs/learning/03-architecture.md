# บท 03 — สถาปัตยกรรมระบบ (System Architecture)

> 🎯 **เป้าหมายของบท:** ผู้อ่านจะเข้าใจ "ทำไมเลือก tech แต่ละตัว" และ "data ไหลผ่าน layer ไหนบ้าง"
> 📚 **ความรู้พื้นฐาน:** อ่าน [บท 02](02-core-concepts.md) แล้ว
> ⏱️ **เวลาในการอ่าน:** ~20 นาที

---

## 1. ภาพรวม — 4 Layers

เปิดไฟล์ `docs/proposal/figures/fig09_architecture.png` เพื่อดูภาพประกอบ

ระบบ CarbonScan AI แบ่งเป็น **4 layers** จากบนลงล่าง:

```
[1] INPUT LAYER       — ตัวรับข้อมูลเข้า (LiDAR / Mobile)
[2] WEB/API GATEWAY   — Web Dashboard ↔ Backend API
[3] PROCESSING        — Database + Queue + ML Pipeline (GPU)
[4] OUTPUT            — Certificate + Marketplace + Audit Log
```

**ทำไมแบ่ง layers?**

- **Separation of concerns** — แต่ละ layer ทำงานคนละแบบ จึงควรแยก
- **Scalability** — ถ้าจะเพิ่ม GPU workers ทำได้โดยไม่กระทบ frontend
- **Reusability** — เปลี่ยน Web เป็น mobile dashboard ก็ใช้ API/DB เดิมได้

> 💡 **Analogy:** เหมือนร้านอาหาร
> - Layer 1 = ลูกค้าสั่งอาหาร (เมนู = LiDAR file)
> - Layer 2 = พนักงาน (Web + API)
> - Layer 3 = ครัว (GPU + Pipeline)
> - Layer 4 = จานอาหารที่ส่งให้ลูกค้า (Certificate + Marketplace)

---

## 2. Layer [1] — INPUT LAYER

### 2.1 หน้าที่

รับข้อมูล point cloud จาก 3 แหล่ง (จัดลำดับความสำคัญ):

| Priority | Input | Format | ขนาดทั่วไป | จากใคร |
|---|---|---|---|---|
| 🥇 Primary | LiDAR Upload | `.las`, `.laz`, `.ply` | 50-500 MB | Auditor / Survey Contractor |
| 🥈 Secondary | Mobile Photogrammetry | 30 JPG → `.ply` | 5-30 MB | Smallholder farmer |
| 🥉 Bonus | Existing Inventory CSV | `.csv` | < 1 MB | กรมป่าไม้, projects เก่า |

### 2.2 ทำไม LiDAR เป็น Primary

> 💡 **นี่คือสิ่งที่ pivot จาก v1 — Mobile-first → LiDAR-first**

เหตุผล:
1. **Realistic for production** — auditor มี LiDAR อยู่แล้ว
2. **Accuracy สูง** — DBH error ~1-3 cm vs photogrammetry ~5-10 cm
3. **Scale** — drone LiDAR คลุม 100+ ไร่ใน 1 flight
4. **Industry standard** — ทุก carbon survey ในไทยที่ใช้ LiDAR ใช้ `.las` format

### 2.3 ทำไม Mobile = Secondary

- Smallholder (เกษตรกร < 1 ไร่) ไม่มีงบซื้อ LiDAR
- เปิด accessibility — ทุกคนใช้ระบบได้แม้ไม่มีอุปกรณ์แพง
- เป็น "democratization layer"

> ⚠️ **ข้อจำกัด:** mobile = scan **1 ต้น/session** ใช้ 30-50 รูป → คนเดียวเดินถ่ายป่า 100 ต้นไม่ realistic

---

## 3. Layer [2] — WEB/API GATEWAY

### 3.1 Web Dashboard (Next.js 14)

**ไฟล์:** `apps/web/`

**หน้าที่:**
- ผู้ใช้ login/signup
- อัปโหลด LiDAR file
- ดู 3D viewer + GIS map
- เรียกดูผลลัพธ์ + ดาวน์โหลด certificate
- Marketplace UI

**Tech choices (จาก ADR 0003):**

| ตัวเลือก | ตัดสินใจ | เหตุผล |
|---|---|---|
| **Next.js 14** (App Router) | ✅ ใช้ | RSC + SSR, edge runtime, ระบบนิเวศ React ใหญ่สุด |
| **Tailwind CSS** | ✅ ใช้ | Utility-first, รวดเร็ว, professional |
| **shadcn/ui** | ✅ ใช้ | Copy-paste components, ไม่ใช่ library — แก้ได้ |
| **Three.js + R3F** | ✅ ใช้ | มาตรฐาน WebGL, declarative API |
| **Leaflet** | ✅ ใช้ | Free, mature, OpenStreetMap |
| Material UI / Chakra | ❌ ไม่ใช้ | bundle ใหญ่ + ไม่ flexible เท่า shadcn |
| Vite | ❌ ไม่ใช้ | ไม่มี SSR + ไม่มี App Router |

### 3.2 Backend API (FastAPI)

**ไฟล์:** `services/api/`

**หน้าที่:**
- Authentication (JWT via Supabase)
- รับ upload + เก็บ metadata ลง database
- Dispatch jobs ไปยัง queue
- Return results / progress via REST + WebSocket
- Spatial queries (PostGIS)

**Endpoints หลัก:**

```
GET    /health                     → health check
POST   /api/v1/auth/login         → login
POST   /api/v1/jobs/las           → start LAS upload
POST   /api/v1/jobs/photogrammetry → start photo upload
GET    /api/v1/jobs/{id}          → poll job status
GET    /api/v1/trees              → list trees (spatial filter)
GET    /api/v1/marketplace/plots  → marketplace listings
WS     /api/v1/ws/jobs/{id}       → progress streaming
```

**Tech choices:**

| ตัวเลือก | ตัดสินใจ | เหตุผล |
|---|---|---|
| **FastAPI** | ✅ ใช้ | Native async, auto OpenAPI docs, Pydantic v2 type safety |
| **uvicorn** | ✅ ใช้ | ASGI server, fast |
| **SQLAlchemy 2.0 async** | ✅ ใช้ | Modern type hints, native async |
| **asyncpg** | ✅ ใช้ | Fastest Postgres driver in Python |
| Django REST | ❌ ไม่ใช้ | sync-only, ORM ไม่ทันสมัยเท่า |
| Flask | ❌ ไม่ใช้ | no async, no type safety |
| Express (Node) | ❌ ไม่ใช้ | ML libraries ใน Python ดีกว่า |

---

## 4. Layer [3] — PROCESSING

### 4.1 Database — Supabase (PostgreSQL + PostGIS)

**ทำไมเลือก Supabase:**
- All-in-one: Database + Auth + Storage ในแพ็คเกจเดียว
- Free tier มี 500MB DB, 1GB storage — พอสำหรับ NSC prototype
- มี Row-Level Security (RLS) built-in
- เปิด real-time subscriptions

**Tables หลัก:**

| Table | Purpose |
|---|---|
| `users` | Account + role (community/industrial/auditor) |
| `plots` | แปลงป่า + geometry (POLYGON) |
| `trees` | ต้นไม้รายต้น + location (POINT) + measurements |
| `jobs` | ML pipeline jobs + status + progress |
| `transactions` | การซื้อขาย carbon credits |
| `species_db` | สมการ allometric ของแต่ละ species |
| `audit_log` | Immutable log ทุก mutation |

**PostGIS magic:**

```sql
-- Anti-fraud: หาต้นในรัศมี 2m
SELECT id FROM trees
WHERE plot_id = $1
  AND ST_DWithin(location, ST_MakePoint($lon, $lat)::geography, 2);

-- ใช้ GIST index → fast even ที่ 1M rows
CREATE INDEX idx_trees_location ON trees USING GIST(location);
```

### 4.2 Job Queue — Supabase PGMQ

**ทำไม PGMQ:**
- PostgreSQL-native queue (no extra infra)
- Transactional — push to queue + insert metadata = atomic
- Free tier เพียงพอ

**Flow:**
```
User upload .las → API insert job row → API push to PGMQ
                                     ↓
GPU Worker poll queue → pick up job → process → update job row
                                            ↓
                                     WebSocket notify Web
```

### 4.3 GPU Worker — RunPod Serverless

**ทำไม RunPod:**
- Pay-per-second ($0.39/hr for A10G)
- Scale-to-zero — ไม่มี idle cost
- Docker container support — deploy ของเราได้

**ทำไมไม่ใช้:**
- ❌ AWS SageMaker — แพงและซับซ้อน
- ❌ Google Colab — ไม่เหมาะ production
- ❌ Self-hosted GPU — ลงทุนเครื่อง ฿100,000+ ไม่คุ้ม

**Pipeline ที่ run:**

8 ขั้นใน `services/ml/pipeline/`:
```
1. ground_classification.py     → แยกพื้นดิน
2. height_normalization.py      → ปรับ Z = 0
3. canopy_height_model.py       → CHM raster
4. tree_segmentation.py         → Watershed ITD
5. wood_leaf_separation.py      → PCA/PointNet++
6. qsm.py                       → DBH + Volume
7. species_classifier.py        → ResNet (Phase 2)
8. allometric.py                → → CO₂eq output
```

รายละเอียดแต่ละขั้นอยู่ใน [บท 05-12](04-ml-pipeline-overview.md)

### 4.4 Photogrammetry Worker — COLMAP + OpenMVS

**เฉพาะ path mobile photos:**

```
30 JPG → COLMAP feature matching → sparse cloud + camera poses
       → OpenMVS dense reconstruction → .ply
       → ส่งต่อให้ ML Pipeline (step 1-8) ทำงานต่อ
```

---

## 5. Layer [4] — OUTPUT

ผลลัพธ์ 3 อย่างที่ user ได้รับ:

### 5.1 Verified Carbon Certificate (PDF)

**Format:**
- A4 PDF generated ด้วย `@react-pdf/renderer` (Phase 2) หรือ `weasyprint` (Python)
- ภาษาไทย + อังกฤษ
- มี:
  - Plot info (location, owner, scan date)
  - Per-tree breakdown (species, DBH, height, carbon)
  - Total CO₂eq + price
  - 3D visualization screenshot
  - QR code → verify on platform
  - Reference: TGO 2017 standard

### 5.2 B2B Marketplace Listing

**Web page** ที่:
- โรงงาน browse แปลงที่ขายคาร์บอน
- Filter: ภูมิภาค, species, ราคา, certification
- Detail page: GIS map + 3D viewer + spec sheet
- Mock checkout (สำหรับ NSC) → real payment ใน production

### 5.3 GIS Map + Audit Log

**Web dashboard:**
- Leaflet map แสดงทุกต้น/แปลงใน database
- Filter ตามสถานะ (verified / pending / sold)
- Audit timeline — ทุก mutation มี timestamp + user
- Multi-temporal — เปรียบเทียบ Carbon ปีต่อปี (Additionality)

---

## 6. Data Flow — End-to-End

### Path A — Auditor LiDAR (primary, 80% of traffic)

```
[Auditor] เปิดเว็บ → login → upload .las (300MB)
       ↓
[Web]    POST /api/v1/jobs/las → ได้ tus upload URL
       ↓ resumable chunks
[Supabase Storage] รับไฟล์ + emit event
       ↓
[API] insert jobs row (status=queued) → push PGMQ
       ↓
[RunPod GPU] poll queue → download .las → run pipeline 8 steps
       ↓ (5-15 นาที)
[GPU] upload results JSON + .ply (segmented) → update job row
       ↓
[API] WebSocket push to Web → progress 100%
       ↓
[Web] fetch results → render 3D viewer + table → user ดาวน์โหลด PDF
```

### Path B — Smallholder Mobile (secondary)

```
[Farmer] เปิด app → "Start scan" → camera + GPS
       ↓ ถ่าย 30 รูป
[App]    upload JPG batch → API
       ↓
[Photogrammetry Worker] COLMAP/OpenMVS → .ply
       ↓
[continues like Path A from this point]
```

### Path C — Industrial Buyer (downstream)

```
[Factory] เปิด /marketplace → browse plots → filter
       ↓
[Web] เลือกแปลง → "Buy 100 tCO2eq" → checkout
       ↓
[API] POST /api/v1/marketplace/checkout → insert transaction row
       ↓
[Email] ส่ง PDF receipt + certificate
```

---

## 7. Architectural Decision Records (ADRs)

ทุก decision ใหญ่ของระบบ document ไว้ใน `docs/decisions/` เป็น ADR

### ADR-0001 — Monorepo Structure

**ตัดสินใจ:** ใช้ monorepo (pnpm workspaces + Turborepo)

**ทำไม:**
- 4 components (Web, Mobile, API, ML) ใช้ types/API contracts ร่วมกัน
- Single source of truth สำหรับ documentation
- CI/CD เรียก turbo affected → build เฉพาะที่เปลี่ยน

**Trade-off:** repo ใหญ่ขึ้น (~100MB+) — แต่ทีมเล็กกว่าจะรู้สึกง่ายกว่า split repos

### ADR-0002 — No iPhone LiDAR Path

**ตัดสินใจ:** ไม่ทำ iPhone LiDAR app

**ทำไม:**
- iPhone Pro LiDAR ระยะ < 5 ม. — scan ต้นสูง 20 ม. ไม่ได้
- ทีมไม่มี Mac เพื่อ build iOS app
- ตลาด Android ใหญ่กว่า

### ADR-0003 — Tech Stack Selection

ดูตารางในข้อ 3.1 + 3.2 ข้างบน

### ADR-0004 — Dual-Input Architecture

**ตัดสินใจ:** รับทั้ง LiDAR (primary) และ Mobile photogrammetry (secondary)

**ทำไม:**
- LiDAR = professional accuracy + scalable แต่ค่าอุปกรณ์แพง
- Mobile = democratization layer
- ทั้ง 2 → .ply → same ML pipeline = code reuse 90%

### ADR-0005 — Cloud GPU Strategy

**ตัดสินใจ:** RunPod Serverless, not self-host

**ทำไม:**
- ทีมไม่มีเงินซื้อ RTX 4090 (~฿100k)
- RunPod pay-as-you-go = $40/เดือนระหว่าง NSC
- Scale-to-zero — ไม่ใช้ก็ไม่จ่าย

### ADR-0006 — Team Ownership

**ตัดสินใจ:** Codeowners แบ่งตาม layer

```
apps/web/          → Person A
apps/mobile/       → User
services/api/      → User
services/ml/       → User
packages/design-tokens/ → Person B
```

**ทำไม:** ทีมเล็ก 3 คน — User รับงานเทคนิคหนัก (50%), Person A web (30%), Person B design (20%)

---

## 8. Scalability Considerations

### NSC Phase (prototype)
- ~10 users, ~100 jobs/เดือน
- Cost ~$15-50/เดือน
- All free/hobby tiers

### Production Hypothetical
| Component | Scale Strategy |
|---|---|
| Web | Vercel auto-scale, ISR |
| API | Railway horizontal pods + Redis cache |
| DB | Supabase Pro $25/mo, 8GB |
| ML Worker | RunPod auto-scale (cold start ~30s) |
| Queue | Migrate to Redis Streams ที่ scale ใหญ่ |
| Storage | S3-compatible + CDN |

---

## 9. Security Considerations

| Layer | Threat | Mitigation |
|---|---|---|
| **Auth** | Token theft | JWT short-lived (1 hr), refresh 30 days |
| **Upload** | Malicious file | Max 500MB, allowed `.las/.laz/.ply/.jpg/.png` |
| **API** | DDoS | Rate limit (60 req/min) per user |
| **DB** | Unauthorized read | RLS policies per table |
| **Mobile** | Fake GPS | EXIF check + server dedup |
| **Audit** | Data tampering | Append-only audit_log + cryptographic hash chain (Phase 2) |

---

## 10. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไมแบ่งเป็น 4 layers แทนที่จะรวม Web + API เป็นตัวเดียว?**
   - hint: ข้อ 1 (separation of concerns)

2. **ทำไม LiDAR เป็น primary input ไม่ใช่ mobile?**
   - hint: 2.2

3. **PostGIS ให้อะไรเราที่ PostgreSQL ปกติให้ไม่ได้?**
   - hint: 4.1

4. **ทำไมใช้ Supabase PGMQ ไม่ใช้ Redis/RabbitMQ?**
   - hint: 4.2

5. **Cost estimate ของ NSC vs production scale ต่างกันยังไง?**
   - hint: 8

6. **ADR-0002 บอกว่าไม่ทำ iPhone LiDAR — เหตุผลคืออะไร?**
   - hint: 7

---

## 11. อ่านต่อ

- [บท 04 — ภาพรวม ML Pipeline 8 ขั้น](04-ml-pipeline-overview.md)
- [บท 12 — สูตรคาร์บอน (Allometric) ⭐](12-ml-step8-allometric.md)
- [บท 14 — Frontend Web (Next.js + Three.js)](14-frontend-web.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
