# Forest Observatory — Implementation Freeze Evidence

**วันที่:** 2026-07-30
**Branch:** `codex/web-visual-redesign-impl`
**สถานะ:** Frozen partial — Tasks 1–6, 9, 10 implemented and verified · **Tasks 7–8 not implemented**

> เอกสารนี้คือหลักฐานว่า freeze gate รันแล้วได้ผลอะไร ไม่ใช่คำประกาศว่าเสร็จทั้งแผน
> สิ่งที่ยังไม่ทำถูกระบุไว้ชัดเจน เพราะการปิดงานโดยไม่บอกว่าเหลืออะไรคือปัญหาเดียวกับ
> ที่ระบบนี้ทั้งระบบถูกออกแบบมาเพื่อป้องกัน

---

## 1. Gate results

รันจาก `run-gates.ps1` (คำสั่งเดียว เรียงตัว — สอง npm บน Windows แย่ง pnpm store กัน):

| Gate | ผล |
|---|---|
| Unit tests | **PASS** — 122 tests / 22 files |
| Type-check | **PASS** |
| Lint (`--max-warnings=0`) | **PASS** |
| Production build | **PASS** — 10 static pages |
| Judge journey (browser) | **PASS** — 38 runs (19 checks × 2 viewports) |
| Forbidden-claim scan | **clean** |

### Forbidden-claim scan

```
93\.135|25,400\.58|18 calculated|20 detected|จำนวนต้นไม้|PointNet\+\+.*default|certified carbon credit|รองรับ \.las|รองรับ \.laz
```

ผลลัพธ์ในไฟล์ source: **ไม่พบ**

Hit ที่เจอมีสองรายการและทั้งคู่อยู่ใน**ไฟล์เทสต์**:

- `page.test.tsx:31` — `expect(markup).not.toContain('93.135')`
- `result-rail.test.tsx:90` — ชื่อเทสต์ที่ยืนยันว่าต้องมีประโยค non-certification

ทั้งสองคือ**ตัวป้องกัน ไม่ใช่การละเมิด** สคริปต์จึงกรองไฟล์ `*.test.*` ออก

> **ช่องโหว่ของ pattern ที่ควรรู้:** มันจับเฉพาะ `รองรับ .las` ถ้ามีใครเขียน
> `อัปโหลด .las` หรือ `ใช้ .laz ได้` ก็จะหลุด — pattern นี้กันคำ ไม่ได้กันความหมาย

### Asset scan

```
git ls-files apps/web/public/visual apps/web/src/assets/fonts   → 13 ไฟล์
rg -i "wallhaven|dribbble" apps/web/src apps/web/public          → 1 hit
```

13 ไฟล์: รูป production 4 (`landing-mist` · `judge-road` · `auth-lake` · `dashboard-road`) + `ASSETS.md` + ฟอนต์ 5 + OFL license 3

Hit เดียวอยู่ใน `ASSETS.md` ซึ่ง**บันทึกว่า Wallhaven กับ Dribbble ไม่ได้ถูกใช้เป็น production reference** — เป็น provenance record ที่ควรมี ไม่ใช่การละเมิด

---

## 2. Accepted deviations จาก Figma

### 2.1 Clay token `#A65F46` → `#8F5039`

Figma กำหนด `#A65F46` ซึ่ง**ผ่าน WCAG AA เฉพาะบน Paper เท่านั้น** (4.67:1) แต่ token นี้
ถูกใช้บนพื้นอื่นด้วย:

| การใช้งานจริง | contrast เดิม |
|---|---|
| `EXCLUDED` ในตารางรายต้น (10px) บนแถว Gallery Ivory | **4.28:1** ❌ |
| ข้อความ error ใน UploadDropzone (14px) บน tint `bg-clay/10` ที่ composite ได้ `#F3EBE5` | **4.10:1** ❌ |
| `Experimental` ใน provenance บน Paper | 4.67:1 ✅ |

**สองในสามการใช้งานไม่ผ่าน** จึงแก้ที่ token ไม่ใช่ที่ call site — เพราะข้อความ error
ไม่เคยถูกจำกัดอยู่บนพื้นเดียว ค่าที่ผ่านแค่บน Paper จะพังทุกครั้งที่ไปโผล่บนพื้นใหม่

ค่าใหม่: 5.5:1 (Ivory) · 6.0:1 (Paper) · 5.2:1 (tint) — มีระยะเหลือทุกกรณี

> **บทเรียนของ tint:** Tailwind composite `bg-clay/10` ใน sRGB ดังนั้น contrast ของ
> ข้อความที่อยู่บนนั้นขึ้นกับ**สีที่ผสมแล้ว** ไม่ใช่ token ตั้งต้นทั้งสองตัว — ซึ่งดูดีทั้งคู่
> เมื่อวัดแยกกัน `src/test-support/wcag.ts` มีฟังก์ชัน compositing สำหรับกรณีนี้

**Figma ต้องอัปเดต variable ตามค่านี้** ถ้าไม่อัปเดต Task ต่อไปที่ generate จาก Figma
จะย้อนบั๊กกลับมา

