"""Fail-closed orchestration for the independent PointNet evidence gate."""

from __future__ import annotations

import csv
import io
import json
import math
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import qsm
from pipeline.demol_eval import DemolTree, evaluate_demol_pair, load_demol_cohort
from pipeline.evidence_metrics import (
    aggregate_segmentation_metrics,
    decide_independent_verdict,
    paired_percentile_ci,
    segmentation_metrics,
)
from pipeline.external_tree_dataset import (
    _load_freeze,
    _validate_manifest,
    load_external_trees,
)
from pipeline.pointnet_tiled import predict_tiled
from pipeline.provenance import (
    EvaluationMetrics,
    PromotionEvidence,
    evaluate_promotion,
    sha256_file,
)
from pipeline.wood_leaf_separation import WoodLeafSegmenter, segment_wood_leaf
from training.evidence_protocol import load_protocol


class IndependentEvaluationError(RuntimeError):
    """Raised whenever a run cannot qualify as valid independent evidence."""


@dataclass(frozen=True, slots=True)
class ValidatedEvidenceIdentity:
    """Logical, path-free identity validated before any cohort is opened."""

    schema_version: str
    experiment_id: str
    protocol_sha256: str
    freeze_manifest_sha256: str
    external_manifest_sha256: str
    checkpoint_sha256: str
    evaluation_git_commit: str


@dataclass(slots=True)
class EvaluationBundle:
    """Fully composed in-memory evidence awaiting atomic publication."""

    result: dict[str, Any]
    segmentation_rows: list[dict[str, Any]]
    downstream_rows: list[dict[str, Any]]


_LIMITATIONS = [
    "Cohort A contains only 10 individual non-Thai TLS trees, so confidence intervals may be wide.",
    "Wan development data is not an independent final test.",
    "Demol is a locked reused benchmark, not a newly blind cohort.",
    "Downstream evidence validates only DBH, height, and taper-volume measurements.",
    "This evaluation does not validate species classification, allometric carbon, carbon credits, or deployment.",
    "This result does not automatically change the production default.",
]

_SEGMENTATION_FIELDS = [
    "tree_id",
    "point_count",
    *[
        f"{backend}_{field}"
        for backend in ("baseline", "candidate")
        for field in (
            "wood_iou",
            "leaf_iou",
            "mean_iou",
            "accuracy",
            "wood_as_wood",
            "wood_as_leaf",
            "leaf_as_wood",
            "leaf_as_leaf",
        )
    ],
    "wood_iou_delta",
    "leaf_iou_delta",
    "mean_iou_delta",
    "accuracy_delta",
]

_DOWNSTREAM_FIELDS = [
    "tree_id",
    "gt_dbh_cm",
    "gt_height_m",
    "gt_volume_m3",
    *[
        f"{backend}_{field}"
        for backend in ("baseline", "candidate")
        for field in (
            "status",
            "failure",
            "dbh_cm",
            "height_m",
            "volume_m3",
            "dbh_abs_error_cm",
            "height_abs_error_m",
            "volume_ape_pct",
        )
    ],
]

