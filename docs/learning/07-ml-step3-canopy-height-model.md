# บท 07 — Step 3: Canopy Height Model (CHM)

> 🎯 **เป้าหมาย:** เข้าใจวิธี rasterize point cloud → 2D grid ที่แต่ละ cell = ความสูงสูงสุดของเรือนยอด
> 📚 **พื้นฐาน:** [บท 06 — Height Normalization](06-ml-step2-height-normalization.md)
> ⏱️ **เวลา:** ~20 นาที

---

## 1. ปัญหา

หลัง Step 2 เรามี **3D point cloud** ที่ Z = height-above-ground

ปัญหา: **คอมพิวเตอร์รู้จัก "image" (2D grid) ดีกว่า "point cloud" (3D scatter)**

หลายเทคนิคการประมวลผลภาพ (segmentation, edge detection, peak finding) ออกแบบมาสำหรับ **raster** เท่านั้น

**ทางออก:** แปลง point cloud → **2D raster** ที่แต่ละ cell = "ความสูงเรือนยอดที่จุดนั้น"

= **Canopy Height Model (CHM)**

---

## 2. หลักการ

```
สำหรับ grid cell (i, j) ที่ขนาด res × res เมตร:
    CHM[i, j] = max(z สำหรับทุก point ที่อยู่ใน cell นี้)
```

หรือพูดง่าย: **"จุดสูงสุดในกริดเซลล์นั้นๆ"**

```
Point Cloud (3D):              CHM (2D):
                                ┌─────────────────┐
   ●            ●               │ 0   8   12  10 0│
     ●●  ●● ●                   │ 0   15  18  9  0│
     ●●●●●●●                    │ 0   20  22  12 0│
     ●●●●●●●                    │ 0   18  17  8  0│
       ●●●●                     │ 0   0   0   0  0│
         ●                      └─────────────────┘
─ ─ ground ─ ─                  (numbers = max Z in m)
                                (raster overhead view)
```

### 2.1 Resolution Choice

- **0.5 m × 0.5 m** (เราใช้) — เหมาะสำหรับต้นไม้
- หากเลือกใหญ่เกิน (>2m) → ต้นเล็กรวมกัน → tree detection ผิด
- หากเลือกเล็กเกิน (<0.2m) → เซลล์ว่างเยอะ → noisy

---

## 3. คณิตศาสตร์/อัลกอริทึม

### 3.1 Max-Z Rasterization

```python
def rasterize_max_z(points, resolution=0.5):
    x_min, y_min = points[:, 0].min(), points[:, 1].min()

    n_cols = ceil((x_max - x_min) / resolution)
    n_rows = ceil((y_max - y_min) / resolution)

    chm = np.full((n_rows, n_cols), -inf)

    # Assign each point to a cell
    col = floor((points[:, 0] - x_min) / resolution)
    row = floor((points[:, 1] - y_min) / resolution)

    # Take max per cell
    np.maximum.at(chm, (row, col), points[:, 2])

    # Empty cells (-inf) → NaN
    chm[np.isinf(chm)] = np.nan
    return chm
```

### 3.2 Pit-free CHM (Phase 2)

**ปัญหาของ max-Z:** บางที่ laser ทะลุ canopy ลงไปถึงพื้น → cell มีจุดต่ำ → "pit" ใน CHM

```
           ●                          ●
          ●●●                        ●●●
         ●  ●           →           ● ↓ ●        ← pit!
        ●    ●                     ●     ●
         ●  ●                       ●   ●
```

**Solution (Khosravipour 2014):** สร้าง CHM หลายชั้นที่ Z threshold ต่างกัน → เลือก max

$$
\text{CHM}_{\text{pit-free}}(x, y) = \max_{t \in T} \text{CHM}_t(x, y)
$$

โดย $T = \{0, 5, 10, 15, 20, 25, 30\}$ m

### 3.3 Phase 1 ของเรา — Morphological Closing

ใช้ **scipy.ndimage.grey_closing** เป็นทดแทน pit-free (ลด pits ระดับเล็ก):

