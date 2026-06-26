"""Tests for segmented PLY export (Sprint P1 / ply-viewer spec §5)."""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.ply_export import read_segmented_ply, write_segmented_ply


def test_roundtrip(tmp_path):
    pts = np.array([[0, 0, 0], [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=float)
    cls = np.array([0, 1, 2], dtype=np.uint8)
    out = write_segmented_ply(pts, cls, tmp_path / "a.ply")
    rpts, rcls = read_segmented_ply(out)
    assert rpts.shape == (3, 3)
    assert np.allclose(rpts, pts, atol=1e-5)
    assert np.array_equal(rcls, cls)


def test_header_binary_le_and_class_property(tmp_path):
    out = write_segmented_ply(np.zeros((2, 3)), np.zeros(2, np.uint8), tmp_path / "b.ply")
    head = out.read_bytes()[:256].decode("ascii", "ignore")
    assert "format binary_little_endian" in head
    assert "property uchar class" in head
    assert "element vertex 2" in head


def test_mismatched_lengths_raise(tmp_path):
    with pytest.raises(ValueError):
        write_segmented_ply(np.zeros((3, 3)), np.zeros(2, np.uint8), tmp_path / "c.ply")


def test_process_points_writes_segmented_ply_with_three_classes(tmp_path):
    from pipeline import synthetic
    from pipeline.main import process_points

    pts, _, _ = synthetic.generate_synthetic_plot(
        n_trees=3, plot_size_m=20.0, ground_z_variation=0.8,
        ground_point_density=20.0, leaves_per_tree=1500, seed=42,
    )
    out = tmp_path / "seg.ply"
    process_points(pts, segmented_ply_out=str(out))
    assert out.exists()
    rpts, rcls = read_segmented_ply(out)
    assert len(rpts) == len(pts)  # whole plot exported
    present = set(np.unique(rcls).tolist())
    assert present.issubset({0, 1, 2})
    assert {0, 1, 2}.issubset(present)  # wood + leaf + ground all present
