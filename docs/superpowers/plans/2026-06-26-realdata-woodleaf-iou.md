# Real Wood/Leaf IoU Evaluation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a zero-shot evaluation that runs the existing wood/leaf segmenter (PointNet++ + PCA baseline) on real labelled TLS trees and reports wood/leaf/mean IoU per backend, so the report can quote a real-tree IoU instead of synthetic-only.

**Architecture:** One new dependency-light module `pipeline/realdata_eval.py` with two dataset loaders (Wan per-point labels; Shivalik wood-only matching), a dataset-agnostic eval core (`evaluate_cloud`/`evaluate_dataset`), and a CLI `eval-realdata` in `pipeline/main.py`. Reuses `training.metrics.iou_score`, `pipeline.field_eval.load_point_cloud`, and `wood_leaf_separation.WoodLeafSegmenter`. Datasets are downloaded manually and git-ignored.

**Tech Stack:** Python 3.11, NumPy, SciPy (`cKDTree`), Click; pytest. Run everything from `services/ml/` using the venv interpreter `./.venv/Scripts/python.exe`.

**Spec:** [docs/superpowers/specs/2026-06-26-realdata-woodleaf-iou-design.md](../specs/2026-06-26-realdata-woodleaf-iou-design.md)

**Reused APIs (do not reimplement):**
- `from training.metrics import iou_score` → `iou_score(pred, target, positive_class=0) -> float` (empty union → 1.0)
- `from pipeline.field_eval import load_point_cloud` → `load_point_cloud(path, max_points=200_000) -> (N,3) float64` (supports .txt/.xyz/.csv/.ply/.las/.laz; pass a huge `max_points` to disable its internal random decimation)
- `from pipeline import wood_leaf_separation` → `WoodLeafSegmenter(model_path=None, backend="tlsep").segment(points) -> labels` with `WOOD=0`, `LEAF=1`

---

### Task 1: Git-ignore the real-data directory

**Files:**
- Modify: `.gitignore` (repo root)

- [ ] **Step 1: Append the ignore rule**

Add these lines to the end of `.gitignore`:

```gitignore
# Real-world evaluation datasets (downloaded manually, too large to commit)
services/ml/data/realdata/
```

- [ ] **Step 2: Verify it is ignored**

Run: `mkdir -p services/ml/data/realdata && touch services/ml/data/realdata/probe.txt && git status --porcelain services/ml/data/realdata`
Expected: no output (the path is ignored). Then clean up: `rm services/ml/data/realdata/probe.txt`

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(ml): git-ignore data/realdata for downloaded eval datasets

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `load_labelled_cloud` — Wan per-point label loader

**Files:**
- Create: `services/ml/pipeline/realdata_eval.py`
- Test: `services/ml/tests/test_realdata_eval.py`

- [ ] **Step 1: Write the failing test**

Create `services/ml/tests/test_realdata_eval.py`:

```python
"""Tests for real-world wood/leaf IoU evaluation (spec 2026-06-26)."""

from __future__ import annotations

import numpy as np

from pipeline.realdata_eval import load_labelled_cloud


def test_load_labelled_cloud_maps_wood_labels(tmp_path):
    # cols: x y z label   (label 1 == wood, 0 == leaf for this fixture)
    f = tmp_path / "tree.txt"
    f.write_text("0 0 0 1\n1 1 1 0\n2 2 2 1\n")
    points, gt = load_labelled_cloud(f, label_col=3, wood_labels=[1])
    assert points.shape == (3, 3)
    assert points.dtype == np.float64
    assert gt.tolist() == [0, 1, 0]  # label 1 -> wood(0); label 0 -> leaf(1)
    assert gt.dtype == np.uint8
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py -q --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.realdata_eval'`

- [ ] **Step 3: Write minimal implementation**

Create `services/ml/pipeline/realdata_eval.py`:

