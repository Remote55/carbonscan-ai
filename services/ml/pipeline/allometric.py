"""Step 8: Allometric biomass + carbon calculation.

Reference: Chave et al. 2014 — pantropical biomass model (Global Change Biology)
Reference: IPCC 2006 — Vol. 4 (AFOLU) carbon fraction defaults
Reference: TGO 2017 — Forestry Sector GHG Calculation Guideline (Thailand)

Formulas:
    AGB (kg) = a × DBH^b × H^c        (species-specific, Tier 2/3)
        or
    AGB (kg) = 0.0673 × (ρ × DBH² × H)^0.976   (Chave 2014 pantropical, Tier 1)

    BGB (kg) = AGB × root_to_shoot_ratio (default 0.24 for tropical, IPCC 2006)
    Biomass (kg) = AGB + BGB
    Carbon (kg C) = Biomass × C_fraction (default 0.47, IPCC 2006)
    CO2eq (kg) = Carbon × (44/12)         (molar mass ratio)

⚠️ Coefficients in this file are sourced from peer-reviewed literature
   (Tsutsumi, Ogawa, Chave, ICRAF, IPCC). Before final NSC submission,
   verify all values against the official TGO 2017 Forestry Guideline PDF.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# CO2 to Carbon ratio (44 g/mol CO2 / 12 g/mol C)
CO2_PER_CARBON = 44.0 / 12.0

# Default Chave 2014 pantropical model
CHAVE_2014_A = 0.0673
CHAVE_2014_EXPONENT = 0.976

# IPCC 2006 defaults (Vol 4, Ch 4, Table 4.4)
DEFAULT_CARBON_FRACTION = 0.47
DEFAULT_ROOT_TO_SHOOT_TROPICAL = 0.24
# Used only when the species is unknown, which on the production path is always:
# nothing supplies a species to process_points. Roughly the pantropical mean in
# the Global Wood Density Database; it is a stand-in for a measurement, and a
# tree costed with it carries that in its `source`. Measured against the Demol
# destructive cohort, whose true mean is 508, this default is the largest single
# source of carbon error - see docs/superpowers/specs/2026-08-09-*.
DEFAULT_WOOD_DENSITY_TROPICAL = 600.0


@dataclass(frozen=True)
class SpeciesParams:
    """Allometric + density parameters for one species."""

    name_sci: str
    name_th: str
    name_en: str
    wood_density: float  # kg/m³
    agb_a: float | None  # species-specific allometric coefficients
    agb_b: float | None  # AGB = a × DBH^b × H^c
    agb_c: float | None
    agb_source: str
    root_to_shoot: float = DEFAULT_ROOT_TO_SHOOT_TROPICAL
    carbon_fraction: float = DEFAULT_CARBON_FRACTION
    #: Has someone checked a, b and c against the cited primary source?
    #:
    #: Not "does it look plausible" — checked, units and functional form, against
    #: the paper. Nobody has yet, so every row is currently False and every tree
    #: is costed with Chave 2014 instead. Four of the five equations return
    #: 1.4x-3.5x what Chave returns at the same density, and the ratio climbs
    #: with diameter, so their exponents disagree with the reference too. Flip a
    #: row to yes in species_db.csv once its source has actually been read.
    coefficients_verified: bool = False


@dataclass
class CarbonResult:
    """Carbon calculation output for one tree."""

    species_sci: str | None
    dbh_cm: float
    height_m: float
    method: str  # 'species_specific' | 'chave_pantropical' | 'volume_density'
    agb_kg: float
    bgb_kg: float
    biomass_kg: float
    carbon_kg: float
    co2eq_kg: float
    wood_density: float
    source: str


# --- Species DB loader ---


@lru_cache(maxsize=1)
def load_species_db(csv_path: str | Path | None = None) -> dict[str, SpeciesParams]:
    """Load species parameters from CSV.

    CSV columns (matches data/species_db.csv):
        name_sci, name_th, name_en, wood_density, agb_a, agb_b, agb_c,
        agb_source, root_to_shoot, carbon_fraction

    Returns:
        Dict {name_sci: SpeciesParams}
    """
    if csv_path is None:
        csv_path = Path(__file__).parent.parent / "data" / "species_db.csv"
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Species DB not found: {csv_path}")

    db: dict[str, SpeciesParams] = {}
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db[row["name_sci"]] = SpeciesParams(
                name_sci=row["name_sci"],
                name_th=row["name_th"],
                name_en=row.get("name_en", ""),
                wood_density=float(row["wood_density"]),
                agb_a=float(row["agb_a"]) if row.get("agb_a") else None,
                agb_b=float(row["agb_b"]) if row.get("agb_b") else None,
                agb_c=float(row["agb_c"]) if row.get("agb_c") else None,
                agb_source=row.get("agb_source", ""),
                # Absent column, empty cell, or anything that is not an explicit
                # yes reads as unverified. The safe reading has to be the default
                # one: a row nobody has annotated is a row nobody has checked.
                coefficients_verified=(row.get("coefficients_verified") or "").strip().lower()
                in {"yes", "true", "1"},
                root_to_shoot=float(row.get("root_to_shoot") or DEFAULT_ROOT_TO_SHOOT_TROPICAL),
                carbon_fraction=float(row.get("carbon_fraction") or DEFAULT_CARBON_FRACTION),
            )
    return db


# --- Calculations ---


def calculate_agb_species_specific(
    dbh_cm: float,
    height_m: float,
    species: SpeciesParams,
) -> float:
    """Compute AGB using species-specific allometric equation.

    AGB = a × DBH^b × H^c

    Requires: species.agb_a, agb_b, agb_c all defined.
    """
    if species.agb_a is None or species.agb_b is None or species.agb_c is None:
        raise ValueError(f"Missing allometric coefficients for {species.name_sci}")

    return species.agb_a * (dbh_cm**species.agb_b) * (height_m**species.agb_c)


def calculate_agb_chave_pantropical(
    dbh_cm: float,
    height_m: float,
    wood_density: float,
) -> float:
    """Compute AGB using Chave 2014 pantropical model.

    AGB = 0.0673 × (ρ × DBH² × H)^0.976

    Where:
        ρ = wood density in g/cm³ (i.e., kg/m³ / 1000)
        DBH = cm
        H   = m
    """
    rho_g_cm3 = wood_density / 1000.0
    return CHAVE_2014_A * ((rho_g_cm3 * (dbh_cm**2) * height_m) ** CHAVE_2014_EXPONENT)


def calculate_carbon(
    dbh_cm: float,
    height_m: float,
    species_sci: str | None = None,
    *,
    prefer_method: str = "auto",
) -> CarbonResult:
    """Compute biomass + carbon + CO2 equivalent for one tree.

    Args:
        dbh_cm: Diameter at Breast Height (cm)
        height_m: Total height (m)
        species_sci: Scientific name (e.g., 'Tectona grandis'). If None or
                     not in DB, uses pantropical Chave 2014 model with
                     default tropical hardwood density (0.60 g/cm³).
        prefer_method: 'auto' | 'species_specific' | 'chave_pantropical'

    Returns:
        CarbonResult with all values.
    """
    if dbh_cm <= 0:
        raise ValueError(f"DBH must be positive, got {dbh_cm}")
    if height_m <= 0:
        raise ValueError(f"Height must be positive, got {height_m}")

    db = load_species_db()
    species = db.get(species_sci) if species_sci else None

    # Decide which method to use
    if prefer_method == "species_specific" and species is None:
        raise ValueError(f"No species-specific data for {species_sci}")

    # A species equation is used only once its coefficients have been checked
    # against the cited source. Four of the five in species_db return 1.4x-3.5x
    # what Chave 2014 returns for the same tree at the same density, with the
    # ratio climbing across the diameter range - their exponents (2.15-2.42)
    # disagree with Chave's effective 1.952, so the disagreement is structural,
    # not a scale offset. Four of five wrong in the same direction is the shape
    # of a unit error, not of independent published equations. Until someone
    # reads the papers, costing a tree with them produces a number we cannot
    # defend, and the density is the one parameter here we do have grounds for.
    usable_species_equation = (
        species is not None
        and species.agb_a is not None
        and species.coefficients_verified
    )

    if usable_species_equation and prefer_method != "chave_pantropical":
        method = "species_specific"
        agb = calculate_agb_species_specific(dbh_cm, height_m, species)
        wood_density = species.wood_density
        source = species.agb_source
    else:
        method = "chave_pantropical"
        wood_density = species.wood_density if species else DEFAULT_WOOD_DENSITY_TROPICAL
        agb = calculate_agb_chave_pantropical(dbh_cm, height_m, wood_density)
        source = "Chave et al. 2014"
        if species is not None and species.agb_a is not None and not species.coefficients_verified:
            # Name what was skipped and why, so the figure carries its own
            # caveat rather than needing this file to explain it.
            source = (
                f"Chave et al. 2014 (ใช้ความหนาแน่นของ {species.name_th}; "
                f"สมการเฉพาะชนิดยังไม่ตรวจสอบกับต้นฉบับ — {species.agb_source})"
            )

    # Belowground biomass
    root_ratio = species.root_to_shoot if species else DEFAULT_ROOT_TO_SHOOT_TROPICAL
    bgb = agb * root_ratio
    biomass = agb + bgb

    # Carbon
    c_frac = species.carbon_fraction if species else DEFAULT_CARBON_FRACTION
    carbon = biomass * c_frac
    co2eq = carbon * CO2_PER_CARBON

    return CarbonResult(
        species_sci=species_sci,
        dbh_cm=dbh_cm,
        height_m=height_m,
        method=method,
        agb_kg=agb,
        bgb_kg=bgb,
        biomass_kg=biomass,
        carbon_kg=carbon,
        co2eq_kg=co2eq,
        wood_density=wood_density,
        source=source,
    )


def calculate_carbon_from_volume(
    volume_m3: float,
    wood_density: float,
    *,
    root_to_shoot: float = DEFAULT_ROOT_TO_SHOOT_TROPICAL,
    carbon_fraction: float = DEFAULT_CARBON_FRACTION,
) -> CarbonResult:
    """Alternative: compute carbon from QSM-derived volume.

    Biomass = Volume × Density
    Then apply BGB ratio + Carbon fraction same as before.

    Useful for cross-validation against allometric method.
    """
    if volume_m3 <= 0:
        raise ValueError(f"Volume must be positive, got {volume_m3}")
    if wood_density <= 0:
        raise ValueError(f"Density must be positive, got {wood_density}")

    agb = volume_m3 * wood_density  # kg
    bgb = agb * root_to_shoot
    biomass = agb + bgb
    carbon = biomass * carbon_fraction
    co2eq = carbon * CO2_PER_CARBON

    return CarbonResult(
        species_sci=None,
        dbh_cm=0.0,
        height_m=0.0,
        method="volume_density",
        agb_kg=agb,
        bgb_kg=bgb,
        biomass_kg=biomass,
        carbon_kg=carbon,
        co2eq_kg=co2eq,
        wood_density=wood_density,
        source="V × ρ",
    )
