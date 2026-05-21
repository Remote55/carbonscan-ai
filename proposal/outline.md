# ข้อเสนอโครงการ — CarbonScan AI

> **เป้าหมาย:** เอกสาร 8-10 หน้า (excluding cover + appendix) พร้อมส่ง NSC 2026
> **Status:** 🟡 Draft v1 — รอ feedback จากที่ปรึกษา
> **Format:** วาง content นี้ลง template Word ของสถาบัน → ส่งให้ Person B จัดหน้า

---

## หน้าปก (Cover Page) — Person B

```
┌─────────────────────────────────────────────┐
│  [โลโก้ CarbonScan AI]   [โลโก้ NSC 2026]   │
│                                              │
│    คาร์บอนสแกน เอไอ:                          │
│    แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้          │
│    อัจฉริยะด้วยเทคโนโลยี 3D Vision           │
│    และระบบจับคู่ชดเชยคาร์บอน                 │
│    ภาคอุตสาหกรรม                              │
│                                              │
│    CarbonScan AI: 3D Vision Tree Biomass     │
│    Assessment and B2B Carbon Offset          │
│    Matchmaking Platform                      │
│                                              │
│    [Hero Visual: tree + point cloud]         │
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
| **ชื่อโครงการ (ไทย)** | คาร์บอนสแกน เอไอ: แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้อัจฉริยะด้วยเทคโนโลยี 3D Vision และระบบจับคู่ชดเชยคาร์บอนภาคอุตสาหกรรม |
| **ชื่อโครงการ (อังกฤษ)** | CarbonScan AI: 3D Vision Tree Biomass Assessment and B2B Carbon Offset Matchmaking Platform |
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

ในยุคที่ภาคอุตสาหกรรมทั่วโลกต้องเผชิญมาตรการสิ่งแวดล้อมที่เข้มงวด เช่น นโยบายความเป็นกลางทางคาร์บอน (Carbon Neutrality) ภายในปี ค.ศ. 2050 และมาตรการการเก็บภาษีคาร์บอนข้ามแดนของสหภาพยุโรป (Carbon Border Adjustment Mechanism — CBAM) ที่จะเริ่มมีผลในปี 2026 ทำให้ "คาร์บอนเครดิตภาคป่าไม้" เป็นที่ต้องการอย่างมาก อย่างไรก็ตาม กระบวนการประเมินคาร์บอนเครดิตในประเทศไทยยังพึ่งพาผู้ตรวจสอบ (Auditor) ที่ต้องลงพื้นที่วัดขนาดต้นไม้ทีละต้นด้วยสายวัด ส่งผลให้มีต้นทุนสูงในระดับ 100,000 บาทต่อแปลง เกษตรกรรายย่อยจึงไม่สามารถเข้าถึงระบบ ขณะที่ภาคอุตสาหกรรมที่ลงทุนกับ CSR ก็ขาดเครื่องมือตรวจสอบผลลัพธ์ที่โปร่งใส มีความเสี่ยงต่อข้อครหา Greenwashing

โครงการ "CarbonScan AI" นำเสนอแพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ที่ผสานเทคโนโลยี **3D Point Cloud Processing** กับ **Deep Learning (PointNet++)** บนสถาปัตยกรรม Cloud-native โดยรองรับข้อมูล input สองช่องทาง: (1) ไฟล์ LiDAR Point Cloud `.las/.laz` จากผู้ตรวจสอบหรือฐานข้อมูลสาธารณะ และ (2) ภาพถ่ายจากกล้องสมาร์ทโฟนทั่วไป (Android/iOS) ที่ผ่านการ Reconstruction แบบ 3 มิติด้วยเทคนิค Structure-from-Motion (COLMAP/OpenMVS)

ระบบจะทำการแยกจุดข้อมูล (Semantic Segmentation) ใน Point Cloud ออกเป็น "ใบ" และ "ลำต้น/กิ่ง" ด้วย Deep Learning Model จากนั้นคำนวณปริมาตรไม้ผ่าน Quantitative Structure Model (QSM) และแปลงเป็นปริมาณคาร์บอนโดยใช้สมการแอลโลเมตริกตามมาตรฐานองค์การบริหารจัดการก๊าซเรือนกระจก (TGO) ผลลัพธ์จะแสดงผ่าน Web Dashboard 3D และระบบจับคู่ B2B ระหว่างชุมชนผู้ปลูกต้นไม้กับโรงงานอุตสาหกรรม พร้อมระบบป้องกันการนับซ้ำด้วย GPS Coordinates ระดับทศนิยม 6 ตำแหน่งและ EXIF metadata

เวอร์ชันต้นแบบรองรับการจำแนกและคำนวณคาร์บอนของไม้เศรษฐกิจ 5 ชนิด ได้แก่ ไม้สัก ไม้ยางนา ไม้ไผ่ ไม้ยางพารา และไม้มะค่าโมง โดยมีเป้าหมายความแม่นยำ DBH RMSE ≤ 5 cm และ Wood-Leaf Segmentation IoU ≥ 0.70 ระบบนี้คาดว่าจะช่วยลดต้นทุนการประเมินคาร์บอนเครดิตภาคป่าไม้ในไทยได้กว่า 100 เท่า เปิดทางให้เกษตรกรรายย่อยและชุมชนเข้าถึงระบบเศรษฐกิจสีเขียวที่เคยเป็นเอกสิทธิ์ของบริษัทขนาดใหญ่

**Keywords:** LiDAR, Point Cloud Processing, Wood-Leaf Semantic Segmentation, PointNet++, Carbon Credit, Allometric Equation, Photogrammetry, Climate FinTech, ESG, Sustainable Innovation

*(ความยาวประมาณ 280 คำ)*

---

## ส่วนที่ 3: หลักการและเหตุผล (Background and Rationale)

### 3.1 บริบทระดับโลก

การเปลี่ยนแปลงสภาพภูมิอากาศ (Climate Change) เป็นวิกฤตระดับโลกที่ทุกภาคส่วนต้องร่วมรับผิดชอบ ในปี ค.ศ. 2015 ภายใต้ Paris Agreement ประเทศต่าง ๆ ทั่วโลกได้ตกลงร่วมกันในการจำกัดอุณหภูมิเฉลี่ยของโลกไม่ให้สูงขึ้นเกิน 1.5°C จากระดับก่อนการปฏิวัติอุตสาหกรรม [1] ส่งผลให้ภาคอุตสาหกรรมต้องเร่งปรับตัวสู่การลดการปล่อยก๊าซเรือนกระจก โดยใช้กลไก "Carbon Credit" เพื่อชดเชยการปล่อยคาร์บอนที่ไม่สามารถลดได้

มาตรการสำคัญที่จะกระทบประเทศไทยโดยตรงคือ **Carbon Border Adjustment Mechanism (CBAM)** ของสหภาพยุโรป ซึ่งจะเริ่มเก็บภาษีคาร์บอนกับสินค้านำเข้าตั้งแต่ปี 2026 [2] ทำให้ภาคอุตสาหกรรมส่งออกของไทยต้องเร่งหาแนวทางลดและชดเชยคาร์บอน

### 3.2 บริบทประเทศไทย

ประเทศไทยได้ประกาศเป้าหมาย **Carbon Neutrality ภายในปี 2050** และ **Net Zero ภายในปี 2065** [3] ในการประชุม COP26 ส่งผลให้องค์การบริหารจัดการก๊าซเรือนกระจก (Thailand Greenhouse Gas Management Organization — TGO) เร่งพัฒนากลไกตลาดคาร์บอนภายในประเทศ (Thailand Voluntary Emission Reduction Program — T-VER)

ในกลุ่ม Nature-based Solutions "คาร์บอนเครดิตภาคป่าไม้" (Forest Carbon) เป็นหมวดที่มีศักยภาพสูงที่สุด เนื่องจากประเทศไทยมีพื้นที่ป่าไม้กว่า 102 ล้านไร่ และมีแผนเพิ่มพื้นที่ป่าให้ถึง 40% ของพื้นที่ประเทศ [4] อย่างไรก็ตาม การประเมินคาร์บอนเครดิตภาคป่าไม้ยังมีข้อจำกัดสำคัญ

### 3.3 ปัญหาคอขวด (Pain Points)

**1. ต้นทุนการประเมินสูง**

กระบวนการประเมินคาร์บอนเครดิตป่าไม้ตามมาตรฐาน T-VER ในปัจจุบันต้องใช้ผู้ตรวจสอบลงพื้นที่จริง โดยใช้สายวัดโอบรอบลำต้นเพื่อหาเส้นผ่านศูนย์กลางระดับอก (Diameter at Breast Height — DBH) และใช้กล้องเล็งวัดความสูง ทีละต้น ทำให้มีต้นทุนการสำรวจในระดับ 100,000-500,000 บาทต่อแปลง 50 ไร่ [5] เกษตรกรรายย่อยและชุมชนซึ่งมีพื้นที่ป่าหรือไม้ยืนต้นจำนวนมากจึงไม่สามารถเข้าสู่ระบบได้

**2. ความล่าช้าและความคลาดเคลื่อน**

การวัดทีละต้นด้วยมือมีโอกาสเกิด Human Error เช่น การคำนวณความสูงด้วยตา (visual estimation) อาจมีความคลาดเคลื่อนถึง ±15-20% [6] นอกจากนี้ การประเมินป่า 1 แปลงอาจใช้เวลาหลายสัปดาห์

**3. ขาดความโปร่งใสในการตรวจสอบย้อนหลัง**

โรงงานอุตสาหกรรมที่ลงทุนกับโครงการปลูกป่า CSR มักได้รับเพียง "รายงานสรุปจำนวนต้นไม้ที่ปลูก" ไม่สามารถตรวจสอบได้ว่าต้นไม้แต่ละต้นยังมีชีวิตหรือไม่ และดูดซับคาร์บอนได้เท่าไหร่จริง ๆ ทำให้เสี่ยงต่อข้อครหา **Greenwashing** [7]

### 3.4 โอกาสในการแก้ปัญหาด้วยเทคโนโลยี

ในช่วง 5 ปีที่ผ่านมา เทคโนโลยี 3D Vision ได้พัฒนาก้าวหน้าอย่างมาก ทั้งในด้านการสแกน Point Cloud (LiDAR sensor ที่ราคาถูกลง, photogrammetry ที่แม่นยำขึ้น) และ Deep Learning สำหรับการประมวลผล 3 มิติ (เช่น PointNet++ [8], KPConv [9]) ทำให้สามารถสร้างระบบประเมินคาร์บอนต้นไม้แบบอัตโนมัติได้ในต้นทุนที่ต่ำลงอย่างมหาศาล

ในขณะเดียวกัน Cloud Computing แบบ Serverless GPU (เช่น RunPod, Modal.com) ได้ทำให้นักวิจัยและสตาร์ทอัพระดับนักศึกษาสามารถเข้าถึงทรัพยากร GPU ที่จำเป็นได้ในราคาเพียงไม่กี่บาทต่อชั่วโมง ลดอุปสรรคในการพัฒนา Deep Tech อย่างมีนัยสำคัญ

### 3.5 ช่องว่างทางการตลาดและทางวิชาการ (Research Gap)

แม้ในต่างประเทศจะมีงานวิจัยและเครื่องมือเช่น `lidR` [10], TreeQSM [11] สำหรับการประมวลผล LiDAR ของต้นไม้ แต่ในประเทศไทยยัง:

- **ขาดแพลตฟอร์มสำเร็จรูป** ที่เชื่อมต่อตั้งแต่การ scan → ประมวลผล → ออกใบรับรอง → ตลาด B2B
- **ขาดสมการแอลโลเมตริก digital** ที่นำมาใช้กับซอฟต์แวร์ได้โดยตรง (ข้อมูล TGO ส่วนใหญ่อยู่ใน PDF ที่ต้องคำนวณด้วยมือ)
- **ขาดเครื่องมือสำหรับชุมชน** ที่ไม่ต้องการ Hardware แพง (LiDAR Scanner เครื่องละหลายแสน-ล้านบาท)

CarbonScan AI จึงถูกออกแบบมาเพื่อปิดช่องว่างเหล่านี้

---

## ส่วนที่ 4: วัตถุประสงค์ของโครงการ (Objectives)

โครงการนี้มีวัตถุประสงค์เฉพาะ (Measurable Objectives) ดังนี้:

1. **พัฒนาระบบประมวลผล LiDAR Point Cloud อัตโนมัติ** ที่สามารถ:
   - แยกจุดข้อมูลเป็นพื้นดิน/ไม่ใช่พื้นดิน (Ground Classification ด้วย CSF algorithm)
   - แยกต้นไม้ทีละต้น (Individual Tree Detection ด้วย Watershed segmentation)
   - แยกใบและลำต้น/กิ่ง (Wood-Leaf Semantic Segmentation) ด้วย Deep Learning โดยมี IoU ≥ 0.70

2. **พัฒนาระบบคำนวณปริมาตรไม้** (Quantitative Structure Model — QSM) และแปลงเป็นปริมาณคาร์บอนผ่านสมการแอลโลเมตริกตามมาตรฐาน TGO โดยรองรับไม้เศรษฐกิจ 5 ชนิด ได้แก่ ไม้สัก ไม้ยางนา ไม้ไผ่ ไม้ยางพารา และไม้มะค่าโมง

3. **พัฒนา Web Dashboard** ที่แสดงผล:
   - 3D Point Cloud Viewer ที่ไฮไลต์การแบ่งใบ/ลำต้นด้วยสี
   - GIS Map พร้อม GPS pins ของต้นไม้แต่ละต้น
   - Marketplace สำหรับการจับคู่ B2B ระหว่างชุมชนกับโรงงานอุตสาหกรรม

4. **พัฒนา Mobile Application** (Android และ iOS) ที่ใช้กล้องธรรมดาถ่ายภาพต้นไม้ พร้อม Photogrammetry บน Cloud Backend เพื่อสร้าง Point Cloud สำหรับชุมชนที่ไม่มี LiDAR scanner

5. **ทดสอบความแม่นยำของระบบ** เทียบกับการวัดด้วยสายวัดจริง (Ground Truth) ในต้นไม้ตัวอย่าง 20 ต้น โดยมีเป้าหมาย DBH RMSE ≤ 5 cm และ Height RMSE ≤ 1 m

---

## ส่วนที่ 5: ขอบเขตของโครงการ (Scope)

### 5.1 In-Scope (เวอร์ชัน Prototype สำหรับ NSC)

| Component | รายละเอียด |
|---|---|
| **ML Pipeline** | 8 ขั้นตอน (Ground Classification → Tree Segmentation → Wood-Leaf Segmentation → QSM → Allometric Carbon) |
| **Species Coverage** | 5 ชนิด: สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง |
| **Input Format** | `.las`, `.laz`, `.ply` (Path A) + JPEG photos 30-50 ภาพ (Path B) |
| **Output** | JSON {DBH, Height, Volume, Biomass, Carbon, CO2eq} + 3D visualization |
| **Web Dashboard** | Responsive (mobile + desktop), 4 personas (Community, Industrial, Auditor, Admin) |
| **Mobile App** | Android (primary), iOS (secondary if Mac available) |
| **Marketplace** | Mock payment flow with Stripe Test Mode |
| **Anti-Fraud** | GPS hash + EXIF validation + server-side dedup (radius 1-2 ม.) |

### 5.2 Out-of-Scope (ไม่อยู่ในขอบเขต เฟสนี้)

- รองรับต้นไม้ทุกชนิดบนโลก (ขยาย Phase 4+)
- Drone-based scanning integration
- Blockchain-based ledger
- Real-time scanning (ใช้ async pipeline แทน)
- การชำระเงินจริง (ใช้ Test Mode)
- การส่งออกใบรับรองที่รับรองโดย TGO อย่างเป็นทางการ (เป็น Pilot — ไม่ใช่ Certified)

### 5.3 Constraints and Assumptions

**Constraints:**
- ทีมงาน 3 คน, ระยะเวลาพัฒนา ~12 สัปดาห์
- งบประมาณ Cloud GPU ≤ $30/เดือน
- ไม่มี iPhone Pro ที่มี LiDAR Sensor ในทีม

**Assumptions:**
- ความเร็วอินเทอร์เน็ตของ user ≥ 5 Mbps สำหรับ upload
- Android ที่ใช้ทดสอบ ≥ API 26 (Android 8.0)
- เข้าถึง Public LiDAR Dataset (NEON) ได้

---

## ส่วนที่ 6: วิธีดำเนินการ (Methodology)

### 6.1 สถาปัตยกรรมระบบ (System Architecture)

```
┌────────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐     │
│  │  Mobile (Flutter)│    │   Web (Next.js 14)            │    │
│  │  - Camera + GPS  │    │   - 3D Viewer (R3F)           │    │
│  │  - TFLite ID     │    │   - GIS Map (Leaflet)         │    │
│  └────────┬─────────┘    │   - Marketplace               │    │
└───────────┼──────────────┴──────────────┬───────────────────┘
            │                              │
            ▼ HTTPS                        ▼ HTTPS
