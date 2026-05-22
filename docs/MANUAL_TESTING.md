# 🧪 Manual Testing Playbook

> คู่มือทดสอบโปรเจคด้วยตัวเอง — Web + Backend API + Database + Mobile
>
> **เป้าหมาย:** เดิน checklist top-to-bottom ภายใน 60-90 นาที แล้วมั่นใจว่าระบบทุกส่วนทำงาน
>
> **ผู้ใช้:** Solo developer (คุณ) + กรรมการ NSC หรือ ที่ปรึกษา ที่อยากลองระบบ

---

## 📋 ภาพรวม (Overview)

| Section | What | Time | Required? |
|---|---|---|---|
| **1. Pre-flight** | เช็คว่าทุกอย่างพร้อม | ~3 นาที | ✅ ต้องทำก่อน |
| **2. Quick Smoke** | Verify ทุก service boot ได้ | ~5 นาที | ✅ ก่อนทดสอบรายละเอียด |
| **3. Web E2E** | Signup → Login → Dashboard | ~20 นาที | ✅ Critical |
| **4. Backend API** | Endpoints + JWT verification | ~10 นาที | ✅ Critical |
| **5. Database** | RLS + auto-sync trigger | ~5 นาที | 🟡 Optional |
| **6. Mobile** | Flutter app (รวม install) | ~45 นาที | ⏭ Skip ได้ ถ้าไม่มี Flutter |
| **7. Error Scenarios** | Negative cases | ~10 นาที | 🟡 Recommended |
| **8. Checklist Card** | Quick reference | — | 📋 Print/save |

**รวม:** Section 1-5 + 7 = ~55 นาที (essentials). + Mobile = ~100 นาที total.

---

## 1. Pre-flight Checklist (~3 นาที)

ก่อนเริ่มทดสอบ — ยืนยันสิ่งเหล่านี้พร้อม:

### 1.1 `.env` files

```bash
# Check 3 files exist:
ls -la D:/Project_Carbon/services/api/.env
ls -la D:/Project_Carbon/apps/web/.env.local
ls -la D:/Project_Carbon/services/ml/.env
```

✅ **Expected:** 3 ไฟล์ existed + size > 500 bytes (มี content จริง)
❌ ถ้าไม่มี → ดู [`docs/SUPABASE_SETUP.md`](SUPABASE_SETUP.md) Step 7

### 1.2 Supabase project ACTIVE

เปิด browser:
```
https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf
```

✅ **Expected:** หน้า Dashboard โหลดได้ — ไม่มีแบนเนอร์ "Project Paused"
❌ ถ้า paused → กดปุ่ม **"Restore"** + รอ 30 วินาที

### 1.3 Python venv พร้อม

```bash
cd D:/Project_Carbon/services/api
.venv/Scripts/python.exe -c "import fastapi, uvicorn, asyncpg; print('API deps OK')"
```

✅ **Expected:** `API deps OK`
❌ ถ้า ImportError → `.venv/Scripts/pip.exe install -e ".[dev]"`

### 1.4 Web deps พร้อม

```bash
ls D:/Project_Carbon/node_modules/.pnpm | head -1
ls D:/Project_Carbon/apps/web/node_modules/.bin/next 2>&1 | head -1
```

✅ **Expected:** เห็น symlink files
❌ ถ้าไม่มี → จาก repo root รัน `pnpm install`

### ✅ Decision Tree

| Status | Next action |
|---|---|
| ทุกข้อ ✅ | → ไป Section 2 |
| 1.1 fail | → [`SUPABASE_SETUP.md`](SUPABASE_SETUP.md) |
| 1.2 fail | → Supabase Dashboard → Restore |
| 1.3 fail | → `pip install -e ".[dev]"` ใน services/api |
| 1.4 fail | → `pnpm install` ที่ repo root |

---

## 2. Quick Smoke Test (~5 นาที)

ตรวจสอบว่า services ทั้งหมด boot ได้ ก่อนเริ่ม functional testing

### 2.1 Start FastAPI Backend

