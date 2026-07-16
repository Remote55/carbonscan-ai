# PointNet++ Independent Real-Data Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง PointNet++ checkpoint ที่มี provenance ครบ, freeze ก่อนเปิด external labels และตัดสินด้วย blind segmentation cohort + locked Demol downstream gate โดยคง `tlsep` เป็น default จนกว่าจะได้ `PROMOTE_POINTNET`

**Architecture:** ใช้ machine-readable protocol เป็น contract กลาง แล้วต่อ workflow ห้าช่วง: deterministic Wan build → three-seed training + reproducibility rerun → checkpoint freeze → guarded external fetch → paired segmentation/downstream evaluation. Formal point-estimate gate ใช้ `pipeline.provenance.evaluate_promotion()` เดิม ส่วน full-precision metrics, paired bootstrap และ four-state verdict อยู่ในโมดูลใหม่ที่ไม่เปลี่ยน production default อัตโนมัติ

**Tech Stack:** Python 3.11+, NumPy 1.26+, SciPy 1.13+, PyTorch 2.3+, Open3D 0.18+, Click 8.1+, HTTPX 0.27+, Pytest 8.2+, Git/GitHub Actions, RTX 4060 8 GB สำหรับ real training

## Global Constraints

- ตอบและเขียนคำอธิบายผู้ใช้เป็นภาษาไทย; technical identifiers ใช้ English
- `tlsep` เป็น production baseline; PointNet++ เป็น `Experimental` จนกว่าจะผ่าน gate
- Raw Wan/Demol/Zenodo data, NPZ และ `.pt` checkpoints ห้ามเข้า Git
- Cohort A DOI `10.5281/zenodo.6831378` ห้ามดาวน์โหลดก่อน freeze manifest ถูก commit
- Wan ใช้ 3 plots, `n_off=10000`, `per=1500`, tile 2.5 m, 2,048 points, min 1,024, train fraction 0.70, buffer 2.5 m, resampling seed 0
- Training ใช้ scratch + synthetic 200, no class weights, 60 epochs, batch 8, Adam `1e-3`, weight decay `1e-4`, StepLR step 20 gamma 0.5
- Training seeds คือ `20260716`, `20260717`, `20260718`; tie เลือก seed ต่ำกว่า
- PointNet formal inference ใช้ window 2.5 m, stride 1.25 m, model input 2,048, query chunk 1,024 และ prediction coverage 100%
- Demol ใช้ matched 65 trees, deterministic 20,000-point view, sampling seed 0 และ QSM seed 0
- Formal metrics ใช้ค่า full precision; rounding ใช้เฉพาะ presentation
- Bootstrap ใช้ 10,000 paired tree resamples, seed `20260716`, percentile 95% CI
- External/data/hash/provenance/coverage failure ต้อง fail closed เป็น `INVALID_EVIDENCE`
- Evaluator ห้ามเปลี่ยน default; promotion เป็น PR แยกหลัง verdict `PROMOTE_POINTNET`
- ทำ TDD: เขียน test ให้ fail → รันยืนยัน failure → implement ขั้นต่ำ → รันยืนยัน pass → commit

---

## File Structure

### New files

- `docs/evidence/pointnet_independent_eval/protocol.json` — precommitted machine contract
- `services/ml/training/evidence_protocol.py` — protocol validation and typed access
- `services/ml/training/evidence_training.py` — deterministic runtime, canonical state hash, run selection and freeze validation
- `services/ml/pipeline/pointnet_tiled.py` — strict context/query tiled inference with no fallback
- `services/ml/pipeline/external_tree_dataset.py` — guarded Zenodo fetch, PCD pairing and dataset manifest
- `services/ml/pipeline/evidence_metrics.py` — full-precision metrics, bootstrap intervals and four-state verdict
- `services/ml/pipeline/demol_eval.py` — paired Demol loader and downstream metrics
- `services/ml/pipeline/independent_eval.py` — end-to-end paired evaluator and artifact writer
- `services/ml/scripts/pointnet_evidence.py` — `prepare-wan`, `train`, `freeze`, `fetch-external`, `evaluate` CLI
- `services/ml/tests/test_evidence_protocol.py`
- `services/ml/tests/test_evidence_training.py`
- `services/ml/tests/test_pointnet_tiled.py`
- `services/ml/tests/test_external_tree_dataset.py`
- `services/ml/tests/test_evidence_metrics.py`
- `services/ml/tests/test_demol_eval.py`
- `services/ml/tests/test_independent_eval.py`
- `scripts/review_pointnet_evidence.py` — import reviewed result into the core truth manifest without changing default
- `scripts/tests/test_review_pointnet_evidence.py`

### Modified files

- `services/ml/pipeline/provenance.py` — streaming file hashes and canonical JSON utilities
- `services/ml/training/realdata_dataset.py` — tile/split provenance and honest terminology
- `services/ml/training/train_woodleaf.py` — deterministic seed, metadata-rich checkpoints and full-precision run record
- `services/ml/pipeline/wood_leaf_separation.py` — strict normalized-logit method used by tiled inference
- `services/ml/tests/test_provenance.py`
- `services/ml/tests/test_realdata_dataset.py`
- `services/ml/tests/test_evidence_gate.py`
- `scripts/sync_truth.py`
- `scripts/tests/test_sync_truth.py`
- `.github/workflows/ci-ml.yml`
- `docs/DOCUMENT_STATUS.md`
- `docs/evidence/core_demo_manifest.json` — updated only after reviewed real result
- `docs/PROJECT_SPEC.md`, `docs/ml/PIPELINE.md`, `docs/ml/WOODLEAF_RESULTS.md` — generated truth + limitations after result
- `services/ml/training/realdata_dataset.py`, `docs/ml/FINETUNE_REALDATA.md` — remove unprovable leakage-free wording
- `services/ml/notebooks/experiment_g3_pointnet_volume.py` — mark historical experiment as confounded and non-gating

## Interfaces Locked by This Plan

- `pipeline.provenance.sha256_file(path: str | Path, chunk_size: int = 1048576) -> str`
- `pipeline.provenance.sha256_ndarray(array: np.ndarray, dtype: str) -> str`
- `pipeline.provenance.write_canonical_json(path: str | Path, payload: dict[str, Any]) -> None`
- `training.evidence_protocol.load_protocol(path: str | Path) -> dict[str, Any]`
- `training.realdata_dataset.build_evidence_dataset(plot_paths: list[str | Path], out_train: str | Path, out_dev: str | Path, out_manifest: str | Path, *, protocol: dict[str, Any], repo_root: str | Path) -> dict[str, Any]`
- `training.evidence_training.set_global_determinism(seed: int) -> dict[str, Any]`
- `training.evidence_training.canonical_state_dict_sha256(state_dict: dict[str, Any]) -> str`
- `training.evidence_training.select_winning_run(records: list[dict[str, Any]]) -> dict[str, Any]`
- `training.evidence_training.validate_reproducibility(first: dict[str, Any], rerun: dict[str, Any]) -> None`
- `pipeline.pointnet_tiled.TiledPrediction(labels: np.ndarray, logits: np.ndarray, coverage: np.ndarray)`
- `pipeline.pointnet_tiled.predict_tiled(points: np.ndarray, infer_logits: Callable[[np.ndarray], np.ndarray], *, window_size_m: float, stride_m: float, model_points: int, query_points: int, seed: int) -> TiledPrediction`
- `pipeline.external_tree_dataset.fetch_external_cohort(protocol: dict[str, Any], freeze_manifest: str | Path, checkpoint: str | Path, destination: str | Path, manifest_out: str | Path, repo_root: str | Path, client: Any | None = None) -> dict[str, Any]`
- `pipeline.external_tree_dataset.load_external_trees(root: str | Path, manifest: dict[str, Any], point_loader: Callable[[Path], np.ndarray] | None = None) -> list[tuple[str, np.ndarray, np.ndarray]]`
- `pipeline.evidence_metrics.segmentation_metrics(pred: np.ndarray, gt: np.ndarray) -> dict[str, Any]`
- `pipeline.evidence_metrics.paired_percentile_ci(baseline: dict[str, float], candidate: dict[str, float], *, resamples: int, seed: int, confidence: float) -> dict[str, float]`
- `pipeline.evidence_metrics.decide_independent_verdict(*, evidence_valid: bool, formal_decision: PromotionDecision, intervals: dict[str, dict[str, float]]) -> dict[str, Any]`
- `pipeline.demol_eval.load_demol_cohort(root: str | Path, *, max_points: int, seed: int) -> list[dict[str, Any]]`
- `pipeline.demol_eval.evaluate_demol_pair(trees: list[dict[str, Any]], *, baseline_predictor: Callable[[np.ndarray], np.ndarray], candidate_predictor: Callable[[np.ndarray], np.ndarray], qsm_func: Callable[[np.ndarray, int], Any], qsm_seed: int) -> dict[str, Any]`
- `pipeline.independent_eval.run_independent_evaluation(protocol_path: str | Path, freeze_manifest: str | Path, checkpoint: str | Path, external_root: str | Path, external_manifest: str | Path, demol_root: str | Path, evidence_dir: str | Path, repo_root: str | Path) -> dict[str, Any]`

