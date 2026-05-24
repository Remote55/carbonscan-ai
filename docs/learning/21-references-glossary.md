# บท 21 — References + Glossary (อ้างอิงและศัพท์)

> 🎯 **เป้าหมาย:** ที่รวม "ทุก paper, ทุก link, ทุกศัพท์" ของระบบ
> 📚 **พื้นฐาน:** (อ่านบทไหนก็มาเปิดที่นี่ได้)
> ⏱️ **เวลา:** Reference — เปิดดูเป็นระยะ

---

## 1. Academic Papers (เรียงตามปี)

### 1.1 ML Pipeline Algorithms

| Citation | Algorithm | บทที่อ้างถึง |
|---|---|---|
| **Ogawa et al. 1965** | Dipterocarp allometry | 12 |
| **Tsutsumi et al. 1983** | Thai monsoon forest allometry | 12 |
| **IPCC 2006** Vol 4 (AFOLU) | Default coefficients (C fraction, root:shoot) | 12 |
| **Yiping et al. 2010** | Bamboo allometry | 12 |
| **Raumonen et al. 2013** | TreeQSM | 10 |
| **Khosravipour et al. 2014** | Pit-free CHM | 7 |
| **Chave et al. 2014** | Pantropical biomass model | 12 |
| **Chiarucci et al. 2014** | Rubber plantation allometry | 12 |
| **Zhang et al. 2016** | Cloth Simulation Filter (CSF) | 5 |
| **He et al. 2016** | ResNet | 11 |
| **TGO 2017** | Thailand Forestry GHG Guideline | 12 |
| **Qi et al. 2017** | PointNet++ | 9 |
| **Vicari et al. 2019** | TLSeparation (wood-leaf rule-based) | 9 |
| **Roussel et al. 2020** | lidR R package | 8 |
| **Demol et al. 2021** | Destructive biomass validation | 13, 20 |

### 1.2 Detailed Citations