**Terminal #1:**
```powershell
cd D:\Project_Carbon\services\api
$env:PYTHONIOENCODING="utf-8"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

✅ **Expected logs:**
```
🌲 Starting CarbonScan AI API v0.1.0 (development)
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2.2 Backend Liveness

**Terminal #2:**
```bash
curl http://localhost:8000/health
```

✅ **Expected:** `{"status":"ok","version":"0.1.0"}`

### 2.3 Backend Readiness (DB connection)

```bash
curl http://localhost:8000/api/v1/health/ready
```

✅ **Expected:** `{"status":"ok","database":true}`
❌ ถ้า `database: false` → DATABASE_URL ใน `.env` ผิด → ดู [`HANDOFF.md`](HANDOFF.md) Troubleshooting

### 2.4 Start Web Frontend

**Terminal #3:**
```powershell
cd D:\Project_Carbon\apps\web
pnpm dev
```

✅ **Expected logs:**
```
   ▲ Next.js 14.2.x
   - Local:        http://localhost:3000
 ✓ Ready in <2s
```

### 2.5 Landing Page Loads

เปิด browser → **http://localhost:3000**

✅ **Expected (visual checklist):**
- [ ] Header แสดง logo (รูปต้นไม้+มือ+CO₂) + ข้อความ "CarbonScan AI"
- [ ] ลิงก์ "Marketplace" + "เข้าสู่ระบบ" + ปุ่มสีเขียว "เริ่มใช้ฟรี"
- [ ] Hero: "NSC 2026 — Sustainable Innovation" + heading "แปลงต้นไม้เป็น Carbon Credits ด้วย AI ที่โปร่งใส"
- [ ] 4 feature cards: AI Wood-Leaf, Anti-Fraud, Verifiable 3D, TGO Standard
- [ ] Stats section: 100× / 5 ชนิด / < 10 นาที
- [ ] Footer: © 2026 CarbonScan AI · NSC 2026 หมวด 14

❌ ถ้าหน้าเปล่า → ดู Console (F12) → มัก env var ขาด

---

## 3. Web E2E Test (~20 นาที) — Critical Path 🔥

ทดสอบ flow ของผู้ใช้จริง: สมัคร → เข้าสู่ระบบ → ดู dashboard

### 3.1 Setup — Disable Email Confirmation (Dev Only)

เพื่อทดสอบโดยไม่ต้องเช็คอีเมลจริง:

1. เปิด https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/auth/providers
2. คลิก **"Email"** provider
3. หา **"Confirm email"** → toggle **OFF**
4. กด **Save**

> ⚠️ ก่อน production ต้องเปิดกลับ — ตอนนี้ทดสอบเฉย ๆ

### 3.2 Signup Test

ไป http://localhost:3000/signup

กรอกฟอร์ม:
| Field | Value |
|---|---|
| ชื่อ | `Test User` |
| อีเมล | `testuser+01@gmail.com` (เปลี่ยน +01, +02, ... แต่ละครั้งทดสอบ) |
| รหัสผ่าน | `TestPass123` |
| ประเภทผู้ใช้ | `ชุมชน / เกษตรกร` |

กด **"สมัครสมาชิกฟรี"**

✅ **Expected:**
- ปุ่มเปลี่ยนเป็น "กำลังสมัคร..." (~1-2 วินาที)
- ถ้า email confirmation OFF → redirect ไป `/dashboard` ทันที
- ถ้า email confirmation ON → เห็นข้อความ "ตรวจอีเมลของคุณ ✉"

❌ ถ้า error "User already registered" → เปลี่ยน +XX ในอีเมล + ลองอีกที

### 3.3 Dashboard Verification

หลัง signup สำเร็จ → ควรอยู่ที่ `/dashboard`:

✅ **Expected (visual):**
- [ ] Heading: "ยินดีต้อนรับ, Test User"
- [ ] Subtext: "คุณเข้าสู่ระบบเป็น **community**"
- [ ] Card: "เริ่มต้นใช้งาน" + 4 bullet points ของ Phase 1 features
- [ ] Footer: "User ID: <uuid>" (รูปแบบเช่น `abc12345-67de-...`)

### 3.4 Session Persistence

