"""Tests for the photogrammetry pipeline (COLMAP -> OpenMVS -> .ply).

Only the dependency-free parts are unit-tested here: image discovery and the
construction of the COLMAP / OpenMVS command lines. The actual subprocess runs
need the external COLMAP + OpenMVS binaries (validated via --dry-run by hand).
"""

from __future__ import annotations

import pytest

from photogrammetry.colmap_wrapper import build_sfm_commands, find_images
from photogrammetry.openmvs_wrapper import build_densify_commands
from photogrammetry.run import REQUIRED_BINARIES, check_binaries, photos_to_pointcloud

# --- find_images -----------------------------------------------------------


def test_find_images_picks_only_images(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.JPG").write_bytes(b"x")
    (tmp_path / "c.png").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("x")
    imgs = find_images(tmp_path)
    assert len(imgs) == 3
    assert all(p.suffix.lower() in {".jpg", ".jpeg", ".png"} for p in imgs)


def test_find_images_sorted(tmp_path):
    for n in ["c.jpg", "a.jpg", "b.jpg"]:
        (tmp_path / n).write_bytes(b"x")
    assert [p.name for p in find_images(tmp_path)] == ["a.jpg", "b.jpg", "c.jpg"]


def test_find_images_empty_raises(tmp_path):
    with pytest.raises(ValueError):
        find_images(tmp_path)


# --- build_sfm_commands (COLMAP) -------------------------------------------


def test_build_sfm_commands_step_order(tmp_path):
    cmds = build_sfm_commands(tmp_path / "images", tmp_path / "work", use_gpu=True)
    assert all(c[0] == "colmap" for c in cmds)
    assert [c[1] for c in cmds] == [
        "feature_extractor",
        "exhaustive_matcher",
        "mapper",
        "image_undistorter",
    ]


def test_build_sfm_gpu_flag(tmp_path):
    gpu = build_sfm_commands(tmp_path / "i", tmp_path / "w", use_gpu=True)[0]
    cpu = build_sfm_commands(tmp_path / "i", tmp_path / "w", use_gpu=False)[0]
    assert gpu[gpu.index("--SiftExtraction.use_gpu") + 1] == "1"
    assert cpu[cpu.index("--SiftExtraction.use_gpu") + 1] == "0"


# --- build_densify_commands (OpenMVS) --------------------------------------


def test_build_densify_commands_programs(tmp_path):
    cmds = build_densify_commands(tmp_path / "work", tmp_path / "out.ply")
    progs = [c[0] for c in cmds]
    assert "InterfaceCOLMAP" in progs
    assert "DensifyPointCloud" in progs


# --- orchestrator (run.py) -------------------------------------------------


def test_check_binaries_reports_all_required():
    b = check_binaries()
    assert set(b) == set(REQUIRED_BINARIES)


def test_dry_run_needs_no_binaries(tmp_path):
    imgs = tmp_path / "imgs"
    imgs.mkdir()
    for i in range(3):
        (imgs / f"{i}.jpg").write_bytes(b"x")
    out = photos_to_pointcloud(imgs, tmp_path / "out.ply", dry_run=True)
    assert str(out).endswith("out.ply")
