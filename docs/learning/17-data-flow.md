# บท 17 — Data Flow: End-to-End User Journey

> 🎯 **เป้าหมาย:** เห็นภาพรวม "ข้อมูลไหลผ่าน layers ยังไง" สำหรับแต่ละ user type
> 📚 **พื้นฐาน:** [บท 03 — Architecture](03-architecture.md), [บท 14-16](14-frontend-web.md)
> ⏱️ **เวลา:** ~25 นาที

---

## 1. 3 User Paths

| Path | User Type | Input | Use Case |
|---|---|---|---|
| **A** | Auditor (primary) | LiDAR .las upload | ตรวจสอบป่าจริงระดับมืออาชีพ |
| **B** | Smallholder (secondary) | Mobile 30 JPG | เกษตรกร < 1 ไร่ |
| **C** | Industrial Buyer | Browse marketplace | ซื้อ carbon credits |

---

## 2. Path A — Auditor LiDAR Upload

### 2.1 Sequence Diagram

```
User                Web              API           Storage      Queue        GPU            DB
  │                  │                │              │            │           │              │
  ├─Login───────────►│                │              │            │           │              │
  │                  ├─JWT check─────►│              │            │           │              │
  │                  │◄─OK + cookies──┤              │            │           │              │
  │                  │                │              │            │           │              │
  ├─Upload .las─────►│                │              │            │           │              │
  │                  ├─POST /jobs/las─────────────►│              │            │           │              │
  │                  │                │              │            │           │              │
  │                  │                ├─Insert Job (status=AWAITING_UPLOAD)──────────────────►│
  │                  │                │              │            │           │              │
  │                  │                ├─Generate tus URL──────►│              │            │           │              │
  │                  │◄─{job_id, url}─┤              │            │           │              │
  │                  │                │              │            │           │              │
  ├─Chunked upload──►│                ├──Stream chunks──────────►│            │           │              │
  │ (resumable)      │                │              │            │           │              │
  │                  │                │              │            │           │              │
  │                  ├─POST /jobs/{id}/confirm─────►│              │            │           │              │
  │                  │                ├─Push to PGMQ────────────────────────►│              │              │
  │                  │                ├─Update Job (status=QUEUED)──────────────────────────►│
  │                  │◄─{status=queued}┤             │            │           │              │
  │                  │                │              │            │           │              │
  │◄─WS connect──────┤                │              │            │           │              │
  │                  ├─WS /ws/jobs/{id}──►│         │            │           │              │
  │                  │                │              │            │           │              │
  │                  │                │              │            │  ◄─poll──┤              │
  │                  │                │              │            │  pickup  │              │
  │                  │                │              │            ├──msg────►│              │
  │                  │                │              │            │           ├─Download .las│
  │                  │                │              │  ◄─stream──┤───────────┤              │
  │                  │                │              │            │           │              │
  │                  │                │              │            │           ├─Run pipeline │
  │                  │                │              │            │           │   step 1...8 │
  │                  │                │              │            │           │              │
  │                  │                │              │            │           ├─Update Job   │
  │                  │                │              │            │           │   progress=X ►│
  │                  │◄─WS broadcast────────────────────────────────────────────┤             │
  │                  │ progress=X     │              │            │           │              │
  │                  │                │              │            │           │              │
  │                  │                │              │            │           ├─Upload .ply +│
  │                  │                │              │            │           │   results JSON│
  │                  │                │              │            │           │              │
  │                  │                │              │            │           ├─Update Job   │
  │                  │                │              │            │           │   status=DONE►│
  │                  │◄─WS complete──────────────────────────────────────────────┤            │
  │                  │                │              │            │           │              │
  ├─Refresh─────────►│                │              │            │           │              │
  │                  ├─GET /jobs/{id}─►│              │            │           │              │
  │                  │                ├─Query Job + Trees──────────────────────────────────►│
  │                  │◄─JSON─────────┤              │            │           │              │
  │◄─Render 3D + table │              │              │            │           │              │
```

### 2.2 Key Steps สรุป

| Step | Layer | Component | Action |
|---|---|---|---|
| 1 | Web | Login form | User auth via Supabase |
| 2 | API | `/jobs/las` | Create Job row, generate tus URL |
| 3 | Storage | Supabase | Receive chunked upload |
| 4 | API | `/confirm` | Push to PGMQ + update Job |
| 5 | Worker | RunPod GPU | Poll queue, download .las |
| 6 | ML | Pipeline 8 steps | Process point cloud |
| 7 | Storage | Supabase | Upload .ply + results JSON |
| 8 | DB | Postgres | Update Job + insert tree rows |
| 9 | API | WebSocket | Broadcast progress + complete |
| 10 | Web | 3D Viewer | Render results |