```python
"""Zero-shot real wood/leaf IoU evaluation (spec 2026-06-26).

Runs the existing wood/leaf segmenter on real labelled TLS trees and reports
per-class IoU. Dataset-specific parsing is isolated in the two loaders; the
eval core is dataset-agnostic.

Classes: WOOD = 0, LEAF = 1 (matches pipeline.wood_leaf_separation).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pipeline.field_eval import load_point_cloud
from training.metrics import iou_score

_NO_DECIMATION = 10**12  # pass as max_points to load every point


def load_labelled_cloud(
    path: str | Path, *, label_col: int, wood_labels: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    """Load XYZ + a per-point wood/leaf label column (Wan-style datasets).

    Args:
        path: whitespace- (.txt/.xyz) or comma- (.csv) separated file
        label_col: column index holding the class label
        wood_labels: label values that mean wood; everything else is leaf

    Returns:
        (points (N,3) float64, gt (N,) uint8 in {0=wood, 1=leaf})
    """
    path = Path(path)
    delimiter = "," if path.suffix.lower() == ".csv" else None
    arr = np.atleast_2d(np.loadtxt(path, delimiter=delimiter))
    points = arr[:, :3].astype(np.float64)
    labels = arr[:, label_col]
    gt = np.where(np.isin(labels, np.asarray(wood_labels, dtype=labels.dtype)), 0, 1)
    return points, gt.astype(np.uint8)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py -q --no-cov`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/realdata_eval.py services/ml/tests/test_realdata_eval.py
git commit -m "feat(ml): load_labelled_cloud for per-point wood/leaf labels (Wan)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `derive_labels_from_woodonly` — Shivalik wood-only matching

**Files:**
- Modify: `services/ml/pipeline/realdata_eval.py`
- Test: `services/ml/tests/test_realdata_eval.py`

- [ ] **Step 1: Write the failing test**

Append to `services/ml/tests/test_realdata_eval.py`:

```python
def test_derive_labels_from_woodonly(tmp_path):
    full = tmp_path / "full.txt"
    full.write_text("0 0 0\n1 0 0\n2 0 0\n3 0 0\n4 0 0\n5 0 0\n")
    wood = tmp_path / "wood.txt"
    wood.write_text("0 0 0\n2 0 0\n4 0 0\n")  # points 0,2,4 are wood
    from pipeline.realdata_eval import derive_labels_from_woodonly

    points, gt = derive_labels_from_woodonly(full, wood, tol=1e-6)
    assert points.shape == (6, 3)
    assert gt.tolist() == [0, 1, 0, 1, 0, 1]  # matched -> wood(0), else leaf(1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py::test_derive_labels_from_woodonly -q --no-cov`
Expected: FAIL — `ImportError: cannot import name 'derive_labels_from_woodonly'`

- [ ] **Step 3: Write minimal implementation**

Append to `services/ml/pipeline/realdata_eval.py`:

```python
def derive_labels_from_woodonly(
    full_path: str | Path, wood_only_path: str | Path, tol: float = 1e-3
) -> tuple[np.ndarray, np.ndarray]:
    """Derive per-point wood/leaf labels by matching against a wood-only cloud.

    Shivalik provides ground truth as a separate file containing only the wood
    points. A full-tree point within `tol` (metres) of any wood-only point is
    labelled wood (0); the rest are leaf (1). Matching uses XYZ only (avoids the
    zero-intensity quirk noted in the dataset's paper). Both clouds are loaded
    in full (no decimation) so the match stays aligned.
    """
    from scipy.spatial import cKDTree

    full = load_point_cloud(full_path, max_points=_NO_DECIMATION)
    wood_only = load_point_cloud(wood_only_path, max_points=_NO_DECIMATION)
    dist, _ = cKDTree(wood_only).query(full, k=1)
    gt = np.where(dist <= tol, 0, 1).astype(np.uint8)
    return full, gt
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py::test_derive_labels_from_woodonly -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/realdata_eval.py services/ml/tests/test_realdata_eval.py
git commit -m "feat(ml): derive_labels_from_woodonly via KDTree matching (Shivalik)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Pure helpers — `_decimate_joint` and `_metrics_from_pred`

**Files:**
- Modify: `services/ml/pipeline/realdata_eval.py`
- Test: `services/ml/tests/test_realdata_eval.py`

- [ ] **Step 1: Write the failing tests**

Append to `services/ml/tests/test_realdata_eval.py`:

```python
def test_decimate_joint_keeps_pairs():
    from pipeline.realdata_eval import _decimate_joint

    n = 1000
    points = np.zeros((n, 3))
    points[:, 0] = np.arange(n)  # x encodes original index
    gt = (np.arange(n) % 3).astype(np.uint8)
    p, g = _decimate_joint(points, gt, max_points=100)
    assert len(g) == 100
    assert p.shape == (100, 3)
    # invariant gt == x % 3 must survive
    assert np.array_equal(g, (p[:, 0].astype(int) % 3).astype(np.uint8))


