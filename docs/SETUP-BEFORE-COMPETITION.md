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
                 'C:\Users\Acer\OneDrive\Desktop\CarbonScrip\cloudflared.exe')) {
  if (Test-Path $v) { Write-Host "  OK   $v" } else { Write-Host "  MISS $v" }
}
```

**ผลที่ต้องได้เมื่อ 29 ก.ค. 69 — ต้องเป็น OK ทั้ง 7 บรรทัด**

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

## A5. รันเทสต์ทั้งหมด (5 นาที)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Project_Carbon\scripts\demo\tests\run-tests.ps1
```
ต้องจบด้วย `TESTS PASSED`

```powershell
pnpm --filter web exec vitest run
```
ต้องได้ `Test Files ... passed`

> ต้องใส่คำว่า `run` — `pnpm --filter web test` เข้า watch mode แล้วค้าง ไม่จบให้

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

## B9. ติดตั้ง cloudflared (5 นาที)

โหลด `cloudflared-windows-amd64.exe` จาก
<https://github.com/cloudflare/cloudflared/releases>

เปลี่ยนชื่อเป็น `cloudflared.exe` แล้วเก็บไว้ในโฟลเดอร์เดียว เช่น `C:\tools\`

```powershell
C:\tools\cloudflared.exe --version
```

บอก launcher ว่าอยู่ไหน:

```powershell
$env:TREEQ_CLOUDFLARED = 'C:\tools\cloudflared.exe'
```

หรือส่งเป็นพารามิเตอร์ทุกครั้ง: `-CloudflaredPath C:\tools\cloudflared.exe`

## B10. Build + ตรวจทั้งหมด

ทำตาม **A4 → A7** ทุกข้อ

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
| Auto ตกไป LOCAL LIVE ทุกครั้ง | เน็ตบล็อก cloudflared หรือ tunnel ขึ้นไม่ได้ | ใช้ Local ได้เลย ไม่ต้องแก้ |
| อัปโหลดแล้ว 401 | มี API ที่เปิด demo mode ค้างบนพอร์ต 8000 | ปิด API นั้น แล้วเปิดผ่าน launcher เท่านั้น |

---

# ปฏิทินถอยหลัง

| วันที่ | ทำอะไร |
|---|---|
| **31 ก.ค.** | ทำ **เส้นทาง B** บนเครื่องสำรองให้จบ (ขั้น B8 ใช้เวลานาน) |
| **1–2 ส.ค.** | ซ้อมพูดตาม [บทนำเสนอ](PRESENTATION-SCRIPT.md) จับเวลาจริง อย่างน้อย 3 รอบ |
| **3 ส.ค.** | ซ้อมเต็มรูปแบบ: เปิด launcher → พูด → อัปโหลด → ตอบคำถามที่ซ้อมไว้ |
| **4 ส.ค.** | **Freeze** (A8) · เตรียม USB · ชาร์จไฟ · ห้ามแตะโค้ด |
| **5 ส.ค.** | ใช้ [runbook](RUNBOOK-COMPETITION-DAY.md) อย่างเดียว |

---

# สิ่งที่ต้องเอาไปวันแข่ง

- [ ] โน้ตบุ๊กเครื่องหลัก + อะแดปเตอร์
- [ ] โน้ตบุ๊กสำรอง (ถ้าทำเส้นทาง B ไว้)
- [ ] USB ที่มี `input.ply` + เอกสาร PDF
- [ ] **runbook ฉบับพิมพ์** — ถ้าจอค้างจะได้ยังอ่านได้
- [ ] สาย HDMI ของตัวเอง + หัวแปลง USB-C
- [ ] ปลั๊กพ่วง
- [ ] มือถือที่แชร์เน็ตได้ (เผื่อ Wi-Fi ในห้องล่ม)
