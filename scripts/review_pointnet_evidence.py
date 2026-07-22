"""Import a committed independent PointNet result without changing the default."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


RESULT_KEYS = {
    "schema_version",
    "experiment_id",
    "protocol_sha256",
    "freeze_manifest_sha256",
    "external_manifest_sha256",
    "checkpoint_sha256",
    "evaluation_git_commit",
    "baseline",
    "candidate",
    "paired_deltas",
    "confidence_intervals",
    "formal_gate",
    "verdict",
    "limitations",
}
VERDICTS = {
    "INVALID_EVIDENCE",
    "FAIL_METRICS",
    "POINT_ESTIMATE_PASS_ONLY",
    "PROMOTE_POINTNET",
}
_METRIC_FIELDS = ("dbh_mae_cm", "height_mae_m", "volume_mape_pct")
_LOWER_HEX = set("0123456789abcdef")


def _fail_constant(value: str) -> None:
    raise ValueError(f"JSON contains non-finite constant {value}")


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_fail_constant
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} cannot be parsed as finite JSON") from exc
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _validate_finite_json(payload, label=label)
    return payload


def _validate_finite_json(value: Any, *, label: str) -> None:
    if value is None or type(value) in (str, int):
        return
    if type(value) is bool:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{label} must contain only finite numbers")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_finite_json(item, label=f"{label}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _validate_finite_json(item, label=f"{label}.{key}")
        return
    raise ValueError(f"{label} contains a non-JSON value")


def _exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{label} has missing or extra schema fields")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha(value: Any, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and all(character in _LOWER_HEX for character in value)
    )


def _inside_repo(path: Path, repo_root: Path, *, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"{label} must be inside repo_root") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} is missing")
    return resolved


def _git(repo_root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"Git validation failed: {' '.join(args)}") from exc
    return completed.stdout


def _tracked_head_bytes(path: Path, repo_root: Path, *, label: str) -> None:
    logical = path.relative_to(repo_root).as_posix()
    try:
        _git(repo_root, "ls-files", "--error-unmatch", "--", logical)
        committed = _git(repo_root, "show", f"HEAD:{logical}")
    except ValueError as exc:
        raise ValueError(f"{label} must be Git-tracked and committed") from exc
    if committed != path.read_bytes():
        raise ValueError(f"{label} bytes do not match its committed Git version")


def _finite_number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number, not a boolean")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return number


def _metrics(result: dict[str, Any], label: str) -> dict[str, Any]:
    record = _exact_keys(
        result,
        {"external_segmentation", "downstream"},
        f"result.{label}",
    )
    segmentation = record["external_segmentation"]
    if type(segmentation) is not dict or "macro" not in segmentation:
        raise ValueError(f"result.{label}.external_segmentation macro is required")
    macro = segmentation["macro"]
    if type(macro) is not dict or "wood_iou" not in macro:
        raise ValueError(f"result.{label}.external_segmentation.macro.wood_iou is required")
    wood_iou = _finite_number(
        macro["wood_iou"], f"result.{label}.external macro Wood IoU", minimum=0.0
    )
    if wood_iou > 1.0:
        raise ValueError(f"result.{label}.external macro Wood IoU must not exceed 1")
    downstream = record["downstream"]
    if type(downstream) is not dict:
        raise ValueError(f"result.{label}.downstream must be an object")
    values = {"external_macro_wood_iou": macro["wood_iou"]}
    for field in _METRIC_FIELDS:
        values[field] = downstream.get(field)
        _finite_number(values[field], f"result.{label}.downstream.{field}", minimum=0.0)
    count = downstream.get("measurable_trees")
    if type(count) is not int or count <= 0:
        raise ValueError(f"result.{label}.downstream.measurable_trees must be a positive integer")
    values["measurable_trees"] = count
    return values


def _validate_result(result: dict[str, Any]) -> dict[str, Any]:
    _exact_keys(result, RESULT_KEYS, "result")
    if result["schema_version"] != "1":
        raise ValueError("result schema_version must equal '1'")
    if type(result["experiment_id"]) is not str or not result["experiment_id"]:
        raise ValueError("result experiment_id must be a non-empty string")
    for field in (
        "protocol_sha256",
        "freeze_manifest_sha256",
        "external_manifest_sha256",
        "checkpoint_sha256",
    ):
        if not _is_sha(result[field], 64):
            raise ValueError(f"result {field} must be lowercase SHA-256")
    if not _is_sha(result["evaluation_git_commit"], 40):
        raise ValueError("result evaluation_git_commit must be lowercase Git SHA")

    baseline = _metrics(result["baseline"], "baseline")
    candidate = _metrics(result["candidate"], "candidate")
    formal = _exact_keys(
        result["formal_gate"],
        {"promote", "status", "failed_criteria", "baseline", "candidate"},
        "result.formal_gate",
    )
    if type(formal["promote"]) is not bool or type(formal["status"]) is not str:
        raise ValueError("result formal_gate values are malformed")
    if formal["status"] not in {"promoted", "rejected", "candidate_not_evaluated"}:
        raise ValueError("result formal_gate status is invalid")
    if type(formal["failed_criteria"]) is not list or any(
        type(item) is not str or not item for item in formal["failed_criteria"]
    ):
        raise ValueError("result formal_gate failed_criteria must be non-empty strings")
    if len(set(formal["failed_criteria"])) != len(formal["failed_criteria"]):
        raise ValueError("result formal_gate failed_criteria must be unique")
    formal_baseline = _formal_metrics(formal["baseline"], "baseline")
    formal_candidate = _formal_metrics(formal["candidate"], "candidate")
    if formal_baseline != _formal_from_result(baseline) or formal_candidate != _formal_from_result(candidate):
        raise ValueError("result formal gate metrics do not match reported metrics")

    verdict = _exact_keys(result["verdict"], {"verdict", "promote"}, "result.verdict")
    if verdict["verdict"] not in VERDICTS or type(verdict["promote"]) is not bool:
        raise ValueError("result verdict is malformed")
    if verdict["verdict"] != "POINT_ESTIMATE_PASS_ONLY" and verdict["promote"] != formal["promote"]:
        raise ValueError("result verdict and formal gate promote values disagree")
    if verdict["verdict"] == "PROMOTE_POINTNET":
        if not (formal["promote"] and formal["status"] == "promoted" and not formal["failed_criteria"]):
            raise ValueError("PROMOTE_POINTNET requires a fully passed formal gate")
    elif verdict["verdict"] == "POINT_ESTIMATE_PASS_ONLY":
        if not (formal["promote"] and formal["status"] == "promoted" and not formal["failed_criteria"]):
            raise ValueError("POINT_ESTIMATE_PASS_ONLY requires a passed formal gate")
    elif formal["promote"] or formal["status"] != "rejected" or not formal["failed_criteria"]:
        raise ValueError("only passed verdicts may use a promoted formal gate")
    if type(result["limitations"]) is not list or not result["limitations"] or any(
        type(item) is not str or not item for item in result["limitations"]
    ):
        raise ValueError("result limitations must be non-empty strings")
    return {
        "baseline": baseline,
        "candidate": candidate,
        "formal_failed_criteria": list(formal["failed_criteria"]),
        "verdict": verdict["verdict"],
    }


def _formal_metrics(value: Any, label: str) -> dict[str, Any]:
    record = _exact_keys(
        value,
        {"wood_iou", *set(_METRIC_FIELDS), "measurable_trees"},
        f"result.formal_gate.{label}",
    )
    _finite_number(record["wood_iou"], f"result.formal_gate.{label}.wood_iou", minimum=0.0)
    for field in _METRIC_FIELDS:
        _finite_number(record[field], f"result.formal_gate.{label}.{field}", minimum=0.0)
    if type(record["measurable_trees"]) is not int or record["measurable_trees"] <= 0:
        raise ValueError(f"result.formal_gate.{label}.measurable_trees must be positive")
    return record


def _formal_from_result(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "wood_iou": metrics["external_macro_wood_iou"],
        **{field: metrics[field] for field in _METRIC_FIELDS},
        "measurable_trees": metrics["measurable_trees"],
    }


def _validate_cross_links(result: dict[str, Any], result_path: Path, repo_root: Path) -> None:
    siblings = {
        "protocol_sha256": result_path.parent / "protocol.json",
        "freeze_manifest_sha256": result_path.parent / "freeze_manifest.json",
        "external_manifest_sha256": result_path.parent / "external_dataset_manifest.json",
    }
    payloads: dict[str, dict[str, Any]] = {}
    for hash_field, path in siblings.items():
        path = _inside_repo(path, repo_root, label=path.name)
        _tracked_head_bytes(path, repo_root, label=path.name)
        if _sha256(path) != result[hash_field]:
            raise ValueError(f"result {hash_field} does not match {path.name}")
        payloads[hash_field] = _load_json(path, label=path.name)

    protocol = payloads["protocol_sha256"]
    freeze = payloads["freeze_manifest_sha256"]
    external = payloads["external_manifest_sha256"]
    experiment_id = result["experiment_id"]
    if protocol.get("experiment_id") != experiment_id:
        raise ValueError("protocol experiment identity does not match result")
    checks = {
        "freeze experiment": freeze.get("experiment_id") == experiment_id,
        "external experiment": external.get("experiment_id") == experiment_id,
        "freeze protocol": freeze.get("protocol_sha256") == result["protocol_sha256"],
        "external protocol": external.get("protocol_sha256") == result["protocol_sha256"],
        "external freeze": external.get("freeze_manifest_sha256") == result["freeze_manifest_sha256"],
        "freeze checkpoint": freeze.get("winner", {}).get("checkpoint_sha256")
        == result["checkpoint_sha256"],
        "external checkpoint": external.get("checkpoint_sha256") == result["checkpoint_sha256"],
    }
    failed = [name for name, matched in checks.items() if not matched]
    if failed:
        raise ValueError(f"evidence cross-links do not bind result: {', '.join(failed)}")


def _pointnet_capability(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row
        for row in manifest.get("capabilities", [])
        if type(row) is dict and row.get("name") == "5b. PointNet++ wood/leaf candidate"
    ]
    if len(rows) != 1:
        raise ValueError("manifest must contain exactly one PointNet++ capability row")
    return rows[0]


def _independent_block(
    result: dict[str, Any],
    validated: dict[str, Any],
    result_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    return {
        "result_path": result_path.relative_to(repo_root).as_posix(),
        "result_sha256": _sha256(result_path),
        "verdict": validated["verdict"],
        "baseline": validated["baseline"],
        "candidate": validated["candidate"],
        "provenance": {
            field: result[field]
            for field in (
                "experiment_id",
                "protocol_sha256",
                "freeze_manifest_sha256",
                "external_manifest_sha256",
                "checkpoint_sha256",
                "evaluation_git_commit",
            )
        },
        "failed_criteria": validated["formal_failed_criteria"],
        "limitations": list(result["limitations"]),
    }


def validate_imported_independent(
    block: Any, *, repo_root: str | Path
) -> dict[str, Any]:
    """Revalidate imported bytes and cross-links for ``sync_truth --check``."""
    repository = Path(repo_root).resolve()
    imported = _exact_keys(
        block,
        {
            "result_path",
            "result_sha256",
            "verdict",
            "baseline",
            "candidate",
            "provenance",
            "failed_criteria",
            "limitations",
        },
        "validation.pointnet_independent",
    )
    relative = imported["result_path"]
    if type(relative) is not str or not relative or Path(relative).is_absolute():
        raise ValueError("validation.pointnet_independent result_path must be repository-relative")
    result_file = _inside_repo(repository / relative, repository, label="imported result")
    _tracked_head_bytes(result_file, repository, label="imported result")
    result = _load_json(result_file, label="imported result")
    validated = _validate_result(result)
    _validate_cross_links(result, result_file, repository)
    expected = _independent_block(result, validated, result_file, repository)
    if imported != expected:
        raise ValueError("validation.pointnet_independent does not match the committed result")
    return expected


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def import_reviewed_result(
    result_path: str | Path,
    manifest_path: str | Path,
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Import one committed result while preserving every non-review surface."""
    repository = Path(repo_root).resolve()
    result_file = _inside_repo(Path(result_path), repository, label="result")
    manifest_file = _inside_repo(Path(manifest_path), repository, label="manifest")
    _tracked_head_bytes(result_file, repository, label="result")
    result = _load_json(result_file, label="result")
    validated = _validate_result(result)
    _validate_cross_links(result, result_file, repository)
    manifest = _load_json(manifest_file, label="manifest")
    before = copy.deepcopy(manifest)
    updated = copy.deepcopy(manifest)
    candidate = updated.get("candidate")
    if type(candidate) is not dict:
        raise ValueError("manifest candidate is missing")
    promotion = candidate.get("promotion_evidence")
    if type(promotion) is not dict or type(promotion.get("policy")) is not str:
        raise ValueError("manifest promotion evidence policy is missing")
    candidate["status"] = "Experimental"
    candidate["promoted"] = False
    promotion["all_passed"] = validated["verdict"] == "PROMOTE_POINTNET"
    promotion["failed_criteria"] = (
        [] if promotion["all_passed"] else validated["formal_failed_criteria"]
    )
    validation = updated.get("validation")
    if type(validation) is not dict:
        raise ValueError("manifest validation is missing")
    validation["pointnet_independent"] = _independent_block(
        result, validated, result_file, repository
    )
    pointnet = _pointnet_capability(updated)
    for field in ("evidence", "claim"):
        if type(pointnet.get(field)) is not str:
            raise ValueError(f"PointNet++ capability {field} is missing")
    pointnet["evidence"] = (
        f"{validation['pointnet_independent']['result_path']}; SHA-256 "
        f"{validation['pointnet_independent']['result_sha256']}"
    )
    pointnet["claim"] = (
        f"Reviewed independent verdict {validated['verdict']}; candidate external macro Wood IoU "
        f"{validated['candidate']['external_macro_wood_iou']}; remains Experimental and not default-promoted."
    )
    _assert_only_allowed_changes(before, updated)
    _write_json_atomic(manifest_file, updated)
    return updated


