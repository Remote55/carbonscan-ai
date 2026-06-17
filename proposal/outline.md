# ข้อเสนอโครงการ — CarbonScan AI

> **เป้าหมาย:** เอกสาร 10-12 หน้า (ไม่นับ cover + appendix) พร้อมส่ง NSC 2026
> **Status:** 🟢 Draft v2 — โครงสร้างตรง NSC 2026 Booklet (Section 7.1-7.5) + pivot LiDAR-primary
> **Format:** วาง content นี้ลง template Word ของสถาบัน → Person B จัดหน้า

---

## หน้าปก (Cover Page) — Person B

```
┌─────────────────────────────────────────────┐
│  [โลโก้ CarbonScan AI]   [โลโก้ NSC 2026]   │
│                                              │
│    คาร์บอนสแกน เอไอ:                          │
│    แพลตฟอร์มยืนยันคาร์บอนเครดิตจาก            │
│    LiDAR Point Cloud ด้วย AI                  │
│    และระบบจับคู่ B2B ภาคอุตสาหกรรม           │
│                                              │
│    CarbonScan AI: LiDAR-driven Carbon        │
│    Credit Verification & B2B Marketplace     │
│    Platform                                   │
│                                              │
│    [Hero Visual: 3D segmented point cloud]   │
│                                              │
│    เสนอเพื่อขอรับการสนับสนุนใน                │
│    โครงการแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์      │
│    แห่งประเทศไทย ครั้งที่ 28 (NSC 2026)        │
│                                              │
│    หมวด 14 โปรแกรมเพื่องานการพัฒนา           │
│    ด้านวิทยาศาสตร์และเทคโนโลยี                │
│    ระดับนิสิต/นักศึกษา                         │
│                                              │
│    [ชื่อสมาชิกทีม x3]                          │
│    ที่ปรึกษาโครงการ: [ชื่ออาจารย์]            │
│    [คณะ มหาวิทยาลัย]                          │
│                                              │
│    เสนอเมื่อวันที่ 29 พฤษภาคม 2569              │
└─────────────────────────────────────────────┘
```

---

## ส่วนที่ 1: ข้อมูลโครงการ (Project Information)

| รายการ | รายละเอียด |
|---|---|
| **ชื่อโครงการ (ไทย)** | คาร์บอนสแกน เอไอ: แพลตฟอร์มยืนยันคาร์บอนเครดิตจาก LiDAR Point Cloud ด้วย AI และระบบจับคู่ B2B ภาคอุตสาหกรรม |
| **ชื่อโครงการ (อังกฤษ)** | CarbonScan AI: LiDAR-driven Carbon Credit Verification & B2B Marketplace Platform |
| **หมวด** | 14 — โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี |
| **ระดับ** | อุดมศึกษา (ปริญญาตรี) |
| **คำสำคัญ** | LiDAR, Point Cloud, Wood-Leaf Segmentation, Deep Learning, Carbon Credit, Allometric Equation, Climate FinTech, ESG |
| **สมาชิกในทีม** | 1. [User] — Team Lead, AI/ML, Mobile, Backend<br>2. [Person A] — Frontend / Web Development<br>3. [Person B] — UI/UX Design / Content Creation |
| **ที่ปรึกษาโครงการ** | [ชื่อ-สกุล, ตำแหน่งวิชาการ] |
| **สถาบัน** | [คณะ มหาวิทยาลัย] |
| **ระยะเวลา** | 30 พฤษภาคม 2569 – 21 สิงหาคม 2569 (รวม 12 สัปดาห์) |
| **งบประมาณ** | (TBD ตามมาตรฐาน NSC) |

---

## ส่วนที่ 2: บทคัดย่อ (Abstract)

ในยุคที่ภาคอุตสาหกรรมทั่วโลกต้องเผชิญมาตรการสิ่งแวดล้อมที่เข้มงวด เช่น นโยบายความเป็นกลางทางคาร์บอน (Carbon Neutrality) ภายในปี ค.ศ. 2050 และมาตรการการเก็บภาษีคาร์บอนข้ามแดนของสหภาพยุโรป (Carbon Border Adjustment Mechanism — CBAM) ที่จะเริ่มมีผลในปี 2026 ทำให้ "คาร์บอนเครดิตภาคป่าไม้" เป็นที่ต้องการอย่างมาก ปัจจุบันบริการ LiDAR scanner (TLS และ Drone) ในประเทศไทยมีอยู่แล้ว แต่หลังจาก scan จบลูกค้าจะได้เพียงไฟล์ `.las/.laz` ที่ยังไม่ผ่านการประมวลผล — ต้องไปจ้าง consultant / auditor / lawyer / market broker ต่ออีกหลายขั้น ทำให้กระบวนการขายคาร์บอนเครดิตยังคงมีต้นทุนสูงและไม่โปร่งใส

โครงการ "CarbonScan AI" นำเสนอ **software platform ระหว่าง LiDAR scanning ↔ Carbon Credit Marketplace** ที่ทำหน้าที่:
(1) รับ input LiDAR Point Cloud `.las/.laz` เป็น primary path (สำหรับผู้ตรวจสอบและผู้รับเหมา carbon survey ที่มีอุปกรณ์อยู่แล้ว) และรับภาพถ่ายมือถือเป็น secondary path สำหรับเกษตรกรรายย่อย (Photogrammetry < 1 ไร่)
(2) ประมวลผลผ่าน ML Pipeline 8 ขั้น — จำแนกใบ/ลำต้น (Phase 1: PCA eigenstructure heuristic ที่ใช้งานได้แล้ว; Phase 2: Deep Learning PointNet++) + RANSAC วัด DBH + สมการแอลโลเมตริก TGO 2017 คำนวณคาร์บอน
(3) ออก PDF certificate ที่อ้างอิงมาตรฐาน TGO + รองรับการ verify ของ third-party
(4) เป็นตัวกลาง B2B marketplace ระหว่างชุมชนผู้ปลูกต้นไม้กับโรงงานอุตสาหกรรมที่ต้องการชดเชย CBAM/ESG
(5) ป้องกันการนับซ้ำผ่าน GPS dedup, EXIF validation, multi-temporal tracking สำหรับ Additionality

ระบบในเวอร์ชันต้นแบบรองรับไม้เศรษฐกิจของไทย 5 ชนิด (สัก ยางนา ไผ่ ยางพารา มะค่าโมง) และผ่านการทดสอบเบื้องต้นบน **Demol et al. 2021 Belgium Destructive Biomass dataset (Zenodo 4557401)** ขนาด 65 ต้น × 4 species พบความแม่นยำ **DBH MAE = 1.17 cm (3.8% mean error)** และ **Tree Height MAE = 0.54 m (2.6%)** ซึ่งอยู่ในช่วงมาตรฐานวิจัย TLS Forestry (1-3 cm DBH, 0.5-1.5 m Height)

ระบบนี้คาดว่าจะลดต้นทุนการประเมินคาร์บอนเครดิตภาคป่าไม้ในไทยได้กว่า 100 เท่า เปิดทางให้เกษตรกรรายย่อยและชุมชนเข้าถึงระบบเศรษฐกิจสีเขียวที่เคยเป็นเอกสิทธิ์ของบริษัทขนาดใหญ่ และช่วยให้ผู้ส่งออกไทยเตรียมพร้อมรับมาตรการ CBAM ของ EU

**Keywords:** LiDAR, Point Cloud Processing, Wood-Leaf Semantic Segmentation, PointNet++, Carbon Credit, Allometric Equation, Photogrammetry, Climate FinTech, ESG, Sustainable Innovation

*(ความยาวประมาณ 320 คำ)*

---

## ส่วนที่ 3: หลักการและเหตุผล (Background and Rationale)

### 3.1 บริบทระดับโลก

การเปลี่ยนแปลงสภาพภูมิอากาศ (Climate Change) เป็นวิกฤตระดับโลกที่ทุกภาคส่วนต้องร่วมรับผิดชอบ ในปี ค.ศ. 2015 ภายใต้ Paris Agreement ประเทศต่าง ๆ ทั่วโลกได้ตกลงร่วมกันในการจำกัดอุณหภูมิเฉลี่ยของโลกไม่ให้สูงขึ้นเกิน 1.5°C จากระดับก่อนการปฏิวัติอุตสาหกรรม [1] ส่งผลให้ภาคอุตสาหกรรมต้องเร่งปรับตัวสู่การลดการปล่อยก๊าซเรือนกระจก โดยใช้กลไก "Carbon Credit" เพื่อชดเชยการปล่อยคาร์บอนที่ไม่สามารถลดได้

มาตรการสำคัญที่จะกระทบประเทศไทยโดยตรงคือ **Carbon Border Adjustment Mechanism (CBAM)** ของสหภาพยุโรป ซึ่งจะเริ่มเก็บภาษีคาร์บอนกับสินค้านำเข้าตั้งแต่ปี 2026 [2] ทำให้ภาคอุตสาหกรรมส่งออกของไทย (เหล็ก, ปูนซีเมนต์, อะลูมิเนียม, ไฟฟ้า, ไฮโดรเจน, ปุ๋ย) ต้องเร่งหาแนวทางลดและชดเชยคาร์บอน

### 3.2 บริบทประเทศไทย

ประเทศไทยได้ประกาศเป้าหมาย **Carbon Neutrality ภายในปี 2050** และ **Net Zero ภายในปี 2065** [3] ในการประชุม COP26 ส่งผลให้องค์การบริหารจัดการก๊าซเรือนกระจก (Thailand Greenhouse Gas Management Organization — TGO) เร่งพัฒนากลไกตลาดคาร์บอนภายในประเทศ (Thailand Voluntary Emission Reduction Program — T-VER)

ในกลุ่ม Nature-based Solutions "คาร์บอนเครดิตภาคป่าไม้" (Forest Carbon) เป็นหมวดที่มีศักยภาพสูงที่สุด เนื่องจากประเทศไทยมีพื้นที่ป่าไม้กว่า 102 ล้านไร่ และมีแผนเพิ่มพื้นที่ป่าให้ถึง 40% ของพื้นที่ประเทศ [4]

### 3.3 ปัญหาคอขวด (Pain Points)

**1. ต้นทุนการประเมินสูง**

กระบวนการประเมินคาร์บอนเครดิตป่าไม้ตามมาตรฐาน T-VER [5] ในปัจจุบันต้องใช้ผู้ตรวจสอบลงพื้นที่จริง โดยใช้สายวัดโอบรอบลำต้นเพื่อหาเส้นผ่านศูนย์กลางระดับอก (Diameter at Breast Height — DBH) และใช้กล้องเล็งวัดความสูงทีละต้น ทำให้มีต้นทุนการสำรวจและประเมินในระดับ 50,000–200,000 บาทต่อแปลง (ขึ้นกับขนาดพื้นที่และจำนวนต้น; ประมาณการจากการสอบถามผู้ประกอบการ carbon survey)

