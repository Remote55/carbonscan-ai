import hashlib
import json
import os
import random
import shutil
import struct
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from pipeline.provenance import sha256_file, write_canonical_json
from scripts import pointnet_evidence
from training import evidence_training, train_woodleaf
from training.evidence_training import (
    build_freeze_manifest,
    canonical_state_dict_sha256,
    capture_training_environment,
    run_training_matrix,
    select_winning_run,
    set_global_determinism,
    validate_reproducibility,
)


def _expected_single_tensor_hash(
    name: str,
    dtype: str,
    shape: tuple[int, ...],
    little_endian_bytes: bytes,
) -> str:
    """Build the locked v1 digest independently from the public byte contract."""

    hasher = hashlib.sha256()
    hasher.update(b"treeq-state-dict-v1")
    hasher.update(struct.pack("<Q", 1))
    for value in (name.encode("utf-8"), dtype.encode("ascii")):
        hasher.update(struct.pack("<Q", len(value)))
        hasher.update(value)
    hasher.update(struct.pack("<Q", len(shape)))
    for dimension in shape:
        hasher.update(struct.pack("<Q", dimension))
    hasher.update(struct.pack("<Q", len(little_endian_bytes)))
    hasher.update(little_endian_bytes)
    return hasher.hexdigest()


def _valid_training_records():
    return [
        {"seed": 20260716, "best_macro_tile_wood_iou": 0.51},
        {"seed": 20260717, "best_macro_tile_wood_iou": 0.49},
        {"seed": 20260718, "best_macro_tile_wood_iou": 0.50},
    ]


def _protocol():
    return {"training": {"seeds": [20260716, 20260717, 20260718]}}


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


def test_loader_from_arrays_uses_seeded_generator_and_zero_workers():
    generator = torch.Generator().manual_seed(20260716)
    loader = train_woodleaf._loader_from_arrays(
        np.zeros((2, 4, 3), dtype=np.float32),
        np.zeros((2, 4), dtype=np.int64),
        batch_size=1,
        shuffle=True,
        generator=generator,
    )

    assert loader.num_workers == 0
    assert loader.sampler.generator is generator


def test_train_returns_full_precision_record_and_saves_v2_checkpoint(
    tmp_path,
    monkeypatch,
    preserve_determinism_globals,
):
    class TinySegmenter(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.classifier = torch.nn.Linear(3, 2)

        def forward(self, points):
            return self.classifier(points)

    train_npz = tmp_path / "train.npz"
    dev_npz = tmp_path / "dev.npz"
    x = np.asarray([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]], dtype=np.float32)
    y = np.asarray([[0, 1]], dtype=np.int64)
    np.savez(train_npz, x=x, y=y)
    np.savez(dev_npz, x=x, y=y)

    full_precision_metrics = {
        "wood_iou": 0.4444444444444444,
        "leaf_iou": 0.4444444444444444,
        "mean_iou": 0.4444444444444444,
        "accuracy": 0.6666666666666666,
    }
    selection_metric = 0.5555555555555556
    monkeypatch.setattr(
        train_woodleaf,
        "PointNet2SegSSG",
        lambda num_classes: TinySegmenter(),
    )
    monkeypatch.setattr(
        train_woodleaf,
        "evaluate_full",
        lambda model, loader, device: dict(full_precision_metrics),
    )
    monkeypatch.setattr(
        train_woodleaf,
        "evaluate",
        lambda model, loader, device: selection_metric,
    )

    checkpoint_path = tmp_path / "seed-20260716.pt"
    args = SimpleNamespace(
        device="cpu",
        seed=20260716,
        train_npz=str(train_npz),
        val_npz=str(dev_npz),
        augment_synthetic=0,
        synthetic_seed_start=50000,
        n_train=1,
        n_val=1,
        n_points=2,
        batch_size=1,
        epochs=1,
        lr=0.001,
        weight_decay=0.0001,
        scheduler_step=20,
        scheduler_gamma=0.5,
        class_weight="none",
        init_checkpoint=None,
        out=str(checkpoint_path),
        protocol_sha256="a" * 64,
        wan_manifest_sha256="b" * 64,
        training_git_commit="c" * 40,
    )

    record = train_woodleaf.train(args)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)

    assert set(checkpoint) == {
        "schema_version",
        "state_dict",
        "num_classes",
        "seed",
        "selected_epoch",
        "dev_metrics",
        "protocol_sha256",
        "wan_manifest_sha256",
        "training_git_commit",
    }
    assert checkpoint["schema_version"] == "2"
    assert checkpoint["selected_epoch"] == 1
    assert checkpoint["dev_metrics"] == full_precision_metrics
    assert record["best_macro_tile_wood_iou"] == selection_metric
    assert record["dev_metrics"] == full_precision_metrics
    assert record["state_dict_sha256"] == canonical_state_dict_sha256(
        checkpoint["state_dict"]
    )
    assert record["checkpoint_sha256"] == sha256_file(checkpoint_path)
    assert record["checkpoint_path"] == str(checkpoint_path)