```python
from scipy.ndimage import grey_closing
chm_filled = grey_closing(chm, size=(2, 2))
```

ผลคล้ายกัน (~90%) แต่เร็วและง่ายกว่ามาก

---

## 4. โค้ดของเรา

📂 **`services/ml/pipeline/canopy_height_model.py`**

```python
from dataclasses import dataclass
import numpy as np
from scipy.ndimage import grey_closing

@dataclass(frozen=True)
class ChmTransform:
    """Geo-transform mapping CHM pixel ↔ world (x, y)."""
    x_min: float
    y_min: float
    resolution: float
    n_rows: int
    n_cols: int

def compute_chm_array(
    normalized_points: np.ndarray,
    *,
    resolution: float = 0.5,
    closing_size: int = 2,
    min_height: float = 0.0,
) -> tuple[np.ndarray, ChmTransform]:
    """Compute Canopy Height Model from height-normalized points."""

    # 1. Filter by min_height (skip ground)
    pts = normalized_points[normalized_points[:, 2] >= min_height]

    # 2. Build grid
    x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
    y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
    n_cols = int(np.ceil((x_max - x_min) / resolution)) + 1
    n_rows = int(np.ceil((y_max - y_min) / resolution)) + 1

    # 3. Initialize to -inf for max accumulation
    chm = np.full((n_rows, n_cols), -np.inf, dtype=np.float32)

    # 4. Bin points into cells
    col = np.clip(np.floor((pts[:, 0] - x_min) / resolution).astype(int), 0, n_cols - 1)
    row = np.clip(np.floor((pts[:, 1] - y_min) / resolution).astype(int), 0, n_rows - 1)

    # 5. Max-Z reduction (np.maximum.at handles duplicate indices)
    np.maximum.at(chm, (row, col), pts[:, 2])

    # 6. Empty cells → NaN
    empty_mask = np.isinf(chm)
    chm[empty_mask] = np.nan

    # 7. Pit fill (morphological closing on filled mask)
    if closing_size > 0 and empty_mask.any() and (~empty_mask).any():
        filled = np.where(empty_mask, 0.0, chm).astype(np.float32)
        closed = grey_closing(filled, size=(closing_size, closing_size))
        chm = np.where(empty_mask & (closed > 0), closed, chm)

    transform = ChmTransform(x_min, y_min, resolution, n_rows, n_cols)
    return chm, transform
```

### Performance
- 1M points → CHM 100x100: ~0.5 second
- 10M points → CHM 500x500: ~3 seconds

---

## 5. Visualization

ดู `docs/proposal/figures/fig04_chm.png`:
- Heatmap แสดง height
- เครื่องหมาย × แดง = ตำแหน่ง treetop จริง (ground truth)
- เซลล์สูงสุดในแต่ละ cluster = ยอดต้น

---

## 6. Citation

- **Khosravipour, A. et al. 2014**. "Generating Pit-free Canopy Height Models from Airborne Lidar". *Photogrammetric Engineering & Remote Sensing*, 80(9), 863-872.

---

## 7. ข้อจำกัด + Phase 2

| Phase 1 | Phase 2 plan |
|---|---|
| Morphological closing → pit-fill ระดับเล็ก | True Khosravipour multi-threshold pit-free |
| Fixed 0.5m resolution | Adaptive resolution based on density |
| Single max-Z (no smoothing) | Gaussian smoothing for noisy data |

---

## 8. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไมเปลี่ยน 3D → 2D? เสีย info ไปไหม?**
2. **resolution 0.5 m หมายถึงอะไร?**
3. **"pit" ใน CHM เกิดจากอะไร? ทำไมต้องแก้?**
4. **ChmTransform เก็บอะไรบ้าง? ใช้ทำอะไร?**
5. **ถ้าตั้ง resolution = 5.0 m จะเกิดอะไรขึ้นกับ Step 4 (tree detection)?**

---

## 9. อ่านต่อ

- [บท 08 — Step 4: Tree Segmentation (Watershed)](08-ml-step4-tree-segmentation.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
