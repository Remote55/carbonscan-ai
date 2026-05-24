# บท 02 — แนวคิดพื้นฐานที่ต้องรู้ก่อน

> 🎯 **เป้าหมายของบท:** ผู้อ่านจะอธิบายได้ว่า LiDAR, Point Cloud, GIS, Carbon Credit, TGO, CBAM แต่ละอันคืออะไร — เป็นพื้นฐานก่อนเข้าบทเทคนิค
> 📚 **ความรู้พื้นฐานที่ต้องมีก่อน:** อ่าน [บท 01](01-overview.md) แล้ว
> ⏱️ **เวลาในการอ่าน:** ~30 นาที (มีศัพท์เยอะ)

---

## 1. LiDAR — เครื่องสแกน 3D ด้วยแสงเลเซอร์

### 1.1 LiDAR คืออะไร

**LiDAR** = **Li**ght **D**etection **A**nd **R**anging

หลักการทำงานเรียบง่าย:
```
1. ยิงแสง laser pulse ออกไปยังวัตถุ
2. วัดเวลาที่แสงสะท้อนกลับ
3. คำนวณระยะ: distance = (speed_of_light × time) / 2
4. ทำซ้ำหลายล้านครั้งต่อวินาที → ได้จุด 3D หลายล้านจุด
```

**Analogy:**
- เหมือนกับ **sonar** ของเรือดำน้ำ (ส่งคลื่นเสียง วัดเวลาสะท้อน)
- แต่ใช้ **แสง** แทน → เร็วกว่า + ความแม่นยำสูงกว่า
- หรือเหมือน **เครื่องวัดระยะของกล้องมือถือ** (iPhone Pro มี LiDAR ด้านหลัง) — แค่ scale ใหญ่กว่า

### 1.2 ประเภทของ LiDAR (สำคัญ)

| ประเภท | ตั้งที่ไหน | คลุมพื้นที่ | ราคา | ใช้ตอนไหน |
|---|---|---|---|---|
| **TLS** (Terrestrial Laser Scanning) | ตั้งกับขาตั้งบนพื้น | 0.1-1 ไร่/scan | 500K-2M | งานวิจัย, ตรวจสอบละเอียด |
| **MLS** (Mobile Laser Scanning) | ติดรถ/รถเข็น | 1-10 ไร่/วัน | 1M-5M | mapping ถนน, ป่าใหญ่ |
| **ALS** (Airborne Laser Scanning) | ติดเครื่องบินใหญ่ | 100-10K ไร่/วัน | 5M-20M | mapping ระดับจังหวัด |
| **UAV LiDAR** (Drone) | ติด drone | 10-100 ไร่/flight | 1M-3M | survey เร็ว, ป่าขนาดกลาง |
| **iPhone LiDAR** | ในตัว iPhone Pro | ระยะ < 5 เมตร | 30K+ (มือถือ) | scan วัตถุเล็ก, AR |

> 💡 **โครงการเราโฟกัสที่:** TLS + UAV LiDAR (สำหรับ professional auditor) + Photogrammetry (สำหรับ smallholder ที่ไม่มี LiDAR)

### 1.3 LiDAR ดีกว่ากล้องธรรมดายังไง

| สิ่งที่ต้องการ | กล้องธรรมดา | LiDAR |
|---|---|---|
| ความแม่นยำ XYZ | ปานกลาง (ต้องคำนวณจากภาพ) | **สูงมาก** (~ 1 cm) |
| กลางคืน/ไฟต่ำ | ใช้ไม่ได้ | **ใช้ได้** (เลเซอร์ active) |
| เห็นใต้ canopy | เห็นเฉพาะยอด | **เห็นทั้ง trunk + ground** (penetration) |
| ราคา | ถูก | แพง |
| สี (RGB) | ✅ มี | ❌ ไม่มี (ต้องใช้กล้องเสริม) |

> ⚠️ **ข้อจำกัด:** LiDAR ไม่มีสี — ดูได้แค่ "รูปทรง" ไม่ได้ "ดู" ว่าเป็นต้นอะไร นั่นเป็นเหตุผลที่เราต้องใช้ **กล้อง RGB** เสริมในขั้น species classification

---

## 2. Point Cloud — กลุ่มจุด 3 มิติ

### 2.1 Point Cloud คืออะไร

