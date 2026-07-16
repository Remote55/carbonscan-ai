"""Validation for the precommitted PointNet independent-evaluation protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_TOP_LEVEL = {
    "schema_version",
    "experiment_id",
    "baseline",
    "wan",
    "training",
    "pointnet_inference",
    "external",
    "demol",
    "statistics",
}

EXPECTED_SECTIONS: dict[str, dict[str, Any]] = {
    "baseline": {
        "backend": "tlsep",
        "k_neighbors": 20,
        "linearity_min": 0.45,
        "planarity_max": 0.5,
        "verticality_boost_min": 0.55,
    },
    "wan": {
        "source_record": "10.5061/dryad.rfj6q5799",
        "files": [
            "reference_pc_White_Birch.txt",
            "reference_pc_Dahurian_Larch.txt",
            "reference_pc_Chinese_scholar_tree.txt",
        ],
        "n_off": 10000,
        "per": 1500,
        "tile_m": 2.5,
        "points_per_tile": 2048,
        "min_points_per_tile": 1024,
        "train_fraction": 0.7,
        "buffer_m": 2.5,
        "resampling_seed": 0,
    },
    "training": {
        "seeds": [20260716, 20260717, 20260718],
        "initialization": "scratch",
        "synthetic_samples": 200,
        "synthetic_seed_start": 50000,
        "class_weight": "none",
        "epochs": 60,
        "batch_size": 8,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "scheduler_step": 20,
        "scheduler_gamma": 0.5,
        "selection_metric": "macro_tile_wood_iou",
    },
    "pointnet_inference": {
        "window_size_m": 2.5,
        "stride_m": 1.25,
        "model_points": 2048,
        "query_points": 1024,
        "seed": 0,
    },
    "external": {
        "provider": "Zenodo",
        "record_id": 6831378,
        "doi": "10.5281/zenodo.6831378",
        "license": "CC-BY-4.0",
        "expected_trees": 10,
        "concatenation_order": ["wood", "leaf"],
    },
    "demol": {
        "record_id": 4557401,
        "expected_trees": 65,
        "max_points": 20000,
        "sampling_seed": 0,
        "qsm_seed": 0,
        "qsm_algorithm": "ransac_dbh_maxz_height_taper_volume",
    },
    "statistics": {
        "resamples": 10000,
        "seed": 20260716,
        "confidence": 0.95,
    },
}


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} must equal {expected!r}, got {actual!r}")


def load_protocol(path: str | Path) -> dict[str, Any]:
    """Load and strictly validate the fixed independent-evaluation contract."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"protocol must be a JSON object, got {type(payload).__name__}")

    _require_equal(set(payload), EXPECTED_TOP_LEVEL, "protocol sections")
    _require_equal(payload["schema_version"], "1", "schema_version")
    _require_equal(
        payload["experiment_id"],
        "pointnet-independent-eval-2026-07-16",
        "experiment_id",
    )

    for section, expected_fields in EXPECTED_SECTIONS.items():
        actual_fields = payload[section]
        if not isinstance(actual_fields, dict):
            raise ValueError(f"{section} must be a JSON object, got {type(actual_fields).__name__}")
        _require_equal(set(actual_fields), set(expected_fields), f"{section} fields")
        for field, expected in expected_fields.items():
            _require_equal(actual_fields[field], expected, f"{section}.{field}")

    return payload
