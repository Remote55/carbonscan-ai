"""Deterministic controls and checkpoint identity for evidence training."""

from __future__ import annotations

import hashlib
import os
import platform
import random
import struct
import sys
from collections.abc import Mapping
from typing import Any

import numpy as np
import torch

_HASH_DOMAIN = b"treeq-state-dict-v1"
_REPRODUCIBILITY_KEYS = (
    "best_epoch",
    "best_macro_tile_wood_iou",
    "state_dict_sha256",
)


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


def _little_endian_contiguous_bytes(tensor: torch.Tensor) -> bytes:
    cpu_tensor = tensor.detach().cpu().contiguous()
    byte_view = cpu_tensor.reshape(-1).view(torch.uint8)
    raw = byte_view.numpy().tobytes(order="C")

    if sys.byteorder == "little" or cpu_tensor.element_size() == 1:
        return raw

    element_size = cpu_tensor.element_size()
    elements = np.frombuffer(raw, dtype=np.uint8).reshape(-1, element_size)
    return elements[:, ::-1].copy(order="C").tobytes(order="C")


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
    return max(
        records,
        key=lambda record: (
            float(record["best_macro_tile_wood_iou"]),
            -int(record["seed"]),
        ),
    )


def validate_reproducibility(first: dict[str, Any], rerun: dict[str, Any]) -> None:
    """Require exact agreement for the three locked reproducibility fields."""

    mismatch = [
        key
        for key in _REPRODUCIBILITY_KEYS
        if key not in first or key not in rerun or first[key] != rerun[key]
    ]
    if mismatch:
        raise ValueError(f"reproducibility mismatch: {mismatch}")


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