ที่หน้า `/dashboard`:
- กด **F5** (refresh page)

✅ **Expected:** หน้ายังคงแสดง dashboard ของ user เดิม (ไม่ redirect ไป login)

### 3.5 Logout (Manual — ยังไม่มีปุ่ม Logout UI)

1. เปิด DevTools (F12) → **Application** tab → **Cookies** → `http://localhost:3000`
2. หา cookies ที่ขึ้นต้นด้วย `sb-` (เช่น `sb-umuszxwwwxyvqxwhlpxf-auth-token`)
3. คลิกขวา → **Clear** (ลบทุก sb-* cookie)
4. กด **F5** (refresh)

✅ **Expected:** Redirect อัตโนมัติไป `/login?redirect=/dashboard`

### 3.6 Route Protection Test

เปิด **Incognito/Private window**:
- ไป `http://localhost:3000/dashboard` ตรง ๆ

✅ **Expected:** Redirect ทันทีไป `/login?redirect=%2Fdashboard`

### 3.7 Login Test

ที่ `/login` (จาก step ก่อน):

กรอก:
- อีเมล: `testuser+01@gmail.com` (เดิม)
- รหัสผ่าน: `TestPass123`

กด **"เข้าสู่ระบบ"**

✅ **Expected:**
- ปุ่มเปลี่ยน "กำลังเข้าสู่ระบบ..." (~1-2s)
- Redirect ไป `/dashboard` (ตาม `redirect` query param)
- แสดง dashboard ของ user เดิม

### 3.8 Invalid Login Test

Logout ก่อน (Section 3.5) → ไป `/login` → ใส่:
- อีเมล: `testuser+01@gmail.com`
- รหัสผ่าน: `WrongPassword`

กด login

✅ **Expected:**
- เห็น error box สีแดงในฟอร์ม: "Invalid login credentials"
- ไม่ redirect
- ฟอร์มยังคงอยู่ ผู้ใช้แก้ password ได้

---

## 4. Backend API Testing (~10 นาที)

ทดสอบ endpoints + JWT verification — Backend สำคัญสำหรับ Phase 2+

### 4.1 Swagger UI

เปิด **http://localhost:8000/docs**

✅ **Expected:**
- [ ] Title: "CarbonScan AI API"
- [ ] Version: 0.1.0
- [ ] 5 tags: root, health, auth, upload, jobs, trees
- [ ] **GET /api/v1/auth/me** — สามารถ Try it out ได้
- [ ] **POST /api/v1/auth/signup** — แสดงไว้แต่ status 501

> 💡 ลอง click "Try it out" → "Execute" บน /health → เห็น response

### 4.2 Health Endpoints via curl

```bash
# 1. Root
curl http://localhost:8000/

# 2. Health (no DB check)
curl http://localhost:8000/health

# 3. V1 health
curl http://localhost:8000/api/v1/health

# 4. Readiness (with DB check)
curl http://localhost:8000/api/v1/health/ready
```

✅ **Expected:** ทุก endpoint ตอบ 200 พร้อม JSON

### 4.3 /me without Token

```bash
curl http://localhost:8000/api/v1/auth/me
```

✅ **Expected:**
```json
{"error":"Unauthorized","message":"Missing or malformed Authorization header","details":{}}
```
(HTTP 401)

### 4.4 /me with Invalid Token

```bash
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer garbage-token"
```

✅ **Expected:**
```json
{"error":"Unauthorized","message":"Invalid or expired token","details":{}}
```
(HTTP 401)

### 4.5 /me with Real Token

**Step 1: ขอ token จาก Supabase Auth**

```bash
curl -X POST "https://umuszxwwwxyvqxwhlpxf.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: <YOUR_SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"testuser+01@gmail.com\",\"password\":\"TestPass123\"}"
```

Copy ค่า `access_token` (ขึ้นต้นด้วย `eyJ...`)

