"""Deterministic controls and checkpoint identity for evidence training."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import struct
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import numpy as np
import torch

from pipeline.provenance import (
    git_worktree_dirty,
    resolve_git_commit,
    sha256_file,
)
from training.evidence_protocol import load_protocol

_HASH_DOMAIN = b"treeq-state-dict-v1"
_LOCKED_TRAINING_SEEDS = (20260716, 20260717, 20260718)
_LOWER_HEX = frozenset("0123456789abcdef")
_REPRODUCIBILITY_KEYS = (
    "best_epoch",
    "best_macro_tile_wood_iou",
    "state_dict_sha256",
)
_TRAINING_RUNS_KEYS = {
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
_RUN_RECORD_KEYS = (
    "seed",
    "best_epoch",
    "best_macro_tile_wood_iou",
    "dev_metrics",
    "state_dict_sha256",
    "checkpoint_file",
    "checkpoint_sha256",
    "protocol_sha256",
    "wan_manifest_sha256",
    "training_git_commit",
)
_CHECKPOINT_KEYS = {
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
_WAN_SOURCE_KEYS = {"filename", "sha256", "size_bytes"}


def set_global_determinism(seed: int) -> dict[str, Any]:
    """Seed training RNGs and require deterministic PyTorch operations."""

    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    random.seed(seed)
    np.random.seed(seed)  # noqa: NPY002 -- the training code uses NumPy's global RNG
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    return {
        "seed": seed,
        "deterministic_algorithms": True,
        "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
    }


def _update_length_prefixed(hasher: Any, value: bytes) -> None:
    hasher.update(struct.pack("<Q", len(value)))
    hasher.update(value)


def _normalize_little_endian_bytes(
    raw: bytes,
    *,
    element_size: int,
    component_size: int,
    source_byteorder: str,
) -> bytes:
    """Normalize raw tensor bytes without changing complex component order."""

    if source_byteorder not in {"little", "big"}:
        raise ValueError(f"unsupported byte order: {source_byteorder!r}")
    if element_size <= 0 or component_size <= 0 or element_size % component_size:
        raise ValueError("invalid tensor element/component size")
    if len(raw) % element_size:
        raise ValueError("raw tensor byte length is not element aligned")
    if source_byteorder == "little" or component_size == 1:
        return raw

    components = np.frombuffer(raw, dtype=np.uint8).reshape(-1, component_size)
    return components[:, ::-1].copy(order="C").tobytes(order="C")


def _little_endian_contiguous_bytes(tensor: torch.Tensor) -> bytes:
    cpu_tensor = tensor.detach().cpu().contiguous()
    byte_view = cpu_tensor.reshape(-1).view(torch.uint8)
    raw = byte_view.numpy().tobytes(order="C")
    element_size = cpu_tensor.element_size()
    component_size = element_size // 2 if cpu_tensor.is_complex() else element_size
    return _normalize_little_endian_bytes(
        raw,
        element_size=element_size,
        component_size=component_size,
        source_byteorder=sys.byteorder,
    )


def canonical_state_dict_sha256(state_dict: Mapping[str, torch.Tensor]) -> str:
    """Hash tensor names, metadata, and normalized bytes in canonical order."""

    for name, value in state_dict.items():
        if not isinstance(name, str):
            raise TypeError(f"state_dict name must be a string, got {type(name).__name__}")
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"state_dict value for {name!r} must be a tensor")

    hasher = hashlib.sha256()
    hasher.update(_HASH_DOMAIN)
    hasher.update(struct.pack("<Q", len(state_dict)))

    for name in sorted(state_dict):
        tensor = state_dict[name]
        _update_length_prefixed(hasher, name.encode("utf-8"))
        _update_length_prefixed(hasher, str(tensor.dtype).encode("ascii"))
        hasher.update(struct.pack("<Q", tensor.ndim))
        for dimension in tensor.shape:
            hasher.update(struct.pack("<Q", dimension))
        _update_length_prefixed(hasher, _little_endian_contiguous_bytes(tensor))

    return hasher.hexdigest()


def select_winning_run(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Select highest macro tile wood IoU, breaking ties by lower seed."""

    if not records:
        raise ValueError("training records are empty")
    seeds: list[int] = []
    for record in records:
        seed = record.get("seed")
        if type(seed) is not int:
            raise ValueError("training record seed must be an exact integer")
        metric = record.get("best_macro_tile_wood_iou")
        if type(metric) is not float or not math.isfinite(metric) or not 0.0 <= metric <= 1.0:
            raise ValueError(
                "training record best_macro_tile_wood_iou must be a finite "
                "Python float in [0, 1]"
            )
        seeds.append(seed)

    if sorted(seeds) != list(_LOCKED_TRAINING_SEEDS):
        raise ValueError(
            "training record seeds must contain exactly one each of "
            f"{list(_LOCKED_TRAINING_SEEDS)}"
        )
    return max(
        records,
        key=lambda record: (
            record["best_macro_tile_wood_iou"],
            -record["seed"],
        ),
    )