### 2.2 ไม่ทำ screenshot baseline

Plan Task 10 ขอ approved screenshot baselines — **ตัดสินใจไม่ทำ**

Results workspace render **WebGL canvas** ผ่าน Three.js ดังนั้น baseline ที่ commit
ไว้จะฝัง GPU และการ rasterize ฟอนต์ของเครื่องนี้ลงไป แล้วแดงบนเครื่องอื่น
**gate ที่แดงเพราะ antialiasing ต่างกัน 2 pixel ในสัปดาห์แข่ง เสียมากกว่าที่มันป้องกัน**

ทุกข้อที่ plan อยากให้ screenshot เฝ้า วัดจาก DOM ได้และ assert ไว้แล้วใน
`e2e/judge-journey.spec.ts`:

| plan ขอให้ตรวจ | assert ที่ไหน |
|---|---|
| Frozen copy | `FROZEN EVIDENCE — NOT A LIVE RUN` ต้องมี 2 ที่ (header + ข้างผลลัพธ์) |
| Calculated label | `ต้นไม้ที่คำนวณสำเร็จ` ต้องมี · `จำนวนต้นไม้` ต้องไม่มี |
| Non-certification | ประโยคต้องมองเห็น |
| Synthetic viewer label | `SYNTHETIC · NOT PIPELINE EVIDENCE` |
| Document width | `scrollWidth - clientWidth ≤ 0` ทั้ง 5 route × 2 viewport + 600px |

---

## 3. Code Connect — ยังไม่ทำ

Plan ระบุเงื่อนไขเองว่า *"ทำ Code Connect หลัง source components ครบ"*

**เงื่อนไขยังไม่ครบ** — Task 7 (AuthPanel) และ Task 8 (dashboard overview) ยังไม่ได้
implement ดังนั้น component ใน Figma อีก 2 ตัว (`AuthPanel 30:38`, และ dashboard
composition ที่ `39:2`) ยังไม่มี source ให้ map

ทำ Code Connect ตอนนี้จะได้ mapping ที่ไม่ครบและต้องรื้อทำใหม่

---

## 4. สิ่งที่ยังไม่ได้ทำ

| Task | สถานะ | ผลกระทบต่อการสาธิต |
|---|---|---|
| **7 — Login/Signup** | ไม่ได้ทำ | หน้า auth ยังเป็นดีไซน์เดิม (shadcn) **ไม่อยู่ในเส้นทางกรรมการ** |
| **8 — Observatory Dashboard** | ไม่ได้ทำ | dashboard ยังเป็นดีไซน์เดิม **ไม่อยู่ในเส้นทางกรรมการ** |
| **11 — Code Connect** | ไม่ได้ทำ | ไม่กระทบ runtime |
| **11 — Figma visual compare ทุก node** | ทำบางส่วน | เทียบด้วยการวัด DOM ไม่ได้เทียบภาพต่อภาพ |

> หน้า `/login`, `/signup`, `/dashboard/viewer` **ผ่าน browser gate เรื่อง overflow แล้ว**
> ทั้งสอง viewport แม้ยังไม่ถูก redesign — คือใช้งานได้และไม่พัง แค่ยังไม่ได้ตกแต่ง

### Deferred minors (จาก ledger)

- `provenance-panel.test.tsx` ยังเก็บ WCAG math ของตัวเองแทนที่จะ import `test-support/wcag.ts`
- ยังไม่มี sentinel manifest กัน hard-coded fixture ใน provenance test
- Table test ยังไม่ตรวจ `tabular-nums` ทุก measurement cell
- `design-system.test.tsx` ยังไม่ครอบ editorial semantic styling กับ legacy Button variant แยกทุกกรณี
- Keyframes `fade-in` / `slide-up` / `accordion-*` ใน `tailwind.config.ts` **ไม่มีที่ไหนใช้** — ซากจาก landing เดิม ควรลบตอน cleanup

---

## 5. สิ่งที่ต้องทำก่อน merge เข้า main

Redesign นี้**แทน UI ที่ผ่านการซ้อม launcher จริงมาแล้ว** แต่ตัวมันเอง**ยังไม่เคยถูกซ้อม
กับ launcher** — browser gate รันบน `next start` ที่พอร์ต 3100 ไม่ได้ผ่าน
`start-treeq-demo.ps1` และไม่ได้ผ่าน runtime handoff จริง

**ต้องซ้อมตาม `docs/RUNBOOK-COMPETITION-DAY.md` ให้ผ่านทั้ง 3 โหมดก่อน merge**
ถ้าซ้อมไม่ทันก่อน 4 ส.ค. — **อย่า merge** ใช้ของที่ซ้อมผ่านแล้วไปแข่ง

---

## 6. Commits

```
17f4eea fix(web): harden responsive and accessible presentation   (Task 6 fix + Task 9)
a0d9f2a test(web): gate the judge journey in a real browser        (Task 10)
```

Task 1–6 commit history อยู่ใน `docs/design/2026-07-30-treeq-web-redesign-handoff.md` §10
