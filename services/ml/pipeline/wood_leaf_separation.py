"""Step 5: Wood-Leaf Semantic Segmentation.

Phase 1 (this file): TLSeparation-inspired rule-based segmentation using
local PCA eigenvalue ratios. Robust, CPU-only, no training needed.

Phase 2: PointNet++ deep learning model trained on annotated NEON data,
with this rule-based version kept as fallback.

References:
- Vicari et al. 2019 — TLSeparation (separating wood from leaves in TLS)
- Qi et al. 2017 — PointNet++ (NeurIPS)
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from scipy.spatial import cKDTree


# Output class codes
WOOD = 0
LEAF = 1


def segment_wood_leaf(
    points: np.ndarray,
    *,
    k_neighbors: int = 20,
    linearity_min: float = 0.45,
    planarity_max: float = 0.50,
    verticality_boost_min: float = 0.55,
) -> np.ndarray:
    """Classify each point as wood (0) or leaf (1) by local geometry.

    Algorithm (per point):
        1. Find K nearest neighbors
        2. Compute covariance of neighbor positions
        3. Eigen-decompose → λ0 ≥ λ1 ≥ λ2 (descending)
        4. linearity = (λ0 - λ1) / λ0      # high for stems/branches
           planarity = (λ1 - λ2) / λ0      # high for planar leaf clusters
        5. Wood iff (linearity high AND planarity low) OR strongly vertical

    Args:
        points: (N, 3) XYZ array (already isolated to one tree, but works on
                whole plots too — just slower)
        k_neighbors: Neighborhood size for local geometry
        linearity_min: linearity threshold for wood
        planarity_max: planarity threshold for wood (must be below this)
        verticality_boost_min: extra wood vote if local axis is this vertical

    Returns:
        (N,) int8 array with 0 = wood, 1 = leaf
    """
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {points.shape}")
    n = len(points)
    if n < k_neighbors:
        # Too few points for reliable geometry — call them all wood
        return np.full(n, WOOD, dtype=np.int8)

    tree = cKDTree(points)
    _, nbr_idx = tree.query(points, k=k_neighbors)

    labels = np.full(n, LEAF, dtype=np.int8)
    # Vectorised covariance + eigvals would need batched einsum; for clarity
    # we loop but use float32 + early break — acceptable for ≤ 100k points.
    nbrs = points[nbr_idx]  # (N, k, 3)
    centered = nbrs - nbrs.mean(axis=1, keepdims=True)  # (N, k, 3)
    # Batched covariance: (N, 3, 3)
    cov = np.einsum("nki,nkj->nij", centered, centered) / k_neighbors

    # Single eigh call: ascending eigenvalues + matching eigenvectors
    eigvals, eigvecs = np.linalg.eigh(cov)
    # Flip to descending: λ0 ≥ λ1 ≥ λ2
    lam = eigvals[:, ::-1]
    lam0 = lam[:, 0]
    eps = 1e-9
    linearity = (lam[:, 0] - lam[:, 1]) / (lam0 + eps)
    planarity = (lam[:, 1] - lam[:, 2]) / (lam0 + eps)

    # Verticality boost — eigenvector for largest eigenvalue is at index -1
    # (because eigh returns ascending; we want the principal axis).
    principal = eigvecs[:, :, -1]
    verticality = np.abs(principal[:, 2])

    is_wood = (
        ((linearity >= linearity_min) & (planarity <= planarity_max))
        | (verticality >= verticality_boost_min)
    )
    labels[is_wood] = WOOD
    labels[~is_wood] = LEAF
    return labels


class WoodLeafSegmenter:
    """Wood vs Leaf semantic segmentation with pluggable backend."""

    def __init__(
        self,
        model_path: str | None = None,
        backend: Literal["tlsep", "pointnet"] = "tlsep",
        device: str = "auto",
    ) -> None:
        self.backend = backend
        self.device = device
        self.model_path = model_path
        self._model = None

    def load(self) -> None:
        """Load model weights (no-op for rule-based)."""
        if self.backend == "pointnet":
            raise NotImplementedError("Phase 2 — load PointNet++ checkpoint")

    def segment(self, points: np.ndarray) -> np.ndarray:
        """Classify each point as wood (0) or leaf (1)."""
        if self.backend == "tlsep":
            return self._segment_tlsep(points)
        if self.backend == "pointnet":
            return self._segment_pointnet(points)
        raise ValueError(f"Unknown backend: {self.backend}")

    def _segment_tlsep(self, points: np.ndarray) -> np.ndarray:
        return segment_wood_leaf(points)

    def _segment_pointnet(self, points: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Phase 2 — PointNet++ inference")