@pytest.fixture
def preserve_determinism_globals():
    missing = object()
    cublas_config = os.environ.get("CUBLAS_WORKSPACE_CONFIG", missing)
    python_rng_state = random.getstate()
    numpy_rng_state = np.random.get_state()  # noqa: NPY002
    torch_rng_state = torch.random.get_rng_state()
    deterministic_enabled = torch.are_deterministic_algorithms_enabled()
    deterministic_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    cudnn_benchmark = torch.backends.cudnn.benchmark
    cudnn_deterministic = torch.backends.cudnn.deterministic
    try:
        yield
    finally:
        if cublas_config is missing:
            os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
        else:
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = cublas_config
        random.setstate(python_rng_state)
        np.random.set_state(numpy_rng_state)  # noqa: NPY002
        torch.random.set_rng_state(torch_rng_state)
        torch.use_deterministic_algorithms(
            deterministic_enabled,
            warn_only=deterministic_warn_only,
        )
        torch.backends.cudnn.benchmark = cudnn_benchmark
        torch.backends.cudnn.deterministic = cudnn_deterministic


def test_select_winning_run_uses_macro_iou_then_lower_seed():
    records = [
        {"seed": 20260718, "best_macro_tile_wood_iou": 0.51},
        {"seed": 20260716, "best_macro_tile_wood_iou": 0.51},
        {"seed": 20260717, "best_macro_tile_wood_iou": 0.49},
    ]
    assert select_winning_run(records)["seed"] == 20260716


def test_select_winning_run_rejects_empty_records():
    with pytest.raises(ValueError, match="empty"):
        select_winning_run([])


@pytest.mark.parametrize(
    "seeds",
    [
        [20260716, 20260717],
        [20260716, 20260717, 20260717],
        [20260716, 20260717, 20260718, 20260719],
        [20260716, 20260717, 20260719],
    ],
    ids=("missing", "duplicate", "extra", "wrong"),
)
def test_select_winning_run_requires_exact_locked_seed_set(seeds):
    records = [
        {"seed": seed, "best_macro_tile_wood_iou": 0.5}
        for seed in seeds
    ]

    with pytest.raises(ValueError, match="seed"):
        select_winning_run(records)


@pytest.mark.parametrize("invalid_seed", [True, "20260716", 20260716.0, 20260716.5])
def test_select_winning_run_rejects_non_exact_integer_seed(invalid_seed):
    records = _valid_training_records()
    records[0]["seed"] = invalid_seed

    with pytest.raises(ValueError, match="seed"):
        select_winning_run(records)


@pytest.mark.parametrize(
    "invalid_metric",
    [True, 1, "0.5", np.float64(0.5), float("nan"), float("inf"), -float("inf")],
)
def test_select_winning_run_rejects_non_finite_or_non_python_float_metric(
    invalid_metric,
):
    records = _valid_training_records()
    records[0]["best_macro_tile_wood_iou"] = invalid_metric

    with pytest.raises(ValueError, match="best_macro_tile_wood_iou"):
        select_winning_run(records)


@pytest.mark.parametrize("invalid_metric", [-0.0001, 1.0001])
def test_select_winning_run_rejects_out_of_range_metric(invalid_metric):
    records = _valid_training_records()
    records[0]["best_macro_tile_wood_iou"] = invalid_metric

    with pytest.raises(ValueError, match="best_macro_tile_wood_iou"):
        select_winning_run(records)


def test_canonical_state_hash_ignores_mapping_order():
    first = {"b": torch.tensor([2.0]), "a": torch.tensor([[1.0]])}
    second = {"a": torch.tensor([[1.0]]), "b": torch.tensor([2.0])}
    assert canonical_state_dict_sha256(first) == canonical_state_dict_sha256(second)


