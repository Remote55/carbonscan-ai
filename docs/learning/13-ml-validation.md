# บท 13 — Validation: ระบบนี้แม่นแค่ไหน?

> 🎯 **เป้าหมาย:** เข้าใจวิธีตรวจสอบความแม่นยำของ pipeline + ตัวเลข validation ที่ใส่ใน Proposal ได้
> 📚 **พื้นฐาน:** [บท 04-12 — ML Pipeline](04-ml-pipeline-overview.md)
> ⏱️ **เวลา:** ~20 นาที

---

## 1. ปัญหา

"พิสูจน์ว่าระบบทำงาน" คือสิ่งที่กรรมการ NSC + อาจารย์ที่ปรึกษา + ลูกค้าทุกคนจะถาม

ต้องการ:
- 📊 ตัวเลข accuracy ที่ **อ้างอิงได้**
- 📈 Plot ที่แสดง prediction vs ground truth
- 🎯 Comparison กับ literature

---

## 2. Validation Strategy — 2 Datasets

### 2.1 Synthetic Plot (Sanity Check)

**File:** `services/ml/pipeline/synthetic.py`

- Generate point cloud จากต้นไม้สังเคราะห์ 5 ต้น
- รู้ ground truth (DBH, Height) ด้วย exact
- ทดสอบ pipeline ทั้ง 8 steps end-to-end

**ผลลัพธ์:**
```
5/5 trees detected ✓
Mean DBH error:    5.9%
Mean Height error: 6.0%
Pipeline runtime:  ~30 sec on laptop CPU
Tests passing:     25/25
```

### 2.2 Belgium Real Dataset — Demol et al. 2021 ⭐

**Citation:** Demol, M. et al. 2021. *Estimating forest above-ground biomass with terrestrial laser scanning: current status and future directions*. Trees, 35, 671-685.

**Dataset:** [Zenodo 4557401](https://doi.org/10.5281/zenodo.4557401)

**Content:**
- 65 ต้น × 4 species จาก Belgium
  - **Fagus sylvatica** (European Beech) — 15 trees
  - **Pinus sylvestris** (Scots Pine) — 30 trees (sites A + B)
  - **Fraxinus excelsior** (European Ash) — 15 trees
  - **Larix decidua** (European Larch) — 5 trees
- TLS scan: RIEGL VZ-1000 (point density ~10K pts/m²)
- **Destructive sampling ground truth:**
  - DBH (cm) — felled measurement
  - Tree Height (m) — felled measurement
  - Fresh mass (kg) — weighed after harvest
  - Wood density (kg/m³) — sampled discs

**ทำไมดี:**
- ✅ **Real data** ไม่ใช่ synthetic
- ✅ **Peer-reviewed** (Trees journal)
- ✅ **Destructive sampling = gold standard** ในวงการ forestry
- ✅ **N = 65 ต้น = statistically significant**

---

## 3. Results

### 3.1 ตารางสรุป

| Metric | Mean Error | Median Error | MAE | RMSE | Literature Range |
|---|---|---|---|---|---|
| **DBH** | 3.8% | 2.9% | **1.17 cm** | 2.07 cm | 1-3 cm (TLS literature) ✅ |
| **Tree Height** | 2.6% | 2.1% | **0.54 m** | 0.76 m | 0.5-1.5 m ✅ |
| **Stem Volume** | 18.8% | 19.6% | 0.20 m³ | 0.28 m³ | ~10-20% (taper equation typical) 🟡 |

### 3.2 ตีความ

- **DBH 1.17 cm error** = อยู่ใน research-grade range ของ TLS literature ✅
- **Height 0.54 m error** = ดีกว่ามาตรฐาน (ปกติ 0.5-1.5 m)
- **Volume 18.8% error** = expected เพราะ taper equation = approximation
  - **Phase 2:** ใช้ TreeQSM → expected 5-10%

---

## 4. Math — Validation Metrics

### 4.1 MAE (Mean Absolute Error)

$$
\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |\hat{y}_i - y_i|
$$

> 📏 **Unit:** เดียวกับ data (cm, m, m³)
> ✅ **Robust** ต่อ outliers

### 4.2 RMSE (Root Mean Squared Error)

$$
\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)^2}
$$

> ⚠️ **Sensitive** ต่อ outliers (เพราะยกกำลัง 2)
> ใช้คู่กับ MAE — ถ้า RMSE >> MAE → มี outliers

### 4.3 Mean / Median Error %

$$
\text{Mean Error \%} = \frac{1}{n} \sum_{i=1}^{n} \frac{\hat{y}_i - y_i}{y_i} \times 100
$$

> ⚠️ **Signed** — บวก = overestimate, ลบ = underestimate
> ✅ Median ใช้กับ data ที่มี outliers

### 4.4 Bias

$$
\text{Bias} = \frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)
$$

> ✅ บอกว่าระบบ "เอนเอียง" ไปทางไหน
> Bias ≈ 0 = unbiased (ดี)

---

## 5. Validation Script

📂 **`services/ml/notebooks/validate_belgium.py`**

