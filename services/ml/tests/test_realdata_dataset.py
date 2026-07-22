"""Tests for the real-data (Wan) -> PointNet++ training-sample converter."""

from __future__ import annotations

import json
from pathlib import PurePosixPath, PureWindowsPath

import numpy as np
import pytest

from pipeline.provenance import sha256_file, sha256_ndarray
from training import realdata_dataset
from training.realdata_dataset import spatial_split, tile_samples


def _tiny_protocol():
    return {
        "wan": {
            "source_record": "tiny-wan-fixture",
            "files": ["plot_a.txt", "plot_b.txt"],
            "n_off": 1,
            "per": 10_000,
            "tile_m": 1.0,
            "points_per_tile": 4,
            "min_points_per_tile": 4,
            "train_fraction": 0.5,
            "buffer_m": 1.0,
            "resampling_seed": 7,
        }
    }


def _write_tiny_wan_plots(tmp_path):
    paths = []
    for filename, y_offset in (("plot_a.txt", 0.0), ("plot_b.txt", 0.2)):
        path = tmp_path / filename
        lines = []
        for grid_x in range(5):
            for point_index in range(6):
                x = grid_x + 0.1 + point_index * 0.01
                y = y_offset + 0.1 + point_index * 0.01
                z = 0.2 * point_index
                label = point_index % 2
                lines.append(f"{x} {y} {z} 0 0 0 {label}\n")
        path.write_text("".join(lines), encoding="utf-8")
        paths.append(path)
    return list(reversed(paths))


def _replace_first_wan_row(path, row):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines[0] = f"{row}\n"
    path.write_text("".join(lines), encoding="utf-8")


def _assert_path_private(value, forbidden_root):
    if isinstance(value, dict):
        for child in value.values():
            _assert_path_private(child, forbidden_root)
        return
    if isinstance(value, list):
        for child in value:
            _assert_path_private(child, forbidden_root)
        return
    if not isinstance(value, str):
        return

    normalized = value.replace("\\", "/")
    assert not PurePosixPath(normalized).is_absolute()
    assert not PureWindowsPath(value).is_absolute()
    assert forbidden_root.resolve().as_posix().casefold() not in normalized.casefold()


def _build_tiny_evidence(tmp_path, sources, protocol=None):
    output = tmp_path / "output"
    output.mkdir()
    return realdata_dataset.build_evidence_dataset(
        sources,
        output / "train.npz",
        output / "dev.npz",
        output / "manifest.json",
        protocol=_tiny_protocol() if protocol is None else protocol,
        repo_root=tmp_path,
    )


def _grid_cloud(n_per_tile=2000):
    """A cloud spanning 4 tiles along x (tile=2.5 m), half wood / half leaf."""
    rng = np.random.default_rng(0)
    pts, lab = [], []
    for tx in range(4):
        x = rng.uniform(tx * 2.5, tx * 2.5 + 2.5, n_per_tile)
        y = rng.uniform(0.0, 2.5, n_per_tile)
        z = rng.uniform(0.0, 5.0, n_per_tile)
        pts.append(np.column_stack([x, y, z]))
        lab.append(np.arange(n_per_tile) % 2)  # 0=wood, 1=leaf
    return np.vstack(pts), np.concatenate(lab).astype(np.uint8)


def test_tile_samples_shapes_and_labels():
    pts, lab = _grid_cloud()
    x, y, centers = tile_samples(pts, lab, tile=2.5, n_points=64, min_pts=500)
    assert x.shape == (4, 64, 3)
    assert y.shape == (4, 64)
    assert x.dtype == np.float32
    assert y.dtype == np.int64
    assert set(np.unique(y).tolist()) <= {0, 1}
    assert centers.shape == (4, 2)


def test_tile_samples_normalized_to_unit_sphere():
    pts, lab = _grid_cloud()
    x, _, _ = tile_samples(pts, lab, tile=2.5, n_points=128, min_pts=500)
    for sample in x:
        assert np.allclose(sample.mean(axis=0), 0.0, atol=1e-4)
        assert np.max(np.linalg.norm(sample, axis=1)) <= 1.0 + 1e-4


def test_tile_samples_skips_small_tiles():
    pts, lab = _grid_cloud()
    x, _y, centers = tile_samples(pts, lab, tile=2.5, n_points=64, min_pts=10_000)
    assert x.shape[0] == 0
    assert centers.shape[0] == 0


