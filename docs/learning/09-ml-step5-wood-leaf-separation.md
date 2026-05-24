# บท 09 — Step 5: Wood-Leaf Separation (แยกลำต้น/กิ่ง จากใบ)

> 🎯 **เป้าหมาย:** เข้าใจวิธีจำแนกจุดใน point cloud ว่าเป็น "wood" (ลำต้น/กิ่ง) หรือ "leaf" (ใบ)
> 📚 **พื้นฐาน:** [บท 08 — Tree Segmentation](08-ml-step4-tree-segmentation.md)
> ⏱️ **เวลา:** ~25 นาที

---

## 1. ปัญหา

หลัง Step 4 เรามี **point cloud ของแต่ละต้น** — รู้แล้วว่า "เป็นของต้นไหน" แต่ภายในต้น 1 ต้นมีทั้ง:

- 🪵 **Wood** — ลำต้น (trunk) + กิ่งใหญ่ (branches) — เป็นที่เก็บคาร์บอนหลัก
- 🍃 **Leaf** — ใบ (มีคาร์บอนน้อยกว่า)

ปัญหา: ขั้นต่อไป (Step 6 — QSM) ต้องการ **เฉพาะ wood points** เพื่อวัด DBH + Volume

> 💡 **ทำไมไม่นับใบ:** DBH หมายถึง diameter ของลำต้น — ถ้านับใบเข้าไปด้วย จะวัด "diameter ของพุ่ม" ผิดหมด

---

## 2. หลักการ — Local Geometry Features

### 2.1 Insight

> **ลำต้น/กิ่ง = เป็นเส้น (linear)** → จุด neighbors อยู่ในแนวยาว
> **ใบ = เป็นแผ่น (planar)** หรือ **กระจัดกระจาย (scatter)** → จุด neighbors กระจาย

หาความแตกต่างได้จาก **eigenvalues ของ covariance matrix** ของจุด neighbors

### 2.2 PCA Eigenvalues

สำหรับแต่ละจุด:
1. หา K nearest neighbors
2. คำนวณ covariance matrix ของ neighbors
3. Eigen decompose → eigenvalues $\lambda_0 \geq \lambda_1 \geq \lambda_2$

**Features:**

$$
\text{linearity} = \frac{\lambda_0 - \lambda_1}{\lambda_0}
\quad\quad\quad
\text{planarity} = \frac{\lambda_1 - \lambda_2}{\lambda_0}
\quad\quad\quad
\text{sphericity} = \frac{\lambda_2}{\lambda_0}
$$

> 💡 **Intuition:**
> - **Linearity สูง** = neighbors อยู่ในแนวเดียว → wood
> - **Planarity สูง** = neighbors อยู่บนระนาบ → leaves
> - **Sphericity สูง** = neighbors กระจายทุกทิศ → noise/foliage

### 2.3 Decision Rule (Phase 1)

```python
is_wood = (linearity > 0.45) AND (planarity < 0.50)
        OR (verticality > 0.55)   # additional: ลำต้นแนวตั้ง
```

---

## 3. คณิตศาสตร์ — Local Covariance + Eigendecomposition

### 3.1 ขั้นตอน

สำหรับแต่ละจุด $p_i = (x_i, y_i, z_i)$:

**Step A: หา K neighbors (K = 15-20)**

```python
nbrs = KDTree.query(p_i, k=K)  # K nearest indices
```

**Step B: คำนวณ covariance**

$$
\bar{p} = \frac{1}{K}\sum_{j=1}^{K} p_j
$$

$$
C = \frac{1}{K} \sum_{j=1}^{K} (p_j - \bar{p})(p_j - \bar{p})^T
$$

C เป็น $3 \times 3$ symmetric matrix

**Step C: Eigendecompose**

$$
C \vec{v}_k = \lambda_k \vec{v}_k, \quad k \in \{0, 1, 2\}
$$

โดย $\lambda_0 \geq \lambda_1 \geq \lambda_2 \geq 0$

**Step D: คำนวณ features**

```
linearity  = (λ₀ - λ₁) / λ₀
planarity  = (λ₁ - λ₂) / λ₀
verticality = |v₂.z|     # z-component of smallest eigenvector
```

**Step E: Classify**

```
is_wood = (linearity > τ_L) AND (planarity < τ_P)
        OR (verticality > τ_V)
```

### 3.2 ทำไม K = 15-20

- K ต่ำ (~5) → noisy (sensitive to single outlier point)
- K สูง (~50) → smear feature, ขอบ wood/leaf หยาบ
- K = 15-20 = sweet spot สำหรับ TLS data density

---

## 4. โค้ดของเรา

