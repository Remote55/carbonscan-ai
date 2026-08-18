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

DEMOL_TREE_IDS = [
    "FEXC-01",
    "FEXC-02",
    "FEXC-03",
    "FEXC-04",
    "FEXC-05",
    "FEXC-06",
    "FEXC-07",
    "FEXC-08",
    "FEXC-09",
    "FEXC-10",
    "FEXC-11",
    "FEXC-13",
    "FEXC-14",
    "FEXC-15",
    "FEXC-16",
    "FSYL-01",
    "FSYL-02",
    "FSYL-03",
    "FSYL-04",
    "FSYL-05",
    "FSYL-06",
    "FSYL-07",
    "FSYL-08",
    "FSYL-09",
    "FSYL-10",
    "FSYL-11",
    "FSYL-12",
    "FSYL-13",
    "FSYL-14",
    "FSYL-15",
    "LXDC-01",
    "LXDC-02",
    "LXDC-03",
    "LXDC-04",
    "LXDC-05",
    "PSYLA-01",
    "PSYLA-02",
    "PSYLA-03",
    "PSYLA-04",
    "PSYLA-05",
    "PSYLA-06",
    "PSYLA-07",
    "PSYLA-08",
    "PSYLA-09",
    "PSYLA-10",
    "PSYLA-11",
    "PSYLA-12",
    "PSYLA-13",
    "PSYLA-14",
    "PSYLA-15",
    "PSYLB-01",
    "PSYLB-02",
    "PSYLB-03",
    "PSYLB-04",
    "PSYLB-05",
    "PSYLB-06",
    "PSYLB-07",
    "PSYLB-08",
    "PSYLB-09",
    "PSYLB-10",
    "PSYLB-11",
    "PSYLB-12",
    "PSYLB-13",
    "PSYLB-14",
    "PSYLB-15",
]

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
        "optimizer": "Adam",
        "epochs": 60,
        "batch_size": 8,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "scheduler_step": 20,
        "scheduler_gamma": 0.5,
        "selection_metric": "macro_tile_wood_iou",
        "selection_tie_break": "lowest_seed",
    },
    "pointnet_inference": {
        "window_size_m": 2.5,
        "stride_m": 1.25,
        "model_points": 2048,
        "query_points": 1024,
        "seed": 0,
        "required_coverage": 1.0,
    },
    "external": {
        "provider": "Zenodo",
        "record_id": 6831378,
        "doi": "10.5281/zenodo.6831378",
        "license": "CC-BY-4.0",
        "expected_trees": 10,
        "concatenation_order": ["wood", "leaf"],
    },
    # NOTE: the licence and DOI deliberately do NOT live here. This dict is the
    # frozen contract that protocol.json is validated against field for field,
    # and protocol.json is hash-pinned by the sealed independent evaluation, so
    # adding a key here invalidates that evidence. The Demol record is CC BY 4.0
    # (10.5281/zenodo.4557401) and that is recorded in docs/ml/DATASETS.md.
    "demol": {
        "record_id": 4557401,
        "expected_trees": 65,
        "tree_ids": DEMOL_TREE_IDS,
        "max_points": 20000,
        "sampling_seed": 0,
        "qsm_seed": 0,
        "qsm_algorithm": "ransac_dbh_maxz_height_taper_volume",
    },
    "statistics": {
        "method": "paired_percentile",
        "resampling_unit": "tree",
        "resamples": 10000,
        "seed": 20260716,
        "confidence": 0.95,
    },
}


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{label} must equal {expected!r}, got {actual!r}")

    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError(f"{label} must equal {expected!r}, got {actual!r}")
        for key, expected_value in expected.items():
            _require_equal(actual[key], expected_value, label)
        return

    if isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"{label} must equal {expected!r}, got {actual!r}")
        for actual_value, expected_value in zip(actual, expected, strict=True):
            _require_equal(actual_value, expected_value, label)
        return

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
