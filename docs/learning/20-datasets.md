# บท 20 — Datasets (ข้อมูลที่ใช้ + ที่จะใช้)

> 🎯 **เป้าหมาย:** เข้าใจ data sources ทั้งหมด — synthetic + real public + future plans
> 📚 **พื้นฐาน:** [บท 13 — Validation](13-ml-validation.md)
> ⏱️ **เวลา:** ~15 นาที

---

## 1. ภาพรวม Data Sources

| Source | ขนาด | Status | Use |
|---|---|---|---|
| **Synthetic Generator** | parametric | ✅ Implemented | Smoke testing, demo |
| **Demol 2021 Belgium** | 65 trees | ✅ Validated | Validation |
| **NEON US** | 50+ plots | 🟡 Planned Phase 2 | Wood/leaf training |
| **Field collection (Thailand)** | TBD | 🔴 Phase 3 | Domain adaptation |
| **iNaturalist scrape** | 1200 images | 🟡 Phase 2 | Species classifier |

---

## 2. Synthetic Data Generator

### 2.1 File

📂 **`services/ml/pipeline/synthetic.py`**

### 2.2 What it generates

```python
points, gt_labels, trees = synthetic.generate_synthetic_plot(
    n_trees=5,
    plot_size_m=30.0,
    ground_z_variation=1.2,
    seed=42,
)
```

**Output:**
- `points` — (N, 3) XYZ array, ~30,000 points
- `gt_labels` — (N,) int8 with class (0=ground, 1=wood, 2=leaf)
- `trees` — list of `TreeParams` (DBH, height, species)

### 2.3 Algorithm Overview

```
1. Generate ground plane with terrain undulation (sin/cos)
2. For each tree (5 trees default):
     - Place at non-overlapping random position
     - Generate trunk: cylindrical with taper (DBH 20-45cm, height 12-22m)
     - Generate branches: 12 per tree, radiating from upper trunk
     - Generate canopy: ellipsoidal leaf cloud (~4000 points each)
3. Stack ground + wood + leaf with class labels
4. Shuffle so order doesn't leak class info
```

### 2.4 Use cases

- ✅ Smoke testing (25/25 tests pass)
- ✅ Demo without 5GB download
- ✅ Reproducible (seed-controlled)
- ✅ Has perfect ground truth

### 2.5 Limitations

- ❌ Not statistically representative ของป่าจริง
- ❌ Tree shapes simplistic (one species template)
- ❌ ไม่สามารถ validate ค่าจริงของ accuracy

---

## 3. Demol et al. 2021 — Belgium Destructive Biomass

### 3.1 Citation