**Chave, J. et al. (2014).** Improved allometric models to estimate the aboveground biomass of tropical trees. *Global Change Biology*, 20(10), 3177-3190.
DOI: [10.1111/gcb.12629](https://doi.org/10.1111/gcb.12629)

**Demol, M. et al. (2021).** Estimating forest above-ground biomass with terrestrial laser scanning: current status and future directions. *Trees*, 35, 671-685.
DOI: [10.1007/s00468-020-02067-7](https://doi.org/10.1007/s00468-020-02067-7)
Dataset: [10.5281/zenodo.4557401](https://doi.org/10.5281/zenodo.4557401)

**He, K. et al. (2016).** Deep Residual Learning for Image Recognition. *CVPR 2016*.
arXiv: [1512.03385](https://arxiv.org/abs/1512.03385)

**IPCC. (2006).** 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Vol. 4 (AFOLU).
Link: [ipcc-nggip.iges.or.jp/public/2006gl/vol4.html](https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html)

**Khosravipour, A. et al. (2014).** Generating Pit-free Canopy Height Models from Airborne Lidar. *Photogrammetric Engineering & Remote Sensing*, 80(9), 863-872.

**Qi, C.R. et al. (2017).** PointNet++: Deep Hierarchical Feature Learning on Point Sets in a Metric Space. *NeurIPS 2017*.
arXiv: [1706.02413](https://arxiv.org/abs/1706.02413)

**Raumonen, P. et al. (2013).** Fast Automatic Precision Tree Models from Terrestrial Laser Scanner Data. *Remote Sensing*, 5(2), 491-520.
DOI: [10.3390/rs5020491](https://doi.org/10.3390/rs5020491)

**Roussel, J.-R. et al. (2020).** lidR: An R package for analysis of Airborne Laser Scanning (ALS) data. *Remote Sensing of Environment*, 251, 112061.
DOI: [10.1016/j.rse.2020.112061](https://doi.org/10.1016/j.rse.2020.112061)

**Zhang, W. et al. (2016).** An Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth Simulation. *Remote Sensing*, 8(6), 501.
DOI: [10.3390/rs8060501](https://doi.org/10.3390/rs8060501)

---

## 2. Standards + Organizations

### 2.1 Thai

- **TGO** — องค์การบริหารจัดการก๊าซเรือนกระจก
  - Website: https://www.tgo.or.th
  - T-VER standard: https://ghgreduction.tgo.or.th/en/tver-method
- **กรมป่าไม้** — Royal Forest Department
  - Website: https://www.forest.go.th
- **อบก. = TGO** (เหมือนกัน)

### 2.2 International

- **IPCC** — Intergovernmental Panel on Climate Change
  - https://www.ipcc.ch
- **Verra (VCS)** — Verified Carbon Standard
  - https://verra.org
- **Gold Standard**
  - https://www.goldstandard.org
- **CDM** — Clean Development Mechanism (UN)
  - https://cdm.unfccc.int
- **CBAM** — Carbon Border Adjustment Mechanism (EU)
  - https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en

---

## 3. Glossary EN ↔ ไทย

### 3.1 Technical Terms (LiDAR / Point Cloud)

| EN | ไทย | คำอธิบาย |
|---|---|---|
| **LiDAR** | ลีดาร์ / เลเซอร์สแกน | Light Detection And Ranging |
| **Point Cloud** | กลุ่มจุด 3D | ผลลัพธ์ของ LiDAR/photogrammetry |
| **Photogrammetry** | การวัดภาพถ่าย | สร้าง 3D จากภาพถ่าย |
| **Structure from Motion (SfM)** | (ไม่แปล) | photogrammetry algorithm |
| **TLS** | LiDAR ตั้งพื้น | Terrestrial Laser Scanning |
| **ALS** | LiDAR บนเครื่องบิน | Airborne Laser Scanning |
| **MLS** | LiDAR บนรถ | Mobile Laser Scanning |
| **UAV** | อากาศยานไร้คนขับ | Drone |
| **Voxel** | กล่อง 3D | 3D pixel |
| **Mesh** | ตาข่ายผิว 3D | 3D surface |

### 3.2 Forestry Terms

| EN | ไทย | คำอธิบาย |
|---|---|---|
| **DBH** | เส้นผ่านศูนย์กลางระดับอก | Diameter at Breast Height (1.3 m) |
| **AGB** | ชีวมวลเหนือดิน | Above-Ground Biomass |
| **BGB** | ชีวมวลใต้ดิน | Below-Ground Biomass |
| **CHM** | แผนที่ความสูงเรือนยอด | Canopy Height Model |
| **DTM** | แผนที่ความสูงพื้น | Digital Terrain Model |
| **DSM** | แผนที่ความสูงผิวบน | Digital Surface Model |
| **Canopy** | เรือนยอด, ทรงพุ่ม | Tree top portion |
| **Stem** | ลำต้น | Tree trunk |
| **Crown** | ทรงพุ่ม | Canopy crown |
| **Foliage** | ใบไม้รวม | Leaves collectively |
| **Stand** | ป่าผืน, แปลง | Forest stand |
| **Allometric** | สมการอัลโลเมตริก | Power-law equation linking dimensions to biomass |

### 3.3 ML / CS Terms

| EN | ไทย | คำอธิบาย |
|---|---|---|
| **Segmentation** | การแบ่งส่วน | Group pixels/points by class |
| **Classification** | การจำแนก | Assign each item a class label |
| **Inference** | การอนุมาน (run model) | Use trained model to predict |
| **Training** | การฝึก (model) | Fit model parameters to data |
| **Backbone** | (ไม่แปล) | Pretrained feature extractor (e.g., ResNet) |
| **Transfer Learning** | การเรียนรู้แบบส่งต่อ | Reuse pretrained model |
| **Fine-tuning** | การปรับแต่ง | Re-train last layers on new data |
| **Eigenvalue / Eigenvector** | ค่าลักษณะเฉพาะ | Linear algebra concept |
| **PCA** | (ไม่แปล) | Principal Component Analysis |
| **RANSAC** | (ไม่แปล) | Random Sample Consensus |
| **Watershed** | (ไม่แปล) | Segmentation algorithm |
| **KD-tree** | (ไม่แปล) | Spatial data structure |

### 3.4 Carbon Market Terms

| EN | ไทย | คำอธิบาย |
|---|---|---|
| **Carbon Credit** | คาร์บอนเครดิต | 1 unit = 1 ton CO₂eq |
| **Carbon Offset** | การชดเชยคาร์บอน | Buying credits to offset emissions |
| **CO₂ equivalent** | คาร์บอนไดออกไซด์เทียบเท่า | Standard unit for GHG |
| **Additionality** | (ไม่แปลตรงตัว) | คาร์บอนต้องเป็นของใหม่ที่เพิ่มมา |
| **Permanence** | ความถาวร | คาร์บอนต้องเก็บไว้นาน |
| **Verifiability** | การตรวจสอบได้ | Third-party verification possible |
| **Leakage** | การรั่ว | ลดที่นี่ ไปทำลายที่อื่นแทน |
| **CBAM** | กลไกปรับคาร์บอน EU | Carbon Border Adjustment |
| **ETS** | ระบบซื้อขายปล่อย | Emissions Trading System |
| **MRV** | กระบวนการตรวจสอบ | Monitoring, Reporting, Verification |
| **REDD+** | (ไม่แปล) | Reducing Emissions from Deforestation |

### 3.5 Software / Web / Mobile

| EN | ไทย | คำอธิบาย |
|---|---|---|
| **Framework** | กรอบงาน | Coding template (Next.js, Flutter) |
| **Library** | ไลบรารี | Reusable code package |
| **API** | เอพีไอ | Application Programming Interface |
| **Endpoint** | จุดสิ้นสุด API | A URL that handles a request |
| **WebSocket** | (ไม่แปล) | Real-time bidirectional channel |
| **JWT** | (ไม่แปล) | JSON Web Token |
| **CI/CD** | (ไม่แปล) | Continuous Integration/Deployment |
| **PR** | คำขอ merge | Pull Request |
| **Commit** | (ไม่แปล) | Git change snapshot |
| **Branch** | สาขา (git) | Independent line of code |
| **Merge** | รวม | Combine branches |

---

## 4. Project Files Cross-Reference

### 4.1 Main Docs

| File | บทที่อ้างถึง |
|---|---|
| `docs/ARCHITECTURE.md` | 03 |
| `docs/ROADMAP.md` | 01 |
| `docs/DEVELOPMENT_PLAN.md` | (separate sprint plan) |
| `docs/ml/PIPELINE.md` | 04-12 |
| `docs/ml/ALLOMETRIC.md` | 12 |
| `docs/proposal/SYSTEM_OVERVIEW.md` | 01, 17 |
| `docs/decisions/0001-0006.md` | 03 |

### 4.2 Code Files

| File | บทที่อ้างถึง |
|---|---|
| `services/ml/pipeline/main.py` | 04 |
| `services/ml/pipeline/ground_classification.py` | 05 |
| `services/ml/pipeline/height_normalization.py` | 06 |
| `services/ml/pipeline/canopy_height_model.py` | 07 |
| `services/ml/pipeline/tree_segmentation.py` | 08 |
| `services/ml/pipeline/wood_leaf_separation.py` | 09 |
| `services/ml/pipeline/qsm.py` | 10 |
| `services/ml/pipeline/species_classifier.py` | 11 |
| `services/ml/pipeline/allometric.py` | 12 |
| `services/ml/pipeline/synthetic.py` | 20 |
| `services/ml/notebooks/validate_belgium.py` | 13 |
| `services/ml/tests/test_allometric.py` | 12 |
| `services/ml/data/species_db.csv` | 12 |
| `apps/web/package.json` | 14 |
| `apps/mobile/pubspec.yaml` | 15 |
| `services/api/pyproject.toml` | 16 |

### 4.3 Figures

| Figure | File | Used in |
|---|---|---|
| Architecture (v2) | `fig09_architecture.png` | 03 |
| User flow | `fig10_user_flow.png` | 17 |
| Synthetic pipeline | `fig01-08_*.png` | 04-13 |
| Belgium DBH parity | `fig11_belgium_dbh_parity.png` | 13 |
| Belgium Height parity | `fig12_belgium_height_parity.png` | 13 |
| Belgium Volume parity | `fig13_belgium_volume_parity.png` | 13 |

---

## 5. Further Reading

### 5.1 Books

- **Naesset, E. (2015).** *Forest Inventory: Methodology and Applications.* Springer.
- **Wulder, M.A. et al. (2012).** *Forestry Applications of Airborne Laser Scanning.* Springer.
- **Goodfellow, I., Bengio, Y., Courville, A. (2016).** *Deep Learning.* MIT Press. Free at [deeplearningbook.org](https://www.deeplearningbook.org)

### 5.2 Online Courses

- **Fast.ai** — Practical Deep Learning
- **Coursera — Deep Learning Specialization** (Andrew Ng)
- **OSGeo Live tutorials** — GIS open-source tools

### 5.3 Communities

- **r/forestry, r/MachineLearning** on Reddit
- **PostGIS users group**
- **TGO Thailand** — meetups + workshops

---

## 6. ขอบคุณ

ขอขอบคุณงานวิจัยทุกชิ้นข้างต้นที่ทำให้โครงการ CarbonScan AI เกิดขึ้นได้ — โดยเฉพาะ:

- **อาจารย์ Wannipa** (NSC supervisor) สำหรับ feedback ที่กำหนดทิศทาง v2 pivot
- **Tsutsumi, Ogawa** สำหรับสมการป่าไทยจากยุค 60-80
- **TGO** สำหรับมาตรฐานคาร์บอนไทย
- **Demol et al.** สำหรับ open dataset ที่ทำให้ validation เป็นไปได้
- **PointNet++ team** สำหรับ open-source DL implementations

---

> 📝 **เขียนครั้งแรก:** 2026-05-24 | **Last update:** 2026-05-24

🎉 **จบ Learning Guide ทั้ง 21 บท** — ขอให้ทีมประสบความสำเร็จในการแข่งขัน NSC 2026!