**2. ขาด software layer ที่เชื่อม LiDAR → Carbon Credit**

ปัจจุบันบริการ LiDAR scanner (TLS เครื่องละ 500,000-2,000,000 บาท; Drone LiDAR แบบ DJI Matrice + Zenmuse L1/L2 อีก ~1,000,000 บาท) มีในตลาดไทยอย่างน้อย 10 บริษัท แต่หลัง scan เสร็จลูกค้าจะได้แค่ไฟล์ `.las/.laz` ดิบ — ยังไม่ผ่านการ:
- AI segmentation แยก wood/leaf
- คำนวณ biomass + carbon ตามสมการ TGO
- ออกเป็น certificate ที่มีคุณภาพ
- จับคู่ผู้ซื้อในตลาด B2B
- ตรวจสอบ Additionality (multi-temporal tracking)

ลูกค้าต้องไปจ้าง consultant + auditor + lawyer ต่ออีกหลายขั้น

**3. ขาดความโปร่งใสในการตรวจสอบย้อนหลัง**

โรงงานอุตสาหกรรมที่ลงทุนกับโครงการปลูกป่า CSR มักได้รับเพียง "รายงานสรุปจำนวนต้นไม้ที่ปลูก" ไม่สามารถตรวจสอบได้ว่าต้นไม้แต่ละต้นยังมีชีวิตหรือไม่ และดูดซับคาร์บอนได้เท่าไหร่จริง ๆ ทำให้เสี่ยงต่อข้อครหา **Greenwashing** [7]

### 3.4 โอกาสในการแก้ปัญหาด้วยเทคโนโลยี

ในช่วง 5 ปีที่ผ่านมา เทคโนโลยี Computer Vision สำหรับ 3 มิติได้พัฒนาก้าวหน้าอย่างมาก ทั้ง Deep Learning สำหรับการประมวลผล Point Cloud (PointNet++ [8], KPConv [9]) และ algorithm สำหรับวัดต้นไม้ (Watershed segmentation, TreeQSM [11], CSF [12], Pit-free CHM [13]) — ทำให้สามารถสร้างระบบประเมินคาร์บอนต้นไม้แบบอัตโนมัติได้ในต้นทุนต่ำ

ขณะเดียวกัน Cloud Computing แบบ Serverless GPU (RunPod, Modal.com) ได้ทำให้นักวิจัยและสตาร์ทอัพระดับนักศึกษาสามารถเข้าถึงทรัพยากร GPU ที่จำเป็นได้ในราคาเพียงไม่กี่บาทต่อชั่วโมง ลดอุปสรรคในการพัฒนา Deep Tech อย่างมีนัยสำคัญ

### 3.5 ช่องว่าง (Research Gap)

แม้ในต่างประเทศจะมีงานวิจัยและเครื่องมือเช่น `lidR` [10], TreeQSM [11] สำหรับการประมวลผล LiDAR ของต้นไม้ แต่ในประเทศไทยยัง **ขาด integrated software platform** ที่:

- **เชื่อมต่อตั้งแต่ LiDAR file → AI processing → Certificate → B2B Marketplace ในระบบเดียว**
- ใช้ **สมการแอลโลเมตริกของไทย** (TGO 2017 + Tsutsumi 1983 + Ogawa 1965 + Yiping 2010 + Chiarucci 2014) ไม่ใช่ Chave pantropical ที่ overestimate
- **รองรับ Multi-temporal tracking** สำหรับ Additionality ที่ ESG reporting บังคับ
- มี **กลไก Anti-fraud** ระดับ trust infrastructure (GPS dedup + EXIF + audit log)
- เปิดทาง **smallholder via mobile photogrammetry** เป็น democratization layer สำหรับเกษตรกร < 1 ไร่ที่ drone ไม่คุ้ม

CarbonScan AI จึงถูกออกแบบมาเพื่อปิดช่องว่างเหล่านี้

---

## ส่วนที่ 4: วัตถุประสงค์ของโครงการ (Objectives)

โครงการนี้มีวัตถุประสงค์เฉพาะ (Measurable Objectives) ดังนี้:

1. **พัฒนา Web Platform ที่รับ LiDAR Upload (.las/.laz) เป็น primary input** และ photogrammetry จาก mobile photos เป็น secondary input โดย integrate ทั้ง 2 ผ่าน ML Pipeline เดียวกัน

2. **พัฒนาระบบประมวลผล LiDAR Point Cloud อัตโนมัติ** ที่สามารถ:
   - แยกจุดข้อมูลเป็นพื้นดิน/ไม่ใช่พื้นดิน (Ground Classification ด้วย CSF algorithm)
   - แยกต้นไม้ทีละต้น (Individual Tree Detection ด้วย Watershed segmentation)
   - แยกใบและลำต้น/กิ่ง (Wood-Leaf Semantic Segmentation) ด้วย Deep Learning โดยมี IoU ≥ 0.70 (Phase 2) — Phase 1 ใช้ rule-based PCA eigenvalue fallback

3. **พัฒนาระบบคำนวณปริมาตรไม้** (Quantitative Structure Model — QSM) และแปลงเป็นปริมาณคาร์บอนผ่านสมการแอลโลเมตริกตามมาตรฐาน TGO 2017 [14] โดยรองรับไม้เศรษฐกิจ 5 ชนิด: สัก ยางนา ไผ่ ยางพารา มะค่าโมง

4. **พัฒนา B2B Marketplace** เป็นตัวกลางระหว่าง:
   - **ผู้ขาย:** ชุมชน / เกษตรกร / ผู้รับเหมา carbon survey ที่ลงทะเบียนแปลงและ verify carbon credit ผ่านระบบ
   - **ผู้ซื้อ:** โรงงานอุตสาหกรรมที่ต้องการชดเชย CBAM / ESG offset

5. **พัฒนา 3D Point Cloud Viewer + GIS Map** บน Web Dashboard ที่ทำให้:
   - ผู้ขายเห็นข้อมูลต้นไม้แต่ละต้นที่ตัวเองมี
   - ผู้ซื้อตรวจสอบ provenance ก่อนซื้อ (3D model + GPS pins)
   - Auditor ตรวจสอบย้อนหลังได้ (audit trail + immutable log)

6. **ทดสอบความแม่นยำของระบบ** เทียบกับ peer-reviewed dataset (Demol et al. 2021 [25] — Belgium TLS + destructive sampling, 65 ต้น × 4 species) โดยตั้งเป้า DBH MAE ≤ 2 cm และ Height MAE ≤ 1 m **(บรรลุแล้วใน Phase 1)**

---

## ส่วนที่ 5: ภาพรวมโครงการ (Project Overview)

> รายละเอียดของขอบเขต ดู Section 7.5 — บทนี้คือสรุประดับสูง

โครงการประกอบด้วย **4 องค์ประกอบหลัก** ทำงานร่วมกัน:

| องค์ประกอบ | หน้าที่ | ผู้ใช้หลัก |
|---|---|---|
| **Web Platform** (Next.js) | Upload LiDAR, 3D Viewer, GIS Map, Marketplace, Certificate viewer | Auditor / Industrial buyer |
| **Mobile App** (Flutter) | Photogrammetry capture, ผลการ scan ส่วนตัว | Smallholder farmer |
| **Backend API** (FastAPI) | Auth, Job orchestration, Spatial queries, WebSocket progress | (ระบบภายใน) |
| **ML Pipeline** (Python, RunPod GPU) | 8 ขั้นตอน (Ground → Normalize → CHM → Tree Seg → Wood-Leaf → QSM → Species → Allometric) | (ระบบภายใน) |

ข้อมูล input ที่ระบบรองรับ 3 ประเภท: LiDAR file (`.las/.laz/.ply`), Mobile photos (JPG ≥ 30 ภาพ + GPS), Existing CSV inventory จาก TGO/กรมป่าไม้

ผลลัพธ์ (output) ที่ระบบสร้าง 3 อย่าง: **(1) Verified Carbon Certificate (PDF) ที่อ้างอิงมาตรฐาน TGO 2017**, **(2) B2B Marketplace listing** สำหรับขายให้โรงงาน, **(3) GIS Map + Audit Log** สำหรับ Multi-temporal Additionality tracking

---

## ส่วนที่ 6: ระเบียบวิธีวิจัย / Methodology (สรุป)

> รายละเอียดเทคนิคทุกขั้น ดู Section 7.2 — บทนี้คือสรุประดับสูง

ระบบใช้ **Dual-Input Architecture**: ทั้ง LiDAR Upload (Path A — primary) และ Mobile Photogrammetry (Path B — secondary) จะถูกแปลงเป็น Point Cloud `.ply` ก่อนเข้า ML Pipeline เดียวกัน 8 ขั้นตอน

```
Path A — LiDAR Upload (PRIMARY)
  Auditor → .las/.laz upload → Storage → Queue → GPU Worker
                                                       ↓
                                              ML Pipeline (8 ขั้น)
                                                       ↓
Path B — Mobile Photogrammetry (SECONDARY)            ↓
  Smallholder → 30 JPG + GPS → COLMAP+OpenMVS → .ply ─┘
                                                       ↓
                                              Output (Certificate + Marketplace + GIS+Audit)
```

ระบบรัน ML pipeline บน Cloud GPU (RunPod Serverless A10G, ~$0.39/ชั่วโมง pay-per-second) ใช้เวลาประมาณ 10–15 นาทีต่อ scan โดยใช้ WebSocket ส่ง progress กลับมา client แบบ real-time

ระเบียบวิธีในการประเมินความแม่นยำใช้ **Public Dataset ที่ peer-reviewed คือ Demol et al. 2021 [25] (Zenodo 4557401)** — TLS scan ของ 65 ต้น × 4 species ใน Belgium พร้อม destructive sampling reference

ผลทดสอบเบื้องต้น **(Preliminary Validation — รันเสร็จเมื่อ 24 พ.ค. 2569):**

| Metric | Mean Error | MAE | RMSE | Literature Range | Status |
|---|---|---|---|---|---|
| **DBH** | 3.8% | **1.17 cm** | 2.07 cm | 1-3 cm | ✅ ผ่าน |
| **Tree Height** | 2.6% | **0.54 m** | 0.76 m | 0.5-1.5 m | ✅ ผ่าน |
| **Stem Volume (taper)** | 18.8% | 0.20 m³ | 0.28 m³ | (Phase 2 จะใช้ TreeQSM ลดเหลือ 5-10%) | 🟡 |

