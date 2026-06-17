"""Tests for sectional (stacked-cylinder) stem volume — Sprint P1 / G3.

The Phase-1 volume was a single taper equation (~18.8% error on Belgium).
The sectional method slices wood points by height, fits a circle per slice,
and sums cylinder volumes — capturing the real taper profile. We validate it
on synthetic shapes whose true volume is known analytically.
"""

from __future__ import annotations

import numpy as np

from pipeline.qsm import estimate_volume_sectional


def _make_cylinder(radius, height, n_layers=60, per_ring=80, z0=0.0, seed=0):
    """Surface points of a vertical cylinder (radius constant with height)."""
    rng = np.random.default_rng(seed)
    pts = []
    for z in np.linspace(z0, z0 + height, n_layers):
        ang = rng.uniform(0, 2 * np.pi, per_ring)
        x = radius * np.cos(ang)
        y = radius * np.sin(ang)
        pts.append(np.column_stack([x, y, np.full(per_ring, z)]))
    return np.vstack(pts)


def _make_cone(base_radius, height, n_layers=60, per_ring=80, z0=0.0, seed=0):
    """Surface points of a cone tapering from base_radius (z0) to 0 (top)."""
    rng = np.random.default_rng(seed)
    pts = []
    for z in np.linspace(z0, z0 + height, n_layers):
        r = base_radius * (1.0 - (z - z0) / height)
        if r <= 0:
            continue
        ang = rng.uniform(0, 2 * np.pi, per_ring)
        pts.append(np.column_stack([r * np.cos(ang), r * np.sin(ang), np.full(per_ring, z)]))
    return np.vstack(pts)


def test_sectional_recovers_cylinder_volume():
    pts = _make_cylinder(radius=0.2, height=10.0)
    vol, n_cyl = estimate_volume_sectional(pts, slice_thickness_m=0.5)
    true_vol = np.pi * 0.2**2 * 10.0  # ≈ 1.257 m³
    assert n_cyl > 0
    assert abs(vol - true_vol) / true_vol < 0.15


def test_sectional_recovers_cone_volume():
    pts = _make_cone(base_radius=0.3, height=12.0)
    vol, _ = estimate_volume_sectional(pts, slice_thickness_m=0.4)
    true_vol = (1.0 / 3.0) * np.pi * 0.3**2 * 12.0  # cone ≈ 1.131 m³
    assert abs(vol - true_vol) / true_vol < 0.20


def test_sectional_beats_taper_on_cone():
    # A strongly tapered stem is exactly where a single form-factor errs most.
    from pipeline.qsm import estimate_volume_taper

    pts = _make_cone(base_radius=0.3, height=12.0)
    true_vol = (1.0 / 3.0) * np.pi * 0.3**2 * 12.0
    sect_vol, _ = estimate_volume_sectional(pts, slice_thickness_m=0.4)
    # taper using the cone's base DBH (60 cm) — overestimates badly
    taper_vol = estimate_volume_taper(dbh_cm=60.0, height_m=12.0)
    assert abs(sect_vol - true_vol) < abs(taper_vol - true_vol)


def test_sectional_zero_for_too_short():
    pts = _make_cylinder(radius=0.1, height=0.1, n_layers=3)
    vol, n_cyl = estimate_volume_sectional(pts, slice_thickness_m=0.5)
    assert vol == 0.0
    assert n_cyl == 0


def test_sectional_is_deterministic():
    pts = _make_cylinder(radius=0.15, height=8.0)
    v1, _ = estimate_volume_sectional(pts, slice_thickness_m=0.5, seed=3)
    v2, _ = estimate_volume_sectional(pts, slice_thickness_m=0.5, seed=3)
    assert v1 == v2
