# Truth + Reproducible Core Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one deterministic `tlsep` core-demo path with provenance and a strict PointNet++ promotion gate, then make the API, web, repository documents, CI, and a new NSC DOCX report state the same verified truth.

**Architecture:** `services/ml/pipeline/provenance.py` owns the evidence schema, stable hashing, algorithm map, and model-promotion decision. A deterministic runner executes the existing eight-step pipeline twice and writes machine-readable artifacts plus `docs/evidence/core_demo_manifest.json`. A truth-sync script generates capability/web evidence and checks marker-controlled documents; API and viewer surface the metadata that the pipeline actually returned. The Word builder copies the source report, validates exact anchors, applies conservative replacements, and never writes into the repository.

**Tech Stack:** Python 3.11, NumPy, existing ML pipeline/Open3D stack, pytest, FastAPI/Pydantic v2, Next.js 14/TypeScript/Vitest, JSON, GitHub Actions, python-docx, OOXML structural checks.

## Global Constraints

- `tlsep` is the production baseline for this sprint; PointNet++ remains `Experimental` unless every promotion criterion passes.
- PointNet++ promotion requires checkpoint SHA-256, training provenance, an independent real-tree test, higher Wood IoU, non-regressing DBH MAE/Height MAE/Volume MAPE, non-decreasing measurable-tree count, and reproducible commands.
- Report Wan held-out metrics exactly: Wood IoU `0.418`, Leaf IoU `0.808`, Mean IoU `0.613`, accuracy `0.831`.
- Report Demol 65-tree DBH MAE exactly as `1.1673846154 cm`; never replace it with a rounded marketing claim without the full value nearby.
- `species_db.csv` remains the allometric coefficient source of truth; species classification remains `Stub`.
- Carbon stock and CO2e estimates are not certified carbon credits.
- No PointNet checkpoint, model binary, raw private point cloud, credential, tunnel URL, or personal data from the report may enter Git.
- Never overwrite `C:\Users\Acer\Downloads\เล่มโครงงานNSC_แก้ไขแล้ว_ปรับปรุง (3).docx`.
- The new report path is `C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx`.
- Preserve the existing Word layout and direct formatting; change page size/headings only after successful render review proves no layout damage.
- Python console output must use ASCII-safe status text so Windows cp874 cannot crash the process.
- New behavior follows Red-Green-Refactor: test first, observe the expected failure, add minimal implementation, rerun the focused and neighboring suites.
- Commit each task separately after its focused verification passes.

## Execution Environment

Use the bundled Python only to create a disposable workspace environment; do not repair or reuse the broken checked-in-service `.venv` paths:

```powershell
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv temp/truth-venv
& 'temp/truth-venv/Scripts/python.exe' -m pip install --upgrade pip
& 'temp/truth-venv/Scripts/python.exe' -m pip install -e './services/ml[cpu,dev]'
& 'temp/truth-venv/Scripts/python.exe' -m pip install -e './services/api[dev]' python-docx
```

The `temp/` directory is already ignored. If dependency installation is blocked by network policy, request scoped network permission and rerun the same commands; do not count an unexecuted suite as passing.

---

## File Responsibility Map

**Create:**

- `services/ml/pipeline/provenance.py` — evidence schema helpers, canonical hashing, algorithm map, checkpoint identity, Git identity, promotion gate.
- `services/ml/tests/test_provenance.py` — stable-hash and provenance contract tests.
- `services/ml/tests/test_evidence_gate.py` — one test per promotion criterion and aggregate decision.
- `services/ml/scripts/run_core_demo.py` — deterministic two-run demo and artifact writer.
- `services/ml/tests/test_core_demo.py` — focused deterministic runner test.
- `docs/evidence/core_demo_manifest.json` — reviewed metrics/status plus verified core-demo result.
- `docs/CAPABILITY_MATRIX.md` — generated capability status matrix.
- `scripts/sync_truth.py` — manifest validator/generator/checker.
- `scripts/tests/test_sync_truth.py` — generator and drift-detection tests.
- `apps/web/src/generated/core-demo-evidence.ts` — generated immutable web evidence.
- `apps/web/src/lib/evidence.ts` — pure metadata-to-label adapter.
- `apps/web/src/lib/evidence.test.ts` — backend/status label tests.
- `scripts/build_truth_aligned_report.py` — conservative report copier/patcher/auditor.
- `scripts/tests/test_build_truth_aligned_report.py` — anchor, source-integrity, and structure tests.

**Modify:**

- `services/ml/pipeline/main.py` — attach actual provenance metadata to every result and update TreeQ naming.
- `services/ml/pipeline/ply_export.py` — update product name in artifact comment only.
- `services/ml/pyproject.toml` — update project name/description copy only; no dependency expansion.
- `services/api/app/schemas/analyze.py` — type the evidence metadata contract.
- `services/api/tests/test_upload_analyze.py` — assert metadata survives the HTTP response.
- `apps/web/src/lib/api.ts` — type `AnalyzeMetadata`.
- `apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx` — show actual backend, checkpoint/evidence status, and limitations.
- `apps/web/src/app/page.tsx` — replace unsupported/ambiguous claims with manifest-backed copy.
- `.github/workflows/ci-ml.yml` — remove the swallowed failure and add truth/core-demo gates.
- `docs/PROJECT_SPEC.md` — add the generated truth block and correct conflicting current-state claims.
- `docs/ml/PIPELINE.md` — describe the algorithms actually implemented in all eight stages.
- `docs/ml/WOODLEAF_RESULTS.md` — exact metrics, validation limitation, and promotion status.
- `README.md` — TreeQ name and truthful core-demo status only.

---

### Task 1: Provenance contract and PointNet++ evidence gate

**Files:**

- Create: `services/ml/pipeline/provenance.py`
- Create: `services/ml/tests/test_provenance.py`
- Create: `services/ml/tests/test_evidence_gate.py`

**Interfaces:**

- Produces: `ALGORITHM_MAP`, `sha256_bytes`, `sha256_file`, `hash_points`, `normalized_payload`, `normalized_sha256`, `resolve_git_commit`, `checkpoint_identity`, `EvaluationMetrics`, `PromotionEvidence`, `evaluate_promotion`.
- Consumes: standard library plus NumPy; no Torch import.

- [ ] **Step 1: Write failing provenance tests**