def test_canonical_state_hash_includes_name_dtype_and_shape():
    baseline = canonical_state_dict_sha256({"weight": torch.tensor([1, 2], dtype=torch.int32)})

    assert baseline != canonical_state_dict_sha256(
        {"bias": torch.tensor([1, 2], dtype=torch.int32)}
    )
    assert baseline != canonical_state_dict_sha256(
        {"weight": torch.tensor([1, 2], dtype=torch.float32)}
    )
    assert baseline != canonical_state_dict_sha256(
        {"weight": torch.tensor([[1, 2]], dtype=torch.int32)}
    )


def test_canonical_state_hash_uses_contiguous_value_bytes():
    contiguous = torch.tensor([[1, 2], [3, 4]], dtype=torch.int16)
    non_contiguous = contiguous.transpose(0, 1)
    same_values_contiguous = non_contiguous.contiguous()

    assert not non_contiguous.is_contiguous()
    assert canonical_state_dict_sha256(
        {"weight": non_contiguous}
    ) == canonical_state_dict_sha256({"weight": same_values_contiguous})


def test_canonical_state_hash_rejects_non_tensor_values():
    with pytest.raises(TypeError, match="tensor"):
        canonical_state_dict_sha256({"epoch": 8})


def test_canonical_state_hash_rejects_non_string_names():
    with pytest.raises(TypeError, match=r"name.*string"):
        canonical_state_dict_sha256({1: torch.tensor([1.0])})


@pytest.mark.parametrize(
    ("tensor", "little_endian_bytes"),
    [
        (torch.tensor(0x1234, dtype=torch.int16), b"\x34\x12"),
        (torch.empty((0, 2), dtype=torch.float32), b""),
        (
            torch.tensor([1.0, -2.0], dtype=torch.bfloat16),
            b"\x80\x3f\x00\xc0",
        ),
    ],
    ids=("scalar", "empty", "bfloat16"),
)
def test_canonical_state_hash_uses_locked_little_endian_tensor_encoding(
    tensor, little_endian_bytes
):
    assert canonical_state_dict_sha256({"value": tensor}) == _expected_single_tensor_hash(
        "value",
        str(tensor.dtype),
        tuple(tensor.shape),
        little_endian_bytes,
    )


@pytest.mark.parametrize(
    ("element_size", "component_size", "big_endian", "little_endian"),
    [
        (
            8,
            4,
            b"\x3f\x80\x00\x00\xc0\x00\x00\x00",
            b"\x00\x00\x80\x3f\x00\x00\x00\xc0",
        ),
        (
            16,
            8,
            b"\x3f\xf0\x00\x00\x00\x00\x00\x00"
            b"\xc0\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\xf0\x3f"
            b"\x00\x00\x00\x00\x00\x00\x00\xc0",
        ),
    ],
    ids=("complex64", "complex128"),
)
def test_big_endian_complex_normalization_reverses_each_component_lane(
    element_size, component_size, big_endian, little_endian
):
    assert evidence_training._normalize_little_endian_bytes(
        big_endian,
        element_size=element_size,
        component_size=component_size,
        source_byteorder="big",
    ) == little_endian


def test_set_global_determinism_reseeds_all_generators(preserve_determinism_globals):
    seed = 20260716
    metadata = set_global_determinism(seed)
    first = (random.random(), np.random.random(), torch.rand(1))  # noqa: NPY002

    assert set_global_determinism(seed) == metadata
    second = (random.random(), np.random.random(), torch.rand(1))  # noqa: NPY002

    assert first[0] == second[0]
    assert first[1] == second[1]
    assert torch.equal(first[2], second[2])
    assert metadata == {
        "seed": seed,
        "deterministic_algorithms": True,
        "cublas_workspace_config": ":4096:8",
    }
    assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"
    assert torch.are_deterministic_algorithms_enabled()
    assert not torch.backends.cudnn.benchmark
    assert torch.backends.cudnn.deterministic


def test_set_global_determinism_seeds_all_cuda_devices_when_available(
    monkeypatch, preserve_determinism_globals
):
    cuda_seeds = []
    monkeypatch.setattr(torch, "manual_seed", lambda _seed: None)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "manual_seed_all", cuda_seeds.append)

    set_global_determinism(20260716)

    assert cuda_seeds == [20260716]