**Step 2: ใช้ token เรียก /me**

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJ...<paste token>..."
```

✅ **Expected:**
```json
{
  "id": "<uuid>",
  "email": "testuser+01@gmail.com",
  "name": "Test User",
  "role": "community",
  "created_at": "2026-05-22T..."
}
```

> 📖 รายละเอียดเพิ่มเติม: [`docs/AUTH_TESTING.md`](AUTH_TESTING.md) Step 6

### 4.6 Stub Endpoints (Expected 501)

```bash
curl http://localhost:8000/api/v1/trees/
curl http://localhost:8000/api/v1/jobs/some-id
curl -X POST http://localhost:8000/api/v1/upload/las
```

✅ **Expected:** ทุก endpoint คืน 501 พร้อมข้อความ "Not implemented — see TODO in..."

> 💡 ปกติ — เหล่านี้คือ Phase 2 work

---

## 5. Database Verification (~5 นาที)

ตรวจว่า data ลงถูกต้อง + RLS ทำงาน

### 5.1 Supabase Table Editor

เปิด https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/editor

ดู tables ใน sidebar:

✅ **Expected (8 tables):**
- alembic_version
- jobs
- plots
- spatial_ref_sys (PostGIS)
- species_db
- transactions
- trees
- users

### 5.2 species_db — มี 5 ชนิด

คลิก **`species_db`** → ดู rows

✅ **Expected:**

| name_sci | name_th | wood_density | agb_a | agb_b | agb_c |
|---|---|---|---|---|---|
| Tectona grandis | สัก | 660 | 0.0509 | 2.15 | 0.7 |
| Dipterocarpus alatus | ยางนา | 720 | 0.0396 | 2.38 | 0.8 |
| Bambusa spp. | ไผ่ (ไผ่ทั่วไป) | 650 | 0.131 | 2.28 | 0.59 |
| Hevea brasiliensis | ยางพารา | 580 | 0.0464 | 2.33 | 0.72 |
| Afzelia xylocarpa | มะค่าโมง | 850 | 0.0612 | 2.42 | 0.66 |

❌ ถ้าไม่มี rows → รัน `services/api/scripts/seed_species_db.sql` ใน SQL Editor

### 5.3 auth.users — มี Test User

Dashboard → **Authentication** → **Users**

✅ **Expected:** เห็น row ที่อีเมล `testuser+01@gmail.com` (จาก Section 3.2)
- Provider: email
- Email confirmed at: <timestamp ถ้า OFF | null ถ้า ON>

### 5.4 public.users — Auto-sync Trigger Worked

กลับไป **Table Editor** → คลิก `users` table

✅ **Expected:**
- เห็น row 1 อันที่มี `id` ตรงกับ auth.users
- `email = testuser+01@gmail.com`
- `name = Test User`
- `role = community`
- `created_at` ภายในนาทีที่ผ่านมา

❌ ถ้าไม่มี row → trigger ไม่ทำงาน → รัน `services/api/scripts/rls_policies.sql` ใน SQL Editor อีกครั้ง

### 5.5 RLS Isolation Check (Optional)

ทดสอบว่า RLS ป้องกัน user A ดูข้อมูล user B:

**Test:** ทำ signup user ใหม่ (testuser+02@gmail.com) → ทำ flow signup → ดู Table Editor → public.users ควรมี 2 rows

แต่ถ้าใช้ anon key query (เช่น Web ที่ไม่ login) → ควรเห็นแค่ row ของตัวเองเท่านั้น

> 💡 Skip step นี้ได้ — ใช้เวลา ~10 นาทีถ้าจะทดสอบเต็มที่

### 5.6 Storage Buckets

Dashboard → **Storage** → ดู buckets

✅ **Expected (4 buckets):**
| Bucket | Visibility | File size limit |
|---|---|---|
| brand-assets | 🌐 Public | 5 MB |
| reports | 🌐 Public | 5 MB |
| photos | 🔒 Private | 20 MB |
| point-clouds | 🔒 Private | 50 MB |

---

## 6. Mobile Testing (~45 นาที)

> ⏭ **Skip ส่วนนี้ได้** ถ้าคุณยังไม่มี Flutter installed — เป็นงาน Phase 3 (15-17 ก.ค.) ไม่ critical ตอนนี้

### 6.1 Install Flutter SDK (~15 นาที, one-time)

**Windows:**
1. ดาวน์โหลด Flutter SDK: https://docs.flutter.dev/get-started/install/windows
2. แตก zip ลง `C:\src\flutter` (อย่าใส่ใน `Program Files` — มี permission issues)
3. เพิ่ม `C:\src\flutter\bin` ลง System PATH:
   - กด Windows → "Edit environment variables" → User → Path → Edit → New → paste path → OK
4. เปิด **PowerShell ใหม่** (ปิด-เปิดใหม่ ให้ PATH update)
5. รัน:
   ```powershell
   flutter --version
   ```
   ✅ Expected: `Flutter 3.24.x`

### 6.2 Install Android Studio + Emulator

1. ดาวน์โหลด: https://developer.android.com/studio (~1GB)
2. Install ตาม wizard (ใช้ค่า default ได้)
3. เปิด Android Studio → **More Actions** → **SDK Manager**:
   - ✅ Android API 34 (or latest)
   - ✅ Android SDK Command-line Tools
4. **Virtual Device Manager** → **Create Device** → Pixel 6 → API 34 → Finish
5. กดปุ่ม ▶ ที่ emulator เพื่อ start

### 6.3 Verify Flutter Setup

```powershell
flutter doctor
```

✅ **Expected:** ทุกข้อ ✅ (อาจมี Visual Studio toolchain ที่ ⚠ ถ้าไม่ต้องการ Windows desktop build — ข้ามได้)

ถ้ามี ❌ → ทำตามที่ flutter doctor บอก

### 6.4 Bootstrap Mobile Project (One-time)

```powershell
cd D:\Project_Carbon\apps\mobile

