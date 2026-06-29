# Wood/Leaf Real-Data Experiments — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable same-environment wood/leaf training on real (Wan) data with more data + synthetic augmentation, run a 4-variant matrix, and self-report full per-class metrics — per the advisor's guidance.

**Architecture:** Reuse `training/train_woodleaf.py` (flags only — no new runner). Add two pure helpers (`_iou_triple`, `_augment_with_synthetic`), a full held-out report (`evaluate_full`), a `--augment-synthetic` flag, and converter `--n-off/--per` knobs for a bigger regen. Plus a results-log doc + recipe.

**Tech Stack:** Python 3.11, NumPy, PyTorch (GPU on Colab), pytest. Run ML commands from `services/ml/` with `./.venv/Scripts/python.exe`.

**Spec:** [docs/superpowers/specs/2026-06-29-woodleaf-realdata-experiments-design.md](../specs/2026-06-29-woodleaf-realdata-experiments-design.md)

**Reused APIs:** `training.metrics.iou_score(pred, target, positive_class)`, `training.woodleaf_dataset.build_woodleaf_dataset(n_samples, n_points, seed0) -> (x f32 (N,P,3), y i64 (N,P))`, `training.realdata_dataset.load_wan_plot(path, *, label_col, n_off, per)`. Class convention WOOD=0, LEAF=1.

---

### Task 1: `_iou_triple` helper (pure)

**Files:**
- Modify: `services/ml/training/train_woodleaf.py`
- Test: `services/ml/tests/test_woodleaf_training.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_woodleaf_training.py`

```python
def test_iou_triple_known_values():
    pytest.importorskip("torch")  # train_woodleaf imports torch at module load
    from training.train_woodleaf import _iou_triple

    gt = np.array([WOOD, WOOD, WOOD, LEAF])
    pred = np.array([WOOD, WOOD, LEAF, LEAF])
    # wood: inter {0,1}=2, union {0,1,2}=3 -> 2/3 ; leaf: inter {3}=1, union {2,3}=2 -> 1/2
    wood, leaf, mean = _iou_triple(pred, gt)
    assert wood == round(2 / 3, 10) or abs(wood - 2 / 3) < 1e-9
    assert abs(leaf - 0.5) < 1e-9
    assert abs(mean - (2 / 3 + 0.5) / 2) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py::test_iou_triple_known_values -q --no-cov`
Expected: FAIL — `ImportError: cannot import name '_iou_triple'`

- [ ] **Step 3: Write minimal implementation** — in `training/train_woodleaf.py`, add immediately after the `_class_weights` function (before the `@torch.no_grad()` `evaluate`):