def test_validate_reproducibility_rejects_metric_or_state_drift():
    first = {
        "best_epoch": 8,
        "best_macro_tile_wood_iou": 0.5,
        "state_dict_sha256": "a" * 64,
    }
    validate_reproducibility(first, dict(first))
    with pytest.raises(ValueError, match="reproducibility"):
        validate_reproducibility(first, {**first, "state_dict_sha256": "b" * 64})


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("best_epoch", 9),
        ("best_macro_tile_wood_iou", 0.5000000000000001),
        ("state_dict_sha256", "b" * 64),
    ],
)
def test_validate_reproducibility_compares_each_locked_field_exactly(field, replacement):
    first = {
        "best_epoch": 8,
        "best_macro_tile_wood_iou": 0.5,
        "state_dict_sha256": "a" * 64,
    }

    with pytest.raises(ValueError, match=field):
        validate_reproducibility(first, {**first, field: replacement})


def test_validate_reproducibility_ignores_unlocked_fields():
    first = {
        "best_epoch": 8,
        "best_macro_tile_wood_iou": 0.5,
        "state_dict_sha256": "a" * 64,
        "elapsed_seconds": 1.0,
    }
    rerun = {**first, "elapsed_seconds": 2.0}

    validate_reproducibility(first, rerun)


@pytest.mark.parametrize(
    "missing_field",
    ["best_epoch", "best_macro_tile_wood_iou", "state_dict_sha256"],
)
def test_validate_reproducibility_rejects_missing_locked_fields(missing_field):
    first = {
        "best_epoch": 8,
        "best_macro_tile_wood_iou": 0.5,
        "state_dict_sha256": "a" * 64,
    }
    del first[missing_field]

    with pytest.raises(ValueError, match=missing_field):
        validate_reproducibility(first, dict(first))


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("best_epoch", True),
        ("best_epoch", 8.0),
        ("best_epoch", "8"),
        ("best_epoch", -1),
        ("best_macro_tile_wood_iou", True),
        ("best_macro_tile_wood_iou", 1),
        ("best_macro_tile_wood_iou", "0.5"),
        ("best_macro_tile_wood_iou", np.float64(0.5)),
        ("best_macro_tile_wood_iou", float("nan")),
        ("best_macro_tile_wood_iou", float("inf")),
        ("best_macro_tile_wood_iou", -float("inf")),
        ("best_macro_tile_wood_iou", -0.0001),
        ("best_macro_tile_wood_iou", 1.0001),
        ("state_dict_sha256", "a" * 63),
        ("state_dict_sha256", "a" * 65),
        ("state_dict_sha256", "A" * 64),
        ("state_dict_sha256", "g" * 64),
        ("state_dict_sha256", 64),
    ],
)
def test_validate_reproducibility_rejects_invalid_identical_schema(
    field, invalid_value
):
    record = {
        "best_epoch": 8,
        "best_macro_tile_wood_iou": 0.5,
        "state_dict_sha256": "a" * 64,
    }
    record[field] = invalid_value

    with pytest.raises(ValueError, match=field):
        validate_reproducibility(record, dict(record))


