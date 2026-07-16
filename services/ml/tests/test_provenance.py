"""Tests for auditable pipeline provenance."""

from __future__ import annotations

from copy import deepcopy

import numpy as np

from pipeline.provenance import (
    ALGORITHM_MAP,
    hash_points,
    normalized_payload,
    normalized_sha256,
    sha256_bytes,
)


def _evidence() -> dict:
    return {
        "schema_version": "1",
        "run": {
            "input_sha256": "a" * 64,
            "git_commit": "0036996",
            "pipeline_version": "0.3.0",
            "backend": "tlsep",
            "checkpoint_sha256": None,
        },
        "algorithms": dict(ALGORITHM_MAP),
        "results": {"dbh_cm": 10.25, "height_m": 8.5, "volume_m3": 0.12},
        "runtime": {
            "created_at": "2026-07-16T00:00:00Z",
            "output_dir": "C:/first",
        },
    }


def test_algorithm_map_names_actual_implementations():
    assert ALGORITHM_MAP == {
        "ground_segmentation": "percentile_grid",
        "height_normalization": "knn_idw",
        "chm": "max_z_morphology",
        "tree_segmentation": "watershed",
        "wood_leaf": "tlsep",
        "qsm": "ransac_dbh_maxz_height_taper_volume",
        "species": "stub",
        "allometric": "species_db_or_chave_fallback",
    }


def test_normalized_hash_ignores_only_runtime_fields():
    first = _evidence()
    second = deepcopy(first)
    second["runtime"] = {
        "created_at": "2026-07-17T00:00:00Z",
        "output_dir": "D:/second",
    }
    assert normalized_payload(first) == normalized_payload(second)
    assert normalized_sha256(first) == normalized_sha256(second)


def test_normalized_hash_changes_when_algorithm_or_result_changes():
    first = _evidence()
    changed_result = deepcopy(first)
    changed_result["results"]["dbh_cm"] = 10.26
    assert normalized_sha256(first) != normalized_sha256(changed_result)

    changed_algorithm = deepcopy(first)
    changed_algorithm["algorithms"]["wood_leaf"] = "pointnet"
    assert normalized_sha256(first) != normalized_sha256(changed_algorithm)


def test_hash_points_is_shape_and_dtype_stable():
    points = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
    assert hash_points(points) == hash_points(points.astype(np.float64))
    assert hash_points(points) == sha256_bytes(points.astype("<f8").tobytes(order="C"))


def test_hash_points_rejects_non_xyz_shape():
    points = np.array([[1, 2], [3, 4]], dtype=np.float64)
    try:
        hash_points(points)
    except ValueError as exc:
        assert "Expected points (N, 3)" in str(exc)
    else:
        raise AssertionError("hash_points accepted a non-XYZ array")
