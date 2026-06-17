"""Tests for Thai field ground-truth validation helpers (Sprint P1 / G1).

Pure logic only (no matplotlib) so it runs on any machine. The plotting +
CLI live in notebooks/validate_thai.py.
"""

from __future__ import annotations

import numpy as np

from pipeline.field_eval import (
    circumference_to_dbh,
    error_metrics,
    load_point_cloud,
    normalize_ground,
    predict_tree,
)

# --- circumference_to_dbh --------------------------------------------------


def test_circumference_to_dbh():
    # tape girth of a 20 cm-DBH stem is π·20 ≈ 62.83 cm
    assert abs(circumference_to_dbh(np.pi * 20.0) - 20.0) < 1e-9


def test_circumference_to_dbh_zero_or_negative():
    assert circumference_to_dbh(0.0) == 0.0
    assert circumference_to_dbh(-5.0) == 0.0


# --- error_metrics ---------------------------------------------------------


def test_error_metrics_perfect():
    m = error_metrics([10.0, 20.0], [10.0, 20.0])
    assert m["n"] == 2
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["abs_mean_pct"] == 0.0


def test_error_metrics_known_values():
    # pred 11 vs gt 10 -> +1 (+10%);  pred 18 vs gt 20 -> -2 (-10%)
    m = error_metrics([11.0, 18.0], [10.0, 20.0])
    assert abs(m["mae"] - 1.5) < 1e-9          # (|+1| + |-2|) / 2
    assert abs(m["rmse"] - np.sqrt((1 + 4) / 2)) < 1e-9
    assert abs(m["abs_mean_pct"] - 10.0) < 1e-9  # (10 + 10) / 2
    assert abs(m["mean_pct"] - 0.0) < 1e-9       # (+10 - 10) / 2


def test_error_metrics_empty():
    m = error_metrics([], [])
    assert m["n"] == 0


# --- load_point_cloud / normalize_ground -----------------------------------


def test_load_point_cloud_txt(tmp_path):
    p = tmp_path / "tree.txt"
    np.savetxt(p, np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=float))
    pts = load_point_cloud(p)
    assert pts.shape == (3, 3)
    assert pts.dtype == np.float64


def test_load_point_cloud_unsupported(tmp_path):
    p = tmp_path / "tree.weird"
    p.write_text("nope")
    try:
        load_point_cloud(p)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_normalize_ground_sets_min_z_zero():
    pts = np.array([[0, 0, 5.0], [1, 1, 7.0], [2, 2, 6.0]])
    out = normalize_ground(pts)
    assert abs(out[:, 2].min()) < 1e-9


# --- predict_tree (integration on a synthetic tree) ------------------------


def test_predict_tree_on_synthetic_is_plausible():
    from pipeline.synthetic import generate_synthetic_plot

    pts, _, _ = generate_synthetic_plot(n_trees=1, seed=1)
    pred = predict_tree(normalize_ground(pts))
    assert set(pred) >= {"dbh_cm", "height_m", "volume_m3", "fit_quality"}
    assert pred["dbh_cm"] > 0
    assert 5.0 < pred["height_m"] < 30.0
    assert pred["volume_m3"] > 0