def test_capture_training_environment_contains_versions_and_device_without_paths():
    environment = capture_training_environment()

    assert set(environment) == {
        "python_version",
        "numpy_version",
        "pytorch_version",
        "cuda_version",
        "cudnn_version",
        "device_type",
        "gpu_count",
        "gpu_names",
    }
    assert environment["device_type"] in {"cpu", "cuda"}
    assert environment["gpu_count"] == len(environment["gpu_names"])
    assert not any(isinstance(value, Path) for value in environment.values())
    assert not any("path" in key.lower() for key in environment)
    assert str(Path.cwd()) not in repr(environment)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _freeze_fixture(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    artifact_dir = repo / "artifacts"
    evidence_dir = repo / "evidence"
    repo.mkdir()
    artifact_dir.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "TreeQ Tests")
    (repo / ".gitignore").write_text("/artifacts/\n", encoding="utf-8")
    protocol_path = repo / "protocol.json"
    source_protocol = Path(__file__).parents[3] / "docs/evidence/pointnet_independent_eval/protocol.json"
    protocol_path.write_bytes(source_protocol.read_bytes())
    _git(repo, "add", ".gitignore", "protocol.json")
    _git(repo, "commit", "-q", "-m", "fixture")
    training_git_commit = _git(repo, "rev-parse", "HEAD")

    protocol_sha256 = sha256_file(protocol_path)
    wan_manifest_path = artifact_dir / "wan_manifest.json"
    wan_manifest = {
        "schema_version": "1",
        "source_record": "10.5061/dryad.rfj6q5799",
        "config": {"tile_m": 2.5},
        "sources": [
            {"filename": "reference_pc_White_Birch.txt", "sha256": "1" * 64},
            {"filename": "reference_pc_Dahurian_Larch.txt", "sha256": "2" * 64},
            {
                "filename": "reference_pc_Chinese_scholar_tree.txt",
                "sha256": "3" * 64,
            },
        ],
        "outputs": {
            "train": {
                "filename": "wan-train.npz",
                "sha256": "4" * 64,
                "x_sha256": "5" * 64,
                "y_sha256": "6" * 64,
                "samples": 3,
            },
            "dev": {
                "filename": "wan-dev.npz",
                "sha256": "7" * 64,
                "x_sha256": "8" * 64,
                "y_sha256": "9" * 64,
                "samples": 2,
            },
        },
        "tiles": [],
    }
    write_canonical_json(wan_manifest_path, wan_manifest)
    wan_manifest_sha256 = sha256_file(wan_manifest_path)
    environment = {"python_version": "test", "device_type": "cpu"}
    monkeypatch.setattr(
        evidence_training,
        "capture_training_environment",
        lambda: dict(environment),
    )

    metrics = {
        20260716: 0.40,
        20260717: 0.55,
        20260718: 0.50,
    }

    def checkpoint(seed: int, filename: str, *, winner_state=False):
        state_dict = {
            "weight": torch.tensor(
                [17.0 if winner_state else float(seed)],
                dtype=torch.float32,
            )
        }
        dev_metrics = {
            "wood_iou": metrics[seed] - 0.01,
            "leaf_iou": 0.6,
            "mean_iou": (metrics[seed] - 0.01 + 0.6) / 2.0,
            "accuracy": 0.7,
        }
        path = artifact_dir / filename
        torch.save(
            {
                "schema_version": "2",
                "state_dict": state_dict,
                "num_classes": 2,
                "seed": seed,
                "selected_epoch": 12,
                "dev_metrics": dev_metrics,
                "protocol_sha256": protocol_sha256,
                "wan_manifest_sha256": wan_manifest_sha256,
                "training_git_commit": training_git_commit,
            },
            path,
        )
        return {
            "seed": seed,
            "best_epoch": 12,
            "best_macro_tile_wood_iou": metrics[seed],
            "dev_metrics": dev_metrics,
            "state_dict_sha256": canonical_state_dict_sha256(state_dict),
            "checkpoint_file": filename,
            "checkpoint_sha256": sha256_file(path),
            "protocol_sha256": protocol_sha256,
            "wan_manifest_sha256": wan_manifest_sha256,
            "training_git_commit": training_git_commit,
        }

    runs = [
        checkpoint(20260716, "seed-20260716.pt"),
        checkpoint(20260717, "seed-20260717.pt", winner_state=True),
        checkpoint(20260718, "seed-20260718.pt"),
    ]
    shutil.copyfile(artifact_dir / "seed-20260717.pt", artifact_dir / "winner.pt")
    winner = {
        **runs[1],
        "checkpoint_file": "winner.pt",
        "checkpoint_sha256": sha256_file(artifact_dir / "winner.pt"),
    }
    rerun = checkpoint(20260717, "seed-20260717-rerun.pt", winner_state=True)
    training_runs_path = artifact_dir / "training_runs.json"
    training_runs = {
        "schema_version": "1",
        "experiment_id": "pointnet-independent-eval-2026-07-16",
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
        "training_git_commit": training_git_commit,
        "training_command": [
            "python",
            "-m",
            "scripts.pointnet_evidence",
            "train",
            "--protocol",
            "protocol.json",
        ],
        "environment": environment,
        "runs": runs,
        "winner": winner,
        "rerun": rerun,
        "reproducible": True,
    }
    write_canonical_json(training_runs_path, training_runs)
    assert not _git(repo, "status", "--porcelain")
    return {
        "repo": repo,
        "artifact_dir": artifact_dir,
        "evidence_dir": evidence_dir,
        "protocol_path": protocol_path,
        "wan_manifest_path": wan_manifest_path,
        "training_runs_path": training_runs_path,
        "training_runs": training_runs,
    }


