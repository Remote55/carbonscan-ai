# 📊 Datasets

> Sources of training and validation data for CarbonScan AI

---

## Primary Datasets

### 1. NEON (National Ecological Observatory Network) ⭐

**URL:** https://data.neonscience.org/

**Why:** Open-access, high-quality LiDAR ป่าไม้ของ USA, มี ground-truth annotations

**Data Products:**
- **DP1.30003.001** — Discrete return LiDAR point cloud (.las)
- **DP3.30015.001** — Ecosystem Structure (canopy height model)
- **DP1.30010.001** — High-resolution orthorectified imagery (RGB)
- **DP1.10098.001** — Vegetation structure (DBH, height field measurements)

**Recommended Sites for Pilot:**
- **OSBS** (Ordway-Swisher Biological Station, Florida) — Mixed forest, ใกล้ tropical
- **BART** (Bartlett Experimental Forest, NH) — Temperate
- **TALL** (Talladega, Alabama) — Pine forest

**How to Download:**
```bash
# Get API token from https://data.neonscience.org/myaccount
export NEON_TOKEN="your_token"

# Use script
python services/ml/scripts/download_neon.py \
    --site OSBS \
    --year 2022 \
    --output data/raw/neon/OSBS_2022/

# Or manual: https://data.neonscience.org/data-products/explore
```

**Storage:**
- 1 plot ≈ 500MB - 2GB
- Train on 5-10 plots = ~10GB
- ตั้งไว้ที่ `data/raw/neon/` (gitignored)

---

### 2. ForestSemantic / Tree Species Wikidata RGB

**Use:** Species classifier training (Step 7)

**Sources:**
- iNaturalist (manually filter Thai species)
- Pl@ntNet API (free tier)
- Google Images (manual scraping)
- เก็บภาพ field ของทีมเอง (high quality)

**Target:** 200 images per species × 5 species = 1000 images

**Annotation Tool:** None needed (filename-based labels)

---

### 3. TLSeparation Sample Data

**URL:** https://github.com/TLSeparation/source

**Use:** Wood-leaf separation baseline + validation

**Includes:** 6 tree point clouds with labeled wood/leaf

---

## Datasets to Build (Phase 1-2)

### Calibration Dataset (Ground Truth)
**Purpose:** Validate Photogrammetry accuracy vs manual measurement

**Plan:**
1. หาต้นไม้ 20 ต้นใน ม. หรือสวน
2. วัด DBH ด้วยสายวัด, ความสูงด้วย clinometer
3. ถ่ายภาพรอบต้นไม้ 30-50 รูป
4. Process ด้วย COLMAP/OpenMVS
5. Compare: ML output vs ground truth → report RMSE

**Storage:** `data/ground-truth/calibration_2026/`

---

### Thai Species Photo Database (Phase 4+)
**Purpose:** Improve species classifier accuracy for Thai trees

**Plan:**
1. Site visits to ม.เกษตร / ม.อ. / สวนพฤกษศาสตร์
2. ถ่ายรูป bark + leaf + tree shape ของแต่ละชนิด
3. Annotate with botanist consultation
4. Train + release as open dataset (ดึง community)

---

## Public LiDAR Sources (Alternative)

### OpenTopography
- URL: https://opentopography.org/
- Global LiDAR (Aerial)
- ดี for landscape-scale, less for individual trees

### USGS 3DEP
- URL: https://www.usgs.gov/3d-elevation-program
- USA only

### GEDI (Spaceborne LiDAR)
- URL: https://gedi.umd.edu/
- Global, but low resolution (~25m footprint)
- ไม่เหมาะกับ tree-level

### Thai Sources (To Explore)
- **GISTDA** — National space agency, อาจมี LiDAR
- **กรมป่าไม้** — National Forestry Department
- **มหาวิทยาลัย** — บางมหาวิทยาลัยมี LiDAR scanner

⚠️ ส่วนใหญ่ต้องขอ permission + วัตถุประสงค์การใช้งาน

---

## Data Pipeline

```
Raw Data (NEON, etc.)
        │
        ▼
data/raw/
        │ (preprocess)
        ▼
data/processed/
        │ (train/val/test split)
        ▼
data/splits/
        │
        ▼
PyTorch DataLoader
```

### Preprocessing Steps
```python
# services/ml/scripts/preprocess_neon.py

1. Read .las with laspy
2. Filter outliers (statistical_outlier_removal)
3. Voxel downsample (1cm)
4. Normalize coordinates
5. Split into chunks (4096 points each)
6. Save as .pt files (PyTorch tensors)
```

---

## Storage Strategy

### Local Dev
```
data/
├── raw/           Large files (gitignored)
├── processed/     Smaller, gitignored
└── samples/       1 small sample for tests (committed)
```

### Production (Cloud)
- Raw datasets: Supabase Storage (private bucket)
- Trained models: Hugging Face Hub (public)
- User uploads: Supabase Storage (per-user bucket)

---

## Annotation Tools

### CloudCompare (Desktop)
- Free, cross-platform
- Manual wood-leaf labeling
- Export to .las with classification field

### CVAT (Web)
- For RGB image classification (species)
- Self-host or use cvat.ai

### Roboflow
- For RGB image, easy UI
- Free tier for small projects

---

## Data Quality Checks

### Before Training
- [ ] No duplicate point clouds
- [ ] Class balance (wood vs leaf — should be ~30:70)
- [ ] Geographic diversity (multiple sites)
- [ ] No corrupted files

### Validation
- [ ] Train/val/test = 70/15/15
- [ ] No leakage (same tree not in both train and val)

---

## Licensing

| Dataset | License | Use |
|---|---|---|
| NEON | Public Domain | Free use, attribution appreciated |
| Pl@ntNet | CC BY-NC 4.0 | Non-commercial OK |
| TLSeparation | Apache 2.0 | Free use |
| Our own data | MIT | We choose |

---

## ⚠️ Action Items

- [ ] (User) Apply for NEON API token
- [ ] (User) Download 1 sample plot for testing
- [ ] (User) Build calibration dataset (Phase 1)
- [ ] (User) Document any custom preprocessing in this file

---

📖 **See also:**
- [PIPELINE.md](PIPELINE.md) — How datasets feed into pipeline
- [services/ml/scripts/](../../services/ml/scripts/) — Download scripts