ผลลัพธ์ของ LiDAR คือ **Point Cloud** — กลุ่มของจุดในพื้นที่ 3 มิติ แต่ละจุดมี:

```
จุดที่ i = (x, y, z) + optional metadata
         = (12.5, 45.3, 2.8) + (intensity, classification, RGB, ...)
```

ป่า 1 ไร่ ที่ scan ละเอียด TLS → อาจมี **1-10 ล้านจุด**

### 2.2 รูปแบบไฟล์ (Format)

| Format | จุดเด่น | จุดด้อย | ใช้เมื่อไหร่ |
|---|---|---|---|
| **`.las`** | มาตรฐานอุตสาหกรรม, มี metadata เยอะ | ไฟล์ใหญ่ | LiDAR raw data |
| **`.laz`** | compressed `.las` (ลดขนาด ~80%) | ต้อง decompress ก่อนใช้ | จัดเก็บ/transfer |
| **`.ply`** | text-based, อ่านง่าย, มี RGB | metadata น้อย | photogrammetry, mesh |
| **`.xyz` / `.txt`** | text เปลือยๆ XYZ | metadata น้อย, ช้า | export ทดสอบ |
| **`.pcd`** | Open3D/PCL native | ไม่ standard | ML pipeline บางตัว |

> 💡 **โครงการเราอ่าน:** `.las` / `.laz` (LiDAR primary), `.ply` (photogrammetry output), `.txt` (test data จาก Belgium dataset)

### 2.3 Visualize Point Cloud

ดูบน:
- **CloudCompare** (free, desktop) — มาตรฐานวิจัย
- **MeshLab** (free, desktop)
- **Web:** Three.js + potree-core (ของเราใน Sprint 3+)
- **Mobile:** AR apps

ลองดู: เปิด `docs/proposal/figures/fig01_raw_point_cloud.png` — คือ point cloud synthetic 30×30 ม. ที่เรา generate

### 2.4 ทำไม Point Cloud ยาก

```
ปัญหาที่ AI ต้องจัดการ:
1. ขนาดใหญ่      — 10M points/ไร่ × ทั้งโครงการ = TB
2. ไม่มี structure — ต่างจาก image ที่เป็น grid (W×H)
3. ความหนาแน่นไม่สม่ำเสมอ — ใกล้ scanner หนา ไกล scanner บาง
4. มี noise        — แมลง, ฝุ่น, ใบไม้ที่ขยับ
5. occlusion      — กิ่งบังกัน เห็นไม่ทั่ว
```

นี่คือเหตุผลที่ Point Cloud ML ต่างจาก Image ML — เราใช้ library พิเศษ เช่น Open3D, PDAL, PyTorch Geometric

---

## 3. Photogrammetry — สร้าง Point Cloud จากภาพถ่าย

### 3.1 หลักการ

ใช้ **กล้องธรรมดา** ถ่ายภาพวัตถุจากหลายมุม → AI สร้าง 3D point cloud ขึ้นมาจากเรขาคณิต

```
30-50 รูปจากมือถือ
     ↓
[Structure-from-Motion (SfM)]   ← COLMAP
     ↓
Sparse point cloud + camera poses
     ↓
[Multi-View Stereo (MVS)]       ← OpenMVS
     ↓
Dense point cloud (.ply)         ← เหมือน LiDAR output (แต่หยาบกว่า)
```

### 3.2 Photogrammetry vs LiDAR

| Aspect | Photogrammetry | LiDAR |
|---|---|---|
| **อุปกรณ์** | กล้อง (มือถือก็ได้) | LiDAR scanner |
| **ราคา** | ฟรี (มือถือ) - หมื่น | แสน - ล้าน |
| **ความแม่นยำ** | ปานกลาง (~ 2-5 cm) | สูง (~ 1 cm) |
| **เวลา** | scan 5 นาที + cloud 5 นาที = 10 นาที | scan 1-5 นาที |
| **มี RGB** | ✅ มาพร้อม | ❌ ไม่มี |
| **เห็นใต้ canopy** | ❌ ไม่ดี (ใบบัง) | ✅ ดี (penetrate) |
| **กลางคืน** | ❌ ใช้ไม่ได้ | ✅ ใช้ได้ |
| **Texture/สี** | ✅ ดี | ❌ ต้องใช้กล้องเสริม |

### 3.3 ทำไมโครงการเราเลือกใช้ Photogrammetry เป็น secondary path

