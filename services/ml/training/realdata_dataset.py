"""Convert labelled Wan 2021 TLS plots into PointNet++ samples.

The converter seek-samples each large source, tiles its XY extent, and applies a
deterministic spatial train/dev split with a buffer. The split is a spatial
separation proxy; it does not prove that biological tree crowns are independent.
"""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Sequence

import numpy as np

from pipeline.provenance import sha256_file, sha256_ndarray, write_canonical_json
from training.woodleaf_dataset import _resample_indices, normalize_points


def _is_cross_platform_absolute(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return PurePosixPath(normalized).is_absolute() or PureWindowsPath(
        value
    ).is_absolute()


def _validate_manifest_path_privacy(value: Any, *, repo_root: Path) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _validate_manifest_path_privacy(child, repo_root=repo_root)
        return
    if isinstance(value, list):
        for child in value:
            _validate_manifest_path_privacy(child, repo_root=repo_root)
        return
    if not isinstance(value, str):
        return

    normalized = value.replace("\\", "/")
    if _is_cross_platform_absolute(value):
        raise ValueError(f"manifest cannot contain absolute path {value!r}")
    if repo_root.as_posix().casefold() in normalized.casefold():
        raise ValueError("manifest cannot contain repo_root")


def _tile_samples_with_records(
    points: np.ndarray,
    labels: np.ndarray,
    *,
    source_id: str,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    seed: int = 0,
    frac: float = 0.7,
    buffer: float = 2.5,
    axis: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    """Tile one seek-sampled source and retain stable tile provenance."""
    points = np.asarray(points, dtype=np.float64)
    labels = np.asarray(labels)
    gx = np.floor(points[:, 0] / tile).astype(np.int64)
    gy = np.floor(points[:, 1] / tile).astype(np.int64)
    grid = np.column_stack((gx, gy))
    rng = np.random.default_rng(seed)

    xs, ys, centers = [], [], []
    record_inputs: list[tuple[int, int, np.ndarray, np.ndarray]] = []
    for grid_x, grid_y in np.unique(grid, axis=0):
        idx = np.where((gx == grid_x) & (gy == grid_y))[0]
        if len(idx) < min_pts:
            continue
        sel = idx[_resample_indices(len(idx), n_points, rng)]
        center = points[idx, :2].mean(axis=0)
        xs.append(normalize_points(points[sel]).astype(np.float32))
        ys.append(labels[sel].astype(np.int64))
        centers.append(center)
        record_inputs.append((int(grid_x), int(grid_y), idx, sel))

    if not xs:
        return (
            np.zeros((0, n_points, 3), np.float32),
            np.zeros((0, n_points), np.int64),
            np.zeros((0, 2), np.float64),
            [],
        )

    x = np.stack(xs)
    y = np.stack(ys)
    center_array = np.stack(centers)
    assignments = spatial_split_assignments(
        center_array,
        frac=frac,
        buffer=buffer,
        axis=axis,
    )
    records = []
    for (grid_x, grid_y, idx, sel), center, split_name in zip(
        record_inputs,
        center_array,
        assignments,
    ):
        records.append(
            {
                "tile_id": f"{source_id}:{grid_x}:{grid_y}",
                "source_id": source_id,
                "grid_x": int(grid_x),
                "grid_y": int(grid_y),
                "center_x": float(center[0]),
                "center_y": float(center[1]),
                "raw_points": int(len(idx)),
                "selected_indices_sha256": sha256_ndarray(sel, "<i8"),
                "split": str(split_name),
            }
        )
    return x, y, center_array, records


def tile_samples(
    points: np.ndarray,
    labels: np.ndarray,
    *,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Split a plot into cells and return normalized samples and XY centers."""
    x, y, centers, _records = _tile_samples_with_records(
        points,
        labels,
        source_id="source",
        tile=tile,
        n_points=n_points,
        min_pts=min_pts,
        seed=seed,
    )
    return x, y, centers


def spatial_split_assignments(
    centers: np.ndarray, *, frac: float, buffer: float, axis: int = 0
) -> np.ndarray:
    c = np.asarray(centers, dtype=np.float64)[:, axis]
    cut = float(c.min()) + frac * float(c.max() - c.min())
    split = np.full(len(c), "dropped_buffer", dtype="<U14")
    split[c < (cut - buffer / 2.0)] = "train"
    split[c > (cut + buffer / 2.0)] = "dev"
    return split


def spatial_split(
    x: np.ndarray,
    y: np.ndarray,
    centers: np.ndarray,
    *,
    frac: float = 0.7,
    buffer: float = 2.5,
    axis: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split samples into train/dev regions and omit the spatial buffer band."""
    assignments = spatial_split_assignments(
        centers,
        frac=frac,
        buffer=buffer,
        axis=axis,
    )
    train = assignments == "train"
    dev = assignments == "dev"
    return x[train], y[train], x[dev], y[dev]


def load_wan_plot(
    path: str | Path,
    *,
    label_col: int = 6,
    n_off: int = 3000,
    per: int = 1000,
) -> tuple[np.ndarray, np.ndarray]:
    """Seek-sample a Wan text plot into XYZ points and per-point labels."""
    path = Path(path)
    size = path.stat().st_size
    xyz: list[tuple[float, float, float]] = []
    lab: list[int] = []
    with path.open("rb") as stream:
        for offset_index in range(n_off):
            stream.seek(int(size * offset_index / n_off))
            if offset_index > 0:
                stream.readline()
            for line_number in range(1, per + 1):
                line = stream.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                context = (
                    f"{path.name}: offset {offset_index + 1}, line {line_number}"
                )
                parts = line.split()
                if len(parts) < label_col + 1:
                    raise ValueError(
                        f"{context}: expected at least {label_col + 1} columns, "
                        f"got {len(parts)}"
                    )
                try:
                    point = (float(parts[0]), float(parts[1]), float(parts[2]))
                    label = float(parts[label_col])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"{context}: expected numeric XYZ and label"
                    ) from exc
                if not np.isfinite((*point, label)).all():
                    raise ValueError(f"{context}: expected finite XYZ and label")
                if label not in (0.0, 1.0):
                    raise ValueError(
                        f"{context}: must contain only binary labels 0 and 1; "
                        f"got {label!r}"
                    )
                xyz.append(point)
                lab.append(int(label))
    return np.asarray(xyz, np.float64), np.asarray(lab, np.uint8)


def build_evidence_dataset(
    plot_paths: Sequence[str | Path],
    out_train: str | Path,
    out_dev: str | Path,
    manifest_path: str | Path,
    *,
    protocol: dict[str, Any],
    repo_root: str | Path,
) -> dict[str, Any]:
    """Build deterministic Wan train/dev artifacts and a canonical manifest."""
    out_train = Path(out_train).resolve()
    out_dev = Path(out_dev).resolve()
    manifest_path = Path(manifest_path).resolve()
    if len({out_train, out_dev, manifest_path}) != 3:
        raise ValueError("train, dev, and manifest must use distinct output paths")

    repo_root = Path(repo_root).resolve()
    wan = protocol["wan"]
    source_record = wan["source_record"]
    if _is_cross_platform_absolute(source_record):
        raise ValueError("absolute paths are forbidden in wan.source_record")

    expected_names = list(wan["files"])
    if any(
        _is_cross_platform_absolute(name)
        or "/" in name.replace("\\", "/")
        for name in expected_names
    ):
        raise ValueError("protocol source filenames must be logical basenames")

    resolved_sources = [Path(path).resolve() for path in plot_paths]
    for source in resolved_sources:
        try:
            source.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError(
                f"source path must be within repo_root: {source.name}"
            ) from exc
    supplied_names = [Path(path).name for path in plot_paths]
    if len(supplied_names) != len(set(supplied_names)) or sorted(
        supplied_names
    ) != sorted(expected_names):
        raise ValueError(
            "source filenames do not match protocol: "
            f"expected {expected_names!r}, got {supplied_names!r}"
        )
    source_by_name = {path.name: path for path in resolved_sources}
    ordered_sources = [(name, source_by_name[name]) for name in expected_names]
    config = {
        "n_off": wan["n_off"],
        "per": wan["per"],
        "tile_m": wan["tile_m"],
        "points_per_tile": wan["points_per_tile"],
        "min_points_per_tile": wan["min_points_per_tile"],
        "train_fraction": wan["train_fraction"],
        "buffer_m": wan["buffer_m"],
        "resampling_seed": wan["resampling_seed"],
    }
    train_x, train_y, dev_x, dev_y = [], [], [], []
    sources = []
    tiles: list[dict[str, Any]] = []
    for filename, path in ordered_sources:
        sources.append({"filename": filename, "sha256": sha256_file(path)})
        points, labels = load_wan_plot(
            path,
            label_col=6,
            n_off=config["n_off"],
            per=config["per"],
        )
        if not np.isin(np.unique(labels), (0, 1)).all():
            raise ValueError(f"{filename} must contain only binary labels 0 and 1")
        x, y, _centers, records = _tile_samples_with_records(
            points,
            labels,
            source_id=Path(filename).stem,
            tile=config["tile_m"],
            n_points=config["points_per_tile"],
            min_pts=config["min_points_per_tile"],
            seed=config["resampling_seed"],
            frac=config["train_fraction"],
            buffer=config["buffer_m"],
        )
        assignments = np.asarray([record["split"] for record in records])
        train_mask = assignments == "train"
        dev_mask = assignments == "dev"
        if not train_mask.any() or not dev_mask.any():
            raise ValueError(
                f"empty train/dev split for source {filename}; "
                "every source must contribute at least one train and dev tile"
            )
        train_x.append(x[train_mask])
        train_y.append(y[train_mask])
        dev_x.append(x[dev_mask])
        dev_y.append(y[dev_mask])
        tiles.extend(records)

    tile_ids = [record["tile_id"] for record in tiles]
    if len(tile_ids) != len(set(tile_ids)):
        raise ValueError("duplicate tile IDs in Wan evidence dataset")

    x_train = np.concatenate(train_x)
    y_train = np.concatenate(train_y)
    x_dev = np.concatenate(dev_x)
    y_dev = np.concatenate(dev_y)
    if len(x_train) == 0 or len(x_dev) == 0:
        raise ValueError("empty train/dev split after spatial assignment")

    np.savez_compressed(out_train, x=x_train, y=y_train)
    np.savez_compressed(out_dev, x=x_dev, y=y_dev)
    manifest = {
        "schema_version": "1",
        "source_record": source_record,
        "config": config,
        "sources": sources,
        "outputs": {
            "train": {
                "filename": out_train.name,
                "sha256": sha256_file(out_train),
                "x_sha256": sha256_ndarray(x_train, "<f4"),
                "y_sha256": sha256_ndarray(y_train, "<i8"),
                "samples": int(len(x_train)),
            },
            "dev": {
                "filename": out_dev.name,
                "sha256": sha256_file(out_dev),
                "x_sha256": sha256_ndarray(x_dev, "<f4"),
                "y_sha256": sha256_ndarray(y_dev, "<i8"),
                "samples": int(len(x_dev)),
            },
        },
        "tiles": tiles,
    }
    _validate_manifest_path_privacy(manifest, repo_root=repo_root)
    write_canonical_json(manifest_path, manifest)
    return manifest


def build(
    plot_paths: list[str | Path],
    out_train: str | Path,
    out_test: str | Path,
    *,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    frac: float = 0.7,
    buffer: float = 2.5,
    label_col: int = 6,
    n_off: int = 3000,
    per: int = 1000,
) -> dict:
    """Convert plots into the legacy per-plot train/test NPZ artifacts."""
    xtr_l, ytr_l, xte_l, yte_l = [], [], [], []
    per_plot = {}
    for path in plot_paths:
        pts, lab = load_wan_plot(path, label_col=label_col, n_off=n_off, per=per)
        x, y, centers = tile_samples(
            pts, lab, tile=tile, n_points=n_points, min_pts=min_pts
        )
        xtr, ytr, xte, yte = spatial_split(x, y, centers, frac=frac, buffer=buffer)
        xtr_l.append(xtr)
        ytr_l.append(ytr)
        xte_l.append(xte)
        yte_l.append(yte)
        per_plot[Path(path).stem] = {
            "tiles": len(x),
            "train": len(xtr),
            "test": len(xte),
        }

    x_train, y_train = np.concatenate(xtr_l), np.concatenate(ytr_l)
    x_test, y_test = np.concatenate(xte_l), np.concatenate(yte_l)
    np.savez_compressed(out_train, x=x_train, y=y_train)
    np.savez_compressed(out_test, x=x_test, y=y_test)
    return {
        "per_plot": per_plot,
        "train_samples": len(x_train),
        "test_samples": len(x_test),
        "train_wood_frac": round(float(np.mean(y_train == 0)), 4)
        if len(y_train)
        else 0.0,
        "test_wood_frac": round(float(np.mean(y_test == 0)), 4)
        if len(y_test)
        else 0.0,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Wan plots -> PointNet++ train/test .npz"
    )
    parser.add_argument("--plots", nargs="+", required=True, help="Wan plot .txt files")
    parser.add_argument("--out-train", default="wan_train.npz")
    parser.add_argument("--out-test", default="wan_test.npz")
    parser.add_argument("--tile", type=float, default=2.5)
    parser.add_argument("--n-points", type=int, default=2048)
    parser.add_argument("--min-pts", type=int, default=1024)
    parser.add_argument(
        "--frac", type=float, default=0.7, help="train fraction along the spatial cut"
    )
    parser.add_argument(
        "--buffer", type=float, default=2.5, help="held-out gap (m) between train/test"
    )
    parser.add_argument("--label-col", type=int, default=6)
    parser.add_argument("--n-off", type=int, default=3000)
    parser.add_argument("--per", type=int, default=1000)
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    stats = build(
        args.plots,
        args.out_train,
        args.out_test,
        tile=args.tile,
        n_points=args.n_points,
        min_pts=args.min_pts,
        frac=args.frac,
        buffer=args.buffer,
        label_col=args.label_col,
        n_off=args.n_off,
        per=args.per,
    )
    print(stats)
    print(f"wrote {args.out_train} + {args.out_test}")
