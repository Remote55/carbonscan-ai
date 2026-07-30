# คู่มือ Setup ก่อนแข่ง — TreeQ Carbon Platform

> **วันแข่ง: 5 สิงหาคม 2569**
> เอกสารนี้มีสองเส้นทาง เลือกอันเดียว:
>
> - **เส้นทาง A** — เครื่องที่ใช้อยู่ (`D:\Project_Carbon`) มีของครบแล้ว → แค่ตรวจและอัปเดต · **ใช้เวลา ~20 นาที**
> - **เส้นทาง B** — เครื่องใหม่/เครื่องสำรอง ยังไม่มีอะไรเลย → ติดตั้งตั้งแต่ต้น · **ใช้เวลา ~90 นาที**
>
> วันแข่งให้ใช้ [runbook](RUNBOOK-COMPETITION-DAY.md) ไม่ใช่ไฟล์นี้

---

# เส้นทาง A — เครื่องหลัก (ตรวจและอัปเดต)

## A1. ตรวจว่าของครบ (2 นาที)

```powershell
foreach ($t in @('node','pnpm','git','py')) {
  $c = Get-Command $t -EA SilentlyContinue
  if ($c) { Write-Host ("  OK   {0,-6} {1}" -f $t, $c.Source) } else { Write-Host "  MISS $t" }
}
foreach ($v in @('D:\Project_Carbon\services\api\.venv\Scripts\python.exe',
                 'D:\Project_Carbon\services\ml\.venv\Scripts\python.exe',
                 'C:\Users\Acer\OneDrive\Desktop\CarbonScrip\cloudflared.exe',
                 'C:\Users\Acer\OneDrive\Desktop\CarbonScrip\TreeQ-Demo-Start.bat')) {
  if (Test-Path $v) { Write-Host "  OK   $v" } else { Write-Host "  MISS $v" }
}
```

**ผลที่ต้องได้เมื่อ 30 ก.ค. 69 — ต้องเป็น OK ทั้ง 8 บรรทัด**

> บรรทัดสุดท้ายคือ wrapper ที่บอก launcher ว่า cloudflared อยู่ไหน
> ถ้า MISS ให้ทำ **B9** ก่อนอย่างอื่น — ขาดตัวนี้แล้ว Auto จะได้ `LOCAL LIVE` ทุกครั้ง

| สิ่งที่ต้องมี | เวอร์ชันที่ยืนยันแล้วว่าใช้ได้ |
|---|---|
| Node | v24.15.0 (ต้อง ≥ 20) |
| pnpm | 9.x |
| Python (venv ทั้งสอง) | 3.11.9 |
| cloudflared | 2026.7.1 |

ถ้ามีอันไหน MISS → ข้ามไปทำเฉพาะข้อนั้นใน **เส้นทาง B**

## A2. ดึงโค้ดล่าสุด (1 นาที)

```powershell
cd D:\Project_Carbon
git checkout main
git pull --ff-only
git log --oneline -1
```

จดเลข commit ที่ได้ไว้ — นี่คือเวอร์ชันที่จะใช้แข่ง

## A3. ติดตั้ง dependency ที่อาจเปลี่ยน (3 นาที)

```powershell
pnpm install --frozen-lockfile
```

## A4. Build (3 นาที) — **ข้ามไม่ได้**

```powershell
pnpm --filter web build
```

> ⚠️ **launcher ไม่ build ให้** มันเสิร์ฟ build ที่มีอยู่เท่านั้น
> ถ้าลืม build หลังแก้โค้ด จะได้หน้าเว็บเวอร์ชันเก่าโดยไม่มีอะไรเตือน
> (เกิดขึ้นจริงมาแล้ว: แก้ปุ่มบนหน้าแรกแล้วลืม build ปุ่มเลยไม่เปลี่ยน)

เช็คว่า build ใหม่จริง:

```powershell
Get-Item D:\Project_Carbon\apps\web\.next\BUILD_ID | Select-Object LastWriteTime
```

เวลาต้องเป็นเมื่อกี้นี้