- 🏝️ **Smallholder accessibility** — เกษตรกร 1 ไร่ ไม่ซื้อ LiDAR แน่นอน
- 📱 **Mobile-native** — ภาพ 30 รูป + app บน Android ก็ใช้ได้แล้ว
- 🌳 **เหมาะกับต้นไม้เดี่ยว** — scan ต้นเดียวรอบทิศ ไม่ต้องคลุมทั้งแปลง

> ⚠️ **อย่างไรก็ตาม** photogrammetry **ไม่เหมาะ** กับการ scan ป่าใหญ่ — เพราะ:
> - 1 ต้น = 30-50 รูป
> - 100 ต้น = 3,000-5,000 รูป
> - คนเดินถ่ายไม่ไหว = **นี่คือสิ่งที่อาจารย์ feedback ตั้งแต่ต้น**
>
> ดังนั้นใน v2 เราเปลี่ยน positioning: **photogrammetry = optional fallback สำหรับ < 1 ไร่ เท่านั้น**

---

## 4. GIS — Geographic Information System

### 4.1 GIS คืออะไร

ระบบจัดเก็บ + ค้นหา + วิเคราะห์ข้อมูลที่มี **พิกัดทางภูมิศาสตร์** (latitude, longitude)

### 4.2 ส่วนประกอบ

| ส่วน | หน้าที่ | ตัวอย่าง |
|---|---|---|
| **Spatial database** | เก็บ geometry + attributes | PostgreSQL + PostGIS |
| **Web mapping library** | แสดงแผนที่บนเว็บ | Leaflet, Mapbox |
| **Tile server** | ส่ง map tiles ตามที่ user pan/zoom | OpenStreetMap |
| **Spatial query** | "หาต้นไม้ใน radius 100m ของจุดนี้" | ST_DWithin, ST_Within |

### 4.3 ทำไม CarbonScan AI ต้องมี GIS

- ทุก **ต้นไม้** มีพิกัด GPS (lat, lon) → เก็บใน `trees.location` (PostGIS POINT)
- ทุก **แปลงป่า** มี polygon ขอบเขต → `plots.geometry` (PostGIS POLYGON)
- **Anti-fraud:** ก่อน insert ต้นใหม่ → query "มีต้นในรัศมี 1-2m ไหม?" → ถ้ามี = duplicate
- **Marketplace UI:** โรงงานเห็น map ของแปลงที่จะซื้อ
- **Reporting:** สรุปคาร์บอนตาม region / province

> 💡 **PostGIS** = extension ของ PostgreSQL ที่เพิ่ม spatial column types + index + functions — เป็นมาตรฐานทองในวงการ GIS

---

## 5. Carbon Credit + ตลาดคาร์บอน

### 5.1 Carbon Credit คืออะไร

> **1 carbon credit = 1 ตัน CO₂eq ที่ถูก "ลด" หรือ "กักเก็บ" ออกจากชั้นบรรยากาศ**

ใช้ใน:
- **Offset** — บริษัทที่ปล่อย CO₂ ซื้อเครดิตมาชดเชย
- **Compliance** — กฎหมาย (เช่น EU CBAM) บังคับให้ชดเชย
- **Voluntary** — บริษัทที่อยากแสดงความรับผิดชอบ

### 5.2 แหล่ง Carbon Credit

| ประเภท | ตัวอย่าง | ลักษณะ |
|---|---|---|
| **Forestry (ป่าไม้)** | ปลูกป่าใหม่, อนุรักษ์ป่าเดิม | ราคาสูง, verify ยาก ← **โครงการเราโฟกัสตรงนี้** |
| **Renewable energy** | solar, wind | ราคาต่ำ, verify ง่าย |
| **Methane capture** | ดักจับ methane จาก landfill | ราคาปานกลาง |
| **Direct Air Capture (DAC)** | เครื่องดูดอากาศ + เก็บใต้ดิน | ราคาสูงมาก, technology ใหม่ |

### 5.3 ราคาคาร์บอนเครดิต (2026)

```
🌎 ตลาดอินเตอร์ (Voluntary): $5-50 / ตัน CO₂eq
🇪🇺 EU ETS (Compliance):       $80-150 / ตัน CO₂eq
🇹🇭 ไทย (T-VER):                ฿200-800 / ตัน CO₂eq (~$6-22)
```