ระบบ Phase 1 ผ่าน 25/25 unit tests + smoke tests (16 allometric + 9 pipeline) บนทั้ง synthetic data และ real Belgium dataset

---

## ส่วนที่ 7: รายละเอียดของการพัฒนา (Development Details)

> หัวข้อใน Section 7 ตรงตาม template ของ NSC 2026 Booklet (หน้า 25-26)

### 7.1 เนื้อเรื่องย่อ (Story Board)

#### 7.1.1 เรื่องราวจากมุมมองของ "เกษตรกร / ชุมชนผู้ปลูก"

นายสมพร เกษตรกรรายย่อยในจังหวัดเชียงใหม่ ปลูกต้นสักและต้นยางนาในที่ดิน 5 ไร่มาตลอด 8 ปี เขาเคยอยากขายคาร์บอนเครดิตจากต้นไม้แต่ต้นทุนการตรวจสอบ ~150,000 บาท สูงเกินกว่าจะคุ้ม ในระบบ CarbonScan AI นายสมพรสามารถ:
1. ดาวน์โหลด Mobile App ฟรี
2. เดินถ่ายภาพรอบต้นไม้สำคัญในสวน (ต้นใหญ่ 10-20 ต้น)
3. ระบบ Cloud ใช้ Photogrammetry แปลงเป็น 3D Point Cloud
4. AI ประมวลผลคำนวณคาร์บอนตามสมการ TGO
5. List ขายในระบบ marketplace
6. โรงงานในกรุงเทพ จ่ายเงินซื้อโดยตรง ไม่มี broker

#### 7.1.2 เรื่องราวจากมุมมองของ "โรงงานอุตสาหกรรม"

บริษัท ABC ผลิตปูนซีเมนต์ส่งออกไป EU ตั้งแต่ปี 2026 ต้องชดเชยคาร์บอน 5,000 ตัน/ปี ตาม CBAM ปัจจุบันซื้อเครดิตจาก broker ต่างประเทศในราคาสูงและไม่สามารถ verify ได้ว่าต้นไม้ที่ "สนับสนุน" อยู่ที่ไหน ในระบบ CarbonScan AI:
1. เปิด /marketplace บนเว็บ → กรองตามภูมิภาค (เชียงใหม่) + species (สัก)
2. เห็น 3D Point Cloud + GIS Map ของแปลงที่ตัวเองจะซื้อ
3. ดู Multi-temporal tracking ปีต่อปีเพื่อ verify Additionality
4. กดซื้อ → ระบบสร้าง PDF Certificate ที่อ้างอิงมาตรฐาน TGO 2017
5. นำ certificate ไป report ใน ESG / CBAM submission ของบริษัท
6. **ทุกข้อมูลตรวจสอบย้อนหลังได้** ผ่าน audit log

#### 7.1.3 ภาพประกอบหลัก (Figures)

ใน Proposal version full จะมีภาพทั้งหมด 13 ภาพอ้างอิงเรื่องราว:

| Figure | คำอธิบาย | ที่ใช้ใน Storyboard |
|---|---|---|
| `fig09_architecture.png` | สถาปัตยกรรมระบบ 4 layers | ภาพรวมที่ผู้ใช้/กรรมการต้องเห็นก่อน |
| `fig10_user_flow.png` | User Journey ตั้งแต่ scan ถึงผลลัพธ์ | แสดงเรื่องราว 8 ขั้นตอน |
| `fig01-08` | Synthetic pipeline output | แสดงตัวอย่างผลที่ระบบทำได้ |
| `fig11-13` | Belgium parity plots | **proof of work** ที่กรรมการต้องเห็น |

#### 7.1.4 ทฤษฎีที่เกี่ยวข้อง

- **Photogrammetry (Structure-from-Motion):** Schönberger & Frahm 2016 [16] — แปลงภาพหลายมุมเป็น 3D
- **Cloth Simulation Filter (CSF):** Zhang et al. 2016 [12] — แยกพื้นดินจาก point cloud
- **Pit-free Canopy Height Model:** Khosravipour et al. 2014 [13] — สร้าง CHM raster
- **Watershed Segmentation:** Roussel et al. 2020 [10] — แยกต้นไม้ทีละต้น
- **PointNet++ Deep Learning:** Qi et al. 2017 [8] — Wood/Leaf semantic segmentation
- **Quantitative Structure Model (QSM):** Raumonen et al. 2013 [11] — วัดปริมาตรไม้
- **Chave Pantropical Allometric:** Chave et al. 2014 [26] — สมการ biomass ป่าเขตร้อน (fallback)
- **TGO Forestry Sector Guideline:** TGO 2017 [14] — สมการของไทยเฉพาะ
- **IPCC AFOLU Guidelines:** IPCC 2006 [15] — ค่ามาตรฐาน Carbon fraction = 0.47, Root:Shoot = 0.24

#### 7.1.5 ตัวอย่างผลงานที่ทำได้แล้ว (Proof of Work)

ทีมได้พัฒนาและทดสอบ Phase 1 ของระบบเสร็จแล้ว:
- ✅ ML Pipeline 8 ขั้นตอน (heuristic implementation) รัน end-to-end ได้
- ✅ Synthetic data generator สำหรับ test (ไม่ต้องโหลด 5 GB NEON)
- ✅ Allometric calculator ที่อ้างอิง TGO 2017 + Chave 2014 + IPCC 2006
- ✅ Validation บน Demol 2021 Belgium dataset: 65 trees × 4 species
- ✅ 25/25 unit + smoke tests pass
- ✅ Architecture + UI mockups + documentation 30+ ไฟล์

---

### 7.2 เทคนิคหรือเทคโนโลยีที่ใช้ (Techniques / Technologies)

#### 7.2.1 ML Pipeline ภาพรวม

ระบบประกอบด้วย 8 ขั้นตอนเรียงตามลำดับ:

```
INPUT (.las / .laz / .ply)
   ↓
[1] Ground Classification          → แยกพื้นดิน
   ↓
[2] Height Normalization           → ปรับ Z = 0 บนพื้น
   ↓
[3] Canopy Height Model (CHM)      → 2D raster ของความสูง
   ↓
[4] Individual Tree Detection      → แยกต้นไม้ทีละต้น
   ↓ (per tree)
[5] Wood-Leaf Separation           → แยกลำต้น/กิ่ง vs ใบ
   ↓
[6] Quantitative Structure Model    → วัด DBH, Height, Volume
   ↓
[7] Species Classification          → จำแนกชนิดต้นไม้จาก RGB
   ↓
[8] Allometric Carbon Calculation   → คำนวณ Biomass + Carbon + CO₂eq
   ↓
OUTPUT (JSON per tree + PDF Certificate)
```

#### 7.2.2 รายละเอียดอัลกอริทึมแต่ละขั้น

**ขั้นตอนที่ 1: Ground Classification**
- **Algorithm:** Cloth Simulation Filter (CSF) [12] — Phase 2; **Grid percentile heuristic** — Phase 1
- **Data structure:** 2D grid (XY cells 1 m × 1 m)
- **Parameters:** percentile=5, z_threshold=0.3 m
- **Library:** PDAL (Phase 2), NumPy (Phase 1)
- **Output:** boolean mask — True = ground, False = non-ground

**ขั้นตอนที่ 2: Height Normalization**
- **Algorithm:** K-Nearest-Neighbor + Inverse Distance Weighting (IDW) interpolation
- **Data structure:** KD-tree (scipy.spatial.cKDTree) สำหรับ ground points
- **Parameters:** k_neighbors=8, distance_weight_power=2
- **Formula:** $z_{\text{norm}}(x, y) = z - \sum_{i=1}^{K} \frac{z_i/d_i^p}{\sum_j 1/d_j^p}$
- **Output:** point cloud ที่ Z normalized to 0 = ground

**ขั้นตอนที่ 3: Canopy Height Model (CHM)**
- **Algorithm:** Max-Z rasterization + morphological closing (Phase 1); Pit-free multi-threshold [13] (Phase 2)
- **Data structure:** 2D float32 array (raster grid) + ChmTransform (geo-reference)
- **Parameters:** resolution=0.5 m, closing_size=2 pixels, min_height=0.5 m
- **Library:** NumPy + scipy.ndimage.grey_closing
- **Output:** 2D raster ที่แต่ละ cell = max height ของต้นไม้ที่จุดนั้น

**ขั้นตอนที่ 4: Individual Tree Detection (ITD)**
- **Algorithm:** Watershed segmentation seeded by local maxima
- **Data structure:** 2D label array (int32, tree IDs)
- **Parameters:** min_height=4 m, min_distance=5 pixels (= 2.5 m)
- **Library:** scikit-image (`peak_local_max` + `watershed`)
- **Output:** ทุก point ใน cloud ได้ tree_id (0 = no tree, 1..N = tree number)

**ขั้นตอนที่ 5: Wood-Leaf Semantic Segmentation** ⭐
- **Algorithm Phase 1:** Local PCA eigenvalue analysis [19] — คำนวณ linearity, planarity, verticality
- **Algorithm Phase 2:** PointNet++ deep learning [8] — fine-tune on annotated data
- **Data structure:** (N, 3) point array + (N, 3, 3) covariance matrices (batched einsum)
- **Formulas:**
  - linearity = (λ₀ − λ₁) / λ₀
  - planarity = (λ₁ − λ₂) / λ₀
  - is_wood = (linearity ≥ 0.45 AND planarity ≤ 0.50) OR (verticality ≥ 0.55)
- **Parameters:** k_neighbors=15
- **Library:** NumPy + scipy.spatial.cKDTree (Phase 1); PyTorch + open3d-ml (Phase 2)
- **Output:** (N,) int8 array (0=wood, 1=leaf)

**ขั้นตอนที่ 6: Quantitative Structure Model (QSM)**
- **Algorithm:** RANSAC circle fit at z=1.3 m slice + Max-Z height + Taper equation volume
- **Data structures:** 2D point slice (xy) + RANSAC iterations
- **Parameters:** n_iterations=200, inlier_tolerance=0.02 m, max_radius_m=0.6 (DBH ≤ 120 cm)
- **Formulas:**
  - DBH = 2 × r_ransac (m → cm)
  - Height = max(z) ของ wood points
  - Volume = (π/4) × DBH² × H × form_factor (form_factor = 0.5)
- **Library:** NumPy (custom RANSAC)
- **Output:** QsmResult{dbh_cm, height_m, volume_m3, fit_quality}

**ขั้นตอนที่ 7: Species Classification** (Phase 2 — Mobile)
- **Algorithm:** ResNet-50 [27] Transfer Learning + TFLite int8 quantization
- **Parameters:** Input 224×224 RGB, 5 classes + Unknown
- **Library:** PyTorch + torchvision; TensorFlow Lite สำหรับ mobile deployment
- **Output:** dict {species_sci: probability} — top-1 prediction + confidence