## A5. รันเทสต์ทั้งหมด (6 นาที) — คำสั่งเดียว

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Project_Carbon\run-gates.ps1
```

รันให้ครบทั้ง 5 อย่างเรียงตัวกัน แล้วสรุปท้ายสุด **ต้องได้ `All gates passed.`**

| gate | ตรวจอะไร |
|---|---|
| Unit tests | ~130 เทสต์ |
| Type-check | TypeScript |
| Lint | ESLint |
| Build | production build |
| **Judge journey (browser)** | 42 เทสต์ในเบราว์เซอร์จริง 2 ขนาดจอ |

พร้อมสแกนคำที่ห้ามเคลม (`certified carbon credit`, `จำนวนต้นไม้` ฯลฯ) ให้ด้วย — ต้องขึ้น `none`

> **ทำไมต้องเรียงตัว:** สอง npm/pnpm บน Windows แย่ง pnpm store กันแล้วพังด้วยเหตุผลที่ไม่เกี่ยวกับโค้ด
> และ browser gate ต้องรัน**หลัง** build เพราะมันเสิร์ฟ production output แล้วตรวจแฮชผ่าน HTTP

**ส่วน launcher แยกอีกชุด** (สคริปต์ข้างบนไม่ครอบ):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Project_Carbon\scripts\demo\tests\run-tests.ps1
```
ต้องจบด้วย `TESTS PASSED` (~76 assertion)

> ถ้าจะรันเทสต์เว็บเดี่ยวๆ ต้องใส่คำว่า `run` — `pnpm --filter web test` เข้า watch mode แล้วค้าง ไม่จบให้

## A6. ซ้อมทั้งสามโหมด (6 นาที)

```powershell
cd D:\Project_Carbon
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\start-treeq-demo.ps1 -Mode Frozen -NoBrowser -ExitAfterReady
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\start-treeq-demo.ps1 -Mode Local  -NoBrowser -ExitAfterReady
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\start-treeq-demo.ps1 -Mode Auto   -NoBrowser -ExitAfterReady
```

**ทุกรอบต้องได้:**

| โหมด | บรรทัดที่ต้องเห็น | เวลา |
|---|---|---|
| Frozen | `Mode: FROZEN - NOT A LIVE RUN` | ~7 วิ |
| Local | `Mode: LOCAL LIVE` | ~7 วิ |
| Auto | `Mode: AUTO PUBLIC LIVE` | 40–50 วิ |

และทุกรอบต้องจบด้วย `Cleanup complete` **ถ้ารอบไหน exit ไม่ใช่ 0 → หยุด อย่าไปต่อ**

## A7. เตรียม USB (3 นาที)

ใส่ลง USB:

```
TreeQ-USB\
  input.ply                       ← ก๊อปจาก apps\web\public\demo\input.ply
  RUNBOOK-COMPETITION-DAY.pdf     ← พิมพ์ออกมาด้วยหนึ่งชุด
  PRESENTATION-SCRIPT.pdf
  slides.pdf                      ← สไลด์ฉบับ PDF เผื่อ PowerPoint พัง
```

```powershell
Copy-Item D:\Project_Carbon\apps\web\public\demo\input.ply E:\TreeQ-USB\ -Force
```

> เปลี่ยน `E:` เป็นไดรฟ์ USB จริง

---

# เส้นทาง C — บริการบนคลาวด์ (Vercel + Supabase)

> **ส่วนนี้ไม่ได้อยู่ในโค้ด** ตั้งครั้งเดียวแล้วอยู่ถาวร — แต่ถ้าไม่ตั้ง เว็บจะพังในแบบที่
> เทสต์ทั้ง 172 ตัวจับไม่ได้เลย เพราะมันเป็นค่า config ฝั่งบริการ
>
> **นี่คือต้นเหตุของบั๊กที่เพื่อนร่วมทีมเจอจริง** — อีเมลยืนยันชี้ `localhost:3000`
> แล้วเปิดบน iPad ไม่ได้ ยืนยันบัญชีไม่ได้เลย

## C1. Environment variables บน Vercel

ต้องมี **3 ตัว** ใน environment `Production`:

