"""Contract tests for importing a reviewed independent PointNet result."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.review_pointnet_evidence import import_reviewed_result
from scripts.sync_truth import CONTROLLED_DOCS, TRUTH_END, TRUTH_START, load_manifest, render_truth_block, sync


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _manifest() -> dict[str, object]:
    return {
        "schema_version": "1",
        "project": "TreeQ Carbon Platform",
        "baseline": {"backend": "tlsep", "status": "Implemented"},
        "candidate": {
            "backend": "pointnet",
            "display_name": "PointNet++",
            "status": "Experimental",
            "promoted": False,
            "promotion_evidence": {
                "all_passed": False,
                "failed_criteria": ["independent_real_test_not_recorded"],
                "policy": "Promote only after reviewed independent evidence.",
            },
        },
        "validation": {
            "wan_held_out": {
                "wood_iou": 0.418,
                "leaf_iou": 0.808,
                "mean_iou": 0.613,
                "accuracy": 0.831,
            },
            "demol_65": {"dbh_mae_cm": 1.1673846154, "volume_mape_pct": 18.7650916186},
        },
        "capabilities": [
            {
                "name": "5b. PointNet++ wood/leaf candidate",
                "status": "Experimental",
                "implementation": "candidate",
                "evidence": "historical",
                "claim": "historical",
            },
            {
                "name": "Species classification",
                "status": "Stub",
                "implementation": "stub",
                "evidence": "stub.py",
                "claim": "not implemented",
            },
        ],
        "core_demo": {
            "reproducible": True,
            "analyzed_commit": "a" * 40,
            "git_dirty": False,
            "pipeline_version": "0.3.0",
            "input_sha256": "b" * 64,
            "normalized_result_sha256": "c" * 64,
            "segmented_ply_sha256": "d" * 64,
            "total_trees": 3,
            "total_carbon_kg": 1320.39,
            "total_co2eq_kg": 4841.48,
        },
    }


def _result(verdict: str, *, promote: bool, failed: list[str]) -> dict[str, object]:
    formal_promote = verdict in {"POINT_ESTIMATE_PASS_ONLY", "PROMOTE_POINTNET"}
    return {
        "schema_version": "1",
        "experiment_id": "synthetic-independent-eval",
        "protocol_sha256": "",
        "freeze_manifest_sha256": "",
        "external_manifest_sha256": "",
        "checkpoint_sha256": "e" * 64,
        "evaluation_git_commit": "f" * 40,
        "baseline": {
            "external_segmentation": {"macro": {"wood_iou": 0.4000000000000001}},
            "downstream": {
                "dbh_mae_cm": 1.0000000000000002,
                "height_mae_m": 0.5000000000000001,
                "volume_mape_pct": 10.000000000000002,
                "measurable_trees": 65,
            },
        },
        "candidate": {
            "external_segmentation": {"macro": {"wood_iou": 0.6000000000000001}},
            "downstream": {
                "dbh_mae_cm": 0.9999999999999999,
                "height_mae_m": 0.4999999999999999,
                "volume_mape_pct": 9.999999999999998,
                "measurable_trees": 65,
            },
        },
        "paired_deltas": {},
        "confidence_intervals": {},
        "formal_gate": {
            "promote": formal_promote,
            "status": "promoted" if formal_promote else "rejected",
            "failed_criteria": failed,
            "baseline": {
                "wood_iou": 0.4000000000000001,
                "dbh_mae_cm": 1.0000000000000002,
                "height_mae_m": 0.5000000000000001,
                "volume_mape_pct": 10.000000000000002,
                "measurable_trees": 65,
            },
            "candidate": {
                "wood_iou": 0.6000000000000001,
                "dbh_mae_cm": 0.9999999999999999,
                "height_mae_m": 0.4999999999999999,
                "volume_mape_pct": 9.999999999999998,
                "measurable_trees": 65,
            },
        },
        "verdict": {"verdict": verdict, "promote": promote},
        "limitations": ["Synthetic fixture only.", "This result does not change the default."],
    }


@pytest.fixture
def reviewed_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    evidence = repo / "docs/evidence/pointnet_independent_eval"
    protocol = evidence / "protocol.json"
    freeze = evidence / "freeze_manifest.json"
    external = evidence / "external_dataset_manifest.json"
    _write_json(protocol, {"schema_version": "1", "experiment_id": "synthetic-independent-eval"})
    _write_json(
        freeze,
        {
            "schema_version": "1",
            "experiment_id": "synthetic-independent-eval",
            "protocol_sha256": _sha256(protocol),
            "training_git_commit": "1" * 40,
            "winner": {"checkpoint_sha256": "e" * 64},
        },
    )
    _write_json(
        external,
        {
            "schema_version": "1",
            "experiment_id": "synthetic-independent-eval",
            "protocol_sha256": _sha256(protocol),
            "freeze_manifest_sha256": _sha256(freeze),
            "checkpoint_sha256": "e" * 64,
        },
    )
    result = _result("FAIL_METRICS", promote=False, failed=["wood_iou_not_improved"])
    result["protocol_sha256"] = _sha256(protocol)
    result["freeze_manifest_sha256"] = _sha256(freeze)
    result["external_manifest_sha256"] = _sha256(external)
    result_path = evidence / "result.json"
    _write_json(result_path, result)
    manifest_path = repo / "docs/evidence/core_demo_manifest.json"
    _write_json(manifest_path, _manifest())
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "synthetic evidence")
    return repo, result_path, manifest_path


@pytest.mark.parametrize(
    ("verdict", "promote", "failed", "all_passed"),
    [
        ("INVALID_EVIDENCE", False, ["provenance_invalid"], False),
        ("FAIL_METRICS", False, ["wood_iou_not_improved"], False),
        ("POINT_ESTIMATE_PASS_ONLY", False, [], False),
        ("PROMOTE_POINTNET", True, [], True),
    ],
)
def test_imports_all_declared_verdicts_without_auto_promotion(
    reviewed_repo: tuple[Path, Path, Path],
    verdict: str,
    promote: bool,
    failed: list[str],
    all_passed: bool,
):
    repo, result_path, manifest_path = reviewed_repo
    result = _result(verdict, promote=promote, failed=failed)
    evidence = result_path.parent
    result["protocol_sha256"] = _sha256(evidence / "protocol.json")
    result["freeze_manifest_sha256"] = _sha256(evidence / "freeze_manifest.json")
    result["external_manifest_sha256"] = _sha256(evidence / "external_dataset_manifest.json")
    _write_json(result_path, result)
    _git(repo, "add", str(result_path.relative_to(repo)))
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo, check=False
    ).returncode:
        _git(repo, "commit", "-m", f"{verdict} result")

    before = json.loads(manifest_path.read_text(encoding="utf-8"))
    imported = import_reviewed_result(result_path, manifest_path, repo_root=repo)

    after = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert after["baseline"] == before["baseline"]
    assert after["candidate"]["backend"] == before["candidate"]["backend"]
    assert after["candidate"]["display_name"] == before["candidate"]["display_name"]
    assert after["candidate"]["status"] == "Experimental"
    assert after["candidate"]["promoted"] is False
    assert after["core_demo"] == before["core_demo"]
    assert after["capabilities"][1] == before["capabilities"][1]
    assert after["candidate"]["promotion_evidence"]["all_passed"] is all_passed
    assert after["candidate"]["promotion_evidence"]["failed_criteria"] == failed
    assert after["validation"]["pointnet_independent"]["verdict"] == verdict
    assert after["validation"]["pointnet_independent"]["result_sha256"] == _sha256(result_path)
    assert imported == after


def test_import_rejects_untracked_or_non_finite_result(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    _git(repo, "rm", "--cached", str(result_path.relative_to(repo)))
    with pytest.raises(ValueError, match="Git-tracked"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)

    _git(repo, "add", str(result_path.relative_to(repo)))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["baseline"]["external_segmentation"]["macro"]["wood_iou"] = float("nan")
    result_path.write_text(json.dumps(result), encoding="utf-8")
    _git(repo, "add", str(result_path.relative_to(repo)))
    _git(repo, "commit", "-m", "non-finite result")
    with pytest.raises(ValueError, match="finite"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_manifest_validation_rehashes_imported_result_and_renders_exact_metrics(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    import_reviewed_result(result_path, manifest_path, repo_root=repo)
    manifest = load_manifest(manifest_path, repo_root=repo)
    truth = render_truth_block(manifest)
    assert "FAIL_METRICS" in truth
    assert "0.4000000000000001" in truth
    assert "0.9999999999999999" in truth
    assert "0.418" in truth
    assert "1.1673846154" in truth

    result_path.write_text(result_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed Git version"):
        load_manifest(manifest_path, repo_root=repo)


def test_sync_check_rejects_result_tampering_after_import(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    import_reviewed_result(result_path, manifest_path, repo_root=repo)
    for relative in CONTROLLED_DOCS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{TRUTH_START}\n{TRUTH_END}\n", encoding="utf-8")

    assert sync(repo, check=False) == 0
    assert sync(repo, check=True) == 0
    result_path.write_text(result_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed Git version"):
        sync(repo, check=True)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda result: result.update({"unexpected": 1}), "missing or extra schema fields"),
        (lambda result: result.pop("confidence_intervals"), "missing or extra schema fields"),
        (
            lambda result: result["baseline"]["downstream"].update({"dbh_mae_cm": True}),
            "not a boolean",
        ),
        (
            lambda result: result["formal_gate"].update({"status": "promoted"}),
            "only passed verdicts",
        ),
    ],
)
def test_importer_rejects_result_schema_and_gate_aliases(
    reviewed_repo: tuple[Path, Path, Path], mutate, message: str
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    mutate(result)
    _write_json(result_path, result)
    _git(repo, "add", str(result_path.relative_to(repo)))
    _git(repo, "commit", "-m", "malformed result")

    with pytest.raises(ValueError, match=message):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)