# Generate android/ folder (gitignored on purpose)
flutter create . --platforms=android --org=com.carbonscan --project-name=carbonscan_mobile

# Install Dart deps
flutter pub get
```

✅ **Expected:**
- โฟลเดอร์ `android/` ถูกสร้าง
- `flutter pub get` จบโดยไม่มี error

### 6.5 Configure Env

```powershell
cd D:\Project_Carbon\apps\mobile
cp .env.example .env
# Edit .env — fill API_BASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY
```

ใน `.env`:
```
API_BASE_URL=http://10.0.2.2:8000
SUPABASE_URL=https://umuszxwwwxyvqxwhlpxf.supabase.co
SUPABASE_ANON_KEY=<paste publishable key>
```

> 💡 `10.0.2.2` คือ Android emulator's way to access host's localhost

### 6.6 Run App

ใน emulator (จาก Section 6.2) ต้อง running แล้ว:

```powershell
cd D:\Project_Carbon\apps\mobile
flutter devices            # ตรวจว่า emulator detected
.\scripts\run-dev.ps1       # อ่าน .env + flutter run พร้อม --dart-define
```

✅ **Expected:**
- เห็น log: "▶ Running with defines: API_BASE_URL=... SUPABASE_URL=..."
- App build สำเร็จ (~1-3 นาที ครั้งแรก)
- App เปิดบน emulator

### 6.7 Home Screen Visual Check

✅ **Expected:**
- [ ] Logo "C" (gradient เขียว) + ข้อความ "CarbonScan AI"
- [ ] Heading: "แปลงต้นไม้ของคุณ\nเป็นรายได้"
- [ ] Subtext: "สแกนต้นไม้ด้วยกล้องมือถือ — ใช้เวลา 5 นาที"
- [ ] ปุ่มเขียวใหญ่: "เริ่มสแกนต้นไม้"
- [ ] ปุ่มขอบ: "ดูประวัติการสแกน"
- [ ] Stats card: "0 ต้นไม้ที่สแกน | 0 kg CO₂eq | ฿0 รายได้"

### 6.8 Tree Scan Screen

แตะ **"เริ่มสแกนต้นไม้"**

✅ **Expected:** เห็น checklist 4 ข้อก่อนสแกน
- [ ] แสงสว่างพอ
- [ ] ยืนห่างต้นไม้ 2-5 เมตร
- [ ] เดินรอบต้นไม้
- [ ] เปิด GPS

ปุ่มล่าง: "เปิดกล้องเริ่มสแกน"

### 6.9 Camera Screen Mock

แตะ **"เปิดกล้องเริ่มสแกน"**

✅ **Expected:**
- [ ] Background ดำ
- [ ] Counter ด้านบนขวา: "0 / 30"
- [ ] Placeholder ตรงกลาง: "Camera Preview (TODO Phase 3)"
- [ ] ปุ่ม shutter วงกลมขาวด้านล่าง
- [ ] แตะปุ่ม shutter → counter เพิ่ม +1 ทุกครั้ง

### 6.10 Back Navigation

แตะ ✕ มุมซ้ายบน

✅ **Expected:** กลับไป Tree Scan Screen

แตะ Back button ของ Android (หรือ ESC ใน emulator) → กลับ Home

---

## 7. Error Scenarios (~10 นาที)

ทดสอบ negative cases — ระบบควรจัดการ error สวยงาม

### 7.1 Signup ซ้ำอีเมล

ไปที่ `/signup` → กรอกอีเมลเดียวกับที่สมัครไปแล้ว (`testuser+01@gmail.com`) → submit

✅ **Expected:**
- Error box สีแดง: "User already registered"
- ฟอร์มยังคงอยู่
- เปลี่ยน email เพื่อ retry ได้

### 7.2 รหัสผ่านสั้นเกิน (Validation)

`/signup` → ใส่ password = `abc` (3 ตัวอักษร)

✅ **Expected:**
- Browser's HTML5 validation: tooltip "Please lengthen this text to 8 characters or more"
- ฟอร์มไม่ submit

### 7.3 Login ด้วย Email ที่ไม่มี

`/login` → email = `nonexistent@example.com`, password = anything

✅ **Expected:**
- Error: "Invalid login credentials"
- ไม่ redirect

### 7.4 Backend Down

ปิด FastAPI (Ctrl+C ใน terminal 1) → ที่หน้า `/dashboard` (logged in):

ทำ action ที่ต้องเรียก backend (Phase 1 มี — ตอนนี้ test ผ่าน curl):

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token จาก 4.5>"
```