| ตัวแปร | ค่า | ใครใช้ | ถ้าหายจะเป็นอะไร |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://umuszxwwwxyvqxwhlpxf.supabase.co` | login/signup | เข้าสู่ระบบไม่ได้ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | (คีย์ anon จาก Supabase) | login/signup | เข้าสู่ระบบไม่ได้ |
| `NEXT_PUBLIC_SITE_URL` | `https://treeqcarbon.vercel.app` | **ลิงก์ในอีเมลยืนยัน** | อีเมลชี้ localhost |

ตรวจว่ามีครบ:

```powershell
cd D:\Project_Carbon\apps\web
npx vercel env ls production
```

> ⚠️ **`NEXT_PUBLIC_*` ถูกฝังตอน build** เปลี่ยนค่าแล้ว **ต้อง redeploy** ไม่งั้นเว็บยังใช้ค่าเก่า
> ```powershell
> npx vercel --prod --archive=tgz
> ```

> `NEXT_PUBLIC_API_URL` มีอยู่ด้วยแต่**ไม่จำเป็นสำหรับวันแข่ง** — มันใช้กับ
> `/dashboard/viewer` เท่านั้น ส่วน `/demo` รับ endpoint จาก launcher ผ่าน URL fragment

## C2. Supabase — URL Configuration

เปิดตรงๆ:

```
https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/auth/url-configuration
```

| ช่อง | ต้องเป็น |
|---|---|
| **Site URL** | `https://treeqcarbon.vercel.app` |
| **Redirect URLs** | `https://treeqcarbon.vercel.app/auth/callback` |
| | `http://localhost:3000/auth/callback` |

กด **Save changes** (ถ้าปุ่มเป็นสีจางแปลว่าบันทึกแล้ว) · Redirect URLs บันทึกทันทีตอนกด Add URL

> **ทำไมต้องมีทั้งสอง URL:** ตัว vercel ให้อีเมลจากเว็บจริงกลับมาถูกที่
> ตัว localhost ให้ทีมยังสมัคร/ทดสอบบนเครื่องตัวเองได้ **ถ้าลบอันนี้ dev พัง**
>
> **ทำไม Site URL สำคัญกว่าที่คิด:** ถ้า redirect URL ไม่อยู่ใน allow-list
> Supabase จะ**เงียบๆ** ใช้ Site URL แทน ของโปรเจกต์ใหม่คือ `http://localhost:3000`
> แก้โค้ดฝั่งเราอย่างเดียวไม่พอ

**ทดสอบ:** สมัครด้วยอีเมล**ใหม่** แล้ว hover ดูลิงก์ในเมล ต้องเห็น
`redirect_to=https://treeqcarbon.vercel.app/auth/callback` — ถ้ายังเป็น localhost คือยังไม่ Save
หรือพิมพ์ไม่ตรงเป๊ะ (ต่างแค่ `/` ปิดท้ายก็ไม่ผ่าน)

## C3. ⚠️ Supabase free tier หยุดเองได้ — ตรงช่วงวันแข่ง

organization อยู่แพลน **FREE** ซึ่ง **pause โปรเจกต์ที่ไม่มีการใช้งานราวหนึ่งสัปดาห์**
(อีกโปรเจกต์ในบัญชีนี้ `Remote55's Project` โดนไปแล้ว)

**กันง่ายๆ: เข้า dashboard หรือลองล็อกอินเว็บวันละครั้ง ช่วง 1–4 ส.ค.**

เช็คสถานะ:
```
https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf
```
ต้องไม่ขึ้นคำว่า `Paused` — ถ้าขึ้นให้กด **Restore** (ใช้เวลาไม่กี่นาที)

> **ข่าวดี: ไม่กระทบการสาธิตวันแข่ง** เส้นทางกรรมการคือ launcher → `/demo`
> ซึ่ง**ไม่แตะ Supabase เลย** จะกระทบแค่ถ้าตั้งใจโชว์หน้า login/dashboard บนเวที

## C4. ถ้าบัญชีใครยืนยันอีเมลไม่ได้

```
https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/auth/users
```

หา user → `⋯` → **Confirm email** (กดยืนยันให้เลย เร็วกว่าส่งเมลใหม่)

---

## A8. Freeze (T-24 ชม. = 4 ส.ค.)

