# 🔬 ML Pipeline Details

> Step-by-step explanation of the CarbonScan AI ML Pipeline

---

## Overview

```
Input: .las / .laz / .ply (Point Cloud)
                  │
                  ▼
        ┌─────────────────────┐
        │ Pre-processing      │
        │ - Read              │
        │ - Filter outliers   │
        │ - Voxel downsample  │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 1. Ground Class.    │
        │   (CSF algorithm)   │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 2. Height Normalize │
        │   (DTM subtraction) │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 3. Canopy Height    │
        │   Model (Pit-free)  │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 4. Tree Segmentation│
        │   (Watershed)       │
        └─────────┬───────────┘
                  │
                  ▼ for each tree
        ┌─────────────────────┐
        │ 5. Wood-Leaf Sep    │
        │   (PointNet++)      │  ⭐ Deep Learning
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 6. QSM              │
        │   (Cylinder fit)    │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 7. Species Classify │
        │   (ResNet on RGB)   │  ⭐ Deep Learning
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ 8. Allometric → C   │
        │   (TGO equations)   │
        └─────────┬───────────┘
                  │
                  ▼
Output: JSON per tree
       {dbh_cm, height_m, volume_m3, biomass_kg, carbon_kg, co2eq_kg}
```

---

## Step 1: Ground Classification (CSF)

**Algorithm:** Cloth Simulation Filter
**Library:** PDAL
**Time:** ~30 sec / 1 ไร่

### What it does
แยกจุด point cloud ออกเป็น 2 ประเภท: ground (พื้นดิน) และ non-ground (พืชพรรณ)

### How it works
1. Invert point cloud (พลิกบน-ล่าง)
2. จำลอง "ผ้า" ตกลงบนยอด → ผ้าจะติดอยู่บนพื้นดิน
3. จุดที่ใกล้ผ้า = ground

### Parameters
```python
{
    "resolution": 0.5,    # คลอธ grid spacing (ม.)
    "threshold": 0.5,     # ระยะห่างที่ยอมรับ (ม.)
    "rigidness": 3,       # 1 (loose) - 3 (rigid)
}
```

### Output
Each point has classification:
- `2` = ground
- `1` = unclassified (everything else)

---

## Step 2: Height Normalization

**Library:** lidR (R) ported to Python (Open3D + scipy)
**Time:** ~30 sec / 1 ไร่

### What it does
Subtract DTM (Digital Terrain Model) จากทุกจุด → จุดที่อยู่บนพื้นดินมี Z = 0

### Why?
ต้นไม้ที่อยู่บนเนินกับที่ราบ → ความสูง absolute Z จะต่างกัน แต่ความสูงจริงเท่ากัน

### Algorithm
1. Build DTM from ground points (TIN interpolation)
2. For each non-ground point: `z_normalized = z - dtm(x, y)`

---

## Step 3: Canopy Height Model (CHM)

**Algorithm:** Pit-free CHM (Khosravipour et al. 2014)
**Library:** Custom (numpy + scipy)
**Time:** ~1 min / 1 ไร่

### What it does
สร้าง raster 2D ที่แต่ละ pixel = ความสูงของยอดต้นไม้ที่จุดนั้น

### Why pit-free?
Standard CHM มี "หลุม" (pits) จากจุดที่ผ่านใบลงไปถึงพื้น → ทำให้ tree detection ผิด

Pit-free algorithm:
1. สร้าง CHM หลาย threshold (0, 10, 20, 30, 40, 50 ม.)
2. Combine → ใช้ max(CHM_t) → ไม่มีหลุม

### Output
`numpy.ndarray` (H, W) ที่แต่ละ cell = max height ในระยะ resolution × resolution ม.

---

## Step 4: Individual Tree Detection (ITD)

**Algorithm:** Watershed Segmentation
**Library:** scikit-image
**Time:** ~10 sec / CHM

### What it does
แยก CHM raster ออกเป็น "polygons" → แต่ละ polygon = 1 ต้นไม้

### Algorithm
1. หา local maxima ใน CHM (= treetops)
2. ใช้ maxima เป็น markers
3. Watershed flood-fill จาก markers → boundaries = ขอบทรงพุ่ม

### Parameters
```python
{
    "min_distance": 3,      # minimum distance between treetops (pixels)
    "min_height": 4.0,      # minimum tree height (m)
}
```

### Output
Each point in original cloud gets `treeID` (integer) or `NA` (not a tree, e.g., shrub)

---

## Step 5: Wood-Leaf Semantic Segmentation ⭐

**Algorithm:** PointNet++ (Qi et al. 2017)
**Library:** PyTorch + Open3D-ML
**Time:** ~5 sec / tree (on GPU)

### What it does
สำหรับแต่ละ tree point cloud → label แต่ละจุดว่าเป็น `wood` (ลำต้น/กิ่ง) หรือ `leaf` (ใบ)

### Why DL not rule-based?
- Rule-based (เช่น TLSeparation) ใช้ geometric features (linearity, sphericity)
- DL learn features จาก data → robust กับ tree species, scan quality ต่าง ๆ

### Training Strategy
- **Dataset:** NEON forest LiDAR + manual annotation (use CloudCompare)
- **Architecture:** PointNet++ MSG (Multi-Scale Grouping)
- **Loss:** Cross-entropy + Dice loss
- **Augmentation:** rotation, scaling, noise
- **Target:** IoU ≥ 0.70 บน validation set

### Fallback (Phase 1 ก่อน DL พร้อม)
ใช้ **TLSeparation** (Cembrowski et al.) — rule-based, works without training

```python
from tlseparation import wood_leaf_classification

result = wood_leaf_classification(
    point_cloud,
    k=20,                 # k-nearest neighbors
    knn_downsample=0.5,
)
# Output: 0 = wood, 1 = leaf
```

