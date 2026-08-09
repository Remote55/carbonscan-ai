"""Integration tests for the independent PointNet evidence evaluation."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from pipeline.demol_eval import DemolTree
from pipeline.provenance import sha256_file
from training.evidence_protocol import load_protocol

PROTOCOL = (
    Path(__file__).resolve().parents[3] / "docs/evidence/pointnet_independent_eval/protocol.json"
)


def _points(tree_number: float, count: int) -> np.ndarray:
    return np.column_stack(
        [
            np.full(count, tree_number, dtype=np.float64),
            np.arange(count, dtype=np.float64),
            np.arange(count, dtype=np.float64),
        ]
    )


def _identity():
    from pipeline.independent_eval import ValidatedEvidenceIdentity

    return ValidatedEvidenceIdentity(
        schema_version="1",
        experiment_id="pointnet-independent-eval-2026-07-16",
        protocol_sha256="a" * 64,
        freeze_manifest_sha256="b" * 64,
        external_manifest_sha256="c" * 64,
        checkpoint_sha256="d" * 64,
        evaluation_git_commit="e" * 40,
    )


def _toy_cohorts():
    external = [
        ("external-large", _points(101.0, 5), np.array([0, 0, 0, 1, 1], dtype=np.uint8)),
        ("external-small", _points(100.0, 2), np.array([0, 1], dtype=np.uint8)),
    ]
    demol = [
        DemolTree("DEMOL-B", _points(2.0, 4), 20.0, 10.0, 4.0),
        DemolTree("DEMOL-A", _points(1.0, 4), 10.0, 5.0, 2.0),
    ]
    return external, demol


def _baseline(points: np.ndarray) -> np.ndarray:
    if len(points) == 2:
        return np.array([0, 1], dtype=np.int8)
    if len(points) == 5:
        return np.ones(5, dtype=np.int8)
    return np.array([0, 0, 0, 1], dtype=np.int8)


def _candidate(points: np.ndarray) -> np.ndarray:
    if len(points) == 2:
        return np.array([0, 1], dtype=np.int8)
    if len(points) == 5:
        return np.array([0, 0, 0, 1, 1], dtype=np.int8)
    return np.array([0, 0, 1, 1], dtype=np.int8)


_MEASUREMENTS = {
    (1.0, 3): (11.125, 4.75, 2.25),
    (1.0, 2): (9.5, 5.5, 1.75),
    (2.0, 3): (18.25, 11.125, 3.5),
    (2.0, 2): (20.75, 9.875, 4.5),
}


def _fake_qsm(wood: np.ndarray, *, seed: int):
    assert seed == 0
    dbh, height, volume = _MEASUREMENTS[(float(wood[0, 0]), len(wood))]
    return SimpleNamespace(dbh_cm=dbh, height_m=height, total_volume_m3=volume)


def _toy_bundle(*, baseline=_baseline, candidate=_candidate, qsm_func=_fake_qsm):
    from pipeline.independent_eval import _compose_evaluation_from_validated_inputs

    external, demol = _toy_cohorts()
    return _compose_evaluation_from_validated_inputs(
        identity=_identity(),
        protocol=load_protocol(PROTOCOL),
        external_cohort=external,
        demol_cohort=demol,
        baseline_predictor=baseline,
        candidate_predictor=candidate,
        qsm_func=qsm_func,
    )


def test_two_tree_cpu_composition_writes_full_precision_artifacts(tmp_path: Path):
    from pipeline.independent_eval import (
        ValidatedEvidenceIdentity,
        _compose_evaluation_from_validated_inputs,
        _publish_evidence_artifacts,
    )

    identity = ValidatedEvidenceIdentity(
        schema_version="1",
        experiment_id="pointnet-independent-eval-2026-07-16",
        protocol_sha256="a" * 64,
        freeze_manifest_sha256="b" * 64,
        external_manifest_sha256="c" * 64,
        checkpoint_sha256="d" * 64,
        evaluation_git_commit="e" * 40,
    )
    external = [
        ("external-large", _points(101.0, 5), np.array([0, 0, 0, 1, 1], dtype=np.uint8)),
        ("external-small", _points(100.0, 2), np.array([0, 1], dtype=np.uint8)),
    ]
    demol = [
        DemolTree("DEMOL-B", _points(2.0, 4), 20.0, 10.0, 4.0),
        DemolTree("DEMOL-A", _points(1.0, 4), 10.0, 5.0, 2.0),
    ]

    def baseline(points: np.ndarray) -> np.ndarray:
        if len(points) == 2:
            return np.array([0, 1], dtype=np.int8)
        if len(points) == 5:
            return np.ones(5, dtype=np.int8)
        return np.array([0, 0, 0, 1], dtype=np.int8)

    def candidate(points: np.ndarray) -> np.ndarray:
        if len(points) == 2:
            return np.array([0, 1], dtype=np.int8)
        if len(points) == 5:
            return np.array([0, 0, 0, 1, 1], dtype=np.int8)
        return np.array([0, 0, 1, 1], dtype=np.int8)

    measurements = {
        (1.0, 3): (11.125, 4.75, 2.25),
        (1.0, 2): (9.5, 5.5, 1.75),
        (2.0, 3): (18.25, 11.125, 3.5),
        (2.0, 2): (20.75, 9.875, 4.5),
    }

    def fake_qsm(wood: np.ndarray, *, seed: int):
        assert seed == 0
        dbh, height, volume = measurements[(float(wood[0, 0]), len(wood))]
        return SimpleNamespace(dbh_cm=dbh, height_m=height, total_volume_m3=volume)

    bundle = _compose_evaluation_from_validated_inputs(
        identity=identity,
        protocol=load_protocol(PROTOCOL),
        external_cohort=external,
        demol_cohort=demol,
        baseline_predictor=baseline,
        candidate_predictor=candidate,
        qsm_func=fake_qsm,
    )
    evidence_dir = tmp_path / "evidence"
    result = _publish_evidence_artifacts(bundle, evidence_dir)

    assert result["baseline"]["external_segmentation"]["macro"]["wood_iou"] == 0.5
    assert result["baseline"]["external_segmentation"]["pooled"]["wood_iou"] == 0.25
    assert result["candidate"]["downstream"]["dbh_mae_cm"] == 0.625
    assert result["baseline"]["downstream"]["height_mae_m"] == 0.6875
    assert result["candidate"]["downstream"]["volume_mape_pct"] == 12.5
    assert result["formal_gate"]["baseline"]["wood_iou"] == 0.5
    assert result["checkpoint_sha256"] == "d" * 64
    assert result["verdict"] == {
        "verdict": "POINT_ESTIMATE_PASS_ONLY",
        "promote": False,
    }

    assert sorted(path.name for path in evidence_dir.iterdir()) == [
        "REPORT.md",
        "downstream_per_tree.csv",
        "result.json",
        "segmentation_per_tree.csv",
    ]
    with (evidence_dir / "segmentation_per_tree.csv").open(encoding="utf-8", newline="") as handle:
        segmentation_rows = list(csv.DictReader(handle))
    with (evidence_dir / "downstream_per_tree.csv").open(encoding="utf-8", newline="") as handle:
        downstream_rows = list(csv.DictReader(handle))
    assert [row["tree_id"] for row in segmentation_rows] == [
        "external-large",
        "external-small",
    ]
    assert [row["tree_id"] for row in downstream_rows] == ["DEMOL-A", "DEMOL-B"]

    written = json.loads((evidence_dir / "result.json").read_text(encoding="utf-8"))
    assert written == result
    report = (evidence_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "POINT_ESTIMATE_PASS_ONLY" in report
    assert "0.6875" in report
    assert "95% CI" in report
    for metric_name, interval in result["confidence_intervals"].items():
        assert metric_name in report
        assert repr(interval["estimate"]) in report
        assert repr(interval["lower"]) in report
        assert repr(interval["upper"]) in report
    assert "Cohort A contains only 10 individual non-Thai TLS trees" in report
    assert "does not automatically change the production default" in report


def test_evaluate_cli_accepts_only_eight_paths_and_prints_exact_json(
    tmp_path: Path, monkeypatch, capsys
):
    import training

    evidence_training_stub = ModuleType("training.evidence_training")
    evidence_training_stub.build_freeze_manifest = lambda *args, **kwargs: None
    evidence_training_stub.run_training_matrix = lambda *args, **kwargs: None
    evidence_training_stub.capture_training_environment = dict
    evidence_training_stub._validate_path_privacy = lambda *args, **kwargs: None
    evidence_training_stub._validate_wan_manifest = lambda manifest: manifest
    train_woodleaf_stub = ModuleType("training.train_woodleaf")
    train_woodleaf_stub.train = lambda args: None
    monkeypatch.setitem(sys.modules, "training.evidence_training", evidence_training_stub)
    monkeypatch.setitem(sys.modules, "training.train_woodleaf", train_woodleaf_stub)
    monkeypatch.setattr(training, "evidence_training", evidence_training_stub, raising=False)
    monkeypatch.setattr(training, "train_woodleaf", train_woodleaf_stub, raising=False)
    monkeypatch.delitem(sys.modules, "scripts.pointnet_evidence", raising=False)
    from scripts import pointnet_evidence

    captured = {}
    result = {
        "checkpoint_sha256": "d" * 64,
        "baseline": {
            "external_segmentation": {"macro": {"wood_iou": 1 / 3}},
            "downstream": {
                "dbh_mae_cm": 1.0000000000000002,
                "height_mae_m": 0.5000000000000001,
                "volume_mape_pct": 18.7650916186,
                "measurable_trees": 65,
            },
        },
        "candidate": {
            "external_segmentation": {"macro": {"wood_iou": 2 / 3}},
            "downstream": {
                "dbh_mae_cm": 0.9999999999999999,
                "height_mae_m": 0.4999999999999999,
                "volume_mape_pct": 18.7650916185,
                "measurable_trees": 65,
            },
        },
        "verdict": {"verdict": "PROMOTE_POINTNET", "promote": True},
    }

    def fake_run(**kwargs):
        captured.update(kwargs)
        return result

    monkeypatch.setattr(
        pointnet_evidence,
        "run_independent_evaluation",
        fake_run,
        raising=False,
    )
    values = {
        name: str(tmp_path / name)
        for name in (
            "protocol",
            "freeze_manifest",
            "checkpoint",
            "external_root",
            "external_manifest",
            "demol_root",
            "evidence_dir",
            "repo_root",
        )
    }
    argv = ["evaluate"]
    for name, value in values.items():
        argv.extend([f"--{name.replace('_', '-')}", value])

    assert pointnet_evidence.main(argv) == 0

    line = capsys.readouterr().out.strip()
    line.encode("ascii")
    summary = json.loads(line)
    assert summary == {
        "baseline_dbh_mae_cm": 1.0000000000000002,
        "baseline_height_mae_m": 0.5000000000000001,
        "baseline_measurable_trees": 65,
        "baseline_volume_mape_pct": 18.7650916186,
        "baseline_wood_iou": 1 / 3,
        "candidate_dbh_mae_cm": 0.9999999999999999,
        "candidate_height_mae_m": 0.4999999999999999,
        "candidate_measurable_trees": 65,
        "candidate_volume_mape_pct": 18.7650916185,
        "candidate_wood_iou": 2 / 3,
        "checkpoint_sha256": "d" * 64,
        "command": "evaluate",
        "promote": True,
        "status": "ok",
        "verdict": "PROMOTE_POINTNET",
    }
    assert captured == values


def test_public_runner_has_exact_eight_path_interface_and_cli_has_no_injection_options():
    from pipeline.independent_eval import run_independent_evaluation
    from scripts import pointnet_evidence

    assert list(inspect.signature(run_independent_evaluation).parameters) == [
        "protocol",
        "freeze_manifest",
        "checkpoint",
        "external_root",
        "external_manifest",
        "demol_root",
        "evidence_dir",
        "repo_root",
    ]
    parsed = pointnet_evidence.build_arg_parser().parse_args(
        [
            "evaluate",
            "--protocol",
            "protocol.json",
            "--freeze-manifest",
            "freeze.json",
            "--checkpoint",
            "winner.pt",
            "--external-root",
            "external",
            "--external-manifest",
            "external.json",
            "--demol-root",
            "demol",
            "--evidence-dir",
            "evidence",
            "--repo-root",
            ".",
        ]
    )
    assert set(vars(parsed)) == {
        "command",
        "handler",
        "protocol",
        "freeze_manifest",
        "checkpoint",
        "external_root",
        "external_manifest",
        "demol_root",
        "evidence_dir",
        "repo_root",
    }


def test_external_predictors_share_identical_read_only_objects():
    baseline_seen: list[np.ndarray] = []
    candidate_seen: list[np.ndarray] = []

    def baseline(points: np.ndarray) -> np.ndarray:
        baseline_seen.append(points)
        return _baseline(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        candidate_seen.append(points)
        return _candidate(points)

    _toy_bundle(baseline=baseline, candidate=candidate)

    external_pairs = [
        (left, right)
        for left, right in zip(baseline_seen, candidate_seen, strict=True)
        if len(left) in {2, 5}
    ]
    assert len(external_pairs) == 2
    for baseline_points, candidate_points in external_pairs:
        assert baseline_points is candidate_points
        assert baseline_points.flags.c_contiguous
        assert not baseline_points.flags.writeable
        assert baseline_points.tobytes() == candidate_points.tobytes()


def test_composition_rejects_forged_validated_identity_record():
    from pipeline.independent_eval import (
        IndependentEvaluationError,
        _compose_evaluation_from_validated_inputs,
    )

    external, demol = _toy_cohorts()
    with pytest.raises(IndependentEvaluationError, match="identity"):
        _compose_evaluation_from_validated_inputs(
            identity=replace(_identity(), checkpoint_sha256="not-a-sha256"),
            protocol=load_protocol(PROTOCOL),
            external_cohort=external,
            demol_cohort=demol,
            baseline_predictor=_baseline,
            candidate_predictor=_candidate,
            qsm_func=_fake_qsm,
        )


def test_external_force_mutation_is_whole_run_invalid_evidence():
    from pipeline.independent_eval import IndependentEvaluationError

    candidate_calls = 0

    def mutating_baseline(points: np.ndarray) -> np.ndarray:
        if len(points) in {2, 5}:
            points.flags.writeable = True
            points[0, 0] = -999.0
        return _baseline(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        nonlocal candidate_calls
        candidate_calls += 1
        return _candidate(points)

    with pytest.raises(IndependentEvaluationError, match="paired input"):
        _toy_bundle(baseline=mutating_baseline, candidate=candidate)
    assert candidate_calls == 0


def test_external_label_coercion_mutation_aborts_before_candidate():
    from pipeline.independent_eval import IndependentEvaluationError

    candidate_calls = 0

    class MutatingLabels:
        def __init__(self, points: np.ndarray, labels: np.ndarray):
            self.points = points
            self.labels = labels

        def __array__(self, dtype=None, copy=None):
            self.points.flags.writeable = True
            self.points[0, 0] = -999.0
            return np.asarray(self.labels, dtype=dtype)

    def baseline(points: np.ndarray):
        labels = _baseline(points)
        if len(points) in {2, 5}:
            return MutatingLabels(points, labels)
        return labels

    def candidate(points: np.ndarray) -> np.ndarray:
        nonlocal candidate_calls
        candidate_calls += 1
        return _candidate(points)

    with pytest.raises(IndependentEvaluationError, match="paired input"):
        _toy_bundle(baseline=baseline, candidate=candidate)
    assert candidate_calls == 0


@pytest.mark.parametrize(
    "invalid_labels",
    [
        np.array([], dtype=np.int8),
        np.array([[0, 1]], dtype=np.int8),
        np.array([0.0, 1.0]),
        np.array([0, 2], dtype=np.int8),
    ],
)
def test_external_invalid_labels_fail_closed(invalid_labels: np.ndarray):
    from pipeline.independent_eval import IndependentEvaluationError

    def candidate(points: np.ndarray) -> np.ndarray:
        if len(points) == 2:
            return invalid_labels
        return _candidate(points)

    with pytest.raises(IndependentEvaluationError, match="labels"):
        _toy_bundle(candidate=candidate)


def test_demol_zero_measurable_candidate_is_invalid_evidence():
    from pipeline.independent_eval import IndependentEvaluationError

    def candidate(points: np.ndarray) -> np.ndarray:
        if len(points) == 4:
            return np.ones(len(points), dtype=np.int8)
        return _candidate(points)

    with pytest.raises(IndependentEvaluationError, match="zero measurable"):
        _toy_bundle(candidate=candidate)


def test_demol_requires_at_least_one_identically_paired_measurable_row():
    from pipeline.independent_eval import IndependentEvaluationError

    def baseline(points: np.ndarray) -> np.ndarray:
        if len(points) == 4 and points[0, 0] == 1.0:
            return np.ones(len(points), dtype=np.int8)
        return _baseline(points)

    def candidate(points: np.ndarray) -> np.ndarray:
        if len(points) == 4 and points[0, 0] == 2.0:
            return np.ones(len(points), dtype=np.int8)
        return _candidate(points)

    with pytest.raises(IndependentEvaluationError, match="paired downstream"):
        _toy_bundle(baseline=baseline, candidate=candidate)


def test_artifact_validation_rejects_nonfinite_numbers_without_publication(tmp_path: Path):
    from pipeline.independent_eval import IndependentEvaluationError, _publish_evidence_artifacts

    bundle = _toy_bundle()
    bundle.result["baseline"]["downstream"]["dbh_mae_cm"] = float("nan")
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="finite"):
        _publish_evidence_artifacts(bundle, evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []


def test_artifact_validation_rejects_boolean_numeric_field(tmp_path: Path):
    from pipeline.independent_eval import IndependentEvaluationError, _publish_evidence_artifacts

    bundle = _toy_bundle()
    bundle.result["baseline"]["downstream"]["dbh_mae_cm"] = True
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="boolean"):
        _publish_evidence_artifacts(bundle, evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []


def test_artifact_preflight_never_overwrites_existing_final(tmp_path: Path):
    from pipeline.independent_eval import IndependentEvaluationError, _publish_evidence_artifacts

    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    existing = evidence_dir / "result.json"
    existing.write_bytes(b"belongs to user")

    with pytest.raises(IndependentEvaluationError, match="already exists"):
        _publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert existing.read_bytes() == b"belongs to user"
    assert [path.name for path in evidence_dir.iterdir()] == ["result.json"]


def test_artifact_staging_validation_failure_leaves_no_finals_or_temp(tmp_path: Path, monkeypatch):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    monkeypatch.setattr(
        independent_eval,
        "_validate_staged_artifacts",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("injected validation failure")),
    )
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="injected validation failure"):
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []
    assert not list(tmp_path.glob(".evidence.*"))


def test_staged_csv_content_mismatch_rolls_back_before_publication(tmp_path: Path, monkeypatch):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    real_write_csv = independent_eval._write_csv

    def corrupt_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
        real_write_csv(path, fields, rows)
        if path.name == "segmentation_per_tree.csv":
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace(",5,", ",6,", 1), encoding="utf-8", newline="\n")

    monkeypatch.setattr(independent_eval, "_write_csv", corrupt_csv)
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="segmentation content"):
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []
    assert not list(tmp_path.glob(".evidence.*"))


def test_artifact_mid_publish_link_failure_rolls_back_every_created_final(
    tmp_path: Path, monkeypatch
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    real_link = independent_eval._link_staged_file
    calls = 0

    def injected_link(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected link failure")
        real_link(source, destination)

    monkeypatch.setattr(independent_eval, "_link_staged_file", injected_link)
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="injected link failure"):
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []
    assert not list(tmp_path.glob(".evidence.*"))


def test_artifact_post_link_failure_rolls_back_successfully_published_final(
    tmp_path: Path, monkeypatch
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    real_link = independent_eval._link_staged_file

    def link_then_fail(source: Path, destination: Path) -> None:
        real_link(source, destination)
        raise OSError("injected post-link failure")

    monkeypatch.setattr(independent_eval, "_link_staged_file", link_then_fail)
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="injected post-link failure"):
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []
    assert not list(tmp_path.glob(".evidence.*"))


def test_staged_source_unlink_failure_rolls_back_its_owned_final(tmp_path: Path, monkeypatch):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    real_unlink = Path.unlink

    def fail_staged_unlink(path: Path, *args, **kwargs) -> None:
        if path.name == "segmentation_per_tree.csv" and path.parent.name.startswith(".evidence."):
            raise OSError("injected staged source unlink failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_staged_unlink)
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError, match="injected staged source unlink failure"):
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []
    assert not list(tmp_path.glob(".evidence.*"))


def test_artifact_race_preserves_concurrent_final_and_rolls_back_owned_files(
    tmp_path: Path, monkeypatch
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    real_link = independent_eval._link_staged_file
    concurrent_bytes = b"belongs to concurrent publisher"

    def concurrent_publish(source: Path, destination: Path) -> None:
        destination.write_bytes(concurrent_bytes)
        try:
            real_link(source, destination)
        except FileExistsError as exc:
            raise FileExistsError(17, "File exists", destination) from exc

    monkeypatch.setattr(independent_eval, "_link_staged_file", concurrent_publish)
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(IndependentEvaluationError) as caught:
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert str(caught.value) == "final evidence artifact already exists"
    assert isinstance(caught.value.__cause__, FileExistsError)
    concurrent = evidence_dir / "segmentation_per_tree.csv"
    assert concurrent.read_bytes() == concurrent_bytes
    assert [path.name for path in evidence_dir.iterdir()] == [concurrent.name]
    assert not list(tmp_path.glob(".evidence.*"))


@pytest.mark.parametrize(
    ("artifact", "corruption"),
    [
        ("result.json", "formatting"),
        ("result.json", "ordering"),
        ("result.json", "newline"),
        ("REPORT.md", "content"),
    ],
)
def test_staged_json_and_report_corruption_prevent_publication(
    tmp_path: Path, monkeypatch, artifact: str, corruption: str
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    if artifact == "result.json":
        real_write = independent_eval._write_result_json

        def corrupt(path: Path, result: dict) -> None:
            real_write(path, result)
            if corruption == "formatting":
                path.write_text(
                    json.dumps(result, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
            elif corruption == "ordering":
                path.write_text(
                    json.dumps(
                        result,
                        sort_keys=False,
                        indent=2,
                        ensure_ascii=True,
                        allow_nan=False,
                    )
                    + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
            else:
                path.write_bytes(path.read_bytes().rstrip(b"\n"))

        monkeypatch.setattr(independent_eval, "_write_result_json", corrupt)
        expected_error = "result content mismatch"
    else:
        real_write = independent_eval._write_report

        def corrupt(path: Path, result: dict) -> None:
            real_write(path, result)
            path.write_text("corrupt report\n", encoding="utf-8", newline="\n")

        monkeypatch.setattr(independent_eval, "_write_report", corrupt)
        expected_error = "report content mismatch"

    evidence_dir = tmp_path / "evidence"
    with pytest.raises(IndependentEvaluationError, match=expected_error):
        independent_eval._publish_evidence_artifacts(_toy_bundle(), evidence_dir)
    assert not evidence_dir.exists() or list(evidence_dir.iterdir()) == []
    assert not list(tmp_path.glob(".evidence.*"))


def test_default_pipeline_file_and_tlsep_default_are_unchanged():
    """Tripwire: the measurement path must not drift while PointNet is unpromoted.

    Update the pin only after confirming the change leaves the default backend
    and the measurement algorithms alone, and record why here.

    History:
    - 8360851: baseline at the time of the independent evaluation.
    - c4a78ab: pipeline 0.4.0 reports excluded segments instead of dropping them
      silently. It adds ExcludedSegment/PipelineDiagnostics, the detected/
      measured/excluded counts and pipeline_result_to_dict. No QSM, allometric
      or DBH/height computation was touched, and tlsep stays the default.
    - 9e66b42: the exported segmented PLY is now assembled from the per-tree
      labels the measurements were taken from, instead of a second
      WoodLeafSegmenter pass over the whole non-ground cloud. Every changed line
      sits inside the `segmented_ply_out` branch: the added GROUND_CLASS
      constant, the plot_classes array, one write-back inside the tree loop, and
      the export call. The removed pass fed nothing but that file. tlsep stays
      the default, and the measurement path - segment, QSM, allometric,
      exclusions, counts - is byte-identical, which test_core_demo's output hash
      independently confirms by still passing.
    - 1aeaafa / 798c7c8 / 59c0c2a: the measurement path DID change here, and
      unlike every entry above this one the numbers moved. Three things:
      allometric.py gates species equations whose coefficients nobody has
      checked, qsm.py replaces one unsourced form factor with two measured ones
      and reports crown volume instead of claiming zero, and both qsm.py and
      main.py stop reporting a DBH whose circle fit failed. Details are in the
      commits; what matters here is that this pin is not evidence of stability
      this time, it is a record of a deliberate break.

      This entry also widens the pin. Until now it covered main.py alone - the
      orchestrator - while DBH, volume and biomass are decided in qsm.py and
      allometric.py, which could be rewritten without this test noticing. A
      tripwire on the wrong file is worse than none, because it reports having
      checked.
    - 6dfecc1 / da62fc8: the carbon figure now carries bounds from the plausible
      wood density range, which the pipeline never measures. Additive - the
      point estimate is untouched, which the judge-demo total confirms by not
      moving. qsm.py is unchanged from the entry above.
    - 3ff3499: ground_classification takes the k-th lowest point in a cell
      rather than a percentile of everything in it. A percentile is only the
      ground when the cell is mostly ground; under a stem, cells that were
      97-99% tree returned ground candidates up to 10 m in the air, the
      interpolated surface rose about a metre beneath every trunk, and the
      1.3 m slice landed in the branches. Two of four real trees then measured
      2x and 5x their taped DBH through the plot path while measuring correctly
      in isolation. This moved the judge-demo total by 76 kg CO2e.

      And the pin did not notice, because ground_classification.py was not in
      it. The same lesson as the entry above, one level out: the measurement is
      the whole chain from ground to carbon, not the three files where the
      arithmetic is most visible. All eight stages are pinned now.
    """
    from pipeline import (
        allometric,
        canopy_height_model,
        ground_classification,
        height_normalization,
        main,
        qsm,
        tree_segmentation,
        wood_leaf_separation,
    )

    pipeline_main = main
    expected = {
        ground_classification: (
            "3ff349981e8cec233602605d4e6d0d34c24ac8cf47d805bc23c6cd1a072b4247"
        ),
        height_normalization: (
            "c6d022d1259ff4f73a5f7306954bda34d06d1aa28bd446dcea9f7ffb50561e0d"
        ),
        canopy_height_model: (
            "914a89e0be9490d37dfc7d3620f4421c4b60a33fbc6c947e505cff7ba24c414f"
        ),
        tree_segmentation: (
            "d7da9f066ff7f6309bbbd307a04ae4ebde6cdbeebdd77ec24dc61cef700e5939"
        ),
        wood_leaf_separation: (
            "ee9cf7e55c930094af4b37584518a4a1de338201e5cb3591c8e9281e82ee0431"
        ),
        qsm: "798c7c8a67e90dc404e2626635a91f5f014b89f70aa118f7748ea78b93611a99",
        allometric: "da62fc88e2a79c01bf9a7c8c0c807f6901dbddccff5e83a76e8f603f5d9bf1c3",
        main: "6dfecc1aa35d8d2ae6b51de7e611c5945e5ae7ac78905c0932974ccfddb4eeed",
    }
    for module, pinned in expected.items():
        body = Path(module.__file__).resolve().read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(body).hexdigest()
        assert actual == pinned, (
            f"{Path(module.__file__).name} changed: {actual}\n"
            "If the measurement is meant to move, say so in the History block above."
        )
    assert (
        inspect.signature(pipeline_main.process_points).parameters["wood_leaf_backend"].default
        == "tlsep"
    )


def _guard_fixture(tmp_path: Path):
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_bytes(PROTOCOL.read_bytes())
    checkpoint = tmp_path / "winner.pt"
    checkpoint.write_bytes(b"strict checkpoint fixture")
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_bytes(b"strict freeze fixture")
    external_path = tmp_path / "external.json"
    external_path.write_bytes(b"strict external fixture")
    external_root = tmp_path / "external"
    demol_root = tmp_path / "demol"
    external_root.mkdir()
    demol_root.mkdir()
    protocol = load_protocol(protocol_path)
    freeze = {
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": sha256_file(protocol_path),
        "training_configuration": protocol["training"],
        "training_git_commit": "f" * 40,
        "training_command": ["python", "-m", "scripts.pointnet_evidence", "train"],
        "winner": {"checkpoint_sha256": sha256_file(checkpoint)},
    }
    external_manifest = {
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": sha256_file(protocol_path),
        "freeze_manifest_sha256": sha256_file(freeze_path),
        "checkpoint_sha256": sha256_file(checkpoint),
        "tree_ids": [f"external-{index:02d}" for index in range(10)],
    }
    paths = {
        "protocol": str(protocol_path),
        "freeze_manifest": str(freeze_path),
        "checkpoint": str(checkpoint),
        "external_root": str(external_root),
        "external_manifest": str(external_path),
        "demol_root": str(demol_root),
        "evidence_dir": str(tmp_path / "evidence"),
        "repo_root": str(tmp_path),
    }
    return paths, protocol, freeze, external_manifest


@pytest.mark.parametrize("failure_stage", ["protocol", "freeze", "external", "git"])
def test_schema_and_git_guards_precede_model_data_and_output(
    tmp_path: Path, monkeypatch, failure_stage: str
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    paths, protocol, freeze, external = _guard_fixture(tmp_path)
    expensive_calls: list[str] = []

    def fail(label: str):
        raise ValueError(f"injected {label} guard failure")

    monkeypatch.setattr(
        independent_eval,
        "load_protocol",
        (lambda path: fail("protocol")) if failure_stage == "protocol" else lambda path: protocol,
    )
    monkeypatch.setattr(
        independent_eval,
        "_load_freeze",
        (lambda path: fail("freeze")) if failure_stage == "freeze" else lambda path: freeze,
    )
    monkeypatch.setattr(
        independent_eval,
        "_load_external_manifest",
        (lambda path: fail("external")) if failure_stage == "external" else lambda path: external,
    )
    monkeypatch.setattr(
        independent_eval,
        "_validate_git_evidence_state",
        (lambda **kwargs: fail("git")) if failure_stage == "git" else lambda **kwargs: "e" * 40,
    )
    monkeypatch.setattr(
        independent_eval,
        "WoodLeafSegmenter",
        lambda *args, **kwargs: expensive_calls.append("model"),
    )
    monkeypatch.setattr(
        independent_eval,
        "load_external_trees",
        lambda *args, **kwargs: expensive_calls.append("external_data"),
    )
    monkeypatch.setattr(
        independent_eval,
        "load_demol_cohort",
        lambda *args, **kwargs: expensive_calls.append("demol_data"),
    )

    with pytest.raises(IndependentEvaluationError, match=failure_stage):
        independent_eval.run_independent_evaluation(**paths)
    assert expensive_calls == []
    assert not Path(paths["evidence_dir"]).exists()


@pytest.mark.parametrize(
    "mismatch",
    [
        "freeze_protocol",
        "external_protocol",
        "external_freeze",
        "freeze_checkpoint",
        "external_checkpoint",
        "experiment",
        "training_configuration",
    ],
)
def test_every_identity_mismatch_precedes_expensive_operations(
    tmp_path: Path, monkeypatch, mismatch: str
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    paths, protocol, freeze, external = _guard_fixture(tmp_path)
    if mismatch == "freeze_protocol":
        freeze["protocol_sha256"] = "0" * 64
    elif mismatch == "external_protocol":
        external["protocol_sha256"] = "0" * 64
    elif mismatch == "external_freeze":
        external["freeze_manifest_sha256"] = "0" * 64
    elif mismatch == "freeze_checkpoint":
        freeze["winner"]["checkpoint_sha256"] = "0" * 64
    elif mismatch == "external_checkpoint":
        external["checkpoint_sha256"] = "0" * 64
    elif mismatch == "experiment":
        external["experiment_id"] = "wrong-experiment"
    else:
        freeze["training_configuration"] = {}

    expensive_calls: list[str] = []
    monkeypatch.setattr(independent_eval, "load_protocol", lambda path: protocol)
    monkeypatch.setattr(independent_eval, "_load_freeze", lambda path: freeze)
    monkeypatch.setattr(independent_eval, "_load_external_manifest", lambda path: external)
    monkeypatch.setattr(
        independent_eval,
        "_validate_git_evidence_state",
        lambda **kwargs: expensive_calls.append("git"),
    )
    monkeypatch.setattr(
        independent_eval,
        "WoodLeafSegmenter",
        lambda *args, **kwargs: expensive_calls.append("model"),
    )

    with pytest.raises(IndependentEvaluationError):
        independent_eval.run_independent_evaluation(**paths)
    assert expensive_calls == []
    assert not Path(paths["evidence_dir"]).exists()


def test_production_runner_uses_one_strict_model_and_every_protocol_parameter(
    tmp_path: Path, monkeypatch
):
    from pipeline import independent_eval
    from pipeline.pointnet_tiled import TiledPrediction

    paths, protocol, freeze, external_manifest = _guard_fixture(tmp_path)
    model_instances = []
    baseline_calls = []
    tiled_calls = []
    logits_calls = []
    loader_calls = {}

    class FakeSegmenter:
        def __init__(self, model_path, *, backend):
            assert model_path == str(Path(paths["checkpoint"]).resolve())
            assert backend == "pointnet"
            model_instances.append(self)

        def pointnet_logits(self, normalized_points: np.ndarray) -> np.ndarray:
            logits_calls.append(normalized_points.copy())
            logits = np.zeros((len(normalized_points), 2), dtype=np.float64)
            logits[: len(normalized_points) // 2, 0] = 1.0
            logits[len(normalized_points) // 2 :, 1] = 1.0
            return logits

        def segment(self, points):
            pytest.fail("strict evidence must never call segment/fallback")

    def fake_baseline(points: np.ndarray, **kwargs) -> np.ndarray:
        baseline_calls.append((points, kwargs))
        return np.array([0, 0, 1, 1], dtype=np.int8)

    def fake_tiled(points: np.ndarray, model_logits, **kwargs):
        tiled_calls.append((points, model_logits, kwargs))
        model_logits(np.zeros((protocol["pointnet_inference"]["model_points"], 3)))
        labels = np.array([0, 0, 1, 1], dtype=np.int8)
        logits = np.column_stack([labels == 0, labels == 1]).astype(np.float64)
        return TiledPrediction(labels, logits, np.ones(len(points), dtype=np.int64))

    external_trees = [
        (tree_id, _points(100.0 + index, 4), np.array([0, 0, 1, 1], dtype=np.uint8))
        for index, tree_id in enumerate(external_manifest["tree_ids"])
    ]
    demol_trees = [
        DemolTree(tree_id, _points(float(index + 1), 4), 10.0, 5.0, 2.0)
        for index, tree_id in enumerate(protocol["demol"]["tree_ids"])
    ]

    def fake_external_loader(root, manifest):
        loader_calls["external"] = (root, manifest)
        return external_trees

    def fake_demol_loader(root, **kwargs):
        loader_calls["demol"] = (root, kwargs)
        return demol_trees

    monkeypatch.setattr(independent_eval, "load_protocol", lambda path: protocol)
    monkeypatch.setattr(independent_eval, "_load_freeze", lambda path: freeze)
    monkeypatch.setattr(independent_eval, "_load_external_manifest", lambda path: external_manifest)
    monkeypatch.setattr(independent_eval, "_validate_git_evidence_state", lambda **kwargs: "e" * 40)
    monkeypatch.setattr(independent_eval, "WoodLeafSegmenter", FakeSegmenter)
    monkeypatch.setattr(independent_eval, "segment_wood_leaf", fake_baseline)
    monkeypatch.setattr(independent_eval, "predict_tiled", fake_tiled)
    monkeypatch.setattr(independent_eval, "load_external_trees", fake_external_loader)
    monkeypatch.setattr(independent_eval, "load_demol_cohort", fake_demol_loader)
    monkeypatch.setattr(
        independent_eval.qsm,
        "compute_qsm",
        lambda wood, *, seed: SimpleNamespace(dbh_cm=10.0, height_m=5.0, total_volume_m3=2.0),
    )

    result = independent_eval.run_independent_evaluation(**paths)

    assert result["verdict"]["verdict"] == "FAIL_METRICS"
    assert len(model_instances) == 1
    assert len(baseline_calls) == 75
    assert len(tiled_calls) == 75
    assert len(logits_calls) == 75
    expected_baseline = dict(protocol["baseline"])
    expected_baseline.pop("backend")
    assert all(kwargs == expected_baseline for _, kwargs in baseline_calls)
    expected_tiled = dict(protocol["pointnet_inference"])
    expected_tiled.pop("required_coverage")
    assert all(kwargs == expected_tiled for _, _, kwargs in tiled_calls)
    assert loader_calls["external"] == (
        str(Path(paths["external_root"]).resolve()),
        external_manifest,
    )
    assert loader_calls["demol"] == (
        str(Path(paths["demol_root"]).resolve()),
        {
            "max_points": protocol["demol"]["max_points"],
            "sample_seed": protocol["demol"]["sampling_seed"],
            "formal": True,
            "expected_tree_ids": protocol["demol"]["tree_ids"],
        },
    )


def test_cohort_validation_failure_precedes_model_construction(tmp_path: Path, monkeypatch):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError

    paths, protocol, freeze, external_manifest = _guard_fixture(tmp_path)
    model_calls: list[str] = []
    monkeypatch.setattr(independent_eval, "load_protocol", lambda path: protocol)
    monkeypatch.setattr(independent_eval, "_load_freeze", lambda path: freeze)
    monkeypatch.setattr(independent_eval, "_load_external_manifest", lambda path: external_manifest)
    monkeypatch.setattr(independent_eval, "_validate_git_evidence_state", lambda **kwargs: "e" * 40)
    monkeypatch.setattr(
        independent_eval,
        "load_external_trees",
        lambda root, manifest: [
            (tree_id, _points(100.0 + index, 4), np.array([0, 0, 1, 1], dtype=np.uint8))
            for index, tree_id in enumerate(external_manifest["tree_ids"])
        ],
    )
    monkeypatch.setattr(
        independent_eval,
        "load_demol_cohort",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("invalid Demol cohort")),
    )
    monkeypatch.setattr(
        independent_eval,
        "WoodLeafSegmenter",
        lambda *args, **kwargs: model_calls.append("model"),
    )

    with pytest.raises(IndependentEvaluationError, match="invalid Demol cohort"):
        independent_eval.run_independent_evaluation(**paths)
    assert model_calls == []
    assert not Path(paths["evidence_dir"]).exists()


def test_incomplete_tiled_coverage_invalidates_whole_run_without_artifacts(
    tmp_path: Path, monkeypatch
):
    from pipeline import independent_eval
    from pipeline.independent_eval import IndependentEvaluationError
    from pipeline.pointnet_tiled import TiledPrediction

    paths, protocol, freeze, external_manifest = _guard_fixture(tmp_path)
    monkeypatch.setattr(independent_eval, "load_protocol", lambda path: protocol)
    monkeypatch.setattr(independent_eval, "_load_freeze", lambda path: freeze)
    monkeypatch.setattr(independent_eval, "_load_external_manifest", lambda path: external_manifest)
    monkeypatch.setattr(independent_eval, "_validate_git_evidence_state", lambda **kwargs: "e" * 40)
    monkeypatch.setattr(
        independent_eval,
        "WoodLeafSegmenter",
        lambda *args, **kwargs: SimpleNamespace(
            pointnet_logits=lambda points: np.zeros((len(points), 2))
        ),
    )
    monkeypatch.setattr(
        independent_eval,
        "predict_tiled",
        lambda points, model_logits, **kwargs: TiledPrediction(
            np.zeros(len(points), dtype=np.int8),
            np.zeros((len(points), 2)),
            np.array([0, *([1] * (len(points) - 1))], dtype=np.int64),
        ),
    )
    monkeypatch.setattr(
        independent_eval,
        "load_external_trees",
        lambda root, manifest: [
            (tree_id, _points(100.0 + index, 4), np.array([0, 0, 1, 1], dtype=np.uint8))
            for index, tree_id in enumerate(external_manifest["tree_ids"])
        ],
    )
    demol_loads = []
    monkeypatch.setattr(
        independent_eval,
        "load_demol_cohort",
        lambda *args, **kwargs: demol_loads.append("loaded") or [],
    )

    with pytest.raises(IndependentEvaluationError, match="coverage"):
        independent_eval.run_independent_evaluation(**paths)
    assert demol_loads == ["loaded"]
    assert not Path(paths["evidence_dir"]).exists()


def test_demol_predictor_failure_invalidates_evidence_and_cli_without_artifacts(
    tmp_path: Path, monkeypatch, capsys
):
    from pipeline import independent_eval
    from pipeline.demol_eval import DemolTree
    from pipeline.pointnet_tiled import TiledPrediction
    from scripts import pointnet_evidence

    paths, protocol, freeze, external_manifest = _guard_fixture(tmp_path)
    monkeypatch.setattr(independent_eval, "load_protocol", lambda path: protocol)
    monkeypatch.setattr(independent_eval, "_load_freeze", lambda path: freeze)
    monkeypatch.setattr(independent_eval, "_load_external_manifest", lambda path: external_manifest)
    monkeypatch.setattr(independent_eval, "_validate_git_evidence_state", lambda **kwargs: "e" * 40)
    monkeypatch.setattr(
        independent_eval,
        "load_external_trees",
        lambda root, manifest: [
            (tree_id, _points(100.0 + index, 4), np.array([0, 0, 1, 1], dtype=np.uint8))
            for index, tree_id in enumerate(manifest["tree_ids"])
        ],
    )
    monkeypatch.setattr(
        independent_eval,
        "load_demol_cohort",
        lambda *args, **kwargs: [DemolTree("DEMOL-A", _points(1.0, 4), 10.0, 5.0, 2.0)],
    )
    monkeypatch.setattr(
        independent_eval,
        "WoodLeafSegmenter",
        lambda *args, **kwargs: SimpleNamespace(
            pointnet_logits=lambda points: np.zeros((len(points), 2))
        ),
    )
    monkeypatch.setattr(
        independent_eval,
        "segment_wood_leaf",
        lambda points, **kwargs: np.array([0, 0, 1, 1], dtype=np.int8),
    )
    monkeypatch.setattr(
        independent_eval,
        "predict_tiled",
        lambda points, model_logits, **kwargs: TiledPrediction(
            np.array([0, 0, 1, 1], dtype=np.int8),
            np.zeros((len(points), 2)),
            np.array([0, 1, 1, 1], dtype=np.int64)
            if points[0, 0] < 100.0
            else np.ones(len(points), dtype=np.int64),
        ),
    )
    monkeypatch.setattr(
        independent_eval.qsm,
        "compute_qsm",
        lambda wood, *, seed: SimpleNamespace(
            dbh_cm=10.0,
            height_m=5.0,
            total_volume_m3=2.0,
        ),
    )
    monkeypatch.setattr(pointnet_evidence, "run_independent_evaluation", independent_eval.run_independent_evaluation)

    argv = ["evaluate"]
    for name, value in paths.items():
        argv.extend([f"--{name.replace('_', '-')}", value])

    assert pointnet_evidence.main(argv) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["verdict"] == "INVALID_EVIDENCE"
    assert "predictor:" in output["error"]
    assert not Path(paths["evidence_dir"]).exists()


def test_composition_reaches_fail_and_strong_promotion_verdicts():
    from pipeline.independent_eval import _compose_evaluation_from_validated_inputs

    failed = _toy_bundle(candidate=_baseline)
    assert failed.result["verdict"] == {"verdict": "FAIL_METRICS", "promote": False}

    def weaker_baseline(points: np.ndarray) -> np.ndarray:
        if len(points) in {2, 5}:
            return np.ones(len(points), dtype=np.int8)
        return _baseline(points)

    def exact_candidate(points: np.ndarray) -> np.ndarray:
        if len(points) == 2:
            return np.array([0, 1], dtype=np.int8)
        if len(points) == 5:
            return np.array([0, 0, 0, 1, 1], dtype=np.int8)
        return np.zeros(len(points), dtype=np.int8)

    def qsm(wood: np.ndarray, *, seed: int):
        exact = {(1.0, 4): (10.0, 5.0, 2.0), (2.0, 4): (20.0, 10.0, 4.0)}
        key = (float(wood[0, 0]), len(wood))
        values = exact[key] if key in exact else _MEASUREMENTS[key]
        return SimpleNamespace(dbh_cm=values[0], height_m=values[1], total_volume_m3=values[2])

    external, demol = _toy_cohorts()
    promoted = _compose_evaluation_from_validated_inputs(
        identity=_identity(),
        protocol=load_protocol(PROTOCOL),
        external_cohort=external,
        demol_cohort=demol,
        baseline_predictor=weaker_baseline,
        candidate_predictor=exact_candidate,
        qsm_func=qsm,
    )
    assert promoted.result["verdict"] == {"verdict": "PROMOTE_POINTNET", "promote": True}


def test_cli_guard_failure_is_ascii_invalid_evidence_json(monkeypatch, capsys):
    from pipeline.independent_eval import IndependentEvaluationError
    from scripts import pointnet_evidence

    monkeypatch.setattr(
        pointnet_evidence,
        "run_independent_evaluation",
        lambda **kwargs: (_ for _ in ()).throw(IndependentEvaluationError("hash mismatch")),
    )
    argv = ["evaluate"]
    for name in (
        "protocol",
        "freeze-manifest",
        "checkpoint",
        "external-root",
        "external-manifest",
        "demol-root",
        "evidence-dir",
        "repo-root",
    ):
        argv.extend([f"--{name}", name])

    assert pointnet_evidence.main(argv) == 1
    line = capsys.readouterr().out.strip()
    line.encode("ascii")
    assert json.loads(line) == {
        "command": "evaluate",
        "error": "hash mismatch",
        "error_type": "IndependentEvaluationError",
        "status": "error",
        "verdict": "INVALID_EVIDENCE",
    }