def _validate_reproducibility_record(record: dict[str, Any]) -> None:
    epoch = record.get("best_epoch")
    if type(epoch) is not int or epoch < 0:
        raise ValueError("reproducibility best_epoch must be a non-negative integer")

    metric = record.get("best_macro_tile_wood_iou")
    if type(metric) is not float or not math.isfinite(metric) or not 0.0 <= metric <= 1.0:
        raise ValueError(
            "reproducibility best_macro_tile_wood_iou must be a finite "
            "Python float in [0, 1]"
        )

    state_hash = record.get("state_dict_sha256")
    if (
        type(state_hash) is not str
        or len(state_hash) != 64
        or any(character not in _LOWER_HEX for character in state_hash)
    ):
        raise ValueError(
            "reproducibility state_dict_sha256 must be 64 lowercase hex characters"
        )


def validate_reproducibility(first: dict[str, Any], rerun: dict[str, Any]) -> None:
    """Require exact agreement for the three locked reproducibility fields."""

    _validate_reproducibility_record(first)
    _validate_reproducibility_record(rerun)
    mismatch = [
        key
        for key in _REPRODUCIBILITY_KEYS
        if key not in first or key not in rerun or first[key] != rerun[key]
    ]
    if mismatch:
        raise ValueError(f"reproducibility mismatch: {mismatch}")


def run_training_matrix(
    protocol: dict[str, Any],
    artifact_dir: str | Path,
    *,
    train_one_seed: Any,
) -> dict[str, Any]:
    """Run the locked seed matrix and verify an exact winner rerun."""

    artifact_dir = Path(artifact_dir)
    records = []
    for seed in protocol["training"]["seeds"]:
        records.append(train_one_seed(seed, artifact_dir / f"seed-{seed}.pt"))
    winner = select_winning_run(records)
    rerun = train_one_seed(
        winner["seed"],
        artifact_dir / f"seed-{winner['seed']}-rerun.pt",
    )
    validate_reproducibility(winner, rerun)
    return {
        "runs": records,
        "winner": winner,
        "rerun": rerun,
        "reproducible": True,
    }


def _is_lower_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in _LOWER_HEX for character in value)
    )


def _is_cross_platform_absolute(value: str) -> bool:
    return PurePosixPath(value.replace("\\", "/")).is_absolute() or PureWindowsPath(
        value
    ).is_absolute()