**ขั้นตอนที่ 8: Allometric Carbon Calculation** ⭐ บทสำคัญที่สุด
- **Algorithm:** Species-specific Tier-2 + Chave 2014 [26] fallback (Tier-3); กรอบการประเมินชีวมวลอ้างอิง Brown 1997 [6] + IPCC 2006 [15]
- **Data structure:** Species DB CSV (5 species × 10 columns)
- **สูตรเต็ม:**

  $$\text{AGB (species-specific)} = a \times \text{DBH}^b \times H^c \quad (\text{kg})$$

  $$\text{AGB (Chave 2014)} = 0.0673 \times (\rho \times \text{DBH}^2 \times H)^{0.976}$$

  $$\text{BGB} = \text{AGB} \times 0.24$$

  $$B_{\text{total}} = \text{AGB} + \text{BGB}$$

  $$C = B_{\text{total}} \times 0.47$$

  $$\text{CO}_2\text{eq} = C \times \frac{44}{12}$$

- **Species coefficients (จาก peer-reviewed papers):**

  | Species | a | b | c | Wood density (kg/m³) | Source |
  |---|---|---|---|---|---|
  | Tectona grandis (สัก) | 0.0509 | 2.150 | 0.700 | 660 | Tsutsumi et al. 1983 [21] |
  | Dipterocarpus alatus (ยางนา) | 0.0396 | 2.380 | 0.800 | 720 | Ogawa et al. 1965 [22] |
  | Bambusa spp. (ไผ่) | 0.131 | 2.280 | 0.590 | 650 | Yiping et al. 2010 [23] |
  | Hevea brasiliensis (ยางพารา) | 0.0464 | 2.330 | 0.720 | 580 | Chiarucci et al. 2014 [24] |
  | Afzelia xylocarpa (มะค่าโมง) | 0.0612 | 2.420 | 0.660 | 850 | Chave 2014 adjusted |

- **Library:** Python (custom — 16/16 unit tests pass)
- **Output:** CarbonResult{agb_kg, bgb_kg, biomass_kg, carbon_kg, co2eq_kg}

#### 7.2.3 Dual-Input Architecture: Photogrammetry สำหรับ Mobile

สำหรับ Path B (Mobile photogrammetry) ใช้:
- **COLMAP** [16] — Structure from Motion (SfM): จาก 30 JPG → sparse 3D model + camera poses
- **OpenMVS** [17] — Multi-View Stereo (MVS): จาก sparse → dense point cloud (.ply)

ผลลัพธ์ .ply เข้าสู่ ML Pipeline ขั้น 1-8 เดียวกัน

#### 7.2.4 Anti-Fraud Mechanism (4 ชั้น)

1. **GPS Precision Lock** — บันทึก GPS ระดับทศนิยม 6 ตำแหน่ง (precision ~0.1 ม.)
2. **EXIF Metadata Validation** — ตรวจสอบ timestamp ของรูปถ่าย + server time drift check
3. **Camera-Only Capture** — Mobile App ไม่อนุญาต upload จาก gallery (ImageSource.camera only)
4. **Server-side Deduplication** — PostGIS ST_DWithin query ก่อน insert ต้นใหม่ — ถ้ามีต้นในรัศมี 1-2 ม. → flag

#### 7.2.5 ผลการทดสอบบน Public Dataset (Preliminary Validation)

**Dataset:** Demol et al. 2021 [25] — TLS point clouds 65 ต้น × 4 species (Fagus sylvatica, Pinus sylvestris, Fraxinus excelsior, Larix decidua) ใน Belgium พร้อม destructive sampling reference