def _assert_only_allowed_changes(before: dict[str, Any], after: dict[str, Any]) -> None:
    if before.get("baseline") != after.get("baseline"):
        raise ValueError("importer must not change baseline")
    for field in ("backend", "display_name"):
        if before.get("candidate", {}).get(field) != after.get("candidate", {}).get(field):
            raise ValueError(f"importer must not change candidate.{field}")
    if after.get("candidate", {}).get("status") != "Experimental" or after.get("candidate", {}).get("promoted") is not False:
        raise ValueError("importer must retain Experimental, unpromoted candidate")
    if before.get("core_demo") != after.get("core_demo"):
        raise ValueError("importer must not change core_demo")
    before_rows = {row.get("name"): row for row in before.get("capabilities", []) if type(row) is dict}
    after_rows = {row.get("name"): row for row in after.get("capabilities", []) if type(row) is dict}
    for name, row in before_rows.items():
        if name != "5b. PointNet++ wood/leaf candidate" and after_rows.get(name) != row:
            raise ValueError("importer must not change non-PointNet capabilities")
    preserved_validation = {
        key: value for key, value in before.get("validation", {}).items() if key != "pointnet_independent"
    }
    if {
        key: value for key, value in after.get("validation", {}).items() if key != "pointnet_independent"
    } != preserved_validation:
        raise ValueError("importer must not change existing validation evidence")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    import_reviewed_result(args.result, args.manifest, repo_root=args.repo_root)
    print(json.dumps({"status": "ok", "result": str(args.result)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
