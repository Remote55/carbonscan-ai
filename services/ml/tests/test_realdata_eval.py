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
