"""Synthetic forest plot generator — for development & E2E pipeline validation.

Generates a realistic point cloud (ground + trunks + branches + leaves) without
requiring a 5GB NEON download. Useful for:
- Smoke-testing the full pipeline before real data arrives
- Producing figures for the Proposal "Preliminary Results" section
- Reproducible CI tests (seed-controlled)

NOT a substitute for real LiDAR — the geometry is parametric, not physically
modelled. But the densities, dimensions, and structure (trunk vs canopy)
are close enough that downstream algorithms (CSF, watershed, wood/leaf
separation, QSM) behave qualitatively the same as on real data.

Usage:
    from pipeline.synthetic import generate_synthetic_plot
    points, labels = generate_synthetic_plot(n_trees=5, seed=42)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Class labels used throughout the pipeline
CLASS_GROUND = 0
CLASS_WOOD = 1
CLASS_LEAF = 2


@dataclass(frozen=True)
class TreeParams:
    """Parameters describing a single synthetic tree."""

    x: float  # center X (m)
    y: float  # center Y (m)
    z_ground: float  # ground elevation at base (m)
    height: float  # total height (m)
    dbh_cm: float  # diameter at breast height (cm)
    crown_radius: float  # canopy radius (m)
    crown_depth: float  # vertical extent of crown (m)
    species_sci: str = "Tectona grandis"


def _generate_ground_plane(
    *,
    plot_size_m: float,
    z_variation: float,
    point_density: float,  # points per m²
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate ground points with gentle terrain undulation."""
    n_points = int(plot_size_m * plot_size_m * point_density)
    xy = rng.uniform(0, plot_size_m, size=(n_points, 2))
    # Gentle sinusoidal terrain + noise
    z = (
        z_variation
        * (
            0.5 * np.sin(xy[:, 0] / plot_size_m * 2 * np.pi)
            + 0.3 * np.cos(xy[:, 1] / plot_size_m * 3 * np.pi)
        )
        + rng.normal(0, 0.05, size=n_points)
    )
    return np.column_stack([xy, z])


def _terrain_z(x: float, y: float, plot_size_m: float, z_variation: float) -> float:
    """Deterministic terrain elevation at (x, y) — matches _generate_ground_plane."""
    return float(
        z_variation
        * (
            0.5 * np.sin(x / plot_size_m * 2 * np.pi)
            + 0.3 * np.cos(y / plot_size_m * 3 * np.pi)
        )
    )