---

## Step 6: Quantitative Structure Model (QSM)

**Algorithm:** Cylinder Fitting (TreeQSM-inspired)
**Library:** Custom Python (numpy + scipy)
**Time:** ~2 sec / tree

### What it does
จาก wood points → fit ทรงกระบอกครอบลำต้นและกิ่ง → คำนวณปริมาตรไม้ (Volume in m³)

### Algorithm Overview
1. Skeleton extraction (find centerline of wood structure)
2. Branching detection (where stem splits)
3. Cylinder fit per segment (RANSAC)
4. Sum volumes ของทุก cylinder

### Output
```python
{
    "stem_volume_m3": 0.234,
    "branches_volume_m3": 0.058,
    "total_volume_m3": 0.292,
    "n_cylinders": 47,
    "model_quality": 0.89,  # 0-1 fit quality
}
```

### Validation
เทียบกับ **destructive sampling** (โค่นต้นแล้วชั่ง) ในงานวิจัย — TreeQSM RMSE typically 10-15%

---

## Step 7: Species Classification ⭐

**Algorithm:** ResNet-50 with Transfer Learning
**Library:** PyTorch + torchvision
**Time:** ~100 ms / image (GPU), ~500ms (CPU/Mobile)

### What it does
จาก RGB photo ของเปลือก/ใบไม้ → predict species (5 classes)

### Why on-device (mobile)?
- เร็ว (no API call needed)
- Privacy
- Offline support

### Training
- **Dataset:** scraped from iNaturalist + manual labeling (Phase 1 deliverable)
- **Classes:** Tectona, Dipterocarpus, Bambusa, Hevea, Afzelia + "Unknown"
- **Backbone:** ResNet-50 pretrained ImageNet
- **Fine-tune:** last 2 layers
- **Target:** Top-1 accuracy ≥ 85%

### Mobile Deployment
- Export to TFLite (int8 quantization)
- Model size: < 20 MB
- Inference: < 500ms on mid-range Android

---

## Step 8: Allometric Carbon Calculation

**Library:** Custom Python (pandas + species DB)
**Time:** < 1 ms / tree

### Formulas (TGO Forestry Sector Guideline 2017)

**Aboveground Biomass (AGB):**
$$
\text{AGB} = a \times \text{DBH}^b \times H^c \quad (\text{kg})
$$

**Belowground Biomass (BGB):**
$$
\text{BGB} = \text{AGB} \times R_{\text{root/shoot}}
$$

**Total Biomass:**
$$
B = \text{AGB} + \text{BGB}
$$

**Carbon Stock:**
$$
C = B \times C_{\text{fraction}}
$$
(IPCC default $C_{\text{fraction}} = 0.47$)

**CO2 Equivalent:**
$$
\text{CO}_2\text{eq} = C \times \frac{44}{12}
$$

### Wood Density vs Allometric
Two ways to calculate biomass:
1. **From DBH + H:** Use allometric equation (this is what we use)
2. **From Volume + Density:** $B = V \times \rho$ (alternative cross-check)

We compute both and report whichever has higher confidence.

📖 ดู [ALLOMETRIC.md](ALLOMETRIC.md) สำหรับสมการแต่ละชนิดต้นไม้

---

## Pipeline Output Format

```json
{
  "metadata": {
    "input_file": "abc.las",
    "processing_time_seconds": 423,
    "pipeline_version": "0.1.0",
    "model_versions": {
      "wood_leaf_segmenter": "v1.0",
      "species_classifier": "v1.0"
    }
  },
  "summary": {
    "total_trees": 42,
    "total_carbon_kg": 5847.3,
    "total_co2eq_kg": 21430.6,
    "species_breakdown": {
      "Tectona grandis": 15,
      "Dipterocarpus alatus": 22,
      "Bambusa spp.": 5
    }
  },
  "trees": [
    {
      "tree_id": 1,
      "location": {"lat": 18.7883, "lon": 98.9853, "z": 320.4},
      "species_sci": "Tectona grandis",
      "species_confidence": 0.92,
      "dbh_cm": 25.3,
      "height_m": 15.8,
      "crown_radius_m": 3.2,
      "volume_m3": 0.45,
      "biomass_kg": 292.5,
      "carbon_kg": 137.5,
      "co2eq_kg": 504.2,
      "point_count": 8472,
      "wood_leaf_iou": 0.78
    }
  ]
}
```

---

## Performance Benchmarks (Target)

| Step | Time | Hardware |
|---|---|---|
| 1. Ground class. | 30s/plot | CPU |
| 2. Height norm. | 30s/plot | CPU |
| 3. CHM | 1min/plot | CPU |
| 4. Tree seg. | 10s/plot | CPU |
| 5. Wood-leaf (per tree) | 5s | GPU |
| 6. QSM (per tree) | 2s | CPU |
| 7. Species (per tree) | 1s | GPU |
| 8. Allometric | < 1ms | CPU |
| **Total** | **~10 min/plot** | **GPU+CPU** |

(Assuming 30-50 trees/plot)

---

## Future Improvements

1. **Deep QSM** — End-to-end DL for volume (skip cylinder fitting)
2. **TreeID via Re-identification** — Track ต้นเดียวกันข้ามปี (4D Carbon)
3. **Multi-modal fusion** — Combine LiDAR + RGB end-to-end
4. **Lighter models** — Distill to smaller models for faster inference

---

📖 **See also:**
- [ALLOMETRIC.md](ALLOMETRIC.md) — Detailed equations per species
- [DATASETS.md](DATASETS.md) — Training data
- [services/ml/README.md](../../services/ml/README.md) — Code structure
