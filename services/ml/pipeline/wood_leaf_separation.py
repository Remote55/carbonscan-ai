"""Step 5: Wood-Leaf Semantic Segmentation using PointNet++.

Reference: Qi et al. 2017 — PointNet++ (NeurIPS)
Reference: Vicari et al. 2019 — TLSeparation (rule-based fallback)

TODO Phase 2: Implement PointNet++ training + inference.
TODO Phase 1: Use TLSeparation as baseline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class WoodLeafSegmenter:
    """Wood vs Leaf semantic segmentation.

    Two backends available:
    - 'pointnet': Deep Learning (PointNet++), requires GPU + trained model
    - 'tlsep':    Rule-based (geometric features), CPU-only baseline
    """

    def __init__(
        self,
        model_path: str | None = None,
        backend: str = "tlsep",
        device: str = "auto",
    ) -> None:
        self.backend = backend
        self.device = device
        self.model_path = model_path
        self._model = None  # lazy load

    def load(self) -> None:
        """Load model weights into memory."""
        if self.backend == "pointnet":
            raise NotImplementedError("Implement in Phase 2 — load PointNet++ checkpoint")
        # TLSeparation needs no loading

    def segment(self, points: "np.ndarray") -> "np.ndarray":
        """Classify each point as wood (0) or leaf (1).

        Args:
            points: (N, 3) array of XYZ for a single tree

        Returns:
            (N,) int array with 0 = wood, 1 = leaf
        """
        if self.backend == "tlsep":
            return self._segment_tlsep(points)
        elif self.backend == "pointnet":
            return self._segment_pointnet(points)
        raise ValueError(f"Unknown backend: {self.backend}")

    def _segment_tlsep(self, points: "np.ndarray") -> "np.ndarray":
        """Rule-based segmentation via TLSeparation.

        TODO Phase 1: Implement using `tlseparation` library.
        """
        raise NotImplementedError("Implement in Phase 1 — use TLSeparation library")

    def _segment_pointnet(self, points: "np.ndarray") -> "np.ndarray":
        """Deep Learning segmentation via PointNet++.

        TODO Phase 2: Implement.
        """
        raise NotImplementedError("Implement in Phase 2")