---

### Task 1: Make Evidence Hashing Safe for Multi-GB Inputs

**Files:**
- Modify: `services/ml/pipeline/provenance.py`
- Modify: `services/ml/tests/test_provenance.py`

**Interfaces:**
- Produces: streaming `sha256_file()`, typed `sha256_ndarray()`, stable `write_canonical_json()`
- Consumed by: Tasks 2–16

- [ ] **Step 1: Write failing streaming/canonical tests**

Add to `services/ml/tests/test_provenance.py`:

```python
import hashlib
import json

from pipeline.provenance import sha256_file, sha256_ndarray, write_canonical_json


def test_sha256_file_streams_without_path_read_bytes(tmp_path, monkeypatch):
    path = tmp_path / "large.bin"
    payload = b"treeq" * 400_000
    path.write_bytes(payload)

    def forbidden_read_bytes(self):
        raise AssertionError("sha256_file must stream")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read_bytes)
    assert sha256_file(path, chunk_size=8192) == hashlib.sha256(payload).hexdigest()


def test_sha256_ndarray_includes_shape_and_dtype():
    a = np.array([[1, 2], [3, 4]], dtype=np.int64)
    assert sha256_ndarray(a, "<i8") == sha256_ndarray(a.copy(), "<i8")
    assert sha256_ndarray(a, "<i8") != sha256_ndarray(a.reshape(1, 4), "<i8")
    assert sha256_ndarray(a, "<i8") != sha256_ndarray(a, "<f8")


def test_write_canonical_json_has_stable_bytes(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_canonical_json(first, {"b": 2, "a": {"z": 1}})
    write_canonical_json(second, {"a": {"z": 1}, "b": 2})
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text(encoding="utf-8")) == {"a": {"z": 1}, "b": 2}
```

- [ ] **Step 2: Run tests and verify failure**

