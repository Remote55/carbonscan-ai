"""Step 5: Wood-Leaf Semantic Segmentation.

Phase 1 (this file): TLSeparation-inspired rule-based segmentation using
local PCA eigenvalue ratios. Robust, CPU-only, no training needed.

Phase 2: PointNet++ deep learning model (see the `training/` package — trained
on synthetic labelled trees, with real data to follow), with this rule-based
version kept as fallback.

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

# The PointNet++ model's first sampling layer needs at least this many points;
# sparser clouds fall back to the rule-based segmenter.
_POINTNET_MIN_POINTS = 512


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
        """Load model weights (no-op for rule-based; checkpoint for pointnet)."""
        if self.backend != "pointnet":
            return
        import torch  # local import — torch only required for the DL backend

        from training.pointnet2_seg import PointNet2SegSSG

        if self.model_path is None:
            raise ValueError("backend='pointnet' requires model_path to a .pt checkpoint")
        device = self.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        ckpt = torch.load(self.model_path, map_location=device, weights_only=True)
        num_classes = ckpt.get("num_classes", 2)
        model = PointNet2SegSSG(num_classes=num_classes)
        model.load_state_dict(ckpt["state_dict"])
        model.to(device).eval()
        self._model = model
        self._device = device
        self._torch = torch

    def segment(self, points: np.ndarray) -> np.ndarray:
        """Classify each point as wood (0) or leaf (1)."""
        if self.backend == "tlsep":
            return self._segment_tlsep(points)
        if self.backend == "pointnet":
            return self._segment_pointnet(points)
        raise ValueError(f"Unknown backend: {self.backend}")

    def _segment_tlsep(self, points: np.ndarray) -> np.ndarray:
        return segment_wood_leaf(points)

    def pointnet_logits(self, normalized_points: np.ndarray) -> np.ndarray:
        """Return strict PointNet logits for points normalized by the caller.

        This evidence-only interface never normalizes its input and never falls
        back to the production ``tlsep`` segmenter.
        """
        if self.backend != "pointnet":
            raise ValueError("pointnet_logits requires backend='pointnet'")
        try:
            points = np.asarray(normalized_points, dtype=np.float32)
        except (TypeError, ValueError) as exc:
            raise ValueError("normalized_points must be a finite (N, 3) array") from exc
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError(
                f"normalized_points must be a finite (N, 3) array, got {points.shape}"
            )
        if not np.all(np.isfinite(points)):
            raise ValueError("normalized_points must be a finite (N, 3) array")
        if len(points) < _POINTNET_MIN_POINTS:
            raise ValueError(
                f"pointnet_logits requires at least {_POINTNET_MIN_POINTS} points"
            )
        if self._model is None:
            self.load()

        torch = self._torch
        points = np.ascontiguousarray(points)
        model_input = torch.from_numpy(points).unsqueeze(0).to(self._device)
        with torch.no_grad():
            raw_logits = self._model(model_input)
        if hasattr(raw_logits, "detach"):
            raw_logits = raw_logits.detach().cpu().numpy()
        logits = np.asarray(raw_logits, dtype=np.float32)
        if logits.shape == (1, len(points), 2):
            logits = logits[0]
        expected_shape = (len(points), 2)
        if logits.shape != expected_shape or not np.all(np.isfinite(logits)):
            raise ValueError(
                "PointNet model must return finite "
                f"{expected_shape} logits, got shape {logits.shape}"
            )
        return logits

    def _segment_pointnet(self, points: np.ndarray) -> np.ndarray:
        """Classify each point as wood (0) / leaf (1) with the PointNet++ model.

        Falls back to the rule-based segmenter when the cloud has too few points
        for the model's sampling layers.
        """
        if self._model is None:
            self.load()
        if len(points) < _POINTNET_MIN_POINTS:
            return self._segment_tlsep(points)
        torch = self._torch
        # Normalise to unit sphere (same as training; see training.woodleaf_dataset)
        pts = np.asarray(points, dtype=np.float64)
        centered = pts - pts.mean(axis=0)
        scale = np.linalg.norm(centered, axis=1).max()
        if scale > 0:
            centered = centered / scale
        x = torch.from_numpy(centered.astype(np.float32)).unsqueeze(0).to(self._device)
        with torch.no_grad():
            logits = self._model(x)  # (1, N, num_classes)
        return logits.argmax(dim=-1).squeeze(0).cpu().numpy().astype(np.int8)
