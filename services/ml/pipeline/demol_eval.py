"""Strict paired downstream evaluation on the Demol tree cohort."""

from __future__ import annotations

import csv
import math
import os
import re
import warnings
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import qsm

_CSV_NAME = "Destructive_and_qsm_data_DEMOL.csv"
_POINT_DIR = Path("pointclouds") / "pointclouds_clean"
_REQUIRED_COLUMNS = {
    "tree_name",
    "DBH",
    "TH_felled",
    "Volume_total_tree_harvested",
}
_PREDICTION_FIELDS = (
    "dbh_cm",
    "height_m",
    "volume_m3",
    "dbh_abs_error_cm",
    "height_abs_error_m",
    "volume_ape_pct",
)


@dataclass(frozen=True, slots=True)
class DemolTree:
    """One sampled Demol tree and its destructive ground truth."""

    tree_id: str
    points: np.ndarray
    gt_dbh_cm: float
    gt_height_m: float
    gt_volume_m3: float


def _exact_positive_int(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _exact_non_negative_int(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _positive_finite_real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    if converted <= 0.0:
        raise ValueError(f"{name} must be positive")
    return converted


def _csv_positive_float(value: object, *, name: str) -> float:
    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    if converted <= 0.0:
        raise ValueError(f"{name} must be positive")
    return converted


def _valid_exact_id(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be an exact string")
    if not value or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{name} must not contain surrounding whitespace")
    return value


def _file_to_csv_name(file_stem: str) -> str:
    """Apply the exact filename normalization used by validate_belgium.py."""
    match = re.match(r"^([A-Z]+)(\d+)$", file_stem)
    if not match:
        return file_stem
    species, number = match.group(1), int(match.group(2))
    return f"{species}-{number:02d}"


def _expected_ids(value: object) -> list[str] | None:
    if value is None:
        return None
    if type(value) is not list:
        raise TypeError("expected_tree_ids must be an exact list")
    if not value:
        raise ValueError("expected_tree_ids must be non-empty")
    ids = [
        _valid_exact_id(tree_id, name=f"expected_tree_ids[{index}]")
        for index, tree_id in enumerate(value)
    ]
    if len(ids) != len(set(ids)):
        raise ValueError("expected_tree_ids must be unique")
    if ids != sorted(ids):
        raise ValueError("expected_tree_ids must be sorted")
    return ids


def _read_ground_truth(csv_path: Path) -> dict[str, tuple[float, float, float]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if fieldnames is None or not _REQUIRED_COLUMNS.issubset(fieldnames):
            raise ValueError("Demol CSV is missing required columns")
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("Demol CSV contains duplicate column names")
        rows = list(reader)

    if not rows:
        raise ValueError("Demol CSV must contain at least one tree")

    ground_truth: dict[str, tuple[float, float, float]] = {}
    casefold_ids: dict[str, str] = {}
    for row_index, row in enumerate(rows, start=2):
        tree_id = _valid_exact_id(row.get("tree_name"), name=f"CSV row {row_index} tree_name")
        folded = tree_id.casefold()
        if tree_id in ground_truth:
            raise ValueError(f"duplicate CSV tree ID: {tree_id}")
        if folded in casefold_ids:
            raise ValueError(f"case-colliding CSV tree IDs: {casefold_ids[folded]} and {tree_id}")

        dbh_cm = _csv_positive_float(row.get("DBH"), name=f"{tree_id}.DBH")
        height_m = _csv_positive_float(row.get("TH_felled"), name=f"{tree_id}.TH_felled")
        volume_dm3 = _csv_positive_float(
            row.get("Volume_total_tree_harvested"),
            name=f"{tree_id}.Volume_total_tree_harvested",
        )
        volume_m3 = _positive_finite_real(
            volume_dm3 / 1000.0,
            name=f"{tree_id}.gt_volume_m3",
        )
        ground_truth[tree_id] = (dbh_cm, height_m, volume_m3)
        casefold_ids[folded] = tree_id
    return ground_truth


def _point_file_map(point_dir: Path) -> dict[str, Path]:
    point_files: dict[str, Path] = {}
    casefold_ids: dict[str, str] = {}
    for path in sorted(point_dir.glob("*.txt"), key=lambda item: item.name):
        tree_id = _valid_exact_id(_file_to_csv_name(path.stem), name=f"point file {path.name}")
        folded = tree_id.casefold()
        if tree_id in point_files:
            raise ValueError(f"duplicate normalized point-cloud ID: {tree_id}")
        if folded in casefold_ids:
            raise ValueError(
                f"case-colliding normalized point-cloud IDs: {casefold_ids[folded]} and {tree_id}"
            )
        point_files[tree_id] = path
        casefold_ids[folded] = tree_id
    return point_files


def _load_xyz(path: Path, *, max_points: int, sample_seed: int) -> np.ndarray:
    if path.stat().st_size == 0:
        raise ValueError(f"point cloud is empty: {path.name}")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            loaded = np.loadtxt(path, dtype=np.float64, usecols=(0, 1, 2))
    except (OSError, TypeError, ValueError, UserWarning) as exc:
        raise ValueError(f"malformed point cloud: {path.name}") from exc

    if loaded.ndim == 1:
        loaded = loaded.reshape(1, -1)
    if loaded.ndim != 2 or loaded.shape[0] == 0:
        raise ValueError(f"point cloud must be a non-empty two-dimensional array: {path.name}")
    if loaded.shape[1] < 3:
        raise ValueError(f"point cloud must have at least three columns: {path.name}")

    xyz = np.ascontiguousarray(loaded[:, :3], dtype=np.float64)
    if not np.all(np.isfinite(xyz)):
        raise ValueError(f"point cloud XYZ must be finite: {path.name}")
    xyz = xyz.copy(order="C")
    with np.errstate(over="ignore", invalid="ignore"):
        xyz[:, 2] -= float(np.min(xyz[:, 2]))
    if not np.all(np.isfinite(xyz)):
        raise ValueError(f"point cloud Z normalization must remain finite: {path.name}")
    if len(xyz) > max_points:
        rng = np.random.default_rng(sample_seed)
        selected = np.sort(rng.choice(len(xyz), max_points, replace=False))
        xyz = np.ascontiguousarray(xyz[selected], dtype=np.float64)
    return xyz


def load_demol_cohort(
    data_root: str | os.PathLike[str],
    *,
    max_points: int = 20_000,
    sample_seed: int = 0,
    formal: bool = True,
    expected_tree_ids: list[str] | None = None,
) -> list[DemolTree]:
    """Load, validate, normalize and deterministically sample a Demol cohort."""
    max_points = _exact_positive_int(max_points, name="max_points")
    sample_seed = _exact_non_negative_int(sample_seed, name="sample_seed")
    if type(formal) is not bool:
        raise TypeError("formal must be an exact boolean")
    expected_ids = _expected_ids(expected_tree_ids)
    if not isinstance(data_root, (str, os.PathLike)):
        raise TypeError("data_root must be a path string or path-like object")

    root = Path(data_root)
    csv_path = root / _CSV_NAME
    point_dir = root / _POINT_DIR
    if not csv_path.is_file():
        raise FileNotFoundError(f"missing Demol CSV: {csv_path}")
    if not point_dir.is_dir():
        raise FileNotFoundError(f"missing Demol point-cloud directory: {point_dir}")

    ground_truth = _read_ground_truth(csv_path)
    point_files = _point_file_map(point_dir)
    matched_ids = sorted(set(ground_truth).intersection(point_files))
    if not matched_ids:
        raise ValueError("Demol CSV and point files have no exact ID matches")
    if formal and expected_ids is None:
        raise ValueError("formal Demol evaluation requires frozen expected_tree_ids")
    if formal and len(matched_ids) != 65:
        raise ValueError(
            f"formal Demol cohort requires exactly 65 matched trees, got {len(matched_ids)}"
        )
    if expected_ids is not None and expected_ids != matched_ids:
        raise ValueError("expected_tree_ids must exactly equal the sorted matched cohort IDs")

    cohort: list[DemolTree] = []
    for tree_id in matched_ids:
        dbh_cm, height_m, volume_m3 = ground_truth[tree_id]
        points = _load_xyz(
            point_files[tree_id],
            max_points=max_points,
            sample_seed=sample_seed,
        )
        cohort.append(DemolTree(tree_id, points, dbh_cm, height_m, volume_m3))
    return cohort


def _validated_cohort(cohort: object) -> list[tuple[DemolTree, np.ndarray, float, float, float]]:
    if isinstance(cohort, (str, bytes)) or not isinstance(cohort, Iterable):
        raise TypeError("cohort must be an iterable of DemolTree records")
    trees = list(cohort)
    if not trees:
        raise ValueError("cohort must be non-empty")

    validated: list[tuple[DemolTree, np.ndarray, float, float, float]] = []
    seen_ids: set[str] = set()
    for index, tree in enumerate(trees):
        if type(tree) is not DemolTree:
            raise TypeError(f"cohort[{index}] must be exactly DemolTree")
        tree_id = _valid_exact_id(tree.tree_id, name=f"cohort[{index}].tree_id")
        if tree_id in seen_ids:
            raise ValueError(f"duplicate cohort tree ID: {tree_id}")
        seen_ids.add(tree_id)

        points = tree.points
        if not isinstance(points, np.ndarray):
            raise TypeError(f"{tree_id}.points must be a NumPy array")
        if points.ndim != 2 or points.shape[0] == 0 or points.shape[1] != 3:
            raise ValueError(f"{tree_id}.points must have non-empty shape (N, 3)")
        if points.dtype.kind not in "fiu":
            raise TypeError(f"{tree_id}.points must have a real numeric dtype")
        if not np.all(np.isfinite(points)):
            raise ValueError(f"{tree_id}.points must contain only finite XYZ")
        with np.errstate(over="ignore", invalid="ignore"):
            paired_points = np.array(points, dtype=np.float64, order="C", copy=True)
        if not np.all(np.isfinite(paired_points)):
            raise ValueError(f"{tree_id}.points must remain finite after float64 conversion")

        dbh_cm = _positive_finite_real(tree.gt_dbh_cm, name=f"{tree_id}.gt_dbh_cm")
        height_m = _positive_finite_real(tree.gt_height_m, name=f"{tree_id}.gt_height_m")
        volume_m3 = _positive_finite_real(tree.gt_volume_m3, name=f"{tree_id}.gt_volume_m3")
        validated.append((tree, paired_points, dbh_cm, height_m, volume_m3))
    return sorted(validated, key=lambda item: item[0].tree_id)


def _labels(output: object, *, n_points: int, backend: str) -> np.ndarray:
    labels = np.asarray(output)
    if labels.ndim != 1:
        raise ValueError(f"{backend} labels must be one-dimensional")
    if labels.size == 0:
        raise ValueError(f"{backend} labels must be non-empty")
    if labels.dtype.kind not in "iu":
        raise TypeError(f"{backend} labels must have an integer dtype")
    if len(labels) != n_points:
        raise ValueError(f"{backend} labels must have one label per point")
    if not np.all((labels == 0) | (labels == 1)):
        raise ValueError(f"{backend} labels must contain only 0 or 1")
    return labels


def _empty_backend(backend: str, *, failure: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        f"{backend}_status": "failed" if failure is not None else "measurable",
        f"{backend}_failure": failure,
    }
    result.update({f"{backend}_{field}": None for field in _PREDICTION_FIELDS})
    return result


def _failure_reason(stage: str, exc: Exception) -> str:
    return f"{stage}: {type(exc).__name__}"


def _assert_paired_input(
    points: np.ndarray,
    *,
    original_bytes: bytes,
    original_shape: tuple[int, ...],
    original_strides: tuple[int, ...],
    backend: str,
    stage: str,
) -> None:
    unchanged = (
        points.shape == original_shape
        and points.strides == original_strides
        and points.dtype == np.dtype(np.float64)
        and points.flags.c_contiguous
        and not points.flags.writeable
        and points.tobytes(order="C") == original_bytes
    )
    if not unchanged:
        raise ValueError(f"paired input contract violated during {backend} {stage}")


def _run_backend(
    backend: str,
    *,
    predictor: Callable[[np.ndarray], object],
    points: np.ndarray,
    original_bytes: bytes,
    original_shape: tuple[int, ...],
    original_strides: tuple[int, ...],
    qsm_func: Callable[..., object],
    qsm_seed: int,
    gt_dbh_cm: float,
    gt_height_m: float,
    gt_volume_m3: float,
) -> dict[str, Any]:
    def assert_paired_input(stage: str) -> None:
        _assert_paired_input(
            points,
            original_bytes=original_bytes,
            original_shape=original_shape,
            original_strides=original_strides,
            backend=backend,
            stage=stage,
        )

    assert_paired_input("before predictor")
    try:
        output = predictor(points)
    except Exception as exc:
        assert_paired_input("predictor exception")
        return _empty_backend(backend, failure=_failure_reason("predictor", exc))

    assert_paired_input("after predictor")
    try:
        labels = _labels(output, n_points=len(points), backend=backend)
    except Exception as exc:
        assert_paired_input("label conversion exception")
        return _empty_backend(backend, failure=_failure_reason("labels", exc))
    assert_paired_input("after label conversion")

    wood_points = np.ascontiguousarray(points[labels == 0], dtype=np.float64)
    try:
        measurement = qsm_func(wood_points, seed=qsm_seed)
    except Exception as exc:
        assert_paired_input("qsm exception")
        return _empty_backend(backend, failure=_failure_reason("qsm", exc))
    assert_paired_input("after qsm")

    try:
        dbh_cm = _positive_finite_real(measurement.dbh_cm, name=f"{backend}.dbh_cm")
        height_m = _positive_finite_real(measurement.height_m, name=f"{backend}.height_m")
        volume_m3 = _positive_finite_real(
            measurement.total_volume_m3, name=f"{backend}.total_volume_m3"
        )
        dbh_abs_error_cm = abs(dbh_cm - gt_dbh_cm)
        height_abs_error_m = abs(height_m - gt_height_m)
        volume_ape_pct = abs(volume_m3 - gt_volume_m3) / gt_volume_m3 * 100.0
        if not all(
            math.isfinite(value) for value in (dbh_abs_error_cm, height_abs_error_m, volume_ape_pct)
        ):
            raise ValueError(f"{backend} derived errors must be finite")
    except Exception as exc:
        assert_paired_input("measurement validation exception")
        return _empty_backend(backend, failure=_failure_reason("qsm_validation", exc))
    assert_paired_input("after measurement validation")

    result = _empty_backend(backend, failure=None)
    result.update(
        {
            f"{backend}_dbh_cm": dbh_cm,
            f"{backend}_height_m": height_m,
            f"{backend}_volume_m3": volume_m3,
            f"{backend}_dbh_abs_error_cm": dbh_abs_error_cm,
            f"{backend}_height_abs_error_m": height_abs_error_m,
            f"{backend}_volume_ape_pct": volume_ape_pct,
        }
    )
    return result


def _aggregate(rows: list[dict[str, Any]], *, backend: str) -> dict[str, float | int | None]:
    measurable = [row for row in rows if row[f"{backend}_status"] == "measurable"]
    if not measurable:
        return {
            "dbh_mae_cm": None,
            "height_mae_m": None,
            "volume_mape_pct": None,
            "measurable_trees": 0,
        }
    count = len(measurable)
    return {
        "dbh_mae_cm": math.fsum(row[f"{backend}_dbh_abs_error_cm"] / count for row in measurable),
        "height_mae_m": math.fsum(
            row[f"{backend}_height_abs_error_m"] / count for row in measurable
        ),
        "volume_mape_pct": math.fsum(
            row[f"{backend}_volume_ape_pct"] / count for row in measurable
        ),
        "measurable_trees": count,
    }


def evaluate_demol_pair(
    cohort: Iterable[DemolTree],
    *,
    baseline_predictor: Callable[[np.ndarray], object],
    candidate_predictor: Callable[[np.ndarray], object],
    qsm_func: Callable[..., object] = qsm.compute_qsm,
    qsm_seed: int = 0,
) -> dict[str, Any]:
    """Evaluate paired wood/leaf predictors through one identical QSM path."""
    if not callable(baseline_predictor):
        raise TypeError("baseline_predictor must be callable")
    if not callable(candidate_predictor):
        raise TypeError("candidate_predictor must be callable")
    if not callable(qsm_func):
        raise TypeError("qsm_func must be callable")
    qsm_seed = _exact_non_negative_int(qsm_seed, name="qsm_seed")
    trees = _validated_cohort(cohort)

    per_tree: list[dict[str, Any]] = []
    for tree, points, gt_dbh_cm, gt_height_m, gt_volume_m3 in trees:
        points.setflags(write=False)
        original_bytes = points.tobytes(order="C")
        original_shape = points.shape
        original_strides = points.strides
        row: dict[str, Any] = {
            "tree_id": tree.tree_id,
            "gt_dbh_cm": gt_dbh_cm,
            "gt_height_m": gt_height_m,
            "gt_volume_m3": gt_volume_m3,
        }
        row.update(
            _run_backend(
                "baseline",
                predictor=baseline_predictor,
                points=points,
                original_bytes=original_bytes,
                original_shape=original_shape,
                original_strides=original_strides,
                qsm_func=qsm_func,
                qsm_seed=qsm_seed,
                gt_dbh_cm=gt_dbh_cm,
                gt_height_m=gt_height_m,
                gt_volume_m3=gt_volume_m3,
            )
        )
        row.update(
            _run_backend(
                "candidate",
                predictor=candidate_predictor,
                points=points,
                original_bytes=original_bytes,
                original_shape=original_shape,
                original_strides=original_strides,
                qsm_func=qsm_func,
                qsm_seed=qsm_seed,
                gt_dbh_cm=gt_dbh_cm,
                gt_height_m=gt_height_m,
                gt_volume_m3=gt_volume_m3,
            )
        )
        per_tree.append(row)

    return {
        "per_tree": per_tree,
        "baseline": _aggregate(per_tree, backend="baseline"),
        "candidate": _aggregate(per_tree, backend="candidate"),
    }
