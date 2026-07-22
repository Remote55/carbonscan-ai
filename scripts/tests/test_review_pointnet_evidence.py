"""Production-shaped contract tests for reviewed PointNet evidence imports."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.review_pointnet_evidence import import_reviewed_result
from scripts.sync_truth import CONTROLLED_DOCS, TRUTH_END, TRUTH_START, load_manifest, render_truth_block, sync


ROOT = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _manifest() -> dict[str, object]:
    return {
        "schema_version": "1", "project": "TreeQ Carbon Platform",
        "baseline": {"backend": "tlsep", "status": "Implemented"},
        "candidate": {"backend": "pointnet", "display_name": "PointNet++", "status": "Experimental", "promoted": False,
                      "promotion_evidence": {"all_passed": False, "failed_criteria": ["independent_real_test_not_recorded"], "policy": "Promote only after reviewed independent evidence."}},
        "validation": {"wan_held_out": {"wood_iou": 0.418, "leaf_iou": 0.808, "mean_iou": 0.613, "accuracy": 0.831},
                       "demol_65": {"dbh_mae_cm": 1.1673846154, "volume_mape_pct": 18.7650916186}},
        "capabilities": [
            {"name": "5b. PointNet++ wood/leaf candidate", "status": "Experimental", "implementation": "candidate", "evidence": "historical", "claim": "historical"},
            {"name": "Species classification", "status": "Stub", "implementation": "stub", "evidence": "stub.py", "claim": "not implemented"},
        ],
        "core_demo": {"reproducible": True, "analyzed_commit": "a" * 40, "git_dirty": False, "pipeline_version": "0.3.0", "input_sha256": "b" * 64, "normalized_result_sha256": "c" * 64, "segmented_ply_sha256": "d" * 64, "total_trees": 3, "total_carbon_kg": 1320.39, "total_co2eq_kg": 4841.48},
    }


def _metrics(confusion: dict[str, int]) -> dict[str, object]:
    wood, wood_leaf, leaf_wood, leaf = (confusion[key] for key in ("wood_as_wood", "wood_as_leaf", "leaf_as_wood", "leaf_as_leaf"))
    wood_iou = wood / (wood + wood_leaf + leaf_wood) if wood + wood_leaf + leaf_wood else 1.0
    leaf_iou = leaf / (leaf + wood_leaf + leaf_wood) if leaf + wood_leaf + leaf_wood else 1.0
    return {"wood_iou": wood_iou, "leaf_iou": leaf_iou, "mean_iou": (wood_iou + leaf_iou) / 2.0, "accuracy": (wood + leaf) / sum(confusion.values()), "confusion": confusion}


def _segmentation(confusion: dict[str, int]) -> dict[str, object]:
    one = _metrics(confusion)
    doubled = {key: value * 2 for key, value in confusion.items()}
    return {"per_tree": {"tree-a": copy.deepcopy(one), "tree-b": copy.deepcopy(one)}, "macro": {key: one[key] for key in ("wood_iou", "leaf_iou", "mean_iou", "accuracy")}, "pooled": _metrics(doubled)}


def _external(protocol_sha: str, freeze_sha: str, checkpoint: str, experiment: str) -> dict[str, object]:
    tree_ids = [f"tree-{index:02d}" for index in range(1, 11)]
    files = []
    for tree_id in tree_ids:
        for part in ("leaf", "wood"):
            files.append({"filename": f"{tree_id}_{part}.pcd", "tree_id": tree_id, "part": part, "publisher_md5": "a" * 32, "publisher_size_bytes": 1, "sha256": "b" * 64, "size_bytes": 1})
    return {"schema_version": "1", "experiment_id": experiment, "protocol_sha256": protocol_sha, "freeze_manifest_sha256": freeze_sha, "checkpoint_sha256": checkpoint,
            "record": {"provider": "Zenodo", "record_id": 6831378, "doi": "10.5281/zenodo.6831378", "license": "CC-BY-4.0"}, "tree_ids": tree_ids, "files": files}


def _freeze(protocol: dict[str, object], protocol_sha: str, training_commit: str, checkpoint: str) -> dict[str, object]:
    metrics = {"wood_iou": 0.5, "leaf_iou": 0.5, "mean_iou": 0.5, "accuracy": 0.5}
    return {"schema_version": "1", "experiment_id": protocol["experiment_id"], "protocol_sha256": protocol_sha, "wan_manifest_sha256": "c" * 64, "training_runs_sha256": "d" * 64,
            "training_git_commit": training_commit, "working_tree_clean": True, "training_command": ["python", "-m", "scripts.pointnet_evidence", "train"], "environment": {}, "architecture": "PointNet2SegSSG",
            "training_configuration": protocol["training"], "wan_evidence": {"schema_version": "1", "config": {}, "sources": [], "outputs": {"train": {}, "dev": {}}},
            "winner": {"seed": 1, "selected_epoch": 1, "dev_metrics": metrics, "checkpoint_file": "winner.pt", "checkpoint_sha256": checkpoint, "state_dict_sha256": "e" * 64},
            "rerun_evidence": {"seed": 1, "best_epoch": 1, "best_macro_tile_wood_iou": 0.5, "state_dict_sha256": "e" * 64, "checkpoint_file": "seed-1-rerun.pt", "checkpoint_sha256": checkpoint, "reproducible": True}}


def _result(verdict: str, evaluation_commit: str, hashes: dict[str, str]) -> dict[str, object]:
    baseline = {"external_segmentation": _segmentation({"wood_as_wood": 2, "wood_as_leaf": 2, "leaf_as_wood": 1, "leaf_as_leaf": 2}),
                "downstream": {"dbh_mae_cm": 1.0, "height_mae_m": 0.5, "volume_mape_pct": 10.0, "measurable_trees": 65}}
    failing = verdict in {"FAIL_METRICS", "INVALID_EVIDENCE"}
    candidate = {"external_segmentation": _segmentation({"wood_as_wood": 2 if failing else 3, "wood_as_leaf": 2 if failing else 1, "leaf_as_wood": 1, "leaf_as_leaf": 2 if failing else 3}),
                 "downstream": {"dbh_mae_cm": 1.1 if failing else 0.9, "height_mae_m": 0.5 if failing else 0.4, "volume_mape_pct": 10.0 if failing else 9.0, "measurable_trees": 65}}
    base = {"wood_iou": baseline["external_segmentation"]["macro"]["wood_iou"], **baseline["downstream"]}
    cand = {"wood_iou": candidate["external_segmentation"]["macro"]["wood_iou"], **candidate["downstream"]}
    delta_fields = {"wood_iou_delta": ("Wood IoU candidate-minus-baseline", "proportion", "wood_iou"), "dbh_abs_error_delta": ("DBH absolute-error candidate-minus-baseline", "cm", "dbh_mae_cm"), "height_abs_error_delta": ("Height absolute-error candidate-minus-baseline", "m", "height_mae_m"), "volume_ape_delta": ("Volume APE candidate-minus-baseline", "percent", "volume_mape_pct")}
    intervals = {}
    paired = {}
    for key, (name, unit, metric) in delta_fields.items():
        estimate = cand[metric] - base[metric]
        lower, upper = (estimate, estimate) if verdict == "PROMOTE_POINTNET" else (0.0, 0.2) if key == "wood_iou_delta" and not failing else (estimate - 0.1, estimate + 0.1)
        intervals[key] = {"estimate": estimate, "lower": lower, "upper": upper}
        paired[key] = {"name": name, "unit": unit, "estimate": estimate}
    failed = ["wood_iou_improves", "dbh_mae_non_regression"] if failing else []
    return {"schema_version": "1", "experiment_id": "pointnet-independent-eval-2026-07-16", **hashes, "checkpoint_sha256": "f" * 64, "evaluation_git_commit": evaluation_commit,
            "baseline": baseline, "candidate": candidate, "paired_deltas": paired, "confidence_intervals": intervals,
            "formal_gate": {"promote": not failing, "status": "rejected" if failing else "promoted", "failed_criteria": failed, "baseline": base, "candidate": cand},
            "verdict": {"verdict": verdict, "promote": verdict == "PROMOTE_POINTNET"}, "limitations": ["Synthetic production-shaped fixture.", "No automatic default promotion."]}


@pytest.fixture
def reviewed_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"; repo.mkdir(); _git(repo, "init"); _git(repo, "config", "user.email", "test@example.com"); _git(repo, "config", "user.name", "Test")
    evidence = repo / "docs/evidence/pointnet_independent_eval"
    protocol = json.loads((ROOT / "docs/evidence/pointnet_independent_eval/protocol.json").read_text(encoding="utf-8"))
    protocol_path = evidence / "protocol.json"; _write(protocol_path, protocol)
    manifest_path = repo / "docs/evidence/core_demo_manifest.json"; _write(manifest_path, _manifest())
    _git(repo, "add", "."); _git(repo, "commit", "-m", "training provenance")
    training = _git(repo, "rev-parse", "HEAD")
    freeze_path = evidence / "freeze_manifest.json"; _write(freeze_path, _freeze(protocol, _sha(protocol_path), training, "f" * 64))
    external_path = evidence / "external_dataset_manifest.json"; _write(external_path, _external(_sha(protocol_path), _sha(freeze_path), "f" * 64, str(protocol["experiment_id"])))
    _git(repo, "add", "."); _git(repo, "commit", "-m", "evaluation inputs")
    evaluation = _git(repo, "rev-parse", "HEAD")
    result_path = evidence / "result.json"; _write(result_path, _result("FAIL_METRICS", evaluation, {"protocol_sha256": _sha(protocol_path), "freeze_manifest_sha256": _sha(freeze_path), "external_manifest_sha256": _sha(external_path)}))
    _git(repo, "add", "."); _git(repo, "commit", "-m", "result after evaluation")
    return repo, result_path, manifest_path


def _commit_result(repo: Path, result_path: Path, result: dict[str, object], message: str = "updated result") -> None:
    _write(result_path, result); _git(repo, "add", result_path.relative_to(repo).as_posix())
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, check=False).returncode:
        _git(repo, "commit", "-m", message)


@pytest.mark.parametrize("verdict", ["INVALID_EVIDENCE", "FAIL_METRICS", "POINT_ESTIMATE_PASS_ONLY", "PROMOTE_POINTNET"])
def test_imports_all_declared_verdicts_without_auto_promotion(reviewed_repo: tuple[Path, Path, Path], verdict: str):
    repo, result_path, manifest_path = reviewed_repo
    hashes = {key: _sha(result_path.parent / name) for key, name in (("protocol_sha256", "protocol.json"), ("freeze_manifest_sha256", "freeze_manifest.json"), ("external_manifest_sha256", "external_dataset_manifest.json"))}
    result = _result(verdict, _git(repo, "rev-parse", "HEAD~1"), hashes); _commit_result(repo, result_path, result, verdict)
    before = json.loads(manifest_path.read_text(encoding="utf-8")); after = import_reviewed_result(result_path, manifest_path, repo_root=repo)
    assert after["baseline"] == before["baseline"] and after["core_demo"] == before["core_demo"]
    assert after["candidate"]["status"] == "Experimental" and after["candidate"]["promoted"] is False
    assert after["capabilities"][1] == before["capabilities"][1]
    assert after["validation"]["pointnet_independent"]["verdict"] == verdict
    assert after["candidate"]["promotion_evidence"]["all_passed"] is (verdict == "PROMOTE_POINTNET")


@pytest.mark.parametrize("mutate, message", [
    (lambda result: result["formal_gate"].update({"promote": True, "status": "promoted", "failed_criteria": []}), "formal gate"),
    (lambda result: result["confidence_intervals"]["wood_iou_delta"].update({"lower": 0.3}), "bounds"),
    (lambda result: result["candidate"]["external_segmentation"]["per_tree"]["tree-a"].update({"wood_iou": True}), "not a boolean"),
    (lambda result: result["confidence_intervals"]["wood_iou_delta"].update({"extra": 1}), "missing or extra"),
    (lambda result: result["formal_gate"].update({"failed_criteria": ["not_a_criterion"]}), "failed_criteria"),
    (lambda result: result["verdict"].update({"verdict": "POINT_ESTIMATE_PASS_ONLY", "promote": True}), "verdict"),
])
def test_rejects_forged_nested_result(reviewed_repo: tuple[Path, Path, Path], mutate, message: str):
    repo, result_path, manifest_path = reviewed_repo; result = json.loads(result_path.read_text(encoding="utf-8")); mutate(result); _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match=message): import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_noncanonical_paths_and_preimport_candidate_mutation(reviewed_repo: tuple[Path, Path, Path]):
    repo, result_path, manifest_path = reviewed_repo
    with pytest.raises(ValueError, match="canonical"): import_reviewed_result(result_path.parent / ".." / "pointnet_independent_eval/result.json", manifest_path, repo_root=repo)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest["candidate"]["promoted"] = True; _write(manifest_path, manifest)
    with pytest.raises(ValueError, match="pre-import candidate"): import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_non_ancestral_commit_and_committed_sibling_byte_drift(reviewed_repo: tuple[Path, Path, Path]):
    repo, result_path, manifest_path = reviewed_repo; result = json.loads(result_path.read_text(encoding="utf-8")); result["evaluation_git_commit"] = "0" * 40; _commit_result(repo, result_path, result, "forged commit")
    with pytest.raises(ValueError, match="Git validation"): import_reviewed_result(result_path, manifest_path, repo_root=repo)
    result["evaluation_git_commit"] = _git(repo, "rev-parse", "HEAD~2"); _commit_result(repo, result_path, result, "restore eval")
    protocol = result_path.parent / "protocol.json"; protocol.write_text(protocol.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed Git version"): import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_sync_rechecks_result_bytes_and_renders_reviewed_metrics(reviewed_repo: tuple[Path, Path, Path]):
    repo, result_path, manifest_path = reviewed_repo; import_reviewed_result(result_path, manifest_path, repo_root=repo)
    manifest = load_manifest(manifest_path, repo_root=repo); truth = render_truth_block(manifest)
    assert "FAIL_METRICS" in truth and "0.418" in truth and "1.1673846154" in truth and "measurable trees" in truth
    for relative in CONTROLLED_DOCS:
        path = repo / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(f"{TRUTH_START}\n{TRUTH_END}\n", encoding="utf-8")
    assert sync(repo, check=False) == 0 and sync(repo, check=True) == 0
    result_path.write_text(result_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed Git version"): sync(repo, check=True)


def test_ci_filters_include_importer_for_push_and_pull_request():
    workflow = (ROOT / ".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    assert workflow.count('"scripts/review_pointnet_evidence.py"') == 2
