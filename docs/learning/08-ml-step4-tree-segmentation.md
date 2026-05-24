# บท 08 — Step 4: Tree Segmentation (Watershed) — แยกต้นไม้ทีละต้น

> 🎯 **เป้าหมาย:** เข้าใจวิธีแยกต้นไม้แต่ละต้นออกจากแปลงเดียวกัน ใช้ Watershed algorithm
> 📚 **พื้นฐาน:** [บท 07 — CHM](07-ml-step3-canopy-height-model.md)
> ⏱️ **เวลา:** ~25 นาที

---

## 1. ปัญหา

หลัง Step 3 เรามี **CHM** — 2D raster ของความสูงเรือนยอด

แต่: CHM = สีเทาที่แสดงความสูง — **ไม่รู้ว่าแต่ละจุดเป็นต้นไหน**

```
CHM (max-Z heatmap):           ต้องการ:
┌──────────────────┐           ┌──────────────────┐
│ ░░░░▓▓▓▓▓░░░▓▓▓▓│           │ ░░░░TTTTT░░░UUUU│
│ ░░░▓▓██▓▓░░▓▓██▓│           │ ░░░TTBBTTT░UU██U│
│ ░░░▓██████░██▓▓▓│   →       │ ░░░TBBBBT░UUU██U│
│ ░░░▓▓██▓▓░░▓▓▓▓░│           │ ░░░TTBBTT░░UU██U│
│ ░░░░▓▓▓░░░░░░▓░░│           │ ░░░░TTT░░░░░░U░░│
└──────────────────┘           └──────────────────┘
"สีเทา = ความสูง"             "T=tree1, U=tree2, B=peak"
```

**ทางออก:** Watershed Segmentation

---

## 2. หลักการ — Watershed

### 2.1 Idea

> **Watershed** จากคำว่า "watershed" = "ลุ่มน้ำ" — เขตที่น้ำไหลเข้าสู่จุดเดียวกัน
>
> **Nature analogy:** นึกภาพ ภูมิประเทศที่ฝนตก → น้ำไหลลงตามแรงโน้มถ่วง → แยกเป็น "ลุ่มน้ำ" ตาม peak

ใน CHM:
- **Peak** = ยอดต้นไม้ (local maximum)
- **Watershed** = ขอบเขตเรือนยอดของต้นนั้น
- **Each peak → 1 tree**

### 2.2 ขั้นตอน

```
1. หา local maxima ใน CHM → markers (1 marker = 1 ต้น)
2. Flood-fill จาก marker ลงเขาตาม gradient
3. ที่ "ลำธาร" ระหว่าง 2 peaks มาเจอกัน = ขอบต้นไม้
4. แต่ละจุดในแปลง ถูก assign tree_id (1..N)
```

### 2.3 Visual

```
CHM gradient:
  Peak A (height 20m)              Peak B (height 18m)
        ●                                ●
      ╱   ╲                            ╱   ╲
    ╱       ╲                        ╱       ╲
  ╱           ╲ ▲ watershed boundary ╱           ╲
 ▔▔▔▔▔▔▔▔▔▔▔▔ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ ▔▔▔▔▔▔▔▔▔▔▔▔
   tree A region              tree B region
```

---

## 3. อัลกอริทึม

### 3.1 Peak Detection

ใช้ `scikit-image.feature.peak_local_max`:

```python
coords = peak_local_max(
    chm,
    min_distance=5,        # peaks ต้องห่างกันอย่างน้อย 5 pixels (≈ 2.5m)
    threshold_abs=4.0,     # ต้องสูงอย่างน้อย 4 m
    labels=mask,           # หาแค่ใน mask (ที่ chm >= min_height)
)
```

**Parameters สำคัญ:**
- `min_distance=5` — เป็น pixels (5 × 0.5m/px = 2.5m) → กันต้นใกล้กันถูกตรวจเป็น 2 ต้น
- `threshold_abs=4.0` — ต้นที่สูงน้อยกว่า 4m → ไม่นับ (เป็นกล้า/พุ่ม)

### 3.2 Watershed

ใช้ `scikit-image.segmentation.watershed`:

```python
from skimage.segmentation import watershed

# Build marker array
markers = np.zeros_like(chm, dtype=int)
for i, (r, c) in enumerate(coords, start=1):
    markers[r, c] = i

# Watershed on -CHM (peaks → basins after negation)
labels = watershed(-chm, markers=markers, mask=mask)
```

