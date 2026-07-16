# 🚀 CarbonScan AI — แผนพัฒนาแอปฉบับละเอียด (Development Blueprint)

> [!NOTE]
> **Historical development blueprint.** รายการและ code snippets ด้านล่างเป็นแผน ไม่ใช่หลักฐานว่า implement แล้ว.
> สถานะปัจจุบัน: async jobs ใช้ polling; WebSocket/GIS/Marketplace/production RunPod = Planned;
> PointNet++ = Experimental/not promoted; Species classifier = Stub. ให้ยึด
> `docs/evidence/core_demo_manifest.json` และ `docs/CAPABILITY_MATRIX.md`.

> **เวอร์ชัน:** 1.0 (2026-05-23)
> **สถานะ:** Phase 0 (Proposal Sprint), Phase 1 จะเริ่ม 30 พ.ค.
> **เป้าหมายของเอกสารนี้:** Blueprint สำหรับทีม 3 คน ที่อ่านแล้วเริ่มลงมือทำงาน **โดยไม่ต้องเดา**

> 📖 อ่าน [ROADMAP.md](ROADMAP.md) ก่อน — เป็น overview ระดับ phase. เอกสารนี้คือ **drill-down** เป็น sprint/file/function ทุกบรรทัด

---

## 0. Table of Contents