```python
# services/ml/tests/test_provenance.py
from __future__ import annotations

from copy import deepcopy

import numpy as np

from pipeline.provenance import (
    ALGORITHM_MAP,
    hash_points,
    normalized_payload,
    normalized_sha256,
    sha256_bytes,
)


def _evidence() -> dict:
    return {
        "schema_version": "1",
        "run": {
            "input_sha256": "a" * 64,
            "git_commit": "0036996",
            "pipeline_version": "0.3.0",
            "backend": "tlsep",
            "checkpoint_sha256": None,
        },
        "algorithms": dict(ALGORITHM_MAP),
        "results": {"dbh_cm": 10.25, "height_m": 8.5, "volume_m3": 0.12},
        "runtime": {"created_at": "2026-07-16T00:00:00Z", "output_dir": "C:/first"},
    }


def test_algorithm_map_names_actual_implementations():
    assert ALGORITHM_MAP == {
        "ground_segmentation": "percentile_grid",
        "height_normalization": "knn_idw",
        "chm": "max_z_morphology",
        "tree_segmentation": "watershed",
        "wood_leaf": "tlsep",
        "qsm": "ransac_dbh_maxz_height_taper_volume",
        "species": "stub",
        "allometric": "species_db_or_chave_fallback",
    }


def test_normalized_hash_ignores_only_runtime_fields():
    first = _evidence()
    second = deepcopy(first)
    second["runtime"] = {"created_at": "2026-07-17T00:00:00Z", "output_dir": "D:/second"}
    assert normalized_payload(first) == normalized_payload(second)
    assert normalized_sha256(first) == normalized_sha256(second)


def test_normalized_hash_changes_when_algorithm_or_result_changes():
    first = _evidence()
    second = deepcopy(first)
    second["results"]["dbh_cm"] = 10.26
    assert normalized_sha256(first) != normalized_sha256(second)


def test_hash_points_is_shape_and_dtype_stable():
    points = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
    assert hash_points(points) == hash_points(points.astype(np.float64))
    assert hash_points(points) == sha256_bytes(points.astype("<f8").tobytes(order="C"))
```

- [ ] **Step 2: Run provenance tests and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_provenance.py -v --no-cov
```

Expected: collection fails with `ModuleNotFoundError: No module named 'pipeline.provenance'`.

- [ ] **Step 3: Write failing evidence-gate tests**

```python
# services/ml/tests/test_evidence_gate.py
from dataclasses import replace

from pipeline.provenance import EvaluationMetrics, PromotionEvidence, evaluate_promotion


BASELINE = EvaluationMetrics(
    wood_iou=0.42,
    dbh_mae_cm=1.2,
    height_mae_m=0.55,
    volume_mape_pct=18.8,
    measurable_trees=65,
)
CANDIDATE = EvaluationMetrics(
    wood_iou=0.50,
    dbh_mae_cm=1.1,
    height_mae_m=0.54,
    volume_mape_pct=18.0,
    measurable_trees=65,
)
VALID = PromotionEvidence(
    baseline=BASELINE,
    candidate=CANDIDATE,
    checkpoint_sha256="b" * 64,
    training_provenance_complete=True,
    independent_real_test=True,
    reproducible_command=True,
)


def test_complete_non_regressing_candidate_is_promoted():
    decision = evaluate_promotion(VALID)
    assert decision.promote is True
    assert decision.failed_criteria == ()


def test_missing_candidate_is_not_evaluated():
    decision = evaluate_promotion(replace(VALID, candidate=None))
    assert decision.promote is False
    assert decision.status == "candidate_not_evaluated"


def test_every_gate_is_mandatory():
    cases = (
        (replace(VALID, checkpoint_sha256=None), "checkpoint_sha256"),
        (replace(VALID, training_provenance_complete=False), "training_provenance"),
        (replace(VALID, independent_real_test=False), "independent_real_test"),
        (replace(VALID, reproducible_command=False), "reproducible_command"),
        (replace(VALID, candidate=replace(CANDIDATE, wood_iou=0.42)), "wood_iou_improves"),
        (replace(VALID, candidate=replace(CANDIDATE, dbh_mae_cm=1.21)), "dbh_mae_non_regression"),
        (replace(VALID, candidate=replace(CANDIDATE, height_mae_m=0.56)), "height_mae_non_regression"),
        (replace(VALID, candidate=replace(CANDIDATE, volume_mape_pct=18.81)), "volume_mape_non_regression"),
        (replace(VALID, candidate=replace(CANDIDATE, measurable_trees=64)), "measurable_tree_count"),
    )
    for evidence, criterion in cases:
        decision = evaluate_promotion(evidence)
        assert decision.promote is False
        assert criterion in decision.failed_criteria
```

- [ ] **Step 4: Run gate tests and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_evidence_gate.py -v --no-cov
```

Expected: collection fails because the provenance module and dataclasses do not exist.

- [ ] **Step 5: Implement the pure provenance module**

Create `services/ml/pipeline/provenance.py` with these exact public contracts:

```python
"""Auditable provenance and evidence-gated model promotion."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

ALGORITHM_MAP = {
    "ground_segmentation": "percentile_grid",
    "height_normalization": "knn_idw",
    "chm": "max_z_morphology",
    "tree_segmentation": "watershed",
    "wood_leaf": "tlsep",
    "qsm": "ransac_dbh_maxz_height_taper_volume",
    "species": "stub",
    "allometric": "species_db_or_chave_fallback",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def hash_points(points: np.ndarray) -> str:
    stable = np.asarray(points, dtype="<f8", order="C")
    if stable.ndim != 2 or stable.shape[1] != 3:
        raise ValueError(f"Expected points (N, 3), got {stable.shape}")
    return sha256_bytes(stable.tobytes(order="C"))


def normalized_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(json.dumps(evidence))
    payload.pop("runtime", None)
    return payload


def normalized_sha256(evidence: dict[str, Any]) -> str:
    encoded = json.dumps(
        normalized_payload(evidence), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def resolve_git_commit(repo_root: str | Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def checkpoint_identity(model_path: str | Path | None) -> str | None:
    if model_path is None:
        return None
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    return sha256_file(path)


@dataclass(frozen=True)
class EvaluationMetrics:
    wood_iou: float
    dbh_mae_cm: float
    height_mae_m: float
    volume_mape_pct: float
    measurable_trees: int


@dataclass(frozen=True)
class PromotionEvidence:
    baseline: EvaluationMetrics
    candidate: EvaluationMetrics | None
    checkpoint_sha256: str | None
    training_provenance_complete: bool
    independent_real_test: bool
    reproducible_command: bool


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    status: str
    failed_criteria: tuple[str, ...]
    baseline: dict[str, Any]
    candidate: dict[str, Any] | None


def evaluate_promotion(evidence: PromotionEvidence) -> PromotionDecision:
    if evidence.candidate is None:
        return PromotionDecision(
            promote=False,
            status="candidate_not_evaluated",
            failed_criteria=("candidate_metrics",),
            baseline=asdict(evidence.baseline),
            candidate=None,
        )
    candidate = evidence.candidate
    baseline = evidence.baseline
    checks = {
        "checkpoint_sha256": bool(evidence.checkpoint_sha256),
        "training_provenance": evidence.training_provenance_complete,
        "independent_real_test": evidence.independent_real_test,
        "reproducible_command": evidence.reproducible_command,
        "wood_iou_improves": candidate.wood_iou > baseline.wood_iou,
        "dbh_mae_non_regression": candidate.dbh_mae_cm <= baseline.dbh_mae_cm,
        "height_mae_non_regression": candidate.height_mae_m <= baseline.height_mae_m,
        "volume_mape_non_regression": candidate.volume_mape_pct <= baseline.volume_mape_pct,
        "measurable_tree_count": candidate.measurable_trees >= baseline.measurable_trees,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return PromotionDecision(
        promote=not failed,
        status="promoted" if not failed else "rejected",
        failed_criteria=failed,
        baseline=asdict(baseline),
        candidate=asdict(candidate),
    )
```

