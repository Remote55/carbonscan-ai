"""Step 7: Species classification from RGB image.

Uses ResNet-50 fine-tuned on tree species (bark + leaf images).
Exports to TFLite for mobile on-device inference.

TODO Phase 2: Implement training + inference.
"""

from __future__ import annotations

from pathlib import Path


class SpeciesClassifier:
    """RGB → species classifier."""

    SPECIES = [
        "Tectona grandis",       # สัก
        "Dipterocarpus alatus",  # ยางนา
        "Bambusa spp.",          # ไผ่
        "Hevea brasiliensis",    # ยางพารา
        "Afzelia xylocarpa",     # มะค่าโมง
        "Unknown",               # fallback
    ]

    def __init__(self, model_path: str | Path | None = None, device: str = "auto") -> None:
        self.model_path = model_path
        self.device = device
        self._model = None

    def load(self) -> None:
        """Load model weights."""
        raise NotImplementedError("Implement in Phase 2 — load ResNet checkpoint")

    def classify(self, image_path: str | Path) -> dict[str, float]:
        """Classify a single image.

        Returns:
            Dict {species_sci: probability} for all classes.
        """
        raise NotImplementedError("Implement in Phase 2")

    def classify_batch(self, image_paths: list[Path]) -> list[dict[str, float]]:
        """Classify multiple images at once."""
        raise NotImplementedError("Implement in Phase 2")
