from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import numpy as np
import pytest

import pipeline.demol_eval as demol_eval
from pipeline.demol_eval import DemolTree, evaluate_demol_pair, load_demol_cohort

CSV_FIELDS = (
    "tree_name",
    "DBH",
    "TH_felled",
    "Volume_total_tree_harvested",
)


def _tree(
    tree_id: str,
    x: float = 1.0,
    *,
    dbh: float = 10.0,
    height: float = 5.0,
    volume: float = 2.0,
    points: np.ndarray | None = None,
) -> DemolTree:
    if points is None:
        points = np.array(
            [[x, 0.0, 0.0], [x, 1.0, 1.0], [x, 2.0, 2.0], [x, 3.0, 3.0]],
            dtype=np.float64,
        )
    return DemolTree(tree_id, points, dbh, height, volume)


def _qsm(dbh: object = 10.0, height: object = 5.0, volume: object = 2.0):
    return SimpleNamespace(dbh_cm=dbh, height_m=height, total_volume_m3=volume)


def _all_wood(points: np.ndarray) -> np.ndarray:
    return np.zeros(len(points), dtype=np.int8)


def _write_fixture(data_root, rows, clouds) -> None:
    point_dir = data_root / "pointclouds" / "pointclouds_clean"
    point_dir.mkdir(parents=True)
    with (data_root / "Destructive_and_qsm_data_DEMOL.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    for filename, contents in clouds.items():
        path = point_dir / filename
        if isinstance(contents, str):
            path.write_text(contents, encoding="utf-8")
        else:
            np.savetxt(path, contents)


def _row(
    tree_id: object,
    *,
    dbh: object = 10.0,
    height: object = 5.0,
    volume_dm3: object = 2000.0,
) -> dict[str, object]:
    return {
        "tree_name": tree_id,
        "DBH": dbh,
        "TH_felled": height,
        "Volume_total_tree_harvested": volume_dm3,
    }


def test_demol_tree_is_an_immutable_record():
    tree = _tree("TREE-A")

    with pytest.raises(FrozenInstanceError):
        tree.gt_dbh_cm = 12.0  # type: ignore[misc]


def test_known_value_errors_and_aggregates_keep_full_precision():
    cohort = [
        _tree("TREE-B", 2.0, dbh=20.0, height=10.0, volume=4.0),
        _tree("TREE-A", 1.0, dbh=10.0, height=5.0, volume=2.0),
    ]

    predictions = {
        (1.0, 3): _qsm(11.125, 4.75, 2.25),
        (1.0, 2): _qsm(9.5, 5.5, 1.75),
        (2.0, 3): _qsm(18.25, 11.125, 3.5),
        (2.0, 2): _qsm(20.75, 9.875, 4.5),
    }

    def fake_qsm(wood: np.ndarray, *, seed: int):
        assert seed == 0
        return predictions[(float(wood[0, 0]), len(wood))]

    result = evaluate_demol_pair(
        cohort,
        baseline_predictor=lambda points: np.array([0, 0, 0, 1], dtype=np.int8),
        candidate_predictor=lambda points: np.array([0, 0, 1, 1], dtype=np.int8),
        qsm_func=fake_qsm,
        qsm_seed=0,
    )

    assert [row["tree_id"] for row in result["per_tree"]] == ["TREE-A", "TREE-B"]
    assert result["per_tree"][0] == {
        "tree_id": "TREE-A",
        "gt_dbh_cm": 10.0,
        "gt_height_m": 5.0,
        "gt_volume_m3": 2.0,
        "baseline_status": "measurable",
        "baseline_failure": None,
        "baseline_dbh_cm": 11.125,
        "baseline_height_m": 4.75,
        "baseline_volume_m3": 2.25,
        "baseline_dbh_abs_error_cm": 1.125,
        "baseline_height_abs_error_m": 0.25,
        "baseline_volume_ape_pct": 12.5,
        "candidate_status": "measurable",
        "candidate_failure": None,
        "candidate_dbh_cm": 9.5,
        "candidate_height_m": 5.5,
        "candidate_volume_m3": 1.75,
        "candidate_dbh_abs_error_cm": 0.5,
        "candidate_height_abs_error_m": 0.5,
        "candidate_volume_ape_pct": 12.5,
    }
    assert result["baseline"] == {
        "dbh_mae_cm": 1.4375,
        "height_mae_m": 0.6875,
        "volume_mape_pct": 12.5,
        "measurable_trees": 2,
    }
    assert result["candidate"] == {
        "dbh_mae_cm": 0.625,
        "height_mae_m": 0.3125,
        "volume_mape_pct": 12.5,
        "measurable_trees": 2,
    }


def test_predictors_share_one_read_only_object_and_every_backend_is_called_once():
    cohort = [_tree("TREE-B", 2.0), _tree("TREE-A", 1.0)]
    baseline_seen: list[np.ndarray] = []
    candidate_seen: list[np.ndarray] = []
    baseline_snapshots: list[bytes] = []
    candidate_snapshots: list[bytes] = []
    qsm_calls: list[tuple[float, int, int]] = []

    def baseline(points: np.ndarray) -> np.ndarray:
        baseline_seen.append(points)
        baseline_snapshots.append(points.tobytes())
        return np.array([0, 0, 0, 1], dtype=np.int8)

    def candidate(points: np.ndarray) -> np.ndarray:
        candidate_seen.append(points)
        candidate_snapshots.append(points.tobytes())
        return np.array([0, 0, 1, 1], dtype=np.int8)

    def fake_qsm(wood: np.ndarray, *, seed: int):
        qsm_calls.append((float(wood[0, 0]), len(wood), seed))
        return _qsm()

    evaluate_demol_pair(
        cohort,
        baseline_predictor=baseline,
        candidate_predictor=candidate,
        qsm_func=fake_qsm,
    )

    assert len(baseline_seen) == len(candidate_seen) == 2
    for baseline_points, candidate_points in zip(baseline_seen, candidate_seen, strict=True):
        assert baseline_points is candidate_points
        assert baseline_points.flags.c_contiguous
        assert not baseline_points.flags.writeable
        assert baseline_points.tobytes() == candidate_points.tobytes()
    assert [float(points[0, 0]) for points in baseline_seen] == [1.0, 2.0]
    assert baseline_snapshots == candidate_snapshots
    assert baseline_snapshots == [cohort[1].points.tobytes(), cohort[0].points.tobytes()]
    assert Counter(qsm_calls) == Counter([(1.0, 3, 0), (1.0, 2, 0), (2.0, 3, 0), (2.0, 2, 0)])


def test_normal_write_attempt_is_failed_independently_without_changing_candidate_input():
    tree = _tree("TREE-A")
    candidate_seen: list[np.ndarray] = []

    def baseline(points: np.ndarray) -> np.ndarray:
        points[0, 0] = 99.0
        return _all_wood(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        candidate_seen.append(points.copy())
        return _all_wood(points)

    result = evaluate_demol_pair(
        [tree],
        baseline_predictor=baseline,
        candidate_predictor=candidate,
        qsm_func=lambda wood, *, seed: _qsm(),
    )

    assert result["per_tree"][0]["baseline_status"] == "failed"
    assert result["per_tree"][0]["candidate_status"] == "measurable"
    assert np.array_equal(candidate_seen[0], tree.points)


def test_force_mutation_is_a_whole_call_contract_error_and_never_reaches_candidate():
    tree = _tree("TREE-A")
    original = tree.points.copy()
    candidate_calls = 0

    def baseline(points: np.ndarray) -> np.ndarray:
        points.flags.writeable = True
        points[0, 0] = 99.0
        return _all_wood(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        nonlocal candidate_calls
        candidate_calls += 1
        return _all_wood(points)

    with pytest.raises(ValueError, match="paired input"):
        evaluate_demol_pair(
            [tree],
            baseline_predictor=baseline,
            candidate_predictor=candidate,
            qsm_func=lambda wood, *, seed: _qsm(),
        )

    assert candidate_calls == 0
    assert np.array_equal(tree.points, original)


@pytest.mark.parametrize("raise_during_conversion", [False, True])
def test_label_array_conversion_mutation_aborts_before_candidate(raise_during_conversion):
    tree = _tree("TREE-A")
    candidate_snapshots: list[bytes] = []

    class MutatingLabels:
        def __init__(self, paired_points: np.ndarray):
            self.paired_points = paired_points

        def __array__(self, dtype=None, copy=None):
            self.paired_points.flags.writeable = True
            self.paired_points[0, 0] = 99.0
            if raise_during_conversion:
                raise RuntimeError("conversion failed after mutation")
            return np.zeros(len(self.paired_points), dtype=np.int8)

    def baseline(points: np.ndarray):
        return MutatingLabels(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        candidate_snapshots.append(points.tobytes())
        return _all_wood(points)

    with pytest.raises(ValueError, match="paired input"):
        evaluate_demol_pair(
            [tree],
            baseline_predictor=baseline,
            candidate_predictor=candidate,
            qsm_func=lambda wood, *, seed: _qsm(),
        )

    assert candidate_snapshots == []


@pytest.mark.parametrize("raise_after_mutation", [False, True])
def test_qsm_closure_mutation_aborts_before_candidate(raise_after_mutation):
    tree = _tree("TREE-A")
    shared: dict[str, np.ndarray] = {}
    candidate_snapshots: list[bytes] = []

    def baseline(points: np.ndarray) -> np.ndarray:
        shared["points"] = points
        return _all_wood(points)

    def mutating_qsm(wood: np.ndarray, *, seed: int):
        shared["points"].flags.writeable = True
        shared["points"][0, 0] = 99.0
        if raise_after_mutation:
            raise RuntimeError("qsm failed after mutation")
        return _qsm()

    def candidate(points: np.ndarray) -> np.ndarray:
        candidate_snapshots.append(points.tobytes())
        return _all_wood(points)

    with pytest.raises(ValueError, match="paired input"):
        evaluate_demol_pair(
            [tree],
            baseline_predictor=baseline,
            candidate_predictor=candidate,
            qsm_func=mutating_qsm,
        )

    assert candidate_snapshots == []


def test_measurement_validation_mutation_aborts_before_candidate():
    tree = _tree("TREE-A")
    shared: dict[str, np.ndarray] = {}
    candidate_snapshots: list[bytes] = []

    class MutatingMeasurement:
        @property
        def dbh_cm(self):
            shared["points"].flags.writeable = True
            shared["points"][0, 0] = 99.0
            return 10.0

        height_m = 5.0
        total_volume_m3 = 2.0

    def baseline(points: np.ndarray) -> np.ndarray:
        shared["points"] = points
        return _all_wood(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        candidate_snapshots.append(points.tobytes())
        return _all_wood(points)

    with pytest.raises(ValueError, match="paired input"):
        evaluate_demol_pair(
            [tree],
            baseline_predictor=baseline,
            candidate_predictor=candidate,
            qsm_func=lambda wood, *, seed: MutatingMeasurement(),
        )

    assert candidate_snapshots == []


def test_candidate_failures_retain_every_row_and_zero_count_uses_none_metrics():
    cohort = [_tree(f"TREE-{index}", float(index)) for index in range(1, 5)]

    def candidate(points: np.ndarray) -> np.ndarray:
        tree_number = int(points[0, 0])
        if tree_number == 1:
            raise RuntimeError("boom")
        if tree_number == 2:
            return np.array([0, 2, 1, 1], dtype=np.int8)
        return np.array([0, 0, 1, 1], dtype=np.int8)

    def fake_qsm(wood: np.ndarray, *, seed: int):
        tree_number = int(wood[0, 0])
        if len(wood) == 2 and tree_number == 3:
            return _qsm(dbh=0.0)
        if len(wood) == 2 and tree_number == 4:
            return _qsm(height=float("inf"))
        return _qsm()

    result = evaluate_demol_pair(
        cohort,
        baseline_predictor=_all_wood,
        candidate_predictor=candidate,
        qsm_func=fake_qsm,
    )

    assert len(result["per_tree"]) == 4
    assert all(row["baseline_status"] == "measurable" for row in result["per_tree"])
    assert all(row["candidate_status"] == "failed" for row in result["per_tree"])
    assert result["per_tree"][0]["candidate_failure"] == "predictor: RuntimeError"
    assert all(row["candidate_failure"] for row in result["per_tree"])
    for row in result["per_tree"]:
        assert row["candidate_dbh_cm"] is None
        assert row["candidate_height_m"] is None
        assert row["candidate_volume_m3"] is None
        assert row["candidate_dbh_abs_error_cm"] is None
        assert row["candidate_height_abs_error_m"] is None
        assert row["candidate_volume_ape_pct"] is None
    assert result["baseline"]["measurable_trees"] == 4
    assert result["candidate"] == {
        "dbh_mae_cm": None,
        "height_mae_m": None,
        "volume_mape_pct": None,
        "measurable_trees": 0,
    }


def test_baseline_and_candidate_failures_are_independent_without_fallback():
    cohort = [_tree("TREE-A", 1.0), _tree("TREE-B", 2.0)]

    def baseline(points: np.ndarray) -> np.ndarray:
        if points[0, 0] == 1.0:
            return np.array([0.0, 0.0, 0.0, 1.0])
        return _all_wood(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        if points[0, 0] == 2.0:
            raise LookupError("candidate unavailable")
        return np.array([0, 0, 1, 1], dtype=np.int8)

    result = evaluate_demol_pair(
        cohort,
        baseline_predictor=baseline,
        candidate_predictor=candidate,
        qsm_func=lambda wood, *, seed: _qsm(12.0, 6.0, 3.0),
    )

    first, second = result["per_tree"]
    assert (first["baseline_status"], first["candidate_status"]) == ("failed", "measurable")
    assert (second["baseline_status"], second["candidate_status"]) == ("measurable", "failed")
    assert first["candidate_dbh_cm"] == 12.0
    assert second["candidate_dbh_cm"] is None
    assert result["baseline"]["measurable_trees"] == 1
    assert result["candidate"]["measurable_trees"] == 1


def test_nonfinite_derived_volume_error_is_a_backend_failure():
    tree = _tree("TREE-A", volume=np.nextafter(0.0, 1.0))

    result = evaluate_demol_pair(
        [tree],
        baseline_predictor=_all_wood,
        candidate_predictor=_all_wood,
        qsm_func=lambda wood, *, seed: _qsm(volume=1e308),
    )

    assert result["per_tree"][0]["baseline_status"] == "failed"
    assert result["per_tree"][0]["candidate_status"] == "failed"
    assert result["baseline"]["volume_mape_pct"] is None
    assert result["candidate"]["volume_mape_pct"] is None


def test_aggregate_mean_stays_finite_when_naive_positive_sum_would_overflow():
    cohort = [_tree("TREE-A", volume=1.0), _tree("TREE-B", volume=1.0)]

    result = evaluate_demol_pair(
        cohort,
        baseline_predictor=_all_wood,
        candidate_predictor=_all_wood,
        qsm_func=lambda wood, *, seed: _qsm(volume=1e306),
    )

    assert math.isfinite(result["baseline"]["volume_mape_pct"])
    assert result["baseline"]["volume_mape_pct"] == 1e308
    assert result["candidate"]["volume_mape_pct"] == 1e308


@pytest.mark.parametrize(
    "labels",
    [
        np.array([], dtype=np.int8),
        np.array([[0, 1, 1, 0]], dtype=np.int8),
        np.array([0, 1, 1], dtype=np.int8),
        np.array([0.0, 0.0, 1.0, 1.0]),
        np.array([False, False, True, True]),
        np.array([0, 0, 1, 2], dtype=np.int8),
    ],
)
def test_invalid_predictor_labels_are_retained_as_backend_failures(labels):
    result = evaluate_demol_pair(
        [_tree("TREE-A")],
        baseline_predictor=_all_wood,
        candidate_predictor=lambda points: labels,
        qsm_func=lambda wood, *, seed: _qsm(),
    )

    assert result["per_tree"][0]["baseline_status"] == "measurable"
    assert result["per_tree"][0]["candidate_status"] == "failed"
    assert result["candidate"]["measurable_trees"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dbh", 0.0),
        ("dbh", -1.0),
        ("dbh", float("nan")),
        ("height", float("inf")),
        ("height", True),
        ("volume", "2.0"),
    ],
)
def test_invalid_qsm_measurements_are_retained_as_backend_failures(field, value):
    measurements = {"dbh": 10.0, "height": 5.0, "volume": 2.0}
    measurements[field] = value

    result = evaluate_demol_pair(
        [_tree("TREE-A")],
        baseline_predictor=_all_wood,
        candidate_predictor=_all_wood,
        qsm_func=lambda wood, *, seed: _qsm(**measurements),
    )

    assert result["per_tree"][0]["baseline_status"] == "failed"
    assert result["per_tree"][0]["candidate_status"] == "failed"


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit()])
def test_control_flow_exceptions_are_not_caught(error):
    def predictor(_points: np.ndarray) -> np.ndarray:
        raise error

    with pytest.raises(type(error)):
        evaluate_demol_pair(
            [_tree("TREE-A")],
            baseline_predictor=predictor,
            candidate_predictor=_all_wood,
            qsm_func=lambda wood, *, seed: _qsm(),
        )


@pytest.mark.parametrize(
    "cohort",
    [
        [],
        [object()],
        [_tree(1)],  # type: ignore[arg-type]
        [_tree("")],
        [_tree("TREE-A"), _tree("TREE-A")],
        [_tree("TREE-A", points=np.empty((0, 3), dtype=np.float64))],
        [_tree("TREE-A", points=np.ones((3, 2), dtype=np.float64))],
        [_tree("TREE-A", points=np.ones((3, 4), dtype=np.float64))],
        [_tree("TREE-A", points=np.array([[0.0, 0.0, float("nan")]]))],
        [_tree("TREE-A", points=np.ones((3, 3), dtype=np.bool_))],
        [_tree("TREE-A", points=np.ones((3, 3), dtype=np.complex128))],
        [replace(_tree("TREE-A"), gt_dbh_cm=0.0)],
        [replace(_tree("TREE-A"), gt_height_m=float("nan"))],
        [replace(_tree("TREE-A"), gt_volume_m3=True)],
    ],
)
def test_evaluator_rejects_malformed_cohorts_and_records(cohort):
    with pytest.raises((TypeError, ValueError)):
        evaluate_demol_pair(
            cohort,
            baseline_predictor=_all_wood,
            candidate_predictor=_all_wood,
            qsm_func=lambda wood, *, seed: _qsm(),
        )


def test_evaluator_revalidates_finite_points_after_float64_cast(monkeypatch):
    tree = _tree("TREE-A")
    real_array = demol_eval.np.array

    def cast_with_nonfinite(*args, **kwargs):
        converted = real_array(*args, **kwargs)
        converted[0, 0] = float("inf")
        return converted

    monkeypatch.setattr(demol_eval.np, "array", cast_with_nonfinite)

    with pytest.raises(ValueError, match="float64"):
        evaluate_demol_pair(
            [tree],
            baseline_predictor=_all_wood,
            candidate_predictor=_all_wood,
            qsm_func=lambda wood, *, seed: _qsm(),
        )


@pytest.mark.parametrize(
    ("baseline", "candidate", "qsm_func", "qsm_seed"),
    [
        (None, _all_wood, lambda wood, *, seed: _qsm(), 0),
        (_all_wood, None, lambda wood, *, seed: _qsm(), 0),
        (_all_wood, _all_wood, None, 0),
        (_all_wood, _all_wood, lambda wood, *, seed: _qsm(), -1),
        (_all_wood, _all_wood, lambda wood, *, seed: _qsm(), True),
        (_all_wood, _all_wood, lambda wood, *, seed: _qsm(), np.int64(0)),
    ],
)
def test_evaluator_rejects_malformed_controls(baseline, candidate, qsm_func, qsm_seed):
    with pytest.raises((TypeError, ValueError)):
        evaluate_demol_pair(
            [_tree("TREE-A")],
            baseline_predictor=baseline,
            candidate_predictor=candidate,
            qsm_func=qsm_func,
            qsm_seed=qsm_seed,
        )


def test_loader_normalizes_names_orders_trees_and_samples_sorted_seed_zero_indices(
    tmp_path, monkeypatch
):
    data_root = tmp_path / "demol"
    raw = np.column_stack(
        [
            np.arange(6, dtype=np.float64),
            np.arange(6, dtype=np.float64) + 10.0,
            np.arange(6, dtype=np.float64) + 20.0,
            np.arange(6, dtype=np.float64) + 30.0,
        ]
    )
    _write_fixture(
        data_root,
        [_row("FEXC-02", dbh=20.0), _row("FEXC-01")],
        {"FEXC2.txt": raw + np.array([100.0, 0.0, 0.0, 0.0]), "FEXC1.txt": raw},
    )
    real_loadtxt = np.loadtxt
    loaded_paths = []

    def counted_loadtxt(path, *args, **kwargs):
        loaded_paths.append(path)
        return real_loadtxt(path, *args, **kwargs)

    monkeypatch.setattr(np, "loadtxt", counted_loadtxt)
    cohort = load_demol_cohort(data_root, max_points=3, sample_seed=0, formal=False)

    expected_indices = np.sort(np.random.default_rng(0).choice(6, 3, replace=False))
    assert expected_indices.tolist() == sorted(expected_indices.tolist())
    assert [tree.tree_id for tree in cohort] == ["FEXC-01", "FEXC-02"]
    assert np.array_equal(cohort[0].points[:, 0], raw[expected_indices, 0])
    assert np.array_equal(cohort[1].points[:, 0], raw[expected_indices, 0] + 100.0)
    assert np.array_equal(cohort[0].points[:, 2], raw[expected_indices, 2] - raw[:, 2].min())
    assert np.array_equal(cohort[0].points, np.ascontiguousarray(cohort[0].points))
    assert cohort[0].points.shape == (3, 3)
    assert cohort[0].points.dtype == np.float64
    assert len(loaded_paths) == 2
    assert len(set(loaded_paths)) == 2


@pytest.mark.parametrize("missing", ["root", "csv", "point_dir"])
def test_loader_rejects_missing_paths(tmp_path, missing):
    data_root = tmp_path / "demol"
    if missing != "root":
        data_root.mkdir()
    if missing == "point_dir":
        with (data_root / "Destructive_and_qsm_data_DEMOL.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()

    with pytest.raises(FileNotFoundError):
        load_demol_cohort(data_root, formal=False)


@pytest.mark.parametrize(
    "rows",
    [
        [_row("FEXC-01"), _row("FEXC-01")],
        [_row("FEXC-01"), _row("fexc-01")],
        [_row("")],
        [_row("   ")],
    ],
)
def test_loader_rejects_duplicate_empty_and_case_colliding_csv_ids(tmp_path, rows):
    data_root = tmp_path / "demol"
    _write_fixture(data_root, rows, {"FEXC1.txt": np.ones((3, 3))})

    with pytest.raises(ValueError):
        load_demol_cohort(data_root, formal=False)


def test_loader_rejects_duplicate_normalized_point_cloud_ids(tmp_path):
    data_root = tmp_path / "demol"
    _write_fixture(
        data_root,
        [_row("FEXC-01")],
        {"FEXC1.txt": np.ones((3, 3)), "FEXC-01.txt": np.ones((3, 3))},
    )

    with pytest.raises(ValueError, match="duplicate"):
        load_demol_cohort(data_root, formal=False)


def test_loader_rejects_case_colliding_normalized_point_cloud_ids(tmp_path):
    data_root = tmp_path / "demol"
    _write_fixture(
        data_root,
        [_row("FEXC-01")],
        {"FEXC1.txt": np.ones((3, 3)), "fexc-01.txt": np.ones((3, 3))},
    )

    with pytest.raises(ValueError, match="case-colliding"):
        load_demol_cohort(data_root, formal=False)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("DBH", 0.0),
        ("DBH", -1.0),
        ("DBH", float("nan")),
        ("TH_felled", float("inf")),
        ("TH_felled", "bad"),
        ("Volume_total_tree_harvested", 0.0),
        ("Volume_total_tree_harvested", -1.0),
        ("Volume_total_tree_harvested", float("nan")),
        ("Volume_total_tree_harvested", np.nextafter(0.0, 1.0)),
    ],
)
def test_loader_rejects_invalid_ground_truth(tmp_path, field, value):
    data_root = tmp_path / "demol"
    row = _row("FEXC-01")
    row[field] = value
    _write_fixture(data_root, [row], {"FEXC1.txt": np.ones((3, 3))})

    with pytest.raises((TypeError, ValueError)):
        load_demol_cohort(data_root, formal=False)


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "1 2\n",
        "1 2 nan\n",
        "not numeric\n",
    ],
)
def test_loader_rejects_empty_malformed_and_nonfinite_xyz(tmp_path, contents):
    data_root = tmp_path / "demol"
    _write_fixture(data_root, [_row("FEXC-01")], {"FEXC1.txt": contents})

    with pytest.raises((TypeError, ValueError)):
        load_demol_cohort(data_root, formal=False)