def _build_freeze(fixture):
    return build_freeze_manifest(
        fixture["protocol_path"],
        fixture["wan_manifest_path"],
        fixture["training_runs_path"],
        fixture["artifact_dir"],
        fixture["evidence_dir"],
        fixture["repo"],
    )


def _assert_no_freeze_outputs(fixture):
    assert not (fixture["evidence_dir"] / "training_runs.json").exists()
    assert not (fixture["evidence_dir"] / "freeze_manifest.json").exists()


def test_build_freeze_manifest_writes_sanitized_canonical_evidence(tmp_path, monkeypatch):
    fixture = _freeze_fixture(tmp_path, monkeypatch)

    manifest = _build_freeze(fixture)

    tracked_runs_path = fixture["evidence_dir"] / "training_runs.json"
    freeze_path = fixture["evidence_dir"] / "freeze_manifest.json"
    tracked_runs = json.loads(tracked_runs_path.read_text(encoding="utf-8"))
    tracked_freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    assert manifest == tracked_freeze
    assert set(tracked_runs) == {
        "schema_version",
        "experiment_id",
        "protocol_sha256",
        "wan_manifest_sha256",
        "training_git_commit",
        "training_command",
        "environment",
        "runs",
        "winner",
        "rerun",
        "reproducible",
    }
    assert set(tracked_freeze) == {
        "schema_version",
        "experiment_id",
        "protocol_sha256",
        "wan_manifest_sha256",
        "training_runs_sha256",
        "training_git_commit",
        "working_tree_clean",
        "training_command",
        "environment",
        "architecture",
        "training_configuration",
        "wan_evidence",
        "winner",
        "rerun_evidence",
    }
    assert tracked_freeze["training_runs_sha256"] == sha256_file(tracked_runs_path)
    assert tracked_freeze["working_tree_clean"] is True
    assert tracked_freeze["architecture"] == "PointNet2SegSSG"
    assert tracked_freeze["winner"]["checkpoint_file"] == "winner.pt"
    assert "checkpoint_path" not in repr(tracked_runs)
    assert str(fixture["repo"]) not in repr(tracked_runs)
    assert str(fixture["repo"]) not in repr(tracked_freeze)