### 2.3 Latency Budget

```
Upload (300MB LAS, 4G):     ~60 sec
Queue wait:                 ~5 sec
Download to GPU:            ~10 sec
ML pipeline (5-15 trees):   ~3-5 min
Upload results:             ~5 sec
─────────────────────────────────
Total user wait:            ~4-6 minutes
```

---

## 3. Path B — Smallholder Mobile

### 3.1 Flow

```
1. User opens app → tap "เริ่มสแกนต้นไม้"
2. TreeScanScreen → checklist 4 ข้อ → tap "เปิดกล้อง"
3. CameraScreen:
     - Request permissions (camera + GPS)
     - Initialize CameraController
     - Show live preview
     - Auto-capture every 1.5 sec (or manual shutter)
     - GPS captured per frame, embedded in EXIF
     - Counter: X / 30
4. หลัง 30 ภาพ → "Send Photos"
5. Upload to API:
     POST /api/v1/jobs/photogrammetry
     Body: { photos: [base64], gps: [...], plot_id }
6. API:
     - Insert Job (status=AWAITING_PHOTOGRAMMETRY)
     - Push to photogrammetry queue
7. Photogrammetry worker:
     - COLMAP feature extraction + matching
     - OpenMVS dense reconstruction
     - Output: .ply file
     - Push to ML queue (same as Path A from here)
8. ML Pipeline → Results
9. Notify user via push notification
10. User opens ResultsScreen → see DBH, height, carbon
```

### 3.2 Differences from Path A

| Aspect | Path A (LiDAR) | Path B (Mobile) |
|---|---|---|
| Input size | 50-500 MB | 5-30 MB (30 JPG) |
| Extra step | - | Photogrammetry (3-5 min) |
| Latency | 4-6 min | 8-15 min (longer) |
| Accuracy | High | Medium |

---

## 4. Path C — Industrial Buyer

### 4.1 Flow

```
1. Buyer signup → /marketplace
2. Browse plots:
     GET /api/v1/marketplace/plots?region=north&min_co2=100
3. Plot detail:
     GET /api/v1/marketplace/plots/{id}
     → render 3D viewer + GIS map + spec sheet
4. Buy:
     POST /api/v1/marketplace/checkout
     { plot_id, tco2_amount, payment_method (mock) }
5. API:
     - Insert transaction row
     - Update plot.available_credits -= amount
     - Trigger PDF generation
6. Buyer receives:
     - Email with PDF receipt
     - Certificate (downloadable in dashboard)
     - QR code link to verify
```

---

## 5. Data Flow ของแต่ละ Layer

### 5.1 What Data Moves Where

| Storage | Content | Lifecycle |
|---|---|---|
| **Supabase Storage** (buckets) | .las / .ply / photos / PDFs | 30 days (photos) → keep .ply |
| **Postgres DB** | Metadata, measurements, GIS coords | Forever (audit) |
| **PGMQ Queue** | Job messages (lightweight refs) | Until ack |
| **GPU Worker temp** | Downloaded files, intermediate | Deleted after job |

### 5.2 Data Size Estimates

| Data | Size per item |
|---|---|
| LAS file | 50-500 MB |
| PLY (output) | 10-50 MB |
| Photos batch (30 JPG) | 5-30 MB |
| Results JSON (1 plot, 50 trees) | < 1 MB |
| Tree DB row | < 1 KB |
| Audit log row | < 0.5 KB |
| PDF Certificate | < 2 MB |

---

## 6. Error Handling

| Failure Point | Behavior |
|---|---|
| Upload disconnect | tus auto-resume |
| API down | Mobile retry with exp backoff |
| GPU worker timeout | Queue retry (max 3 attempts) |
| ML pipeline crashes mid-way | Job marked FAILED + Sentry alert |
| WebSocket disconnect | Auto-reconnect |

---

## 7. ❓ คำถามตรวจสอบความเข้าใจ

1. **Path A vs Path B — Latency ต่างกันยังไง? เพราะอะไร?**
2. **WebSocket vs Polling — ทำไมเลือก WebSocket?**
3. **tus protocol แก้ปัญหาอะไรของ chunked upload?**
4. **ทำไมต้องมี "intermediate" PLY ใน Storage?**
5. **ถ้า GPU worker crash กลางทาง → job state เป็นยังไง?**

---

## 8. อ่านต่อ

- [บท 18 — Tools & Hardware](18-tools-hardware.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