def _require_logical_filename(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a non-empty logical filename")
    normalized = value.replace("\\", "/")
    if (
        _is_cross_platform_absolute(value)
        or normalized in {".", ".."}
        or "/" in normalized
        or PureWindowsPath(value).name != value
    ):
        raise ValueError(f"{label} must be a logical basename without traversal")
    return value


def _validate_path_privacy(value: Any, *, repo_root: Path) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _validate_path_privacy(child, repo_root=repo_root)
        return
    if isinstance(value, list):
        for child in value:
            _validate_path_privacy(child, repo_root=repo_root)
        return
    if type(value) is not str:
        return
    normalized = value.replace("\\", "/")
    if _is_cross_platform_absolute(value):
        raise ValueError(f"evidence cannot contain absolute path {value!r}")
    if repo_root.as_posix().casefold() in normalized.casefold():
        raise ValueError("evidence cannot contain repo_root")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _validate_wan_source(source: Any, index: int) -> dict[str, Any]:
    label = f"Wan source {index}"
    if type(source) is not dict or set(source) != _WAN_SOURCE_KEYS:
        raise ValueError(f"{label} schema is not exact")
    _require_logical_filename(source["filename"], f"{label} filename")
    if not _is_lower_sha256(source["sha256"]):
        raise ValueError(f"{label} sha256 must be lowercase SHA-256")
    if type(source["size_bytes"]) is not int or source["size_bytes"] <= 0:
        raise ValueError(f"{label} size_bytes must be a positive integer")
    return source


def _validate_wan_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "1":
        raise ValueError("Wan manifest schema_version must equal '1'")
    config = payload.get("config")
    sources = payload.get("sources")
    outputs = payload.get("outputs")
    if type(config) is not dict or type(sources) is not list or type(outputs) is not dict:
        raise ValueError("Wan manifest must contain config, sources, and outputs")
    if set(outputs) != {"train", "dev"}:
        raise ValueError("Wan manifest outputs must contain exactly train and dev")
    for index, source in enumerate(sources):
        _validate_wan_source(source, index)
    for split_name, output in outputs.items():
        if type(output) is not dict:
            raise ValueError(f"Wan output {split_name} must be an object")
        _require_logical_filename(
            output.get("filename"),
            f"Wan output {split_name} filename",
        )
        for hash_name in ("sha256", "x_sha256", "y_sha256"):
            if not _is_lower_sha256(output.get(hash_name)):
                raise ValueError(
                    f"Wan output {split_name} {hash_name} must be lowercase SHA-256"
                )
    return {
        "schema_version": payload["schema_version"],
        "config": config,
        "sources": sources,
        "outputs": outputs,
    }


def _validate_dev_metrics(value: Any, label: str) -> dict[str, float]:
    expected = {"wood_iou", "leaf_iou", "mean_iou", "accuracy"}
    if type(value) is not dict or set(value) != expected:
        raise ValueError(f"{label} must contain exactly {sorted(expected)!r}")
    for name, metric in value.items():
        if type(metric) is not float or not math.isfinite(metric) or not 0.0 <= metric <= 1.0:
            raise ValueError(f"{label}.{name} must be a finite Python float in [0, 1]")
    return value


def _sanitize_run_record(
    record: Any,
    *,
    label: str,
    protocol_sha256: str,
    wan_manifest_sha256: str,
    training_git_commit: str,
    artifact_dir: Path,
) -> dict[str, Any]:
    if type(record) is not dict:
        raise ValueError(f"{label} must be an object")
    if "checkpoint_path" in record:
        raise ValueError(f"{label} cannot contain checkpoint_path")
    missing = [key for key in _RUN_RECORD_KEYS if key not in record]
    if missing:
        raise ValueError(f"{label} is missing fields: {missing!r}")
    seed = record.get("seed")
    if type(seed) is not int:
        raise ValueError(f"{label}.seed must be an exact integer")
    _validate_reproducibility_record(record)
    _validate_dev_metrics(record.get("dev_metrics"), f"{label}.dev_metrics")
    expected_provenance = {
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
        "training_git_commit": training_git_commit,
    }
    for name, expected in expected_provenance.items():
        if record.get(name) != expected:
            raise ValueError(f"{label}.{name} does not match training run provenance")
    checkpoint_file = _require_logical_filename(
        record.get("checkpoint_file"),
        f"{label}.checkpoint_file",
    )
    checkpoint_sha256 = record.get("checkpoint_sha256")
    if not _is_lower_sha256(checkpoint_sha256):
        raise ValueError(f"{label}.checkpoint_sha256 must be lowercase SHA-256")
    checkpoint_path = (artifact_dir / checkpoint_file).resolve()
    if checkpoint_path.parent != artifact_dir or not checkpoint_path.is_file():
        raise ValueError(f"{label}.checkpoint_file must resolve under artifact_dir")
    if sha256_file(checkpoint_path) != checkpoint_sha256:
        raise ValueError(f"{label} checkpoint sha256 mismatch")
    return {key: record[key] for key in _RUN_RECORD_KEYS}


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _publish_evidence_pair(
    evidence_dir: Path,
    training_runs_bytes: bytes,
    freeze_manifest_bytes: bytes,
) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_paths = [
        evidence_dir / "training_runs.json",
        evidence_dir / "freeze_manifest.json",
    ]
    temp_paths: list[Path] = []
    published: list[Path] = []
    try:
        for payload in (training_runs_bytes, freeze_manifest_bytes):
            descriptor, raw_temp_path = tempfile.mkstemp(
                prefix=".pointnet-evidence-",
                suffix=".tmp",
                dir=evidence_dir,
            )
            temp_path = Path(raw_temp_path)
            temp_paths.append(temp_path)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        for temp_path, output_path in zip(temp_paths, output_paths, strict=True):
            os.replace(temp_path, output_path)
            published.append(output_path)
    except Exception:
        for output_path in published:
            output_path.unlink(missing_ok=True)
        raise
    finally:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)