Run from `services/ml`:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/test_provenance.py -q -o addopts=''
```

Expected: FAIL because `sha256_ndarray`, `write_canonical_json` and the `chunk_size` argument do not exist

- [ ] **Step 3: Implement streaming and canonical helpers**

Replace `sha256_file` and add helpers in `services/ml/pipeline/provenance.py`:

```python
def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_ndarray(array: np.ndarray, dtype: str) -> str:
    stable = np.asarray(array, dtype=np.dtype(dtype), order="C")
    header = json.dumps(
        {"dtype": stable.dtype.str, "shape": list(stable.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\0")
    digest.update(stable.tobytes(order="C"))
    return digest.hexdigest()


def write_canonical_json(path: str | Path, payload: dict[str, Any]) -> None:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    Path(path).write_text(encoded, encoding="utf-8", newline="\n")
```

- [ ] **Step 4: Run tests and verify pass**

Run the Step 2 command.

Expected: all `test_provenance.py` tests PASS

- [ ] **Step 5: Commit**

```powershell
git add services/ml/pipeline/provenance.py services/ml/tests/test_provenance.py
git commit -m "feat(ml): stream evidence hashes"
```

---

### Task 2: Add the Machine-Readable Precommitted Protocol

**Files:**
- Create: `docs/evidence/pointnet_independent_eval/protocol.json`
- Create: `services/ml/training/evidence_protocol.py`
- Create: `services/ml/tests/test_evidence_protocol.py`

**Interfaces:**
- Consumes: `sha256_file()` from Task 1
- Produces: validated protocol dict with exact keys and values used by every later command

- [ ] **Step 1: Write failing protocol tests**

Create `services/ml/tests/test_evidence_protocol.py`:

```python
import json
from pathlib import Path

import pytest

from training.evidence_protocol import load_protocol


PROTOCOL = Path(__file__).resolve().parents[3] / "docs/evidence/pointnet_independent_eval/protocol.json"


def test_checked_in_protocol_locks_blind_contract():
    p = load_protocol(PROTOCOL)
    assert p["training"]["seeds"] == [20260716, 20260717, 20260718]
    assert p["training"]["synthetic_samples"] == 200
    assert p["wan"]["n_off"] == 10000
    assert p["wan"]["per"] == 1500
    assert p["pointnet_inference"] == {
        "window_size_m": 2.5,
        "stride_m": 1.25,
        "model_points": 2048,
        "query_points": 1024,
        "seed": 0,
    }
    assert p["external"]["record_id"] == 6831378
    assert p["external"]["expected_trees"] == 10
    assert p["demol"]["expected_trees"] == 65
    assert p["statistics"] == {"resamples": 10000, "seed": 20260716, "confidence": 0.95}


def test_protocol_rejects_changed_seed(tmp_path):
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    payload["training"]["seeds"] = [1, 2, 3]
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="training.seeds"):
        load_protocol(path)
```

- [ ] **Step 2: Run tests and verify failure**

```powershell
cd services/ml
..\..\.venv\Scripts\python.exe -m pytest tests/test_evidence_protocol.py -q -o addopts=''
```

Expected: FAIL because module and protocol file do not exist

- [ ] **Step 3: Create the exact protocol JSON**

Create `docs/evidence/pointnet_independent_eval/protocol.json` with:

```json
{
  "schema_version": "1",
  "experiment_id": "pointnet-independent-eval-2026-07-16",
  "baseline": {
    "backend": "tlsep",
    "k_neighbors": 20,
    "linearity_min": 0.45,
    "planarity_max": 0.5,
    "verticality_boost_min": 0.55
  },
  "wan": {
    "source_record": "10.5061/dryad.rfj6q5799",
    "files": [
      "reference_pc_White_Birch.txt",
      "reference_pc_Dahurian_Larch.txt",
      "reference_pc_Chinese_scholar_tree.txt"
    ],
    "n_off": 10000,
    "per": 1500,
    "tile_m": 2.5,
    "points_per_tile": 2048,
    "min_points_per_tile": 1024,
    "train_fraction": 0.7,
    "buffer_m": 2.5,
    "resampling_seed": 0
  },
  "training": {
    "seeds": [20260716, 20260717, 20260718],
    "initialization": "scratch",
    "synthetic_samples": 200,
    "synthetic_seed_start": 50000,
    "class_weight": "none",
    "epochs": 60,
    "batch_size": 8,
    "learning_rate": 0.001,
    "weight_decay": 0.0001,
    "scheduler_step": 20,
    "scheduler_gamma": 0.5,
    "selection_metric": "macro_tile_wood_iou"
  },
  "pointnet_inference": {
    "window_size_m": 2.5,
    "stride_m": 1.25,
    "model_points": 2048,
    "query_points": 1024,
    "seed": 0
  },
  "external": {
    "provider": "Zenodo",
    "record_id": 6831378,
    "doi": "10.5281/zenodo.6831378",
    "license": "CC-BY-4.0",
    "expected_trees": 10,
    "concatenation_order": ["wood", "leaf"]
  },
  "demol": {
    "record_id": 4557401,
    "expected_trees": 65,
    "max_points": 20000,
    "sampling_seed": 0,
    "qsm_seed": 0,
    "qsm_algorithm": "ransac_dbh_maxz_height_taper_volume"
  },
  "statistics": {
    "resamples": 10000,
    "seed": 20260716,
    "confidence": 0.95
  }
}
```

- [ ] **Step 4: Implement strict protocol validation**

Create `services/ml/training/evidence_protocol.py` with a `load_protocol()` that parses JSON, checks exact schema/version/experiment ID, compares every fixed value above, rejects unknown top-level sections, and returns the validated dict. Use explicit equality checks such as:

```python
EXPECTED_SEEDS = [20260716, 20260717, 20260718]
EXPECTED_TOP_LEVEL = {
    "schema_version", "experiment_id", "baseline", "wan", "training",
    "pointnet_inference", "external", "demol", "statistics",
}


def _require_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} must equal {expected!r}, got {actual!r}")


def load_protocol(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    _require_equal(set(payload), EXPECTED_TOP_LEVEL, "protocol sections")
    _require_equal(payload["schema_version"], "1", "schema_version")
    _require_equal(payload["experiment_id"], "pointnet-independent-eval-2026-07-16", "experiment_id")
    _require_equal(payload["training"]["seeds"], EXPECTED_SEEDS, "training.seeds")
    _require_equal(payload["external"]["record_id"], 6831378, "external.record_id")
    _require_equal(payload["external"]["expected_trees"], 10, "external.expected_trees")
    _require_equal(payload["demol"]["expected_trees"], 65, "demol.expected_trees")
    _require_equal(payload["statistics"], {"resamples": 10000, "seed": 20260716, "confidence": 0.95}, "statistics")
    return payload
```

Continue explicit checks for every JSON field; do not silently default a missing value.

- [ ] **Step 5: Run tests and commit**

Run the Step 2 command; expected all PASS.

```powershell
git add docs/evidence/pointnet_independent_eval/protocol.json services/ml/training/evidence_protocol.py services/ml/tests/test_evidence_protocol.py
git commit -m "feat(ml): lock PointNet evidence protocol"
```

---

### Task 3: Regenerate Wan Data with Immutable Tile/Split Provenance

**Files:**
- Modify: `services/ml/training/realdata_dataset.py`
- Modify: `services/ml/tests/test_realdata_dataset.py`

**Interfaces:**
- Consumes: validated protocol, streaming/canonical hash helpers
- Produces: `build_evidence_dataset()` plus train/dev NPZ and stable manifest

- [ ] **Step 1: Add failing tests for split records and path privacy**

Add tests that create two small labelled Wan-style text fixtures, call `build_evidence_dataset()` twice, and assert:

```python
def test_build_evidence_dataset_records_every_tile_without_absolute_paths(tmp_path):
    protocol = _tiny_protocol()
    sources = _write_tiny_wan_plots(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    build_evidence_dataset(
        sources, first / "train.npz", first / "dev.npz", first / "manifest.json",
        protocol=protocol, repo_root=tmp_path,
    )
    build_evidence_dataset(
        sources, second / "train.npz", second / "dev.npz", second / "manifest.json",
        protocol=protocol, repo_root=tmp_path,
    )

    a = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    b = json.loads((second / "manifest.json").read_text(encoding="utf-8"))
    assert a == b
    assert {row["split"] for row in a["tiles"]} <= {"train", "dev", "dropped_buffer"}
    assert all("selected_indices_sha256" in row for row in a["tiles"])
    assert str(tmp_path) not in json.dumps(a)
```

Also assert train/dev tile IDs are disjoint and the old docstring no longer contains `leakage-free` or `no tree appears`.

- [ ] **Step 2: Run tests and verify failure**

```powershell
cd services/ml
..\..\.venv\Scripts\python.exe -m pytest tests/test_realdata_dataset.py -q -o addopts=''
```

Expected: FAIL because `build_evidence_dataset()` and tile records do not exist

- [ ] **Step 3: Add deterministic split assignment**

Add:

```python
def spatial_split_assignments(
    centers: np.ndarray, *, frac: float, buffer: float, axis: int = 0
) -> np.ndarray:
    c = np.asarray(centers, dtype=np.float64)[:, axis]
    cut = float(c.min()) + frac * float(c.max() - c.min())
    split = np.full(len(c), "dropped_buffer", dtype="<U14")
    split[c < (cut - buffer / 2.0)] = "train"
    split[c > (cut + buffer / 2.0)] = "dev"
    return split
```

Refactor `spatial_split()` to index this array so existing API remains compatible.

- [ ] **Step 4: Capture tile identities and selected-index hashes**

Create a private `_tile_samples_with_records()` that preserves grid coordinates, stable source-local tile IDs and hashes selected seek-sample indices with `sha256_ndarray(sel, "<i8")`. Keep public `tile_samples()` returning its existing three values for backward compatibility.

Each record must contain exactly:

```python
{
    "tile_id": f"{source_id}:{gx}:{gy}",
    "source_id": source_id,
    "grid_x": int(gx),
    "grid_y": int(gy),
    "center_x": float(center[0]),
    "center_y": float(center[1]),
    "raw_points": int(len(idx)),
    "selected_indices_sha256": sha256_ndarray(sel, "<i8"),
    "split": split_name,
}
```

- [ ] **Step 5: Implement `build_evidence_dataset()`**

The function must:

1. hash raw source files by streaming;
2. process sources in protocol filename order;
3. write train/dev NPZ;
4. compute NPZ file SHA-256 and canonical `x`/`y` content hashes;
5. write a canonical manifest with logical filenames only;
6. reject empty train/dev splits, duplicate tile IDs, non-binary labels and config mismatch.

Return the same manifest dict written to disk.

- [ ] **Step 6: Run tests and commit**

Run the Step 2 command; expected all PASS.

```powershell
git add services/ml/training/realdata_dataset.py services/ml/tests/test_realdata_dataset.py
git commit -m "feat(ml): record Wan split provenance"
```

---

### Task 4: Add Deterministic Training and Canonical Checkpoint Identity

**Files:**
- Create: `services/ml/training/evidence_training.py`
- Create: `services/ml/tests/test_evidence_training.py`

**Interfaces:**
- Produces: deterministic setup, canonical state hash, winner selection, rerun validation, environment capture
- Consumed by: Task 5 and real training

- [ ] **Step 1: Write failing unit tests**

Create tests:

```python
def test_select_winning_run_uses_macro_iou_then_lower_seed():
    records = [
        {"seed": 20260718, "best_macro_tile_wood_iou": 0.51},
        {"seed": 20260716, "best_macro_tile_wood_iou": 0.51},
        {"seed": 20260717, "best_macro_tile_wood_iou": 0.49},
    ]
    assert select_winning_run(records)["seed"] == 20260716


def test_canonical_state_hash_ignores_mapping_order():
    first = {"b": torch.tensor([2.0]), "a": torch.tensor([[1.0]])}
    second = {"a": torch.tensor([[1.0]]), "b": torch.tensor([2.0])}
    assert canonical_state_dict_sha256(first) == canonical_state_dict_sha256(second)


def test_validate_reproducibility_rejects_metric_or_state_drift():
    first = {"best_epoch": 8, "best_macro_tile_wood_iou": 0.5, "state_dict_sha256": "a" * 64}
    validate_reproducibility(first, dict(first))
    with pytest.raises(ValueError, match="reproducibility"):
        validate_reproducibility(first, {**first, "state_dict_sha256": "b" * 64})
```

- [ ] **Step 2: Run and verify failure**

```powershell
cd services/ml
..\..\.venv\Scripts\python.exe -m pytest tests/test_evidence_training.py -q -o addopts=''
```

Expected: FAIL because the module does not exist

- [ ] **Step 3: Implement deterministic setup**

```python
def set_global_determinism(seed: int) -> dict[str, Any]:
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    return {
        "seed": seed,
        "deterministic_algorithms": True,
        "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
    }
```

- [ ] **Step 4: Implement canonical tensor hashing and selection**

Hash sorted tensor names, dtype, shape and little-endian contiguous bytes. Reject non-tensor values inside `state_dict`. Implement:

```python
def select_winning_run(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("training records are empty")
    return max(records, key=lambda r: (float(r["best_macro_tile_wood_iou"]), -int(r["seed"])))


def validate_reproducibility(first: dict[str, Any], rerun: dict[str, Any]) -> None:
    keys = ("best_epoch", "best_macro_tile_wood_iou", "state_dict_sha256")
    mismatch = [key for key in keys if first.get(key) != rerun.get(key)]
    if mismatch:
        raise ValueError(f"reproducibility mismatch: {mismatch}")
```

Add `capture_training_environment()` returning Python/NumPy/PyTorch/CUDA/cuDNN/GPU versions without a local path.

- [ ] **Step 5: Run tests and commit**

```powershell
git add services/ml/training/evidence_training.py services/ml/tests/test_evidence_training.py
git commit -m "feat(ml): make PointNet training deterministic"
```

---

### Task 5: Produce Metadata-Rich Runs and a Freeze Manifest

**Files:**
- Modify: `services/ml/training/train_woodleaf.py`
- Create: `services/ml/scripts/pointnet_evidence.py`
- Modify: `services/ml/tests/test_evidence_training.py`

**Interfaces:**
- Consumes: Tasks 2–4
- Produces: `prepare-wan`, `train`, `freeze` subcommands; run records and verified freeze manifest

- [ ] **Step 1: Write failing runner tests with injected training function**

Add a test that calls `run_training_matrix()` with a fake `train_one_seed` and asserts calls occur in protocol seed order plus one rerun of the winner:

```python
def test_run_training_matrix_runs_three_seeds_and_reruns_winner(tmp_path):
    calls = []

    def fake_train(seed, output_path):
        calls.append(seed)
        score = {20260716: 0.40, 20260717: 0.55, 20260718: 0.50}[seed]
        return {
            "seed": seed,
            "best_epoch": 12,
            "best_macro_tile_wood_iou": score,
            "state_dict_sha256": str(seed).zfill(64),
            "checkpoint_path": str(output_path),
        }

    result = run_training_matrix(_protocol(), tmp_path, train_one_seed=fake_train)
    assert calls == [20260716, 20260717, 20260718, 20260717]
    assert result["winner"]["seed"] == 20260717
    assert result["reproducible"] is True
```

For the fake rerun, return the same canonical hash as the first winning run.

- [ ] **Step 2: Run and verify failure**

Run `tests/test_evidence_training.py`; expected FAIL because runner APIs do not exist.

- [ ] **Step 3: Refactor the trainer without changing the model architecture**

Modify loader helpers to accept a seeded `torch.Generator`, set `num_workers=0`, and make `train(args)` return a full-precision record. Save checkpoints with:

```python
checkpoint = {
    "schema_version": "2",
    "state_dict": model.state_dict(),
    "num_classes": 2,
    "seed": args.seed,
    "selected_epoch": epoch,
    "dev_metrics": final_metrics,
    "protocol_sha256": args.protocol_sha256,
    "wan_manifest_sha256": args.wan_manifest_sha256,
    "training_git_commit": args.training_git_commit,
}
```

Use `torch.load(checkpoint_path, map_location=device, weights_only=True)` for project-created checkpoints. Keep rounded console output separate from the unrounded record.

- [ ] **Step 4: Implement `run_training_matrix()` and freeze validation**

In `training/evidence_training.py`, add:

```python
def run_training_matrix(protocol, artifact_dir, *, train_one_seed):
    records = []
    for seed in protocol["training"]["seeds"]:
        records.append(train_one_seed(seed, Path(artifact_dir) / f"seed-{seed}.pt"))
    winner = select_winning_run(records)
    rerun = train_one_seed(winner["seed"], Path(artifact_dir) / f"seed-{winner['seed']}-rerun.pt")
    validate_reproducibility(winner, rerun)
    return {"runs": records, "winner": winner, "rerun": rerun, "reproducible": True}
```

`build_freeze_manifest()` must verify protocol, Wan manifest, checkpoint file hash, canonical state hash, clean Git state, training commit and environment before writing tracked `training_runs.json` and `freeze_manifest.json`.

- [ ] **Step 5: Implement the first three CLI subcommands**

`services/ml/scripts/pointnet_evidence.py` must expose:

```text
prepare-wan --protocol --wan-root --artifact-dir --manifest-out --repo-root
train       --protocol --wan-manifest --artifact-dir --repo-root
freeze      --protocol --wan-manifest --artifact-dir --evidence-dir --repo-root
```

Each command returns non-zero on validation failure and prints one ASCII-only JSON summary line.

- [ ] **Step 6: Run focused tests and commit**

```powershell
cd services/ml
..\..\.venv\Scripts\python.exe -m pytest tests/test_evidence_training.py tests/test_realdata_dataset.py -q -o addopts=''
git add training/train_woodleaf.py training/evidence_training.py scripts/pointnet_evidence.py tests/test_evidence_training.py
git commit -m "feat(ml): build reproducible PointNet checkpoints"
```

---

### Task 6: Implement Strict Tiled PointNet++ Inference

**Files:**
- Create: `services/ml/pipeline/pointnet_tiled.py`
- Create: `services/ml/tests/test_pointnet_tiled.py`
- Modify: `services/ml/pipeline/wood_leaf_separation.py`

**Interfaces:**
- Consumes: normalized 2,048-point model callable
- Produces: `predict_tiled()` with labels, averaged logits and per-point coverage

- [ ] **Step 1: Write failing coverage/determinism tests**

```python
def test_predict_tiled_covers_every_point_and_uses_fixed_model_size():
    rng = np.random.default_rng(3)
    points = rng.uniform([0, 0, 0], [5, 5, 8], size=(5000, 3))
    calls = []

    def fake_logits(batch):
        calls.append(batch.copy())
        assert batch.shape == (2048, 3)
        logits = np.zeros((2048, 2), dtype=np.float64)
        logits[:, 0] = batch[:, 2]
        logits[:, 1] = -batch[:, 2]
        return logits

    first = predict_tiled(
        points, fake_logits, window_size_m=2.5, stride_m=1.25,
        model_points=2048, query_points=1024, seed=0,
    )
    second = predict_tiled(
        points, fake_logits, window_size_m=2.5, stride_m=1.25,
        model_points=2048, query_points=1024, seed=0,
    )
    assert np.all(first.coverage >= 1)
    assert np.array_equal(first.labels, second.labels)
    assert np.array_equal(first.coverage, second.coverage)
```

Add tests for sparse windows, overlap averaging, invalid logits shape and a fake segmenter whose tlsep method raises if called.

- [ ] **Step 2: Run and verify failure**

```powershell
cd services/ml
..\..\.venv\Scripts\python.exe -m pytest tests/test_pointnet_tiled.py -q -o addopts=''
```

Expected: FAIL because module does not exist

- [ ] **Step 3: Implement deterministic context/query batches**

For each XY window, stable-sort original indices. Partition them into query chunks of at most 1,024. Put query points first, then select context from remaining window points with a window/chunk-derived NumPy seed; sample with replacement only when needed to reach 2,048. Normalize each batch with `training.woodleaf_dataset.normalize_points()` and accumulate logits only for query positions.

Finish with:

```python
if np.any(coverage == 0):
    missing = int(np.count_nonzero(coverage == 0))
    raise ValueError(f"PointNet tiled inference left {missing} points uncovered")
mean_logits = logits_sum / coverage[:, None]
labels = mean_logits.argmax(axis=1).astype(np.int8)
return TiledPrediction(labels=labels, logits=mean_logits, coverage=coverage)
```

- [ ] **Step 4: Add strict normalized-logit model access**

Add `WoodLeafSegmenter.pointnet_logits(normalized_points)` that requires backend `pointnet`, loads the checkpoint if necessary, requires at least 512 points, returns NumPy logits, and never calls `_segment_tlsep`. Existing `segment()` behavior remains unchanged for non-gating production paths.

- [ ] **Step 5: Run tests and commit**

```powershell
git add services/ml/pipeline/pointnet_tiled.py services/ml/pipeline/wood_leaf_separation.py services/ml/tests/test_pointnet_tiled.py
git commit -m "feat(ml): add strict tiled PointNet inference"
```

---

### Task 7: Guard the Blind External Fetch and Pair PCD Labels

**Files:**
- Create: `services/ml/pipeline/external_tree_dataset.py`
- Create: `services/ml/tests/test_external_tree_dataset.py`
- Modify: `services/ml/scripts/pointnet_evidence.py`

**Interfaces:**
- Consumes: committed freeze manifest and checkpoint identity
- Produces: verified raw files, `external_dataset_manifest.json`, deterministic `(tree_id, points, gt)` list

- [ ] **Step 1: Write failing fail-before-network tests**

```python
def test_fetch_refuses_missing_freeze_before_http(tmp_path):
    called = False

    class Client:
        def get(self, url):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

    with pytest.raises(ValueError, match="freeze"):
        fetch_external_cohort(
            protocol=_protocol(), freeze_manifest=tmp_path / "missing.json",
            checkpoint=tmp_path / "missing.pt", destination=tmp_path / "data",
            manifest_out=tmp_path / "manifest.json", repo_root=tmp_path, client=Client(),
        )
    assert called is False
```

Add fixture tests for MD5 mismatch, expected pair count, duplicate tree IDs, wood-before-leaf concatenation and local SHA-256.

- [ ] **Step 2: Run and verify failure**

Run `tests/test_external_tree_dataset.py`; expected FAIL because module does not exist.

- [ ] **Step 3: Implement freeze guard**

Before an HTTP request, verify:

- freeze file exists and parses;
- checkpoint file SHA-256 matches freeze manifest;
- protocol SHA-256 matches;
- current worktree is clean;
- freeze manifest is tracked at `HEAD` with identical bytes;
- training commit is an ancestor of `HEAD`.

Use explicit `git` subprocess calls with `check=True`; any failure raises `ValueError`.

- [ ] **Step 4: Implement atomic Zenodo downloads**

Query `https://zenodo.org/api/records/6831378`, select exactly 20 `.pcd` files ending `_wood.pcd` or `_leaf.pcd`, stream each to `filename.part`, calculate MD5 and SHA-256 while streaming, compare publisher MD5, then rename to final path. Delete `.part` on failure.

- [ ] **Step 5: Implement deterministic PCD pairing**

Use lazy Open3D loading. Derive tree ID by removing `_wood.pcd`/`_leaf.pcd`; require exactly ten pairs. Preserve row order and concatenate:

```python
points = np.vstack([wood_points, leaf_points]).astype(np.float64)
gt = np.concatenate([
    np.zeros(len(wood_points), dtype=np.uint8),
    np.ones(len(leaf_points), dtype=np.uint8),
])
```

Reject empty files, non-finite coordinates, duplicates and manifest hash drift.

- [ ] **Step 6: Add `fetch-external` CLI and commit**

```text
fetch-external --protocol --freeze-manifest --checkpoint --destination --manifest-out --repo-root
```

```powershell
git add services/ml/pipeline/external_tree_dataset.py services/ml/scripts/pointnet_evidence.py services/ml/tests/test_external_tree_dataset.py
git commit -m "feat(ml): guard blind external cohort fetch"
```

---

### Task 8: Add Full-Precision Metrics, Bootstrap CIs and Four-State Verdict

**Files:**
- Create: `services/ml/pipeline/evidence_metrics.py`
- Create: `services/ml/tests/test_evidence_metrics.py`
- Modify: `services/ml/tests/test_evidence_gate.py`

**Interfaces:**
- Consumes: per-tree baseline/candidate records and existing formal promotion decision
- Produces: exact aggregate metrics, paired percentile intervals and verdict

- [ ] **Step 1: Write failing known-value tests**

```python
def test_segmentation_metrics_keeps_full_precision_and_confusion_counts():
    gt = np.array([0, 0, 0, 1], dtype=np.uint8)
    pred = np.array([0, 0, 1, 1], dtype=np.uint8)
    result = segmentation_metrics(pred, gt)
    assert result["wood_iou"] == 2 / 3
    assert result["leaf_iou"] == 1 / 2
    assert result["confusion"] == {"wood_as_wood": 2, "wood_as_leaf": 1, "leaf_as_wood": 0, "leaf_as_leaf": 1}


def test_paired_percentile_ci_is_seeded():
    baseline = {"a": 0.2, "b": 0.3, "c": 0.4}
    candidate = {"a": 0.4, "b": 0.5, "c": 0.6}
    first = paired_percentile_ci(baseline, candidate, resamples=10000, seed=20260716, confidence=0.95)
    second = paired_percentile_ci(baseline, candidate, resamples=10000, seed=20260716, confidence=0.95)
    assert first == second
    assert first["estimate"] == pytest.approx(0.2)
```

Add one test for each verdict: invalid evidence, failed formal metric, point-estimate-only, promote.

- [ ] **Step 2: Run and verify failure**

Run `tests/test_evidence_metrics.py tests/test_evidence_gate.py`; expected FAIL because new module/statuses do not exist.

- [ ] **Step 3: Implement full-precision aggregation**

Do not call `_metrics_from_pred()` because it rounds. Validate equal one-dimensional lengths, `{0,1}` labels and non-empty arrays. Aggregate macro metrics by arithmetic mean of per-tree metrics; aggregate pooled metrics from summed confusion counts.

- [ ] **Step 4: Implement paired tree bootstrap**

Sort tree IDs, require identical ID sets, sample integer row indices with replacement into shape `(resamples, n_trees)`, calculate mean candidate-minus-baseline delta per resample and return estimate/lower/upper at 2.5/97.5 percentiles for confidence 0.95.

- [ ] **Step 5: Implement verdict mapping**

```python
def decide_independent_verdict(*, evidence_valid, formal_decision, intervals):
    if not evidence_valid:
        return {"verdict": "INVALID_EVIDENCE", "promote": False}
    if not formal_decision.promote:
        return {"verdict": "FAIL_METRICS", "promote": False}
    strong = (
        intervals["wood_iou_delta"]["lower"] > 0
        and intervals["dbh_abs_error_delta"]["upper"] <= 0
        and intervals["height_abs_error_delta"]["upper"] <= 0
        and intervals["volume_ape_delta"]["upper"] <= 0
    )
    if not strong:
        return {"verdict": "POINT_ESTIMATE_PASS_ONLY", "promote": False}
    return {"verdict": "PROMOTE_POINTNET", "promote": True}
```

- [ ] **Step 6: Run tests and commit**

```powershell
git add services/ml/pipeline/evidence_metrics.py services/ml/tests/test_evidence_metrics.py services/ml/tests/test_evidence_gate.py
git commit -m "feat(ml): quantify independent evidence uncertainty"
```

---

### Task 9: Build the Paired Demol Downstream Evaluator

**Files:**
- Create: `services/ml/pipeline/demol_eval.py`
- Create: `services/ml/tests/test_demol_eval.py`

**Interfaces:**
- Consumes: strict candidate predictor, explicit tlsep parameters, QSM code
- Produces: 65-tree full-precision DBH/height/volume records and measurable counts

- [ ] **Step 1: Write failing paired-input/failure-count tests**

Use two toy trees and injected predictors/QSM function. Assert both predictors receive byte-identical points, the loader uses sorted deterministic indices, and a candidate exception reduces candidate measurable count without deleting the row.

```python
def test_failed_candidate_tree_is_retained_and_counted(toy_cohort):
    result = evaluate_demol_pair(
        toy_cohort,
        baseline_predictor=lambda points: np.zeros(len(points), dtype=np.int8),
        candidate_predictor=lambda points: (_ for _ in ()).throw(RuntimeError("boom")),
        qsm_func=fake_qsm,
        qsm_seed=0,
    )
    assert len(result["per_tree"]) == len(toy_cohort)
    assert result["candidate"]["measurable_trees"] == 0
    assert all(row["candidate_status"] == "failed" for row in result["per_tree"])
```

- [ ] **Step 2: Run and verify failure**

Run `tests/test_demol_eval.py`; expected FAIL because module does not exist.

- [ ] **Step 3: Implement cohort loader**

Move reusable parsing logic from `notebooks/validate_belgium.py` without importing matplotlib/pandas. Match `tree_name`, normalize min Z, select at most 20,000 sorted random indices with seed 0, reject non-positive ground-truth DBH/height/volume and require exactly 65 matches in formal mode.

- [ ] **Step 4: Implement paired evaluation**

Load each point cloud exactly once. Pass the same read-only NumPy array to both predictors, extract wood points, call `qsm.compute_qsm(wood, seed=0)`, and mark measurable only when DBH/height/volume are finite and positive. Compute per-tree absolute DBH error, absolute height error and volume APE; aggregate only after retaining all failure rows.

- [ ] **Step 5: Run tests and commit**

```powershell
git add services/ml/pipeline/demol_eval.py services/ml/tests/test_demol_eval.py
git commit -m "feat(ml): compare paired Demol downstream metrics"
```

---

### Task 10: Orchestrate the Independent Evaluation and Write Evidence Artifacts

**Files:**
- Create: `services/ml/pipeline/independent_eval.py`
- Create: `services/ml/tests/test_independent_eval.py`
- Modify: `services/ml/scripts/pointnet_evidence.py`

**Interfaces:**
- Consumes: Tasks 2, 6–9 and existing `evaluate_promotion()`
- Produces: external/downstream CSV, `result.json`, `REPORT.md`, exact verdict

- [ ] **Step 1: Write a failing CPU integration test**

Inject two external toy trees, two Demol toy trees and fake baseline/candidate predictors. Assert:

- backend rows cover identical tree IDs;
- macro Wood IoU is used in `EvaluationMetrics`;
- result retains unrounded floats;
- CSV row counts match cohorts;
- Markdown prints exact metrics and limitations;
- evaluator never edits `pipeline/main.py` or default backend.

- [ ] **Step 2: Run and verify failure**

Run `tests/test_independent_eval.py`; expected FAIL because module does not exist.

- [ ] **Step 3: Implement evaluation composition**

`run_independent_evaluation()` must validate protocol/freeze/external manifest hashes first, instantiate one strict PointNet model, run both backends, calculate segmentation and Demol aggregates, construct existing `PromotionEvidence`, call `evaluate_promotion()`, calculate bootstrap intervals, then call `decide_independent_verdict()`.

Every output must include:

```python
{
    "schema_version": "1",
    "experiment_id": "pointnet-independent-eval-2026-07-16",
    "protocol_sha256": protocol_sha,
    "freeze_manifest_sha256": freeze_sha,
    "external_manifest_sha256": external_sha,
    "evaluation_git_commit": git_commit,
    "baseline": baseline_metrics,
    "candidate": candidate_metrics,
    "paired_deltas": paired_deltas,
    "confidence_intervals": intervals,
    "formal_gate": asdict(formal_decision),
    "verdict": verdict,
    "limitations": limitations,
}
```

- [ ] **Step 4: Write artifacts atomically**

Write `segmentation_per_tree.csv`, `downstream_per_tree.csv`, `result.json` and `REPORT.md` to a temporary sibling directory, validate row counts and JSON finite values, then rename files into the evidence directory. If any write/validation fails, leave no partial final result.

- [ ] **Step 5: Add `evaluate` CLI**

```text
evaluate --protocol --freeze-manifest --checkpoint --external-root --external-manifest --demol-root --evidence-dir --repo-root
```

The command prints exact verdict, Wood IoUs, DBH MAEs, Height MAEs, Volume MAPEs and measurable counts using ASCII labels.

- [ ] **Step 6: Run tests and commit**

```powershell
git add services/ml/pipeline/independent_eval.py services/ml/scripts/pointnet_evidence.py services/ml/tests/test_independent_eval.py
git commit -m "feat(ml): run the independent PointNet evidence gate"
```

---

### Task 11: Connect Reviewed Results to Repository Truth Without Auto-Promotion

**Files:**
- Create: `scripts/review_pointnet_evidence.py`
- Create: `scripts/tests/test_review_pointnet_evidence.py`
- Modify: `scripts/sync_truth.py`
- Modify: `scripts/tests/test_sync_truth.py`
- Modify: `.github/workflows/ci-ml.yml`
- Modify: `docs/DOCUMENT_STATUS.md`

**Interfaces:**
- Consumes: tracked `result.json`
- Produces: reviewed `validation.pointnet_independent` block and generated truth while keeping default unchanged

- [ ] **Step 1: Write failing review-contract tests**

Create tests for all four verdicts. A `PROMOTE_POINTNET` result must set `promotion_evidence.all_passed=true` and empty failed criteria but keep `candidate.promoted=false` and `candidate.status="Experimental"`. A failed result must copy exact failed criteria and result SHA-256. Tampered result hash must be rejected by `sync_truth.py --check`.

- [ ] **Step 2: Run and verify failure**

```powershell
.\.venv\Scripts\python.exe -m pytest -q -o addopts='' scripts/tests/test_review_pointnet_evidence.py scripts/tests/test_sync_truth.py
```

Expected: FAIL because review script and new manifest block do not exist.

- [ ] **Step 3: Implement reviewed-result importer**

`review_pointnet_evidence.py` must load finite JSON, verify protocol/freeze/external hashes and result schema, then update only:

- `candidate.promotion_evidence`
- `validation.pointnet_independent`
- PointNet capability evidence/claim text

It must never change `baseline.backend`, `candidate.promoted` or `core_demo`.

- [ ] **Step 4: Extend truth validation/rendering**

Make the independent block optional while pending and mandatory once a result path is present. Render verdict, exact candidate/baseline Wood IoU and downstream metrics in the generated truth block. Preserve Wan `0.418` and historical Demol numbers as historical context.

- [ ] **Step 5: Extend CI**

Add `training/` to Ruff checks, add `docs/evidence/pointnet_independent_eval/**` to workflow path filters, and keep real data/training out of CI. CI continues to run all CPU fixtures and truth sync.

- [ ] **Step 6: Run tests and commit**

```powershell
git add scripts/review_pointnet_evidence.py scripts/tests/test_review_pointnet_evidence.py scripts/sync_truth.py scripts/tests/test_sync_truth.py .github/workflows/ci-ml.yml docs/DOCUMENT_STATUS.md
git commit -m "feat(evidence): sync reviewed PointNet verdict"
```

---

### Task 12: Correct Unprovable or Confounded Documentation Before Training

**Files:**
- Modify: `docs/ml/FINETUNE_REALDATA.md`
- Modify: `docs/ml/WOODLEAF_RESULTS.md`
- Modify: `docs/ml/PIPELINE.md`
- Modify: `services/ml/notebooks/experiment_g3_pointnet_volume.py`
- Modify: `scripts/tests/test_sync_truth.py`

**Interfaces:**
- Produces: truthful pre-result documentation; no metric/default change

- [ ] **Step 1: Add failing wording tests**

Assert current documents do not describe Wan dev as `leakage-free`, do not call it an independent final test, and the G3 notebook contains `confounded historical experiment` plus `not promotion evidence`.

- [ ] **Step 2: Run and verify failure**

Run `scripts/tests/test_sync_truth.py`; expected FAIL on current stale wording.

- [ ] **Step 3: Apply narrow documentation corrections**

Keep exact prior metrics `0.418/0.808/0.613/0.831`. Replace the claim with “spatially separated development split with a 2.5 m excluded band; native tree IDs are unavailable, and the same dev loader selected the epoch.” Mark G3 as changing both segmentation and volume method, therefore non-gating.

- [ ] **Step 4: Run truth sync and commit**

```powershell
.\.venv\Scripts\python.exe scripts/sync_truth.py --write
.\.venv\Scripts\python.exe -m pytest -q -o addopts='' scripts/tests/test_sync_truth.py
git add docs/ml/FINETUNE_REALDATA.md docs/ml/WOODLEAF_RESULTS.md docs/ml/PIPELINE.md services/ml/notebooks/experiment_g3_pointnet_volume.py scripts/tests/test_sync_truth.py docs/PROJECT_SPEC.md docs/CAPABILITY_MATRIX.md apps/web/src/generated/core-demo-evidence.ts
git commit -m "docs(ml): clarify PointNet evaluation limits"
```

---

### Task 13: Verify the Complete Implementation Before Touching Real Holdout Data

**Files:**
- No new files

**Interfaces:**
- Produces: clean committed implementation baseline

- [ ] **Step 1: Install the project ML environment in the isolated worktree**

```powershell
cd services/ml
..\..\.venv\Scripts\python.exe -m pip install -e ".[gpu,dev]"
```

Expected: installation succeeds; `python -c "import torch; print(torch.cuda.is_available())"` prints `True`

- [ ] **Step 2: Run lint and focused tests**

```powershell
..\..\.venv\Scripts\ruff.exe check pipeline training scripts tests
..\..\.venv\Scripts\python.exe -m pytest tests/test_provenance.py tests/test_evidence_protocol.py tests/test_realdata_dataset.py tests/test_evidence_training.py tests/test_pointnet_tiled.py tests/test_external_tree_dataset.py tests/test_evidence_metrics.py tests/test_demol_eval.py tests/test_independent_eval.py -v
```

Expected: zero lint errors; all focused tests PASS

- [ ] **Step 3: Run complete ML and repository truth suites**

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
cd ../..
.\.venv\Scripts\python.exe -m pytest scripts/tests/ -v -o addopts=''
.\.venv\Scripts\python.exe scripts/sync_truth.py --check
git diff --check
git status --short
```

Expected: all tests PASS, truth status `ok`, no whitespace errors, clean worktree

- [ ] **Step 4: Record implementation checkpoint**

```powershell
git log -1 --format=%H
git status --porcelain --untracked-files=normal
```

Expected: 40-character commit SHA and no status output. Do not proceed to Task 14 otherwise.

---

### Task 14: Build and Commit the Real Wan Split Manifest

**Files:**
- Create by command: `docs/evidence/pointnet_independent_eval/wan_split_manifest.json`
- Ignored outputs: `services/ml/output/pointnet_evidence/wan_train.npz`, `wan_dev.npz`

**Interfaces:**
- Produces: immutable real training/dev identity from the three local Wan files

- [ ] **Step 1: Run the precommitted builder**

From worktree root:

```powershell
$py = (Resolve-Path .venv\Scripts\python.exe).Path
& $py services/ml/scripts/pointnet_evidence.py prepare-wan `
  --protocol docs/evidence/pointnet_independent_eval/protocol.json `
  --wan-root D:\Project_Carbon\services\ml\data\realdata\wan2021 `
  --artifact-dir services/ml/output/pointnet_evidence `
  --manifest-out docs/evidence/pointnet_independent_eval/wan_split_manifest.json `
  --repo-root .
```

Expected: summary reports three sources, non-empty train/dev samples and zero duplicate tile IDs

- [ ] **Step 2: Validate hashes and deterministic rebuild**

Run the same command with `--artifact-dir services/ml/output/pointnet_evidence-rebuild` and `--manifest-out services/ml/output/pointnet_evidence-rebuild/wan_split_manifest.json`; compare canonical dataset content hashes and tile lists. Expected: identical.

- [ ] **Step 3: Commit only the manifest**

```powershell
git status --short
git add docs/evidence/pointnet_independent_eval/wan_split_manifest.json
git commit -m "evidence(ml): freeze Wan development split"
git status --short
```

Expected: only the manifest enters Git; NPZ/raw files remain ignored; final status clean

---

### Task 15: Train Three Seeds, Rerun the Winner and Commit the Freeze

**Files:**
- Create by command: `docs/evidence/pointnet_independent_eval/training_runs.json`
- Create by command: `docs/evidence/pointnet_independent_eval/freeze_manifest.json`
- Ignored outputs: checkpoints/logs in `services/ml/output/pointnet_evidence/`

**Interfaces:**
- Produces: the only checkpoint permitted to enter Cohort A evaluation

- [ ] **Step 1: Confirm clean/GPU preconditions**

```powershell
git status --porcelain --untracked-files=normal
.\.venv\Scripts\python.exe -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"
```

Expected: no Git output and `NVIDIA GeForce RTX 4060 Laptop GPU`

- [ ] **Step 2: Run the fixed matrix and reproducibility rerun**

```powershell
.\.venv\Scripts\python.exe services/ml/scripts/pointnet_evidence.py train `
  --protocol docs/evidence/pointnet_independent_eval/protocol.json `
  --wan-manifest docs/evidence/pointnet_independent_eval/wan_split_manifest.json `
  --artifact-dir services/ml/output/pointnet_evidence `
  --repo-root .
```

Expected: exactly seeds `20260716/17/18`, one automatic winner rerun, `reproducible=true`; no external path is opened

- [ ] **Step 3: Generate and inspect the freeze manifest**

```powershell
.\.venv\Scripts\python.exe services/ml/scripts/pointnet_evidence.py freeze `
  --protocol docs/evidence/pointnet_independent_eval/protocol.json `
  --wan-manifest docs/evidence/pointnet_independent_eval/wan_split_manifest.json `
  --artifact-dir services/ml/output/pointnet_evidence `
  --evidence-dir docs/evidence/pointnet_independent_eval `
  --repo-root .
```

Expected: checkpoint file SHA-256 and canonical state SHA-256 are 64 lowercase hex characters; rerun hashes/metrics equal winner

- [ ] **Step 4: Commit freeze before any external download**

```powershell
git add docs/evidence/pointnet_independent_eval/training_runs.json docs/evidence/pointnet_independent_eval/freeze_manifest.json
git commit -m "evidence(ml): freeze PointNet candidate"
git status --porcelain --untracked-files=normal
```

Expected: commit succeeds and final status is empty. Record this commit as `external_opened_after_commit` in Task 16.

---

### Task 16: Fetch the Blind Cohort, Commit Its Manifest, Then Evaluate Once

**Files:**
- Create by command: `docs/evidence/pointnet_independent_eval/external_dataset_manifest.json`
- Create by command: `docs/evidence/pointnet_independent_eval/segmentation_per_tree.csv`
- Create by command: `docs/evidence/pointnet_independent_eval/downstream_per_tree.csv`
- Create by command: `docs/evidence/pointnet_independent_eval/result.json`
- Create by command: `docs/evidence/pointnet_independent_eval/REPORT.md`
- Ignored: raw PCD files under `D:\Project_Carbon\services\ml\data\realdata\zenodo_6831378`

**Interfaces:**
- Produces: final immutable evidence verdict

- [ ] **Step 1: Fetch only after freeze commit**

```powershell
.\.venv\Scripts\python.exe services/ml/scripts/pointnet_evidence.py fetch-external `
  --protocol docs/evidence/pointnet_independent_eval/protocol.json `
  --freeze-manifest docs/evidence/pointnet_independent_eval/freeze_manifest.json `
  --checkpoint services/ml/output/pointnet_evidence/winner.pt `
  --destination D:\Project_Carbon\services\ml\data\realdata\zenodo_6831378 `
  --manifest-out docs/evidence/pointnet_independent_eval/external_dataset_manifest.json `
  --repo-root .
```

Expected: exactly 20 verified PCD files forming 10 pairs; all publisher MD5/local SHA-256 checks pass

- [ ] **Step 2: Commit the external identity before computing metrics**

```powershell
git add docs/evidence/pointnet_independent_eval/external_dataset_manifest.json
git commit -m "evidence(ml): record blind external cohort"
git status --porcelain --untracked-files=normal
```

Expected: clean worktree; raw PCD files absent from Git

- [ ] **Step 3: Run the precommitted evaluation exactly once**

```powershell
.\.venv\Scripts\python.exe services/ml/scripts/pointnet_evidence.py evaluate `
  --protocol docs/evidence/pointnet_independent_eval/protocol.json `
  --freeze-manifest docs/evidence/pointnet_independent_eval/freeze_manifest.json `
  --checkpoint services/ml/output/pointnet_evidence/winner.pt `
  --external-root D:\Project_Carbon\services\ml\data\realdata\zenodo_6831378 `
  --external-manifest docs/evidence/pointnet_independent_eval/external_dataset_manifest.json `
  --demol-root D:\Project_Carbon\services\ml\data\raw\zenodo_belgium `
  --evidence-dir docs/evidence/pointnet_independent_eval `
  --repo-root .
```

Expected: one of `INVALID_EVIDENCE`, `FAIL_METRICS`, `POINT_ESTIMATE_PASS_ONLY`, `PROMOTE_POINTNET`; all exact metrics and CIs printed

- [ ] **Step 4: Validate result completeness without tuning**

```powershell
.\.venv\Scripts\python.exe -m pytest services/ml/tests/test_independent_eval.py services/ml/tests/test_evidence_metrics.py -v -o addopts=''
git diff --check
git status --short
```

Expected: tests PASS; exactly four result artifacts plus report are untracked/modified. Do not retrain, change thresholds or rerun with new preprocessing.

- [ ] **Step 5: Commit the result regardless of verdict**

```powershell
git add docs/evidence/pointnet_independent_eval/segmentation_per_tree.csv docs/evidence/pointnet_independent_eval/downstream_per_tree.csv docs/evidence/pointnet_independent_eval/result.json docs/evidence/pointnet_independent_eval/REPORT.md
git commit -m "evidence(ml): record independent PointNet verdict"
```

---

### Task 17: Synchronize Truth, Verify Everything and Stop Before Promotion

**Files:**
- Modify by command: `docs/evidence/core_demo_manifest.json`
- Modify/generated: `docs/CAPABILITY_MATRIX.md`, `apps/web/src/generated/core-demo-evidence.ts`, `docs/PROJECT_SPEC.md`, `docs/ml/PIPELINE.md`, `docs/ml/WOODLEAF_RESULTS.md`

**Interfaces:**
- Consumes: committed independent `result.json`
- Produces: repo-wide truthful status; no default switch

- [ ] **Step 1: Import the reviewed result**

```powershell
.\.venv\Scripts\python.exe scripts/review_pointnet_evidence.py `
  --result docs/evidence/pointnet_independent_eval/result.json `
  --manifest docs/evidence/core_demo_manifest.json
.\.venv\Scripts\python.exe scripts/sync_truth.py --write
```

Expected: exact new metrics/verdict appear while `baseline.backend` remains `tlsep` and `candidate.promoted` remains `false`

- [ ] **Step 2: Run the final verification matrix**

```powershell
cd services/ml
..\..\.venv\Scripts\ruff.exe check pipeline training scripts tests
..\..\.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
cd ../..
.\.venv\Scripts\python.exe -m pytest scripts/tests/ -v -o addopts=''
.\.venv\Scripts\python.exe scripts/sync_truth.py --check
git diff --check
git status --short
```

Expected: all checks PASS; only reviewed truth/generated files are modified

- [ ] **Step 3: Audit exact claims**

Search:

```powershell
rg -n "PROMOTE_POINTNET|POINT_ESTIMATE_PASS_ONLY|FAIL_METRICS|INVALID_EVIDENCE|Wood IoU|DBH MAE|Volume MAPE|fully blind|production-ready" docs README.md AGENTS.md proposal services/ml/README.md
```

Expected: every claim matches `result.json`; no text calls Demol newly blind or calls this full carbon validation

- [ ] **Step 4: Commit truth synchronization**

```powershell
git add docs/evidence/core_demo_manifest.json docs/CAPABILITY_MATRIX.md apps/web/src/generated/core-demo-evidence.ts docs/PROJECT_SPEC.md docs/ml/PIPELINE.md docs/ml/WOODLEAF_RESULTS.md
git commit -m "docs(evidence): align truth with PointNet verdict"
```

- [ ] **Step 5: Final branch verification and handoff**

```powershell
git status --short --branch
git log --oneline --decorate -15
git diff --stat origin/main HEAD
```

Expected: clean `codex/pointnet-independent-eval` branch. If verdict is `PROMOTE_POINTNET`, stop and propose a separate default-switch PR; otherwise keep `tlsep` and report the failed/inconclusive criteria exactly.

---

## Completion Definition

The plan is complete only when Tasks 1–17 finish in order, the external PCD files were first fetched after the committed freeze, every per-tree row is retained, all exact metrics/CIs are committed, truth sync passes, and `tlsep` remains the default in this branch.