def test_loader_rejects_nonfinite_xyz_created_by_z_normalization_overflow(tmp_path):
    data_root = tmp_path / "demol"
    points = np.array([[0.0, 0.0, -1e308], [0.0, 0.0, 1e308]])
    _write_fixture(data_root, [_row("FEXC-01")], {"FEXC1.txt": points})

    with pytest.raises(ValueError, match="normalization"):
        load_demol_cohort(data_root, formal=False)


def test_loader_ignores_extra_nonnumeric_columns_after_xyz(tmp_path):
    data_root = tmp_path / "demol"
    contents = "0 0 5 ignored\n1 1 7 metadata\n"
    _write_fixture(data_root, [_row("FEXC-01")], {"FEXC1.txt": contents})

    cohort = load_demol_cohort(data_root, formal=False)

    assert np.array_equal(
        cohort[0].points,
        np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 2.0]], dtype=np.float64),
    )


def test_loader_requires_65_matches_in_formal_mode(tmp_path):
    data_root = tmp_path / "demol"
    _write_fixture(data_root, [_row("FEXC-01")], {"FEXC1.txt": np.ones((3, 3))})

    with pytest.raises(ValueError, match="65"):
        load_demol_cohort(data_root, expected_tree_ids=["FEXC-01"])


def test_formal_loader_requires_frozen_expected_ids_and_exact_match_passes(tmp_path):
    data_root = tmp_path / "demol"
    tree_ids = [f"TREE-{index:03d}" for index in range(65)]
    rows = [_row(tree_id) for tree_id in tree_ids]
    clouds = {f"{tree_id}.txt": np.ones((3, 3)) for tree_id in tree_ids}
    _write_fixture(data_root, rows, clouds)

    with pytest.raises(ValueError, match="expected_tree_ids"):
        load_demol_cohort(data_root, formal=True)

    cohort = load_demol_cohort(
        data_root,
        formal=True,
        expected_tree_ids=tree_ids,
    )
    assert [tree.tree_id for tree in cohort] == tree_ids


