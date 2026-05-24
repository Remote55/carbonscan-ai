# บท 10 — Step 6: QSM (วัด DBH + Height + Volume)

> 🎯 **เป้าหมาย:** เข้าใจวิธีวัด DBH (ขนาดเส้นผ่านศูนย์กลางลำต้น), ความสูง, และปริมาตรไม้ จาก wood points
> 📚 **พื้นฐาน:** [บท 09 — Wood-Leaf Separation](09-ml-step5-wood-leaf-separation.md)
> ⏱️ **เวลา:** ~30 นาที

---

## 1. ปัญหา

หลัง Step 5 เรามี **wood points** เฉพาะของแต่ละต้น

ต้องการ:
- 📏 **DBH** = Diameter at Breast Height (cm) — ขนาดลำต้นที่ระดับอก (1.3 m)
- 🌳 **Height** = Tree Height (m) — ความสูงต้น
- 📦 **Volume** = Stem Volume (m³) — ปริมาตรเนื้อไม้

**ทำไมสำคัญ:** เป็น input ของ Step 8 (Allometric) → คำนวณ Carbon

---

## 2. QSM คืออะไร

**QSM** = **Q**uantitative **S**tructure **M**odel

แนวคิด: **สร้าง model 3D ที่ประกอบด้วยทรงกระบอกหลายอัน** ครอบลำต้นและกิ่ง → ผลรวม volume ของทรงกระบอก = volume จริง

```
Real tree:                       QSM model:
                                
       🌳                            ⬢⬢
      🌳🌳                          ⬢⬢⬢⬢
       ║                            ║║
       ║                            ║║   ← cylinder
       ║                            ║║
       ║                            ║║
─ ─ ─ ─ ─                        ─ ─ ─ ─ ─
ground                           ground
```

**Reference paper:** Raumonen et al. 2013 — "Fast Automatic Precision Tree Models from Terrestrial Laser Scanner Data" (TreeQSM)

---

## 3. Phase 1 Simplification — Taper Equation

Full TreeQSM ซับซ้อน (~2,000 บรรทัด MATLAB) — Phase 1 ของเราใช้ **3 measurements + taper equation**:

### 3.1 DBH Measurement

วัด diameter ของลำต้นที่ height = 1.3 m

```
Slice point cloud ที่ z ∈ [1.3-0.15, 1.3+0.15] m
       ↓
ได้ "วงแหวน" ของจุดรอบลำต้น
       ↓
Fit circle (RANSAC) → diameter
```

### 3.2 Height

```
Height = max(z) ของ point cloud
```

(หลัง normalize แล้ว Z=0 = พื้น, max Z = ยอดต้น)

### 3.3 Volume (Taper Equation)

แทนที่จะใช้ทรงกระบอกหลายอัน — ใช้สูตรเดียวที่ปาวประมาณ:

$$
\boxed{V = \frac{\pi}{4} \cdot \text{DBH}^2 \cdot H \cdot f}
$$

โดย:
- $\text{DBH}$ ในหน่วย **m** (DBH_cm / 100)
- $H$ ในหน่วย m
- $f$ = **form factor** = $V_{\text{actual}} / V_{\text{cylinder}}$
- ค่าทั่วไป: $f \approx 0.45-0.55$ สำหรับต้นไม้ทั่วไป (เราใช้ 0.5)

> 💡 **Form factor** เกิดเพราะลำต้น **เรียวขึ้นด้านบน** ไม่ใช่ทรงกระบอกสมบูรณ์

---

## 4. RANSAC Circle Fit

### 4.1 ทำไมต้อง RANSAC

Slice ที่ z=1.3m มี:
- ✅ จุดวงรอบลำต้น (inliers)
- ❌ จุดของกิ่งที่บังเอิญผ่าน (outliers)
- ❌ noise

**RANSAC** = **RA**ndom **SA**mple **C**onsensus — fit shape ที่ทนต่อ outliers

### 4.2 อัลกอริทึม

```
Repeat N times:
    1. สุ่ม 3 จุดจาก slice → คำนวณ circumcircle (center, radius)
    2. ถ้า radius ใหญ่ผิดปกติ (> 0.6 m) → skip
    3. นับจุดอื่นๆ ที่อยู่ใน tolerance (~2 cm) ของ circle → inliers
    4. ถ้า inlier count > best → update best

Return: best (center, radius)
```

### 4.3 Median Cluster Filter (Phase 1 enhancement)

ถ้า watershed over-segment → slice อาจมีหลาย trunks → fit circle ได้วงใหญ่เกินจริง

**Solution:** Filter ให้ใช้แค่จุดใกล้ centroid (median) ก่อน fit

```python
median_xy = np.median(slice_xy, axis=0)
near_mask = distance_to_median < 1.0  # 1 m
slice_xy = slice_xy[near_mask]        # keep only nearby points
```

---

## 5. โค้ดของเรา

📂 **`services/ml/pipeline/qsm.py`**