- [ ] `git log --oneline -1` → **จดเลข commit ลงกระดาษ**
- [ ] หลังจากนี้ **ห้าม `git pull`** จนกว่าจะแข่งเสร็จ
- [ ] ห้าม merge อะไรที่ไม่ใช่บั๊กที่ทำให้สาธิตไม่ได้
- [ ] ชาร์จโน้ตบุ๊กเต็ม + เอาอะแดปเตอร์
- [ ] ทดสอบต่อจอโปรเจกเตอร์/HDMI อย่างน้อยหนึ่งครั้ง

---

# เส้นทาง B — เครื่องใหม่ ตั้งแต่ศูนย์

> เผื่อเครื่องหลักพัง หรืออยากมีเครื่องสำรอง
> **ทำล่วงหน้าอย่างน้อย 3 วัน** เพราะขั้นตอน pip install ใช้เวลานานและอาจติดปัญหา

## B1. ติดตั้ง Node 20+ (10 นาที)

โหลด LTS จาก <https://nodejs.org> → ติดตั้งแบบ default → เปิด PowerShell **ใหม่**

```powershell
node --version    # ต้อง v20 ขึ้นไป
```

## B2. ติดตั้ง pnpm (2 นาที)

```powershell
npm install -g pnpm@9
pnpm --version
```

## B3. ติดตั้ง Python 3.11 (10 นาที)

> **ต้อง 3.11 เท่านั้น** 3.12/3.13 ยังไม่ทดสอบ และ dependency บางตัวยังไม่รองรับ

โหลด **Python 3.11.9** จาก <https://www.python.org/downloads/release/python-3119/>
เลือก *Windows installer (64-bit)*

ตอนติดตั้ง **ติ๊ก "Add python.exe to PATH"**

```powershell
py -3.11 --version    # ต้องได้ 3.11.x
```

## B4. ติดตั้ง Git (5 นาที)

<https://git-scm.com/download/win> → ติดตั้งแบบ default

## B5. โคลนโปรเจกต์ (5 นาที)

```powershell
cd D:\
git clone https://github.com/Remote55/carbonscan-ai.git Project_Carbon
cd D:\Project_Carbon
```

ถ้าจะใช้ commit ที่ freeze ไว้:

```powershell
git checkout <เลข commit ที่จดไว้>
```

## B6. ติดตั้ง dependency ของเว็บ (5 นาที)

```powershell
cd D:\Project_Carbon
pnpm install --frozen-lockfile
```

## B7. สร้าง venv ของ API (15 นาที)

```powershell
cd D:\Project_Carbon\services\api
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

ตรวจ:

```powershell
.\.venv\Scripts\python.exe -c "import uvicorn, app.main; print('API OK')"
```

> **สำคัญ:** Python ที่ติดตั้งในเครื่อง (system Python) **ไม่มี uvicorn**
> ต้องเรียกผ่าน `.venv\Scripts\python.exe` เสมอ ห้ามใช้ `python` เฉยๆ

## B8. สร้าง venv ของ ML (25 นาที — นานที่สุด)

```powershell
cd D:\Project_Carbon\services\ml
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

> ขั้นนี้จะโหลด PyTorch, Open3D, laspy ซึ่งรวมกันหลาย GB **ต้องมีเน็ตดี**
> ถ้าเน็ตช้าอาจใช้เวลาเกินครึ่งชั่วโมง — อย่าทำวันแข่ง

ตรวจ:

```powershell
.\.venv\Scripts\python.exe -c "import open3d, laspy, numpy; print('ML OK')"
```

## B9. ติดตั้ง cloudflared + wrapper (10 นาที) — **ข้ามข้อนี้ = ไม่มี public mode**

โหลด `cloudflared-windows-amd64.exe` จาก
<https://github.com/cloudflare/cloudflared/releases>