def test_loader_requires_exact_expected_id_list_and_never_subsets(tmp_path):
    data_root = tmp_path / "demol"
    _write_fixture(
        data_root,
        [_row("FEXC-02"), _row("FEXC-01")],
        {"FEXC2.txt": np.ones((3, 3)), "FEXC1.txt": np.ones((3, 3))},
    )

    cohort = load_demol_cohort(
        data_root,
        formal=False,
        expected_tree_ids=["FEXC-01", "FEXC-02"],
    )
    assert [tree.tree_id for tree in cohort] == ["FEXC-01", "FEXC-02"]

    for expected in (
        [],
        ["FEXC-02", "FEXC-01"],
        ["FEXC-01", "FEXC-01"],
        [""],
        [1],
        ("FEXC-01", "FEXC-02"),
        ["FEXC-01"],
        ["FEXC-01", "OTHER"],
    ):
        with pytest.raises((TypeError, ValueError)):
            load_demol_cohort(
                data_root,
                formal=False,
                expected_tree_ids=expected,
            )


@pytest.mark.parametrize(
    ("max_points", "sample_seed", "formal"),
    [
        (0, 0, False),
        (-1, 0, False),
        (True, 0, False),
        (3.0, 0, False),
        (3, -1, False),
        (3, True, False),
        (3, np.int64(0), False),
        (3, 0, 0),
    ],
)
def test_loader_rejects_malformed_controls(tmp_path, max_points, sample_seed, formal):
    data_root = tmp_path / "demol"
    _write_fixture(data_root, [_row("FEXC-01")], {"FEXC1.txt": np.ones((3, 3))})

    with pytest.raises((TypeError, ValueError)):
        load_demol_cohort(
            data_root,
            max_points=max_points,
            sample_seed=sample_seed,
            formal=formal,
        )


def test_loader_rejects_missing_columns_empty_csv_and_zero_matches(tmp_path):
    missing_columns = tmp_path / "missing-columns"
    point_dir = missing_columns / "pointclouds" / "pointclouds_clean"
    point_dir.mkdir(parents=True)
    (missing_columns / "Destructive_and_qsm_data_DEMOL.csv").write_text(
        "tree_name,DBH\nFEXC-01,10\n", encoding="utf-8"
    )
    with pytest.raises(ValueError):
        load_demol_cohort(missing_columns, formal=False)

    empty_csv = tmp_path / "empty-csv"
    _write_fixture(empty_csv, [], {"FEXC1.txt": np.ones((3, 3))})
    with pytest.raises(ValueError):
        load_demol_cohort(empty_csv, formal=False)

    zero_matches = tmp_path / "zero-matches"
    _write_fixture(zero_matches, [_row("FEXC-01")], {"FSYL1.txt": np.ones((3, 3))})
    with pytest.raises(ValueError):
        load_demol_cohort(zero_matches, formal=False)
