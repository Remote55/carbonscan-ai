import hashlib
import os
import random
import struct
from pathlib import Path

import numpy as np
import pytest
import torch

from training import evidence_training
from training.evidence_training import (
    canonical_state_dict_sha256,
    capture_training_environment,
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
