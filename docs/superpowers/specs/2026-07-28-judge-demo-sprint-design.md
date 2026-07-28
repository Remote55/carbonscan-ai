# TreeQ Judge Demo Sprint — Design Specification

**วันที่:** 2026-07-28

**สถานะ:** Approved design; implementation not started

**วันแข่งขัน:** 2026-08-05

**แนวทางภาพ:** Forest Observatory

**แนวทางเดโม:** Sample-first Hybrid Demo

**แนวทางความเสถียร:** Ephemeral Runtime Handoff + Local Live + Frozen Evidence

## 1. บริบทและปัญหา

TreeQ Carbon Platform มี ML core path, synchronous API, async-job prototype, landing page และ 3D viewer ที่ใช้งานได้แล้ว แต่เส้นทางสาธิตยังเปราะบางและเล่าเรื่องไม่ต่อเนื่อง การเปิดเดโมปัจจุบันต้องรัน API, เปิด Cloudflare Quick Tunnel, เปลี่ยน `NEXT_PUBLIC_API_URL` และ deploy Vercel ใหม่ ทุกครั้งที่ tunnel เปลี่ยน URL จึงเสี่ยงติดขั้น login, project link, network หรือ deploy โค้ดจาก branch เก่า

หน้าเว็บปัจจุบันสื่อทิศทางธรรมชาติได้ แต่ hero แน่นเกินไป หน้าผลลัพธ์มีลักษณะเหมือนตารางหลังบ้าน และ UI เรียก `summary.total_trees` ว่า “จำนวนต้นไม้” ทั้งที่ pipeline ตัด tree segment บางต้นออกด้วย `continue` เมื่อไม่มี wood points หรือ QSM คืน DBH/height ที่ไม่ valid กรรมการจึงเห็นเลข ID ขาดโดยไม่มีคำอธิบาย

Sprint นี้สร้างเส้นทางเดโมบน desktop เพียงเส้นทางเดียวให้พร้อมแข่งขันภายใน 3–5 นาที โดยรักษาหลัก honesty ethos: `tlsep` เป็น default, PointNet++ เป็น Experimental, ตัวเลขมาจาก evidence และทุก fallback ระบุสถานะจริง

## 2. เป้าหมาย

1. เปิด Judge Demo ด้วย launcher เพียงไฟล์เดียว โดยไม่ deploy Vercel ตอนเริ่มเดโม
2. ให้กรรมการเข้าใจปัญหา วิธีทำงาน ผลคาร์บอน และ provenance ภายใน 4 นาทีในรอบปกติ
3. รองรับ Live Upload เมื่อกรรมการร้องขอ โดยใช้ pipeline และ API จริง
4. รองรับ Production Live, Local Live และ Frozen Evidence โดยไม่สวมรอยว่า fallback เป็น live run
5. แสดงจำนวน detected, measured และ excluded พร้อม reason code จาก pipeline
6. ปรับ landing และ results workspace ให้เป็น Forest Observatory ที่เรียบ หรู และมีเอกลักษณ์ TreeQ
7. Freeze commit, build, demo data, result, manifest และวิดีโออย่างน้อย 24 ชั่วโมงก่อนแข่งขัน

## 3. สิ่งที่ไม่อยู่ในขอบเขต

Sprint นี้ไม่รวม:

- การ train species classifier; ขั้นที่ 7 ยังคงเป็น `Stub`
- การ promote PointNet++; `tlsep` ยังคงเป็น default
- mobile completion, marketplace, payment, certification หรือ carbon-credit issuance
- production GPU deployment บน Railway หรือ RunPod
- การเปลี่ยนสูตรหรือ coefficient ใน `species_db.csv`
- การ redesign ทุกหน้าของ dashboard
- การสร้าง canvas/WebGL animation บน landing page
- การรับไฟล์ point cloud ทุก dialect, scale หรือ schema โดยไม่มีข้อจำกัด

## 4. Decisions ที่อนุมัติแล้ว

### 4.1 Forest Observatory