1. [Executive Snapshot](#1-executive-snapshot)
2. [สถานะปัจจุบัน — สิ่งที่มีแล้ว](#2-สถานะปัจจุบัน--สิ่งที่มีแล้ว)
3. [Sprint Calendar (24 พ.ค. – 17 ก.ค.)](#3-sprint-calendar)
4. [Mobile App — Build Plan](#4-mobile-app--build-plan)
5. [Web Dashboard — Build Plan](#5-web-dashboard--build-plan)
6. [Backend API — Build Plan](#6-backend-api--build-plan)
7. [ML Pipeline — Build Plan](#7-ml-pipeline--build-plan)
8. [Database & Infra — Build Plan](#8-database--infra--build-plan)
9. [DevOps / CI / Observability](#9-devops--ci--observability)
10. [Cross-Team Integration Points](#10-cross-team-integration-points)
11. [Risk Register + Mitigations](#11-risk-register--mitigations)
12. [Demo Day Preparation (รอบชิง 21 ส.ค.)](#12-demo-day-preparation)
13. [Definition of Done (DoD)](#13-definition-of-done-dod)
14. [Required Hardware / Accounts / Costs](#14-required-hardware--accounts--costs)

---

## 1. Executive Snapshot

### เป้าหมาย 3 ระดับ
| ระดับ | เกณฑ์ | Owner |
|---|---|---|
| 🥉 **Minimum (Must Pass)** | Proposal ส่งทัน, Web Landing ดู Live ได้, Mobile APK boot ได้, ML allometric คำนวณถูกต้อง | ทั้งทีม |
| 🥈 **Target (Should Have)** | Mobile capture photos → upload → API processing → results return, Web 3D Viewer render .ply ได้, Marketplace มี mock data | User + Person A |
| 🥇 **Stretch (Wow)** | Wood-Leaf Segmentation IoU ≥ 0.70, Live demo บนเวที (กดบนแล้วเห็นผล real-time), Demo Video 3 นาทีคุณภาพสตูดิโอ | ทั้งทีม |

### Critical Path สำหรับ User (Lead)
```
Proposal → ML Pipeline (non-AI) → API endpoints → Mobile capture flow
   ↓             ↓                       ↓                  ↓
29 พ.ค.      30 มิ.ย.               14 ก.ค.            17 ก.ค.
```

ทุกอย่างอื่นเป็น **parallel work** ที่ทำพร้อม Critical Path ได้

### Top 3 ความเสี่ยงสูงสุด
1. **User ทำคนเดียวเยอะเกินไป** → ต้อง offload Web ให้ Person A และ Design ให้ Person B จริงๆ ไม่ใช่แค่ formality
2. **GPU Training (PointNet++)** ไม่ได้ผลตามเป้า → Fallback คือ TLSeparation (rule-based) เตรียมไว้ตั้งแต่ Phase 1
3. **iOS build ทำไม่ได้** (ทีมไม่มี Mac) → ทำ Android only, ใส่ "Android first, iOS roadmap" ใน Proposal

---

## 2. สถานะปัจจุบัน — สิ่งที่มีแล้ว

### ✅ Done (จาก PRs #1-10)
- Monorepo + pnpm-workspace + Turbo
- Flutter scaffold + Material 3 theme + go_router + Riverpod
- Next.js 14 + Tailwind + shadcn/ui + Supabase SSR
- FastAPI + async SQLAlchemy 2.0 + PostGIS + Alembic
- Allometric calculator (16/16 tests pass) — `services/ml/`
- 6 ADRs + ROADMAP + ARCHITECTURE + DATA_MODEL + PIPELINE + API + DEPLOYMENT docs
- GitHub: branch protection + CODEOWNERS + 5 CI workflows
- Supabase Auth scaffolding (Web + Mobile-ready)
- RLS policies for trees, plots, jobs, transactions
- Mobile APK build ทำงานได้ (debug) — แก้ Kotlin 2.3 cache + TFLite namespace + manifest merger เมื่อ 23 พ.ค.

### 🟡 Partial
- Mobile screens เป็น UI stubs (HomeScreen, CameraScreen, ResultsScreen, TreeScanScreen) — ยังไม่ wire กับ API/camera จริง
- Web landing page + auth pages — ยังไม่มี dashboard/marketplace
- API endpoints (auth, upload, jobs, trees) — เป็น stubs ทั้งหมด
- ML pipeline — มีโครงสร้าง 8 steps แต่ implement แค่ allometric (step 8)

### ❌ Missing (ต้องทำใน Phase 1-3)
- ทุก feature ใน "Partial" — ต้องทำให้ทำงานจริง
- 3D Point Cloud Viewer
- GIS Map
- Carbon Credit Marketplace
- Photogrammetry worker (COLMAP/OpenMVS)
- Wood-Leaf Segmentation model
- Species Classifier model
- PDF Report Generator
- Production deployment (Vercel + Railway + Supabase prod)

---

## 3. Sprint Calendar

แบ่งเป็น 12 sprints หลังจาก Proposal ส่ง (รวม 49 วัน, 24 พ.ค. – 17 ก.ค.)

| Sprint | Window | Days | Theme | User Focus | Person A Focus | Person B Focus |
|---|---|---|---|---|---|---|
| **S0** | 24–29 พ.ค. | 6 | Proposal + Sign-offs | Proposal v1-final, ลายเซ็น | Login UI, Vercel deploy | Logo final + Diagrams |
| **S1** | 30 พ.ค. – 5 มิ.ย. | 7 | Local Dev Setup | NEON dataset, lidR R study, Postgres local | Auth flow integration | Wireframe Mobile final |
| **S2** | 6–12 มิ.ย. | 7 | ML Steps 1-4 (Geometric) | classify_ground, normalize_height, CHM, watershed | Community Dashboard skeleton | Hi-fi mockups Web |
| **S3** | 13–19 มิ.ย. | 7 | ML Step 5 Fallback + API Wire | TLSeparation (rule-based), `/upload`, `/jobs` real impl | B2B Dashboard skeleton | App Icon + Splash |
| **S4** | 20–26 มิ.ย. | 7 | PointNet++ Training | Annotate + train wood/leaf model | File Upload UI (tus) | Component library handoff |
| **S5** | 27 มิ.ย. – 3 ก.ค. | 7 | QSM + Job Queue | Cylinder fitting, RunPod Docker | 3D Point Cloud Viewer (R3F) | Lottie animations |
| **S6** | 4–10 ก.ค. | 7 | Species Classifier + Map | ResNet train, GIS endpoints | Leaflet GIS Map | Demo Video script |
| **S7** | 11–14 ก.ค. | 4 | Mobile Camera Flow | Camera + GPS + upload pipeline | Tree Detail page | Demo Video record |
| **S8** | 15–16 ก.ค. | 2 | Integration + Polish | E2E smoke test + bug fix | Marketplace + PDF | Demo Video edit |
| **S9** | 17 ก.ค. | 1 | **Submit Final Report** | Final upload SIMs | Final QA + deploy | Submit video |

> 📝 หลัง 17 ก.ค. มี gap 21 วัน ก่อนรอบนำเสนอ (7 ส.ค.) — ใช้เป็น Sprint 10 "Pitching Prep" (Phase 4)

### Sprint Rituals (แนะนำ)
- **เริ่ม sprint:** ประชุม 30 นาทีวันแรก (online ok) — แบ่งงาน + commit ใน TASKS.md
- **กลาง sprint:** ส่งสรุปสั้นใน Line/Discord ทุกวัน "วันนี้ทำ X, พรุ่งนี้ Y, ติด Z"
- **จบ sprint:** ดู PR ที่ merge แล้ว + ของเหลือถูก carry over

---

## 4. Mobile App — Build Plan

### 4.1 ภาพรวม

**Tech:** Flutter 3.44 + Riverpod + go_router + camera + geolocator + dio + supabase_flutter

**Folder structure (ที่มีอยู่แล้ว — ใช้ต่อ):**
```
apps/mobile/lib/
├── main.dart                         # Entry point
├── app.dart                          # MaterialApp.router
├── core/
│   ├── config/
│   │   ├── app_config.dart          # ENV via dart-define
│   │   └── routes.dart              # go_router config
│   ├── theme/
│   │   ├── app_colors.dart
│   │   └── app_theme.dart
│   ├── network/
│   │   └── dio_client.dart
│   └── utils/
│       └── permissions.dart
├── features/
│   ├── auth/                        # 🆕 to add
│   ├── tree_scan/
│   │   └── presentation/tree_scan_screen.dart
│   ├── camera/
│   │   └── presentation/camera_screen.dart
│   ├── results/
│   │   └── presentation/results_screen.dart
│   └── species_id/
│       └── data/species_classifier.dart
└── shared/
    ├── screens/home_screen.dart
    └── widgets/app_button.dart
```

### 4.2 Feature Build Plan (เรียงตามลำดับการทำ)

#### 4.2.1 Auth Feature (S1, 2 วัน)

**ไฟล์ใหม่ที่ต้องสร้าง:**
- `features/auth/data/auth_repository.dart` — wrap Supabase Auth
- `features/auth/application/auth_controller.dart` — Riverpod controller
- `features/auth/presentation/login_screen.dart`
- `features/auth/presentation/signup_screen.dart`
- `features/auth/presentation/widgets/auth_form.dart`

**API Contract:**
```dart
abstract class AuthRepository {
  Future<User?> signIn(String email, String password);
  Future<User?> signUp(String email, String password);
  Future<void> signOut();
  Stream<User?> authStateChanges();
  User? get currentUser;
}
```

**Acceptance:**
- กรอก email/password → กดเข้าสู่ระบบ → ไปหน้า HomeScreen ได้
- ปุ่ม "ออกจากระบบ" ใน HomeScreen → กลับมาที่ LoginScreen
- ปิดแอปเปิดใหม่ → session ยังคงอยู่ (Supabase auto-restore)
- ใส่รหัสผิด 3 ครั้ง → แสดง error message ภาษาไทย

**Tests:**
- Unit: AuthRepository mock + Supabase
- Widget: LoginScreen form validation
- Integration: full sign-in flow (with mocked Supabase)

#### 4.2.2 Camera + GPS Capture (S2-S3, 5 วัน)

**ไฟล์ที่ต้อง implement (ยังเป็น stub):**
- `features/camera/presentation/camera_screen.dart`
- `features/camera/application/camera_controller.dart` 🆕
- `features/camera/data/photo_capture_service.dart` 🆕
- `features/camera/domain/captured_photo.dart` 🆕

**Captured Photo Model:**
```dart
class CapturedPhoto {
  final String localPath;
  final DateTime capturedAt;
  final double latitude;
  final double longitude;
  final double? altitude;
  final double gpsAccuracy;
  final int imageWidth;
  final int imageHeight;
  // EXIF embedded for fraud detection
}
```

**Flow:**
1. `TreeScanScreen` → กด "เปิดกล้องเริ่มสแกน" → ขอ permission CAMERA + LOCATION
2. ถ้า permission denied → แสดง dialog explain + กลับไป settings
3. `CameraScreen` opens — Camera preview, GPS lock indicator
4. ผู้ใช้ tap shutter — capture ภาพ + GPS + EXIF metadata
5. ทุก 1.5 วินาที auto-capture (ตั้ง `Timer.periodic`) — recommended for ความง่าย
6. Counter แสดง `X / 30` (config minimum)
7. ถึง 30 photos → ปุ่ม "ส่งภาพ" activated
8. กด "ส่งภาพ" → upload ไป API → ได้ `jobId` → navigate ไป `ResultsScreen(jobId)`

**Anti-fraud rules (สำคัญสำหรับ NSC narrative):**
- ห้าม pick from gallery — `ImageSource.camera` only
- เก็บ GPS ทุกภาพ — ถ้า accuracy > 20m → warning + ห้ามใช้
- บันทึก `capturedAt` (server time + device time) — backend จะตรวจ drift
- ภาพต้อง resolution ≥ 1280×720

**Acceptance:**
- เปิดกล้องเห็น preview ภายใน 2 วินาที
- Capture 30 ภาพ + GPS ครบ
- ภาพมี EXIF GPS ถูกต้อง (ตรวจด้วย exif package + Test on real device)
- Storage usage < 50MB ต่อการสแกน (jpeg quality 85)

#### 4.2.3 Photo Upload Pipeline (S3, 2 วัน)

**ไฟล์ใหม่:**
- `features/upload/data/upload_repository.dart`
- `features/upload/application/upload_controller.dart`
- `features/upload/domain/upload_progress.dart`

**API call (using dio):**
```dart
// 1. Initiate job
POST /api/v1/jobs/photogrammetry
Body: { "n_photos": 30, "plot_id": "uuid" }
Response: { "job_id": "uuid", "upload_urls": ["...", ...] }

// 2. Upload each photo (presigned URL → Supabase Storage)
PUT {presigned_url}
Body: <jpeg binary>

// 3. Confirm upload complete
POST /api/v1/jobs/{job_id}/confirm
Response: { "status": "queued" }
```

**Resilience:**
- Retry 3 ครั้งต่อภาพถ้า upload fail (exponential backoff: 2s, 5s, 12s)
- ถ้าฉาก app เด้งไป background → upload ต่อด้วย `WorkManager` (Android)
- แสดง progress bar `28 / 30 photos uploaded`
- ถ้า network ขาดเกิน 30 วินาที → แสดง dialog "ลองใหม่" + บันทึก state

**Acceptance:**
- Upload 30 ภาพ (~30MB total) สำเร็จใน < 60s บน 4G
- ถ้าตัด net ระหว่าง upload → resume ได้เมื่อ net กลับมา
- มี toast notification เมื่อ upload เสร็จ + job_id

#### 4.2.4 Results Screen with WebSocket (S4-S5, 3 วัน)

**ไฟล์:**
- `features/results/presentation/results_screen.dart` (มีอยู่ — ต้อง wire จริง)
- `features/results/application/results_controller.dart` 🆕
- `features/results/data/job_ws_client.dart` 🆕

**WebSocket Spec:**
```
WS /api/v1/ws/jobs/{job_id}

Client → Server (after connect):
  { "type": "subscribe" }

Server → Client (every progress update):
  { "type": "progress", "stage": 3, "stage_name": "tree_segmentation", "percent": 45 }

Server → Client (on complete):
  { "type": "complete", "results": { /* full TreeAnalysisResult */ } }

Server → Client (on error):
  { "type": "error", "message": "...", "stage": 4 }
```

**UI Behavior:**
- เข้าหน้านี้ → connect WS ทันที
- แสดง 8 pipeline stages + checkmark when each completes
- มี estimated time remaining
- เมื่อเสร็จ → switch view เป็น results card (DBH, Height, Carbon)
- มี share/save button (Phase 3)

**Acceptance:**
- Connect WS สำเร็จ
- เห็น progress update ทุก stage
- ถ้า disconnect → re-connect อัตโนมัติ
- ถ้า job fail → แสดง error + ปุ่ม "สแกนใหม่"

#### 4.2.5 Species Classifier on-device (S6, 3 วัน, **หลัง model พร้อม**)

> ⚠️ Depends on `services/ml/training/species_classifier.ipynb` finishing in S6

**Re-enable tflite_flutter:**
- Migrate to `litert` or `tflite_flutter_plus` (รุ่นที่แก้ namespace แล้ว)
- เพิ่ม `assets/ml_models/tree_species_v1.tflite` (< 20MB int8)

**Update `species_classifier.dart`:**
```dart
class SpeciesClassifier {
  late Interpreter _interpreter;

  Future<void> load() async {
    _interpreter = await Interpreter.fromAsset(
      'assets/ml_models/tree_species_v1.tflite',
    );
  }

  Future<TopKResult> classifyTop3(File jpegFile) async {
    final imgBytes = await jpegFile.readAsBytes();
    final input = _preprocess(imgBytes); // 224x224, normalize
    final output = List.filled(species.length, 0.0).reshape([1, species.length]);
    _interpreter.run(input, output);
    return _topK(output[0], k: 3);
  }
}
```

**Acceptance:**
- Load model < 500ms
- Inference < 500ms บน Android กลางตลาด (Snapdragon 7-series)
- Top-3 accuracy ≥ 70% บน test set ใน 5 species

#### 4.2.6 Polish & Tests (S8)

- เพิ่ม widget tests สำหรับ 5 screens
- 1 integration test ที่ครอบทั้ง happy path: login → scan → upload → results
- Sentry SDK + crashlytics
- App icon + splash screen final
- Build signed release APK

### 4.3 Mobile Test Strategy

| Layer | Tool | Coverage Target |
|---|---|---|
| Unit | `flutter_test` | 60% — controllers + repos |
| Widget | `flutter_test` + `golden_toolkit` | 5 screens ทั้งหมด |
| Integration | `integration_test` | 1 happy path + 1 auth failure |
| Manual | Real Android device | ทุก feature ต้องทดสอบบนเครื่องจริง |

---

## 5. Web Dashboard — Build Plan

### 5.1 ภาพรวม

**Tech:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + Supabase SSR + React Three Fiber + Leaflet + TanStack Query + Zustand

**Routes ที่ต้องมี:**
```
/                       ← Landing (มีแล้ว)
/login                  ← Auth (มีแล้ว — wire จริง)
/signup
/auth/callback          ← OAuth redirect
/dashboard              ← After login (มี skeleton)
/dashboard/scans        ← รายการ scans ของฉัน
/dashboard/scans/[id]   ← Detail พร้อม 3D Viewer
/dashboard/map          ← GIS map ทุกต้น
/marketplace            ← B2B browse
/marketplace/[plot_id]  ← Detail + checkout
/auditor                ← Auditor panel (role-gated)
/api/...                ← API routes (proxy ถ้าจำเป็น)
```

### 5.2 Feature Build Plan

#### 5.2.1 Auth Integration (S0-S1, Person A)

**Status:** Scaffolding มีแล้ว (PR #8) แต่ flow ยัง broken เพราะ env var mismatch (แก้แล้ว 23 พ.ค.)

**ต้องทำต่อ:**
- `src/app/(auth)/signup/page.tsx` — ถ้ายังไม่มี form
- `src/app/(auth)/login/login-form.tsx` — wire error states (มี shadcn Form แล้ว)
- `src/middleware.ts` — verify redirect logic (มีอยู่ดีแล้ว)
- เพิ่ม Google OAuth provider (optional — nice for demo)

**Acceptance:**
- Sign-up ใน `/signup` → ส่ง confirm email → click link → redirect `/dashboard`
- Sign-in ใน `/login` → redirect `/dashboard`
- ถ้าไม่ login เข้า `/dashboard` → redirect `/login?redirect=/dashboard`

#### 5.2.2 File Upload (.las/.laz) Component (S4, 3 วัน)

**ไฟล์ใหม่:**
- `src/components/upload/PointCloudUploader.tsx`
- `src/lib/upload/tus-client.ts` — wraps `tus-js-client`
- `src/app/(dashboard)/dashboard/upload/page.tsx`

**Why tus protocol:**
- รองรับ resumable upload (ไฟล์ใหญ่ ~500MB)
- ใช้ได้กับ Supabase Storage (Beta) + S3-compatible

**UI:**
- Drag-and-drop zone (react-dropzone)
- File size + name display
- Progress bar with %
- Pause/Resume buttons
- หลัง upload สำเร็จ → ส่งไป `/dashboard/scans/[id]` (จะแสดง pipeline progress)

**API call:**
```ts
// Step 1: Create job
POST /api/v1/jobs/las
Body: { filename, size_bytes, plot_id? }
→ { job_id, upload_url, upload_offset }

// Step 2: Upload via tus
PATCH {upload_url}
Upload-Offset, Content-Type: application/offset+octet-stream

// Step 3: Confirm
POST /api/v1/jobs/{job_id}/confirm
```

#### 5.2.3 3D Point Cloud Viewer ⭐ Wow Feature (S5, 5 วัน, Person A)

> **กรรมการ NSC จะตื่นเต้นมากกับ feature นี้**

**ไฟล์ใหม่:**
- `src/components/viewer/PointCloudCanvas.tsx`
- `src/components/viewer/PointCloudLoader.ts`
- `src/components/viewer/PointCloudMaterial.ts`
- `src/components/viewer/CameraControls.tsx`
- `src/components/viewer/LegendOverlay.tsx`

**Stack:**
- `@react-three/fiber` — React renderer for Three.js
- `@react-three/drei` — Helpers (OrbitControls, Stats)
- `potree-core` — Specifically for **large point clouds** (octree LOD)
- `three` — base lib

**Two render modes:**
1. **Raw mode** — แสดงสีตามความสูง (gradient: green→yellow→red)
2. **Segmented mode** — แสดงสีตาม class: `wood` (brown), `leaf` (green), `ground` (gray)

**Performance Target:**
- รองรับ 5M points
- 60 FPS บน laptop กลาง (Intel Iris Xe)
- Initial load < 5s บน 100Mbps

**UI Controls:**
- Toggle mode (Raw / Segmented)
- Show/hide ground points
- Color picker per class
- Point size slider
- "Reset view" button
- "Take screenshot" button
- Tree info panel (เลือกต้น → แสดง DBH, Height, Volume, Carbon)

**Data format:**
- Server returns `.ply` (Stanford format) or `.las` reduced
- Or stream as binary chunks (XYZ + RGB + class)

**Acceptance:**
- Load 1M points point cloud < 3s
- Orbit smooth (60 FPS)
- Toggle segmentation mode → recolor real-time
- Click tree → highlight + show tooltip

#### 5.2.4 GIS Map with PostGIS (S6, 3 วัน, Person A)

**ไฟล์ใหม่:**
- `src/components/map/TreeMap.tsx`
- `src/components/map/MapMarkers.tsx`
- `src/lib/map/cluster.ts` — client-side clustering helper
- `src/app/(dashboard)/dashboard/map/page.tsx`

**Stack:** `react-leaflet` + `leaflet.markercluster` + OpenStreetMap tiles (free)

**API:**
```
GET /api/v1/trees?bbox=lat1,lon1,lat2,lon2&species=Tectona_grandis
→ GeoJSON FeatureCollection
```

**Features:**
- Markers cluster เมื่อ zoom out
- Filter sidebar: species, date range, carbon range
- Click marker → popup with tree summary
- Heatmap layer toggle (density of trees)
- Export current view as KML/GeoJSON

**Acceptance:**
- 10,000 markers render smoothly
- Filter responsive (< 200ms)
- Click marker → API call returns ใน 100ms (cached)

#### 5.2.5 Tree Detail Page (S7, 2 วัน, Person A)

**ไฟล์ใหม่:**
- `src/app/(dashboard)/dashboard/trees/[id]/page.tsx`
- `src/components/tree-detail/TreeStats.tsx`
- `src/components/tree-detail/CarbonChart.tsx`
- `src/components/tree-detail/PointCloudPreview.tsx`

**Layout:**
- Top: Tree species + photo + GPS + scanned date
- Middle: Big numbers (DBH, Height, Volume, Carbon, CO₂eq)
- Right: Mini 3D viewer
- Bottom: Bar chart (this tree vs species average)
- Bottom: Pipeline metadata (model versions, confidence)

#### 5.2.6 Carbon Credit Marketplace (S8, 4 วัน, Person A)

**ไฟล์ใหม่:**
- `src/app/marketplace/page.tsx` (listing)
- `src/app/marketplace/[plot_id]/page.tsx` (detail + checkout)
- `src/components/marketplace/PlotCard.tsx`
- `src/components/marketplace/CheckoutDialog.tsx`
- `src/lib/marketplace/pricing.ts`

**Listing:**
- Grid of plots
- Each card: name, owner, total CO₂eq, price/tCO₂eq, location
- Filters: region, species, certification status

**Checkout (mock for NSC — no real payment):**
- Quantity selector (tCO₂eq to offset)
- Total price calculation
- "Mock pay" button → record transaction → success page
- Generates PDF receipt

#### 5.2.7 PDF Report Generator (S8, 2 วัน, Person A)

**Stack:** `@react-pdf/renderer`

**Reports:**
1. **Per-tree report** — 1 page (stats + 3D screenshot + map pin)
2. **Per-plot report** — 5-10 pages (summary + per-tree table + carbon trend)
3. **Marketplace receipt** — 1 page (transaction confirmation)

**Acceptance:**
- Generate PDF < 5s
- รองรับ Thai font (Sarabun)
- File size < 2MB

### 5.3 Web Test Strategy

| Layer | Tool | Coverage |
|---|---|---|
| Unit | Vitest + Testing Library | 50% — lib + hooks |
| Component | Vitest + Testing Library | All shared components |
| E2E | Playwright | Critical flows (signup → upload → view results) |
| Visual | (optional) Chromatic | Storybook stories |
| Performance | Lighthouse (in CI) | Performance > 80, A11y > 90 |

---

## 6. Backend API — Build Plan

### 6.1 ภาพรวม

**Tech:** FastAPI 0.111 + uvicorn + async SQLAlchemy 2.0 + asyncpg + PostGIS + Pydantic v2 + Supabase + Redis (optional)

**ไฟล์ที่มีแล้ว:**
```
services/api/app/
├── main.py                  # ✅ done
├── core/
│   ├── config.py           # ✅ done
│   ├── security.py         # ✅ done (JWT helpers)
│   ├── database.py         # ✅ done
│   └── exceptions.py       # ✅ done
├── api/v1/
│   ├── router.py           # ✅ done
│   ├── health.py           # ✅ done
│   ├── upload.py           # 🟡 stub
│   ├── jobs.py             # 🟡 stub
│   └── trees.py            # 🟡 stub
├── models/
│   ├── user.py             # ✅ done
│   └── tree.py             # ✅ done
├── schemas/
│   └── tree.py             # ✅ done
└── tests/                   # 🟡 minimal
```

### 6.2 Endpoint Implementation Plan

#### 6.2.1 Health & Auth Sanity (S1, 1 วัน)

**Routes:**
- `GET /health` ✅
- `GET /api/v1/auth/me` — verify JWT → return user info

**Implementation:**
```python
# app/api/v1/auth.py 🆕
from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
```

#### 6.2.2 Upload Endpoints (S2-S3, 3 วัน)

**Routes:**
- `POST /api/v1/jobs/las` — initiate .las upload, return presigned URL
- `POST /api/v1/jobs/photogrammetry` — initiate photo upload session
- `POST /api/v1/jobs/{job_id}/confirm` — mark upload complete

**Service layer:**
```python
# app/services/upload_service.py 🆕

class UploadService:
    async def create_las_job(
        self,
        user_id: UUID,
        filename: str,
        size_bytes: int,
    ) -> tuple[Job, str]:
        # 1. Validate size < MAX_UPLOAD_SIZE_BYTES
        # 2. Validate extension in ALLOWED_LAS_LIST
        # 3. Create Job row (status=AWAITING_UPLOAD)
        # 4. Generate presigned upload URL (Supabase Storage)
        # 5. Return (job, upload_url)

    async def confirm_upload(self, job_id: UUID, user_id: UUID) -> Job:
        # 1. Verify ownership
        # 2. Check file exists in Storage
        # 3. Set status=QUEUED
        # 4. Push to queue (call JobDispatcher)
        # 5. Return updated Job
```

**Tests (pytest):**
- Happy path: create job → status=AWAITING_UPLOAD
- Reject oversized file → 413
- Reject invalid extension → 422
- Confirm without upload → 409

#### 6.2.3 Job Queue Integration (S5, 3 วัน)

**Options compared:**
| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Supabase Queues (PGMQ) | All-in-one, no extra infra | Beta, less docs | ✅ for prototype |
| Redis + RQ | Mature, fast | Need Redis host | If time |
| Celery + Redis | Industrial-grade | Heavy setup | Skip for NSC |

**Choose:** Supabase PGMQ for S5, can migrate later

**Service:**
```python
# app/services/job_dispatcher.py 🆕

class JobDispatcher:
    async def dispatch(self, job: Job):
        # Push to queue 'ml_pipeline'
        await pgmq.send(
            queue='ml_pipeline',
            message={'job_id': str(job.id), 'type': job.type, 'input_url': job.input_url}
        )
```

**RunPod Worker (separate service — services/ml/worker.py):**
- Polls queue every 5s
- Picks up job → downloads input from Supabase Storage
- Runs `pipeline.process_point_cloud()`
- Uploads result JSON + .ply visualization
- Updates Job row (status, results)
- Sends WebSocket notification

#### 6.2.4 Trees CRUD + Spatial Query (S6, 3 วัน)

**Routes:**
```
GET    /api/v1/trees                  # list (paginated)
GET    /api/v1/trees?bbox=…           # spatial query
GET    /api/v1/trees/{id}             # detail
PATCH  /api/v1/trees/{id}             # update (auditor only)
DELETE /api/v1/trees/{id}             # admin only
GET    /api/v1/trees/{id}/point-cloud # download .ply
```

**Spatial query example:**
```python
@router.get("/", response_model=list[TreeResponse])
async def list_trees(
    bbox: str | None = None,  # "lat1,lon1,lat2,lon2"
    species: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(Tree)
    if bbox:
        lat1, lon1, lat2, lon2 = map(float, bbox.split(','))
        query = query.where(
            func.ST_Within(
                Tree.location,
                func.ST_MakeEnvelope(lon1, lat1, lon2, lat2, 4326)
            )
        )
    if species:
        query = query.where(Tree.species == species)
    query = query.limit(limit)
    return (await db.execute(query)).scalars().all()
```

#### 6.2.5 WebSocket for Job Progress (S5, 2 วัน)

**Route:**
- `WS /api/v1/ws/jobs/{job_id}` — subscribe to progress

**Implementation:**
```python
# app/api/v1/ws.py 🆕

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import ws_manager

router = APIRouter(prefix="/ws", tags=["ws"])

@router.websocket("/jobs/{job_id}")
async def job_progress(ws: WebSocket, job_id: UUID):
    await ws_manager.connect(job_id, ws)
    try:
        while True:
            data = await ws.receive_json()
            # client subscribed, just keep connection alive
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, ws)

# Worker pushes progress via ws_manager.broadcast(job_id, payload)
```

#### 6.2.6 Marketplace Endpoints (S8, 2 วัน)

**Routes:**
```
GET  /api/v1/marketplace/plots
GET  /api/v1/marketplace/plots/{plot_id}
POST /api/v1/marketplace/checkout   # mock for NSC
GET  /api/v1/marketplace/transactions/{tx_id}
```

#### 6.2.7 PDF Report Generation (S8, 1 วัน)

> Frontend handles PDF (react-pdf), but if backend-side needed:
- `POST /api/v1/reports/tree/{tree_id}` → returns PDF URL
- Use `weasyprint` or `reportlab` server-side

### 6.3 API Test Strategy
- pytest-asyncio + httpx AsyncClient
- Test DB: SQLite in-memory for unit, real Postgres for integration
- 80% coverage target on services/ layer
- 100% on critical paths: auth, upload, job dispatch

---

## 7. ML Pipeline — Build Plan

### 7.1 ภาพรวม

**Tech:** Python 3.11 + PyTorch 2.3 + Open3D 0.18 + laspy 2.5 + PDAL + scikit-image + numpy + pandas

**ไฟล์ structure (มีโครงแล้ว — services/ml/):**
```
services/ml/
├── pipeline/
│   ├── main.py                    # 🟡 stub — orchestrate all steps
│   ├── step1_ground.py            # 🆕
│   ├── step2_normalize.py         # 🆕
│   ├── step3_chm.py               # 🆕
│   ├── step4_tree_seg.py          # 🆕
│   ├── step5_wood_leaf.py         # 🆕 (rule-based + DL)
│   ├── step6_qsm.py               # 🆕
│   ├── step7_species.py           # 🆕
│   └── step8_allometric.py        # ✅ DONE (16/16 tests)
├── photogrammetry/
│   ├── colmap_wrapper.py          # 🟡 stub
│   └── openmvs_wrapper.py         # 🟡 stub
├── training/
│   ├── train_wood_leaf.ipynb      # 🆕 PointNet++
│   ├── train_species.ipynb        # 🆕 ResNet
│   └── annotate_helper.py         # 🆕 CloudCompare conversion
├── data/
│   └── species_db.csv             # ✅ DONE
├── worker.py                      # 🆕 RunPod entrypoint
└── tests/
    └── test_allometric.py         # ✅ DONE
```

### 7.2 Per-Step Implementation Plan

#### 7.2.1 Step 1: Ground Classification (S2, 2 วัน)

**Algorithm:** Cloth Simulation Filter (CSF) via PDAL

**Implementation:**
```python
# pipeline/step1_ground.py
import pdal

def classify_ground(input_las: str, output_las: str) -> dict:
    """Use PDAL's filters.csf to classify ground points."""
    pipeline_json = {
        "pipeline": [
            input_las,
            {
                "type": "filters.csf",
                "resolution": 0.5,
                "threshold": 0.5,
                "rigidness": 3,
            },
            output_las,
        ]
    }
    pipeline = pdal.Pipeline(json.dumps(pipeline_json))
    pipeline.execute()
    return {"n_points_ground": ..., "n_points_nonground": ...}
```

**Test:** NEON sample plot → expect ~30% ground points

#### 7.2.2 Step 2: Height Normalization (S2, 1 วัน)

**Algorithm:** Subtract DTM from non-ground points

```python
# pipeline/step2_normalize.py
import laspy
import numpy as np
from scipy.spatial import cKDTree

def normalize_height(input_las: str, output_las: str) -> None:
    las = laspy.read(input_las)
    ground_mask = las.classification == 2
    ground_xy = np.vstack([las.x[ground_mask], las.y[ground_mask]]).T
    ground_z = las.z[ground_mask]

    tree = cKDTree(ground_xy)
    nonground_xy = np.vstack([las.x[~ground_mask], las.y[~ground_mask]]).T
    _, idx = tree.query(nonground_xy, k=3)
    z_terrain = ground_z[idx].mean(axis=1)

    las.z[~ground_mask] -= z_terrain
    las.write(output_las)
```

#### 7.2.3 Step 3: CHM (S2, 2 วัน)

**Algorithm:** Pit-free CHM (Khosravipour 2014)

```python
# pipeline/step3_chm.py
import numpy as np
from scipy.interpolate import griddata

def pit_free_chm(las_points: np.ndarray, resolution: float = 0.5) -> np.ndarray:
    """Build pit-free CHM at given resolution."""
    thresholds = [0, 5, 10, 15, 20, 25, 30]
    chms = []
    for t in thresholds:
        mask = las_points[:, 2] >= t
        if mask.sum() < 10:
            continue
        chm_t = _rasterize_max(las_points[mask], resolution)
        chms.append(chm_t)
    chm_final = np.nanmax(np.stack(chms), axis=0)
    return chm_final
```

**Acceptance:** RMSE < 1m vs validation Ground Truth

#### 7.2.4 Step 4: Tree Segmentation (S2-S3, 2 วัน)

**Algorithm:** Watershed on CHM

```python
# pipeline/step4_tree_seg.py
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.morphology import disk

def detect_individual_trees(chm: np.ndarray, min_height: float = 4.0) -> np.ndarray:
    coords = peak_local_max(chm, min_distance=3, threshold_abs=min_height)
    markers = np.zeros_like(chm, dtype=np.int32)
    for i, (r, c) in enumerate(coords, start=1):
        markers[r, c] = i
    labels = watershed(-chm, markers, mask=chm > min_height)
    return labels  # 0 = background, 1..N = trees
```

**Output:** Per-tree point cloud + treetop coordinates

#### 7.2.5 Step 5a: Wood-Leaf Rule-Based (S3, 3 วัน) — Fallback first

**Why:** ทำได้ก่อนไม่ต้อง train model — ใช้เป็น baseline + fallback

**Algorithm:** TLSeparation (Cembrowski et al.)

```python
# pipeline/step5_wood_leaf.py
import numpy as np
from sklearn.neighbors import NearestNeighbors

def classify_wood_leaf_rulebased(
    tree_points: np.ndarray,  # (N, 3)
    k: int = 20,
) -> np.ndarray:  # (N,) bool — True = wood
    nbrs = NearestNeighbors(n_neighbors=k).fit(tree_points)
    _, indices = nbrs.kneighbors(tree_points)

    is_wood = np.zeros(len(tree_points), dtype=bool)
    for i, neighbors in enumerate(indices):
        cov = np.cov(tree_points[neighbors].T)
        eigvals = np.sort(np.linalg.eigvalsh(cov))[::-1]
        linearity = (eigvals[0] - eigvals[1]) / eigvals[0]
        planarity = (eigvals[1] - eigvals[2]) / eigvals[0]
        # Wood: high linearity, low planarity
        is_wood[i] = linearity > 0.6 and planarity < 0.3
    return is_wood
```

**Acceptance:** IoU > 0.55 บน validation tree set

#### 7.2.6 Step 5b: PointNet++ Deep Learning (S4, 7 วัน)

**Training (Google Colab Pro+):**
- Dataset: NEON forest LiDAR + manual annotation
- ~50-100 annotated trees (use CloudCompare)
- Architecture: PointNet++ MSG (2 layers)
- Loss: cross-entropy + Dice
- Optimizer: AdamW, lr=1e-3, scheduler cosine
- Target: IoU ≥ 0.70

**Inference code:**
```python
# pipeline/step5_wood_leaf_dl.py
import torch
from pointnet2 import PointNet2Segmentor

class WoodLeafSegmenterDL:
    def __init__(self, ckpt_path: str):
        self.model = PointNet2Segmentor(num_classes=2)
        self.model.load_state_dict(torch.load(ckpt_path))
        self.model.eval().cuda()

    @torch.no_grad()
    def predict(self, tree_points: np.ndarray) -> np.ndarray:
        # Downsample if > 8192 points
        sampled = _farthest_point_sample(tree_points, 8192)
        x = torch.from_numpy(sampled).float().unsqueeze(0).cuda()
        logits = self.model(x)
        labels = logits.argmax(dim=-1).cpu().numpy()[0]
        # Upsample labels back to original
        return _knn_upsample(tree_points, sampled, labels)
```

**Fallback chain:**
```python
def classify_wood_leaf(points):
    try:
        return classifier_dl.predict(points)  # try DL first
    except Exception as e:
        log.warning(f"DL fail, falling back: {e}")
        return classify_wood_leaf_rulebased(points)
```

#### 7.2.7 Step 6: QSM Cylinder Fitting (S5, 4 วัน)

**Algorithm:** TreeQSM-inspired (simplified)

```python
# pipeline/step6_qsm.py

def compute_qsm(wood_points: np.ndarray) -> dict:
    # 1. Build skeleton (Laplacian contraction or simpler: octree slicing)
    skeleton = _extract_skeleton(wood_points)

    # 2. Detect branching points
    branches = _detect_branches(skeleton)

    # 3. Fit cylinders per segment
    cylinders = []
    for segment in branches:
        c = _fit_cylinder_ransac(wood_points, segment)
        cylinders.append(c)

    # 4. Sum volumes
    total_vol = sum(c.volume for c in cylinders)
    return {
        "total_volume_m3": total_vol,
        "n_cylinders": len(cylinders),
        "dbh_m": cylinders[0].radius * 2,  # cylinder at 1.3m
        "height_m": wood_points[:, 2].max(),
    }
```

#### 7.2.8 Step 7: Species Classifier Training (S6, 5 วัน)

**Dataset:**
- Scrape iNaturalist + manual collection
- Target: 200 images/species × 5 species + 100 "Unknown" = 1100 images
- Augmentation: rotation, color jitter, cutout

**Training:** Standard ResNet-50 fine-tune (Colab T4)

**Export to TFLite (int8):**
```python
import tensorflow as tf
converter = tf.lite.TFLiteConverter.from_saved_model('export/')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = lambda: ...  # 100 samples
tflite_model = converter.convert()
with open('tree_species_v1.tflite', 'wb') as f:
    f.write(tflite_model)
```

**Acceptance:** Top-1 acc ≥ 85%, model < 20MB

#### 7.2.9 Step 8: Allometric ✅ DONE
> Already implemented in PR #3 + #5, 16/16 tests pass

#### 7.2.10 Photogrammetry Worker (S7, 4 วัน)

**Stack:**
- COLMAP (SfM)
- OpenMVS (Dense reconstruction)

**Implementation:**
```python
# photogrammetry/colmap_wrapper.py

def photos_to_pointcloud(photo_dir: str, output_ply: str) -> dict:
    workspace = tempfile.mkdtemp()
    # Feature extraction
    subprocess.run(['colmap', 'feature_extractor',
        '--database_path', f'{workspace}/db.db',
        '--image_path', photo_dir,
    ], check=True)
    # Feature matching
    subprocess.run(['colmap', 'exhaustive_matcher',
        '--database_path', f'{workspace}/db.db',
    ], check=True)
    # Sparse reconstruction
    subprocess.run(['colmap', 'mapper',
        '--database_path', f'{workspace}/db.db',
        '--image_path', photo_dir,
        '--output_path', f'{workspace}/sparse',
    ], check=True)
    # Dense reconstruction (OpenMVS)
    # ... InterfaceCOLMAP → DensifyPointCloud → ReconstructMesh → output .ply
    return {"n_points": ..., "time_seconds": ...}
```

**Performance target:** 30 photos → .ply ใน 3-5 นาที (RunPod A10G)

### 7.3 Worker Entry Point

```python
# services/ml/worker.py

import json
import time
from pathlib import Path

from pipeline.main import process_point_cloud
from photogrammetry.colmap_wrapper import photos_to_pointcloud
from queue_client import PGMQClient
from storage_client import SupabaseStorage

def main():
    queue = PGMQClient(queue_name='ml_pipeline')
    storage = SupabaseStorage()

    while True:
        msg = queue.poll(timeout=30)
        if not msg:
            continue
        job_id = msg['job_id']
        try:
            if msg['type'] == 'photogrammetry':
                photos = storage.download_batch(msg['photo_urls'], '/tmp/photos')
                ply_path = photos_to_pointcloud('/tmp/photos', '/tmp/out.ply')
                storage.upload(ply_path, f'point-clouds/{job_id}.ply')
                # Then continue to ML pipeline
                msg['type'] = 'ml_pipeline'
                msg['input_url'] = f'point-clouds/{job_id}.ply'

            if msg['type'] == 'ml_pipeline':
                las_path = storage.download(msg['input_url'], '/tmp/input.las')
                results = process_point_cloud(las_path)
                storage.upload_json(results, f'results/{job_id}.json')

            queue.ack(msg)
        except Exception as e:
            log.exception(f"Job {job_id} failed")
            queue.nack(msg)
```

### 7.4 Dataset Strategy

**Phase 1 (S1):** Download NEON sample
- Source: https://data.neonscience.org/data-products/DP1.30003.001
- 1 plot × ~5GB
- ใช้สำหรับ pipeline development + visualization

**Phase 2 (S4):** Manual annotation for wood-leaf training
- Tool: CloudCompare (free, open-source)
- ~50 trees → ~10 hours work
- 80/10/10 split (train/val/test)

**Phase 2 (S6):** Species image dataset
- iNaturalist scrape via API
- Manual cleanup (remove fruit-only, leaf-only filtered)
- 1100 images final

---

## 8. Database & Infra — Build Plan

### 8.1 Current State

✅ **Done (PR #5, #9):**
- 6 tables: users, plots, trees, jobs, transactions, species_db
- PostGIS extension enabled
- GIST indexes on geometry columns
- RLS policies for trees, plots, jobs, transactions
- Alembic migrations

### 8.2 ต้องเพิ่ม

#### 8.2.1 Seed Data (S1, 1 วัน)
- 5 species in `species_db` ✅ already done
- Demo accounts: 1 community, 1 industrial, 1 auditor
- Demo plots: 3 plots (Chiang Mai, Khon Kaen, Nakhon Si Thammarat)
- Demo trees: 50 mocked trees ที่มี location ใน 3 plots

#### 8.2.2 Audit Log Table (S6, 1 วัน)
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    target_table TEXT,
    target_id UUID,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: only admins can read
```

Triggered by FastAPI middleware on every mutation.

#### 8.2.3 Indexes Optimization (S6)
```sql
CREATE INDEX idx_jobs_status ON jobs(status) WHERE status IN ('queued', 'processing');
CREATE INDEX idx_trees_species ON trees(species);
CREATE INDEX idx_trees_scanned_at ON trees(scanned_at DESC);
CREATE INDEX idx_transactions_buyer ON transactions(buyer_id);
```

### 8.3 Storage Buckets (Supabase)

| Bucket | Public | Purpose |
|---|---|---|
| `point-clouds` | No | .las/.laz/.ply files |
| `photos` | No | Original mobile uploads |
| `reports` | No | Generated PDFs |
| `previews` | Yes | Thumbnails (3D screenshots) |
| `species-images` | Yes | Reference images |

**Lifecycle Rules:**
- `photos`: delete original 30 days after job done (keep .ply)
- `point-clouds`: keep indefinitely
- `reports`: keep 1 year

### 8.4 Database Migrations Discipline

- ทุกการเปลี่ยน schema → ผ่าน Alembic migration
- ห้ามแก้ DB schema โดยตรงใน Supabase UI
- Migration เขียน + test ใน dev branch ก่อน push

---

## 9. DevOps / CI / Observability

### 9.1 Current CI (มี 5 workflows ใน .github/workflows/)

✅ Web (Vitest + Build)
✅ API (Ruff + Pytest + PostGIS in Docker)
✅ ML (Pytest + coverage)
✅ Mobile (analyze + test)
✅ CodeQL (security scanning)

### 9.2 ต้องเพิ่ม

#### 9.2.1 Mobile Build Workflow (S1, 1 วัน)
- `flutter build apk --release` on PR to main
- Upload artifact (.apk)
- Run integration tests on Firebase Test Lab (optional)

#### 9.2.2 Deploy Workflows (S1, 2 วัน)
- **Web:** Vercel auto-deploy from main + preview deploys per PR
- **API:** Railway auto-deploy from main
- **Database:** migrations via Alembic on Railway deploy

#### 9.2.3 Observability (S6-S7, 2 วัน)
- **Sentry** for Web (frontend errors)
- **Sentry** for API (backend errors)
- **Sentry** for Mobile (Flutter crashes)
- **Logflare** (or Supabase Logs) for query monitoring
- **Vercel Analytics** for Web Core Web Vitals

#### 9.2.4 Local Dev Convenience

- `docker-compose.dev.yml` — Postgres + PostGIS + Redis + Adminer
- `scripts/setup-local.sh` — install all deps + seed DB
- `Makefile` — common commands (`make dev`, `make test`, `make deploy`)

---

## 10. Cross-Team Integration Points

### 10.1 API Contract Stability

> ทุก endpoint ที่ Person A หรือ Mobile ใช้ → ต้อง freeze schema ใน S3-S4

**Tool:** OpenAPI auto-generated by FastAPI → publish to `/openapi.json`
- Person A: generate TypeScript types via `openapi-typescript`
- Mobile: generate Dart types via `openapi-generator-cli`

**Convention:**
- เปลี่ยน schema breaking → bump API version (`/api/v1` → `/api/v2`)
- เพิ่ม field optional → ok ไม่ต้องเปลี่ยน version

### 10.2 Design Token Sync

**packages/design-tokens/tokens/colors.json** = source of truth

- Web: imported by Tailwind config
- Mobile: ports to `app_colors.dart` (manual sync for now)
- Person B: updates tokens.json → opens PR → both apps pick up

### 10.3 Daily Sync Channel

**แนะนำ:** Line / Discord group ที่ทำงานทุกวัน
- เช้า: post "วันนี้ทำอะไร"
- เย็น: post "เสร็จ X, ติด Y, ขอความช่วยเหลือ Z"
- ใช้ thread reply ในแชนเนล Issue / PR ที่เกี่ยวข้อง

---

## 11. Risk Register + Mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Wood-Leaf PointNet++ train ไม่ผ่าน IoU 0.70 | Medium | High | Fallback rule-based (Step 5a) — เตรียมไว้ตั้งแต่ S3 |
| R2 | RunPod GPU เปิดไม่ติดวันแข่ง | Low | Critical | Cache .ply + results สำหรับ demo video pre-recorded |
| R3 | iOS build ทำไม่ได้ (ไม่มี Mac) | High | Medium | Android only, ใส่ "iOS roadmap" ใน Proposal |
| R4 | Supabase Free Tier เต็ม (500MB DB) | Medium | Medium | Cleanup ทุก week, อัปเกรด Pro ($25) ถ้าเข้าใกล้ limit |
| R5 | Person A ทำ 3D Viewer ไม่ทัน | Medium | High | Pair-program กับ User 1 session, ใช้ potree-core demo |
| R6 | NEON dataset 5GB download ช้าทั้งคน | Low | Medium | Upload mirror บน Drive ทีม |
| R7 | Photogrammetry COLMAP รันไม่ติดบน RunPod | Medium | Medium | Test ใน Colab ก่อน, มี Dockerfile.gpu prebuilt |
| R8 | กรรมการถามเรื่อง regulatory (TGO certificate) | High | Low | เตรียม Q&A: "Phase post-NSC จะขอ TGO certify" |
| R9 | Demo เน็ตล่มวันแข่ง | Medium | Critical | Offline backup: local API + cached data + recorded video |
| R10 | Code crash ระหว่าง demo | Medium | High | "Reset to demo data" button, pre-warm caches |

### Mitigation Workflow

ทุก Risk Level High+ → ต้องมีคำตอบใน 1 ใน 3:
1. **Avoid:** ไม่ทำ feature นี้ — ระบุใน scope cut
2. **Buffer:** ทำให้เร็วกว่า 3-5 วัน เพื่อ debug
3. **Fallback:** มีแผน B ที่ทำงานได้ (เช่น cached demo)

---

## 12. Demo Day Preparation

### 12.1 Demo Storyboard (4 นาที pitching + 4 นาที Q&A)

> สมมุติ NSC ให้เวลา 8-10 นาที per team

**00:00-00:30 — Hook**
> "ปัญหา: คน 1 ตรวจสอบป่า 1 แปลง ใช้เวลา 2 อาทิตย์ + 50,000 บาท. ทีมเราทำใน 10 นาที + ฟรี"

**00:30-01:30 — Problem & Market**
- ทำไมคาร์บอนเครดิตป่าไม้สำคัญ (CBAM, Net Zero)
- Bottleneck คือการวัด
- เกษตรกรเข้าไม่ถึง, โรงงานเสี่ยง greenwashing

**01:30-04:00 — Live Demo**
1. **Open Mobile App** → scan ต้นไม้จริง (กระถางต้นไม้ใหญ่ที่เตรียมไว้)
2. **Switch to Web** → 3D Viewer แสดง point cloud ที่ segmented แล้ว
3. **GIS Map** → zoom เข้า scanned tree
4. **Marketplace** → โรงงานคลิกซื้อ → transaction success

**04:00-04:30 — Tech & Impact**
- "PointNet++ IoU 0.78, ResNet 92% accuracy"
- "ลดต้นทุน 100×, ช่วยเกษตรกร ~300,000 ครัวเรือนเข้าตลาดคาร์บอนได้"

**04:30 — Q&A**

### 12.2 Demo Asset Checklist

- [ ] Demo Video 3 นาที (backup ถ้าเน็ตล่ม)
- [ ] Pre-loaded scans ในระบบ (ไม่ต้อง upload วันแข่ง — เร็วกว่า)
- [ ] 1 ต้นไม้จริง (กระถางใหญ่) สำหรับ live scan
- [ ] Mobile device พร้อม app installed + กล้องชาร์จเต็ม
- [ ] Laptop พร้อม Chrome + Hotspot สำรอง
- [ ] Slide deck 10 slides (Keynote/PPT + PDF)
- [ ] Poster A1 (ถ้ามี booth)
- [ ] นามบัตร 50 ใบ
- [ ] Q&A prep doc (10 questions + answers)

### 12.3 Common Q&A

> เตรียมคำตอบเหล่านี้ — กรรมการชอบเจาะ

| Q | A สั้น |
|---|---|
| ความแม่นยำเทียบ Auditor จริง? | "± 5-10% บน DBH, ± 10-15% บน volume — ใน range ที่ TGO ยอมรับ" |
| ทำไมไม่ใช้ Drone? | "Drone scan ยอด → ดีสำหรับ canopy. เราทำ Mobile + LiDAR upload → ดี under-canopy + ราคาถูกกว่า 10×" |
| กันโกงยังไง? | "4 layers: camera-only (no gallery), GPS 6-decimal, EXIF validation, server-side dedup ใน 1-2m" |
| Business Model? | "B2B: เก็บค่า platform fee 5-10% จาก marketplace + tiered subscription สำหรับ enterprise auditors" |
| ทำไมยังไม่มี TGO certify? | "Phase post-NSC. ต้องส่ง academic validation paper ก่อน — ตอนนี้ทดสอบกับ destructive sampling data จาก paper" |

---

## 13. Definition of Done (DoD)

### Feature DoD
- [ ] Code merged to main
- [ ] Tests pass (unit + integration relevant)
- [ ] Manual smoke test on real device/browser
- [ ] No new lint warnings
- [ ] Updated docs (if behavior changed)
- [ ] PR description mentions which acceptance criteria covered

### Sprint DoD
- [ ] All committed tasks done OR carried over with reason
- [ ] No critical bugs in main branch
- [ ] Demo of new features in team sync
- [ ] TASKS.md updated

### Phase DoD
- [ ] All phase milestones met
- [ ] Risk register reviewed + updated
- [ ] Cost burn-down checked vs budget

### Final Submission DoD (17 ก.ค.)
- [ ] Full report uploaded to SIMs
- [ ] Source code zipped + uploaded
- [ ] Demo video uploaded
- [ ] Production deployed (Web + API)
- [ ] APK signed + uploaded
- [ ] All 3 team members sign off

---

## 14. Required Hardware / Accounts / Costs

### Hardware (ที่ทีมต้องมี)
| Item | Owner | Purpose |
|---|---|---|
| Android phone (Android 11+) | User หรือ Person A | Mobile dev + demo |
| Laptop ที่รัน Flutter + Next.js + Docker | ทุกคน | Dev |
| External SSD ≥ 500GB | User | NEON dataset + LiDAR work |

### Accounts (Free Tier ok)
- [x] GitHub (Org or personal — already set up)
- [x] Supabase (Free tier 500MB DB)
- [ ] Vercel (Hobby — Person A) — for Web
- [ ] Railway (Hobby — User) — for API
- [ ] RunPod (Pay-as-you-go — User) — for ML GPU
- [ ] Google Colab Pro+ (~$50/mo, optional)
- [ ] Sentry (Developer free)
- [ ] Figma (Free Education License — Person B)

### Estimated Cost (NSC submission phase)
| Item | Monthly |
|---|---|
| Supabase Free | $0 |
| Vercel Hobby | $0 |
| Railway Hobby | $5 |
| RunPod (~100 hours A10G @ $0.39) | $39 |
| Sentry Developer | $0 |
| Domain (optional) | $1 |
| Colab Pro+ (for training) | $50 |
| **Total** | **~$95/month × 2 months = $190** |

> ทุนสนับสนุน NSC ~3,000-5,000 บาท ≈ $90-150 — พอครอบคลุม

---

## 15. Day-by-Day Action Items (วันนี้ — 24 พ.ค.)

### 🚨 Today (24 พ.ค.)
1. รวบรวมข้อมูลทีม (ชื่อจริง + เบอร์ + email + GitHub username) → ใส่ใน Proposal
2. ลงทะเบียน SIMs (User)
3. ติดต่อที่ปรึกษา — นัดวัน review Proposal v1 (23-24 พ.ค.)
4. Person B: finalize logo (ถ้ายัง — ดูเหมือนทำแล้ว PR #4 ✅)
5. Person A: pnpm dev verify localhost:3000 ทำงาน

### 🌅 Tomorrow (25 พ.ค.)
1. User: เริ่มเดินขอลายเซ็นที่ปรึกษา
2. Person A: implement Login UI (no backend wire yet — มี [login-form.tsx](apps/web/src/app/(auth)/login/login-form.tsx) แล้ว)
3. Person B: เริ่ม Architecture Diagram + Pipeline Infographic

### 📅 ก่อนสุดสัปดาห์ (26-27 พ.ค.)
1. User: ส่งเอกสารเข้าระบบสถาบัน — ขอลายเซ็นคณบดี/ผอ.
2. Person A + B: finalize landing page text + visuals
3. User: review Proposal v2 ตาม feedback

### 🎯 28 พ.ค. (1 วัน buffer)
1. User: convert Proposal → PDF + รวมลายเซ็น
2. User: อัปโหลด SIMs

### 🚨 29 พ.ค. < 17:00
1. Verify submission status
2. หยุดพัก!

---

## 16. After-Proposal Quick Wins (30 พ.ค. — 5 มิ.ย.)

หลังส่ง Proposal เสร็จ — ใช้ Sprint 1 ทำของง่ายๆ ที่ build momentum:

### User
- [ ] Setup `docker-compose.dev.yml` (Postgres + PostGIS + Redis)
- [ ] Setup Supabase project จริง (ดู docs/SUPABASE_SETUP.md)
- [ ] Download NEON dataset (~5GB) — submit in `data/raw/`
- [ ] รัน lidR R script บน NEON sample (1 ชม. ศึกษา reference)
- [ ] Port step1_ground.py แรก — งานเริ่มต้น ML

### Person A
- [ ] Deploy Web to Vercel — connect GitHub
- [ ] Wire Login form ให้ทำงานกับ Supabase Auth
- [ ] Skeleton `/dashboard/scans` page (list view)

### Person B
- [ ] Final Wireframe Mobile (Figma)
- [ ] Color/Typography token export → packages/design-tokens/tokens/
- [ ] Architecture Diagram polished version (1200x800 PNG)

---

## 17. Appendix: Useful Commands

```bash
# Mobile
cd apps/mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Web
cd apps/web
pnpm install
pnpm dev          # localhost:3000
pnpm test
pnpm build
pnpm lint

# API
cd services/api
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000
poetry run pytest --cov

# ML
cd services/ml
poetry install
poetry run pytest tests/test_allometric.py -v
poetry run python -m pipeline.main --input data/raw/sample.las

# DB
docker compose up -d postgres
psql postgresql://postgres:postgres@localhost:5432/carbonscan

# Deploy
vercel --prod
railway up
```

---

## 18. References & Further Reading

### Internal docs
- [docs/ROADMAP.md](ROADMAP.md) — Phased timeline overview
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — System architecture
- [docs/DATA_MODEL.md](DATA_MODEL.md) — DB schema details
- [docs/ml/PIPELINE.md](ml/PIPELINE.md) — ML pipeline algorithms
- [docs/decisions/](decisions/) — 6 ADRs
- [TASKS.md](../TASKS.md) — Day-to-day tasks
- [proposal/](../proposal/) — NSC submission docs

### External (recommended deep reads)
1. lidR Wiki — https://github.com/r-lidar/lidR/wiki — Tree segmentation reference
2. TGO Allometric Guidelines 2017 — ดู `services/ml/docs/ALLOMETRIC.md`
3. PointNet++ paper — Qi et al. 2017 (arxiv 1706.02413)
4. NEON Forest LiDAR — https://data.neonscience.org/
5. TLSeparation — Cembrowski et al. (rule-based fallback)
6. TreeQSM — Calders et al. (cylinder fitting reference)
7. Khosravipour 2014 — Pit-free CHM algorithm
8. Supabase docs — https://supabase.com/docs (Auth + Storage + RLS)

---

> 📝 **เอกสารนี้เป็น living doc** — อัปเดตหลัง sprint review ทุกครั้ง.
> ถ้ามีอะไรเปลี่ยน scope, technology, หรือ timeline → ต้องอัปเดตทันที + ทุกคนใน Discord/Line อ่าน.

> **Owner:** User (Lead) — รับผิดชอบรักษาความใหม่ของเอกสาร