def _generate_trunk(
    tree: TreeParams,
    *,
    points_per_meter: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample trunk surface (cylinder tapering toward top)."""
    trunk_top = tree.z_ground + (tree.height - tree.crown_depth * 0.4)
    n_layers = int((trunk_top - tree.z_ground) * points_per_meter)
    n_layers = max(n_layers, 30)

    heights = np.linspace(tree.z_ground, trunk_top, n_layers)
    points = []
    for z in heights:
        # Taper: bottom = dbh, top = ~50% dbh
        frac = (z - tree.z_ground) / max(trunk_top - tree.z_ground, 1e-6)
        radius_m = (tree.dbh_cm / 200.0) * (1.0 - 0.5 * frac)
        # Ring of points around trunk
        n_ring = max(int(2 * np.pi * radius_m * points_per_meter), 8)
        angles = rng.uniform(0, 2 * np.pi, size=n_ring)
        x = tree.x + radius_m * np.cos(angles) + rng.normal(0, 0.005, size=n_ring)
        y = tree.y + radius_m * np.sin(angles) + rng.normal(0, 0.005, size=n_ring)
        z_arr = np.full(n_ring, z) + rng.normal(0, 0.01, size=n_ring)
        points.append(np.column_stack([x, y, z_arr]))
    return np.vstack(points)


def _generate_branches(
    tree: TreeParams,
    *,
    n_branches: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate branches radiating from upper trunk into canopy."""
    crown_base = tree.z_ground + tree.height - tree.crown_depth
    branch_z_starts = rng.uniform(crown_base, tree.z_ground + tree.height * 0.95, size=n_branches)
    points = []
    for z_start in branch_z_starts:
        azimuth = rng.uniform(0, 2 * np.pi)
        elevation = rng.uniform(np.pi / 6, np.pi / 3)  # 30°-60° upward
        length = rng.uniform(0.6, 1.2) * tree.crown_radius
        # Sample points along branch
        n_pts = int(length * 30)
        t = np.linspace(0, 1, n_pts)
        x = tree.x + length * t * np.cos(azimuth) * np.cos(elevation)
        y = tree.y + length * t * np.sin(azimuth) * np.cos(elevation)
        z = z_start + length * t * np.sin(elevation)
        # Add jitter (branches aren't perfectly straight)
        x += rng.normal(0, 0.02, size=n_pts)
        y += rng.normal(0, 0.02, size=n_pts)
        z += rng.normal(0, 0.02, size=n_pts)
        points.append(np.column_stack([x, y, z]))
    return np.vstack(points)


def _generate_canopy(
    tree: TreeParams,
    *,
    n_leaf_points: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate leaf cloud — ellipsoidal shell with internal density falloff."""
    crown_center_z = tree.z_ground + tree.height - tree.crown_depth / 2.0
    # Sample inside ellipsoid (not surface — leaves fill the volume)
    azimuth = rng.uniform(0, 2 * np.pi, size=n_leaf_points)
    elevation = np.arcsin(rng.uniform(-1, 1, size=n_leaf_points))
    # Density falls off toward edges (more leaves in interior)
    r_frac = rng.beta(2.0, 1.5, size=n_leaf_points)
    rx = tree.crown_radius * r_frac
    ry = tree.crown_radius * r_frac
    rz = (tree.crown_depth / 2.0) * r_frac
    x = tree.x + rx * np.cos(elevation) * np.cos(azimuth)
    y = tree.y + ry * np.cos(elevation) * np.sin(azimuth)
    z = crown_center_z + rz * np.sin(elevation)
    return np.column_stack([x, y, z])


def generate_synthetic_plot(
    *,
    n_trees: int = 5,
    plot_size_m: float = 30.0,
    ground_z_variation: float = 1.5,
    ground_point_density: float = 30.0,
    trunk_points_per_meter: int = 60,
    branches_per_tree: int = 12,
    leaves_per_tree: int = 4000,
    seed: int = 42,
    tree_overrides: list[TreeParams] | None = None,
) -> tuple[np.ndarray, np.ndarray, list[TreeParams]]:
    """Generate a realistic-looking forest plot point cloud.

    Args:
        n_trees: Number of trees (ignored if tree_overrides is provided)
        plot_size_m: Plot side length (square plot, meters)
        ground_z_variation: Amplitude of terrain undulation (meters)
        ground_point_density: Ground points per m²
        trunk_points_per_meter: Vertical density of trunk samples
        branches_per_tree: Approximate branch count per tree
        leaves_per_tree: Leaf point count per tree
        seed: RNG seed for reproducibility
        tree_overrides: Optional list of TreeParams to use directly

    Returns:
        points: (N, 3) float64 XYZ array
        labels: (N,) int8 array with class id (0=ground, 1=wood, 2=leaf)
        trees:  List of TreeParams used (ground-truth reference)
    """
    rng = np.random.default_rng(seed)

    if tree_overrides is not None:
        trees = list(tree_overrides)
    else:
        trees = []
        # Stratified random placement so trees don't overlap
        grid_cols = int(np.ceil(np.sqrt(n_trees)))
        cell = plot_size_m / grid_cols
        margin = cell * 0.25
        positions = [
            (col * cell + margin + rng.uniform(0, cell - 2 * margin),
             row * cell + margin + rng.uniform(0, cell - 2 * margin))
            for row in range(grid_cols)
            for col in range(grid_cols)
        ]
        rng.shuffle(positions)
        species_pool = [
            "Tectona grandis",  # Teak
            "Dipterocarpus alatus",  # Yang Na
            "Hevea brasiliensis",  # Rubber
            "Afzelia xylocarpa",  # Makha
        ]
        for i in range(min(n_trees, len(positions))):
            x, y = positions[i]
            height = rng.uniform(12, 22)  # m
            dbh = rng.uniform(20, 45)  # cm
            crown_r = rng.uniform(2.5, 4.5)  # m
            crown_d = rng.uniform(5, 9)  # m
            z_g = _terrain_z(x, y, plot_size_m, ground_z_variation)
            species = species_pool[i % len(species_pool)]
            trees.append(
                TreeParams(
                    x=x,
                    y=y,
                    z_ground=z_g,
                    height=height,
                    dbh_cm=dbh,
                    crown_radius=crown_r,
                    crown_depth=crown_d,
                    species_sci=species,
                )
            )

    # Ground
    ground_points = _generate_ground_plane(
        plot_size_m=plot_size_m,
        z_variation=ground_z_variation,
        point_density=ground_point_density,
        rng=rng,
    )

    # Trees
    wood_chunks: list[np.ndarray] = []
    leaf_chunks: list[np.ndarray] = []
    for tree in trees:
        trunk_pts = _generate_trunk(tree, points_per_meter=trunk_points_per_meter, rng=rng)
        branch_pts = _generate_branches(tree, n_branches=branches_per_tree, rng=rng)
        leaf_pts = _generate_canopy(tree, n_leaf_points=leaves_per_tree, rng=rng)
        wood_chunks.append(np.vstack([trunk_pts, branch_pts]))
        leaf_chunks.append(leaf_pts)

    wood_points = np.vstack(wood_chunks) if wood_chunks else np.zeros((0, 3))
    leaf_points = np.vstack(leaf_chunks) if leaf_chunks else np.zeros((0, 3))

    # Stack everything + labels
    points = np.vstack([ground_points, wood_points, leaf_points])
    labels = np.concatenate(
        [
            np.full(len(ground_points), CLASS_GROUND, dtype=np.int8),
            np.full(len(wood_points), CLASS_WOOD, dtype=np.int8),
            np.full(len(leaf_points), CLASS_LEAF, dtype=np.int8),
        ]
    )

    # Shuffle so the order doesn't leak class info downstream
    perm = rng.permutation(len(points))
    return points[perm], labels[perm], trees