> Demol, M., Verbeeck, H., Gielen, B., et al. (2021). **Estimating forest above-ground biomass with terrestrial laser scanning: current status and future directions**. *Trees*, 35, 671-685. [DOI: 10.1007/s00468-020-02067-7](https://doi.org/10.1007/s00468-020-02067-7)

### 3.2 Download

- **Zenodo:** [10.5281/zenodo.4557401](https://doi.org/10.5281/zenodo.4557401)
- License: CC-BY 4.0 (open)

### 3.3 Content

| File | Size | Content |
|---|---|---|
| `pointclouds_clean.7z` | 128 MB | 66 trees TLS scans (XYZ text) |
| `optimal_QSMs.zip` | 16 MB | Reference TreeQSM v2.3 models |
| `Destructive_and_qsm_data_DEMOL.csv` | 17 KB | Ground truth measurements |
| `images.7z` | 174 MB | Field photos (optional) |

### 3.4 Species

| Code | Species | English | Count |
|---|---|---|---|
| FSYL | *Fagus sylvatica* | European Beech | 15 |
| PSYLA + PSYLB | *Pinus sylvestris* | Scots Pine | 30 (sites A+B) |
| FEXC | *Fraxinus excelsior* | European Ash | 15 |
| LXDC | *Larix decidua* | European Larch | 5 |
| | | **Total** | **65** |

### 3.5 Ground Truth Columns

```
DBH                          ← cm (felled measurement)
TH_felled                    ← m (tree height felled)
Fresh_mass_total_tree_harvested  ← kg (weighed!)
Fresh_mass_stem_harvested
Fresh_mass_crown_harvested
WSG_base_disc                ← wood density (g/cm³)
Volume_total_tree_harvested  ← m³ (destructive volume)
qsm_mean_volume              ← Reference QSM volume
```

### 3.6 ทำไม Gold Standard

- ✅ **Real TLS scans** (not synthetic)
- ✅ **Destructive sampling** = ground truth ที่แท้จริง
- ✅ **Peer-reviewed** (Trees journal)
- ✅ **65 trees** = statistically significant
- ✅ **4 species** with diverse architecture (broadleaf + conifer)

### 3.7 ระบบเราใช้ยังไง

```bash
cd services/ml
python notebooks/validate_belgium.py
# Runs full pipeline on all 65 trees
# Output: docs/proposal/figures/belgium_validation.csv + 3 parity PNGs
```

Results: DBH MAE 1.17 cm, Height MAE 0.54 m (ดู [บท 13](13-ml-validation.md))

### 3.8 ข้อจำกัด

- ❌ European temperate species (ไม่ใช่ Thai tropical)
- ❌ TLS only (ไม่มี drone-LiDAR samples)
- ❌ Healthy trees only (no disease/damage cases)

---

## 4. NEON US Forest LiDAR (Phase 2 Plan)

### 4.1 Source

**NEON** = **N**ational **E**cological **O**bservatory **N**etwork (US)

**URL:** https://data.neonscience.org/data-products/DP1.30003.001

### 4.2 What's available

- ALS LiDAR for **47 forest sites** ทั่ว US
- Includes BBox tile downloads
- License: CC0 (public domain)

### 4.3 ใช้ทำอะไรใน Phase 2

- Train **PointNet++ wood-leaf segmentation model**
- Annotate ~50-100 trees ด้วย CloudCompare
- Cross-validate กับ Belgium (different geography)

### 4.4 ข้อจำกัด

- ❌ US species only (ยังไม่ใช่ Thai)
- ⚠️ Large download (5+ GB per tile)

---

## 5. iNaturalist Species Photos (Phase 2)

### 5.1 Source

**iNaturalist** — community citizen-science platform

**API:** https://api.inaturalist.org/v1/observations

### 5.2 What we'll collect

```python
# Pseudo-code
import requests

for species in TARGET_SPECIES:
    response = requests.get(
        f"https://api.inaturalist.org/v1/observations?taxon_name={species}",
        params={"photos": True, "quality_grade": "research"},
    )
    photos = [obs["photos"][0]["url"] for obs in response.json()["results"]]
    # Download + clean
```

**Target:** 200 photos × 5 species + 100 "Unknown" = **1200 photos**

### 5.3 Use case

Train ResNet-50 species classifier (Step 7, Phase 2)

---

## 6. Thailand Field Collection (Phase 3 — Post-NSC)

### 6.1 Plan

- Partner with **กรมป่าไม้** หรือ **ม.เกษตรศาสตร์**
- Visit 3-5 plots (~1 ha each)
- TLS scan + destructive sampling on 10-20 trees
- Thai species coverage: สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง

### 6.2 ทำไมสำคัญ

- ✅ True validation on Thai species
- ✅ Field-collected RGB for species classifier
- ✅ TGO certification requirement
- ✅ Marketing collateral

---

## 7. Data Privacy + Licensing

### 7.1 Our Pipeline Outputs

ผู้ใช้อัปโหลด .las → ระบบเก็บ:
- Point cloud (anonymized)
- Computed metrics
- GPS coordinates

**Retention policy:**
- LAS file: indefinite (with user consent)
- Photos (mobile): 30 days post-processing
- Audit logs: 7 years (for TGO compliance)

### 7.2 Datasets ที่ใช้ภายใน

| Dataset | License | Can use commercially? |
|---|---|---|
| Synthetic | Our own — MIT | ✅ Yes |
| Demol 2021 | CC-BY 4.0 | ✅ Yes (with citation) |
| NEON | CC0 | ✅ Yes |
| iNaturalist | CC-BY-NC (varies) | ⚠️ Need to filter |

---

## 8. ❓ คำถามตรวจสอบความเข้าใจ

1. **Synthetic vs Real datasets — แต่ละแบบดี/แย่ยังไง?**
2. **Demol 2021 dataset มีอะไรพิเศษ?**
3. **ทำไมยังไม่ใช้ NEON ตั้งแต่ Phase 1?**
4. **Species classifier ต้องการ images กี่รูป?**
5. **Thailand field collection สำคัญสำหรับ TGO certification ยังไง?**

---

## 9. อ่านต่อ

- [บท 21 — References + Glossary](21-references-glossary.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
