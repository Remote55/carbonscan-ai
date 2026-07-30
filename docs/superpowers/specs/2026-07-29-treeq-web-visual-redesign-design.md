# TreeQ Web Visual Redesign — Design Specification

**วันที่:** 2026-07-29  
**สถานะ:** Approved Figma design; ready for implementation planning
**แนวทางภาพ:** Forest Editorial Observatory + Cinematic Field Photography
**ขอบเขต:** Web เท่านั้น

**Figma:** [TreeQ — Forest Editorial Observatory](https://www.figma.com/design/54IMkjTG5teh8P1ZHairlo)

## 1. เป้าหมาย

ยกระดับทุกหน้าเว็บของ TreeQ Carbon Platform ให้ดูเป็นผลิตภัณฑ์เดียวกัน สวยระดับงาน editorial premium และยังอ่านข้อมูลวิทยาศาสตร์ได้ชัดเจน งานนี้เปลี่ยน presentation เท่านั้น ไม่เปลี่ยน ML, API, สูตรคำนวณ, evidence, state machine หรือพฤติกรรมของระบบ

ดีไซน์ต้องสื่อแนวคิด **“ธรรมชาติที่วัดและตรวจสอบได้”** ภายในไม่กี่วินาที กรรมการควรเห็นทั้งความงามของธรรมชาติ ความเป็น Deep Tech และความซื่อสัตย์ของหลักฐานในระบบเดียวกัน

## 2. ขอบเขต

งานออกแบบครอบคลุม:

1. Landing
2. Judge Demo
3. Results / 3D Viewer
4. Tree results และ provenance
5. Login
6. Signup
7. Dashboard และ navigation ที่เชื่อมหน้าข้างต้น

งานนี้ไม่ครอบคลุม Flutter mobile, ML/API changes, marketplace, certification, species training หรือการเพิ่ม workflow ใหม่

## 3. หลักการออกแบบ

### 3.1 Forest Editorial Observatory

TreeQ ใช้ภาษาภาพของนิทรรศการธรรมชาติร่วมสมัย: ภาพหลักขนาดใหญ่, serif headline, whitespace ที่ตั้งใจ, floating information panels และป้ายข้อมูลขนาดเล็กแบบงานจัดแสดง ระบบต้องดูสงบและมั่นใจ ไม่เหมือน generic SaaS dashboard, gaming interface หรือ crypto product

แรงบันดาลใจมาจากงาน [Hotel Booking Website](https://dribbble.com/shots/27262277-Hotel-Booking-Website) และ [EcoTech Exhibition Landing Page](https://dribbble.com/shots/26497016-EcoTech-Exhibition-Landing-Page-Nature-UI-UX-Design) เฉพาะด้าน composition, hierarchy และความประณีต TreeQ ห้ามคัดลอก asset, layout หรือองค์ประกอบเฉพาะของผู้สร้าง

### 3.2 Scientific clarity

ความสวยต้องช่วยให้ข้อมูลอ่านง่าย ทุกหน้าจัดลำดับข้อมูลจากสิ่งสำคัญไปสิ่งสนับสนุน:

1. ผลหรือการกระทำหลัก
2. สถานะของ run
3. หลักฐานและ provenance
4. ข้อจำกัด

ตัวเลขใช้ tabular numerals ตารางจัดแนวตามหลักข้อมูล และ technical metadata ใช้ monospace เฉพาะส่วนที่จำเป็น

### 3.3 Honest states

UI ต้องรักษาความหมายของ `Production Live`, `Local Live` และ `Frozen Evidence` ตาม state machine เดิม ห้ามซ่อนคำว่า `NOT A LIVE RUN`, สร้างเปอร์เซ็นต์ประมวลผลปลอม หรือแสดงตัวเลขเมื่อ evidence verification ล้มเหลว

## 4. Visual Foundation

### 4.1 Color tokens

| Token | ค่า | การใช้งาน |
|---|---:|---|
| Forest Ink | `#152019` | ข้อความหลักและเส้นนำสายตา |
| Deep Forest | `#0E2A1D` | Viewer, hero panel และพื้นที่ contrast สูง |
| Canopy | `#214E35` | Navigation, secondary dark surface |
| Moss | `#789B3B` | Primary CTA และสถานะพร้อม |
| Lichen | `#C7D6A1` | Highlight, chart accent และ selected state |
| Gallery Ivory | `#F4F1E8` | พื้นหลัก |
| Paper | `#FCFBF7` | Card และ form surface |
| Mist | `#D9DED5` | Section contrast และ disabled surface |
| Evidence Amber | `#B28A40` | Frozen, limitation และ excluded result |
| Clay | `#8F5039` | Error และ destructive state (แก้จาก `#A65F46` — ดูหมายเหตุใต้ตาราง) |
| Hairline | `#D6D7CF` | Border และ divider |

สีสถานะต้องไม่พึ่งสีเพียงอย่างเดียว ทุก badge มีข้อความหรือ icon ประกอบ และข้อความทุกขนาดผ่าน WCAG AA

> **หมายเหตุ Clay (`#A65F46` → `#8F5039`)** — ค่าเดิมผ่าน AA เฉพาะบน Paper (4.67:1) เท่านั้น
> แต่ token นี้ถูกใช้บนพื้นอื่นด้วย: `EXCLUDED` ในตารางรายต้นอยู่บนแถว Gallery Ivory (**4.28:1**)
> และข้อความ error ใน UploadDropzone อยู่บน tint `bg-clay/10` ที่ composite แล้วได้ `#F3EBE5`
> (**4.10:1**) — สองในสามการใช้งานจริงจึงไม่ผ่าน
>
> แก้ที่ token ไม่ใช่ที่ call site เพราะปัญหาอยู่ที่ตัวสี ไม่ใช่ที่จุดใดจุดหนึ่ง ค่าใหม่ให้
> 5.5:1 บน Gallery Ivory, 6.0:1 บน Paper และ 5.2:1 บน tint — มีระยะเหลือทุกกรณี
>
> **เป็น deviation จาก Figma** ต้องบันทึกใน Task 11 visual compare

### 4.2 Typography

- Display และ Thai headline: `Noto Serif Thai`, weight 600–700
- UI และ body: `IBM Plex Sans Thai`, weight 400–600
- Hash, commit และ technical labels: `JetBrains Mono`
- ตัวเลขรายงานใช้ `font-variant-numeric: tabular-nums`

ไฟล์ฟอนต์ที่ใช้จริงต้อง self-host ใน repo และโหลดผ่าน `next/font/local` เพื่อให้ production และ offline build เหมือนกัน ห้ามพึ่ง font CDN บน judge path

### 4.3 Layout

- Desktop master frame: `1440 × 900`
- Verification frame: `1366 × 768`
- Grid: 12 columns, content width สูงสุด 1280 px
- Outer margin: 64–80 px ที่ 1440 px; ลดตาม breakpoint
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 96
- Card radius: 20–28 px
- Button radius: full pill หรือ 16 px ตามบริบท
- Hairline border: 1 px; ใช้เงานุ่มเฉพาะ surface ที่ต้องแยกชั้น

### 4.4 Brand motifs

ใช้สาม motif อย่างจำกัด:

1. Point-cloud constellation จาก deterministic public demo
2. วงปีต้นไม้หรือเส้น contour สำหรับ section divider
3. กรอบ label แบบป้ายจัดแสดงสำหรับ provenance และ evidence

Visual asset ต้องมาจาก deterministic public demo, งานที่ทีมสร้างเอง หรือ asset ที่มีสิทธิ์ใช้อย่างชัดเจน ห้ามนำภาพหรือข้อมูลส่วนบุคคลขึ้น Figma หรือเข้า repo

## 5. Screen Architecture

### 5.1 Landing

Landing ใช้ split editorial hero ภายใน first viewport:

- ฝั่ง visual แสดง point-cloud forest หรือ tree specimen ขนาดใหญ่
- ฝั่งข้อความมี headline, supporting copy และ CTA หลัก `เริ่ม Judge Demo`
- Floating evidence card แสดง `tlsep baseline`, Wood IoU `0.418`, Leaf IoU `0.808` และ DBH MAE display `1.167 cm`
- ตัวเลขเต็มและข้อจำกัดอยู่ใกล้ evidence section ตาม honesty rules

ส่วนต่อไปเรียง: Problem → Measurement journey → 3D evidence → Validation → Final CTA เนื้อหาตัดสิ่งที่อยู่นอก web journey ออกเพื่อลดความหนาแน่น

Landing ยังคงเป็น Tailwind server component ห้ามใช้ styled-jsx หรือ canvas 3D

### 5.2 Judge Demo

Judge Demo ใช้ compact workspace header และ guided first step:

- Frozen Sample เป็นเส้นทางหลักที่มองเห็นทันที
- Live Upload เป็นเส้นทางรอง เปิดเฉพาะเมื่อ readiness ผ่าน
- Mode badge อยู่ใกล้ชื่อ run และผลรวม แต่ไม่แย่ง hierarchy
- Upload state แสดง file contract, file identity และสถานะที่ API ยืนยันได้
- Failure state บอกสิ่งที่ผู้ใช้ทำต่อได้ โดยไม่เปิดเผย token, path หรือ raw stderr

### 5.3 Results / 3D Viewer

Results workspace ใช้ asymmetrical 8/4 grid:

- Viewer กินพื้นที่ประมาณ 8 columns และเป็น visual focus
- Result rail ใช้ 4 columns แสดง CO₂e, carbon stock, detected/measured/excluded และ disclaimer
- Viewer frame ใช้ Deep Forest พร้อม legend ที่สอดคล้องกับสี wood, leaf และ ground ใน Three.js
- Controls แสดงเฉพาะความสามารถที่ artifact รองรับจริง
- Tree table และ provenance อยู่ใต้ viewer หรือเปิดเป็น drawer บนจอกว้าง โดยไม่ซ่อนข้อจำกัด

หาก segmented/QSM artifact ไม่มี UI ต้องบอกว่า unavailable ห้ามสร้างภาพทดแทนที่อาจถูกเข้าใจว่าเป็นผลจริง

### 5.4 Tree results and provenance

ตารางรวม measured และ excluded rows ในลำดับ tree ID เดียวกัน แถว excluded ใช้ amber surface พร้อม reason ที่ pipeline ส่งมา ข้อมูล provenance แบ่งเป็น:

- Run identity
- Input and artifact hashes
- Pipeline and backend
- Git commit
- Species status
- Allometric source
- Limitations

### 5.5 Login and Signup

Auth ใช้ editorial split screen:

- ฝั่งหนึ่งแสดง brand visual และข้อความสั้น
- อีกฝั่งเป็น form ที่มี label ชัดเจน, focus state, error state และ password guidance
- หน้าไม่ใช้ card ซ้อนหลายชั้นหรือข้อความ marketing ยาว
- Logo, navigation และ typography ใช้ชุดเดียวกับ Landing

### 5.6 Dashboard

Dashboard เป็น Observatory Console ที่สงบและจัดลำดับชัดเจน:

- Overview และ primary action อยู่ด้านบน
- Recent analyses เป็น list/table ที่อ่านเร็ว
- Carbon metrics แสดงเฉพาะข้อมูลจริง
- CTA ไป Judge Demo และ Viewer เห็นชัด
- ลด card grid ที่มีน้ำหนักเท่ากันทุกใบ

## 6. Shared Components

Figma และ implementation ใช้ชื่อ component ร่วมกัน:

- `AppHeader`
- `CompactWorkspaceHeader`
- `BrandMark`
- `EditorialSection`
- `PrimaryCTA`
- `SecondaryCTA`
- `EvidenceMetric`
- `ModeBadge`
- `UploadDropzone`
- `ViewerStage`
- `ViewerLegend`
- `ResultRail`
- `TreeResultTable`
- `ProvenancePanel`
- `AuthPanel`
- `EmptyState`
- `FailureState`

Repeated elements ต้องเป็น Figma components และ code components ไม่สร้างเป็น one-off frames

## 7. Interaction and Motion

- Hover และ focus: 180–220 ms
- Section reveal: 240–320 ms
- Viewer panel transition: ไม่เกิน 320 ms
- Motion ใช้ opacity และ transform เล็กน้อย หลีกเลี่ยง animation ต่อเนื่องที่รบกวนข้อมูล
- รองรับ `prefers-reduced-motion`
- Loading ใช้ skeleton หรือ indeterminate indicator ตามสถานะจริง

## 8. Responsive Behavior

Desktop เป็นเป้าหมายหลักของการแข่งขัน แต่ทุกหน้าต้องใช้งานได้บนจอเล็ก:

- 1440×900: แสดง hero CTA, mode badge และผลรวมครบใน first view
- 1366×768: ไม่มี headline, CTA หรือ mode badge ถูกตัด
- ต่ำกว่า 1024 px: Results เปลี่ยนจาก 8/4 grid เป็น stack โดย viewer มาก่อน
- ต่ำกว่า 640 px: table เลื่อนภายใน container; ห้ามเกิด horizontal page scroll

งานนี้ไม่เพิ่ม mobile-specific workflow

## 9. Data and State Boundaries

Visual components รับข้อมูลจาก view model และ state machine เดิม งาน redesign ห้าม:

- เปลี่ยน API schema หรือ ML result
- เปลี่ยนสูตรหรือ format ของ evidence artifact
- เปลี่ยน `tlsep` default หรือสถานะ PointNet++
- แสดง certified carbon credit claim
- เปลี่ยน Frozen เป็น Live โดยไม่มี readiness verification
- แสดงผลรวมเมื่อ frozen evidence โหลดหรือ verify ไม่ผ่าน

## 10. Figma Deliverable

สร้าง Figma file ใหม่ชื่อ `TreeQ — Forest Editorial Observatory` พร้อมหน้า:

1. `00 Foundations`
2. `01 Components`
3. `02 Landing`
4. `03 Judge Demo`
5. `04 Results + Viewer`
6. `05 Auth`
7. `06 Dashboard`

แต่ละหน้าใช้ Auto Layout, shared variables, text styles, effect styles และ reusable components Frame หลักใช้ 1440×900 และมี 1366×768 verification frame สำหรับ Landing, Demo และ Results

## 11. Verification

### 11.1 Figma gates

- ไม่มี placeholder text, clipped text หรือ overlapping nodes
- Font family ตรงกับ typography specification
- Components, colors, spacing และ radii ผูกกับ shared tokens
- Screenshots ราย section และ full screen ผ่าน visual review
- 1440×900 และ 1366×768 แสดง critical content ครบ

### 11.2 Implementation gates

- Unit tests เดิมผ่าน
- TypeScript typecheck ผ่าน
- Next.js production build ผ่าน
- Landing ยังคง server-rendered ด้วย Tailwind
- Browser visual review ครบทุก route และทุก mode state
- Keyboard focus, contrast และ reduced motion ผ่าน manual check
- ไม่มี secret, private file, external font dependency หรือ copyrighted reference asset เข้า commit

## 12. Acceptance Criteria

งาน redesign เสร็จเมื่อ:

1. ทุกหน้าในขอบเขตใช้ visual system เดียวกัน
2. Landing สื่อ problem, product และ evidence ได้ใน first viewport
3. Judge Demo แยก Frozen และ Live ชัดเจน
4. Results ให้ 3D Viewer เป็น visual focus และยังอ่านผลรวมได้ทันที
5. Tree table อธิบาย measured และ excluded rows
6. Provenance และ limitation ยังเห็นและตรวจสอบได้
7. Auth และ Dashboard ดูเป็นผลิตภัณฑ์เดียวกับ Landing
8. Critical content ผ่านสอง desktop viewport
9. Design ไม่เปลี่ยนข้อมูลหรือพฤติกรรมระบบ
10. Figma, spec และ implementation ตรงกัน