- [ ] **Step 6: Run focused tests and lint**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_provenance.py services/ml/tests/test_evidence_gate.py -v --no-cov
& 'temp/truth-venv/Scripts/ruff.exe' check services/ml/pipeline/provenance.py services/ml/tests/test_provenance.py services/ml/tests/test_evidence_gate.py
```

Expected: all focused tests pass and Ruff exits `0`.

- [ ] **Step 7: Commit Task 1**

```powershell
git add services/ml/pipeline/provenance.py services/ml/tests/test_provenance.py services/ml/tests/test_evidence_gate.py
git commit -m "feat(ml): add provenance and model promotion gate"
```

---

### Task 2: Pipeline metadata and deterministic core-demo runner

**Files:**

- Modify: `services/ml/pipeline/main.py`
- Modify: `services/ml/pipeline/ply_export.py`
- Modify: `services/ml/pyproject.toml`
- Modify: `services/ml/tests/test_pipeline_orchestrator.py`
- Create: `services/ml/scripts/run_core_demo.py`
- Create: `services/ml/tests/test_core_demo.py`

**Interfaces:**

- Consumes: Task 1 provenance functions.
- Produces: pipeline metadata fields `input_sha256`, `git_commit`, `pipeline_version`, `wood_leaf_backend`, `checkpoint_sha256`, `algorithms`, `evidence_status`, `candidate_status`; CLI `services/ml/scripts/run_core_demo.py --output-dir PATH --repo-root PATH`.

- [ ] **Step 1: Add a failing orchestrator metadata test**

Append to `services/ml/tests/test_pipeline_orchestrator.py`:

```python
def test_process_points_records_auditable_provenance(synth_points):
    result = process_points(synth_points, wood_leaf_backend="tlsep")
    metadata = result.metadata
    assert metadata["input_sha256"]
    assert len(metadata["input_sha256"]) == 64
    assert metadata["checkpoint_sha256"] is None
    assert metadata["algorithms"]["ground_segmentation"] == "percentile_grid"
    assert metadata["algorithms"]["wood_leaf"] == "tlsep"
    assert metadata["algorithms"]["species"] == "stub"
    assert metadata["evidence_status"] == "baseline"
    assert metadata["candidate_status"] == "candidate_not_evaluated"
```

- [ ] **Step 2: Run the new test and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_pipeline_orchestrator.py::test_process_points_records_auditable_provenance -v --no-cov
```

Expected: assertion fails because `input_sha256` is absent.

- [ ] **Step 3: Attach provenance in `process_points`**

Import `ALGORITHM_MAP`, `checkpoint_identity`, `hash_points`, and `resolve_git_commit`. Define `PIPELINE_VERSION = "0.3.0"` next to the dataclasses. Build metadata at return time as follows:

```python
repo_root = Path(__file__).resolve().parents[3]
checkpoint_sha256 = checkpoint_identity(model_path) if wood_leaf_backend == "pointnet" else None
algorithms = dict(ALGORITHM_MAP)
algorithms["wood_leaf"] = wood_leaf_backend
metadata = {
    "pipeline_version": PIPELINE_VERSION,
    "git_commit": resolve_git_commit(repo_root),
    "wood_leaf_backend": wood_leaf_backend,
    "checkpoint_sha256": checkpoint_sha256,
    "input_sha256": hash_points(points),
    "algorithms": algorithms,
    "evidence_status": "baseline" if wood_leaf_backend == "tlsep" else "experimental",
    "candidate_status": (
        "candidate_not_evaluated" if wood_leaf_backend == "tlsep" else "not_promoted"
    ),
    "n_input_points": len(points),
    "status": "ok",
}
```

Use this `metadata` in `PipelineResult`. Keep `input_file` as a separate display field added by `process_point_cloud`; the reproducibility hash remains the canonical point-array hash.