หน้าเว็บใช้ความโปร่งแบบ gallery, serif headline, split composition และธรรมชาติเป็นจุดนำสายตา งานอ้างอิงคือ [EcoTech Exhibition Landing Page](https://dribbble.com/shots/26497016-EcoTech-Exhibition-Landing-Page-Nature-UI-UX-Design) แต่ TreeQ จะไม่คัดลอกภาพ, layout pixel-for-pixel หรือ asset ของผู้สร้าง ภาพหลักต้องสื่อ point cloud, wood/leaf และ QSM ของ TreeQ

### 4.2 Sample-first Hybrid Demo

CTA หลักเปิด frozen sample ที่ตรวจ hash แล้วโดยไม่บังคับ login หรือ file picker ปุ่มรอง “Live Upload .PLY” รัน API จริงเมื่อกรรมการร้องขอ ทั้งสองเส้นทางใช้ results workspace เดียวกัน

### 4.3 Ephemeral Runtime Handoff

Launcher เปิด local API, local web และ Cloudflare Quick Tunnel จากนั้นเปิด production URL พร้อม API endpoint และ token ใน URL fragment:

```text
https://treeqcarbon.vercel.app/demo#api=<encoded-url>&token=<ephemeral-token>
```

URL fragment ไม่ถูกส่งไปกับ HTTP request ของ Vercel เว็บอ่านค่าเพียงครั้งเดียว เก็บไว้ใน `sessionStorage` ของ tab ปัจจุบัน และลบ fragment ออกจาก address bar ด้วย `history.replaceState`

### 4.4 Three honest modes

ระบบมีสามโหมด:

| Mode | Web | API | ป้ายใน UI |
|---|---|---|---|
| Production Live | Vercel production alias | Local API ผ่าน authenticated Quick Tunnel | `LIVE ANALYSIS` |
| Local Live | Local frozen web build | `127.0.0.1:8000` | `LOCAL LIVE MODE` |
| Frozen Evidence | Vercel หรือ local web | ไม่ใช้ API | `FROZEN EVIDENCE — NOT A LIVE RUN` |

UI ต้องใช้ mode จาก state machine กลาง ห้ามให้ component ตั้งป้ายเองจากการคาดเดา

## 5. Judge Journey

เส้นทางปกติมีห้าจังหวะ:

1. **00:00 — Why:** Landing อธิบายว่า TreeQ เปลี่ยน 3D point cloud เป็นค่าประเมินคาร์บอนที่ตรวจสอบย้อนกลับได้
2. **00:35 — Input:** Demo route แสดง frozen artifact, provenance, hash และปุ่ม `ใช้ชุดข้อมูลสาธิต` กับ `Live Upload .PLY`
3. **00:55 — How:** Sync API แสดงสถานะที่ยืนยันได้จริงเท่านั้น: ตรวจไฟล์, อัปโหลด, กำลังประมวลผลแบบ indeterminate และเสร็จสิ้น แผนผัง 8 ขั้นอธิบาย pipeline ได้ แต่ห้ามขยับ highlight หรือเปอร์เซ็นต์เองเมื่อ API ไม่ได้รายงาน stage
4. **02:15 — Result:** Results workspace แสดง 3D Wood/Leaf/QSM, CO₂e estimate, detected/measured/excluded และ tree table
5. **03:25 — Trust:** Provenance panel แสดง input hash, pipeline version, Git commit, algorithm map, allometric source และ limitations

รอบปกติต้องจบภายใน 4 นาที รอบ Live Upload ต้องจบภายใน 5 นาทีเมื่อใช้ known-good `.ply`

## 6. Visual System

### 6.1 Palette

| Token | ค่าเริ่มต้น | หน้าที่ |
|---|---|---|
| Forest Ink | `#17211B` | ข้อความหลัก |
| Moss | `#6F9028` | CTA และ state ที่พร้อม |
| Deep Forest | `#173A29` | 3D viewer และ evidence surfaces |
| Gallery Ivory | `#F5F6F1` | พื้นหน้าเว็บ |
| Mist | `#B9C1C6` | พื้นกรอบและ section contrast |
| Evidence Amber | `#B28A40` | Excluded, limitation และ freeze warning |

สีต้องผ่าน contrast สำหรับข้อความตาม WCAG AA ในขนาดที่ใช้จริง

### 6.2 Typography

- Thai headline ใช้ serif Thai แบบ self-hosted ที่เก็บใน repo และโหลดผ่าน `next/font/local` พร้อม system fallback เพื่อให้ local/offline build ไม่พึ่ง font CDN
- UI, table และ technical metadata ใช้ sans-serif Thai ที่อ่านง่าย
- ตัวเลขผลลัพธ์ใช้ tabular numerals เมื่อเปรียบเทียบเป็นคอลัมน์
- Landing แสดง `0.418`, `0.808` และ `1.167 cm` เพื่ออ่านบนเวที Evidence panel แสดง DBH MAE เต็ม `1.1673846154 cm` พร้อม cohort และ scope

การแสดงเลขสามตำแหน่งบน hero เป็น display formatting ไม่ใช่การเปลี่ยน evidence

### 6.3 Landing

Landing ยังคงเป็น Tailwind server component ห้ามใช้ styled-jsx และ canvas 3D Hero ใช้ split layout: visual ทางซ้าย, headline และ CTA ทางขวา แถบ evidence ด้านล่างแสดง `tlsep baseline`, Wan held-out metrics และ Demol DBH metric พร้อมข้อจำกัด

CTA หลักคือ `เริ่ม Judge Demo` CTA รองคือ `ดูผลทดสอบจริง` เมนู mobile/species/marketplace ไม่อยู่ใน judge path

### 6.4 Results workspace

Results workspace แบ่งเป็น:

- 3D viewer พร้อม `Wood / Leaf`, `QSM` และ `Original` modes เฉพาะ mode ที่มี artifact จริง; หาก API คืนเฉพาะ summary ให้แสดง original preview และระบุว่า segmented/QSM artifact unavailable ห้ามสร้างภาพแทนผลจริง
- Carbon estimate card ที่ระบุว่าไม่ใช่ certified carbon credit
- Counts: `ตรวจพบ`, `คำนวณสำเร็จ`, `ไม่รวมผล`
- Tree table ที่แสดง measured และ excluded segments
- Provenance panel
- Mode badge จาก state machine

หน้า 1440×900 และ 1366×768 ต้องไม่ตัด Thai headline, CTA หรือ mode badge และต้องไม่มี horizontal page scroll

## 7. Runtime Components

| Component | หน้าที่ | Dependency |
|---|---|---|
| `TreeQ-Demo-Start.bat` | จุดเริ่มต้นเดียวสำหรับผู้ใช้ | PowerShell orchestrator |
| `start-treeq-demo.ps1` | Preflight, process lifecycle, tunnel, token และ browser handoff | API/ML venv, Node build, cloudflared |
| FastAPI demo middleware | ตรวจ ephemeral token และ CORS | `TREEQ_DEMO_TOKEN` |
| Runtime endpoint resolver | อ่านและ validate URL fragment | Browser session only |
| Demo mode state machine | เลือก Production Live, Local Live หรือ Frozen Evidence | health challenge |
| Frozen evidence loader | โหลด manifest/result ที่ตรวจ hash | frozen bundle |
| Pipeline diagnostics | บันทึก excluded segment และ reason code | ML pipeline |
| Results workspace | แสดง 3D, metrics, diagnostics และ provenance | typed API/frozen contract |

Canonical scripts ต้องอยู่ใน repo ใต้ `scripts/demo/` Desktop script เดิมทำหน้าที่เป็น thin wrapper เท่านั้น เพื่อไม่ให้สคริปต์นอก version control เป็น source of truth

## 8. Launcher Design

Launcher ทำงานตามลำดับนี้:

1. ตรวจ frozen manifest, artifact hashes และ expected Git commit
2. ตรวจ API venv, ML venv, imports, Node runtime, local web build และ `cloudflared`
3. ตรวจว่าพอร์ต 8000 และ 3000 ว่าง หรือเป็น process ของ TreeQ ที่ launcher เดิมสร้าง
4. สร้าง random token อย่างน้อย 256 bits ด้วย CSPRNG
5. เปิด local API ด้วย token และ CORS allowlist
6. เปิด local production web build ที่พอร์ต 3000
7. เปิด Quick Tunnel แล้ว parse URL จาก machine-readable output/log
8. เรียก authenticated readiness challenge ผ่าน public URL
9. เปิด production judge URL เมื่อ tunnel พร้อม
10. เปิด local judge URL หาก internet, Vercel หรือ tunnel ไม่พร้อม
11. ให้ผู้ใช้เลือก Frozen Evidence หาก API readiness ล้มเหลว

Launcher ห้าม:

- เรียก `vercel env add` หรือ `vercel --prod`
- kill `cloudflared` หรือ Python ทุก process ในเครื่อง
- พิมพ์ token ใน console หรือ log
- ใช้ emoji ใน Python output บน Windows
- เปลี่ยน branch, pull, reset หรือ checkout อัตโนมัติ

Launcher ต้องเก็บ PID ของ process ที่สร้างและปิดเฉพาะ PID เหล่านั้น Log ใช้ ASCII, ปิดบัง token และเก็บไว้ใน local ignored directory

## 9. Runtime Handoff and Security

### 9.1 Endpoint validation

Web รับ API endpoint เฉพาะ:

- `https://<random>.trycloudflare.com`
- `http://127.0.0.1:8000`
- `http://localhost:8000`

ระบบปฏิเสธ scheme, port และ hostname อื่น ห้าม persist endpoint ลง database หรือ analytics

### 9.2 Token behavior

- Token มีอายุเท่ากับ API process
- Client ส่ง token ใน `X-TreeQ-Demo-Token`
- Token ปกป้อง analyze และ job endpoints ที่ใช้ในเดโม
- Liveness endpoint เปิดเผยเฉพาะ status/version; readiness challenge ต้องใช้ token
- API เปรียบเทียบ token แบบ constant-time
- Logs, exceptions และ UI ห้ามแสดง token
- Judge route ไม่โหลด third-party analytics หรือ script ที่อาจส่ง URL fragment ออกนอก session และต้องลบ fragment ด้วย `history.replaceState` ก่อน render เนื้อหาหรือเริ่มบันทึกหน้าจอ

### 9.3 Upload privacy

- ใช้ `.ply` เป็น Live Upload contract ของ Judge Demo
- ตรวจ extension, content signature/parser compatibility, file size และ point count ก่อนรัน
- Demo contract จำกัดไฟล์ไม่เกิน 100 MB และไม่เกิน 2,000,000 จุด; browser preview downsample ได้แต่ server ต้องคำนวณจาก input ที่ผ่าน validation จริง
- Sync endpoint ลบ temp input และ output ใน `finally`
- Error response ห้ามคืน filesystem path, subprocess command หรือ raw stderr เต็ม
- Demo data ที่ commit หรือบันทึกวิดีโอต้องไม่มีข้อมูลส่วนบุคคล

Quick Tunnel ทำให้ endpoint เข้าถึงได้จาก internet ระหว่าง session จึงต้องใช้ token, strict CORS, upload limit และ rate limit ทุกครั้ง

## 10. Live Upload Behavior

ปุ่ม Live Upload เปิดเมื่อ authenticated readiness ผ่านเท่านั้น เมื่อผู้ใช้เลือกไฟล์ ระบบ:

1. Parse `.ply` ใน browser เพื่อ preview และตรวจจำนวนจุด
2. แสดงชื่อไฟล์, ขนาด และ client-side SHA-256
3. ขอการยืนยันก่อนส่งไฟล์ไปยัง API
4. ส่งไฟล์พร้อม ephemeral token
5. แสดงสถานะที่พิสูจน์ได้จริง โดยช่วงประมวลผลของ sync API เป็น indeterminate; ห้ามจำลองเปอร์เซ็นต์หรือ stage timing
6. แสดง result และ server-side normalized XYZ hash แยกจาก raw file hash

หากกรรมการนำไฟล์มาเอง UI ต้องแสดง contract ที่รองรับและรายงาน validation error ตามจริง Known-good upload file สร้างจาก deterministic core-demo generator ของโปรเจกต์ระหว่าง freeze, อยู่ใน local frozen demo pack และมี input hash ใน manifest จึงไม่ต้องนำข้อมูลภายนอกที่ license ยังไม่ชัดมาใช้

## 11. Pipeline Diagnostics Contract

ปัจจุบัน `services/ml/pipeline/main.py` ตัด segment ออกแบบเงียบที่สองจุด:

- ไม่มี wood points หลัง wood/leaf separation
- QSM คืน `dbh_cm <= 0` หรือ `height_m <= 0`

Sprint นี้เปลี่ยน silent drop เป็น typed diagnostic โดยไม่เปลี่ยน measurement algorithm

```json
{
  "summary": {
    "total_trees": 18,
    "detected_trees": 20,
    "measured_trees": 18,
    "excluded_trees": 2,
    "total_carbon_kg": 25400.58,
    "total_co2eq_kg": 93135.0
  },
  "diagnostics": {
    "excluded_segments": [
      {
        "tree_id": 11,
        "stage": "wood_leaf",
        "reason_code": "WOOD_EMPTY"
      },
      {
        "tree_id": 17,
        "stage": "qsm",
        "reason_code": "QSM_INVALID"
      }
    ]
  }
}
```

Contract rules:

- `total_trees` คงไว้เพื่อ backward compatibility และเท่ากับ `measured_trees`
- `detected_trees == measured_trees + excluded_trees`
- `len(excluded_segments) == excluded_trees`
- `reason_code` รอบแรกมี `WOOD_EMPTY` และ `QSM_INVALID`
- Unexpected exception ทำให้ run ล้มเหลวทั้ง run ห้ามแปลงเป็น excluded แบบเงียบ
- Web map reason code เป็นข้อความภาษาไทย ห้ามเดาเหตุผลจาก ID ที่หาย

JSON ข้างต้นเป็นตัวอย่าง schema ไม่ใช่ผลทดสอบ ตัวเลข `20 / 18 / 2` และ `93.135 tCO₂e` ใน mockup มาจากภาพผลลัพธ์ที่ใช้ระหว่างออกแบบ แต่ยังไม่มี manifest หรือ input artifact ใน repo จึงเป็น layout fixture ไม่ใช่ frozen evidence Implementation ต้องอ่านตัวเลขจาก API หรือ frozen result ที่ผ่าน hash verification เท่านั้น ห้าม hard-code ค่าเหล่านี้

## 12. Frozen Evidence Bundle

Frozen fallback ขั้นต่ำใช้ deterministic core demo ที่มีหลักฐานอยู่แล้วใน:

- `docs/evidence/core_demo_manifest.json`
- `apps/web/src/generated/core-demo-evidence.ts`
- deterministic client-side demo point cloud

Sprint เพิ่ม `docs/evidence/judge_demo_manifest.json` เพื่อผูกข้อมูลต่อไปนี้เป็น release เดียว:

- Git commit และ dirty state
- web build identity
- API/ML version
- source core-demo manifest hash
- frozen result JSON hash
- segmented viewer artifact hash หรือ deterministic generator identity
- deterministic known-good `.ply` ที่สร้างจาก core-demo generator พร้อม input hash
- backup video hash

Showcase plot แบบหลายต้นใช้ได้ต่อเมื่อ provenance, privacy, license, input hash, result hash และ diagnostics ครบก่อน freeze หากไม่ผ่าน gate ระบบใช้ deterministic core demo เป็น frozen fallback และไม่แสดงตัวเลขจาก mockup

Frozen UI ต้องแสดงข้อความ `FROZEN EVIDENCE — NOT A LIVE RUN` ใกล้ผลรวมและ provenance

## 13. Error Handling and Mode Transitions

| Failure | การตอบสนอง |
|---|---|
| Preflight dependency ขาด | หยุดก่อนเปิดเดโม แสดง remediation ที่เจาะจง |
| Quick Tunnel เปิดไม่ได้ | เปิด Local Live Mode |
| Production URL หรือ internet ใช้ไม่ได้ | เปิด Local Live Mode |
| API readiness ล้มเหลว | เสนอ Retry หรือ Frozen Evidence |
| Upload validation ล้มเหลว | ไม่ส่งไฟล์ แสดงข้อกำหนดที่ไม่ผ่าน |
| Pipeline timeout/error | แสดง run failed และ stderr tail ที่ sanitize แล้วใน operator log; UI ไม่แสดง internals |
| Frozen hash ไม่ตรง | Fail closed; ห้ามเปิด artifact นั้น |
| Runtime response ไม่มี diagnostics fields | แสดง `diagnostics unavailable`; ห้ามแสดง excluded เป็นศูนย์ |

State machine ห้ามเปลี่ยนจาก Frozen เป็น Live จนกว่า authenticated readiness จะผ่านใหม่

## 14. Testing and Release Gates

### 14.1 Automated gates

- Web: unit tests, typecheck, lint และ production build
- API: pytest รวม token middleware, CORS, upload validation และ schema invariants
- ML: pytest รวม reason codes และ count invariant
- Launcher helpers: PowerShell assertion harness ใน repo ที่ไม่พึ่ง module ภายนอก สำหรับ parsing, redaction, hash verification และ process ownership; CI เรียก harness นี้โดยตรง
- Frozen contract: generated TypeScript, JSON และ manifest ต้อง sync กัน
- Secret scan: token, private path และ raw data ห้ามเข้า commit

### 14.2 Manual gates

- Cold start จากไม่มี process เดิม 3 รอบติด
- ฆ่า tunnel แล้วเข้า Local Live Mode
- ตัด internet แล้วเปิด local web + local API
- หยุด API แล้วเปิด Frozen Evidence
- Live Upload ด้วย known-good `.ply`
- Chrome ที่ 1440×900 และ 1366×768
- Judge Journey ปกติไม่เกิน 4 นาที
- Live Upload ไม่เกิน 5 นาที
- Forced-failure rehearsal ไม่เกิน 4 นาที 30 วินาที

Release ผ่านเมื่อทุก gate เป็น green ไม่มีการยกเว้นด้วย `|| true`

## 15. Freeze Policy

กำหนด freeze ไม่ช้ากว่า 24 ชั่วโมงก่อน competition call time วันที่ 5 สิงหาคม 2026 Freeze package ประกอบด้วย:

- Git tag และ clean commit
- production web build และ local web build
- launcher scripts
- judge demo manifest และ artifacts
- known-good upload file
- backup video 1080p
- presenter script และ failure-response script

หลัง freeze แก้ได้เฉพาะ blocker ที่ทำให้เดโมเปิดไม่ได้ ทุก emergency change ต้องบันทึกเหตุผลและรัน automated gates, three-mode failure tests และ rehearsal ใหม่ ห้ามแก้ cosmetic นาทีสุดท้าย

## 16. Implementation Boundaries

- Landing แยกเป็น focused server components แทนการขยาย `apps/web/src/app/page.tsx` ให้ใหญ่ขึ้น
- Results workspace แยก client state, runtime endpoint resolver, mode state machine, viewer, summary, diagnostics table และ provenance panel
- ML diagnostics เพิ่มข้อมูลรอบ silent-drop points เท่านั้น ไม่ refactor algorithm อื่น
- API demo token แยกจาก Supabase auth และเปิดใช้เฉพาะเมื่อ `TREEQ_DEMO_MODE=1`
- Async-job deployment ไม่อยู่ใน golden path และไม่ต้อง migration database ใน sprint นี้
- External desktop script เป็น wrapper; canonical implementation และ tests อยู่ใน repo

## 17. Risks and Controls

### Quick Tunnel เป็น public endpoint

ควบคุมด้วย ephemeral token, strict allowlist, rate limit, file limit และ process lifetime

### Local web build stale

Manifest ผูก build identity กับ expected commit Launcher ปฏิเสธ build ที่ไม่ตรง

### Frozen evidence ถูกเข้าใจว่า live

Mode badge, copy และ provenance ระบุ `NOT A LIVE RUN` ในตำแหน่งที่เห็นก่อนตัวเลข

### UI แสดงเหตุผลที่ pipeline ไม่ได้ส่ง

Contract บังคับ typed diagnostics Web แสดง `unavailable` แทนการอนุมาน

### งาน UX กระทบ core path ใกล้วันแข่ง

แยก visual components จาก API/ML changes ทำ P0 reliability ก่อน P1 polish และ freeze cosmetic changes ก่อนวันจริง

## 18. Acceptance Criteria

Design นี้ถือว่า implemented เมื่อครบทุกข้อ:

1. ผู้ใช้เปิดเดโมจาก launcher เพียงไฟล์เดียวโดยไม่ deploy Vercel
2. Production Live, Local Live และ Frozen Evidence ผ่าน failure-injection tests
3. Token ไม่ปรากฏใน query string, console, logs, UI หรือ committed files
4. Judge Journey ไม่บังคับ login และ sample-first ทำงานได้
5. Live Upload ใช้ API จริงและปิดเมื่อ readiness ไม่ผ่าน
6. API/ML คืน detected, measured, excluded และ reason codes ตาม invariant
7. Results workspace แสดง estimate, diagnostics, provenance และ limitation ครบ
8. Landing และ results ผ่าน Chrome viewport gates
9. Frozen manifest และ artifacts ผ่าน hash verification
10. Automated tests และ CI ผ่านทั้งหมด
11. Rehearsal ปกติ, upload และ failure ผ่านเวลาที่กำหนด
12. Freeze package เปิดได้จริงจาก local copy และ backup video
13. PointNet++ ยังแสดงเป็น Experimental และ `tlsep` ยังเป็น default
14. UI ไม่เรียก CO₂e estimate ว่า certified หรือ tradable carbon credit

เมื่อ acceptance criteria ครบ TreeQ มี demo ที่สวย เสถียร และซื่อสัตย์พอสำหรับการแข่งขัน โดยไม่ขยาย scope ไปยังฟีเจอร์ที่ยังไม่มีหลักฐาน