**Reference:** Trees Journal, DOI [10.1007/s00468-020-02067-7](https://doi.org/10.1007/s00468-020-02067-7), Zenodo [10.5281/zenodo.4557401](https://doi.org/10.5281/zenodo.4557401)

**ผลลัพธ์:**

| Metric | Mean Error | Median | MAE | RMSE | n | Literature Range |
|---|---|---|---|---|---|---|
| **DBH** | 3.8% | 2.9% | **1.17 cm** | 2.07 cm | 65 | 1-3 cm ✅ |
| **Tree Height** | 2.6% | 2.1% | **0.54 m** | 0.76 m | 65 | 0.5-1.5 m ✅ |
| **Stem Volume** | 18.8% | 19.6% | 0.20 m³ | 0.28 m³ | 65 | (Phase 2 → 5-10%) |

**ตีความ:** DBH และ Height MAE อยู่ในมาตรฐานวิจัย TLS Forestry — เป็นคุณภาพที่ TGO ยอมรับสำหรับ Voluntary Carbon Market

**Reproducibility:** สคริปต์ `services/ml/notebooks/validate_belgium.py` รันใน 13 วินาทีบน laptop CPU ปกติ

ดูภาพ Parity Plot ใน Appendix C:
- `fig11_belgium_dbh_parity.png` — DBH parity (predicted vs felled measurement)
- `fig12_belgium_height_parity.png` — Tree Height parity
- `fig13_belgium_volume_parity.png` — Stem Volume parity (with Phase 2 caveat)

#### 7.2.6 แหล่งข้อมูลที่ใช้ (Data Sources & Provenance)

เนื่องจากข้อมูล LiDAR เป็นหัวใจของระบบ ตารางนี้ระบุ **ที่มาของข้อมูลทุกชุดที่ใช้** พร้อมแหล่งอ้างอิงและตำแหน่งจัดเก็บใน repository เพื่อให้ตรวจสอบย้อนกลับ (reproducible) ได้:

| ประเภทข้อมูล | แหล่งที่มา | รายละเอียด / การเข้าถึง | อ้างอิง |
|---|---|---|---|
| **Validation dataset (หลัก)** | Demol et al. 2021 — TLS + destructive sampling (Belgium) | 65 ต้น × 4 species; DOI `10.1007/s00468-020-02067-7`; Zenodo `10.5281/zenodo.4557401`; จัดเก็บที่ `services/ml/data/raw/zenodo_belgium/` | [25] |
| **Public LiDAR (Phase 2)** | NEON `DP1.30003.001` / OpenTopography | Airborne discrete-return LiDAR สาธารณะ ใช้ขยายผล validation และเตรียมข้อมูลฝึก PointNet++ | [28][29] |
| **ค่าสัมประสิทธิ์ Allometric** | Tsutsumi 1983, Ogawa 1965, Yiping 2010, Chiarucci 2014, Chave 2014, TGO 2017, IPCC 2006 | สมการ AGB = a·DBH^b·H^c + carbon fraction (0.47) + root:shoot (0.24); จัดเก็บที่ `services/ml/data/species_db.csv` | [14][15][21]–[24][26] |
| **ข้อมูลผู้ใช้จริง (runtime)** | ผู้ใช้อัปโหลดเอง: `.las/.laz` จาก TLS/Drone scanner หรือภาพถ่ายมือถือ ≥ 30 ภาพ | ระบบไม่ผูกกับชุดข้อมูลก้อนเดียว — ทำงานกับ point cloud มาตรฐาน ASPRS LAS / Stanford PLY ใดก็ได้ | — (ข้อมูลของผู้ใช้) |
| **ข้อมูลภาคสนามไทย (Phase 3)** | เก็บเองภาคสนาม (สายวัดรอบลำต้น + Vertex/clinometer + TLS/photogrammetry) | ⚠️ **ข้อจำกัดที่ทราบ:** ต้นแบบยังไม่มี ground-truth ของไม้เศรษฐกิจไทย — วางแผนเก็บ 30–50 ต้น (สัก/ยางนา) เพื่อ calibrate สมการ allometric เฉพาะถิ่น | — (เก็บใหม่) |

> **หมายเหตุด้านความโปร่งใส:** สคริปต์ validation (`validate_belgium.py`) และผลรายต้น (`belgium_validation.csv`) เปิดเผยใน repository — กรรมการและผู้ตรวจสอบสามารถ rerun เพื่อยืนยันตัวเลข DBH MAE 1.17 cm / Height MAE 0.54 m ได้ด้วยตนเอง

---

### 7.3 เครื่องมือที่ใช้ในการพัฒนา (Tools)

#### 7.3.1 ภาษาโปรแกรมที่ใช้

| ภาษา | เวอร์ชัน | ใช้ใน |
|---|---|---|
| **Python** | 3.11 | Backend API + ML Pipeline + scripts |
| **TypeScript** | 5.x | Web Frontend (Next.js) |
| **Dart** | 3.12 | Mobile App (Flutter) |
| **SQL** | PostgreSQL 16 dialect | Database queries + migrations |

#### 7.3.2 Frameworks + Libraries หลัก

| Component | Library + Version | บทบาท |
|---|---|---|
| **Web Frontend** | Next.js 14 (App Router) | React framework + SSR |
| | Tailwind CSS 3.4 + shadcn/ui | Utility-first styling + components |
| | Three.js + @react-three/fiber | 3D Point Cloud Viewer (WebGL) |
| | Leaflet + react-leaflet | GIS Map |
| | TanStack Query | Server state management |
| | tus-js-client | Resumable LiDAR upload |
| | @react-pdf/renderer | PDF Certificate generation |
| **Mobile** | Flutter 3.44 | Cross-platform Android + iOS |
| | flutter_riverpod | State management |
| | go_router | Navigation |
| | camera + geolocator | Native camera + GPS |
| | exif | EXIF metadata read/write |
| | tflite_flutter (Phase 2) | On-device ML inference |
| **Backend** | FastAPI 0.111 | Async REST API + WebSocket + auto-Swagger |
| | SQLAlchemy 2.0 (async) | ORM with modern typing |
| | asyncpg | Postgres async driver (fastest) |
| | GeoAlchemy2 | PostGIS support |
| | Alembic | DB migrations |
| | supabase-py | Storage + Auth |
| **AI / ML** | NumPy + SciPy | Array math + KD-tree + signal |
| | scikit-image | Image processing (watershed, peak_local_max) |
| | Open3D 0.19 | 3D point cloud operations |
| | laspy 2.7 | LAS/LAZ file I/O |
| | PyTorch 2.3 + torchvision (Phase 2) | Deep learning |
| | matplotlib + plotly | Visualization for notebooks |
| **Photogrammetry** | COLMAP | Structure from Motion |
| | OpenMVS | Multi-View Stereo (dense) |
| **Database** | PostgreSQL 16 + PostGIS 3.4 | Spatial database |

#### 7.3.3 Development + DevOps Tools

| Tool | Purpose |
|---|---|
| **Git + GitHub** | Source control + PR workflow + branch protection |
| **VS Code** | Main code editor (Python, TypeScript, Dart extensions) |
| **Android Studio** | Flutter Android emulator + APK build |
| **DBeaver** | Database browsing |
| **Docker Desktop** | Container build + local testing |
| **pnpm** | Web monorepo package manager |
| **Turborepo** | Monorepo build orchestration |
| **Poetry** | Python dependency management |
| **Jupyter Notebook** | ML experiments + visualization |
| **CloudCompare** | View 3D point clouds (free, open-source) |
| **GitHub Actions** | CI/CD (5 workflows: web, mobile, api, ml, codeql) |
| **Vercel** | Web hosting (Hobby tier free) |
| **Railway** | API hosting ($5/mo) |
| **Supabase** | Database + Storage + Auth (Free tier) |
| **RunPod Serverless** | GPU compute (~$0.39/hr A10G) |
| **Sentry** | Error tracking (Web + Mobile + API) |
| **Figma** | UI/UX design (Person B) |
| **Discord / Line** | Daily team sync |

---

### 7.4 รายละเอียดโปรแกรมที่จะพัฒนา (Software Specification)

#### 7.4.1 Input Specification

| Input | Format | Source | Constraints | ใช้ใน Path |
|---|---|---|---|---|
| **LiDAR file** | `.las` (ASPRS) / `.laz` (compressed) | TLS scanner, Drone LiDAR, ALS | ≤ 500 MB; CRS = WGS84 หรือ Local UTM | Path A (primary) |
| **3D point cloud** | `.ply` (Stanford) | ผ่าน COLMAP / 3rd-party tools | ≤ 100 MB | ทั้ง Path A และ B |
| **Mobile photos** | JPG / JPEG ≥ 30 ภาพ + GPS EXIF | smartphone camera (Android/iOS) | 1920×1080 ขั้นต่ำ; ทั้งกอง ≤ 50 MB; GPS accuracy ≤ 20 m | Path B |
| **Plot polygon** | GeoJSON / WKT | user-drawn บน web map หรือ import | WGS84 (SRID 4326) | optional metadata |
| **CSV inventory** | CSV (UTF-8) | TGO / กรมป่าไม้ / projects เก่า | ต้องมี tree_id, species, location columns | optional bonus |

#### 7.4.2 Output Specification

**Per-tree JSON record:**

```json
{
  "tree_id": 1,
  "species_sci": "Tectona grandis",
  "species_th": "สัก",
  "species_confidence": 0.92,
  "location": {"lat": 18.7883, "lon": 98.9853, "alt": 320.4},
  "dbh_cm": 25.3,
  "height_m": 15.8,
  "crown_radius_m": 3.2,
  "volume_m3": 0.45,
  "biomass_kg": 292.5,
  "carbon_kg": 137.5,
  "co2eq_kg": 504.2,
  "point_count": 8472,
  "wood_leaf_iou": 0.78,
  "scanned_at": "2026-05-25T08:30:00Z"
}
```

**PDF Carbon Certificate:**
- A4, Thai + English bilingual
- ส่วนประกอบ: Plot info, owner info, scan date, per-tree breakdown table, total CO₂eq, TGO reference number, QR code → verify on platform
- Generated client-side ผ่าน `@react-pdf/renderer` (Phase 2)

**3D Segmented PLY:**
- Stanford PLY format
- มี XYZ + class (wood/leaf/ground) + RGB ตามคลาส
- Downloadable จาก dashboard

**Per-plot CSV summary:**
- Columns: tree_id, species, dbh_cm, height_m, volume_m3, carbon_kg, co2eq_kg, location_lat, location_lon
- เปิดได้ใน Excel / Google Sheets

#### 7.4.3 Functional Specification (10 ฟังก์ชันหลัก)

1. **Authentication** — Sign up / Sign in ผ่าน Supabase Auth (email + password; OAuth ใน Phase 2)
2. **LiDAR file upload** — Drag-and-drop หรือ click-to-upload .las/.laz; chunked + resumable ผ่าน tus protocol
3. **Mobile photo capture** — Camera-only (ห้าม gallery upload); auto-burst 30+ ภาพ; GPS-embedded EXIF
4. **Pipeline job dispatch** — POST /jobs → queue → GPU worker → progress via WebSocket
5. **3D Point Cloud Viewer** — Three.js + R3F แสดง wood/leaf/ground colors; orbit, zoom, pan controls; เลือกต้นไม้ดู metadata
6. **GIS Map view** — Leaflet แสดงทุกต้นไม้บน OpenStreetMap; filter ตาม species, date, region; marker cluster
7. **Per-tree results dashboard** — DBH, Height, Volume, Biomass, Carbon, CO₂eq + mini 3D viewer + bar chart
8. **Marketplace browsing** — กรอง plots ตาม location, species, ราคา/tCO₂eq; preview 3D + GIS
9. **Mock checkout** — Buyer คลิก "Buy X tCO₂eq" → mock payment → insert transaction → generate certificate
10. **PDF certificate generation + download** — Bilingual A4; ลายเซ็น digital; QR verify code

#### 7.4.4 Software Design / โครงสร้างซอฟต์แวร์

**System Architecture (4 layers):**

```
┌─ Layer 1: INPUT ─────────────────────────────────────┐
│  LiDAR Upload (primary) | Mobile Photogrammetry      │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌─ Layer 2: WEB / API GATEWAY ─────────────────────────┐
│  Web Dashboard (Next.js 14) ↔ FastAPI Service        │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌─ Layer 3: PROCESSING ────────────────────────────────┐
│  Supabase (DB + Storage)                              │
│  Job Queue (Supabase PGMQ)                            │
│  RunPod Serverless GPU (ML Pipeline)                  │
│  COLMAP + OpenMVS (Photogrammetry)                    │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌─ Layer 4: OUTPUT ────────────────────────────────────┐
│  Carbon Certificate (PDF)                             │
│  B2B Marketplace listing                              │
│  GIS Map + Audit Log                                  │
└──────────────────────────────────────────────────────┘
```

ดู `fig14_system_simplified.png` สำหรับภาพรวมระบบแบบเข้าใจง่ายใน 1 ภาพ (input → AI → output) และ `fig09_architecture.png` ใน Appendix C สำหรับภาพสถาปัตยกรรมแบบ 4 layers resolution สูง

**Monorepo Structure:**

```
Project_Carbon/
├── apps/
│   ├── web/           — Next.js 14 (Web Dashboard)
│   └── mobile/        — Flutter (Mobile App)
├── services/
│   ├── api/           — FastAPI (Backend API)
│   └── ml/            — Python ML Pipeline (8 stages + photogrammetry)
├── packages/
│   ├── ui/            — Shared React components
│   ├── types/         — TypeScript types
│   └── design-tokens/ — Colors + fonts (Tailwind + Flutter)
├── docs/              — All documentation (architecture, ml, decisions, proposal)
└── .github/workflows/ — 5 CI workflows
```

**Database Schema (PostgreSQL + PostGIS):**

| Table | Purpose |
|---|---|
| `users` | Account + role (community / industrial / auditor) |
| `plots` | แปลงป่า + geometry (POLYGON, SRID 4326) |
| `trees` | ต้นไม้รายต้น + location (POINT) + measurements (DBH, H, V, Carbon) |
| `jobs` | ML pipeline jobs + status + progress + input_url + output_url |
| `transactions` | Carbon credit sales (buyer, plot, amount, price, timestamp) |
| `species_db` | Allometric coefficients per species (5 rows) |
| `audit_log` *(Phase 2)* | Immutable log ทุก mutation (RLS protected) |

ทุก table มี **Row-Level Security (RLS)** policies — community user เห็นเฉพาะของตัวเอง, auditor เห็นทุกอย่าง, industrial buyer เห็น marketplace + own transactions

#### 7.4.5 การออกแบบ UX สำหรับงานประมวลผลที่ใช้เวลานาน (Async Processing UX)

เนื่องจากการประมวลผล LiDAR point cloud ใช้เวลาประมาณ **10–15 นาที/แปลง** (ขึ้นกับขนาดไฟล์และจำนวนต้น) การออกแบบให้ผู้ใช้ "นั่งรอหน้าค้าง" จึงไม่เหมาะสม ระบบจึงใช้สถาปัตยกรรมแบบ **asynchronous job + real-time progress** เพื่อให้ประสบการณ์ใช้งานลื่นไหลแม้งานจะใช้เวลานาน ตามหลักการต่อไปนี้:

| ปัญหา UX ของงานที่ใช้เวลานาน | วิธีแก้ของ CarbonScan AI |
|---|---|
| อัปโหลดไฟล์ใหญ่ (≤ 500 MB) แล้วเน็ตหลุด ต้องเริ่มใหม่ | **Resumable upload (tus protocol)** — อัปโหลดต่อจากจุดเดิมได้ + แสดง % อัปโหลดแยกจาก % ประมวลผล |
| กดแล้วหน้าค้าง ไม่รู้ว่าระบบทำงานอยู่ไหม | ได้ **Job ID ทันที** + แสดง progress ของ **8 ขั้นตอน (ระบุชื่อ)** พร้อม % รวม ผ่าน **WebSocket** แบบ real-time |
| ไม่รู้ว่าต้องรออีกนานเท่าไร | แสดง **เวลาที่เหลือโดยประมาณ (ETA)** คำนวณจาก stage ปัจจุบัน + ขนาดไฟล์ |
| ต้องเฝ้าหน้าจอจนเสร็จ | **ปิดหน้า/ออกไปทำงานอื่นได้** — แจ้งเตือนเมื่อเสร็จผ่าน **อีเมล + push notification (มือถือ)** และดูผลย้อนหลังได้จากหน้า "งานของฉัน" |
| ถ้า pipeline ล้มเหลว ผู้ใช้เห็นแค่ spinner ค้าง | **แสดง error ราย stage** + ปุ่ม retry เฉพาะ stage ที่ fail (ไม่ต้องเริ่มใหม่ทั้งหมด) |
| งานยาวแต่ผู้ใช้อยากเห็นผลก่อน | แสดง **ผลลัพธ์บางส่วน (partial preview)** ทันทีที่แต่ละ stage เสร็จ — เห็น point cloud + ต้นไม้ที่ segment แล้ว ก่อนคำนวณคาร์บอนเสร็จ |

**กลไกทางเทคนิคที่รองรับ:**
- **Job Queue (Supabase PGMQ)** — รับงานเข้าคิวแล้วคืน Job ID ทันที ไม่ block request
- **WebSocket `/api/v1/ws/jobs/{id}`** — ส่ง event `{stage, progress, eta}` กลับ client ทุกครั้งที่ stage เปลี่ยน
- **Skeleton / optimistic UI** — แสดงโครงหน้าผลลัพธ์ก่อนข้อมูลจริงมาถึง
- **Mobile background upload** — อัปโหลดต่อใน background + แจ้งเตือนผ่าน push เมื่อเสร็จ

> ภาพ wireframe ของหน้าจอนี้ดู `fig15_processing_ux.png` (Appendix C) — แสดง progress 8 ขั้น, % รวม, ETA และข้อความ "ปิดหน้านี้ได้ ระบบจะแจ้งเตือนเมื่อเสร็จ"

---

### 7.5 ขอบเขตและข้อจำกัดของโปรแกรมที่พัฒนา

#### 7.5.1 In-Scope (เวอร์ชัน Prototype สำหรับ NSC 2026)

| Component | รายละเอียด |
|---|---|
| **ML Pipeline** | 8 ขั้นตอนครบ (Phase 1 heuristic + Phase 2 deep learning targets) |
| **Species Coverage** | 5 ชนิด: สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง |
| **Input Formats** | `.las`, `.laz`, `.ply` (Path A) + JPG 30-50 ภาพ (Path B) + CSV import (bonus) |
| **Output** | JSON per tree + 3D PLY + PDF Certificate + Marketplace listing + GIS Map |
| **Web Dashboard** | Responsive (mobile + desktop), 4 personas (Community, Industrial, Auditor, Admin) |
| **Mobile App** | Android (primary), iOS (secondary if Mac available) |
| **Marketplace** | Mock payment flow (real payment ใน Phase post-NSC) |
| **Anti-Fraud** | GPS dedup + EXIF + camera-only (audit log: Phase 2) |
| **Validation** | บน Demol 2021 (Belgium 65 trees) — **เสร็จแล้ว**; NEON US (Phase 2 plan) |

#### 7.5.2 Out-of-Scope (ไม่อยู่ในขอบเขตเฟสนี้)

- รองรับต้นไม้ทุกชนิดบนโลก (ขยายใน Phase 2+)
- Drone LiDAR direct integration (อนุญาตให้ user upload ไฟล์ .las ได้)
- Blockchain-based ledger (Phase 3+)
- Real-time scanning (ใช้ async pipeline แทน — 10–15 นาที latency)
- การชำระเงินจริง (ใช้ mock checkout สำหรับ NSC)
- การส่งออกใบรับรองที่รับรองโดย TGO อย่างเป็นทางการ (เป็น Pilot — ไม่ใช่ Certified)
- รองรับ multi-language UI > 2 ภาษา (เริ่มต้นแค่ไทย + อังกฤษ)

#### 7.5.3 Constraints (ข้อจำกัด)

- **ทีมงาน:** 3 คน (User + Person A + Person B)
- **ระยะเวลา:** 12 สัปดาห์ (30 พ.ค. – 21 ส.ค. 2569)
- **งบประมาณ Cloud:** ≤ $30/เดือน (RunPod serverless inference เท่านั้น; training ใช้ Colab/Kaggle free tier)
- **Hardware:** ทีมไม่มี iPhone Pro ที่มี LiDAR Sensor — ไม่ทำ iPhone LiDAR app (ADR-0002)
- **ทีมไม่มี Mac** สำหรับ build iOS — ใช้ Codemagic / Bitrise cloud macOS แทน (optional)

#### 7.5.4 Assumptions (สมมติฐาน)

- ผู้ใช้ Web ใช้ Browser modern (Chrome 90+, Safari 14+, Edge 90+, Firefox 88+)
- ความเร็วอินเทอร์เน็ตของ user ≥ 5 Mbps สำหรับ upload .las file
- Android ที่ใช้ทดสอบ ≥ API 26 (Android 8.0 Oreo)
- เข้าถึง Public LiDAR Dataset ได้ (Demol 2021 ✅; NEON ใน Phase 2)
- Auditor / Carbon survey contractor ที่จะใช้ระบบมี LiDAR scanner อยู่แล้ว (TLS หรือ Drone LiDAR)

---

## ส่วนที่ 8: แผนการดำเนินงาน (Timeline & Milestones)

| Phase | ระยะเวลา | Output หลัก | Deliverables |
|---|---|---|---|
| **0: Proposal** | 20-29 พ.ค. 2569 | ข้อเสนอโครงการ | เอกสาร Proposal + ลายเซ็นที่ปรึกษา + อัปโหลด SIMs |
| **1: Foundation** | 30 พ.ค. – 30 มิ.ย. 2569 | Infrastructure + ML pipeline (non-AI) | Repo setup, Auth, ML pipeline ขั้น 1-4, Belgium validation refined |
| **2: Core AI** | 1-14 ก.ค. 2569 | PointNet++ trained + Full pipeline | Wood-Leaf model + Web Dashboard + 3D Viewer |
| **3: Mobile + Submission** | 15-17 ก.ค. 2569 | Mobile App + Final Report | APK + Marketplace + ส่งรายงานสมบูรณ์ |
| **4: Pitching Prep** | 7-20 ส.ค. 2569 | Demo video + Pitch deck | Video 3-5 นาที + Slides + Rehearsal |
| **5: Competition** | 21-24 ส.ค. 2569 | Final Pitching | นำเสนอรอบชิงชนะเลิศ |

### Gantt Chart (ภาพรวม)

```
                พ.ค.       มิ.ย.        ก.ค.        ส.ค.
                |─────|─────|─────|─────|─────|─────|
Proposal       ████
Infrastructure  ████████████
ML Pipeline           ████████████████████
Web Dashboard          ████████████████████████
Mobile App                          █████████
Documentation       ████████████████████████████████
Pitching                                      ████████
```

---

## ส่วนที่ 9: ผลที่คาดว่าจะได้รับ (Expected Outcomes)

### 9.1 ผลผลิตเชิงเทคนิค (Technical Deliverables)

1. **ระบบประเมินคาร์บอนต้นไม้แบบอัตโนมัติ** ที่บรรลุเป้าหมายความแม่นยำ:
   - DBH MAE ≤ 2 cm **(บรรลุแล้ว: 1.17 cm บน Demol 2021)**
   - Tree Height MAE ≤ 1 m **(บรรลุแล้ว: 0.54 m)**
   - Wood-Leaf IoU ≥ 0.70 (Phase 2 target)
2. **เวลาประมวลผล** ≤ 15 นาที/แปลง (ไม่รวม upload time)
3. **Web Dashboard** ใช้งานได้จริงผ่าน https://carbonscan-ai.vercel.app
4. **Mobile App** (Android APK) ดาวน์โหลดได้จาก GitHub Releases
5. **Trained Models** เผยแพร่บน Hugging Face Hub แบบ Open Source (Phase 2)
6. **Source Code** เปิดเผยบน GitHub แบบ MIT License (หลังการแข่งขัน)
7. **Validation dataset + results** เปิดเผยทำให้ replicable

### 9.2 ผลกระทบเชิงสังคม (Social Impact)

**1. เกษตรกร / ชุมชนผู้ปลูกต้นไม้:**
- เปลี่ยนต้นไม้ที่ปลูกเป็นรายได้ผ่านการขาย Carbon Credit
- ลดต้นทุนเข้าระบบจากระดับ 50,000–200,000 บาท → ใกล้ 0 บาท (mobile path) หรือ ~1,500 บาท (auditor path) — ลดราว 100 เท่า

**2. โรงงานอุตสาหกรรม / SMEs:**
- มีตัวกลาง B2B ที่โปร่งใส (เห็น GPS หมุดของต้นไม้ทุกต้นที่สนับสนุน)
- หลีกเลี่ยงข้อครหา Greenwashing
- พร้อมรับมือมาตรการ CBAM ของ EU
- สร้าง ESG Report ที่ Verifiable ระดับ 3D

**3. TGO / Carbon Auditors:**
- ลดเวลาลงพื้นที่จริงจากหลายสัปดาห์ → ชั่วโมง
- เพิ่ม capacity ในการ verify โครงการคาร์บอนเครดิต
- ตรวจสอบความถูกต้องของข้อมูลย้อนหลังได้จากไฟล์ 3D Point Cloud

**4. ภาคการศึกษา / วิจัย:**
- Open Source Dataset และ Trained Model สำหรับ research community
- ลด barrier ในการทำงานวิจัย Forest Inventory ในไทย
- โอกาสตีพิมพ์ paper ระดับนานาชาติ (ICCV/CVPR Workshop, Remote Sensing journal)

**5. ประเทศไทย (National-level):**
- สนับสนุนเป้าหมาย Carbon Neutrality 2050 ของรัฐบาล
- เพิ่มขีดความสามารถส่งออกสินค้าเข้าตลาด EU (CBAM compliance)
- พัฒนา Climate FinTech ecosystem ของไทย

### 9.3 ผลกระทบเชิงวิชาการ (Academic Impact)

โครงการนี้เป็นการประยุกต์ใช้ Computer Science กับ Forestry Science แบบ Multi-disciplinary อย่างชัดเจน:
- การ Port อัลกอริทึมจาก R (lidR) เป็น Python — เป็นประโยชน์ต่อ Python community
- การปรับ PointNet++ ให้ทำงานกับข้อมูลป่าไม้ของไทย — เป็น novel contribution
- การสร้าง Calibration Dataset Photogrammetry-vs-Ground Truth สำหรับไม้เศรษฐกิจไทย — เป็น open dataset แรกของประเภทนี้

### 9.4 ผลสำเร็จที่ใช้วัด (Success Metrics)

| Metric | Baseline (วิธีดั้งเดิม) | Target (CarbonScan AI) | Improvement |
|---|---|---|---|
| ต้นทุน Auditing / แปลง | 50,000–200,000 บาท | ~1,500 บาท (auditor) / ~0 (mobile) | **~100×** |
| เวลา / แปลง | 2–4 สัปดาห์ | ประมวลผล ≤ 15 นาที (เสร็จภายในวันเดียว) | **หลายร้อยเท่า** |
| Reach (เกษตรกร) | ฟาร์มขนาดใหญ่เท่านั้น | ทุกระดับ (มี smartphone) | Unlimited |
| Transparency (โรงงาน) | Excel report | 3D Visual + GPS | Verifiable |

---

## ส่วนที่ 10: ข้อจำกัดและแนวทางแก้ไข (Risks & Mitigations)

### 10.1 Technical Risks

| ความเสี่ยง | ความน่าจะเป็น | ผลกระทบ | แนวทางแก้ |
|---|---|---|---|
| Photogrammetry แม่นยำต่ำกว่า LiDAR | กลาง | สูง | Mobile = secondary path ที่ optional, primary คือ LiDAR upload; รายงาน Error margin ใน UI |
| PointNet++ Train ไม่ทันก่อน 17 ก.ค. | กลาง | กลาง | Phase 1 ใช้ rule-based PCA fallback ที่ functional แล้ว — DL เป็น enhancement |
| Cloud GPU ค่าใช้จ่ายเกินงบ | ต่ำ | กลาง | ตั้ง budget cap $30/เดือน + ใช้ Colab/Kaggle ฟรีใน dev phase |
| Dataset LiDAR ไทยไม่มี | สูง | กลาง | ใช้ NEON (USA) + Belgium Demol 2021 ✅; field collection ใน Phase 3 |
| iOS build ไม่ได้ (ไม่มี Mac) | สูง | ต่ำ | ใช้ Codemagic / Bitrise cloud macOS build + Focus Android เป็นหลัก |
| Watershed over-segmentation | กลาง | ต่ำ | ระบบมี filter DBH < 2 cm กรอง fragments; Phase 2 ใช้ marker-controlled watershed |

### 10.2 Operational Risks

| ความเสี่ยง | ความน่าจะเป็น | ผลกระทบ | แนวทางแก้ |
|---|---|---|---|
| ลายเซ็นที่ปรึกษา/คณบดีไม่ทัน 29 พ.ค. | สูง | ฆาตกร (ส่งไม่ได้) | เริ่มเดินเอกสารตั้งแต่ 25 พ.ค., เตรียม PDF Preview ส่งล่วงหน้า |
| ทีมงานคนใดคนหนึ่งติดสอบ/ป่วย | สูง | กลาง | งาน Critical Path ให้ทุกคนช่วยร่าง, มี backup ทุก Role |
| Internet วันแข่งไม่เสถียร | ต่ำ | สูง | เตรียม Offline Demo (pre-computed dataset + downloaded videos) |

### 10.3 Q&A Defense (เผื่อกรรมการถาม)

**Q1: Photogrammetry แม่นยำเท่า LiDAR ไหม?**
A: ไม่เท่า — แต่อยู่ในระดับ ±5-10 cm ซึ่งเพียงพอสำหรับ Voluntary Carbon Market (T-VER) [18, 20] ทั้งนี้ระบบมี Calibration กับ Ground Truth + รายงาน Confidence Score ทุก measurement และ Mobile เป็น secondary path สำหรับ smallholder เท่านั้น — primary input คือ LiDAR Upload จาก auditor มืออาชีพ

**Q2: จะรู้ได้ไงว่าไม่นับซ้ำ?**
A: ระบบมีกลไก Anti-Fraud 4 ชั้น (Section 7.2.4) — GPS ทศนิยม 6 ตำแหน่ง + EXIF validation + Camera-only + Server-side dedup ผ่าน PostGIS ST_DWithin

**Q3: ระบบเรา validate ยังไง?**
A: ใช้ peer-reviewed dataset Demol et al. 2021 (Trees Journal, 65 ต้น 4 species จาก Belgium พร้อม destructive sampling) — ผลลัพธ์ DBH MAE 1.17 cm, Height MAE 0.54 m อยู่ใน TLS literature range

**Q4: ทำไม Volume error 18.8% สูงกว่า DBH/Height?**
A: เพราะ Phase 1 ใช้ taper equation (V = π/4 × DBH² × H × form_factor) ซึ่งเป็น approximation — Phase 2 จะใช้ full TreeQSM (Raumonen et al. 2013) ลด error เหลือ 5-10%

**Q5: ค่าใช้จ่าย Run server เดือนละเท่าไหร่?**
A: ในระดับต้นแบบ (~100 jobs/เดือน) ประมาณ **~$15/เดือน (~520 บาท)** = RunPod serverless inference ~$10 (จ่ายตามวินาทีที่รันจริง scale-to-zero) + Railway ~$5; ส่วน Supabase และ Vercel ใช้ free tier (0 บาท). ระดับ production มี Business Model B2B subscription cover ค่าใช้จ่าย

**Q6: ใช้ GPU อะไรเทรน Model?**
A: Training บน Google Colab / Kaggle **free tier** (NVIDIA T4/P100 16GB ฟรี) หรือ Local RTX 3060; Production inference บน RunPod Serverless (A10G 24GB) แบบ pay-per-second เพื่อ scale-to-zero — หลีกเลี่ยงค่า GPU ประจำ

---

## ส่วนที่ 11: งบประมาณ (Budget)

> **หลักการ:** ออกแบบให้ใช้งบ **ต่ำที่สุด** — พึ่ง free tier เป็นหลัก และจ่ายเฉพาะส่วนที่จำเป็นจริงแบบ pay-per-use เพื่อให้เหมาะกับทีมนักศึกษาและกรอบงบ NSC (~3,000–5,000 บาท)

### 11.1 กลยุทธ์ต้นทุนต่ำ (Cost-Minimization Strategy)

| ส่วน | วิธีประหยัด | ค่าใช้จ่าย |
|---|---|---|
| **Training GPU** | Google Colab / Kaggle **free tier** (T4/P100 ฟรี) แทน Colab Pro+ | 0 บาท |
| **Inference GPU** | RunPod Serverless จ่ายตามวินาที (scale-to-zero) — รันเฉพาะตอนประมวลผล/เดโม | ตามใช้จริง |
| **Database + Auth + Storage** | Supabase **free tier** (500 MB DB, 1 GB storage) | 0 บาท |
| **Web hosting** | Vercel **Hobby** (ฟรี) + subdomain `*.vercel.app` | 0 บาท |
| **API hosting** | Railway Hobby | ~$5/เดือน |
| **Software ทั้งหมด** | Open-source (Next.js, FastAPI, Flutter, PyTorch, COLMAP ฯลฯ) | 0 บาท |

### 11.2 รายการที่ขอสนับสนุนจาก NSC (ประมาณการขั้นต่ำ)

| รายการ | จำนวน | ราคา/หน่วย (บาท) | รวม (บาท) |
|---|---|---|---|
| RunPod Serverless GPU (inference ~$10/เดือน + เดโม) | 3 เดือน | ~350 | 1,050 |
| Railway (API hosting ~$5/เดือน) | 3 เดือน | ~180 | 540 |
| ค่าเดินทางเก็บ ground truth ไม้ไทย (ภาคสนาม) | — | — | 1,200 |
| ค่าพิมพ์เอกสาร (Proposal + Final Report) | — | — | 700 |
| ค่าจัดทำ Poster A1 (รอบชิงชนะเลิศ) | 1 | 800 | 800 |
| **รวม** | | | **~4,300** |

⚠️ ปรับยอดตามที่ NSC อนุมัติจริง — ส่วนที่เกินทีมใช้ free tier ทดแทนหรือ self-fund

### 11.3 รายการที่ทีมรับผิดชอบเอง

- Hardware (Notebook ของทีม, โทรศัพท์ Android)
- Software License (ทั้งหมด Open Source / Free Tier — 0 บาท)
- ค่าอินเทอร์เน็ต / ค่าไฟ
- เวลาในการพัฒนา

---

## ส่วนที่ 12: เอกสารอ้างอิง (References)

[1] UNFCCC. (2015). *Paris Agreement*. United Nations Framework Convention on Climate Change. https://unfccc.int/process-and-meetings/the-paris-agreement

[2] European Commission. (2023). *Regulation (EU) 2023/956 establishing a carbon border adjustment mechanism*. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956

[3] Thailand NDC submission to UNFCCC. (2021). *Thailand's Updated Nationally Determined Contribution under the Paris Agreement*. COP26 announcement.

[4] กรมป่าไม้. (2566). *รายงานสถานการณ์ป่าไม้ของประเทศไทย พ.ศ. 2566*. https://www.forest.go.th

[5] TGO. (2565). *T-VER Methodology Documents: Forestry Sector*. องค์การบริหารจัดการก๊าซเรือนกระจก (องค์การมหาชน). https://ghgreduction.tgo.or.th/en/tver-method

[6] Brown, S. (1997). *Estimating biomass and biomass change of tropical forests: a primer*. FAO Forestry Paper 134. http://www.fao.org/3/w4095e/w4095e00.htm

[7] World Resources Institute & WBCSD. (2004). *The Greenhouse Gas Protocol: A Corporate Accounting and Reporting Standard, Revised Edition*. https://ghgprotocol.org/corporate-standard

[8] Qi, C. R., Yi, L., Su, H., & Guibas, L. J. (2017). PointNet++: Deep Hierarchical Feature Learning on Point Sets in a Metric Space. *Advances in Neural Information Processing Systems (NeurIPS 2017)*. arXiv:1706.02413

[9] Thomas, H., Qi, C. R., Deschaud, J. E., Marcotegui, B., Goulette, F., & Guibas, L. J. (2019). KPConv: Flexible and Deformable Convolution for Point Clouds. *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, 6411–6420.

[10] Roussel, J.-R., Auty, D., Coops, N. C., Tompalski, P., Goodbody, T. R., Meador, A. S., et al. (2020). lidR: An R package for analysis of Airborne Laser Scanning (ALS) data. *Remote Sensing of Environment*, 251, 112061. DOI: [10.1016/j.rse.2020.112061](https://doi.org/10.1016/j.rse.2020.112061)

[11] Raumonen, P., Kaasalainen, M., Åkerblom, M., Kaasalainen, S., Kaartinen, H., Vastaranta, M., et al. (2013). Fast Automatic Precision Tree Models from Terrestrial Laser Scanner Data. *Remote Sensing*, 5(2), 491–520. DOI: [10.3390/rs5020491](https://doi.org/10.3390/rs5020491)

[12] Zhang, W., Qi, J., Wan, P., Wang, H., Xie, D., Wang, X., & Yan, G. (2016). An Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth Simulation. *Remote Sensing*, 8(6), 501. DOI: [10.3390/rs8060501](https://doi.org/10.3390/rs8060501)

[13] Khosravipour, A., Skidmore, A. K., Isenburg, M., Wang, T., & Hussin, Y. A. (2014). Generating Pit-free Canopy Height Models from Airborne Lidar. *Photogrammetric Engineering & Remote Sensing*, 80(9), 863–872. DOI: [10.14358/PERS.80.9.863](https://doi.org/10.14358/PERS.80.9.863)

[14] TGO. (2017). *Forestry Sector Greenhouse Gas Calculation Guideline*. องค์การบริหารจัดการก๊าซเรือนกระจก (องค์การมหาชน), ประเทศไทย.

[15] IPCC. (2006). *2006 IPCC Guidelines for National Greenhouse Gas Inventories, Vol. 4: Agriculture, Forestry and Other Land Use (AFOLU)*. https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html

[16] Schönberger, J. L., & Frahm, J. M. (2016). Structure-from-Motion Revisited. *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 4104–4113. (COLMAP)

[17] Cernea, D. (2020). *OpenMVS: Open Multi-View Stereo reconstruction library*. https://github.com/cdcseacave/openMVS

[18] Liang, X., Wang, Y., Pyörälä, J., Lehtomäki, M., Yu, X., Kaartinen, H., et al. (2019). Forest in situ observations through Unmanned Aerial Vehicle-borne photogrammetry. *Forest Ecosystems*, 6(1), 1–16. DOI: [10.1186/s40663-019-0173-3](https://doi.org/10.1186/s40663-019-0173-3)

[19] Vicari, M. B., Disney, M., Wilkes, P., Burt, A., Calders, K., & Woodgate, W. (2019). Leaf and wood classification framework for terrestrial LiDAR point clouds. *Methods in Ecology and Evolution*, 10(5), 680–694. (TLSeparation) DOI: [10.1111/2041-210X.13144](https://doi.org/10.1111/2041-210X.13144)

[20] Mokros, M., Tabacchi, G., Surovy, P., Krásny, M., Slávik, M., Tomastik, J., & Plichta, R. (2021). Estimating individual tree height and diameter at breast height (DBH) from terrestrial laser scanning (TLS) data at plot level. *Forests*, 12(4), 444. DOI: [10.3390/f12040444](https://doi.org/10.3390/f12040444)

[21] Tsutsumi, T., Yoda, K., Sahunalu, P., Dhanmanonda, P., & Prachaiyo, B. (1983). Forest: Felling, sampling and analysis methods. In *Forest ecological studies of the watershed in Northeast Thailand*. Kyoto University: Forest Ecology of the Monsoon Asia Series, 13–62.

[22] Ogawa, H., Yoda, K., Kira, T., Ogino, K., Shidei, T., Ratanawongse, D., & Apasutaya, C. (1965). Comparative ecological study on three main types of forest vegetation in Thailand. *Nature & Life in Southeast Asia*, 4, 49–80.

[23] Yiping, L., Yanxia, L., Buckingham, K., Henley, G., & Guomo, Z. (2010). *Bamboo and Climate Change Mitigation: A comparative analysis of carbon sequestration*. INBAR Technical Report 32, International Network for Bamboo and Rattan (INBAR), Beijing.

[24] Chiarucci, A., D'Auria, F., De Dominicis, V., Lagana, A., Perini, C., & Salerni, E. (2014). Biomass estimation in rubber (Hevea brasiliensis Müll. Arg.) plantations using allometric models. *Forest Ecology and Management*, 318, 220–228.

[25] **Demol, M., Verbeeck, H., Gielen, B., Armston, J., Burt, A., Disney, M., Duncanson, L., Hackenberg, J., Kükenbrink, D., Lau, A., Ploton, P., Sewdien, A., Stovall, A., Takoudjou, S. M., Volkova, L., Weston, C., Wortel, V., & Calders, K. (2021). Estimating forest above-ground biomass with terrestrial laser scanning: current status and future directions. *Trees*, 35, 671–685. DOI: [10.1007/s00468-020-02067-7](https://doi.org/10.1007/s00468-020-02067-7) — Dataset: [10.5281/zenodo.4557401](https://doi.org/10.5281/zenodo.4557401)**

[26] Chave, J., Réjou-Méchain, M., Búrquez, A., Chidumayo, E., Colgan, M. S., Delitti, W. B., et al. (2014). Improved allometric models to estimate the aboveground biomass of tropical trees. *Global Change Biology*, 20(10), 3177–3190. DOI: [10.1111/gcb.12629](https://doi.org/10.1111/gcb.12629)

[27] He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep Residual Learning for Image Recognition. *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 770–778. (ResNet) arXiv:1512.03385

[28] NEON (National Ecological Observatory Network). (2024). *Discrete return LiDAR point cloud (DP1.30003.001)*. Battelle, Boulder, CO, USA. https://data.neonscience.org/data-products/DP1.30003.001

[29] OpenTopography Facility. *High-Resolution Topography Data and Tools*. https://opentopography.org/

---

### 12.1 ตารางการอ้างอิงในแต่ละหัวข้อ (Citation Map)

> ระบุว่าเอกสารอ้างอิงแต่ละฉบับถูกใช้ในส่วนใดของข้อเสนอ (ตอบประเด็นการตรวจสอบการอ้างอิง)

| # | เอกสารอ้างอิง | ถูกอ้างในหัวข้อ |
|---|---|---|
| [1] | UNFCCC — Paris Agreement | 3.1 บริบทระดับโลก |
| [2] | EU — CBAM Regulation | บทคัดย่อ, 3.1 |
| [3] | Thailand NDC (Net Zero) | 3.2 บริบทประเทศไทย |
| [4] | กรมป่าไม้ — สถานการณ์ป่าไม้ | 3.2 |
| [5] | TGO — T-VER Methodology | 3.3 ต้นทุนการประเมิน |
| [6] | Brown — Biomass primer (FAO) | 7.2.8 สมการชีวมวล (อ้างเสริม) |
| [7] | WRI/WBCSD — GHG Protocol | 3.3 Greenwashing |
| [8] | Qi — PointNet++ | 3.4, 7.1.4, 7.2.2 (ขั้นที่ 5) |
| [9] | Thomas — KPConv | 3.4 โอกาสทางเทคโนโลยี |
| [10] | Roussel — lidR / Watershed | 3.4, 3.5, 7.1.4, 7.2.2 (ขั้นที่ 4) |
| [11] | Raumonen — TreeQSM | 3.4, 3.5, 7.1.4, 7.2.2 (ขั้นที่ 6) |
| [12] | Zhang — CSF ground filter | 3.4, 7.1.4, 7.2.2 (ขั้นที่ 1) |
| [13] | Khosravipour — Pit-free CHM | 3.4, 7.1.4, 7.2.2 (ขั้นที่ 3) |
| [14] | TGO 2017 — Forestry Guideline | 3.5, 4 วัตถุประสงค์, 7.1.4, 7.2.8 |
| [15] | IPCC 2006 — AFOLU | 7.1.4, 7.2.8 (carbon fraction/root:shoot) |
| [16] | Schönberger — COLMAP (SfM) | 7.1.4, 7.2.3 |
| [17] | Cernea — OpenMVS (MVS) | 7.2.3 |
| [18] | Liang — UAV photogrammetry | 10.3 Q&A (ความแม่นยำ photogrammetry) |
| [19] | Vicari — TLSeparation | 7.2.2 (ขั้นที่ 5, Phase 1 PCA) |
| [20] | Mokros — TLS DBH/Height | 10.3 Q&A |
| [21] | Tsutsumi 1983 — สัก | 3.5, 7.2.8 (ตารางสัมประสิทธิ์) |
| [22] | Ogawa 1965 — ยางนา | 3.5, 7.2.8 |
| [23] | Yiping 2010 — ไผ่ | 3.5, 7.2.8 |
| [24] | Chiarucci 2014 — ยางพารา | 3.5, 7.2.8 |
| [25] | **Demol 2021 — Belgium validation dataset** | 4, 6, 7.2.5, 7.2.6 (ชุดข้อมูลทดสอบหลัก) |
| [26] | Chave 2014 — Pantropical allometric | 7.1.4, 7.2.8 (fallback Tier-3) |
| [27] | He — ResNet | 7.2.7 (Species classifier) |
| [28] | NEON — LiDAR dataset | 7.2.6, 7.5, 10 (Phase 2 plan) |
| [29] | OpenTopography | 7.2.6 (แหล่งข้อมูลเสริม) |

---

## ส่วนที่ 13: ภาคผนวก (Appendices)

### Appendix A: CV ทีมงาน
- A.1 [User] — ปริญญาตรี ปี X, [คณะ มหาวิทยาลัย], ทักษะ: Python, PyTorch, Flutter, FastAPI
- A.2 [Person A] — ปริญญาตรี ปี X, ทักษะ: Next.js, TypeScript, React
- A.3 [Person B] — ปริญญาตรี ปี X, ทักษะ: Figma, Adobe Creative Suite

### Appendix B: CV ที่ปรึกษาโครงการ
- [ชื่อ-สกุล], [ตำแหน่งวิชาการ], [คณะ มหาวิทยาลัย], [ความเชี่ยวชาญ]

### Appendix C: Architecture Diagrams + Figures (Full Size)
- `fig14_system_simplified.png` — **ระบบใน 1 ภาพ (System at a Glance)** — input → AI → output ⭐
- `fig09_architecture.png` — System Architecture (v2, 4 layers)
- `fig10_user_flow.png` — User Journey
- `fig15_processing_ux.png` — **UX หน้าจอ "กำลังประมวลผล"** (async progress 8 ขั้น + ETA + แจ้งเตือน) ⭐
- `fig01-08` — Synthetic Pipeline Outputs (Steps 1-8)
- `fig11_belgium_dbh_parity.png` — DBH validation (Demol 2021)
- `fig12_belgium_height_parity.png` — Tree Height validation
- `fig13_belgium_volume_parity.png` — Volume validation

### Appendix D: UI/UX Mockups
- Web Dashboard screenshots (Person B จัดทำ)
- Mobile App screenshots (User capture)

### Appendix E: Letter of Recommendation (ถ้ามี)
- [ใส่จดหมายรับรองจากที่ปรึกษา / นักวิจัยที่เกี่ยวข้อง]

---

## 📋 Checklist ก่อนส่ง (29 พ.ค.)

### Content
- [ ] บทคัดย่อ 280-320 คำ ครอบคลุม Problem + Solution + Impact + Validation Results
- [ ] หลักการและเหตุผลมี citations
- [ ] วัตถุประสงค์ measurable
- [ ] Section 7 ครบ 7.1-7.5 ตาม NSC template (สำคัญที่สุด)
- [ ] Methodology ครบ 8 ขั้นตอน + Tech Stack ละเอียด
- [ ] Belgium validation results อยู่ใน Section 7.2.5
- [ ] Timeline + Gantt
- [ ] Risk & Mitigation 9+ ข้อ
- [ ] References 27+ citations ทุกตัวมี DOI

### Format
- [ ] Cover page (Person B)
- [ ] Font Sarabun 14pt body, 16pt heading
- [ ] Margin 2.54 cm รอบด้าน
- [ ] Page numbers
- [ ] Header + Footer
- [ ] PDF format
- [ ] ไม่มี typo
- [ ] Figures มี caption ภาษาไทย

### Signatures
- [ ] ที่ปรึกษาโครงการ
- [ ] หัวหน้าสถาบัน (คณบดี/ผอ.)

### Submission
- [ ] ลงทะเบียน SIMs ทุกคนในทีม
- [ ] อัปโหลดล่วงหน้า 24 ชม.
- [ ] Verify status = "Submitted"
- [ ] Save confirmation email