- [ ] **Step 4: Run focused orchestrator tests**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_pipeline_orchestrator.py -v --no-cov
```

Expected: `tlsep` tests pass; PointNet test is skipped when no tracked checkpoint exists.

- [ ] **Step 5: Write a failing core-demo test**

```python
# services/ml/tests/test_core_demo.py
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_core_demo_runs_twice_and_writes_reproducible_artifacts(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "services" / "ml" / "scripts" / "run_core_demo.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path),
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr
    summary = json.loads((tmp_path / "verification-summary.json").read_text(encoding="utf-8"))
    assert summary["reproducible"] is True
    assert summary["normalized_result_sha256"][0] == summary["normalized_result_sha256"][1]
    assert summary["segmented_ply_sha256"][0] == summary["segmented_ply_sha256"][1]
    for name in ("result.json", "segmented.ply", "evidence.json", "verification-summary.json"):
        assert (tmp_path / name).is_file()
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["run"]["backend"] == "tlsep"
    assert evidence["run"]["checkpoint_sha256"] is None
    assert evidence["algorithms"]["species"] == "stub"
    assert evidence["evidence"]["candidate_status"] == "candidate_not_evaluated"
```

- [ ] **Step 6: Run the core-demo test and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_core_demo.py -v --no-cov
```

Expected: assertion fails because `services/ml/scripts/run_core_demo.py` does not exist and the subprocess returns non-zero.

- [ ] **Step 7: Implement the deterministic runner**

Create `services/ml/scripts/run_core_demo.py` with:

```python
"""Run the reviewed tlsep core demo twice and emit auditable artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click

from pipeline.main import PIPELINE_VERSION, process_points
from pipeline.provenance import normalized_sha256, resolve_git_commit, sha256_file
from pipeline.synthetic import generate_synthetic_plot

DEMO_CONFIG = {
    "n_trees": 3,
    "plot_size_m": 20.0,
    "ground_z_variation": 0.8,
    "ground_point_density": 20.0,
    "leaves_per_tree": 1500,
    "seed": 42,
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _pipeline_payload(result: Any) -> dict[str, Any]:
    return {
        "metadata": result.metadata,
        "summary": result.summary,
        "trees": [asdict(tree) for tree in result.trees],
    }


def _evidence(payload: dict[str, Any], created_at: str, output_dir: Path) -> dict[str, Any]:
    metadata = payload["metadata"]
    return {
        "schema_version": "1",
        "run": {
            "input_sha256": metadata["input_sha256"],
            "git_commit": metadata["git_commit"],
            "pipeline_version": metadata["pipeline_version"],
            "backend": metadata["wood_leaf_backend"],
            "checkpoint_sha256": metadata["checkpoint_sha256"],
            "config": DEMO_CONFIG,
        },
        "algorithms": metadata["algorithms"],
        "results": payload["summary"],
        "trees": payload["trees"],
        "evidence": {
            "dataset": "deterministic_synthetic_plot_seed_42",
            "scope": "core_demo_fixture_not_accuracy_benchmark",
            "candidate_status": metadata["candidate_status"],
        },
        "runtime": {"created_at": created_at, "output_dir": str(output_dir)},
    }


def run_core_demo(output_dir: str | Path, repo_root: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    repo_root = Path(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    points, _, _ = generate_synthetic_plot(**DEMO_CONFIG)
    evidence_runs: list[dict[str, Any]] = []
    ply_hashes: list[str] = []
    payloads: list[dict[str, Any]] = []
    for index in (1, 2):
        ply_path = output_dir / f"segmented-run-{index}.ply"
        result = process_points(
            points,
            wood_leaf_backend="tlsep",
            default_species="Tectona grandis",
            segmented_ply_out=str(ply_path),
        )
        result.metadata["git_commit"] = resolve_git_commit(repo_root)
        payload = _pipeline_payload(result)
        payloads.append(payload)
        evidence_runs.append(
            _evidence(payload, datetime.now(UTC).isoformat(), output_dir)
        )
        ply_hashes.append(sha256_file(ply_path))
    result_hashes = [normalized_sha256(item) for item in evidence_runs]
    reproducible = result_hashes[0] == result_hashes[1] and ply_hashes[0] == ply_hashes[1]
    summary = {
        "schema_version": "1",
        "reproducible": reproducible,
        "normalized_result_sha256": result_hashes,
        "segmented_ply_sha256": ply_hashes,
        "git_commit": resolve_git_commit(repo_root),
        "pipeline_version": PIPELINE_VERSION,
    }
    if not reproducible:
        raise RuntimeError("Core demo is not reproducible")
    _write_json(output_dir / "result.json", payloads[0])
    _write_json(output_dir / "evidence.json", evidence_runs[0])
    _write_json(output_dir / "verification-summary.json", summary)
    (output_dir / "segmented-run-1.ply").replace(output_dir / "segmented.ply")
    (output_dir / "segmented-run-2.ply").unlink()
    return summary


@click.command()
@click.option("--output-dir", required=True, type=click.Path(path_type=Path))
@click.option("--repo-root", default="../..", type=click.Path(path_type=Path))
def cli(output_dir: Path, repo_root: Path) -> None:
    summary = run_core_demo(output_dir, repo_root)
    click.echo(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    cli()
```

If the actual pipeline returns no measurable tree for this fixture, reduce only `min_height`/fixture density through a failing test that reproduces the issue; do not fabricate expected carbon values.

- [ ] **Step 8: Run the demo test twice and inspect artifacts**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests/test_core_demo.py -v --no-cov
& 'temp/truth-venv/Scripts/python.exe' services/ml/scripts/run_core_demo.py --output-dir temp/core-demo --repo-root .
Get-ChildItem -LiteralPath temp/core-demo | Select-Object Name,Length
```

Expected: test passes; CLI exits `0`; four artifacts exist; summary contains `"reproducible": true`.

- [ ] **Step 9: Update product naming and commit Task 2**

Change only display metadata from CarbonScan AI to TreeQ Carbon Platform in `services/ml/pyproject.toml`, `pipeline.main` CLI help, and `ply_export.py` PLY comment. Then run:

```powershell
& 'temp/truth-venv/Scripts/ruff.exe' check services/ml/pipeline services/ml/scripts services/ml/tests/test_pipeline_orchestrator.py services/ml/tests/test_core_demo.py
git add services/ml/pipeline/main.py services/ml/pipeline/ply_export.py services/ml/pyproject.toml services/ml/scripts/run_core_demo.py services/ml/tests/test_pipeline_orchestrator.py services/ml/tests/test_core_demo.py
git commit -m "feat(ml): add deterministic core demo evidence"
```

---

### Task 3: Truth manifest, generated capability matrix, and drift checker

**Files:**

- Create: `docs/evidence/core_demo_manifest.json`
- Create: `docs/CAPABILITY_MATRIX.md`
- Create: `scripts/sync_truth.py`
- Create: `scripts/tests/test_sync_truth.py`
- Create: `apps/web/src/generated/core-demo-evidence.ts`

**Interfaces:**

- Consumes: verified `temp/core-demo/evidence.json` and `verification-summary.json` from Task 2.
- Produces: `load_manifest(path)`, `render_capability_matrix(manifest)`, `render_typescript(manifest)`, `replace_truth_block(text, rendered)`, CLI modes `--write` and `--check`.

- [ ] **Step 1: Write failing truth-sync tests**

```python
# scripts/tests/test_sync_truth.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.sync_truth import (
    load_manifest,
    render_capability_matrix,
    render_typescript,
    replace_truth_block,
)