def build_freeze_manifest(
    protocol_path: str | Path,
    wan_manifest_path: str | Path,
    training_runs_path: str | Path,
    artifact_dir: str | Path,
    evidence_dir: str | Path,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Validate a training run and atomically publish tracked freeze evidence."""

    protocol_path = Path(protocol_path).resolve()
    wan_manifest_path = Path(wan_manifest_path).resolve()
    training_runs_path = Path(training_runs_path).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    evidence_dir = Path(evidence_dir).resolve()
    repo_root = Path(repo_root).resolve()
    output_paths = {
        evidence_dir / "training_runs.json",
        evidence_dir / "freeze_manifest.json",
    }
    input_paths = {protocol_path, wan_manifest_path, training_runs_path}
    if len(output_paths) != 2 or output_paths.intersection(input_paths):
        raise ValueError("freeze outputs must be distinct and cannot alias inputs")
    if evidence_dir.exists() and not evidence_dir.is_dir():
        raise ValueError("freeze evidence_dir must be a directory")
    if any(path.exists() for path in output_paths):
        raise ValueError("freeze evidence outputs must not already exist")

    protocol = load_protocol(protocol_path)
    protocol_sha256 = sha256_file(protocol_path)
    wan_manifest_sha256 = sha256_file(wan_manifest_path)
    sha256_file(training_runs_path)
    wan_manifest = _load_json_object(wan_manifest_path, "Wan manifest")
    wan_evidence = _validate_wan_manifest(wan_manifest)
    training_runs = _load_json_object(training_runs_path, "training runs")
    if set(training_runs) != _TRAINING_RUNS_KEYS:
        raise ValueError("training runs top-level schema is not exact")
    expected_top_level = {
        "schema_version": "1",
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
    }
    for name, expected in expected_top_level.items():
        if training_runs.get(name) != expected:
            raise ValueError(f"training runs {name} does not match frozen input")
    if training_runs.get("reproducible") is not True:
        raise ValueError("training runs reproducible must be true")

    training_git_commit = training_runs.get("training_git_commit")
    if (
        type(training_git_commit) is not str
        or len(training_git_commit) != 40
        or any(character not in _LOWER_HEX for character in training_git_commit)
    ):
        raise ValueError("training_git_commit must be 40 lowercase hex characters")
    if git_worktree_dirty(repo_root):
        raise ValueError("Git working tree must be clean before freeze")
    if resolve_git_commit(repo_root) != training_git_commit:
        raise ValueError("current Git HEAD does not match training_git_commit")

    training_command = training_runs.get("training_command")
    if type(training_command) is not list or not training_command:
        raise ValueError("training_command must be a non-empty list")
    for index, value in enumerate(training_command):
        if type(value) is not str or not value:
            raise ValueError(f"training_command[{index}] must be a non-empty string")
        _validate_path_privacy(value, repo_root=repo_root)
    environment = training_runs.get("environment")
    if type(environment) is not dict or capture_training_environment() != environment:
        raise ValueError("current training environment does not match train-time environment")

    artifact_dir = artifact_dir.resolve()
    run_inputs = training_runs.get("runs")
    if type(run_inputs) is not list:
        raise ValueError("training runs must be a list")
    runs = [
        _sanitize_run_record(
            record,
            label=f"runs[{index}]",
            protocol_sha256=protocol_sha256,
            wan_manifest_sha256=wan_manifest_sha256,
            training_git_commit=training_git_commit,
            artifact_dir=artifact_dir,
        )
        for index, record in enumerate(run_inputs)
    ]
    selected = select_winning_run(runs)
    winner = _sanitize_run_record(
        training_runs.get("winner"),
        label="winner",
        protocol_sha256=protocol_sha256,
        wan_manifest_sha256=wan_manifest_sha256,
        training_git_commit=training_git_commit,
        artifact_dir=artifact_dir,
    )
    rerun = _sanitize_run_record(
        training_runs.get("rerun"),
        label="rerun",
        protocol_sha256=protocol_sha256,
        wan_manifest_sha256=wan_manifest_sha256,
        training_git_commit=training_git_commit,
        artifact_dir=artifact_dir,
    )
    if winner["seed"] != selected["seed"]:
        raise ValueError("winner seed does not match strict seed selection")
    if rerun["seed"] != winner["seed"]:
        raise ValueError("rerun seed does not match winner seed")
    validate_reproducibility(selected, winner)
    validate_reproducibility(winner, rerun)
    if winner["checkpoint_file"] != "winner.pt":
        raise ValueError("winner checkpoint_file must equal 'winner.pt'")

    winner_checkpoint_path = artifact_dir / "winner.pt"
    checkpoint = torch.load(
        winner_checkpoint_path,
        map_location="cpu",
        weights_only=True,
    )
    if type(checkpoint) is not dict or set(checkpoint) != _CHECKPOINT_KEYS:
        raise ValueError("winner checkpoint schema is not exact")
    checkpoint_expected = {
        "schema_version": "2",
        "num_classes": 2,
        "seed": winner["seed"],
        "selected_epoch": winner["best_epoch"],
        "dev_metrics": winner["dev_metrics"],
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
        "training_git_commit": training_git_commit,
    }
    for name, expected in checkpoint_expected.items():
        if checkpoint.get(name) != expected:
            raise ValueError(f"winner checkpoint {name} does not match winner record")
    state_dict_sha256 = canonical_state_dict_sha256(checkpoint["state_dict"])
    if state_dict_sha256 != winner["state_dict_sha256"]:
        raise ValueError("winner state_dict_sha256 mismatch")

    tracked_training_runs = {
        "schema_version": "1",
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
        "training_git_commit": training_git_commit,
        "training_command": training_command,
        "environment": environment,
        "runs": runs,
        "winner": winner,
        "rerun": rerun,
        "reproducible": True,
    }
    _validate_path_privacy(tracked_training_runs, repo_root=repo_root)
    tracked_training_runs_bytes = _canonical_json_bytes(tracked_training_runs)
    freeze_manifest = {
        "schema_version": "1",
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
        "training_runs_sha256": hashlib.sha256(tracked_training_runs_bytes).hexdigest(),
        "training_git_commit": training_git_commit,
        "working_tree_clean": True,
        "training_command": training_command,
        "environment": environment,
        "architecture": "PointNet2SegSSG",
        "training_configuration": protocol["training"],
        "wan_evidence": wan_evidence,
        "winner": {
            "seed": winner["seed"],
            "selected_epoch": winner["best_epoch"],
            "dev_metrics": winner["dev_metrics"],
            "checkpoint_file": "winner.pt",
            "checkpoint_sha256": winner["checkpoint_sha256"],
            "state_dict_sha256": winner["state_dict_sha256"],
        },
        "rerun_evidence": {
            "seed": rerun["seed"],
            "best_epoch": rerun["best_epoch"],
            "best_macro_tile_wood_iou": rerun["best_macro_tile_wood_iou"],
            "state_dict_sha256": rerun["state_dict_sha256"],
            "checkpoint_file": rerun["checkpoint_file"],
            "checkpoint_sha256": rerun["checkpoint_sha256"],
            "reproducible": True,
        },
    }
    _validate_path_privacy(freeze_manifest, repo_root=repo_root)
    freeze_manifest_bytes = _canonical_json_bytes(freeze_manifest)
    _publish_evidence_pair(
        evidence_dir,
        tracked_training_runs_bytes,
        freeze_manifest_bytes,
    )
    return freeze_manifest


def capture_training_environment() -> dict[str, Any]:
    """Capture version and device metadata without machine-local paths."""

    cuda_available = torch.cuda.is_available()
    gpu_count = torch.cuda.device_count() if cuda_available else 0
    return {
        "python_version": platform.python_version(),
        "numpy_version": str(np.__version__),
        "pytorch_version": str(torch.__version__),
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "device_type": "cuda" if cuda_available else "cpu",
        "gpu_count": gpu_count,
        "gpu_names": [torch.cuda.get_device_name(index) for index in range(gpu_count)],
    }