เปลี่ยนชื่อเป็น `cloudflared.exe` แล้วเก็บไว้ในโฟลเดอร์เดียว
บนเครื่องหลักคือ `C:\Users\Acer\OneDrive\Desktop\CarbonScrip\`
(เครื่องใหม่จะใช้ที่ไหนก็ได้ แต่ต้องใช้ path เดียวกันตลอดทั้งข้อนี้)

```powershell
C:\Users\Acer\OneDrive\Desktop\CarbonScrip\cloudflared.exe --version
```

**แล้วสร้าง wrapper** — นี่คือขั้นที่ทำให้ launcher หา cloudflared เจอ:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Project_Carbon\scripts\demo\install-desktop-wrapper.ps1 -DestinationDirectory C:\Users\Acer\OneDrive\Desktop\CarbonScrip
```

ต้องขึ้น `Installed TreeQ-Demo-Start.bat` — ได้ไฟล์ใหม่ในโฟลเดอร์เดียวกับ cloudflared
**วันแข่งเปิดไฟล์นี้ ไม่ใช่ตัวใน `scripts\demo\`**

ตรวจว่าใช้ได้จริง (ต้องขึ้น `Mode: AUTO PUBLIC LIVE` ไม่ใช่ `LOCAL LIVE`):

```powershell
cmd /c "C:\Users\Acer\OneDrive\Desktop\CarbonScrip\TreeQ-Demo-Start.bat" -Mode Auto -NoBrowser -ExitAfterReady
```

> ใช้เวลา ~40 วินาที เพราะ launcher รอ 25 วินาทีก่อนถาม DNS ครั้งแรก
> ถามเร็วกว่านั้น hostname จะติด negative cache 30 นาที แล้วรอบนั้นเสีย public mode

**ทางเลี่ยงถ้าไม่อยากสร้าง wrapper** — ตั้ง env var เองทุกครั้งที่เปิด PowerShell ใหม่
หรือส่ง `-CloudflaredPath <path>` ทุกครั้ง แต่วันแข่ง**อย่าใช้วิธีนี้** เพราะลืมง่าย

```powershell
$env:TREEQ_CLOUDFLARED = 'C:\Users\Acer\OneDrive\Desktop\CarbonScrip\cloudflared.exe'
```

## B10. ติดตั้งเบราว์เซอร์สำหรับเทสต์ (5 นาที)

browser gate ใช้ Chromium ของ Playwright ซึ่ง**ไม่มาพร้อม `pnpm install`** ต้องโหลดแยก:

```powershell
cd D:\Project_Carbon\apps\web
npx playwright install chromium
```

ถ้าข้ามขั้นนี้ `run-gates.ps1` จะแดงที่ gate สุดท้ายด้วยข้อความว่าหา browser ไม่เจอ
— เป็นปัญหาเครื่อง ไม่ใช่ปัญหาโค้ด

## B11. Build + ตรวจทั้งหมด

ทำตาม **A4 → A7** ทุกข้อ (เส้นทาง C ตั้งครั้งเดียว ใช้ร่วมกันทุกเครื่อง ไม่ต้องทำซ้ำ)

---

# ตารางแก้ปัญหาตอน setup

| อาการ | สาเหตุ | แก้ |
|---|---|---|
| `pnpm : not recognized` | ยังไม่ได้เปิด PowerShell ใหม่หลังติดตั้ง | ปิดแล้วเปิดใหม่ |
| `ModuleNotFoundError: uvicorn` | ใช้ system Python แทน venv | เรียก `.\.venv\Scripts\python.exe` |
| venv บอกว่าหา base Python ไม่เจอ | ก๊อป `.venv` ข้ามเครื่องมา | ลบ `.venv` แล้วทำ B7/B8 ใหม่ |
| `next build` ขึ้น EPERM symlink | Windows ไม่ให้สร้าง symlink | โปรเจกต์ปิด `output: standalone` ไว้แล้ว ถ้ายังเจอ ให้เปิด Developer Mode |
| launcher บอก `Port 8000 is already in use` | มี API ค้างอยู่ | `Get-NetTCPConnection -LocalPort 8000 -State Listen \| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }` |
| launcher บอกว่า build ไม่สมบูรณ์ | ลืม build หรือ build ค้าง | ลบ `apps\web\.next` แล้ว `pnpm --filter web build` ใหม่ |
| Auto ตกไป LOCAL LIVE + มีบรรทัด `Cloudflared unavailable` | **ยังไม่ได้ทำ B9** หรือเปิดไฟล์ `.bat` ตัวใน repo แทนตัวบน Desktop | ทำ **B9** แล้วเปิดตัวบน Desktop — นี่คือสาเหตุที่พบบ่อยที่สุด |
| Auto ตกไป LOCAL LIVE + มีบรรทัด `Public readiness was not proven` | tunnel ขึ้นได้แต่เน็ตในห้องบล็อก หรือ DNS ยังไม่ทัน | ใช้ Local ได้เลย ไม่ต้องแก้ |
| อัปโหลดแล้ว 401 | มี API ที่เปิด demo mode ค้างบนพอร์ต 8000 | ปิด API นั้น แล้วเปิดผ่าน launcher เท่านั้น |
| browser gate หา Chromium ไม่เจอ | ยังไม่ได้ทำ B10 | `npx playwright install chromium` |
| อีเมลยืนยันชี้ `localhost:3000` | Supabase Site URL ยังเป็น localhost | ทำ **C2** — แก้โค้ดอย่างเดียวไม่พอ |
| ล็อกอินไม่ได้ทั้งที่รหัสถูก | บัญชียังไม่ยืนยันอีเมล | ทำ **C4** กด Confirm email ให้ |
| ล็อกอินพังทุกบัญชี จู่ๆ | Supabase โดน pause | ทำ **C3** กด Restore |
| แก้ env แล้วเว็บยังใช้ค่าเก่า | `NEXT_PUBLIC_*` ฝังตอน build | `npx vercel --prod --archive=tgz` |
| `vercel --prod` ค้างเกิน 5 นาที | คิว build ตัน (free tier build ได้ทีละหนึ่ง) | `npx vercel ls --prod` ดูสถานะ · รอให้ตัวที่ `Building` จบ **อย่ายิงซ้ำ** เพราะจะต่อคิวเพิ่ม |

---

# ปฏิทินถอยหลัง

| วันที่ | ทำอะไร | ใคร |
|---|---|---|
| **31 ก.ค.** | **เส้นทาง C** ให้จบ (Vercel env + Supabase) — ตั้งครั้งเดียว | หัวหน้าทีม |
| **31 ก.ค.** | **เส้นทาง B** บนเครื่องสำรอง (B8 ใช้เวลานาน อย่าไปทำวันแข่ง) | หัวหน้าทีม |
| **1–2 ส.ค.** | ซ้อมพูดคนละบท อย่างน้อย 3 รอบ จับเวลา | ทั้งคู่ · [บทหัวหน้าทีม](PRESENTATION-SCRIPT.md) / [บทคนที่ 2](PRESENTATION-SCRIPT-PARTNER.md) |
| **2 ส.ค.** | ซ้อม**คู่กัน** เน้นจังหวะส่งไม้ | ทั้งคู่ |
| **3 ส.ค.** | ซ้อมเต็มรูปแบบ + **ซ้อมแบบพัง** (ถอดสาย / ปิด launcher กลางทาง) | ทั้งคู่ |
| **1–4 ส.ค.** | แตะ Supabase วันละครั้ง กัน auto-pause (**C3**) | ใครก็ได้ |
| **4 ส.ค.** | **Freeze** (A8) · เตรียม USB · ชาร์จไฟ · ห้ามแตะโค้ด | หัวหน้าทีม |
| **5 ส.ค.** | ใช้ [runbook](RUNBOOK-COMPETITION-DAY.md) อย่างเดียว | ทั้งคู่ |

---

# สิ่งที่ต้องเอาไปวันแข่ง

- [ ] โน้ตบุ๊กเครื่องหลัก + อะแดปเตอร์
- [ ] โน้ตบุ๊กสำรอง (ถ้าทำเส้นทาง B ไว้)
- [ ] USB ที่มี `input.ply` + เอกสาร PDF
- [ ] **runbook ฉบับพิมพ์** — ถ้าจอค้างจะได้ยังอ่านได้
- [ ] สาย HDMI ของตัวเอง + หัวแปลง USB-C
- [ ] ปลั๊กพ่วง
- [ ] มือถือที่แชร์เน็ตได้ (เผื่อ Wi-Fi ในห้องล่ม)