def manifest(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "project": "TreeQ Carbon Platform",
                "baseline": {"backend": "tlsep", "status": "Implemented"},
                "candidate": {"backend": "pointnet", "status": "Experimental", "promoted": False},
                "validation": {
                    "wan_held_out": {"wood_iou": 0.418, "leaf_iou": 0.808, "mean_iou": 0.613, "accuracy": 0.831},
                    "demol_65": {"dbh_mae_cm": 1.1673846154, "volume_mape_pct": 18.7650916186},
                },
                "capabilities": [
                    {"name": "Species classification", "status": "Stub", "implementation": "No learned classifier", "evidence": "pipeline/species_classifier.py", "claim": "Not implemented"}
                ],
                "core_demo": {"reproducible": True, "git_commit": "0036996", "pipeline_version": "0.3.0"},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_manifest_rejects_promoted_pointnet_without_gate(tmp_path: Path):
    path = manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidate"]["promoted"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="promotion evidence"):
        load_manifest(path)


def test_generated_outputs_contain_exact_truth(tmp_path: Path):
    data = load_manifest(manifest(tmp_path))
    ts = render_typescript(data)
    matrix = render_capability_matrix(data)
    assert "woodIoU: 0.418" in ts
    assert "dbhMaeCm: 1.1673846154" in ts
    assert "PointNet++" in matrix
    assert "Experimental" in matrix


def test_truth_block_requires_exact_markers():
    source = "before\n<!-- TREEQ_TRUTH_START -->\nold\n<!-- TREEQ_TRUTH_END -->\nafter\n"
    updated = replace_truth_block(source, "new")
    assert "before\n<!-- TREEQ_TRUTH_START -->\nnew\n<!-- TREEQ_TRUTH_END -->\nafter" in updated
    with pytest.raises(ValueError, match="truth markers"):
        replace_truth_block("no markers", "new")
```

- [ ] **Step 2: Run truth-sync tests and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests/test_sync_truth.py -v --no-cov
```

Expected: collection fails because `scripts.sync_truth` does not exist.

- [ ] **Step 3: Implement manifest validation and deterministic renderers**

`scripts/sync_truth.py` must:

1. Require the top-level keys used in the test.
2. Require baseline backend/status exactly `tlsep`/`Implemented`.
3. Reject `candidate.promoted == true` unless `candidate.promotion_evidence.all_passed == true` and `failed_criteria` is empty.
4. Render TypeScript with `as const` and numeric literals from JSON.
5. Render a Markdown capability table with columns Capability, Status, Implementation, Evidence, Allowed claim.
6. Replace exactly one marker pair in each controlled Markdown file.
7. In `--check` mode, generate expected strings in memory and return non-zero on any byte-level drift.
8. In `--write` mode, write `docs/CAPABILITY_MATRIX.md`, `apps/web/src/generated/core-demo-evidence.ts`, and the three truth blocks.

Use this CLI contract:

```python
def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    return sync(repo_root=args.repo_root, check=args.check)
```

- [ ] **Step 4: Create the reviewed manifest from actual artifacts**

Rerun the core demo after the Task 2 commit so the evidence records the exact ML implementation commit:

```powershell
& 'temp/truth-venv/Scripts/python.exe' services/ml/scripts/run_core_demo.py --output-dir temp/core-demo --repo-root .
```

Populate `docs/evidence/core_demo_manifest.json` with:

- exact Wan and Demol metrics from the approved design,
- all capability rows from section 5 of the design,
- `candidate.promoted: false`, `candidate.status: "Experimental"`, and current limitations,
- actual `git_commit`, pipeline version, input hash, normalized hash, PLY hash, total trees/carbon/CO2e copied programmatically from `temp/core-demo` artifacts,
- `scope: "deterministic synthetic fixture; reproducibility proof, not accuracy proof"`.

Do not type unknown hashes by hand. Use a short read-only inspection command to copy artifact values and validate that every SHA-256 has length 64.

- [ ] **Step 5: Add truth markers and generate outputs**

Add exactly one empty marker block to each controlled document at the current-status/metrics section:

```markdown
<!-- TREEQ_TRUTH_START -->
<!-- TREEQ_TRUTH_END -->
```

Then run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' scripts/sync_truth.py --write
& 'temp/truth-venv/Scripts/python.exe' scripts/sync_truth.py --check
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests/test_sync_truth.py -v --no-cov
```

Expected: generated files exist, check mode exits `0`, and focused tests pass.

- [ ] **Step 6: Commit Task 3**

```powershell
git add docs/evidence/core_demo_manifest.json docs/CAPABILITY_MATRIX.md scripts/sync_truth.py scripts/tests/test_sync_truth.py apps/web/src/generated/core-demo-evidence.ts docs/PROJECT_SPEC.md docs/ml/PIPELINE.md docs/ml/WOODLEAF_RESULTS.md
git commit -m "feat: establish single-source core demo truth"
```

---

### Task 4: Typed API evidence and web disclosure

**Files:**

- Modify: `services/api/app/schemas/analyze.py`
- Modify: `services/api/tests/test_upload_analyze.py`
- Modify: `apps/web/src/lib/api.ts`
- Create: `apps/web/src/lib/evidence.ts`
- Create: `apps/web/src/lib/evidence.test.ts`
- Modify: `apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx`
- Modify: `apps/web/src/app/page.tsx`

**Interfaces:**

- Consumes: pipeline metadata and generated `CORE_DEMO_EVIDENCE`.
- Produces: Pydantic `AnalyzeMetadata`, TypeScript `AnalyzeMetadata`, `formatBackendLabel(metadata)`, `formatEvidenceStatus(metadata)`.

- [ ] **Step 1: Make the API test require a typed provenance schema**

Extend `FAKE_RESULT["metadata"]` in `services/api/tests/test_upload_analyze.py` with:

```python
"git_commit": "0036996",
"input_sha256": "a" * 64,
"checkpoint_sha256": None,
"algorithms": {
    "ground_segmentation": "percentile_grid",
    "height_normalization": "knn_idw",
    "chm": "max_z_morphology",
    "tree_segmentation": "watershed",
    "wood_leaf": "tlsep",
    "qsm": "ransac_dbh_maxz_height_taper_volume",
    "species": "stub",
    "allometric": "species_db_or_chave_fallback",
},
"evidence_status": "baseline",
"candidate_status": "candidate_not_evaluated",
```

Add assertions:

```python
assert data["metadata"]["wood_leaf_backend"] == "tlsep"
assert data["metadata"]["evidence_status"] == "baseline"
assert data["metadata"]["algorithms"]["species"] == "stub"
assert data["metadata"]["checkpoint_sha256"] is None
```

At module scope import the not-yet-created schema and add an annotation contract test:

```python
from app.schemas.analyze import AnalyzeMetadata, AnalyzeResponse


def test_analyze_response_uses_typed_metadata_schema():
    assert AnalyzeResponse.model_fields["metadata"].annotation is AnalyzeMetadata
```

- [ ] **Step 2: Run API test and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/api/tests/test_upload_analyze.py -v --no-cov
```

Expected: collection fails with `ImportError: cannot import name 'AnalyzeMetadata'`.

- [ ] **Step 3: Add the typed API schema**

In `services/api/app/schemas/analyze.py` add:

```python
class AnalyzeMetadata(BaseModel):
    pipeline_version: str
    git_commit: str
    wood_leaf_backend: str
    input_sha256: str = Field(min_length=64, max_length=64)
    checkpoint_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    algorithms: dict[str, str]
    evidence_status: str
    candidate_status: str
    n_input_points: int
    status: str
    input_file: str | None = None
```

Change `AnalyzeResponse.metadata` to `AnalyzeMetadata`. Run the focused API test again; expected pass.

- [ ] **Step 4: Write failing web evidence adapter tests**

```typescript
// apps/web/src/lib/evidence.test.ts
import { describe, expect, it } from 'vitest';

import { formatBackendLabel, formatEvidenceStatus } from './evidence';

const metadata = {
  pipeline_version: '0.3.0',
  git_commit: '0036996',
  wood_leaf_backend: 'tlsep',
  input_sha256: 'a'.repeat(64),
  checkpoint_sha256: null,
  algorithms: { species: 'stub', wood_leaf: 'tlsep' },
  evidence_status: 'baseline',
  candidate_status: 'candidate_not_evaluated',
  n_input_points: 1000,
  status: 'ok',
};

describe('evidence labels', () => {
  it('labels tlsep as the baseline without calling it PointNet++', () => {
    expect(formatBackendLabel(metadata)).toBe('Baseline: tlsep');
  });

  it('states that the candidate was not evaluated', () => {
    expect(formatEvidenceStatus(metadata)).toContain('candidate not evaluated');
  });
});
```

- [ ] **Step 5: Run web test and observe RED**

Run:

```powershell
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web test --run src/lib/evidence.test.ts
```

Expected: test fails because `src/lib/evidence.ts` does not exist.

- [ ] **Step 6: Implement typed client metadata and pure labels**

Replace `AnalyzeResponse.metadata: Record<string, unknown>` with:

```typescript
export interface AnalyzeMetadata {
  pipeline_version: string;
  git_commit: string;
  wood_leaf_backend: string;
  input_sha256: string;
  checkpoint_sha256: string | null;
  algorithms: Record<string, string>;
  evidence_status: string;
  candidate_status: string;
  n_input_points: number;
  status: string;
  input_file?: string | null;
}
```

Create `apps/web/src/lib/evidence.ts`:

```typescript
import type { AnalyzeMetadata } from './api';

export function formatBackendLabel(metadata: AnalyzeMetadata): string {
  return metadata.wood_leaf_backend === 'tlsep'
    ? 'Baseline: tlsep'
    : `Experimental candidate: ${metadata.wood_leaf_backend}`;
}

export function formatEvidenceStatus(metadata: AnalyzeMetadata): string {
  if (metadata.candidate_status === 'candidate_not_evaluated') {
    return 'PointNet++ candidate not evaluated; tlsep result shown.';
  }
  if (metadata.evidence_status === 'experimental') {
    return 'Experimental result; not promoted to the default pipeline.';
  }
  return 'Baseline result with run provenance attached.';
}
```

- [ ] **Step 7: Render metadata in the viewer**

After the summary cards, add a bordered evidence panel that shows:

- `formatBackendLabel(analysis.metadata)`
- `formatEvidenceStatus(analysis.metadata)`
- pipeline version and first 12 Git SHA characters
- first 12 input SHA characters
- checkpoint SHA or `ไม่มี checkpoint (tlsep baseline)`
- species algorithm status `Stub`

Do not claim the uploaded `.ply` is the same file whose analysis result is displayed unless its backend-generated input hash can be matched; label it as the uploaded analysis input.

- [ ] **Step 8: Replace landing claims with manifest-backed copy**

Import `CORE_DEMO_EVIDENCE`. Apply these exact claim changes while preserving the existing Tailwind/server-component layout:

- Hero: `ประเมินการกักเก็บคาร์บอนจากต้นไม้` instead of `แปลงต้นไม้เป็น Carbon Credits`.
- Explain that the system estimates biomass/carbon/CO2e; formal credit certification remains outside the prototype.
- Feature title: `Evidence-gated Wood–Leaf Segmentation`; description names `tlsep` as baseline and PointNet++ as Experimental.
- Replace the ambiguous `0.61 Wood/Leaf IoU` metric with separate `Wood IoU 0.418` and `Leaf IoU 0.808`, labelled Wan held-out validation.
- Display DBH MAE `1.1673846154 cm`, labelled Demol isolated-tree 65-tree scope.
- Remove `100×` cost reduction and `<10 นาที` processing claims.
- Mark anti-fraud, GIS, Marketplace, Payment, Certificate, mobile-photo input, and WebSocket as `Planned` wherever present.

- [ ] **Step 9: Run API/web focused gates and commit Task 4**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/api/tests/test_upload_analyze.py -v --no-cov
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web test --run
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web type-check
```

Expected: focused API test, all Vitest tests, and TypeScript check pass.

```powershell
git add services/api/app/schemas/analyze.py services/api/tests/test_upload_analyze.py apps/web/src/lib/api.ts apps/web/src/lib/evidence.ts apps/web/src/lib/evidence.test.ts apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx apps/web/src/app/page.tsx
git commit -m "feat: surface verified pipeline evidence"
```

---

### Task 5: Repository documentation and CI honesty gates

**Files:**

- Modify: `.github/workflows/ci-ml.yml`
- Modify: `docs/PROJECT_SPEC.md`
- Modify: `docs/ml/PIPELINE.md`
- Modify: `docs/ml/WOODLEAF_RESULTS.md`
- Modify: `README.md`

**Interfaces:**

- Consumes: truth manifest and `sync_truth.py --check`.
- Produces: repository prose consistent with the code and CI that fails on real ML/test drift.

- [ ] **Step 1: Add a failing static CI contract test**

Append to `scripts/tests/test_sync_truth.py`:

```python
def test_ml_ci_does_not_swallow_test_failures():
    workflow = Path(".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    assert "pytest tests/ -v --tb=short || true" not in workflow
    assert "scripts/sync_truth.py --check" in workflow
    assert "scripts/run_core_demo.py" in workflow
```

- [ ] **Step 2: Run the test and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests/test_sync_truth.py::test_ml_ci_does_not_swallow_test_failures -v --no-cov
```

Expected: assertion fails because CI contains `|| true` and lacks the new gates.

- [ ] **Step 3: Make ML CI fail honestly**

In `.github/workflows/ci-ml.yml`:

- extend path triggers to the manifest, controlled docs, `scripts/sync_truth.py`, and generated web evidence;
- replace `pytest tests/ -v --tb=short || true` with `pytest tests/ -v --tb=short`;
- add `python scripts/run_core_demo.py --output-dir ../../temp/ci-core-demo --repo-root ../..` from `services/ml`;
- add `python ../../scripts/sync_truth.py --check` from `services/ml`;
- keep Ruff format advisory separate from the strict test result.

- [ ] **Step 4: Correct prose outside generated blocks**

Perform a line-by-line audit of the four documents and make these corrections:

- eight-step algorithms match the capability matrix;
- `tlsep` is default and PointNet++ is Experimental;
- species stage is Stub;
- QSM is RANSAC DBH + max-Z height + taper volume, not TreeQSM;
- Wan figures retain all decimals and held-out-selection limitation;
- Demol figures state isolated-tree preprocessing and exclude carbon validation;
- allometric source wording points to `species_db.csv` and the code fallback;
- current async path says polling and local shared filesystem, not WebSocket production processing;
- remove certified-credit, GIS, Marketplace, Payment, and complete-mobile claims;
- TreeQ naming replaces CarbonScan naming in the touched core sections.

Run an explicit forbidden-claim scan and inspect every match rather than deleting terms blindly:

```powershell
rg -n "TreeQSM|CSF|pit-free|certified|100×|100x|WebSocket|Marketplace|Payment Gateway|PointNet\+\+.*default|CarbonScan AI" docs/PROJECT_SPEC.md docs/ml/PIPELINE.md docs/ml/WOODLEAF_RESULTS.md README.md apps/web/src/app/page.tsx
```

Every remaining occurrence must be labelled historical, incorrect, Experimental, Stub, Planned, or out of scope.

- [ ] **Step 5: Run truth/docs/CI checks and commit Task 5**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' scripts/sync_truth.py --check
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests/test_sync_truth.py -v --no-cov
git diff --check
```

Expected: all commands exit `0`.

```powershell
git add .github/workflows/ci-ml.yml docs/PROJECT_SPEC.md docs/ml/PIPELINE.md docs/ml/WOODLEAF_RESULTS.md README.md scripts/tests/test_sync_truth.py
git commit -m "docs: align project claims with verified evidence"
```

---

### Task 6: Conservative NSC DOCX builder and new report

**Files:**

- Create: `scripts/build_truth_aligned_report.py`
- Create: `scripts/tests/test_build_truth_aligned_report.py`
- Read only: `C:\Users\Acer\Downloads\เล่มโครงงานNSC_แก้ไขแล้ว_ปรับปรุง (3).docx`
- Write only: `C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx`

**Interfaces:**

- Produces: `replace_anchor(document, anchor, replacement)`, `build_report(source, output, manifest) -> ReportAudit`, CLI with required `--source`, `--output`, `--manifest`.
- Guarantees: exact-one anchor match, copy-first output, source SHA unchanged, image/table counts preserved, no repository output.

- [ ] **Step 1: Write failing builder tests using a synthetic DOCX**

```python
# scripts/tests/test_build_truth_aligned_report.py
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from docx import Document

from scripts.build_truth_aligned_report import build_report


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source(path: Path) -> None:
    doc = Document()
    doc.add_paragraph("Tree Segmentation เมื่อได้รับแบบจำลอง CHM แล้ว ระบบจะจำแนกพื้นที่")
    doc.add_paragraph("Wood-Leaf Separation ในขั้นตอนดังกล่าว ระบบจะใช้ Deep Learning เช่น PointNet++")
    doc.add_paragraph("QSM (Cylinder Fitting) ใช้งาน TreeQSM (Least Squares Cylinder Fitting)")
    doc.add_paragraph("Allometric Carbon Calc TGO ยอมรับได้ (ร้อยละ ±10)")
    doc.add_paragraph("ผลบนชุดทดสอบ PointNet++ ทำได้ 0.978")
    doc.add_paragraph("6.5.2.1 การทดสอบ Wood-Leaf บนไม้จริง (Wan et al., 2021)")
    doc.add_paragraph("ระบบอัปโหลดและการประมวลผลแบบอะซิงโครนัส ผ่าน WebSocket")
    doc.add_paragraph("ระบบแผนที่ภูมิสารสนเทศ (GIS Map) พร้อมใช้งาน")
    doc.add_paragraph("ตลาดกลางคาร์บอนเครดิต (Marketplace) พร้อมใช้งาน")
    doc.add_paragraph("การออกใบรับรองและการซื้อขาย พร้อมใช้งาน")
    doc.add_paragraph("[7] TGO reference")
    doc.add_paragraph("[18] Demol reference")
    doc.add_paragraph("[20] Wan reference")
    doc.add_table(rows=1, cols=1).cell(0, 0).text = "kept"
    doc.save(path)


def make_manifest(path: Path) -> None:
    path.write_text(
        json.dumps({"validation": {"wan_held_out": {"wood_iou": 0.418, "leaf_iou": 0.808}}}),
        encoding="utf-8",
    )


def test_builder_never_changes_source_and_preserves_structure(tmp_path: Path):
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    manifest = tmp_path / "manifest.json"
    make_source(source)
    make_manifest(manifest)
    before = sha(source)
    audit = build_report(source, output, manifest)
    assert sha(source) == before
    assert output.is_file()
    assert audit.source_sha256 == before
    assert audit.tables_before == audit.tables_after == 1


def test_builder_aborts_when_anchor_is_missing(tmp_path: Path):
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    manifest = tmp_path / "manifest.json"
    make_source(source)
    make_manifest(manifest)
    doc = Document(source)
    doc.paragraphs[1].text = "anchor removed"
    doc.save(source)
    with pytest.raises(ValueError, match="PointNet"):
        build_report(source, output, manifest)
    assert not output.exists()
```

- [ ] **Step 2: Run builder tests and observe RED**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests/test_build_truth_aligned_report.py -v --no-cov
```

Expected: collection fails because the builder does not exist.

- [ ] **Step 3: Implement copy-first, exact-anchor patching**

The builder must:

1. Read and hash the source.
2. Load the source once to count paragraphs/tables/inline shapes/sections and capture page geometry.
3. Validate each required anchor occurs in exactly one paragraph before creating output.
4. Copy source to a sibling temporary output path.
5. Replace paragraph text while copying the first run's formatting and leaving paragraph properties, tables, images, section properties, headers, and footers untouched.
6. Save, reopen, and compare table/image/section counts and source hash.
7. Atomically replace the requested new output only after all structural checks pass.
8. Delete the temporary output on any exception.

Required anchors and replacement subjects:

- `Tree Segmentation เมื่อได้รับแบบจำลอง CHM แล้ว` — complete the watershed explanation.
- `Wood-Leaf Separation ในขั้นตอนดังกล่าว` — baseline `tlsep`; PointNet++ Experimental and evidence-gated.
- `QSM (Cylinder Fitting)` — actual RANSAC DBH, max-Z height, taper volume, branch count limitation; not TreeQSM.
- `Allometric Carbon Calc` — actual Demol scope and exact DBH/height/volume metrics; remove TGO ±10 acceptance.
- `ผลบนชุดทดสอบ PointNet++` — label `0.977625` as synthetic mean IoU only.
- `6.5.2.1 การทดสอบ Wood-Leaf บนไม้จริง` — exact Wan metrics and held-out limitation.
- `ระบบอัปโหลดและการประมวลผลแบบอะซิงโครนัส` — Implemented API/job worker with polling and shared-local-filesystem limitation; WebSocket Planned.
- `ระบบแผนที่ภูมิสารสนเทศ (GIS Map)` — Planned.
- `ตลาดกลางคาร์บอนเครดิต (Marketplace)` — Planned; no certificate/payment implementation.
- `การออกใบรับรองและการซื้อขาย` — Planned and not certified credit issuance.
- references containing `Wan`, `Demol`, and `TGO` — correct titles/links from repository evidence; do not invent bibliographic fields.

Use `[Implemented]`, `[Experimental]`, `[Stub]`, and `[Planned]` labels in the replacement prose. Do not alter A4/page geometry in this task.

- [ ] **Step 4: Run focused builder tests**

Run:

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests/test_build_truth_aligned_report.py -v --no-cov
```

Expected: both tests pass.

- [ ] **Step 5: Build the new report outside the sandboxed repo**

Run the builder with escalated filesystem permission because Downloads is outside `D:\Project_Carbon`:

```powershell
& 'temp/truth-venv/Scripts/python.exe' scripts/build_truth_aligned_report.py --source 'C:\Users\Acer\Downloads\เล่มโครงงานNSC_แก้ไขแล้ว_ปรับปรุง (3).docx' --output 'C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx' --manifest 'docs/evidence/core_demo_manifest.json'
```

Expected: ASCII-safe JSON audit reports source/output SHA-256, anchor count, table/image/section counts, and `source_unchanged: true`.

- [ ] **Step 6: Render and inspect every page**

Use the bundled document renderer:

```powershell
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\Acer\.codex\plugins\cache\openai-primary-runtime\documents\26.715.12143\skills\documents\render_docx.py' 'C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx' --output_dir 'D:\Project_Carbon\temp\report-render' --emit_pdf
```

Inspect every generated page PNG at 100% for clipping, overlap, missing glyphs, broken tables/images, and page-break regressions. If LibreOffice/soffice is unavailable, perform the structural checks below and record the render limitation honestly:

```powershell
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\Acer\.codex\plugins\cache\openai-primary-runtime\documents\26.715.12143\skills\documents\scripts\section_audit.py' 'C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx'
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\Acer\.codex\plugins\cache\openai-primary-runtime\documents\26.715.12143\skills\documents\scripts\images_audit.py' 'C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx'
```

- [ ] **Step 7: Commit only the reusable builder and tests**

Confirm the DOCX is not under the repository and not in `git status`, then run:

```powershell
git add scripts/build_truth_aligned_report.py scripts/tests/test_build_truth_aligned_report.py
git commit -m "feat(docs): build truth-aligned NSC report safely"
```

---

### Task 7: Full verification, scope review, and GitHub publication

**Files:**

- Verify: all files changed by Tasks 1–6.
- Publish: current `codex/truth-repro-core-demo` branch only after every required gate is read and classified.

- [ ] **Step 1: Run the full ML suite and deterministic demo fresh**

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/ml/tests -v
Remove-Item -Recurse -Force -LiteralPath 'temp/final-core-demo' -ErrorAction SilentlyContinue
& 'temp/truth-venv/Scripts/python.exe' services/ml/scripts/run_core_demo.py --output-dir temp/final-core-demo --repo-root .
```

Expected: pytest exits `0`; the CLI exits `0`; verification summary says `reproducible: true` with two matching result hashes and PLY hashes.

- [ ] **Step 2: Run the full API suite**

```powershell
& 'temp/truth-venv/Scripts/python.exe' -m pytest services/api/tests -v
```

Expected: all non-database tests pass; database-dependent tests may skip only for their existing explicit no-`DATABASE_URL` condition. Record exact pass/skip counts.

- [ ] **Step 3: Run web tests, typecheck, lint, and production build**

```powershell
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web test --run
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web type-check
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web lint
& 'C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd' --dir apps/web build
```

Expected: each command exits `0`. A passing test does not substitute for typecheck/lint/build.

- [ ] **Step 4: Run truth, builder, and static honesty checks**

```powershell
& 'temp/truth-venv/Scripts/python.exe' scripts/sync_truth.py --check
& 'temp/truth-venv/Scripts/python.exe' -m pytest scripts/tests -v --no-cov
rg -n "100×|100x|TGO.*±10|PointNet\+\+.*production|ออกใบรับรองคาร์บอนเครดิต|certified carbon credit" README.md docs apps/web/src services
git diff --check
```

Inspect each `rg` match. Historical/Planned/negative statements are allowed; an unqualified active claim fails the gate.

- [ ] **Step 5: Review Git scope and secret/large-file risk**

```powershell
$base = git merge-base HEAD origin/main
git status --short --branch
git diff --stat "$base..HEAD"
git diff --name-only "$base..HEAD"
git ls-files | rg "\.(pt|pth|onnx|h5|ckpt|docx)$|(^|/)\.env($|\.)|secrets"
git diff "$base..HEAD" | rg -n "SUPABASE_SERVICE_ROLE|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|api[_-]?key|access[_-]?token"
```

Expected: no model binary, DOCX, environment file, secret, or unrelated user change is included. If working-tree changes are mixed, stage explicit in-scope paths only.

- [ ] **Step 6: Seal final generated evidence without a self-referential SHA loop**

Rerun the core demo at the last implementation commit. Store that value as `core_demo.analyzed_commit`; it identifies the code that produced the evidence. The evidence-seal commit necessarily has a different SHA and must not trigger another regeneration. Then rerun `sync_truth.py --check`, focused truth tests, and `git diff --check` before creating the evidence-seal commit:

```powershell
git add docs/evidence/core_demo_manifest.json docs/CAPABILITY_MATRIX.md apps/web/src/generated/core-demo-evidence.ts docs/PROJECT_SPEC.md docs/ml/PIPELINE.md docs/ml/WOODLEAF_RESULTS.md
git commit -m "chore: seal verified core demo evidence"
```

- [ ] **Step 7: Verify GitHub prerequisites and publish a draft PR**

```powershell
gh --version
gh auth status
git remote -v
git status --short --branch
git push -u origin codex/truth-repro-core-demo
gh repo view --json nameWithOwner,defaultBranchRef
gh pr create --draft --fill --head codex/truth-repro-core-demo
```

Do not push if any required verification failed, the worktree is dirty with unrelated files, `gh auth status` fails, or the remote target cannot be identified. The draft PR body must state exact test counts, skipped/blocked checks, DOCX render status, true metrics, and the reason PointNet++ remains Experimental.

---

## Plan Self-Review Checklist

- [x] Every design section has an implementation task or an explicit out-of-scope constraint.
- [x] All production behavior starts with a failing test; generated JSON/TypeScript and CI configuration are verified by deterministic checks.
- [x] Function/type names are consistent across ML, API, and web tasks.
- [x] The runner separates runtime fields from normalized hashes and does not call a tolerance comparison byte-identical.
- [x] PointNet++ cannot be promoted by Wood IoU alone.
- [x] The Word source is hashed, copied, anchor-validated, structurally checked, and never committed.
- [x] GitHub publication occurs only after fresh full verification and scope/secret review.