_RESULT_FIELDS = {
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


def _labels(output: object, *, n_points: int, backend: str) -> np.ndarray:
    labels = np.asarray(output)
    if labels.ndim != 1 or labels.size == 0:
        raise IndependentEvaluationError(f"{backend} labels must be a non-empty vector")
    if labels.dtype.kind not in "iu":
        raise IndependentEvaluationError(f"{backend} labels must use an integer dtype")
    if len(labels) != n_points:
        raise IndependentEvaluationError(f"{backend} labels must have one label per point")
    if not np.all((labels == 0) | (labels == 1)):
        raise IndependentEvaluationError(f"{backend} labels must contain only 0 or 1")
    return np.ascontiguousarray(labels, dtype=np.int8)


def _paired_points(points: object, *, tree_id: str) -> np.ndarray:
    try:
        array = np.array(points, dtype=np.float64, order="C", copy=True)
    except (TypeError, ValueError) as exc:
        raise IndependentEvaluationError(f"{tree_id} points are not numeric") from exc
    if array.ndim != 2 or array.shape[1:] != (3,) or len(array) == 0:
        raise IndependentEvaluationError(f"{tree_id} points must have non-empty shape (N, 3)")
    if not np.all(np.isfinite(array)):
        raise IndependentEvaluationError(f"{tree_id} points must be finite")
    array.setflags(write=False)
    return array


def _assert_unchanged(
    points: np.ndarray,
    *,
    original_bytes: bytes,
    original_shape: tuple[int, ...],
    original_strides: tuple[int, ...],
    backend: str,
) -> None:
    if not (
        points.shape == original_shape
        and points.strides == original_strides
        and points.dtype == np.dtype(np.float64)
        and points.flags.c_contiguous
        and not points.flags.writeable
        and points.tobytes(order="C") == original_bytes
    ):
        raise IndependentEvaluationError(
            f"paired input contract was violated by {backend} predictor"
        )


def _external_metrics(
    cohort: Iterable[tuple[str, np.ndarray, np.ndarray]],
    *,
    baseline_predictor: Callable[[np.ndarray], object],
    candidate_predictor: Callable[[np.ndarray], object],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    trees = list(cohort)
    if not trees:
        raise IndependentEvaluationError("external cohort must be non-empty")
    ids = [tree[0] for tree in trees]
    if any(type(tree_id) is not str or not tree_id for tree_id in ids):
        raise IndependentEvaluationError("external tree IDs must be non-empty strings")
    if len(ids) != len(set(ids)):
        raise IndependentEvaluationError("external tree IDs must be unique")

    per_backend: dict[str, dict[str, dict[str, Any]]] = {
        "baseline": {},
        "candidate": {},
    }
    rows: list[dict[str, Any]] = []
    for tree_id, raw_points, raw_gt in sorted(trees, key=lambda item: item[0]):
        points = _paired_points(raw_points, tree_id=tree_id)
        gt = _labels(raw_gt, n_points=len(points), backend=f"{tree_id} ground-truth")
        original_bytes = points.tobytes(order="C")
        original_shape = points.shape
        original_strides = points.strides
        metrics: dict[str, dict[str, Any]] = {}
        for backend, predictor in (
            ("baseline", baseline_predictor),
            ("candidate", candidate_predictor),
        ):
            _assert_unchanged(
                points,
                original_bytes=original_bytes,
                original_shape=original_shape,
                original_strides=original_strides,
                backend=backend,
            )
            try:
                output = predictor(points)
            except Exception as exc:
                _assert_unchanged(
                    points,
                    original_bytes=original_bytes,
                    original_shape=original_shape,
                    original_strides=original_strides,
                    backend=backend,
                )
                raise IndependentEvaluationError(
                    f"{tree_id} {backend} predictor failed: {type(exc).__name__}: {exc}"
                ) from exc
            _assert_unchanged(
                points,
                original_bytes=original_bytes,
                original_shape=original_shape,
                original_strides=original_strides,
                backend=backend,
            )
            labels = _labels(output, n_points=len(points), backend=backend)
            _assert_unchanged(
                points,
                original_bytes=original_bytes,
                original_shape=original_shape,
                original_strides=original_strides,
                backend=backend,
            )
            record = segmentation_metrics(labels, gt)
            metrics[backend] = record
            per_backend[backend][tree_id] = record

        row: dict[str, Any] = {"tree_id": tree_id, "point_count": len(points)}
        for backend in ("baseline", "candidate"):
            record = metrics[backend]
            for name in ("wood_iou", "leaf_iou", "mean_iou", "accuracy"):
                row[f"{backend}_{name}"] = record[name]
            for name, value in record["confusion"].items():
                row[f"{backend}_{name}"] = value
        for name in ("wood_iou", "leaf_iou", "mean_iou", "accuracy"):
            row[f"{name}_delta"] = metrics["candidate"][name] - metrics["baseline"][name]
        rows.append(row)

    return (
        aggregate_segmentation_metrics(per_backend["baseline"]),
        aggregate_segmentation_metrics(per_backend["candidate"]),
        rows,
    )


def _finite_downstream(metrics: Mapping[str, Any], *, backend: str) -> dict[str, Any]:
    if metrics.get("measurable_trees") == 0:
        raise IndependentEvaluationError(f"{backend} has zero measurable Demol trees")
    result = dict(metrics)
    for name in ("dbh_mae_cm", "height_mae_m", "volume_mape_pct"):
        value = result.get(name)
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
            raise IndependentEvaluationError(f"{backend} downstream {name} must be finite")
        result[name] = float(value)
        if not math.isfinite(result[name]):
            raise IndependentEvaluationError(f"{backend} downstream {name} must be finite")
    return result


def _intervals(
    external_baseline: Mapping[str, Any],
    external_candidate: Mapping[str, Any],
    downstream_rows: list[dict[str, Any]],
    statistics: Mapping[str, Any],
) -> dict[str, dict[str, float]]:
    paired_rows = [
        row
        for row in downstream_rows
        if row["baseline_status"] == row["candidate_status"] == "measurable"
    ]
    if not paired_rows:
        raise IndependentEvaluationError("no paired downstream measurable rows")

    kwargs = {
        "resamples": statistics["resamples"],
        "seed": statistics["seed"],
        "confidence": statistics["confidence"],
    }
    intervals = {
        "wood_iou_delta": paired_percentile_ci(
            {key: value["wood_iou"] for key, value in external_baseline["per_tree"].items()},
            {key: value["wood_iou"] for key, value in external_candidate["per_tree"].items()},
            **kwargs,
        )
    }
    for key, field in (
        ("dbh_abs_error_delta", "dbh_abs_error_cm"),
        ("height_abs_error_delta", "height_abs_error_m"),
        ("volume_ape_delta", "volume_ape_pct"),
    ):
        intervals[key] = paired_percentile_ci(
            {row["tree_id"]: row[f"baseline_{field}"] for row in paired_rows},
            {row["tree_id"]: row[f"candidate_{field}"] for row in paired_rows},
            **kwargs,
        )
    return intervals


def _compose_evaluation_from_validated_inputs(
    *,
    identity: ValidatedEvidenceIdentity,
    protocol: dict[str, Any],
    external_cohort: Iterable[tuple[str, np.ndarray, np.ndarray]],
    demol_cohort: Iterable[DemolTree],
    baseline_predictor: Callable[[np.ndarray], object],
    candidate_predictor: Callable[[np.ndarray], object],
    qsm_func: Callable[..., object],
) -> EvaluationBundle:
    """Compose toy or production cohorts only after explicit identity validation."""
    if type(identity) is not ValidatedEvidenceIdentity:
        raise IndependentEvaluationError("validated evidence identity is required")
    _validate_identity_record(identity, protocol)
    try:
        external_baseline, external_candidate, segmentation_rows = _external_metrics(
            external_cohort,
            baseline_predictor=baseline_predictor,
            candidate_predictor=candidate_predictor,
        )
        downstream = evaluate_demol_pair(
            demol_cohort,
            baseline_predictor=baseline_predictor,
            candidate_predictor=candidate_predictor,
            qsm_func=qsm_func,
            qsm_seed=protocol["demol"]["qsm_seed"],
        )
        downstream_rows = list(downstream["per_tree"])
        _reject_deterministic_demol_failures(downstream_rows)
        baseline_downstream = _finite_downstream(downstream["baseline"], backend="baseline")
        candidate_downstream = _finite_downstream(downstream["candidate"], backend="candidate")
        intervals = _intervals(
            external_baseline,
            external_candidate,
            downstream_rows,
            protocol["statistics"],
        )
        baseline_metrics = EvaluationMetrics(
            wood_iou=external_baseline["macro"]["wood_iou"],
            **baseline_downstream,
        )
        candidate_metrics = EvaluationMetrics(
            wood_iou=external_candidate["macro"]["wood_iou"],
            **candidate_downstream,
        )
        formal_decision = evaluate_promotion(
            PromotionEvidence(
                baseline=baseline_metrics,
                candidate=candidate_metrics,
                checkpoint_sha256=identity.checkpoint_sha256,
                training_provenance_complete=True,
                independent_real_test=True,
                reproducible_command=True,
            )
        )
        verdict = decide_independent_verdict(
            evidence_valid=True,
            formal_decision=formal_decision,
            intervals=intervals,
        )
    except IndependentEvaluationError:
        raise
    except Exception as exc:
        raise IndependentEvaluationError(str(exc)) from exc

    units = {
        "wood_iou_delta": ("Wood IoU candidate-minus-baseline", "proportion"),
        "dbh_abs_error_delta": ("DBH absolute-error candidate-minus-baseline", "cm"),
        "height_abs_error_delta": ("Height absolute-error candidate-minus-baseline", "m"),
        "volume_ape_delta": ("Volume APE candidate-minus-baseline", "percent"),
    }
    formal_gate = asdict(formal_decision)
    formal_gate["failed_criteria"] = list(formal_gate["failed_criteria"])
    result = {
        **asdict(identity),
        "baseline": {
            "external_segmentation": external_baseline,
            "downstream": baseline_downstream,
        },
        "candidate": {
            "external_segmentation": external_candidate,
            "downstream": candidate_downstream,
        },
        "paired_deltas": {
            key: {"name": name, "unit": unit, "estimate": intervals[key]["estimate"]}
            for key, (name, unit) in units.items()
        },
        "confidence_intervals": intervals,
        "formal_gate": formal_gate,
        "verdict": verdict,
        "limitations": list(_LIMITATIONS),
    }
    return EvaluationBundle(result, segmentation_rows, downstream_rows)


def _reject_deterministic_demol_failures(rows: Iterable[Mapping[str, Any]]) -> None:
    """Fail the whole run when inference evidence, rather than QSM, is invalid."""
    for index, row in enumerate(rows):
        for backend in ("baseline", "candidate"):
            failure = row.get(f"{backend}_failure")
            if isinstance(failure, str) and failure.startswith(("predictor:", "labels:")):
                tree_id = row.get("tree_id", f"row-{index}")
                raise IndependentEvaluationError(
                    f"{backend} Demol {tree_id} has invalid inference evidence: {failure}"
                )


def _validate_identity_record(
    identity: ValidatedEvidenceIdentity, protocol: Mapping[str, Any]
) -> None:
    """Reject syntactically forged test-helper identities before composition."""
    if identity.schema_version != "1" or identity.experiment_id != protocol.get("experiment_id"):
        raise IndependentEvaluationError("validated evidence identity does not match protocol")
    for name in (
        "protocol_sha256",
        "freeze_manifest_sha256",
        "external_manifest_sha256",
        "checkpoint_sha256",
    ):
        value = getattr(identity, name)
        if (
            type(value) is not str
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise IndependentEvaluationError(f"validated evidence identity has invalid {name}")
    if (
        type(identity.evaluation_git_commit) is not str
        or len(identity.evaluation_git_commit) != 40
        or any(character not in "0123456789abcdef" for character in identity.evaluation_git_commit)
    ):
        raise IndependentEvaluationError(
            "validated evidence identity has invalid evaluation_git_commit"
        )


def _validate_finite_json(value: object, *, path: str = "result") -> None:
    if value is None or type(value) in (str, int):
        return
    if type(value) is bool:
        if not path.endswith(".promote"):
            raise IndependentEvaluationError(f"{path} cannot use a boolean as a number")
        return
    if isinstance(value, (float, np.floating)):
        if not math.isfinite(float(value)):
            raise IndependentEvaluationError(f"{path} must contain only finite numbers")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_finite_json(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise IndependentEvaluationError(f"{path} keys must be strings")
            _validate_finite_json(item, path=f"{path}.{key}")
        return
    raise IndependentEvaluationError(f"{path} contains a non-JSON value")


def _csv_content(fields: list[str], rows: list[dict[str, Any]]) -> str:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle, fieldnames=fields, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.write_text(_csv_content(fields, rows), encoding="utf-8", newline="")


def _result_json_text(result: Mapping[str, Any]) -> str:
    """Serialize result.json once so writing and staged validation agree exactly."""
    return (
        json.dumps(
            result,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def _write_result_json(path: Path, result: Mapping[str, Any]) -> None:
    path.write_text(_result_json_text(result), encoding="utf-8", newline="\n")


def _report(result: Mapping[str, Any]) -> str:
    baseline = result["baseline"]
    candidate = result["candidate"]
    lines = [
        "# Independent PointNet Evidence Report",
        "",
        f"Verdict: `{result['verdict']['verdict']}`",
        f"Promote: `{json.dumps(result['verdict']['promote'])}`",
        f"Checkpoint SHA-256: `{result['checkpoint_sha256']}`",
        "",
    ]
    for name, metrics in (("Baseline", baseline), ("Candidate", candidate)):
        downstream = metrics["downstream"]
        lines.extend(
            [
                f"## {name}",
                "",
                "- External segmentation macro: `"
                + json.dumps(
                    metrics["external_segmentation"]["macro"],
                    sort_keys=True,
                    ensure_ascii=True,
                    allow_nan=False,
                    separators=(",", ":"),
                )
                + "`",
                "- External segmentation pooled: `"
                + json.dumps(
                    metrics["external_segmentation"]["pooled"],
                    sort_keys=True,
                    ensure_ascii=True,
                    allow_nan=False,
                    separators=(",", ":"),
                )
                + "`",
                f"- Macro Wood IoU: `{metrics['external_segmentation']['macro']['wood_iou']!r}`",
                f"- DBH MAE (cm): `{downstream['dbh_mae_cm']!r}`",
                f"- Height MAE (m): `{downstream['height_mae_m']!r}`",
                f"- Volume MAPE (%): `{downstream['volume_mape_pct']!r}`",
                f"- Measurable trees: `{downstream['measurable_trees']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Paired uncertainty",
            "",
            "- Paired deltas: `"
            + json.dumps(
                result["paired_deltas"],
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "`",
            "- Confidence intervals: `"
            + json.dumps(
                result["confidence_intervals"],
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "`",
            "",
        ]
    )
    for key in (
        "wood_iou_delta",
        "dbh_abs_error_delta",
        "height_abs_error_delta",
        "volume_ape_delta",
    ):
        delta = result["paired_deltas"][key]
        interval = result["confidence_intervals"][key]
        lines.append(
            f"- {delta['name']}: estimate `{interval['estimate']!r}`; "
            f"95% CI [`{interval['lower']!r}`, `{interval['upper']!r}`] {delta['unit']}"
        )
    lines.append("")
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in result["limitations"])
    return "\n".join(lines) + "\n"


def _write_report(path: Path, result: Mapping[str, Any]) -> None:
    path.write_text(_report(result), encoding="utf-8", newline="\n")


def _validate_staged_artifacts(stage: Path, bundle: EvaluationBundle) -> None:
    if {path.name for path in stage.iterdir()} != {
        "segmentation_per_tree.csv",
        "downstream_per_tree.csv",
        "result.json",
        "REPORT.md",
    }:
        raise IndependentEvaluationError("staged artifact set is not exact")
    with (stage / "segmentation_per_tree.csv").open(encoding="utf-8", newline="") as handle:
        segmentation = list(csv.DictReader(handle))
    with (stage / "downstream_per_tree.csv").open(encoding="utf-8", newline="") as handle:
        downstream = list(csv.DictReader(handle))
    if len(segmentation) != len(bundle.segmentation_rows):
        raise IndependentEvaluationError("segmentation row count mismatch")
    if len(downstream) != len(bundle.downstream_rows):
        raise IndependentEvaluationError("downstream row count mismatch")
    if (stage / "segmentation_per_tree.csv").read_text(encoding="utf-8") != _csv_content(
        _SEGMENTATION_FIELDS, bundle.segmentation_rows
    ):
        raise IndependentEvaluationError("segmentation content mismatch")
    if (stage / "downstream_per_tree.csv").read_text(encoding="utf-8") != _csv_content(
        _DOWNSTREAM_FIELDS, sorted(bundle.downstream_rows, key=lambda row: row["tree_id"])
    ):
        raise IndependentEvaluationError("downstream content mismatch")
    if [row["tree_id"] for row in segmentation] != sorted(row["tree_id"] for row in segmentation):
        raise IndependentEvaluationError("segmentation rows are not sorted")
    if [row["tree_id"] for row in downstream] != sorted(row["tree_id"] for row in downstream):
        raise IndependentEvaluationError("downstream rows are not sorted")
    result_bytes = (stage / "result.json").read_bytes()
    if result_bytes != _result_json_text(bundle.result).encode("utf-8"):
        raise IndependentEvaluationError("result content mismatch")
    report_bytes = (stage / "REPORT.md").read_bytes()
    if report_bytes != _report(bundle.result).encode("utf-8"):
        raise IndependentEvaluationError("report content mismatch")
    loaded = json.loads(result_bytes.decode("utf-8"))
    if loaded != bundle.result or set(loaded) != _RESULT_FIELDS:
        raise IndependentEvaluationError("result schema or content mismatch")
    _validate_finite_json(loaded)


def _link_staged_file(source: Path, destination: Path) -> None:
    """Atomically create a destination hard link without replacing another run's file."""
    os.link(source, destination)


def _staged_source_owns_destination(source: Path, destination: Path) -> bool:
    """Recognize a post-link wrapper failure without claiming a concurrent file."""
    try:
        return source.exists() and destination.exists() and os.path.samefile(source, destination)
    except OSError:
        return False


def _file_identity(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_dev, stat.st_ino


def _publish_evidence_artifacts(
    bundle: EvaluationBundle,
    evidence_dir: str | Path,
) -> dict[str, Any]:
    """Stage, validate and publish exactly four artifacts without overwrite."""
    destination = Path(evidence_dir).resolve()
    finals = [
        destination / "segmentation_per_tree.csv",
        destination / "downstream_per_tree.csv",
        destination / "result.json",
        destination / "REPORT.md",
    ]
    if destination.exists() and not destination.is_dir():
        raise IndependentEvaluationError("evidence_dir must be a directory")
    if any(path.exists() for path in finals):
        raise IndependentEvaluationError("final evidence artifact already exists")
    _validate_finite_json(bundle.result)
    if set(bundle.result) != _RESULT_FIELDS:
        raise IndependentEvaluationError("result schema is not exact")

    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    created: list[tuple[Path, tuple[int, int]]] = []
    destination_created = False
    try:
        _write_csv(stage / finals[0].name, _SEGMENTATION_FIELDS, bundle.segmentation_rows)
        _write_csv(
            stage / finals[1].name,
            _DOWNSTREAM_FIELDS,
            sorted(bundle.downstream_rows, key=lambda row: row["tree_id"]),
        )
        _write_result_json(stage / finals[2].name, bundle.result)
        _write_report(stage / finals[3].name, bundle.result)
        _validate_staged_artifacts(stage, bundle)
        try:
            destination.mkdir()
            destination_created = True
        except FileExistsError:
            if not destination.is_dir():
                raise IndependentEvaluationError("evidence_dir must be a directory")
        for final in finals:
            source = stage / final.name
            try:
                _link_staged_file(source, final)
            except Exception:
                if _staged_source_owns_destination(source, final):
                    identity = _file_identity(final)
                    if identity is not None:
                        created.append((final, identity))
                raise
            identity = _file_identity(final)
            if identity is None:
                raise OSError("published evidence artifact disappeared before ownership tracking")
            created.append((final, identity))
            source.unlink()
    except Exception as exc:
        for path, identity in created:
            if _file_identity(path) == identity:
                path.unlink(missing_ok=True)
        if destination_created:
            try:
                destination.rmdir()
            except OSError:
                pass
        if isinstance(exc, IndependentEvaluationError):
            raise
        raise IndependentEvaluationError(str(exc)) from exc
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return bundle.result


def _load_external_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("external manifest is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("external manifest cannot be parsed") from exc
    _validate_manifest(payload)
    return payload


def _git(repo_root: Path, *arguments: str, text: bool = False) -> str | bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=text,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"Git validation failed: {' '.join(arguments)}") from exc
    return completed.stdout


def _tracked_head_bytes(repo_root: Path, path: Path, *, label: str) -> None:
    try:
        logical = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"{label} must be inside repo_root") from exc
    _git(repo_root, "ls-files", "--error-unmatch", "--", logical)
    if _git(repo_root, "show", f"HEAD:{logical}") != path.read_bytes():
        raise ValueError(f"{label} bytes do not match tracked HEAD")


def _validate_git_evidence_state(
    *,
    repo_root: Path,
    protocol_path: Path,
    freeze_path: Path,
    external_manifest_path: Path,
    training_git_commit: str,
) -> str:
    if not repo_root.is_dir():
        raise ValueError("repo_root is missing")
    status = _git(
        repo_root,
        "status",
        "--porcelain",
        "--untracked-files=normal",
        text=True,
    )
    if str(status).strip():
        raise ValueError("Git working tree must be clean at evaluation start")
    head = str(_git(repo_root, "rev-parse", "HEAD", text=True)).strip()
    if len(head) != 40:
        raise ValueError("evaluation Git HEAD is invalid")
    _git(repo_root, "merge-base", "--is-ancestor", training_git_commit, "HEAD")
    _tracked_head_bytes(repo_root, protocol_path, label="protocol")
    _tracked_head_bytes(repo_root, freeze_path, label="freeze manifest")
    _tracked_head_bytes(repo_root, external_manifest_path, label="external manifest")
    return head


def _preflight_evidence_dir(evidence_dir: Path) -> None:
    if evidence_dir.exists() and not evidence_dir.is_dir():
        raise ValueError("evidence_dir must be a directory")
    finals = {
        "segmentation_per_tree.csv",
        "downstream_per_tree.csv",
        "result.json",
        "REPORT.md",
    }
    if evidence_dir.is_dir() and any((evidence_dir / name).exists() for name in finals):
        raise ValueError("final evidence artifact already exists")


def _identity_matches(
    protocol_payload: dict[str, Any],
    freeze: dict[str, Any],
    external: dict[str, Any],
    *,
    protocol_sha256: str,
    freeze_sha256: str,
    checkpoint_sha256: str,
) -> None:
    experiment_id = protocol_payload["experiment_id"]
    checks = {
        "freeze protocol SHA-256": freeze.get("protocol_sha256") == protocol_sha256,
        "external protocol SHA-256": external.get("protocol_sha256") == protocol_sha256,
        "external freeze SHA-256": external.get("freeze_manifest_sha256") == freeze_sha256,
        "freeze checkpoint SHA-256": freeze.get("winner", {}).get("checkpoint_sha256")
        == checkpoint_sha256,
        "external checkpoint SHA-256": external.get("checkpoint_sha256") == checkpoint_sha256,
        "freeze experiment ID": freeze.get("experiment_id") == experiment_id,
        "external experiment ID": external.get("experiment_id") == experiment_id,
        "training configuration": freeze.get("training_configuration")
        == protocol_payload["training"],
    }
    failed = [name for name, matches in checks.items() if not matches]
    if failed:
        raise ValueError(f"evidence identity mismatch: {', '.join(failed)}")


def run_independent_evaluation(
    protocol,
    freeze_manifest,
    checkpoint,
    external_root,
    external_manifest,
    demol_root,
    evidence_dir,
    repo_root,
):
    """Run the only strict production path for independent evidence."""
    protocol_path = Path(protocol).resolve()
    freeze_path = Path(freeze_manifest).resolve()
    checkpoint_path = Path(checkpoint).resolve()
    external_manifest_path = Path(external_manifest).resolve()
    evidence_path = Path(evidence_dir).resolve()
    repository = Path(repo_root).resolve()

    try:
        protocol_payload = load_protocol(protocol_path)
    except Exception as exc:
        raise IndependentEvaluationError(f"protocol guard failed: {exc}") from exc
    try:
        freeze = _load_freeze(freeze_path)
    except Exception as exc:
        raise IndependentEvaluationError(f"freeze guard failed: {exc}") from exc
    try:
        external = _load_external_manifest(external_manifest_path)
    except Exception as exc:
        raise IndependentEvaluationError(f"external guard failed: {exc}") from exc

    try:
        protocol_sha256 = sha256_file(protocol_path)
        freeze_sha256 = sha256_file(freeze_path)
        external_sha256 = sha256_file(external_manifest_path)
        checkpoint_sha256 = sha256_file(checkpoint_path)
        _identity_matches(
            protocol_payload,
            freeze,
            external,
            protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256,
            checkpoint_sha256=checkpoint_sha256,
        )
    except Exception as exc:
        raise IndependentEvaluationError(f"identity guard failed: {exc}") from exc
    try:
        evaluation_git_commit = _validate_git_evidence_state(
            repo_root=repository,
            protocol_path=protocol_path,
            freeze_path=freeze_path,
            external_manifest_path=external_manifest_path,
            training_git_commit=freeze["training_git_commit"],
        )
        _preflight_evidence_dir(evidence_path)
    except Exception as exc:
        raise IndependentEvaluationError(f"git/output guard failed: {exc}") from exc

    identity = ValidatedEvidenceIdentity(
        schema_version="1",
        experiment_id=protocol_payload["experiment_id"],
        protocol_sha256=protocol_sha256,
        freeze_manifest_sha256=freeze_sha256,
        external_manifest_sha256=external_sha256,
        checkpoint_sha256=checkpoint_sha256,
        evaluation_git_commit=evaluation_git_commit,
    )
    try:
        external_cohort = load_external_trees(str(Path(external_root).resolve()), external)
        if [tree[0] for tree in external_cohort] != external["tree_ids"]:
            raise ValueError("external loader tree IDs do not match validated manifest")
        demol_cohort = load_demol_cohort(
            str(Path(demol_root).resolve()),
            max_points=protocol_payload["demol"]["max_points"],
            sample_seed=protocol_payload["demol"]["sampling_seed"],
            formal=True,
            expected_tree_ids=protocol_payload["demol"]["tree_ids"],
        )
        segmenter = WoodLeafSegmenter(str(checkpoint_path), backend="pointnet")
        baseline_options = dict(protocol_payload["baseline"])
        if baseline_options.pop("backend") != "tlsep":
            raise ValueError("baseline backend must be tlsep")
        tiled_options = dict(protocol_payload["pointnet_inference"])
        required_coverage = tiled_options.pop("required_coverage")

        def baseline_predictor(points: np.ndarray) -> np.ndarray:
            return segment_wood_leaf(points, **baseline_options)

        def candidate_predictor(points: np.ndarray) -> np.ndarray:
            prediction = predict_tiled(points, segmenter.pointnet_logits, **tiled_options)
            coverage = np.asarray(prediction.coverage)
            labels = _labels(prediction.labels, n_points=len(points), backend="candidate")
            logits = np.asarray(prediction.logits)
            if (
                coverage.ndim != 1
                or len(coverage) != len(points)
                or coverage.dtype.kind not in "iu"
                or np.any(coverage < 0)
            ):
                raise ValueError("PointNet tiled coverage is invalid")
            coverage_fraction = float(np.count_nonzero(coverage) / len(points))
            if coverage_fraction != required_coverage:
                raise ValueError(
                    f"PointNet tiled coverage must equal {required_coverage}, got {coverage_fraction}"
                )
            if logits.shape != (len(points), 2) or not np.all(np.isfinite(logits)):
                raise ValueError("PointNet tiled logits must be finite with shape (N, 2)")
            return labels

        bundle = _compose_evaluation_from_validated_inputs(
            identity=identity,
            protocol=protocol_payload,
            external_cohort=external_cohort,
            demol_cohort=demol_cohort,
            baseline_predictor=baseline_predictor,
            candidate_predictor=candidate_predictor,
            qsm_func=qsm.compute_qsm,
        )
        return _publish_evidence_artifacts(bundle, evidence_path)
    except IndependentEvaluationError:
        raise
    except Exception as exc:
        raise IndependentEvaluationError(str(exc)) from exc