✅ **Expected:**
- curl: `Failed to connect to localhost port 8000`
- Web ยังคงทำงาน (เพราะ Supabase auth client-only)

> 💡 ใน Phase 1+ จะมี API calls ที่ wire กับ backend — error handling ต้องดี

### 7.5 Network ขาด

ที่ `/login` → เปิด DevTools → Network tab → set throttling = **Offline**

ทดสอบ submit form

✅ **Expected:**
- ปุ่มเปลี่ยน "กำลังเข้าสู่ระบบ..."
- หลัง timeout (~10s) → error visible ใน Console
- (ปัจจุบัน UI ไม่ show network error — TODO Phase 1 ปรับ form error handling)

---

## 8. Test Checklist Card 📋

> Print หรือเก็บไว้เป็น quick reference

### Pre-flight ✓
- [ ] 1.1 .env files exist (3 ไฟล์)
- [ ] 1.2 Supabase ACTIVE
- [ ] 1.3 Python venv ready
- [ ] 1.4 Node modules ready

### Smoke ✓
- [ ] 2.1 FastAPI starts
- [ ] 2.2 GET /health = 200
- [ ] 2.3 GET /health/ready = database: true
- [ ] 2.4 Next.js starts
- [ ] 2.5 Landing renders

### Web E2E ✓ (Critical)
- [ ] 3.2 Signup ทำงาน → redirect /dashboard
- [ ] 3.3 Dashboard แสดง welcome + role
- [ ] 3.4 Refresh ไม่ logout
- [ ] 3.5 Clear cookies → redirect /login
- [ ] 3.6 Incognito + /dashboard → redirect
- [ ] 3.7 Login กลับมา = OK
- [ ] 3.8 Wrong password → error visible

### Backend API ✓
- [ ] 4.1 Swagger UI loads
- [ ] 4.3 /me no auth = 401
- [ ] 4.4 /me garbage = 401
- [ ] 4.5 /me real token = user JSON
- [ ] 4.6 Stubs = 501

