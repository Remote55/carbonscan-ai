"""Tests for real-world wood/leaf IoU evaluation (spec 2026-06-26)."""

from __future__ import annotations

import numpy as np

from pipeline.realdata_eval import load_labelled_cloud


def test_load_labelled_cloud_maps_wood_labels(tmp_path):
    # cols: x y z label   (label 1 == wood, 0 == leaf for this fixture)
    f = tmp_path / "tree.txt"
    f.write_text("0 0 0 1\n1 1 1 0\n2 2 2 1\n")
    points, gt = load_labelled_cloud(f, label_col=3, wood_labels=[1])
    assert points.shape == (3, 3)
    assert points.dtype == np.float64
    assert gt.tolist() == [0, 1, 0]  # label 1 -> wood(0); label 0 -> leaf(1)
    assert gt.dtype == np.uint8


def test_derive_labels_from_woodonly(tmp_path):
    full = tmp_path / "full.txt"
    full.write_text("0 0 0\n1 0 0\n2 0 0\n3 0 0\n4 0 0\n5 0 0\n")
    wood = tmp_path / "wood.txt"
    wood.write_text("0 0 0\n2 0 0\n4 0 0\n")  # points 0,2,4 are wood
    from pipeline.realdata_eval import derive_labels_from_woodonly

    points, gt = derive_labels_from_woodonly(full, wood, tol=1e-6)
    assert points.shape == (6, 3)
    assert gt.tolist() == [0, 1, 0, 1, 0, 1]  # matched -> wood(0), else leaf(1)