def test_spatial_split_buffer_separates_train_and_test():
    n = 10
    x = np.zeros((n, 4, 3), np.float32)
    y = np.zeros((n, 4), np.int64)
    centers = np.zeros((n, 2))
    centers[:, 0] = np.arange(n)  # x-centers 0..9
    xtr, ytr, xte, yte = spatial_split(x, y, centers, frac=0.5, buffer=2.0, axis=0)
    # cut = 0 + 0.5*9 = 4.5 ; train x < 3.5 -> {0,1,2,3}; test x > 5.5 -> {6,7,8,9}; drop {4,5}
    assert len(xtr) == 4
    assert len(xte) == 4
    assert len(ytr) == 4
    assert len(yte) == 4


def test_build_evidence_dataset_records_every_tile_without_absolute_paths(tmp_path):
    protocol = _tiny_protocol()
    sources = _write_tiny_wan_plots(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    returned = realdata_dataset.build_evidence_dataset(
        sources,
        first / "train.npz",
        first / "dev.npz",
        first / "manifest.json",
        protocol=protocol,
        repo_root=tmp_path,
    )
    realdata_dataset.build_evidence_dataset(
        sources,
        second / "train.npz",
        second / "dev.npz",
        second / "manifest.json",
        protocol=protocol,
        repo_root=tmp_path,
    )

    a = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    b = json.loads((second / "manifest.json").read_text(encoding="utf-8"))
    assert a == b
    assert returned == a
    assert [source["filename"] for source in a["sources"]] == protocol["wan"]["files"]
    assert [source["sha256"] for source in a["sources"]] == [
        sha256_file(tmp_path / filename) for filename in protocol["wan"]["files"]
    ]
    assert {row["split"] for row in a["tiles"]} <= {
        "train",
        "dev",
        "dropped_buffer",
    }
    assert all("selected_indices_sha256" in row for row in a["tiles"])
    assert all(
        set(row)
        == {
            "tile_id",
            "source_id",
            "grid_x",
            "grid_y",
            "center_x",
            "center_y",
            "raw_points",
            "selected_indices_sha256",
            "split",
        }
        for row in a["tiles"]
    )
    expected_selected = np.arange(6, dtype=np.int64)[
        np.random.default_rng(7).choice(6, size=4, replace=False)
    ]
    first_tile = next(
        row
        for row in a["tiles"]
        if row["source_id"] == "plot_a"
        and row["grid_x"] == 0
        and row["grid_y"] == 0
    )
    assert first_tile["selected_indices_sha256"] == sha256_ndarray(
        expected_selected,
        "<i8",
    )
    _assert_path_private(a, tmp_path)

    for split_name in ("train", "dev"):
        output = first / f"{split_name}.npz"
        with np.load(output) as arrays:
            assert a["outputs"][split_name]["sha256"] == sha256_file(output)
            assert a["outputs"][split_name]["x_sha256"] == sha256_ndarray(
                arrays["x"], "<f4"
            )
            assert a["outputs"][split_name]["y_sha256"] == sha256_ndarray(
                arrays["y"], "<i8"
            )

    train_ids = {row["tile_id"] for row in a["tiles"] if row["split"] == "train"}
    dev_ids = {row["tile_id"] for row in a["tiles"] if row["split"] == "dev"}
    assert train_ids
    assert dev_ids
    assert train_ids.isdisjoint(dev_ids)
    assert "leakage-free" not in realdata_dataset.__doc__
    assert "no tree appears" not in realdata_dataset.__doc__


def test_build_evidence_dataset_rejects_source_config_mismatch(tmp_path):
    sources = _write_tiny_wan_plots(tmp_path)
    with pytest.raises(ValueError, match="source filenames"):
        _build_tiny_evidence(tmp_path, sources[:-1])


@pytest.mark.parametrize("source_record", ["/private/wan.txt", r"C:\private\wan.txt"])
def test_build_evidence_dataset_rejects_absolute_source_record(
    tmp_path, source_record
):
    sources = _write_tiny_wan_plots(tmp_path)
    protocol = _tiny_protocol()
    protocol["wan"]["source_record"] = source_record

    with pytest.raises(ValueError, match=r"absolute.*source_record"):
        _build_tiny_evidence(tmp_path, sources, protocol)

    assert list((tmp_path / "output").iterdir()) == []


def test_build_evidence_dataset_allows_sources_outside_repo_root_without_leak(tmp_path):
    repo_root = tmp_path / "feature-worktree"
    source_root = tmp_path / "authorized-wan-data"
    output = repo_root / "output"
    repo_root.mkdir()
    source_root.mkdir()
    output.mkdir()
    sources = _write_tiny_wan_plots(source_root)

    manifest = realdata_dataset.build_evidence_dataset(
        sources,
        output / "train.npz",
        output / "dev.npz",
        output / "manifest.json",
        protocol=_tiny_protocol(),
        repo_root=repo_root,
    )

    _assert_path_private(manifest, repo_root)
    _assert_path_private(manifest, source_root)
    assert (output / "train.npz").is_file()
    assert (output / "dev.npz").is_file()
    assert (output / "manifest.json").is_file()


@pytest.mark.parametrize("invalid_label", ["2", "1.5", "256"])
def test_build_evidence_dataset_rejects_non_binary_labels(tmp_path, invalid_label):
    sources = _write_tiny_wan_plots(tmp_path)
    path = tmp_path / "plot_a.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            " 0\n", f" {invalid_label}\n", 1
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="binary labels"):
        _build_tiny_evidence(tmp_path, sources)


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ("0 0 0", "columns"),
        ("0 0 0 0 0 0 leaf", "numeric XYZ and label"),
        ("nan 0 0 0 0 0 0", "finite XYZ and label"),
    ],
)
def test_build_evidence_dataset_rejects_malformed_rows_with_context(
    tmp_path, row, reason
):
    sources = _write_tiny_wan_plots(tmp_path)
    _replace_first_wan_row(tmp_path / "plot_a.txt", row)

    with pytest.raises(
        ValueError,
        match=rf"plot_a\.txt.*line 1.*{reason}",
    ):
        _build_tiny_evidence(tmp_path, sources)


