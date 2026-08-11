"""Which species the pipeline knows, read from the pipeline's own data file.

Naming the species is the single largest accuracy improvement available to this
service, and it costs the caller one form field.

Measured against the 65 Demol trees weighed after felling, predicting from their
taped DBH and height: Chave at the default 600 kg/m3 density is 41.0% out with a
+40.8% bias; at each tree's own measured density it is 20.0% out. Roughly half
the error is not knowing what the wood is. The pipeline has accepted a species
since it was written — nothing ever passed one.

The list is parsed from services/ml/data/species_db.csv rather than duplicated
here. The two services have separate virtualenvs so they cannot share code, but
they can share a file, and a copy would drift the moment a row is added.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_ML_DIR = Path(__file__).resolve().parents[3] / "ml"


@dataclass(frozen=True)
class Species:
    name_sci: str
    name_th: str
    name_en: str
    wood_density: float
    #: Whether the species-specific allometric equation has been checked against
    #: its cited paper. False everywhere today - see pipeline/allometric.py.
    coefficients_verified: bool
    #: Whether wood_density is a BASIC density (oven-dry mass / green volume,
    #: which is what Chave 2014 takes) with a citation behind it.
    #:
    #: Also false everywhere. This field exists because the comment above used
    #: to end "which is why naming a species buys its wood density rather than
    #: its equation", and that was the wrong way round: the equation at least
    #: carries a citation and is gated on it, while the density carried neither
    #: a source nor a stated basis and was used unconditionally. The one row
    #: with any evidence, teak, looks like an air-dry figure - the larger
    #: quantity - where the model wants a basic one.
    density_verified: bool


def _species_csv() -> Path:
    root = Path(settings.ML_DIR) if settings.ML_DIR else _DEFAULT_ML_DIR
    return root / "data" / "species_db.csv"


@lru_cache(maxsize=1)
def load_species() -> dict[str, Species]:
    """Every species the pipeline can cost, keyed by scientific name.

    An empty catalogue when the file is missing, not an exception: the species
    field is optional, and an analysis without one is the normal case. A
    deployment that cannot read the file should still measure trees.
    """
    path = _species_csv()
    if not path.is_file():
        logger.warning("species catalogue not found at %s; species selection disabled", path)
        return {}

    catalogue: dict[str, Species] = {}
    try:
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = (row.get("name_sci") or "").strip()
                if not name:
                    continue
                try:
                    density = float(row["wood_density"])
                except (KeyError, TypeError, ValueError):
                    continue
                catalogue[name] = Species(
                    name_sci=name,
                    name_th=(row.get("name_th") or "").strip(),
                    name_en=(row.get("name_en") or "").strip(),
                    wood_density=density,
                    coefficients_verified=(row.get("coefficients_verified") or "")
                    .strip()
                    .lower()
                    in {"yes", "true", "1"},
                    density_verified=(row.get("density_verified") or "")
                    .strip()
                    .lower()
                    in {"yes", "true", "1"},
                )
    except OSError:
        logger.warning("species catalogue at %s could not be read", path)
        return {}
    return catalogue


def is_known(name: str) -> bool:
    return name in load_species()