> 💡 **โอกาส:** ถ้าระบบเรา certify ให้ Thai forestry credits ได้ขายในตลาด EU → ราคาขึ้น **5-10×**

### 5.4 หลักเกณฑ์การออก credit (สำคัญสำหรับ Proposal)

ทุก credit ต้องผ่าน **4 เกณฑ์** (industry standard):

| เกณฑ์ | ความหมาย | กลไกของระบบเรา |
|---|---|---|
| **Additionality** | คาร์บอนที่ลด/เก็บ ต้องเป็น "ของใหม่" ไม่ใช่อยู่แล้ว | Multi-temporal tracking (Carbon Delta ปีต่อปี) |
| **Permanence** | ต้องเก็บไว้นานพอ (≥ 100 ปี ใน some standards) | Audit log + re-scan ทุกปี |
| **Verifiability** | third-party ตรวจสอบได้ | 3D point cloud + GIS + Certificate PDF |
| **Avoid leakage** | ลดป่าที่นี่ ห้ามไปทำลายป่าที่อื่นเพื่อชดเชย | Plot-level tracking + GPS dedup |

---

## 6. มาตรฐานและองค์กรที่ต้องรู้

### 6.1 TGO (อบก. — Thailand Greenhouse Gas Management Organization)

**ภาษาไทย:** องค์การบริหารจัดการก๊าซเรือนกระจก (องค์การมหาชน)

**บทบาท:**
- ออกมาตรฐาน **T-VER** (Thailand Voluntary Emission Reduction)
- รับรอง projects ที่ขายคาร์บอนเครดิตในไทย
- ดูแล species-specific allometric equations สำหรับไม้ไทย (เผยแพร่ใน TGO 2017 Forestry Guideline)

**เกี่ยวกับเรายังไง:**
- ✅ ระบบเราอ้างอิงสูตรของ TGO 2017 ใน `services/ml/data/species_db.csv`
- ✅ ตั้งเป้าได้ TGO certification ใน Phase post-NSC (2027+)

### 6.2 IPCC (Intergovernmental Panel on Climate Change)

**บทบาท:**
- ออกค่า default ระดับโลก (เช่น carbon fraction = 0.47, root:shoot ratio = 0.24 สำหรับ tropical)
- เผยแพร่ Vol. 4 AFOLU (Agriculture, Forestry and Other Land Uses) guidelines

**เกี่ยวกับเรายังไง:**
- ใช้ค่า default ของ IPCC 2006 ใน `services/ml/pipeline/allometric.py`

### 6.3 CBAM (Carbon Border Adjustment Mechanism)

**ของ:** สหภาพยุโรป (EU)

**ผลกระทบ:**
- สินค้าที่ส่งออก EU (เช่น เหล็ก, ปูนซีเมนต์, alumini, electricity, hydrogen, fertilizer) ตั้งแต่ 2026
- บริษัทต้องรายงาน + ชดเชยคาร์บอนที่ใช้ผลิต
- ราคาเทียบเท่า EU ETS (~$80-150/ตัน)

**เกี่ยวกับเรายังไง:**
- โรงงานไทยที่ส่งออก EU **ต้องการ** คาร์บอนเครดิตที่ verify ได้ระดับ EU
- เป็นตลาดเป้าหมายของ marketplace ของเรา

### 6.4 มาตรฐาน Carbon ระดับโลก

| มาตรฐาน | ของ | ใช้กับ |
|---|---|---|
| **Verra (VCS)** | NGO | Voluntary market ใหญ่ที่สุด |
| **Gold Standard** | NGO (Swiss) | Voluntary, มี social criteria |
| **CDM** | UN | Compliance (Kyoto Protocol) |
| **ART TREES** | NGO | National-scale REDD+ |
| **T-VER** | TGO | Thailand domestic |
| **ICVCM Core Carbon Principles** | NGO | Quality benchmark |

---

## 7. คำย่อที่ต้องรู้