def test_build_evidence_dataset_rejects_empty_split(tmp_path):
    sources = _write_tiny_wan_plots(tmp_path)
    protocol = _tiny_protocol()
    protocol["wan"]["buffer_m"] = 100.0
    with pytest.raises(ValueError, match="empty train/dev split"):
        _build_tiny_evidence(tmp_path, sources, protocol)


def test_build_evidence_dataset_requires_train_and_dev_from_every_source(tmp_path):
    sources = _write_tiny_wan_plots(tmp_path)
    path = tmp_path / "plot_a.txt"
    kept_rows = [
        row
        for row in path.read_text(encoding="utf-8").splitlines()
        if float(row.split()[0]) < 2.0
    ]
    path.write_text("\n".join(kept_rows) + "\n", encoding="utf-8")
    protocol = _tiny_protocol()
    protocol["wan"]["train_fraction"] = 0.7

    with pytest.raises(ValueError, match=r"plot_a.*train and dev"):
        _build_tiny_evidence(tmp_path, sources, protocol)


def test_build_evidence_dataset_rejects_duplicate_tile_ids(tmp_path):
    original_sources = _write_tiny_wan_plots(tmp_path)
    content = original_sources[0].read_text(encoding="utf-8")
    sources = [tmp_path / "same.txt", tmp_path / "same.csv"]
    for source in sources:
        source.write_text(content, encoding="utf-8")
    protocol = _tiny_protocol()
    protocol["wan"]["files"] = [source.name for source in sources]

    with pytest.raises(ValueError, match="duplicate tile IDs"):
        _build_tiny_evidence(tmp_path, sources, protocol)


def test_build_evidence_dataset_rejects_resolved_output_alias_before_write(tmp_path):
    sources = _write_tiny_wan_plots(tmp_path)
    output = tmp_path / "output"
    nested = output / "nested"
    nested.mkdir(parents=True)
    shared = output / "shared.npz"
    shared.write_bytes(b"do-not-overwrite")
    alias = nested / ".." / "shared.npz"
    manifest = output / "manifest.json"

    with pytest.raises(ValueError, match="distinct output paths"):
        realdata_dataset.build_evidence_dataset(
            sources,
            shared,
            alias,
            manifest,
            protocol=_tiny_protocol(),
            repo_root=tmp_path,
        )

    assert shared.read_bytes() == b"do-not-overwrite"
    assert not manifest.exists()


def test_build_evidence_dataset_rejects_output_aliasing_raw_source_before_write(
    tmp_path,
):
    sources = _write_tiny_wan_plots(tmp_path)
    raw_source = tmp_path / "plot_a.txt"
    original_raw = raw_source.read_bytes()
    output = tmp_path / "artifacts"
    nested = tmp_path / "nested"
    output.mkdir()
    nested.mkdir()
    raw_alias = nested / ".." / "plot_a.txt"

    with pytest.raises(ValueError, match=r"output paths.*source files"):
        realdata_dataset.build_evidence_dataset(
            sources,
            output / "train.npz",
            output / "dev.npz",
            raw_alias,
            protocol=_tiny_protocol(),
            repo_root=tmp_path,
        )

    assert raw_source.read_bytes() == original_raw
    assert list(output.iterdir()) == []