```python
def run_all() -> pd.DataFrame:
    # Load CSV + match files
    csv_lookup = load_csv()
    file_paths = find_point_clouds()
    matched = sorted(set(csv_lookup) & set(file_paths))

    results = []
    for tree_name in matched:
        # 1. Load point cloud
        pts = load_point_cloud(file_paths[tree_name], max_points=20_000)

        # 2. Normalize Z
        norm_pts = normalize_z(pts)

        # 3. Wood/leaf segmentation
        labels = wood_leaf_separation.segment_wood_leaf(norm_pts)
        wood_pts = norm_pts[labels == wood_leaf_separation.WOOD]

        # 4. QSM
        qsm_result = qsm.compute_qsm(wood_pts)

        # 5. Compare with ground truth
        gt = csv_lookup[tree_name]
        results.append({
            "tree": tree_name,
            "pred_DBH_cm": qsm_result.dbh_cm,
            "pred_H_m":    qsm_result.height_m,
            "pred_V_m3":   qsm_result.total_volume_m3,
            "gt_DBH_cm":   float(gt['DBH']),
            "gt_H_m":      float(gt['TH_felled']),
            "gt_V_m3":     float(gt['Volume_total_tree_harvested']) / 1000,
        })

    df = pd.DataFrame(results)
    df["DBH_err_pct"] = ((df["pred_DBH_cm"] - df["gt_DBH_cm"]) / df["gt_DBH_cm"] * 100).round(1)
    # ...
    return df
```

**Runtime:** 13 seconds for all 65 trees on laptop CPU

---

## 6. Parity Plots

ดู `docs/proposal/figures/`:
- **`fig11_belgium_dbh_parity.png`** — DBH predicted vs felled
- **`fig12_belgium_height_parity.png`** — Height predicted vs felled
- **`fig13_belgium_volume_parity.png`** — Volume predicted vs destructive

### 6.1 อ่าน Parity Plot ยังไง

```
   Predicted ↑
       │  ●●●●        ← y = x (perfect prediction)
       │ ●● ●● ●
       │●●  ●●    ●   ← scatter around y = x
       │● ●●● ●
       │●●  ●● ●
       │_____________→ Ground Truth
```

- จุดบน $y = x$ = predict ตรง
- จุดเหนือ = overestimate
- จุดใต้ = underestimate
- Cluster แน่น = แม่น, กระจาย = ไม่แม่น
- Outliers ที่ห่างมาก = bug or hard case

### 6.2 Stats box ใน plot

แต่ละ parity plot ของเรามี:
```
n = 65
MAE = 1.17 cm
RMSE = 2.07 cm
Mean error = -1.8%
|Mean error| = 3.8%
```

---

## 7. Sanity Check Tests

📂 **`services/ml/tests/test_synthetic_pipeline.py`**

9 smoke tests ที่ run end-to-end:

```python
def test_step1_ground_classification_recovers_ground():
    # Ground recall ≥ 80%

def test_step2_height_normalization_grounds_zero():
    # |mean Z| < 0.3 m after normalization

def test_step3_chm_max_reasonable():
    # CHM max ≈ tallest tree height (±20%)

def test_step4_watershed_detects_trees():
    # N detected = N ground truth ±50%

def test_step5_wood_leaf_finds_wood():
    # Some points classified as wood

def test_step6_qsm_dbh_in_reasonable_range():
    # DBH within ±40% of truth

def test_step8_allometric_returns_positive_carbon():
    # carbon_kg > 0

def test_end_to_end_no_exceptions():
    # Full pipeline runs without errors
```

**Plus 16 unit tests** for allometric (Step 8) = **25/25 total tests passing**

---

## 8. ตัวเลขที่ใส่ใน Proposal ได้

### 8.1 Headline (1 ประโยค)

> "CarbonScan AI Phase 1 pipeline ผ่านการทดสอบบน Demol et al. (2021) Belgium dataset — TLS point clouds **65 ต้น × 4 species** พร้อม destructive sampling reference. DBH MAE = 1.17 cm (3.8% mean error), Tree Height MAE = 0.54 m (2.6% mean error) — อยู่ในมาตรฐานงานวิจัย TLS forestry"

### 8.2 Section Subheadings

- **Methodology:** "ใช้ Demol et al. 2021 dataset (Zenodo 4557401) ที่มี destructive sampling reference"
- **Results:** ตารางในข้อ 3
- **Comparison:** "DBH MAE 1.17 cm = อยู่ใน TLS literature range 1-3 cm"

---

## 9. Limitations + Honest Disclosure

> ⚠️ **กรรมการ NSC ชอบทีมที่ honest กว่าทีมที่ขายฝัน**

**ระบุชัดใน Proposal:**

1. **Dataset เป็น European temperate species** — ไม่ใช่ Thai tropical
   - **Mitigation:** Phase 2 จะ validate กับ Thai data (NEON เกาะที่มี, หรือ field collection)

2. **Volume error 18.8% > DBH/Height error**
   - **Reason:** Taper equation = approximation, not full QSM
   - **Phase 2:** TreeQSM → expected 5-10%

3. **Watershed over-segmentation บางครั้ง**
   - **Mitigation:** QSM filter ตัด fragment trees (DBH < 2cm)
   - **Phase 2:** Marker-controlled watershed

---

## 10. ❓ คำถามตรวจสอบความเข้าใจ

1. **Synthetic vs Real dataset — แต่ละแบบดี/แย่ยังไง?**
2. **MAE vs RMSE — ต่างกันยังไง? ใช้ตอนไหน?**
3. **Mean error vs |Mean error| — ทำไมรายงานทั้งคู่?**
4. **"Destructive sampling" คืออะไร? ทำไม gold standard?**
5. **ทำไม Volume error ของเรา 18.8% — แสดงว่าระบบใช้ไม่ได้ใช่ไหม?**
   - hint: ดู section 9 + Phase 2 plan

---

## 11. อ่านต่อ

- [บท 12 — Allometric (สูตร Carbon)](12-ml-step8-allometric.md)
- [บท 20 — Datasets (Belgium + Synthetic + Future)](20-datasets.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