```python
def _iou_triple(preds: np.ndarray, gts: np.ndarray) -> tuple[float, float, float]:
    """Pooled per-point (wood_iou, leaf_iou, mean_iou) over flat label arrays."""
    wood = iou_score(preds, gts, positive_class=WOOD)
    leaf = iou_score(preds, gts, positive_class=1 - WOOD)
    return wood, leaf, (wood + leaf) / 2.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py::test_iou_triple_known_values -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/training/train_woodleaf.py services/ml/tests/test_woodleaf_training.py
git commit -m "feat(ml): _iou_triple pooled wood/leaf/mean helper

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `evaluate_full` (full held-out report)

**Files:**
- Modify: `services/ml/training/train_woodleaf.py`
- Test: `services/ml/tests/test_woodleaf_training.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_woodleaf_training.py`

```python
def test_evaluate_full_reports_per_class_metrics():
    pytest.importorskip("torch")
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    from training.train_woodleaf import evaluate_full

    class ConstWood(torch.nn.Module):
        """Always predicts class 0 (wood) for every point."""
        def forward(self, x):
            b, n, _ = x.shape
            logits = torch.zeros(b, n, 2)
            logits[..., 0] = 1.0  # argmax over last dim -> 0
            return logits

    x = torch.zeros(2, 4, 3)
    y = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]])  # 4 wood, 4 leaf
    loader = DataLoader(TensorDataset(x, y), batch_size=2)
    m = evaluate_full(ConstWood(), loader, "cpu")
    assert set(m) == {"wood_iou", "leaf_iou", "mean_iou", "accuracy"}
    # pred all wood: wood inter=4 union=8 ->0.5 ; leaf inter=0 union=4 ->0.0 ; acc 4/8=0.5
    assert m["wood_iou"] == 0.5
    assert m["leaf_iou"] == 0.0
    assert m["mean_iou"] == 0.25
    assert m["accuracy"] == 0.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py::test_evaluate_full_reports_per_class_metrics -q --no-cov`
Expected: FAIL — `ImportError: cannot import name 'evaluate_full'`

- [ ] **Step 3: Write minimal implementation** — in `training/train_woodleaf.py`, add immediately after the existing `evaluate` function:

```python
@torch.no_grad()
def evaluate_full(model, loader, device) -> dict:
    """Pooled per-point wood/leaf/mean IoU + accuracy over a loader."""
    model.eval()
    preds, gts = [], []
    for x, y in loader:
        p = model(x.to(device)).argmax(dim=-1).cpu().numpy().reshape(-1)
        preds.append(p)
        gts.append(y.numpy().reshape(-1))
    if not preds:
        return {"wood_iou": 0.0, "leaf_iou": 0.0, "mean_iou": 0.0, "accuracy": 0.0}
    pf = np.concatenate(preds)
    gf = np.concatenate(gts)
    wood, leaf, mean = _iou_triple(pf, gf)
    return {
        "wood_iou": round(wood, 4),
        "leaf_iou": round(leaf, 4),
        "mean_iou": round(mean, 4),
        "accuracy": round(float((pf == gf).mean()), 4),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py::test_evaluate_full_reports_per_class_metrics -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/training/train_woodleaf.py services/ml/tests/test_woodleaf_training.py
git commit -m "feat(ml): evaluate_full — pooled wood/leaf/mean + accuracy report

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `_augment_with_synthetic` helper

**Files:**
- Modify: `services/ml/training/train_woodleaf.py`
- Test: `services/ml/tests/test_woodleaf_training.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_woodleaf_training.py`

```python
def test_augment_with_synthetic_concatenates():
    pytest.importorskip("torch")
    from training.train_woodleaf import _augment_with_synthetic

    x = np.zeros((3, 64, 3), dtype=np.float32)
    y = np.zeros((3, 64), dtype=np.int64)
    ax, ay = _augment_with_synthetic(x, y, n=2, seed=123)
    assert ax.shape == (5, 64, 3)
    assert ay.shape == (5, 64)
    assert ax.dtype == np.float32
    assert ay.dtype == np.int64
    # original samples preserved at the front
    assert np.array_equal(ax[:3], x)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py::test_augment_with_synthetic_concatenates -q --no-cov`
Expected: FAIL — `ImportError: cannot import name '_augment_with_synthetic'`

- [ ] **Step 3: Write minimal implementation** — in `training/train_woodleaf.py`, add immediately after `_iou_triple` (from Task 1):

```python
def _augment_with_synthetic(
    x: np.ndarray, y: np.ndarray, n: int, seed: int = 50_000
) -> tuple[np.ndarray, np.ndarray]:
    """Append `n` synthetic samples (matching point count) to a real (npz) set.

    seed0 is set high to avoid overlapping the synthetic train (0) / val (10_000) seeds.
    """
    sx, sy = build_woodleaf_dataset(n_samples=n, n_points=x.shape[1], seed0=seed)
    x_out = np.concatenate([x, sx.astype(np.float32)], axis=0)
    y_out = np.concatenate([y, sy.astype(np.int64)], axis=0)
    return x_out, y_out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py::test_augment_with_synthetic_concatenates -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/training/train_woodleaf.py services/ml/tests/test_woodleaf_training.py
git commit -m "feat(ml): _augment_with_synthetic — mix synthetic into real train set

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Wire augmentation + final report + `--augment-synthetic` into `train()`

**Files:**
- Modify: `services/ml/training/train_woodleaf.py`

No new unit test (integration wiring); verified by ruff + the existing trainer smoke tests + a tiny synthetic CLI smoke in Step 4.

- [ ] **Step 1: Add `_loader_from_arrays` and refactor `_npz_loader`** — replace the existing `_npz_loader` function:

```python
def _loader_from_arrays(x, y, batch_size, shuffle):
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


def _npz_loader(path, batch_size, shuffle):
    """Loader from a converter .npz holding x:(N,P,3) float32 + y:(N,P) int64."""
    data = np.load(path)
    return _loader_from_arrays(
        data["x"].astype(np.float32), data["y"].astype(np.int64), batch_size, shuffle
    )
```

- [ ] **Step 2: Replace the npz branch in `train()`** — replace these lines:

```python
    if args.train_npz:
        if not args.val_npz:
            raise SystemExit("--val-npz is required when --train-npz is given")
        print(f"[train] real data: train={args.train_npz}  val/held-out={args.val_npz}")
        train_loader = _npz_loader(args.train_npz, args.batch_size, True)
        val_loader = _npz_loader(args.val_npz, args.batch_size, False)
```

with:

```python
    if args.train_npz:
        if not args.val_npz:
            raise SystemExit("--val-npz is required when --train-npz is given")
        data = np.load(args.train_npz)
        x = data["x"].astype(np.float32)
        y = data["y"].astype(np.int64)
        if args.augment_synthetic > 0:
            x, y = _augment_with_synthetic(x, y, args.augment_synthetic)
            print(f"[train] augmented with {args.augment_synthetic} synthetic samples")
        print(f"[train] real data: train={args.train_npz} ({len(x)} samples)  "
              f"val/held-out={args.val_npz}")
        train_loader = _loader_from_arrays(x, y, args.batch_size, True)
        val_loader = _npz_loader(args.val_npz, args.batch_size, False)
```

- [ ] **Step 3: Add the final held-out report** — in `train()`, find the end of the function:

```python
    print(f"[done] best val wood IoU = {best_iou:.4f}  (target >= 0.70)")
    return best_iou
```

replace with (reload the best checkpoint, then print full per-class metrics):

```python
    print(f"[done] best val wood IoU = {best_iou:.4f}  (target >= 0.70)")
    best_ckpt = torch.load(out_path, map_location=device)
    model.load_state_dict(best_ckpt["state_dict"])
    final = evaluate_full(model, val_loader, device)
    print(f"[held-out] wood_iou={final['wood_iou']} leaf_iou={final['leaf_iou']} "
          f"mean_iou={final['mean_iou']} accuracy={final['accuracy']}")
    return best_iou
```

- [ ] **Step 4: Add the CLI flag** — in `build_arg_parser()`, add after the `--class-weight` argument:

```python
    p.add_argument("--augment-synthetic", type=int, default=0,
                   help="add N synthetic samples to the (npz) training set as augmentation")
```

- [ ] **Step 5: Verify ruff + existing trainer tests + a tiny CLI smoke**

```bash
cd services/ml
./.venv/Scripts/python.exe -m ruff check training/train_woodleaf.py
./.venv/Scripts/python.exe -m pytest tests/test_woodleaf_training.py -q --no-cov
# synthetic CLI smoke: trains 1 epoch on the synthetic generator (no npz) and must print [held-out]
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m training.train_woodleaf \
  --n-train 4 --n-val 2 --n-points 256 --epochs 1 --batch-size 2 --out /tmp/smoke.pt 2>&1 | tail -5
```
Expected: ruff clean; trainer tests pass; the smoke run prints a `[held-out] wood_iou=... leaf_iou=... mean_iou=... accuracy=...` line and exits 0.

- [ ] **Step 6: Commit**

```bash
git add services/ml/training/train_woodleaf.py
git commit -m "feat(ml): --augment-synthetic + final held-out wood/leaf/mean report

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Converter `--n-off` / `--per` knobs (bigger regen)

**Files:**
- Modify: `services/ml/training/realdata_dataset.py`

- [ ] **Step 1: Add `n_off`/`per` to `build()`** — replace the `build` signature line:

```python
def build(
    plot_paths: list[str | Path],
    out_train: str | Path,
    out_test: str | Path,
    *,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    frac: float = 0.7,
    buffer: float = 2.5,
    label_col: int = 6,
) -> dict:
```

with:

```python
def build(
    plot_paths: list[str | Path],
    out_train: str | Path,
    out_test: str | Path,
    *,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    frac: float = 0.7,
    buffer: float = 2.5,
    label_col: int = 6,
    n_off: int = 3000,
    per: int = 1000,
) -> dict:
```

- [ ] **Step 2: Forward them to `load_wan_plot`** — replace this line inside `build`:

```python
        pts, lab = load_wan_plot(path, label_col=label_col)
```

with:

```python
        pts, lab = load_wan_plot(path, label_col=label_col, n_off=n_off, per=per)
```

- [ ] **Step 3: Add the CLI args** — in `_build_arg_parser()`, add after the `--label-col` argument:

```python
    p.add_argument("--n-off", type=int, default=3000, help="seek offsets across each plot file")
    p.add_argument("--per", type=int, default=1000, help="contiguous lines read per offset")
```

- [ ] **Step 4: Pass args in `__main__`** — replace the `build(...)` call under `if __name__ == "__main__":`:

```python
    stats = build(
        args.plots, args.out_train, args.out_test,
        tile=args.tile, n_points=args.n_points, min_pts=args.min_pts,
        frac=args.frac, buffer=args.buffer, label_col=args.label_col,
    )
```

with:

```python
    stats = build(
        args.plots, args.out_train, args.out_test,
        tile=args.tile, n_points=args.n_points, min_pts=args.min_pts,
        frac=args.frac, buffer=args.buffer, label_col=args.label_col,
        n_off=args.n_off, per=args.per,
    )
```

- [ ] **Step 5: Verify ruff + converter tests**

```bash
cd services/ml
./.venv/Scripts/python.exe -m ruff check training/realdata_dataset.py
./.venv/Scripts/python.exe -m pytest tests/test_realdata_dataset.py -q --no-cov
```
Expected: ruff clean; 4 converter tests pass.

- [ ] **Step 6: Commit**

```bash
git add services/ml/training/realdata_dataset.py
git commit -m "feat(ml): converter --n-off/--per knobs for larger real-data regen

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Regenerate the bigger Wan dataset (local) + record counts

**Files:** none (produces git-ignored npz under `data/realdata/`)

- [ ] **Step 1: Run the converter with bigger sampling**

```bash
cd services/ml && PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m training.realdata_dataset \
  --plots data/realdata/wan2021/reference_pc_White_Birch.txt \
          data/realdata/wan2021/reference_pc_Dahurian_Larch.txt \
          data/realdata/wan2021/reference_pc_Chinese_scholar_tree.txt \
  --out-train data/realdata/wan_train.npz --out-test data/realdata/wan_test.npz \
  --n-off 10000 --per 1500
```
Expected: prints a stats dict with `train_samples` substantially larger than the previous 295 (record the actual number — used in the results log). Writes the two `.npz`.

- [ ] **Step 2: Sanity-check the npz**

```bash
cd services/ml && ./.venv/Scripts/python.exe -c "
import numpy as np
for n in ('wan_train','wan_test'):
    d=np.load(f'data/realdata/{n}.npz'); x,y=d['x'],d['y']
    print(n, x.shape, 'labels', np.unique(y).tolist(), 'wood_frac', round(float(np.mean(y==0)),3),
          'MB', round((x.nbytes+y.nbytes)/1e6,1))
"
```
Expected: train shape (N, 2048, 3) with N >> 295; labels [0, 1]; wood_frac ~0.2–0.3; size still tens of MB (Colab-uploadable). No commit (npz is git-ignored).

---

### Task 7: Results log doc

**Files:**
- Create: `docs/ml/WOODLEAF_RESULTS.md`

- [ ] **Step 1: Write the results log**

```markdown
# Wood/Leaf Segmentation — Results Log

> เก็บผลทุก variant (ตามคำแนะนำอาจารย์ "เก็บผลไว้ทุกแบบ แม้ผลจะไม่ดี").
> ทุกตัวเลขเป็น IoU บนชุดทดสอบที่ระบุ (held-out, กันข้อมูลรั่วแบบ spatial สำหรับ Wan).

## Synthetic (held-out synthetic test)
| method | wood IoU | leaf IoU | mean IoU |
|---|---|---|---|
| PCA heuristic (`tlsep`) | 0.769 | – | – |
| PointNet++ (`pointnet`) | 0.978 | – | – |

## Real TLS — Wan 2021 (held-out, spatial split + buffer)

### Prior runs (synthetic-trained → real)
| run | init | augment | class-weight | wood IoU | leaf IoU | mean IoU |
|---|---|---|---|---|---|---|
| zero-shot | synthetic-only | – | – | ~0.18 | ~0.62 | ~0.33 |
| fine-tune | synthetic ckpt | – | none | ~0.19 | ~0.63 | ~0.41 |
| fine-tune + CW | synthetic ckpt | – | auto | ~0.24 | ~0.07 | ~0.16 |

### Same-environment matrix (bigger Wan data, from-scratch) — fill from Colab `[held-out]` line
| # | init | augment-synthetic | class-weight | #train tiles | wood IoU | leaf IoU | mean IoU |
|---|---|---|---|---|---|---|---|
| 1 | scratch | 0 | none | _ | _ | _ | _ |
| 2 | scratch | 0 | auto | _ | _ | _ | _ |
| 3 | scratch | 200 | none | _ | _ | _ | _ |
| 4 | scratch | 200 | auto | _ | _ | _ | _ |

> วิธีกรอก: รันแต่ละ variant บน Colab (ดู docs/ml/FINETUNE_REALDATA.md) แล้วก็อปเลขจากบรรทัด
> `[held-out] wood_iou=... leaf_iou=... mean_iou=...` มาใส่ในแถวที่ตรงกัน
```

- [ ] **Step 2: Commit**

```bash
git add docs/ml/WOODLEAF_RESULTS.md
git commit -m "docs(ml): wood/leaf results log (all variants)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Colab recipe for the 4-variant matrix

**Files:**
- Modify: `docs/ml/FINETUNE_REALDATA.md`

- [ ] **Step 1: Append a new section** to the end of `docs/ml/FINETUNE_REALDATA.md`:

```markdown

## Same-environment experiments (train+test on real Wan, 4 variants)

Per advisor guidance: train/test on the **same real environment** with more data,
use synthetic only as **augmentation**, and **keep every result**.

### Step A — regenerate a bigger real training set (local)
```bash
cd services/ml && python -m training.realdata_dataset \
  --plots data/realdata/wan2021/reference_pc_White_Birch.txt \
          data/realdata/wan2021/reference_pc_Dahurian_Larch.txt \
          data/realdata/wan2021/reference_pc_Chinese_scholar_tree.txt \
  --out-train data/realdata/wan_train.npz --out-test data/realdata/wan_test.npz \
  --n-off 10000 --per 1500
```
Upload the two `.npz` to Colab (no checkpoint needed — these are from-scratch runs).

### Step B — run the 4 variants on Colab (GPU)
```python
# 1) from-scratch, no class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --epochs 60 --lr 1e-3 --out wan_v1.pt
# 2) from-scratch, class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --class-weight auto --epochs 60 --lr 1e-3 --out wan_v2.pt
# 3) from-scratch + synthetic augmentation, no class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --augment-synthetic 200 --epochs 60 --lr 1e-3 --out wan_v3.pt
# 4) from-scratch + synthetic augmentation, class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --augment-synthetic 200 --class-weight auto --epochs 60 --lr 1e-3 --out wan_v4.pt
```

### Step C — record results
Each run ends with a line like:
```
[held-out] wood_iou=0.31 leaf_iou=0.55 mean_iou=0.43 accuracy=0.62
```
Copy those numbers into the matrix table in `docs/ml/WOODLEAF_RESULTS.md` (one row per variant).
```

- [ ] **Step 2: Commit**

```bash
git add docs/ml/FINETUNE_REALDATA.md
git commit -m "docs(ml): Colab recipe for 4-variant same-environment experiments

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: Full verification

**Files:** none

- [ ] **Step 1: Full ML suite + ruff**

```bash
cd services/ml
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m pytest -q --no-cov
./.venv/Scripts/python.exe -m ruff check training/ tests/
```
Expected: all tests pass (previous suite + 3 new trainer tests); ruff clean. Fix any issue and re-run until green.

- [ ] **Step 2: Commit any fixes** (skip if none)

```bash
git add -A
git commit -m "style(ml): ruff clean for real-data experiments

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (by plan author)

- **Spec coverage:** §3.1 converter knobs → Task 5 (+ regen Task 6). §3.2 augmentation → Task 3 + wired Task 4. §3.3 full report (`_iou_triple` + `evaluate_full`) → Tasks 1, 2 + wired Task 4. §3.4 results log → Task 7. §3.5 recipe → Task 8. §6 testing → Tasks 1–3 (TDD) + Task 9 (full suite). §8 acceptance → Tasks 5/6 (knobs+regen), 4 (augment+report), 7, 8, 9.
- **Placeholder scan:** Underscores `_` in the WOODLEAF_RESULTS.md table are intentional empty result slots filled after Colab runs (documented in Step note), not plan placeholders. The `[held-out] ... 0.31/0.55/...` numbers in the recipe are illustrative format examples, labelled as such. All code steps contain complete code.
- **Type consistency:** `_iou_triple(preds, gts) -> (wood, leaf, mean)` used by `evaluate_full`; `_augment_with_synthetic(x, y, n, seed) -> (x, y)` used in `train()`; `_loader_from_arrays(x, y, batch_size, shuffle)` used by `_npz_loader` and the npz branch. `build(..., n_off, per)` forwards to `load_wan_plot(..., n_off=, per=)` (existing params). Flag `--augment-synthetic` → `args.augment_synthetic`. Consistent throughout.
