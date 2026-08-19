"""Thailand's official allometric equations for tree biomass.

Source: `T-VER-S-TOOL-01-01`, *การคำนวณการกักเก็บคาร์บอนของต้นไม้*, Version 02,
effective 26 March 2025, Appendix 2 Table 2, published by the Thailand
Greenhouse Gas Management Organization (TGO) at <https://tver.tgo.or.th>. See
`data/reference/README.md` for why the document itself is fetched rather than
mirrored here.

This is the method a Thai forestry carbon project is actually accounted by, and
`CLAUDE.md` has always said to verify against it before submission. Two things
make it a different shape from `allometric.py`:

**It is indexed by forest type, not by species.** There is no T-VER equation for
teak; there is one for the mixed deciduous forest teak grows in. A stand is
classified once and every tree in it uses the same equation.

**It returns three components.** Stem, branch and leaf are separate fits and
`WT = WS + WB + WL`. Using the stem coefficient alone as whole-tree biomass is
the specific mistake `species_db.csv` shipped for a year — see
`docs/ml/ALLOMETRIC_COEFFICIENTS.md`.

Nothing here is wired into `calculate_carbon` by default. Chave 2014 stays the
production model, because these equations have not been checked against a tree
this pipeline measured, and switching the number the product reports is a
decision with evidence attached, not a refactor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

#: Ogawa's leaf mass is not a power of D²H. It is the reciprocal form
#:
#:     WL = [ 28 / (WS + WB) + 0.025 ] ^ -1
#:
#: which saturates: leaf mass approaches 40 kg however large the tree gets,
#: which is the behaviour a crown has and a power law does not.
OGAWA_RECIPROCAL_LEAF = "ogawa_reciprocal"

_OGAWA_LEAF_NUMERATOR = 28.0
_OGAWA_LEAF_OFFSET = 0.025


@dataclass(frozen=True)
class PowerLaw:
    """`W = a · (D²H)^b`, with D in cm, H in m and W in kg."""

    a: float
    b: float

    def evaluate(self, d2h: float) -> float:
        return self.a * d2h**self.b


@dataclass(frozen=True)
class ForestType:
    """One row of T-VER Appendix 2 Table 2."""

    key: str
    name_th: str
    name_en: str
    stem: PowerLaw
    branch: PowerLaw
    leaf: PowerLaw | Literal["ogawa_reciprocal"]
    source: str


@dataclass(frozen=True)
class Biomass:
    """Above-ground biomass in kg, split the way T-VER reports it."""

    stem_kg: float
    branch_kg: float
    leaf_kg: float
    total_kg: float
    forest_type: str


#: Every forest type in the table, transcribed with its exponents intact.
#:
#: Two rows share a stem coefficient of 0.0396 and are not interchangeable: the
#: rain-forest row carries exponent 0.9326 with a branch term of
#: 0.006003·(D²H)^1.027, and the deciduous row carries 0.933 with
#: 0.00349·(D²H)^1.030. Reading one as the other is how species_db.csv came to
#: hold a number that matched a published coefficient and nothing else about it.
FOREST_TYPES: dict[str, ForestType] = {
    "dry_evergreen": ForestType(
        key="dry_evergreen",
        name_th="ป่าดิบแล้ง / ป่าดิบเขา",
        name_en="Dry evergreen and hill evergreen forest",
        stem=PowerLaw(0.0509, 0.919),
        branch=PowerLaw(0.00893, 0.977),
        leaf=PowerLaw(0.0140, 0.669),
        source="Tsutsumi et al. (1983), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
    "tropical_rain": ForestType(
        key="tropical_rain",
        name_th="ป่าดิบชื้น",
        name_en="Tropical rain forest",
        stem=PowerLaw(0.0396, 0.9326),
        branch=PowerLaw(0.006003, 1.027),
        leaf=OGAWA_RECIPROCAL_LEAF,
        source="Ogawa et al. (1965), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
    "mixed_deciduous": ForestType(
        key="mixed_deciduous",
        name_th="ป่าเต็งรัง และ ป่าเบญจพรรณ",
        name_en="Deciduous dipterocarp and mixed deciduous forest",
        stem=PowerLaw(0.0396, 0.933),
        branch=PowerLaw(0.00349, 1.030),
        leaf=OGAWA_RECIPROCAL_LEAF,
        source="Ogawa et al. (1965), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
    "pine_two_needle": ForestType(
        key="pine_two_needle",
        name_th="ป่าสนเขา (สนสองใบ)",
        name_en="Hill pine forest, two-needle",
        stem=PowerLaw(0.2141, 0.9814),
        branch=PowerLaw(0.00002, 1.4561),
        leaf=PowerLaw(0.00072, 1.0138),
        source="สุนันทา (2531), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
    "pine_three_needle": ForestType(
        key="pine_three_needle",
        name_th="ป่าสนเขา (สนสามใบ)",
        name_en="Hill pine forest, three-needle",
        stem=PowerLaw(0.02698, 0.946),
        branch=PowerLaw(0.00018, 1.455),
        leaf=PowerLaw(0.00072, 1.094),
        source="พงษ์ศักดิ์ (2524), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
    "mangrove_rhizophora": ForestType(
        key="mangrove_rhizophora",
        name_th="ไม้โกงกาง (Rhizophora spp.)",
        name_en="Mangrove, Rhizophora spp.",
        stem=PowerLaw(0.05466, 0.945),
        branch=PowerLaw(0.01579, 0.9124),
        leaf=PowerLaw(0.0678, 0.5806),
        source="Komiyama et al. (1987), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
    "mangrove_other": ForestType(
        key="mangrove_other",
        name_th="พรรณไม้ในป่าชายเลนชนิดอื่น ๆ",
        name_en="Mangrove, other species",
        stem=PowerLaw(0.0449, 0.9549),
        branch=PowerLaw(0.02412, 0.8649),
        leaf=PowerLaw(0.09422, 0.5439),
        source="Komiyama et al. (1987), via T-VER-S-TOOL-01-01 v2 Appendix 2",
    ),
}


#: Denser than almost any wood on earth. Balsa is about 160, oak about 700,
#: lignum vitae — among the densest traded timbers — about 1200 air-dry.
#:
#: This is deliberately not `qsm.TOTAL_TREE_FORM_FACTOR`. That ceiling is
#: `(π/4)·D²·H·0.587·ρ`, and 0.587 was measured on 65 Belgian temperate trees;
#: applying it to tropical crowns is the same category of mistake this module
#: documents, and it flags Chave itself. A tree machined from solid ironwood is
#: physics, not a fit, and nothing living can exceed it.
ABSOLUTE_WOOD_DENSITY_KG_M3 = 1000.0


def solid_cylinder_mass_kg(dbh_cm: float, height_m: float) -> float:
    """Mass of a solid cylinder of very dense wood with the tree's dimensions.

    An upper bound no real tree approaches: a stem tapers, a crown is mostly
    air, and wood lighter than this floats.
    """
    radius_m = _positive_finite(dbh_cm, "dbh_cm") / 200.0
    volume_m3 = math.pi * radius_m**2 * _positive_finite(height_m, "height_m")
    return volume_m3 * ABSOLUTE_WOOD_DENSITY_KG_M3


def implausible_sizes(
    forest_type: str, sizes: tuple[tuple[float, float], ...] = ((30.0, 20.0),)
) -> tuple[tuple[float, float], ...]:
    """Sizes where an equation predicts more mass than solid wood would weigh.

    Returns the offending (dbh_cm, height_m) pairs, empty when the equation is
    possible everywhere it was asked about. Used to record a finding rather than
    to gate: these equations are published national methodology, and this module
    reports them as published.
    """
    return tuple(
        (dbh_cm, height_m)
        for dbh_cm, height_m in sizes
        if aboveground_biomass(forest_type, dbh_cm, height_m).total_kg
        > solid_cylinder_mass_kg(dbh_cm, height_m)
    )


def _positive_finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be positive and finite, got {value!r}")
    return number


def aboveground_biomass(forest_type: str, dbh_cm: float, height_m: float) -> Biomass:
    """Above-ground biomass for one tree, by T-VER Appendix 2 Table 2.

    Args:
        forest_type: a key of `FOREST_TYPES`. A stand is classified once; there
            is no per-species selection here, because the table has none.
        dbh_cm: diameter at 1.30 m, in centimetres.
        height_m: total tree height, in metres.

    Returns:
        Stem, branch, leaf and total above-ground biomass in kg.

    Raises:
        KeyError: if the forest type is not in the table.
        ValueError: if either dimension is not a positive finite number.
    """
    if forest_type not in FOREST_TYPES:
        raise KeyError(
            f"unknown forest type {forest_type!r}; "
            f"T-VER Appendix 2 has {sorted(FOREST_TYPES)}"
        )
    equations = FOREST_TYPES[forest_type]
    d2h = _positive_finite(dbh_cm, "dbh_cm") ** 2 * _positive_finite(height_m, "height_m")

    stem = equations.stem.evaluate(d2h)
    branch = equations.branch.evaluate(d2h)
    if equations.leaf == OGAWA_RECIPROCAL_LEAF:
        leaf = 1.0 / (_OGAWA_LEAF_NUMERATOR / (stem + branch) + _OGAWA_LEAF_OFFSET)
    else:
        leaf = equations.leaf.evaluate(d2h)

    return Biomass(
        stem_kg=stem,
        branch_kg=branch,
        leaf_kg=leaf,
        total_kg=stem + branch + leaf,
        forest_type=forest_type,
    )