def test_decimate_joint_noop_when_small():
    from pipeline.realdata_eval import _decimate_joint

    points = np.zeros((5, 3))
    gt = np.array([0, 1, 0, 1, 0], np.uint8)
    p, g = _decimate_joint(points, gt, max_points=100)
    assert len(g) == 5


def test_metrics_from_pred_perfect():
    from pipeline.realdata_eval import _metrics_from_pred

    gt = np.array([0, 0, 1, 1], np.uint8)
    m = _metrics_from_pred(gt.copy(), gt)
    assert m["wood_iou"] == 1.0
    assert m["leaf_iou"] == 1.0
    assert m["mean_iou"] == 1.0
    assert m["accuracy"] == 1.0
    assert m["wood_frac_gt"] == 0.5
    assert m["n_points"] == 4


def test_metrics_from_pred_known_overlap():
    from pipeline.realdata_eval import _metrics_from_pred

    gt = np.array([0, 0, 0, 1], np.uint8)
    pred = np.array([0, 0, 1, 1], np.uint8)
    # wood: inter {0,1}=2, union {0,1,2}=3 -> 2/3 ; leaf: inter {3}=1, union {2,3}=2 -> 1/2
    m = _metrics_from_pred(pred, gt)
    assert m["wood_iou"] == round(2 / 3, 4)
    assert m["leaf_iou"] == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py -q --no-cov`
Expected: FAIL — `ImportError: cannot import name '_decimate_joint'`

- [ ] **Step 3: Write minimal implementation**

Append to `services/ml/pipeline/realdata_eval.py`:

```python
def _decimate_joint(
    points: np.ndarray, gt: np.ndarray, max_points: int, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Jointly subsample points + gt (seeded) so the pairing is preserved."""
    n = len(points)
    if n <= max_points:
        return points, gt
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(n, max_points, replace=False))
    return points[idx], gt[idx]


def _metrics_from_pred(pred: np.ndarray, gt: np.ndarray) -> dict:
    """Per-class IoU + accuracy + class fractions for one tree."""
    pred = np.asarray(pred)
    gt = np.asarray(gt)
    wood_iou = iou_score(pred, gt, positive_class=0)
    leaf_iou = iou_score(pred, gt, positive_class=1)
    return {
        "wood_iou": round(wood_iou, 4),
        "leaf_iou": round(leaf_iou, 4),
        "mean_iou": round((wood_iou + leaf_iou) / 2, 4),
        "accuracy": round(float(np.mean(pred == gt)), 4),
        "wood_frac_gt": round(float(np.mean(gt == 0)), 4),
        "wood_frac_pred": round(float(np.mean(pred == 0)), 4),
        "n_points": int(len(gt)),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py -q --no-cov`
Expected: PASS (all tests so far green)

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/realdata_eval.py services/ml/tests/test_realdata_eval.py
git commit -m "feat(ml): joint decimation + per-class IoU metric helpers

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: `evaluate_cloud` — segment one tree and score it

**Files:**
- Modify: `services/ml/pipeline/realdata_eval.py`
- Test: `services/ml/tests/test_realdata_eval.py`

- [ ] **Step 1: Write the failing test**

Append to `services/ml/tests/test_realdata_eval.py`:

```python
def _toy_tree(seed=0):
    """A vertical wood trunk + a scattered leaf blob (enough points for PCA)."""
    rng = np.random.default_rng(seed)
    z = np.linspace(0, 5, 200)
    trunk = np.column_stack([rng.normal(0, 0.02, 200), rng.normal(0, 0.02, 200), z])
    leaf = rng.normal([0, 0, 5], 0.6, size=(200, 3))
    points = np.vstack([trunk, leaf])
    gt = np.concatenate([np.zeros(200, np.uint8), np.ones(200, np.uint8)])
    return points, gt


def test_evaluate_cloud_returns_metrics(tmp_path):
    from pipeline.realdata_eval import evaluate_cloud

    points, gt = _toy_tree()
    m = evaluate_cloud(points, gt, backend="tlsep")
    assert set(m) == {
        "wood_iou", "leaf_iou", "mean_iou", "accuracy",
        "wood_frac_gt", "wood_frac_pred", "n_points",
    }
    assert 0.0 <= m["mean_iou"] <= 1.0
    assert m["n_points"] == 400


def test_evaluate_cloud_decimates(tmp_path):
    from pipeline.realdata_eval import evaluate_cloud

    points, gt = _toy_tree()
    m = evaluate_cloud(points, gt, backend="tlsep", max_points=150)
    assert m["n_points"] == 150
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py::test_evaluate_cloud_returns_metrics -q --no-cov`
Expected: FAIL — `ImportError: cannot import name 'evaluate_cloud'`

- [ ] **Step 3: Write minimal implementation**

Append to `services/ml/pipeline/realdata_eval.py`:

```python
def evaluate_cloud(
    points: np.ndarray,
    gt: np.ndarray,
    *,
    backend: str = "tlsep",
    model_path: str | None = None,
    max_points: int = 200_000,
) -> dict:
    """Zero-shot: segment one tree with `backend` and score against `gt`."""
    from pipeline import wood_leaf_separation

    points = np.asarray(points, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.uint8)
    points, gt = _decimate_joint(points, gt, max_points)

    segmenter = wood_leaf_separation.WoodLeafSegmenter(model_path=model_path, backend=backend)
    if backend == "pointnet":
        segmenter.load()
    pred = np.asarray(segmenter.segment(points), dtype=np.uint8)
    return _metrics_from_pred(pred, gt)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/realdata_eval.py services/ml/tests/test_realdata_eval.py
git commit -m "feat(ml): evaluate_cloud — zero-shot segment + score one tree

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: `evaluate_dataset` — aggregate across trees and backends

**Files:**
- Modify: `services/ml/pipeline/realdata_eval.py`
- Test: `services/ml/tests/test_realdata_eval.py`

- [ ] **Step 1: Write the failing test** (monkeypatch `evaluate_cloud` for deterministic aggregation)

Append to `services/ml/tests/test_realdata_eval.py`:

```python
def test_evaluate_dataset_aggregates(monkeypatch):
    import pipeline.realdata_eval as re

    def fake_eval(points, gt, *, backend, model_path=None, max_points=200_000):
        return {
            "wood_iou": 0.80, "leaf_iou": 0.60, "mean_iou": 0.70,
            "accuracy": 0.9, "wood_frac_gt": 0.5, "wood_frac_pred": 0.5,
            "n_points": len(gt),
        }

    monkeypatch.setattr(re, "evaluate_cloud", fake_eval)
    trees = [
        ("t1", np.zeros((4, 3)), np.array([0, 0, 1, 1], np.uint8)),
        ("t2", np.zeros((4, 3)), np.array([0, 1, 0, 1], np.uint8)),
    ]
    result = re.evaluate_dataset(trees, backends=["tlsep"])
    assert len(result["per_tree"]) == 2
    s = result["summary"]["tlsep"]
    assert s["n_trees"] == 2
    assert s["mean_wood_iou"] == 0.8
    assert s["mean_leaf_iou"] == 0.6
    assert s["mean_iou"] == 0.7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py::test_evaluate_dataset_aggregates -q --no-cov`
Expected: FAIL — `AttributeError: ... has no attribute 'evaluate_dataset'`

- [ ] **Step 3: Write minimal implementation**

Append to `services/ml/pipeline/realdata_eval.py`:

```python
def evaluate_dataset(
    trees: list[tuple[str, np.ndarray, np.ndarray]],
    *,
    backends: Sequence[str],
    model_path: str | None = None,
    max_points: int = 200_000,
) -> dict:
    """Run `evaluate_cloud` over every (tree_id, points, gt) for each backend.

    Returns {"per_tree": [...], "summary": {backend: {n_trees, mean_*_iou}}}.
    """
    per_tree: list[dict] = []
    summary: dict[str, dict] = {}
    for backend in backends:
        wood, leaf, mean = [], [], []
        for tree_id, points, gt in trees:
            m = evaluate_cloud(
                points, gt, backend=backend, model_path=model_path, max_points=max_points
            )
            per_tree.append({"tree_id": tree_id, "backend": backend, **m})
            wood.append(m["wood_iou"])
            leaf.append(m["leaf_iou"])
            mean.append(m["mean_iou"])
        summary[backend] = {
            "n_trees": len(trees),
            "mean_wood_iou": round(float(np.mean(wood)), 4) if wood else 0.0,
            "mean_leaf_iou": round(float(np.mean(leaf)), 4) if leaf else 0.0,
            "mean_iou": round(float(np.mean(mean)), 4) if mean else 0.0,
        }
    return {"per_tree": per_tree, "summary": summary}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/realdata_eval.py services/ml/tests/test_realdata_eval.py
git commit -m "feat(ml): evaluate_dataset — aggregate IoU per backend

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: CLI command `eval-realdata`

**Files:**
- Modify: `services/ml/pipeline/main.py` (add a new Click command after `process`)
- Test: `services/ml/tests/test_realdata_eval.py`

- [ ] **Step 1: Write the failing test** (Click `CliRunner` on a temp Wan-style dir)

Append to `services/ml/tests/test_realdata_eval.py`:

```python
def test_cli_eval_realdata_wan(tmp_path):
    import json

    from click.testing import CliRunner

    from pipeline.main import cli

    # two toy labelled trees: cols x y z label, wood label = 0
    root = tmp_path / "wan"
    root.mkdir()
    for name, seed in [("a.txt", 1), ("b.txt", 2)]:
        pts, gt = _toy_tree(seed)
        rows = np.column_stack([pts, gt.astype(float)])
        np.savetxt(root / name, rows)

    out = tmp_path / "wan_iou.json"
    res = CliRunner().invoke(
        cli,
        [
            "eval-realdata", "--dataset", "wan", "--root", str(root),
            "--backend", "tlsep", "--out", str(out),
            "--label-col", "3", "--wood-labels", "0",
        ],
    )
    assert res.exit_code == 0, res.output
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["summary"]["tlsep"]["n_trees"] == 2
    assert len(data["per_tree"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py::test_cli_eval_realdata_wan -q --no-cov`
Expected: FAIL — `No such command 'eval-realdata'` (exit_code != 0)

- [ ] **Step 3: Write minimal implementation**

In `services/ml/pipeline/main.py`, add this command immediately after the `process` command function (before `if __name__ == "__main__":`). `json`, `click`, and `cli` are already imported/defined at the top of the file.

```python
@cli.command("eval-realdata")
@click.option("--dataset", type=click.Choice(["wan", "shivalik"]), required=True)
@click.option("--root", required=True, type=click.Path(exists=True))
@click.option("--backend", "backends", default="tlsep",
              help="comma-separated backends: tlsep,pointnet")
@click.option("--model", "model_path", type=click.Path(), default=None,
              help="PointNet++ checkpoint (required for backend pointnet)")
@click.option("--out", "output_path", type=click.Path(), default="realdata_iou.json")
@click.option("--max-points", default=200_000, type=int)
@click.option("--label-col", default=3, type=int, help="(wan) label column index")
@click.option("--wood-labels", default="0",
              help="(wan) comma-separated label values that mean wood")
def eval_realdata(dataset: str, root: str, backends: str, model_path: str | None,
                  output_path: str, max_points: int, label_col: int,
                  wood_labels: str) -> None:
    """Zero-shot wood/leaf IoU on a real labelled dataset (wan | shivalik)."""
    from pipeline import realdata_eval

    root_path = Path(root)
    backend_list = [b.strip() for b in backends.split(",") if b.strip()]
    trees: list[tuple[str, Any, Any]] = []

    if dataset == "wan":
        wood_vals = [float(x) for x in wood_labels.split(",") if x.strip()]
        files = sorted([*root_path.glob("*.txt"), *root_path.glob("*.csv")])
        for f in files:
            try:
                pts, gt = realdata_eval.load_labelled_cloud(
                    f, label_col=label_col, wood_labels=wood_vals
                )
            except Exception as exc:  # noqa: BLE001 - skip unreadable file, keep going
                click.echo(f"skip {f.name}: {exc}")
                continue
            trees.append((f.stem, pts, gt))
    else:  # shivalik: pair "<stem>.las" with wood-only "<stem>_wood.las"
        for f in sorted([*root_path.glob("*.las"), *root_path.glob("*.laz")]):
            if f.stem.endswith("_wood"):
                continue
            wood_only = f.with_name(f"{f.stem}_wood{f.suffix}")
            if not wood_only.exists():
                click.echo(f"skip {f.name}: missing wood-only file {wood_only.name}")
                continue
            pts, gt = realdata_eval.derive_labels_from_woodonly(f, wood_only)
            trees.append((f.stem, pts, gt))

    if not trees:
        raise click.ClickException(f"no trees found under {root_path}")

    result = realdata_eval.evaluate_dataset(
        trees, backends=backend_list, model_path=model_path, max_points=max_points
    )
    Path(output_path).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for backend, s in result["summary"].items():
        click.echo(
            f"[{backend}] trees={s['n_trees']} "
            f"wood_iou={s['mean_wood_iou']} leaf_iou={s['mean_leaf_iou']} "
            f"mean_iou={s['mean_iou']}"
        )
    click.echo(f"OK - output written to: {output_path}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m pytest tests/test_realdata_eval.py::test_cli_eval_realdata_wan -q --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/main.py services/ml/tests/test_realdata_eval.py
git commit -m "feat(ml): eval-realdata CLI (wan + shivalik) for real wood/leaf IoU

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full Python test suite**

Run: `cd services/ml && PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m pytest -q --no-cov`
Expected: all tests pass (previous suite + the new `test_realdata_eval.py` tests), 0 failures

- [ ] **Step 2: Lint the new/changed files**

Run: `cd services/ml && ./.venv/Scripts/python.exe -m ruff check pipeline/realdata_eval.py pipeline/main.py tests/test_realdata_eval.py`
Expected: `All checks passed!`
If ruff reports issues, fix them inline and re-run until clean.

- [ ] **Step 3: Commit any lint fixes**

```bash
git add -A
git commit -m "style(ml): ruff clean for realdata eval

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
(Skip this commit if there was nothing to fix.)

---

## Manual run (after datasets are downloaded — not part of automated tests)

> These produce the numbers for the report. They require the datasets in
> `services/ml/data/realdata/` and (for pointnet) the trained checkpoint.

**Phase 1 — Wan 2021** (Dryad `10.5061/dryad.rfj6q5799`): inspect one file to confirm
`--label-col` and which value is wood, then:
```
cd services/ml && PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m pipeline.main \
  eval-realdata --dataset wan --root data/realdata/wan2021 \
  --backend tlsep,pointnet --model <path/to/woodleaf_pn2.pt> \
  --label-col <N> --wood-labels <V> --out wan_iou.json
```

**Phase 2 — Shivalik 2026** (Zenodo `10.5281/zenodo.15362444`): confirm the wood-only
file naming, adjust the `_wood` suffix in the `shivalik` branch of `eval_realdata` if
it differs, then:
```
cd services/ml && PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m pipeline.main \
  eval-realdata --dataset shivalik --root data/realdata/shivalik \
  --backend tlsep,pointnet --model <path/to/woodleaf_pn2.pt> --out shivalik_iou.json
```
Then update [DATASET_SECTION.md](../../proposal/DATASET_SECTION.md) with the real IoU
numbers (PointNet++ vs PCA; for Shivalik also vs the bundled LeWoS/TLSeparation/CANUPO/RF).

---

## Self-Review (completed by plan author)

- **Spec coverage:** §3.1 loaders → Tasks 2,3. §3.2 eval core → Tasks 4,5,6. §3.3 CLI → Task 7. §5 error handling → Task 7 (skip-on-read-error; missing wood-only) + `iou_score` empty-union rule. §6 testing → tests in every task, all synthetic/temp, no network. §2/§7 zero-shot only, datasets git-ignored → Task 1 + manual-run section. Acceptance §8 → Task 8.
- **Placeholder scan:** Concrete `<N>`/`<V>`/`<path>` only in the *manual run* section, which is intentionally dataset-dependent and runs after download; all automated tasks contain complete code and exact commands.
- **Type consistency:** `load_labelled_cloud(path, *, label_col, wood_labels)`, `derive_labels_from_woodonly(full_path, wood_only_path, tol)`, `evaluate_cloud(points, gt, *, backend, model_path, max_points)`, `evaluate_dataset(trees, *, backends, model_path, max_points)` and the `_metrics_from_pred` dict keys are used identically in the CLI and tests. `WoodLeafSegmenter(model_path=, backend=).segment()` matches the real API. `gt` is `uint8 {0,1}` throughout.