📂 **`services/ml/pipeline/wood_leaf_separation.py`**

```python
import numpy as np
from scipy.spatial import cKDTree

WOOD = 0
LEAF = 1

def segment_wood_leaf(
    points: np.ndarray,
    *,
    k_neighbors: int = 15,
    linearity_min: float = 0.45,
    planarity_max: float = 0.50,
    verticality_boost_min: float = 0.55,
) -> np.ndarray:
    """Classify each point as wood (0) or leaf (1)."""

    n = len(points)
    if n < k_neighbors:
        return np.full(n, WOOD, dtype=np.int8)

    # 1. KD-tree
    tree = cKDTree(points)
    _, nbr_idx = tree.query(points, k=k_neighbors)

    # 2. Gather neighborhoods (vectorized)
    nbrs = points[nbr_idx]                    # (N, K, 3)
    centered = nbrs - nbrs.mean(axis=1, keepdims=True)  # (N, K, 3)

    # 3. Batched covariance: (N, 3, 3)
    cov = np.einsum("nki,nkj->nij", centered, centered) / k_neighbors

    # 4. Eigendecomposition (single call for values + vectors)
    eigvals, eigvecs = np.linalg.eigh(cov)
    # eigh returns ascending; flip to descending
    lam = eigvals[:, ::-1]
    lam0 = lam[:, 0]
    eps = 1e-9

    # 5. Features
    linearity = (lam[:, 0] - lam[:, 1]) / (lam0 + eps)
    planarity = (lam[:, 1] - lam[:, 2]) / (lam0 + eps)
    principal = eigvecs[:, :, -1]              # vector for largest eigenvalue
    verticality = np.abs(principal[:, 2])

    # 6. Decision
    is_wood = (
        ((linearity >= linearity_min) & (planarity <= planarity_max))
        | (verticality >= verticality_boost_min)
    )

    labels = np.full(n, LEAF, dtype=np.int8)
    labels[is_wood] = WOOD
    return labels
```

### Performance
- 20K points/tree: ~0.5 sec (vectorized eigh)
- 100K points/tree: ~3 sec

---

## 5. Phase 2 — PointNet++ Deep Learning

### 5.1 ทำไมต้อง Deep Learning

Rule-based ของ Phase 1:
- ✅ ทำงานได้ (~85-90% accuracy บน clean data)
- ❌ พลาดที่ขอบเขต (กิ่งบาง/ใบหนา)
- ❌ ไม่จัดการ noise ดี

**PointNet++:** Neural network สำหรับ point cloud โดยตรง — เรียนรู้ features จาก data

### 5.2 Architecture

```
Input: (N, 3) point cloud
       ↓
Set Abstraction layer 1: sampling + grouping + PointNet
       ↓
Set Abstraction layer 2: sampling + grouping + PointNet
       ↓
Feature Propagation: interpolate back to N points
       ↓
Output: (N, 2) — softmax(wood, leaf)
```

### 5.3 Training (Phase 2)

- Dataset: annotated forest LiDAR (เช่น Demol 2021 + NEON)
- Loss: cross-entropy + Dice loss
- Target IoU: ≥ 0.70

---

## 6. Citation

- **Vicari, M.B. et al. 2019**. "TLSeparation — A Python library for tree segmentation". Inspired our rule-based approach.
- **Qi, C.R. et al. 2017**. "PointNet++: Deep Hierarchical Feature Learning on Point Sets in a Metric Space". *NeurIPS*. — Phase 2 deep learning.

---

## 7. ข้อจำกัด

| Phase 1 | Phase 2 |
|---|---|
| ขอบเขตหยาบ | PointNet++ smoother |
| Sensitive ต่อ noise | DL robust ต่อ noise |
| ต้อง tune thresholds | DL เรียนรู้ thresholds เอง |
| Speed: ~0.5s/tree | Slower แต่แม่นกว่า |

---

## 8. Visualization

ดู `docs/proposal/figures/fig06_wood_leaf.png` — wood สีน้ำตาล, leaf สีเขียว

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

1. **Linearity vs Planarity vs Sphericity — แต่ละ feature บอกอะไร?**
2. **ทำไม K = 15 ไม่ใช่ K = 5 หรือ K = 50?**
3. **"Verticality boost" เพิ่มเข้ามาเพื่ออะไร?**
4. **ทำไม Step 5 ต้องทำหลัง Step 4 (per-tree)?**
5. **PointNet++ ดีกว่า rule-based ตรงไหน?**

---

## 10. อ่านต่อ

- [บท 10 — Step 6: QSM (วัด DBH, Height, Volume)](10-ml-step6-qsm.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