**ทำไม `-chm`?** Watershed คิดในแง่ "basin" (จุดต่ำสุด) → negate เพื่อกลับ peak เป็น basin

---

## 4. โค้ดของเรา

📂 **`services/ml/pipeline/tree_segmentation.py`**

```python
import numpy as np
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

def watershed_segmentation(
    chm: np.ndarray,
    *,
    min_height: float = 4.0,
    min_distance: int = 5,
) -> np.ndarray:
    """Watershed on CHM → tree IDs per cell."""

    # 1. Clean: replace NaN with 0
    chm_clean = np.where(np.isnan(chm), 0.0, chm).astype(np.float32)

    # 2. Mask = pixels above min_height
    mask = chm_clean >= min_height
    if not mask.any():
        return np.zeros_like(chm_clean, dtype=np.int32)

    # 3. Find local maxima (= treetops)
    coords = peak_local_max(
        chm_clean,
        min_distance=min_distance,
        threshold_abs=min_height,
        labels=mask.astype(np.int32),
    )
    if len(coords) == 0:
        return np.zeros_like(chm_clean, dtype=np.int32)

    # 4. Build markers
    markers = np.zeros_like(chm_clean, dtype=np.int32)
    for i, (r, c) in enumerate(coords, start=1):
        markers[r, c] = i

    # 5. Watershed
    labels = watershed(-chm_clean, markers=markers, mask=mask)
    return labels.astype(np.int32)
```

### 4.1 Assign Points to Trees

```python
def assign_points_to_trees(
    normalized_points: np.ndarray,
    tree_labels_2d: np.ndarray,
    transform: ChmTransform,
    *,
    min_height: float = 1.5,
) -> np.ndarray:
    """Map each point to a tree ID via XY lookup."""

    out = np.zeros(len(normalized_points), dtype=np.int32)
    x = normalized_points[:, 0]
    y = normalized_points[:, 1]
    z = normalized_points[:, 2]

    # Convert world XY → pixel (row, col)
    row, col = transform.world_to_pixel(x, y)

    # Only assign points above min_height (skip ground/shrubs)
    in_bounds = (
        (row >= 0) & (row < transform.n_rows) &
        (col >= 0) & (col < transform.n_cols) &
        (z >= min_height)
    )

    out[in_bounds] = tree_labels_2d[row[in_bounds], col[in_bounds]]
    return out
```

---

## 5. Output

```python
{
    1: array([(12.3, 45.6, 18.2), ...]),  # tree 1's points
    2: array([(15.1, 47.8, 19.5), ...]),  # tree 2's points
    3: array([(11.8, 43.2, 17.9), ...]),  # tree 3's points
    ...
}
```

---

## 6. Visualization

ดู `docs/proposal/figures/fig05_tree_segmentation.png` — แต่ละต้นมีสีต่างกัน

---

## 7. Citation

- **Roussel, J.-R. et al. 2020**. "lidR: An R package for analysis of Airborne Laser Scanning (ALS) data". *Remote Sensing of Environment*, 251, 112061.
- DOI: [10.1016/j.rse.2020.112061](https://doi.org/10.1016/j.rse.2020.112061)

---

## 8. ข้อจำกัด + Phase 2

### 8.1 Over-segmentation

ถ้า canopy ของต้นใหญ่กว้าง อาจตรวจพบ peak ภายในเรือนยอนเป็น 2-3 peaks → "1 ต้นถูกแบ่งเป็น 3"

**Phase 1 mitigation:**
- ตั้ง `min_distance=5` (= 2.5m) — กันต้นใกล้กัน

**Phase 2:**
- Marker-controlled watershed (Dalponte 2016) — ใช้ priors เรื่องขนาดเรือนยอด
- Deep learning instance segmentation (PointNet++ on point cloud)

### 8.2 Under-segmentation

ต้นที่อยู่ใกล้กันมาก (< 2m) อาจรวมเป็น 1

**Phase 2:** Adaptive `min_distance` ตาม species/density

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

1. **Watershed ใช้แนวคิดอะไรของธรรมชาติ?**
2. **ทำไม `-chm` ใน `watershed(-chm, ...)`?**
3. **`min_distance=5` แปลว่าอะไรในหน่วยเมตร? (resolution = 0.5m)**
4. **Over-segmentation คืออะไร? ระบบเรา mitigate ยังไง?**
5. **`assign_points_to_trees` ทำอะไร?**

---

## 10. อ่านต่อ

- [บท 09 — Step 5: Wood-Leaf Separation](09-ml-step5-wood-leaf-separation.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