### Database ✓
- [ ] 5.1 8 tables visible
- [ ] 5.2 species_db = 5 rows
- [ ] 5.3 auth.users มี test user
- [ ] 5.4 public.users auto-synced
- [ ] 5.6 4 storage buckets

### Mobile (Optional) ✓
- [ ] 6.3 flutter doctor green
- [ ] 6.4 flutter create + pub get ok
- [ ] 6.6 App boots on emulator
- [ ] 6.7-6.9 Home → Scan → Camera screens
- [ ] 6.10 Back navigation works

### Errors ✓
- [ ] 7.1 Duplicate email → blocked
- [ ] 7.2 Short password → blocked
- [ ] 7.3 Wrong creds → error message

---

## 🚦 Green-light Criteria for "Ship to Advisor"

ก่อนส่ง Proposal/Demo URL ให้ที่ปรึกษาหรือกรรมการ:

✅ **Critical (ต้องผ่านทุกข้อ):**
- Section 2 Smoke (5/5)
- Section 3 Web E2E (7/7)
- Section 4 Backend API (5/5)

✅ **Important (≥80% ผ่าน):**
- Section 5 Database (≥5/6)
- Section 7 Errors (≥3/5)

✅ **Optional:**
- Section 6 Mobile (skip ได้)

---

## 🆘 Troubleshooting

### Issue: "ImportError: email-validator is not installed"
- `cd services/api && .venv/Scripts/python.exe -m pip install email-validator`

### Issue: Web build error "Module not found: @supabase/ssr"
- ที่ repo root: `pnpm install`

### Issue: FastAPI starts but `/health/ready` returns `database: false`
- ตรวจ DATABASE_URL ใน `services/api/.env`
- ดู [`HANDOFF.md`](HANDOFF.md) "Cannot connect to Supabase" section

### Issue: Signup สำเร็จแต่ public.users ไม่มี row
- Auto-sync trigger ไม่ทำงาน
- รัน `services/api/scripts/rls_policies.sql` ใน Supabase SQL Editor
- ดู [`AUTH_TESTING.md`](AUTH_TESTING.md) Troubleshooting

### Issue: Flutter `flutter run` ERROR "Multidex"
- เพิ่ม `multiDexEnabled true` ใน `android/app/build.gradle`
- ดู [`apps/mobile/SETUP.md`](../apps/mobile/SETUP.md) Troubleshooting

### Issue: Emulator แสดง "App not installed"
- จาก `apps/mobile/`: `flutter clean && flutter pub get && flutter run`

### Issue: ไม่เจอ token ใน DevTools cookies
- Cookies เป็น HttpOnly → ใช้ Section 4.5 Step 1 (curl Supabase /auth/v1/token) แทน

---

## 📚 Related Documentation

| Need | Doc |
|---|---|
| Setup Supabase from scratch | [`SUPABASE_SETUP.md`](SUPABASE_SETUP.md) |
| Auth flow deep dive + JWT retrieval | [`AUTH_TESTING.md`](AUTH_TESTING.md) |
| Flutter SDK install + run guide | [`apps/mobile/SETUP.md`](../apps/mobile/SETUP.md) |
| Architecture overview | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| API endpoint reference | [`API.md`](API.md) |
| Daily commands cheat sheet | [`HANDOFF.md`](HANDOFF.md) |
| Project status snapshot | [`HANDOFF.md`](HANDOFF.md) |
| Troubleshooting common issues | [`HANDOFF.md`](HANDOFF.md) |

---

## 🎯 If Everything Passes — What's Next

ระบบของคุณพร้อมส่ง demo URL ให้ที่ปรึกษา/กรรมการ NSC! ขั้นต่อไป:

1. **Critical Path** — ส่ง Proposal ให้ที่ปรึกษา ([`proposal/advisor_email.md`](../proposal/advisor_email.md))
2. **Deploy** Web → Vercel (Phase 1) เพื่อได้ public URL
3. **Phase 1 Foundation** — เริ่ม wire Web ↔ FastAPI integration (ดู [`ROADMAP.md`](ROADMAP.md))

ขอให้สอบผ่าน NSC 2026 ครับ! 🌲🏆