```python
import numpy as np
from dataclasses import dataclass

DEFAULT_FORM_FACTOR = 0.50

@dataclass
class QsmResult:
    dbh_cm: float
    height_m: float
    stem_volume_m3: float
    branches_volume_m3: float
    total_volume_m3: float
    n_cylinders: int
    model_quality: float

def measure_dbh(
    wood_points: np.ndarray,
    *,
    target_height_m: float = 1.3,
    slice_thickness_m: float = 0.3,
    seed: int = 0,
) -> tuple[float, float]:
    """DBH via RANSAC circle fit at 1.3m slice."""

    # 1. Slice
    half = slice_thickness_m / 2.0
    slice_mask = (
        (wood_points[:, 2] >= target_height_m - half)
        & (wood_points[:, 2] <= target_height_m + half)
    )
    slice_xy = wood_points[slice_mask, :2]
    if len(slice_xy) < 5:
        return 0.0, 0.0

    # 2. Median-cluster filter (avoid multi-trunk fits)
    median_xy = np.median(slice_xy, axis=0)
    near = np.hypot(slice_xy[:, 0] - median_xy[0], slice_xy[:, 1] - median_xy[1]) < 1.0
    if int(near.sum()) >= 5:
        slice_xy = slice_xy[near]

    # 3. RANSAC circle fit
    rng = np.random.default_rng(seed)
    _, _, radius_m, inlier_ratio = _ransac_circle_fit(slice_xy, rng=rng)

    dbh_cm = radius_m * 2.0 * 100.0  # m → cm
    dbh_cm = float(np.clip(dbh_cm, 0.0, 120.0))  # sanity clip
    return dbh_cm, float(inlier_ratio)


def measure_height(points: np.ndarray) -> float:
    return float(points[:, 2].max())


def estimate_volume_taper(
    dbh_cm: float,
    height_m: float,
    *,
    form_factor: float = DEFAULT_FORM_FACTOR,
) -> float:
    """V = (π/4) × DBH² × H × form_factor."""
    if dbh_cm <= 0 or height_m <= 0:
        return 0.0
    dbh_m = dbh_cm / 100.0
    return float(np.pi / 4.0 * dbh_m**2 * height_m * form_factor)


def compute_qsm(wood_points: np.ndarray, *, seed: int = 0) -> QsmResult:
    """DBH + Height + Volume for one tree."""

    if len(wood_points) == 0:
        return QsmResult(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0)

    dbh_cm, fit_q = measure_dbh(wood_points, seed=seed)
    height_m = measure_height(wood_points)
    stem_vol = estimate_volume_taper(dbh_cm, height_m)

    return QsmResult(
        dbh_cm=dbh_cm,
        height_m=height_m,
        stem_volume_m3=stem_vol,
        branches_volume_m3=0.0,  # Phase 2
        total_volume_m3=stem_vol,
        n_cylinders=1,
        model_quality=fit_q,
    )
```

### Performance
- 1 tree (~5K wood points): ~50-100 ms (RANSAC 200 iterations)

---

## 6. Validation บน Belgium

จากผลใน [บท 13 — Validation](13-ml-validation.md):

```
65 trees (real TLS scans):
  DBH:     Mean error 3.8% (MAE 1.17 cm)  ⭐
  Height:  Mean error 2.6% (MAE 0.54 m)   ⭐
  Volume:  Mean error 18.8% (Phase 2 จะลด → 5-10%)
```

> 💡 **DBH/Height แม่นมาก แต่ Volume error 18.8%** — เพราะ taper equation = approximation.
> Phase 2: ใช้ **TreeQSM full** (cylinder per branch) → ลด error เหลือ 5-10%

---

## 7. Citation

- **Raumonen, P. et al. 2013**. "Fast Automatic Precision Tree Models from Terrestrial Laser Scanner Data". *Remote Sensing*, 5(2), 491-520. (TreeQSM original)
- **Cao, T. et al. 2019**. "Wood volume from taper equations" — review of taper equation form factors.

---

## 8. ข้อจำกัด + Phase 2

| Phase 1 | Phase 2 |
|---|---|
| Taper equation = approx | Full TreeQSM (cylinder per branch) |
| ไม่แยก branches | แยก stem + branches volume |
| Form factor ค่าเดียว | Species-specific form factors |
| DBH @ 1.3m เท่านั้น | Multi-height profiling |

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

1. **DBH คืออะไร? วัดที่ไหน?**
2. **ทำไมต้องใช้ RANSAC ไม่ใช้ least-squares ปกติ?**
3. **Form factor คืออะไร? ทำไม f ≈ 0.5?**
4. **"Median-cluster filter" ป้องกันปัญหาอะไร?**
5. **ทำไม Volume error ของระบบเรา (18.8%) สูงกว่า DBH/Height error (3-4%)?**

---

## 10. อ่านต่อ

- [บท 11 — Step 7: Species Classification](11-ml-step7-species-classifier.md)
- [บท 12 — Step 8: Allometric Carbon ⭐](12-ml-step8-allometric.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
