"""Import one committed independent PointNet result without changing defaults.

This module intentionally imports neither Torch nor model code.  It validates the
JSON evidence contract and the Git history that binds the evidence instead.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[1]
_ML_ROOT = _REPO_ROOT / "services" / "ml"
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

# These production validators are deliberately data-only: neither imports Torch
# nor opens datasets/checkpoints/network resources.
from pipeline.external_tree_dataset import _load_freeze, _validate_manifest  # noqa: E402
from training.evidence_protocol import load_protocol  # noqa: E402


RESULT_KEYS = {
    "schema_version", "experiment_id", "protocol_sha256", "freeze_manifest_sha256",
    "external_manifest_sha256", "checkpoint_sha256", "evaluation_git_commit",
    "baseline", "candidate", "paired_deltas", "confidence_intervals", "formal_gate",
    "verdict", "limitations",
}
VERDICTS = {"INVALID_EVIDENCE", "FAIL_METRICS", "POINT_ESTIMATE_PASS_ONLY", "PROMOTE_POINTNET"}
_METRICS = ("dbh_mae_cm", "height_mae_m", "volume_mape_pct")
_SEGMENTATION = ("wood_iou", "leaf_iou", "mean_iou", "accuracy")
_CONFUSION = ("wood_as_wood", "wood_as_leaf", "leaf_as_wood", "leaf_as_leaf")
_DELTAS = {
    "wood_iou_delta": ("Wood IoU candidate-minus-baseline", "proportion", "wood_iou"),
    "dbh_abs_error_delta": ("DBH absolute-error candidate-minus-baseline", "cm", "dbh_mae_cm"),
    "height_abs_error_delta": ("Height absolute-error candidate-minus-baseline", "m", "height_mae_m"),
    "volume_ape_delta": ("Volume APE candidate-minus-baseline", "percent", "volume_mape_pct"),
}
_POINT_CRITERIA = (
    "wood_iou_improves", "dbh_mae_non_regression", "height_mae_non_regression",
    "volume_mape_non_regression", "measurable_tree_count",
)
_OPAQUE_CRITERIA = (
    "checkpoint_sha256", "training_provenance", "independent_real_test", "reproducible_command",
)
_ALL_CRITERIA = {"candidate_metrics", *_POINT_CRITERIA, *_OPAQUE_CRITERIA}
_RESULT_RELATIVE = Path("docs/evidence/pointnet_independent_eval/result.json")
_MANIFEST_RELATIVE = Path("docs/evidence/core_demo_manifest.json")


def _fail_constant(value: str) -> None:
    raise ValueError(f"JSON contains non-finite constant {value}")


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key, item in pairs:
            if key in payload:
                raise ValueError(f"{label} contains duplicate JSON key {key!r}")
            payload[key] = item
        return payload

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_fail_constant,
            object_pairs_hook=no_duplicate_keys,
        )
    except ValueError as exc:
        raise ValueError(f"{label} is invalid: {exc}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} cannot be parsed as finite JSON") from exc
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _finite_json(value, label)
    return value


def _finite_json(value: Any, label: str) -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{label} must contain only finite numbers")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _finite_json(item, f"{label}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _finite_json(item, f"{label}.{key}")
        return
    raise ValueError(f"{label} contains a non-JSON value")


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{label} has missing or extra schema fields")
    return value


def _number(value: Any, label: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{label} must be a finite number, not a boolean")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    if minimum is not None and result < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    if maximum is not None and result > maximum:
        raise ValueError(f"{label} must be at most {maximum}")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha(value: Any, length: int) -> bool:
    return type(value) is str and len(value) == length and all(c in "0123456789abcdef" for c in value)


def _git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"Git validation failed: {' '.join(args)}") from exc


def _canonical_file(value: str | Path, *, repo: Path, expected: Path, label: str) -> Path:
    supplied = Path(value)
    if ".." in supplied.parts or supplied.is_symlink():
        raise ValueError(f"{label} must use its canonical repository path (no traversal or symlink)")
    path = supplied.resolve()
    if path != expected.resolve():
        raise ValueError(f"{label} must equal {expected.relative_to(repo).as_posix()}")
    # A symlinked parent may otherwise hide a non-canonical source location.
    current = supplied if supplied.is_absolute() else repo / supplied
    while current != repo:
        if current.is_symlink():
            raise ValueError(f"{label} must not traverse a symlink")
        current = current.parent
    if not path.is_file():
        raise ValueError(f"{label} is missing")
    return path


def _tracked_head_bytes(path: Path, *, repo: Path, label: str) -> None:
    logical = path.relative_to(repo).as_posix()
    try:
        _git(repo, "ls-files", "--error-unmatch", "--", logical)
        committed = _git(repo, "show", f"HEAD:{logical}")
    except ValueError as exc:
        raise ValueError(f"{label} must be Git-tracked and committed") from exc
    if committed != path.read_bytes():
        raise ValueError(f"{label} bytes do not match its committed Git version")


def _commit_exists_and_is_ancestor(commit: str, ancestor_of: str, *, repo: Path, label: str) -> None:
    _git(repo, "cat-file", "-e", f"{commit}^{{commit}}")
    _git(repo, "merge-base", "--is-ancestor", commit, ancestor_of)


def _commit_bytes(path: Path, commit: str, *, repo: Path, label: str) -> None:
    logical = path.relative_to(repo).as_posix()
    try:
        committed = _git(repo, "show", f"{commit}:{logical}")
    except ValueError as exc:
        raise ValueError(f"{label} is not committed at evaluation_git_commit") from exc
    if committed != path.read_bytes():
        raise ValueError(f"{label} bytes differ from evaluation_git_commit")


def _introduced_commit(path: Path, *, through: str, repo: Path, label: str) -> str:
    """Find the first ancestor that introduced exactly the current file bytes."""
    logical = path.relative_to(repo).as_posix()
    commits = _git(repo, "rev-list", "--reverse", through).decode("ascii").splitlines()
    current = path.read_bytes()
    for commit in commits:
        try:
            blob = _git(repo, "show", f"{commit}:{logical}")
        except ValueError:
            continue
        if blob != current:
            continue
        parents = _git(repo, "rev-list", "--parents", "-n", "1", commit).decode("ascii").split()
        if len(parents) == 1:
            return commit
        parent = parents[1]
        try:
            parent_blob = _git(repo, "show", f"{parent}:{logical}")
        except ValueError:
            return commit
        if parent_blob != current:
            return commit
    raise ValueError(f"{label} canonical bytes were not introduced before evaluation")


def _strict_ancestor(earlier: str, later: str, *, repo: Path, label: str) -> None:
    if earlier == later:
        raise ValueError(f"{label} must be a strict ancestor")
    try:
        _commit_exists_and_is_ancestor(earlier, later, repo=repo, label=label)
    except ValueError as exc:
        raise ValueError(f"{label} must be a strict ancestor") from exc


def _validate_freeze_reproducibility(freeze: dict[str, Any], protocol: dict[str, Any], checkpoint: str) -> None:
    winner = freeze["winner"]
    rerun = freeze["rerun_evidence"]
    seeds = protocol["training"]["seeds"]
    if winner["seed"] not in seeds:
        raise ValueError("freeze winner seed is not one of the locked protocol seeds")
    if rerun["seed"] != winner["seed"]:
        raise ValueError("freeze rerun seed does not match winner")
    if rerun["best_epoch"] != winner["selected_epoch"]:
        raise ValueError("freeze rerun best epoch does not match winner")
    if rerun["best_macro_tile_wood_iou"] != winner["dev_metrics"]["wood_iou"]:
        raise ValueError("freeze rerun Wood IoU does not match winner")
    if rerun["state_dict_sha256"] != winner["state_dict_sha256"]:
        raise ValueError("freeze rerun state identity does not match winner")
    if winner["checkpoint_sha256"] != checkpoint or rerun["checkpoint_sha256"] != winner["checkpoint_sha256"]:
        raise ValueError("freeze checkpoint identity does not match winner/rerun/result")


def _from_confusion(confusion: dict[str, int]) -> dict[str, Any]:
    wood, wood_leaf, leaf_wood, leaf = (confusion[key] for key in _CONFUSION)
    total = wood + wood_leaf + leaf_wood + leaf
    if total <= 0:
        raise ValueError("segmentation confusion must represent at least one point")
    wood_iou = wood / (wood + wood_leaf + leaf_wood) if wood + wood_leaf + leaf_wood else 1.0
    leaf_iou = leaf / (leaf + wood_leaf + leaf_wood) if leaf + wood_leaf + leaf_wood else 1.0
    return {"wood_iou": wood_iou, "leaf_iou": leaf_iou, "mean_iou": (wood_iou + leaf_iou) / 2.0, "accuracy": (wood + leaf) / total, "confusion": dict(confusion)}


def _segmentation_record(value: Any, label: str) -> dict[str, Any]:
    record = _exact(value, {*_SEGMENTATION, "confusion"}, label)
    confusion = _exact(record["confusion"], set(_CONFUSION), f"{label}.confusion")
    if any(type(confusion[key]) is not int or confusion[key] < 0 for key in _CONFUSION):
        raise ValueError(f"{label}.confusion must contain non-negative integer counts")
    expected = _from_confusion(confusion)
    for key in _SEGMENTATION:
        _number(record[key], f"{label}.{key}", minimum=0.0, maximum=1.0)
        if record[key] != expected[key]:
            raise ValueError(f"{label}.{key} is inconsistent with confusion")
    return expected


def _segmentation(value: Any, label: str) -> dict[str, Any]:
    record = _exact(value, {"per_tree", "macro", "pooled"}, f"result.{label}.external_segmentation")
    per_tree = record["per_tree"]
    if type(per_tree) is not dict or not per_tree:
        raise ValueError(f"result.{label}.external_segmentation.per_tree must be non-empty")
    retained: list[dict[str, Any]] = []
    totals = dict.fromkeys(_CONFUSION, 0)
    for tree_id, tree in per_tree.items():
        if type(tree_id) is not str or not tree_id:
            raise ValueError(f"result.{label} external tree IDs must be non-empty strings")
        canonical = _segmentation_record(tree, f"result.{label}.external[{tree_id}]")
        retained.append(canonical)
        for key in _CONFUSION:
            totals[key] += canonical["confusion"][key]
    macro = _exact(record["macro"], set(_SEGMENTATION), f"result.{label}.external macro")
    expected_macro = {key: sum(tree[key] for tree in retained) / len(retained) for key in _SEGMENTATION}
    for key in _SEGMENTATION:
        _number(macro[key], f"result.{label}.external macro.{key}", minimum=0.0, maximum=1.0)
        if macro[key] != expected_macro[key]:
            raise ValueError(f"result.{label}.external macro is inconsistent with per-tree records")
    if _segmentation_record(record["pooled"], f"result.{label}.external pooled") != _from_confusion(totals):
        raise ValueError(f"result.{label}.external pooled metrics are inconsistent")
    return {"wood_iou": macro["wood_iou"], "tree_ids": frozenset(per_tree)}


def _metrics(
    value: Any,
    label: str,
    *,
    external_tree_ids: frozenset[str] | None = None,
    max_measurable_trees: int | None = None,
) -> dict[str, Any]:
    record = _exact(value, {"external_segmentation", "downstream"}, f"result.{label}")
    result = _segmentation(record["external_segmentation"], label)
    if external_tree_ids is not None and result["tree_ids"] != external_tree_ids:
        raise ValueError(f"result.{label} external per-tree IDs do not match canonical cohort")
    downstream = _exact(record["downstream"], {*_METRICS, "measurable_trees"}, f"result.{label}.downstream")
    for key in _METRICS:
        _number(downstream[key], f"result.{label}.downstream.{key}", minimum=0.0)
        result[key] = downstream[key]
    count = downstream["measurable_trees"]
    if type(count) is not int or count <= 0:
        raise ValueError(f"result.{label}.downstream.measurable_trees must be a positive integer")
    if max_measurable_trees is not None and count > max_measurable_trees:
        raise ValueError(f"result.{label}.downstream.measurable_trees exceeds protocol Demol count")
    result["measurable_trees"] = count
    result.pop("tree_ids")
    return result


def _formal_metrics(value: Any, label: str) -> dict[str, Any]:
    record = _exact(value, {"wood_iou", *_METRICS, "measurable_trees"}, f"result.formal_gate.{label}")
    _number(record["wood_iou"], f"result.formal_gate.{label}.wood_iou", minimum=0.0, maximum=1.0)
    for key in _METRICS:
        _number(record[key], f"result.formal_gate.{label}.{key}", minimum=0.0)
    if type(record["measurable_trees"]) is not int or record["measurable_trees"] <= 0:
        raise ValueError(f"result.formal_gate.{label}.measurable_trees must be a positive integer")
    return record


def _intervals(value: Any) -> dict[str, dict[str, Any]]:
    intervals = _exact(value, set(_DELTAS), "result confidence intervals")
    for name, interval in intervals.items():
        _exact(interval, {"estimate", "lower", "upper"}, f"result confidence intervals.{name}")
        for field in ("estimate", "lower", "upper"):
            _number(interval[field], f"result confidence intervals.{name}.{field}")
        if not interval["lower"] <= interval["estimate"] <= interval["upper"]:
            raise ValueError(f"result confidence intervals.{name} bounds are inconsistent")
    return intervals


def _validate_deltas(value: Any, intervals: dict[str, dict[str, Any]], baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    deltas = _exact(value, set(_DELTAS), "result paired_deltas")
    for key, (name, unit, metric) in _DELTAS.items():
        delta = _exact(deltas[key], {"name", "unit", "estimate"}, f"result paired_deltas.{key}")
        if delta["name"] != name or delta["unit"] != unit:
            raise ValueError(f"result paired_deltas.{key} declaration is invalid")
        _number(delta["estimate"], f"result paired_deltas.{key}.estimate")
        if delta["estimate"] != intervals[key]["estimate"]:
            raise ValueError(f"result paired_deltas.{key} estimate does not match confidence interval")
        if key == "wood_iou_delta" and delta["estimate"] != candidate[metric] - baseline[metric]:
            raise ValueError(f"result paired_deltas.{key} estimate is inconsistent with aggregate metrics")


def _formal_failures(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    checks = {
        "checkpoint_sha256": True,
        "training_provenance": True,
        "independent_real_test": True,
        "reproducible_command": True,
        "wood_iou_improves": candidate["wood_iou"] > baseline["wood_iou"],
        "dbh_mae_non_regression": candidate["dbh_mae_cm"] <= baseline["dbh_mae_cm"],
        "height_mae_non_regression": candidate["height_mae_m"] <= baseline["height_mae_m"],
        "volume_mape_non_regression": candidate["volume_mape_pct"] <= baseline["volume_mape_pct"],
        "measurable_tree_count": candidate["measurable_trees"] >= baseline["measurable_trees"],
    }
    return [criterion for criterion, passed in checks.items() if not passed]


def _validate_result(
    result: dict[str, Any],
    *,
    external_tree_ids: frozenset[str] | None = None,
    max_measurable_trees: int | None = None,
) -> dict[str, Any]:
    _exact(result, RESULT_KEYS, "result")
    if result["schema_version"] != "1" or type(result["experiment_id"]) is not str or not result["experiment_id"]:
        raise ValueError("result identity is malformed")
    for key in ("protocol_sha256", "freeze_manifest_sha256", "external_manifest_sha256", "checkpoint_sha256"):
        if not _is_sha(result[key], 64):
            raise ValueError(f"result {key} must be lowercase SHA-256")
    if not _is_sha(result["evaluation_git_commit"], 40):
        raise ValueError("result evaluation_git_commit must be lowercase Git SHA")
    if result["verdict"].get("verdict") == "INVALID_EVIDENCE":
        raise ValueError("INVALID_EVIDENCE cannot be imported because Task 10 publishes no invalid artifacts")
    baseline = _metrics(result["baseline"], "baseline", external_tree_ids=external_tree_ids, max_measurable_trees=max_measurable_trees)
    candidate = _metrics(result["candidate"], "candidate", external_tree_ids=external_tree_ids, max_measurable_trees=max_measurable_trees)
    intervals = _intervals(result["confidence_intervals"])
    _validate_deltas(result["paired_deltas"], intervals, baseline, candidate)
    formal = _exact(result["formal_gate"], {"promote", "status", "failed_criteria", "baseline", "candidate"}, "result.formal_gate")
    if type(formal["promote"]) is not bool or type(formal["status"]) is not str or formal["status"] not in {"promoted", "rejected"}:
        raise ValueError("result formal_gate values are malformed")
    if type(formal["failed_criteria"]) is not list or any(type(item) is not str or item not in _ALL_CRITERIA for item in formal["failed_criteria"]):
        raise ValueError("result formal_gate failed_criteria are invalid")
    if len(set(formal["failed_criteria"])) != len(formal["failed_criteria"]):
        raise ValueError("result formal_gate failed_criteria must be unique")
    formal_baseline, formal_candidate = _formal_metrics(formal["baseline"], "baseline"), _formal_metrics(formal["candidate"], "candidate")
    expected_baseline = {"wood_iou": baseline["wood_iou"], **{key: baseline[key] for key in _METRICS}, "measurable_trees": baseline["measurable_trees"]}
    expected_candidate = {"wood_iou": candidate["wood_iou"], **{key: candidate[key] for key in _METRICS}, "measurable_trees": candidate["measurable_trees"]}
    if formal_baseline != expected_baseline or formal_candidate != expected_candidate:
        raise ValueError("result formal gate metrics do not match reported metrics")
    failures = _formal_failures(baseline, candidate)
    if formal["failed_criteria"] != failures or formal["promote"] != (not failures) or formal["status"] != ("promoted" if not failures else "rejected"):
        raise ValueError("result formal gate is inconsistent with recomputed metrics")
    verdict = _exact(result["verdict"], {"verdict", "promote"}, "result.verdict")
    if verdict["verdict"] not in VERDICTS or type(verdict["promote"]) is not bool:
        raise ValueError("result verdict is malformed")
    strong = intervals["wood_iou_delta"]["lower"] > 0 and all(intervals[name]["upper"] <= 0 for name in ("dbh_abs_error_delta", "height_abs_error_delta", "volume_ape_delta"))
    expected = "PROMOTE_POINTNET" if not failures and strong else "POINT_ESTIMATE_PASS_ONLY" if not failures else "FAIL_METRICS"
    if verdict["verdict"] != expected or verdict["promote"] != (expected == "PROMOTE_POINTNET"):
        raise ValueError("result verdict is inconsistent with formal gate and confidence intervals")
    if type(result["limitations"]) is not list or not result["limitations"] or any(type(item) is not str or not item for item in result["limitations"]):
        raise ValueError("result limitations must be non-empty strings")
    return {"baseline": baseline, "candidate": candidate, "failed_criteria": failures, "verdict": verdict["verdict"]}


def _validate_cross_links(result: dict[str, Any], *, result_path: Path, repo: Path) -> tuple[frozenset[str], int, str]:
    siblings = {
        "protocol_sha256": result_path.parent / "protocol.json",
        "freeze_manifest_sha256": result_path.parent / "freeze_manifest.json",
        "external_manifest_sha256": result_path.parent / "external_dataset_manifest.json",
    }
    evaluation = result["evaluation_git_commit"]
    _commit_exists_and_is_ancestor(evaluation, "HEAD", repo=repo, label="evaluation_git_commit")
    loaded: dict[str, dict[str, Any]] = {}
    for field, path in siblings.items():
        path = _canonical_file(path, repo=repo, expected=path, label=path.name)
        _tracked_head_bytes(path, repo=repo, label=path.name)
        _commit_bytes(path, evaluation, repo=repo, label=path.name)
        if _sha256(path) != result[field]:
            raise ValueError(f"result {field} does not match {path.name}")
        loaded[field] = _load_json(path, label=path.name)
    _, freeze, external = loaded.values()
    try:
        production_protocol = load_protocol(siblings["protocol_sha256"])
        production_freeze = _load_freeze(siblings["freeze_manifest_sha256"])
        _validate_manifest(external)
    except Exception as exc:
        raise ValueError(f"production evidence schema is invalid: {exc}") from exc
    training = production_freeze["training_git_commit"]
    _commit_exists_and_is_ancestor(training, evaluation, repo=repo, label="training_git_commit")
    freeze_introduced = _introduced_commit(
        siblings["freeze_manifest_sha256"], through=evaluation, repo=repo, label="freeze manifest"
    )
    external_introduced = _introduced_commit(
        siblings["external_manifest_sha256"], through=evaluation, repo=repo, label="external manifest"
    )
    _strict_ancestor(
        freeze_introduced, external_introduced, repo=repo, label="external_opened_after_commit"
    )
    _commit_exists_and_is_ancestor(
        external_introduced, evaluation, repo=repo, label="external manifest introduction/evaluation"
    )
    checks = {
        "protocol experiment": production_protocol["experiment_id"] == result["experiment_id"],
        "freeze experiment": freeze["experiment_id"] == result["experiment_id"],
        "external experiment": external["experiment_id"] == result["experiment_id"],
        "freeze protocol": freeze["protocol_sha256"] == result["protocol_sha256"],
        "external protocol": external["protocol_sha256"] == result["protocol_sha256"],
        "external freeze": external["freeze_manifest_sha256"] == result["freeze_manifest_sha256"],
        "freeze training configuration": freeze["training_configuration"] == production_protocol["training"],
        "freeze checkpoint": freeze["winner"]["checkpoint_sha256"] == result["checkpoint_sha256"],
        "external checkpoint": external["checkpoint_sha256"] == result["checkpoint_sha256"],
    }
    failed = [name for name, matched in checks.items() if not matched]
    if failed:
        raise ValueError(f"evidence cross-links do not bind result: {', '.join(failed)}")
    _validate_freeze_reproducibility(production_freeze, production_protocol, result["checkpoint_sha256"])
    return frozenset(external["tree_ids"]), production_protocol["demol"]["expected_trees"], freeze_introduced


def _independent_block(result: dict[str, Any], validated: dict[str, Any], path: Path, repo: Path, *, freeze_introduced: str) -> dict[str, Any]:
    def truth_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_macro_wood_iou": metrics["wood_iou"],
            **{key: metrics[key] for key in _METRICS},
            "measurable_trees": metrics["measurable_trees"],
        }

    return {
        "result_path": path.relative_to(repo).as_posix(), "result_sha256": _sha256(path), "verdict": validated["verdict"],
        "baseline": truth_metrics(validated["baseline"]), "candidate": truth_metrics(validated["candidate"]),
        "provenance": {
            **{key: result[key] for key in ("experiment_id", "protocol_sha256", "freeze_manifest_sha256", "external_manifest_sha256", "checkpoint_sha256", "evaluation_git_commit")},
            "external_opened_after_commit": freeze_introduced,
        },
        "failed_criteria": validated["failed_criteria"], "limitations": list(result["limitations"]),
    }


def _pointnet_row(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in manifest.get("capabilities", []) if type(row) is dict and row.get("name") == "5b. PointNet++ wood/leaf candidate"]
    if len(rows) != 1:
        raise ValueError("manifest must contain exactly one PointNet++ capability row")
    return rows[0]


def _assert_allowed(before: dict[str, Any], after: dict[str, Any]) -> None:
    old_candidate, new_candidate = before.get("candidate"), after.get("candidate")
    if type(old_candidate) is not dict or type(new_candidate) is not dict or old_candidate.get("status") != "Experimental" or old_candidate.get("promoted") is not False:
        raise ValueError("pre-import candidate must be Experimental and unpromoted")
    if new_candidate.get("status") != old_candidate["status"] or new_candidate.get("promoted") is not old_candidate["promoted"]:
        raise ValueError("importer must not change candidate status or promoted")
    if type(old_candidate.get("promotion_evidence")) is not dict or type(new_candidate.get("promotion_evidence")) is not dict or old_candidate["promotion_evidence"].get("policy") != new_candidate["promotion_evidence"].get("policy"):
        raise ValueError("importer must preserve promotion policy text")
    expected = copy.deepcopy(before)
    expected["candidate"]["promotion_evidence"] = copy.deepcopy(after["candidate"]["promotion_evidence"])
    expected["validation"]["pointnet_independent"] = copy.deepcopy(after["validation"]["pointnet_independent"])
    old_row, new_row = _pointnet_row(expected), _pointnet_row(after)
    old_row["evidence"], old_row["claim"] = new_row.get("evidence"), new_row.get("claim")
    if expected != after:
        raise ValueError("importer may change only reviewed PointNet evidence surfaces")


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def import_reviewed_result(result_path: str | Path, manifest_path: str | Path, *, repo_root: str | Path) -> dict[str, Any]:
    """Validate and atomically import one committed evidence result."""
    repo = Path(repo_root).resolve()
    result_file = _canonical_file(result_path, repo=repo, expected=repo / _RESULT_RELATIVE, label="result")
    manifest_file = _canonical_file(manifest_path, repo=repo, expected=repo / _MANIFEST_RELATIVE, label="manifest")
    _tracked_head_bytes(result_file, repo=repo, label="result")
    result = _load_json(result_file, label="result")
    _validate_result(result)
    external_tree_ids, demol_count, freeze_introduced = _validate_cross_links(result, result_path=result_file, repo=repo)
    validated = _validate_result(
        result, external_tree_ids=external_tree_ids, max_measurable_trees=demol_count
    )
    before = _load_json(manifest_file, label="manifest")
    updated = copy.deepcopy(before)
    candidate = updated.get("candidate")
    if type(candidate) is not dict or type(candidate.get("promotion_evidence")) is not dict or type(candidate["promotion_evidence"].get("policy")) is not str:
        raise ValueError("manifest promotion evidence policy is missing")
    # Do not assign candidate.status/promoted: _assert_allowed proves immutability.
    candidate["promotion_evidence"]["all_passed"] = validated["verdict"] == "PROMOTE_POINTNET"
    candidate["promotion_evidence"]["failed_criteria"] = [] if candidate["promotion_evidence"]["all_passed"] else validated["failed_criteria"]
    if type(updated.get("validation")) is not dict:
        raise ValueError("manifest validation is missing")
    updated["validation"]["pointnet_independent"] = _independent_block(
        result, validated, result_file, repo, freeze_introduced=freeze_introduced
    )
    row = _pointnet_row(updated)
    if type(row.get("evidence")) is not str or type(row.get("claim")) is not str:
        raise ValueError("PointNet++ capability evidence/claim is missing")
    independent = updated["validation"]["pointnet_independent"]
    row["evidence"] = f"{independent['result_path']}; SHA-256 {independent['result_sha256']}"
    row["claim"] = f"Reviewed independent verdict {validated['verdict']}; candidate external macro Wood IoU {validated['candidate']['wood_iou']}; remains Experimental and not default-promoted."
    _assert_allowed(before, updated)
    _write_atomic(manifest_file, updated)
    return updated


def validate_imported_independent(block: Any, *, repo_root: str | Path) -> dict[str, Any]:
    """Re-hash and re-validate imported evidence for ``sync_truth --check``."""
    repo = Path(repo_root).resolve()
    imported = _exact(block, {"result_path", "result_sha256", "verdict", "baseline", "candidate", "provenance", "failed_criteria", "limitations"}, "validation.pointnet_independent")
    if imported.get("result_path") != _RESULT_RELATIVE.as_posix() or not _is_sha(imported.get("result_sha256"), 64):
        raise ValueError("validation.pointnet_independent must use the canonical result path and SHA-256")
    path = _canonical_file(repo / imported["result_path"], repo=repo, expected=repo / _RESULT_RELATIVE, label="imported result")
    _tracked_head_bytes(path, repo=repo, label="imported result")
    result = _load_json(path, label="imported result")
    _validate_result(result)
    external_tree_ids, demol_count, freeze_introduced = _validate_cross_links(result, result_path=path, repo=repo)
    validated = _validate_result(
        result, external_tree_ids=external_tree_ids, max_measurable_trees=demol_count
    )
    expected = _independent_block(result, validated, path, repo, freeze_introduced=freeze_introduced)
    if imported != expected:
        raise ValueError("validation.pointnet_independent does not match the committed result")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args()
    import_reviewed_result(args.result, args.manifest, repo_root=args.repo_root)
    print(json.dumps({"status": "ok", "result": str(args.result)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