def test_build_freeze_manifest_allows_preexisting_empty_evidence_dir(
    tmp_path, monkeypatch
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    fixture["evidence_dir"].mkdir()

    manifest = _build_freeze(fixture)

    assert manifest["working_tree_clean"] is True
    assert (fixture["evidence_dir"] / "training_runs.json").is_file()
    assert (fixture["evidence_dir"] / "freeze_manifest.json").is_file()


def test_build_freeze_manifest_rejects_checkpoint_hash_tamper_without_writes(
    tmp_path, monkeypatch
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    winner = fixture["artifact_dir"] / "winner.pt"
    winner.write_bytes(winner.read_bytes() + b"tamper")

    with pytest.raises(ValueError, match=r"checkpoint.*sha256"):
        _build_freeze(fixture)

    _assert_no_freeze_outputs(fixture)


def test_build_freeze_manifest_rejects_dirty_git_without_writes(tmp_path, monkeypatch):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    (fixture["repo"] / "dirty.txt").write_text("dirty", encoding="utf-8")

    with pytest.raises(ValueError, match="clean"):
        _build_freeze(fixture)

    _assert_no_freeze_outputs(fixture)


def test_build_freeze_manifest_rejects_environment_drift_without_writes(
    tmp_path, monkeypatch
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        evidence_training,
        "capture_training_environment",
        lambda: {"python_version": "drift", "device_type": "cpu"},
    )

    with pytest.raises(ValueError, match="environment"):
        _build_freeze(fixture)

    _assert_no_freeze_outputs(fixture)


def test_build_freeze_manifest_rejects_state_hash_mismatch_without_writes(
    tmp_path, monkeypatch
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    fixture["training_runs"]["winner"]["state_dict_sha256"] = "f" * 64
    write_canonical_json(fixture["training_runs_path"], fixture["training_runs"])

    with pytest.raises(ValueError, match="state_dict_sha256"):
        _build_freeze(fixture)

    _assert_no_freeze_outputs(fixture)


def test_build_freeze_manifest_rejects_rerun_seed_mismatch_without_writes(
    tmp_path, monkeypatch
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    fixture["training_runs"]["rerun"]["seed"] = 20260716
    write_canonical_json(fixture["training_runs_path"], fixture["training_runs"])

    with pytest.raises(ValueError, match="rerun seed"):
        _build_freeze(fixture)

    _assert_no_freeze_outputs(fixture)


def test_build_freeze_manifest_rejects_absolute_checkpoint_path_without_writes(
    tmp_path, monkeypatch
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    fixture["training_runs"]["runs"][0]["checkpoint_file"] = "C:\\secret\\seed.pt"
    write_canonical_json(fixture["training_runs_path"], fixture["training_runs"])

    with pytest.raises(ValueError, match="checkpoint_file"):
        _build_freeze(fixture)

    _assert_no_freeze_outputs(fixture)


def _one_ascii_json_line(capsys):
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    lines[0].encode("ascii")
    return json.loads(lines[0])


def test_pointnet_evidence_prepare_wan_uses_protocol_order_and_one_json_line(
    tmp_path, monkeypatch, capsys
):
    repo_root = Path(__file__).parents[3]
    protocol_path = repo_root / "docs/evidence/pointnet_independent_eval/protocol.json"
    wan_root = tmp_path / "wan"
    artifact_dir = tmp_path / "artifacts"
    manifest_out = artifact_dir / "wan_manifest.json"
    wan_root.mkdir()
    captured = {}

    def fake_build(paths, out_train, out_dev, manifest_path, *, protocol, repo_root):
        captured["paths"] = [Path(path).name for path in paths]
        captured["outputs"] = [Path(out_train).name, Path(out_dev).name]
        manifest = {
            "schema_version": "1",
            "sources": [],
            "outputs": {},
            "config": protocol["wan"],
        }
        write_canonical_json(manifest_path, manifest)
        return manifest

    monkeypatch.setattr(pointnet_evidence, "build_evidence_dataset", fake_build)

    exit_code = pointnet_evidence.main(
        [
            "prepare-wan",
            "--protocol",
            str(protocol_path),
            "--wan-root",
            str(wan_root),
            "--artifact-dir",
            str(artifact_dir),
            "--manifest-out",
            str(manifest_out),
            "--repo-root",
            str(repo_root),
        ]
    )

    summary = _one_ascii_json_line(capsys)
    assert exit_code == 0
    assert summary["command"] == "prepare-wan"
    assert summary["status"] == "ok"
    assert captured["paths"] == [
        "reference_pc_White_Birch.txt",
        "reference_pc_Dahurian_Larch.txt",
        "reference_pc_Chinese_scholar_tree.txt",
    ]
    assert captured["outputs"] == ["wan-train.npz", "wan-dev.npz"]


def test_pointnet_evidence_train_writes_ignored_record_and_winner_copy(
    tmp_path, monkeypatch, capsys
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    for checkpoint_path in fixture["artifact_dir"].glob("*.pt"):
        checkpoint_path.unlink()
    fixture["training_runs_path"].unlink()
    (fixture["artifact_dir"] / "wan-train.npz").write_bytes(b"train")
    (fixture["artifact_dir"] / "wan-dev.npz").write_bytes(b"dev")
    wan_manifest = json.loads(
        fixture["wan_manifest_path"].read_text(encoding="utf-8")
    )
    wan_manifest["outputs"]["train"]["sha256"] = sha256_file(
        fixture["artifact_dir"] / "wan-train.npz"
    )
    wan_manifest["outputs"]["dev"]["sha256"] = sha256_file(
        fixture["artifact_dir"] / "wan-dev.npz"
    )
    write_canonical_json(fixture["wan_manifest_path"], wan_manifest)
    calls = []

    def fake_train(args):
        calls.append(args.seed)
        score = {20260716: 0.40, 20260717: 0.55, 20260718: 0.50}[args.seed]
        state_dict = {"weight": torch.tensor([float(args.seed)])}
        dev_metrics = {
            "wood_iou": score,
            "leaf_iou": 0.6,
            "mean_iou": (score + 0.6) / 2.0,
            "accuracy": 0.7,
        }
        torch.save(
            {
                "schema_version": "2",
                "state_dict": state_dict,
                "num_classes": 2,
                "seed": args.seed,
                "selected_epoch": 12,
                "dev_metrics": dev_metrics,
                "protocol_sha256": args.protocol_sha256,
                "wan_manifest_sha256": args.wan_manifest_sha256,
                "training_git_commit": args.training_git_commit,
            },
            args.out,
        )
        return {
            "seed": args.seed,
            "best_epoch": 12,
            "best_macro_tile_wood_iou": score,
            "dev_metrics": dev_metrics,
            "state_dict_sha256": canonical_state_dict_sha256(state_dict),
            "checkpoint_path": str(args.out),
            "checkpoint_sha256": sha256_file(args.out),
            "protocol_sha256": args.protocol_sha256,
            "wan_manifest_sha256": args.wan_manifest_sha256,
            "training_git_commit": args.training_git_commit,
        }

    monkeypatch.setattr(pointnet_evidence.train_woodleaf, "train", fake_train)

    exit_code = pointnet_evidence.main(
        [
            "train",
            "--protocol",
            str(fixture["protocol_path"]),
            "--wan-manifest",
            str(fixture["wan_manifest_path"]),
            "--artifact-dir",
            str(fixture["artifact_dir"]),
            "--repo-root",
            str(fixture["repo"]),
        ]
    )

    summary = _one_ascii_json_line(capsys)
    record = json.loads(fixture["training_runs_path"].read_text(encoding="utf-8"))
    assert exit_code == 0
    assert summary == {
        "command": "train",
        "reproducible": True,
        "status": "ok",
        "winner_seed": 20260717,
    }
    assert calls == [20260716, 20260717, 20260718, 20260717]
    assert (fixture["artifact_dir"] / "winner.pt").read_bytes() == (
        fixture["artifact_dir"] / "seed-20260717.pt"
    ).read_bytes()
    assert record["winner"]["checkpoint_file"] == "winner.pt"
    assert record["rerun"]["checkpoint_file"] == "seed-20260717-rerun.pt"
    assert "checkpoint_path" not in repr(record)
    assert str(fixture["repo"]) not in repr(record)


def test_pointnet_evidence_train_rejects_wan_output_hash_mismatch_before_training(
    tmp_path, monkeypatch, capsys
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    for checkpoint_path in fixture["artifact_dir"].glob("*.pt"):
        checkpoint_path.unlink()
    fixture["training_runs_path"].unlink()
    (fixture["artifact_dir"] / "wan-train.npz").write_bytes(b"tampered-train")
    (fixture["artifact_dir"] / "wan-dev.npz").write_bytes(b"tampered-dev")
    calls = []

    def unexpected_train(args):
        calls.append(args.seed)
        raise RuntimeError("training must not start")

    monkeypatch.setattr(pointnet_evidence.train_woodleaf, "train", unexpected_train)

    exit_code = pointnet_evidence.main(
        [
            "train",
            "--protocol",
            str(fixture["protocol_path"]),
            "--wan-manifest",
            str(fixture["wan_manifest_path"]),
            "--artifact-dir",
            str(fixture["artifact_dir"]),
            "--repo-root",
            str(fixture["repo"]),
        ]
    )

    summary = _one_ascii_json_line(capsys)
    assert exit_code == 1
    assert "sha256" in summary["error"]
    assert calls == []


def test_pointnet_evidence_freeze_returns_nonzero_json_on_validation_failure(
    tmp_path, monkeypatch, capsys
):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    (fixture["repo"] / "dirty.txt").write_text("dirty", encoding="utf-8")

    exit_code = pointnet_evidence.main(
        [
            "freeze",
            "--protocol",
            str(fixture["protocol_path"]),
            "--wan-manifest",
            str(fixture["wan_manifest_path"]),
            "--artifact-dir",
            str(fixture["artifact_dir"]),
            "--evidence-dir",
            str(fixture["evidence_dir"]),
            "--repo-root",
            str(fixture["repo"]),
        ]
    )

    summary = _one_ascii_json_line(capsys)
    assert exit_code == 1
    assert summary["command"] == "freeze"
    assert summary["status"] == "error"
    _assert_no_freeze_outputs(fixture)