┌────────────────────────────────────────────────────────────────┐
│                       API GATEWAY                              │
│  FastAPI Service (Railway) — Auth, Job Orchestration           │
└────────────┬──────────────────────────────┬───────────────────┘
             ▼                              ▼
┌────────────────────────────┐    ┌──────────────────────────┐
│ Supabase                   │    │ Job Queue                 │
│ - PostgreSQL + PostGIS     │    │           │                │
│ - Storage (LAS/PLY/JPG)    │    │           ▼                │
│ - Auth                     │    │ RunPod Serverless GPU     │
└────────────────────────────┘    │ ML Pipeline (PyTorch)     │
                                  │ Photogrammetry (COLMAP)   │
                                  └──────────────────────────┘
```

### 6.2 ML Pipeline (8 ขั้นตอน)

**ขั้นตอนที่ 1: Ground Classification** ใช้ Cloth Simulation Filter (CSF) algorithm [12] ผ่านไลบรารี PDAL เพื่อแยกจุดพื้นดินออกจากจุดอื่น ๆ

**ขั้นตอนที่ 2: Height Normalization** สร้าง Digital Terrain Model (DTM) จากจุดพื้นดิน แล้วลบความสูง absolute Z ออก เพื่อให้ระบบรองรับต้นไม้ที่อยู่บนภูมิประเทศต่างกัน

**ขั้นตอนที่ 3: Canopy Height Model (CHM)** สร้างด้วย Pit-free Algorithm [13] เพื่อหลีกเลี่ยง "หลุม" จากการที่ LiDAR ทะลุผ่านใบ

**ขั้นตอนที่ 4: Individual Tree Detection (ITD)** ใช้ Watershed Segmentation บน CHM เพื่อแยกต้นไม้แต่ละต้น (ตามแนวทางของ `lidR` package [10])

**ขั้นตอนที่ 5: Wood-Leaf Semantic Segmentation** ⭐ Core Deep Tech — ใช้ PointNet++ [8] ที่ผ่านการ Fine-tune บน NEON Forest LiDAR Dataset เพื่อจำแนกแต่ละจุดในต้นไม้ว่าเป็น "ลำต้น/กิ่ง" (Wood) หรือ "ใบ" (Leaf) เป้าหมายความแม่นยำ IoU ≥ 0.70

**ขั้นตอนที่ 6: Quantitative Structure Model (QSM)** ทำ Cylinder Fitting [11] กับจุด Wood ที่ผ่านการแยกในขั้นตอนที่ 5 เพื่อคำนวณปริมาตรไม้ (m³)

**ขั้นตอนที่ 7: Species Classification** ใช้ ResNet-50 ที่ผ่านการ Transfer Learning จาก ImageNet เพื่อจำแนกชนิดต้นไม้จากภาพ RGB ของเปลือก/ใบ (ทำงานบน Mobile แบบ on-device ด้วย TFLite)

**ขั้นตอนที่ 8: Allometric Carbon Calculation** แปลงปริมาตร + ชนิด เป็น Biomass และ Carbon โดยใช้สมการ AGB = a × DBH^b × H^c ตามมาตรฐาน TGO Forestry Sector Guideline 2017 [14] พร้อมเพิ่มสัดส่วน Belowground Biomass (BGB = AGB × 0.25) และ Carbon Fraction = 0.47 ตามมาตรฐาน IPCC [15]

### 6.3 Dual-Input Architecture

ระบบรองรับ Input 2 ทาง โดยทั้งคู่ถูกแปลงเป็น Point Cloud (`.ply`) ก่อนเข้า ML Pipeline เดียวกัน:

**Path A: LAS Upload (สำหรับ Auditor/Researcher)**
- ผู้ใช้ upload ไฟล์ `.las/.laz` ที่ได้จาก TLS, Drone LiDAR, หรือ Public Dataset
- Backend ส่งไป Job Queue → GPU Worker ประมวลผลโดยตรง

**Path B: Photogrammetry (สำหรับ Community/เกษตรกร)**
- ผู้ใช้ถ่ายภาพรอบต้นไม้ 30-50 รูป ด้วยกล้องสมาร์ทโฟนทั่วไป + GPS
- Backend ส่งภาพไป Photogrammetry Worker ที่รัน COLMAP (Structure from Motion) [16] + OpenMVS (Multi-View Stereo) [17] เพื่อสร้าง `.ply`
- จากนั้น Job ถูก chain ต่อไปยัง ML Pipeline เดียวกัน

แนวทาง Photogrammetry นี้ผ่านการพิสูจน์ในงานวิจัยว่ามีความแม่นยำ DBH ในระดับ ±5-10% ซึ่งเพียงพอสำหรับ Carbon Inventory ในระดับ Voluntary Market [18]

### 6.4 เทคโนโลยีที่ใช้ (Technology Stack)

| Layer | Technology | Rationale |
|---|---|---|
| **Web Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Three.js (React Three Fiber), Leaflet | Modern stack, SEO-ready, accessible components |
| **Mobile** | Flutter 3.x, Riverpod, TFLite | Cross-platform Android+iOS, superior camera performance |
| **Backend API** | FastAPI (Python 3.11), Pydantic v2, SQLAlchemy async, GeoAlchemy2 | Native async, auto-Swagger docs, Python ecosystem |
| **Database** | PostgreSQL 16 + PostGIS 3.4 (Supabase) | Spatial queries critical for GIS features |
| **AI/ML** | PyTorch 2.3, PointNet++, Open3D 0.18, laspy, PDAL, COLMAP, OpenMVS | Industry-standard libraries |
| **Job Queue** | Supabase Queues / Redis | Simple, integrated |
| **Cloud GPU** | RunPod Serverless (A10G/RTX 4090) | Pay-per-second, scale-to-zero, ~$0.39/hr |
| **Deployment** | Vercel (Web), Railway (API), Supabase (DB) | Free/cheap tiers, easy deploy |
| **DevOps** | pnpm + Turborepo (monorepo), Docker, GitHub Actions | Fast, modern |

### 6.5 Anti-Fraud Mechanism

เพื่อให้ระบบมีความน่าเชื่อถือเทียบเท่ามาตรฐาน T-VER ระบบจึงมีกลไกป้องกันการนับซ้ำ/โกง 4 ชั้น:

1. **GPS Precision Lock** — บันทึก GPS ระดับทศนิยม 6 ตำแหน่ง (ความแม่นยำ ~0.1 ม.)
2. **EXIF Metadata Validation** — ตรวจสอบ timestamp ของรูปถ่ายว่าอยู่ในช่วงเวลาที่ user ส่ง (ไม่เกิน 24 ชม.)
3. **Camera-Only Capture** — Mobile App ไม่อนุญาตให้ upload จาก gallery (เฉพาะกล้อง real-time)
4. **Server-side Deduplication** — ถ้าพบ scan ในรัศมี 1-2 ม. จากจุดเดิม → ปฏิเสธหรือ flag for review

### 6.6 Evaluation Plan

| Metric | Target | Method |
|---|---|---|
| Wood-Leaf IoU (validation set) | ≥ 0.70 | เทียบกับ labeled NEON data |
| DBH RMSE (ground truth) | ≤ 5 cm | เทียบกับสายวัดจริง 20 ต้น |
| Height RMSE | ≤ 1 m | เทียบกับ clinometer 20 ต้น |
| Species classification Top-1 accuracy | ≥ 85% | เทียบกับ labeled validation set |
| End-to-end pipeline time | ≤ 10 นาที/แปลง | Benchmark บน RunPod A10G |

---

## ส่วนที่ 7: แผนการดำเนินงาน (Timeline & Milestones)

| Phase | ระยะเวลา | Output หลัก | Deliverables |
|---|---|---|---|
| **0: Proposal** | 20-29 พ.ค. 2569 | ข้อเสนอโครงการ | เอกสาร Proposal + ลายเซ็นที่ปรึกษา + อัปโหลด SIMs |
| **1: Foundation** | 30 พ.ค. – 30 มิ.ย. 2569 | Infrastructure + ML pipeline (non-AI) | Repo setup, Auth, ML pipeline ขั้น 1-4 |
| **2: Core AI** | 1-14 ก.ค. 2569 | PointNet++ trained + Full pipeline | Wood-Leaf model + Web Dashboard +3D Viewer |
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

## ส่วนที่ 8: ผลที่คาดว่าจะได้รับ (Expected Outcomes)

### 8.1 ผลผลิตเชิงเทคนิค (Technical Deliverables)

1. **ระบบประเมินคาร์บอนต้นไม้แบบอัตโนมัติ** ที่บรรลุเป้าหมายความแม่นยำ DBH RMSE ≤ 5 cm และ Wood-Leaf IoU ≥ 0.70
2. **เวลาประมวลผล** < 10 นาที/แปลง (ไม่รวม upload time)
3. **Web Dashboard** ใช้งานได้จริงผ่าน https://carbonscan-ai.vercel.app
4. **Mobile App** (Android APK) ดาวน์โหลดได้จาก GitHub Releases
5. **Trained Models** เผยแพร่บน Hugging Face Hub แบบ Open Source
6. **Source Code** เปิดเผยบน GitHub แบบ MIT License (หลังการแข่งขัน)

### 8.2 ผลกระทบเชิงสังคม (Social Impact)

ใช้กรอบ Triple Helix Model + Academic:

**1. เกษตรกร / ชุมชนผู้ปลูกต้นไม้:**
- เปลี่ยนต้นไม้ที่ปลูกเป็นรายได้ผ่านการขาย Carbon Credit
- ลดต้นทุนเข้าระบบจาก ~100,000 บาท → 0 บาท (ลด 100 เท่า)
- เข้าถึงระบบเศรษฐกิจสีเขียวที่เคยเป็นเอกสิทธิ์ของบริษัทใหญ่

**2. โรงงานอุตสาหกรรม / SMEs:**
- มีตัวกลาง B2B ที่โปร่งใส (เห็น GPS หมุดของต้นไม้ทุกต้นที่สนับสนุน)
- หลีกเลี่ยงข้อครหา Greenwashing
- พร้อมรับมือมาตรการ CBAM ของ EU
- สร้าง ESG Report ที่ Verifiable ระดับ 3D

**3. TGO / Carbon Auditors (หน่วยงานรับรอง):**
- ลดเวลาลงพื้นที่จริงจากหลายสัปดาห์ → ชั่วโมง
- เพิ่ม capacity ในการ verify โครงการคาร์บอนเครดิต
- ตรวจสอบความถูกต้องของข้อมูลย้อนหลังได้จากไฟล์ 3D Point Cloud

**4. ภาคการศึกษา / วิจัย:**
- Open Source Dataset และ Trained Model สำหรับ research community
- ลด barrier ในการทำงานวิจัย Forest Inventory ในไทย
- โอกาสตีพิมพ์ paper ระดับนานาชาติ (ICCV/CVPR Workshop, Remote Sensing)

**5. ประเทศไทย (National-level):**
- สนับสนุนเป้าหมาย Carbon Neutrality 2050 ของรัฐบาล
- เพิ่มขีดความสามารถส่งออกสินค้าเข้าตลาด EU (CBAM compliance)
- พัฒนา Climate FinTech ecosystem ของไทย

### 8.3 ผลกระทบเชิงวิชาการ (Academic Impact)

โครงการนี้เป็นการประยุกต์ใช้ Computer Science กับ Forestry Science แบบ Multi-disciplinary อย่างชัดเจน:
- การ Port อัลกอริทึมจาก R (lidR) เป็น Python — เป็นประโยชน์ต่อ Python community
- การปรับ PointNet++ ให้ทำงานกับข้อมูลป่าไม้ของไทย — เป็น novel contribution
- การสร้าง Calibration Dataset Photogrammetry-vs-Ground Truth สำหรับไม้เศรษฐกิจไทย — เป็น open dataset แรกของประเภทนี้ในไทย

### 8.4 ผลสำเร็จที่ใช้วัด (Success Metrics)

| Metric | Baseline (วิธีดั้งเดิม) | Target (CarbonScan AI) | Improvement |
|---|---|---|---|
| ต้นทุน Auditing / แปลง 50 ไร่ | ~150,000 บาท | ~1,500 บาท (Cloud cost) | **100×** |
| เวลา / แปลง | 7-14 วัน | 30 นาที | **400×** |
| Reach (เกษตรกร) | ฟาร์มขนาดใหญ่เท่านั้น | ทุกระดับ (มี smartphone) | Unlimited |
| Transparency (โรงงาน) | Excel report | 3D Visual + GPS | Verifiable |

---

## ส่วนที่ 9: ข้อจำกัดและแนวทางแก้ไข (Risks & Mitigations)

### 9.1 Technical Risks

| ความเสี่ยง | ความน่าจะเป็น | ผลกระทบ | แนวทางแก้ |
|---|---|---|---|
| Photogrammetry แม่นยำต่ำกว่า LiDAR | กลาง | สูง | ทำ Calibration Experiment กับ Ground Truth 20 ต้น + รายงาน Error margin ใน UI |
| PointNet++ Train ไม่ทันก่อน 17 ก.ค. | กลาง | สูง | Fallback ใช้ TLSeparation (rule-based) [19] เป็น baseline + ระบุ DL เป็น "future enhancement" |
| Cloud GPU ค่าใช้จ่ายเกินงบ | ต่ำ | กลาง | ตั้ง budget cap $30/เดือน + ใช้ Colab/Kaggle ฟรีใน dev phase |
| Dataset LiDAR ไทยไม่มี | สูง | กลาง | ใช้ NEON (USA) เทรนก่อน + Transfer learning หรือ Synthetic data |
| iOS build ไม่ได้ (ไม่มี Mac) | สูง | ต่ำ | ใช้ Codemagic / Bitrise cloud macOS build + Focus Android เป็นหลัก |

### 9.2 Operational Risks

| ความเสี่ยง | ความน่าจะเป็น | ผลกระทบ | แนวทางแก้ |
|---|---|---|---|
| ลายเซ็นที่ปรึกษา/คณบดีไม่ทัน 29 พ.ค. | สูง | ฆาตกร (ส่งไม่ได้) | เริ่มเดินเอกสารตั้งแต่ 25 พ.ค., เตรียม PDF Preview ส่งล่วงหน้า |
| ทีมงานคนใดคนหนึ่งติดสอบ/ป่วย | สูง | กลาง | งาน Critical Path ให้ทุกคนช่วยร่าง, มี backup ทุก Role |
| Internet วันแข่งไม่เสถียร | ต่ำ | สูง | เตรียม Offline Demo (pre-computed dataset + downloaded videos) |

### 9.3 Q&A Defense (เผื่อกรรมการถาม)

**Q1: Photogrammetry แม่นยำเท่า LiDAR ไหม?**
A: ไม่เท่า — แต่อยู่ในระดับ ±5-10 cm ซึ่งเพียงพอสำหรับ Voluntary Carbon Market (T-VER) ตามที่งานวิจัย Liang et al. 2019 [18] และ Mokros et al. 2021 [20] ยืนยันไว้ ทั้งนี้ระบบมี Calibration กับ Ground Truth + รายงาน Confidence Score ทุก measurement

**Q2: จะรู้ได้ไงว่าไม่นับซ้ำ?**
A: ระบบมีกลไก Anti-Fraud 4 ชั้น (ดู section 6.5) — GPS ทศนิยม 6 ตำแหน่ง + EXIF validation + Camera-only + Server-side dedup

**Q3: ใช้ GPU อะไรเทรน Model?**
A: Training บน Google Colab Pro+ (NVIDIA A100 40GB), Production Inference บน RunPod Serverless (A10G 24GB) แบบ pay-per-second เพื่อ Scale-to-zero

**Q4: ค่าใช้จ่าย Run server เดือนละเท่าไหร่?**
A: ใน Prototype scale (100 jobs/เดือน) ~$11.50/เดือน (~400 บาท) ใน production scale มี Business Model B2B Subscription cover ค่าใช้จ่าย

**Q5: ทำไมไม่ใช้ R lidR ตรง ๆ?**
A: เพราะ Production deployment ต้องการ Python ecosystem (FastAPI, PyTorch, Deployment via Docker) — เราจึง Port อัลกอริทึมจาก R เป็น Python ซึ่งเป็นประโยชน์ต่อชุมชน Python ทั่วโลกด้วย

---

## ส่วนที่ 10: งบประมาณ (Budget)

> **TBD:** ตามมาตรฐาน NSC ~3,000-5,000 บาท/โครงการ

### 10.1 รายการที่ขอสนับสนุนจาก NSC

| รายการ | จำนวน | ราคา/หน่วย | รวม (บาท) |
|---|---|---|---|
| Cloud GPU (RunPod) Phase 2-3 | 3 เดือน | 400 | 1,200 |
| Cloud GPU Training (Colab Pro+) | 2 เดือน | 1,700 | 3,400 |
| Cloud Storage (Supabase Pro) | 3 เดือน | 850 | 2,550 |
| Domain name (carbonscan-ai.com) | 1 ปี | 350 | 350 |
| ค่าเดินทาง (ลงพื้นที่เก็บ Ground Truth) | — | — | 2,000 |
| ค่าพิมพ์ Proposal + Final Report | 5 ชุด | 200 | 1,000 |
| ค่าจัดทำ Poster A1 + นามบัตร (รอบชิง) | — | — | 1,500 |
| **รวม** | | | **12,000** |

⚠️ ปรับยอดตามที่ NSC อนุมัติได้จริง — รายการที่เกินงบ ทีมจะ self-fund

### 10.2 รายการที่ทีมรับผิดชอบเอง

- Hardware (Notebook ของทีม, Android phone)
- Software License (ทั้งหมดเป็น Open Source / Free Tier)
- ค่าอินเทอร์เน็ต / ค่าไฟ
- เวลาในการพัฒนา

---

## ส่วนที่ 11: เอกสารอ้างอิง (References)

ดูรายการเต็มใน [references.md](references.md) — ภาพรวม 30+ citations ครอบคลุม:

1. UNFCCC Paris Agreement (2015)
2. EU CBAM Regulation 2023/956
3. Thailand NDC submission (COP26, 2021)
4. กรมป่าไม้ — รายงานสถานการณ์ป่าไม้
5. TGO — T-VER Methodology Documents
6. Brown 1997 — Biomass measurement primer
7. World Resources Institute (WRI) — Greenhouse Gas Protocol
8. Qi et al. 2017 — PointNet++ (NeurIPS)
9. Thomas et al. 2019 — KPConv (ICCV)
10. Roussel et al. 2020 — lidR package (Remote Sensing of Environment)
11. Raumonen et al. 2013 — TreeQSM (Remote Sensing)
12. Zhang et al. 2016 — CSF Ground Filter (Remote Sensing)
13. Khosravipour et al. 2014 — Pit-free CHM (PE&RS)
14. TGO 2017 — Forestry Sector Greenhouse Gas Calculation Guideline
15. IPCC 2006 — Guidelines for National GHG Inventories Vol. 4 (AFOLU)
16. Schönberger & Frahm 2016 — COLMAP (CVPR)
17. Cernea — OpenMVS library
18. Liang et al. 2019 — Forest in situ observations via UAV (Forest Ecosystems)
19. Vicari et al. 2019 — TLSeparation (Methods in Ecology and Evolution)
20. Mokros et al. 2021 — Low-cost mobile mapping (Int. J. Applied Earth Obs.)

---

## ส่วนที่ 12: ภาคผนวก (Appendices)

### Appendix A: CV ทีมงาน
- A.1 [User] — ปริญญาตรี ปี X, [คณะ มหาวิทยาลัย], ทักษะ: Python, PyTorch, Flutter, FastAPI
- A.2 [Person A] — ปริญญาตรี ปี X, ทักษะ: Next.js, TypeScript, React
- A.3 [Person B] — ปริญญาตรี ปี X, ทักษะ: Figma, Adobe Creative Suite

### Appendix B: CV ที่ปรึกษาโครงการ
- [ชื่อ-สกุล], [ตำแหน่งวิชาการ], [คณะ มหาวิทยาลัย], [ความเชี่ยวชาญ]

### Appendix C: Architecture Diagram (Full Size)
- [แทรกรูปคุณภาพสูง — Person B จัดทำ]

### Appendix D: UI/UX Mockups
- [Screenshots สำคัญ 5-6 ภาพ — Person B จัดทำ]

### Appendix E: Letter of Recommendation (ถ้ามี)
- [ใส่จดหมายรับรองจากที่ปรึกษา / นักวิจัยที่เกี่ยวข้อง]

---

## 📋 Checklist ก่อนส่ง (29 พ.ค.)

### Content
- [ ] บทคัดย่อ 200-300 คำ ครอบคลุม Problem + Solution + Impact
- [ ] หลักการและเหตุผลมี citations
- [ ] วัตถุประสงค์ measurable
- [ ] Scope ชัด — In-scope และ Out-of-scope
- [ ] Methodology ครบ 8 ขั้นตอน + Tech Stack ละเอียด
- [ ] Timeline + Gantt
- [ ] Risk & Mitigation 10+ ข้อ
- [ ] References ≥ 20 citations

### Format
- [ ] Cover page (Person B)
- [ ] Font Sarabun 14pt body, 16pt heading
- [ ] Margin 2.54 cm รอบด้าน
- [ ] Page numbers
- [ ] Header + Footer
- [ ] PDF format
- [ ] ไม่มี typo

### Signatures
- [ ] ที่ปรึกษาโครงการ
- [ ] หัวหน้าสถาบัน (คณบดี/ผอ.)

### Submission
- [ ] ลงทะเบียน SIMs ทุกคนในทีม
- [ ] อัปโหลดล่วงหน้า 24 ชม.
- [ ] Verify status = "Submitted"
- [ ] Save confirmation email