| ย่อ | เต็ม | ความหมาย |
|---|---|---|
| **AGB** | Above-Ground Biomass | ชีวมวลเหนือดิน (กก. หรือ ตัน) |
| **BGB** | Below-Ground Biomass | ชีวมวลใต้ดิน (ราก) |
| **DBH** | Diameter at Breast Height | ขนาดเส้นผ่านศูนย์กลางลำต้นที่ระดับอก (1.3 ม.) |
| **CHM** | Canopy Height Model | แผนที่ความสูงเรือนยอดเป็น raster |
| **DTM** | Digital Terrain Model | แผนที่ความสูงพื้นดินเป็น raster |
| **DSM** | Digital Surface Model | DTM + canopy บนสุด |
| **ITD** | Individual Tree Detection | การแยกต้นไม้ทีละต้น |
| **QSM** | Quantitative Structure Model | โมเดลทรงกระบอกของลำต้น+กิ่ง |
| **SfM** | Structure from Motion | photogrammetry algorithm |
| **MVS** | Multi-View Stereo | photogrammetry dense reconstruction |
| **CSF** | Cloth Simulation Filter | algorithm แยก ground points |
| **TLS** | Terrestrial Laser Scanning | LiDAR ตั้งพื้น |
| **ALS** | Airborne Laser Scanning | LiDAR บนเครื่องบิน |
| **MLS** | Mobile Laser Scanning | LiDAR ติดรถ |
| **UAV** | Unmanned Aerial Vehicle | Drone |
| **EXIF** | Exchangeable Image File Format | metadata ของรูปภาพ (GPS, time, camera) |
| **GIS** | Geographic Information System | ระบบจัดการข้อมูลภูมิศาสตร์ |
| **GPS** | Global Positioning System | ระบบบอกพิกัดผ่านดาวเทียม |
| **PostGIS** | PostgreSQL spatial extension | spatial database |
| **REDD+** | Reducing Emissions from Deforestation and Forest Degradation | UN framework |
| **MRV** | Monitoring, Reporting, Verification | กระบวนการตรวจสอบคาร์บอน |

---

## 8. คำที่ใช้บ่อยใน Pipeline

| คำ | ความหมาย |
|---|---|
| **Ground point** | จุดที่เป็นพื้นดิน (ไม่ใช่ใบ/ลำต้น) |
| **Non-ground point** | จุดที่ไม่ใช่พื้นดิน (canopy, trunk, ...) |
| **Normalized Z** | ความสูงเหนือพื้น (subtract DTM แล้ว) |
| **Tree top** | จุดสูงสุดของต้นไม้ใน CHM |
| **Wood point** | จุดที่เป็นลำต้นหรือกิ่ง |
| **Leaf point** | จุดที่เป็นใบ |
| **Crown** | เรือนยอด/พุ่มใบของต้นไม้ |
| **Stem** | ลำต้น |
| **Form factor** | สัดส่วน V_actual / V_cylinder (~0.5 สำหรับต้นไม้ทั่วไป) |

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

> ตอบเองได้ทุกข้อ = พร้อมเข้าบท 03

1. **TLS, ALS, MLS, UAV LiDAR — ต่างกันยังไง? ใช้ต่างกันตอนไหน?**
   - hint: ตาราง 1.2

2. **Point Cloud ต่างจาก Image ยังไง ทำไม ML สำหรับ point cloud ต้องใช้ library พิเศษ?**
   - hint: 2.4

3. **Photogrammetry ดี/แย่กว่า LiDAR ยังไง ในด้าน accuracy, cost, conditions?**
   - hint: 3.2

4. **Carbon Credit 1 unit หมายถึงอะไร? ราคาในตลาด voluntary vs EU ETS ต่างกันยังไง?**
   - hint: 5.1, 5.3

5. **4 เกณฑ์ของ carbon credit ที่ดี (Additionality, Permanence, Verifiability, Avoid leakage) — ระบบเราจัดการแต่ละข้อยังไง?**
   - hint: 5.4

6. **TGO กับ IPCC — เป็นองค์กรอะไร เกี่ยวข้องกับเรายังไง?**
   - hint: 6.1, 6.2

7. **CBAM คืออะไร? ทำไมมีผลต่อตลาดคาร์บอนไทย?**
   - hint: 6.3

---

## 10. อ่านต่อ

- [บท 03 — สถาปัตยกรรมระบบ (4 layers)](03-architecture.md)
- [บท 12 — สูตรคาร์บอน (Allometric) ⭐](12-ml-step8-allometric.md) — ถ้าอยากเข้า "เนื้อ" สุดของระบบทันที

---

> 📝 **เขียนครั้งแรก:** 2026-05-24 | **แก้ไขล่าสุด:** 2026-05-24
