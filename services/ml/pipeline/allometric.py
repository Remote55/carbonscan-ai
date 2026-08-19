"""Step 8: Allometric biomass + carbon calculation.

Reference: Chave et al. 2014 — pantropical biomass model (Global Change Biology)
Reference: IPCC 2006 — Vol. 4 (AFOLU) carbon fraction defaults
Reference: TGO, T-VER-S-TOOL-01-01 Version 02 (26 March 2025) — Thailand's
    official tree carbon methodology. Its equations live in pipeline/tver.py,
    which is where the species coefficients below were transcribed from,
    incorrectly. See docs/ml/ALLOMETRIC_COEFFICIENTS.md.

Formulas:
    AGB (kg) = a × DBH^b × H^c        (species-specific, Tier 2/3)
        or
    AGB (kg) = 0.0673 × (ρ × DBH² × H)^0.976   (Chave 2014 pantropical, Tier 1)

    BGB (kg) = AGB × root_to_shoot_ratio (default 0.24 for tropical, IPCC 2006)
    Biomass (kg) = AGB + BGB
    Carbon (kg C) = Biomass × C_fraction (default 0.47, IPCC 2006)
    CO2eq (kg) = Carbon × (44/12)         (molar mass ratio)

⚠️ The species coefficients in species_db.csv were verified against the TGO
   methodology on 2026-08-14 and do not survive it: they are forest-type
   STEM coefficients with exponents that are not the published ones, used as
   whole-tree biomass. Every row is gated off and every tree is costed with
   Chave. The wood densities beside them were air-dry where Chave takes basic,
   and have been corrected — docs/ml/WOOD_DENSITY_PROVENANCE.md.
"""

from __future__ import annotations

import csv
import math
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
# nothing supplies a species to process_points. It is a stand-in for a
# measurement, and a tree costed with it carries that in its `source`.
#
# This was 600, described as roughly the pantropical mean of the Global Wood
# Density Database, with no citation. 570 is the mean basic density of the 428
# tropical Asian species in Reyes et al. 1992 (SE 0.007), which is a sourced
# number and the right continent for a Thai product. The same table gives 0.60
# for tropical America and 0.50 for tropical Africa, so "pantropical" spans a
# 20% range and picking the middle of it was costing about 5% on every tree.
#
# It is a mean over species, not over a forest: it weights a rare ironwood the
# same as a common softwood, and no plot here is a random draw from 428 species.
# Against the Demol cohort, whose measured basic mean is 508, it still reads
# 12% high, and those are temperate trees this figure does not claim to cover.
DEFAULT_WOOD_DENSITY_TROPICAL = 570.0
#: Reyes et al. 1992, table 2, tropical Asia. Kept beside the value so a reader
#: can see the spread the single number is standing in for.
TROPICAL_ASIA_DENSITY_MEAN = 570.0
TROPICAL_ASIA_DENSITY_SE = 7.0
TROPICAL_ASIA_DENSITY_N_SPECIES = 428

# Wood density is never measured by this pipeline, and Chave is close to linear
# in it, so it passes almost undiminished into the carbon figure. These bounds
# turn that into a stated range instead of a single confident number.
#
# Known species: within-species density varies with CV 5.1% in the Demol cohort
# - remarkably steady across all five, 3.4% to 6.7% - so two sigma is ±10%.
# Unknown species: the spread is *between* species, not within one. 400-800
# spans the observed density of every species we have data for (Demol 397-632,
# species_db 525-693) and matches the 0.4-0.8 classes that hold most of the 428
# tropical Asian species in Reyes et al. 1992.
WOOD_DENSITY_SPREAD_KNOWN_SPECIES = 0.10
DEFAULT_WOOD_DENSITY_RANGE = (400.0, 800.0)

# Air-dry at 12% moisture -> basic (ovendry mass / green volume).
#
# Chave 2014 takes basic specific gravity. Timber tables almost universally
# publish air-dry density at 12% moisture content, which is the larger number,
# and every density this project shipped until 2026-08-14 was one of those:
# teak at 660 against a measured 0.50-0.55, Dipterocarpus at 720 against a genus
# range of 0.52-0.62, Hevea at 580 against a measured 0.53.
#
# Reyes et al. 1992 hit the same problem building a tropical density table -
# "most of the data for these regions were in lb/ft3 volume at 12-percent
# moisture" - and regressed one on the other using Chudnoff (1984), 379 trees,
# r2 = 0.988. Their table marks converted values with an asterisk.
#
# Applied to the values this project shipped, it lands inside the independently
# measured range every time it can be checked: teak 660 -> 541 against direct
# measurements of 0.50 and 0.55, Dipterocarpus 720 -> 589 against a genus range
# of 0.52-0.62. Two routes, same answer, which is why the air-dry diagnosis is
# recorded here as established rather than suspected.
REYES_1992_BASIC_INTERCEPT = 0.0134
REYES_1992_BASIC_SLOPE = 0.800


def basic_density_from_air_dry(air_dry_kg_m3: float) -> float:
    """Convert air-dry density at 12% moisture to basic density, in kg/m3.

    Reyes, Brown, Chapman and Lugo 1992, "Wood densities of tropical tree
    species", USDA Forest Service General Technical Report SO-88, page 2.
    Public domain; a copy is in data/reference/.

    Args:
        air_dry_kg_m3: density at 12% moisture content, kg/m3.

    Returns:
        Basic specific gravity expressed as kg/m3, the quantity Chave 2014
        takes.

    Raises:
        ValueError: if the input is not a positive, finite density.
    """
    if not math.isfinite(air_dry_kg_m3) or air_dry_kg_m3 <= 0:
        raise ValueError(f"air-dry density must be positive and finite, got {air_dry_kg_m3}")
    return (REYES_1992_BASIC_INTERCEPT + REYES_1992_BASIC_SLOPE * air_dry_kg_m3 / 1000.0) * 1000.0

# ⚠️ WHAT THIS RANGE IS NOT
#
# It propagates one input. It is not a confidence interval on the carbon figure,
# and it should not be presented as one.
#
# Against the 65 Demol trees weighed after felling (true AGB = fresh mass ×
# dry-matter content, which cross-checks against volume × density to within
# -1.1% ± 2.4%), predicting from the trees' own taped DBH and height:
#
#   Chave at the 600 default, i.e. what we ship   MAPE 41.0%   bias +40.8%
#   Chave at each tree's own measured density     MAPE 20.0%   bias +18.1%
#
# So roughly 21 points of that error is not knowing the wood, which this range
# covers, and roughly 18 points remains with the density known, which it does
# not. That residual is Chave used outside its domain: it is a pantropical model
# and these are Belgian temperate trees. A ±33% range around a centre that is
# 41% high covered 41 of 65 trees.
#
# The honest position is that the carbon figure has never been validated on a
# tropical tree, because no destructive tropical cohort is in this repo. What is
# measured here says the model is unbiased for neither this cohort nor,
# necessarily, for Thailand - it says we do not know.
CARBON_VALIDATION_NOTE = (
    "ยังไม่เคยตรวจสอบกับต้นไม้เขตร้อนที่โค่นชั่งจริง; "
    "บนชุด Demol (เขตอบอุ่น) โมเดลให้ค่าสูงกว่าจริง 41%"
)

# The DBH fed to every equation above reads low, and reads low one-sidedly.
#
# Across the 65 Demol trees the pipeline measures 0.80 cm under the tape, with
# 50 of 65 reading low, and the size of it is set by how fissured the bark is:
# -0.67% on smooth-barked beech, -4.06% on Scots pine. The cohort authors' own
# published QSM shows the same ordering slightly larger, and the two
# implementations' per-tree errors correlate at +0.78, so this is TLS against a
# tape rather than a fault in the fit - docs/ml/DBH_BIAS_AND_BARK.md.
#
# It is stated and not corrected. Chave goes as D^1.952, so -0.7% to -4% on
# diameter is -1.3% to -7.8% on biomass, always downward; but the coefficients
# are for four temperate species and the target list runs from teak to bamboo.
# A Scots-pine correction applied to a teak stem would be another unsourced
# constant, which is the thing this file has been spending its comments
# removing.
#
# The consequence for a reader is that the interval reported here is not
# centred: the density range is symmetric, and this is not.
DBH_BIAS_NOTE = (
    "การวัดเส้นผ่านศูนย์กลางด้วย LiDAR อ่านต่ำกว่าการวัดด้วยเทป "
    "ตามความหยาบของเปลือกไม้ (บนชุด Demol: 0.7-4% ซึ่งคิดเป็นชีวมวล 1-8% "
    "ในทิศทางต่ำกว่าจริงเสมอ) และยังไม่มีค่าชดเชยสำหรับไม้เขตร้อน"
)


@dataclass(frozen=True)
class SpeciesParams:
    """Allometric + density parameters for one species."""

    name_sci: str
    name_th: str
    name_en: str
    wood_density: float  # kg/m³
    #: Which density this is, and where it came from.
    #:
    #: Chave 2014 takes ρ as BASIC specific gravity — oven-dry mass over green
    #: volume. Timber tables overwhelmingly publish air-dry density at 12%
    #: moisture content, which is the larger number, and the two are not
    #: interchangeable: feeding air-dry into Chave overstates biomass roughly in
    #: proportion, and ρ enters almost linearly (exponent 0.976).
    #:
    #: Every row is currently unverified, and the one row with evidence points
    #: the wrong way. World Agroforestry's Tectona grandis profile states
    #: "Density of the wood is (min. 480) 610-750 (max. 850) kg/m³ at 12% mc";
    #: species_db carries 660, the middle of that air-dry range. The Global Wood
    #: Density Database (Zanne et al.) gives teak 0.60 g/cm³ basic — 600, ten
    #: percent lower. Four of five rows have no source at all, so their basis is
    #: unknown rather than merely unconfirmed.
    #:
    #: The numbers have NOT been changed to match. Replacing five values on the
    #: strength of one species would be a different guess, not a correction; the
    #: fix is to read basic densities out of GWDD for all five and record the
    #: source here. Until then this field is what stops the figure from reading
    #: as sourced when it is not.
    density_basis: str = "unknown"
    density_source: str = "unsourced"
    #: True only once wood_density is a basic density with a citation in
    #: density_source. Same bar as coefficients_verified, and for the same
    #: reason: a row nobody has annotated is a row nobody has checked.
    density_verified: bool = False
    agb_a: float | None = None  # species-specific allometric coefficients
    agb_b: float | None = None  # AGB = a × DBH^b × H^c
    agb_c: float | None = None
    agb_source: str = ""
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
    #: CO2e recomputed at the low and high ends of the plausible wood density.
    #: Density only — see CARBON_VALIDATION_NOTE for what this does not cover.
    co2eq_low_kg: float = 0.0
    co2eq_high_kg: float = 0.0
    #: What the bounds above were derived from, in words, so a number that
    #: travels into a report or an API response carries its own basis.
    uncertainty_basis: str = ""
    #: The same tree costed through its taper volume instead. Present only when
    #: a volume was supplied.
    #:
    #: A second allometric model, not a measurement — both it and Chave are
    #: one-parameter functions of ρ·D²·H, differing in exponent and coefficient.
    #: See the note beside its computation in calculate_carbon.
    co2eq_volume_route_kg: float | None = None
    #: |volume route - primary| / primary.
    #:
    #: Two defensible models of the same tree, disagreeing. Measured across the
    #: 65 reference trees the gap is 14.9% on average (median 14.7%, range
    #: 12.7-19.3%), and it barely moves with the density assumption because both
    #: models are linear-ish in it. Neither has ever been checked against a
    #: tropical tree, so this is a fair sketch of how much is unsettled — more
    #: informative than either number alone.
    method_disagreement: float | None = None


# --- Species DB loader ---


@lru_cache(maxsize=1)
def load_species_db(csv_path: str | Path | None = None) -> dict[str, SpeciesParams]:
    """Load species parameters from CSV.

    CSV columns (matches data/species_db.csv):
        name_sci, name_th, name_en, wood_density, density_basis, density_source,
        density_verified, agb_a, agb_b, agb_c, agb_source, root_to_shoot,
        carbon_fraction, coefficients_verified

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
                density_basis=(row.get("density_basis") or "unknown").strip(),
                density_source=(row.get("density_source") or "unsourced").strip(),
                # Same reading as coefficients_verified below: absent column,
                # empty cell or anything that is not an explicit yes means no.
                density_verified=(row.get("density_verified") or "").strip().lower()
                in {"yes", "true", "1"},
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


#: How far above volume × density a predicted AGB may sit before it is refused.
#:
#: A tree cannot weigh more than its own volume times the density of its wood.
#: Taking the whole-tree form factor measured on the 65 felled Demol trees
#: (qsm.TOTAL_TREE_FORM_FACTOR = 0.587), the ceiling for a tree is
#:
#:     (π/4) · D² · H · 0.587 · ρ
#:
#: and a real above-ground biomass should sit at or below it, since that volume
#: is the whole above-ground tree and AGB excludes roots.
#:
#: The allowance is for the slack in that bound rather than for the equation:
#: the form factor is a cohort mean that runs 0.573-0.601 between sites, ρ here
#: is a table value of uncertain basis (see SpeciesParams.density_basis), and
#: Chave itself lands about 1.16x the ceiling on these species. 1.5 sits well
#: clear of all of that and well below what the broken rows do.
MAX_AGB_OVER_PHYSICAL_CEILING = 1.5


def physical_mass_ceiling_kg(dbh_cm: float, height_m: float, wood_density: float) -> float:
    """The most an above-ground tree of this size can weigh, oven-dry."""
    if dbh_cm <= 0 or height_m <= 0:
        return 0.0
    from pipeline.qsm import TOTAL_TREE_FORM_FACTOR

    volume_m3 = math.pi / 4.0 * (dbh_cm / 100.0) ** 2 * height_m * TOTAL_TREE_FORM_FACTOR
    return volume_m3 * wood_density


def species_equation_is_physically_possible(
    species: SpeciesParams,
    *,
    sizes: tuple[tuple[float, float], ...] = ((30.0, 20.0), (50.0, 32.0), (80.0, 50.0)),
) -> bool:
    """Does this row's a·D^b·H^c predict a mass a tree could actually have?

    Four of the five rows in species_db do not, by 2.3x to 3.3x — they predict
    more mass than the tree's entire volume times the density of its own wood.
    That is not a fitting disagreement, it is an impossibility, and it holds
    across the whole diameter range rather than at one end.

    The mechanism is not established. It is not a unit error: grams for
    kilograms would be a factor of 1000, and teak, which uses the same column
    layout, lands at 1.07. What fits the numbers is green mass — dividing each
    ratio into an implied moisture content gives 58%, 60%, 62% and 68%, all
    inside the range for fresh wood, with bamboo highest, which is what a culm
    should be. That is a hypothesis fitted to five points after the fact, and
    confirming it means reading the four papers.

    Checked at three sizes because a wrong exponent shows up as divergence: the
    ratios climb from about 1.5 at DBH 10 cm to 2.7 at 80 cm on three of the
    rows, so a single-size check could be passed by an equation that is badly
    wrong on large trees, which are the ones that carry the carbon.
    """
    if species.agb_a is None or species.agb_b is None or species.agb_c is None:
        return False
    for dbh_cm, height_m in sizes:
        ceiling = physical_mass_ceiling_kg(dbh_cm, height_m, species.wood_density)
        if ceiling <= 0:
            continue
        predicted = calculate_agb_species_specific(dbh_cm, height_m, species)
        if predicted > ceiling * MAX_AGB_OVER_PHYSICAL_CEILING:
            return False
    return True


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
    volume_m3: float | None = None,
    forest_type: str | None = None,
) -> CarbonResult:
    """Compute biomass + carbon + CO2 equivalent for one tree.

    Args:
        dbh_cm: Diameter at Breast Height (cm)
        height_m: Total height (m)
        species_sci: Scientific name (e.g., 'Tectona grandis'). If None or
                     not in DB, uses pantropical Chave 2014 model with
                     default tropical hardwood density (0.60 g/cm³).
        prefer_method: 'auto' | 'species_specific' | 'chave_pantropical'
        volume_m3: the tree's measured volume, if the geometry step produced
            one. Costs the tree a second way — volume x density — and reports
            it alongside. See CarbonResult.co2eq_volume_route_kg for why that
            second number is worth carrying.
        forest_type: a key of pipeline.tver.FOREST_TYPES. Costs the tree with
            Thailand's official methodology instead of Chave — the equation for
            the forest it stands in, summing stem, branch and leaf. Opt-in and
            never the default: T-VER has not been checked against a tree this
            pipeline measured, and changing the number the product reports is a
            decision with evidence attached.

    Returns:
        CarbonResult with all values.

    Raises:
        ValueError: on a non-positive dimension, on prefer_method
            'species_specific' without species data, or on a forest type whose
            published equation is not physically possible.
        KeyError: on an unknown forest type.
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
    # against the cited source AND the equation predicts a mass a tree could
    # actually have.
    #
    # This comment used to say the four disagreeing rows had "the shape of a
    # unit error". Measuring it says otherwise: a unit error is a factor of
    # 1000, and these are 2.3x-3.3x.
    #
    # It also used to say teak was the exception - 1.07 of the ceiling, within
    # 8% of Chave - and read that as evidence the teak row was sound. It was
    # not. Teak's density was an air-dry 660, which inflated its Chave value by
    # about 20%, just enough to meet a wrong equation coming the other way. At
    # the measured basic 525 all five rows diverge. Two wrong numbers agreeing
    # is not agreement.
    #
    # The source of all five is now known: they are T-VER forest-type stem
    # coefficients with the wrong exponents attached and WS used as whole-tree
    # biomass. pipeline/tver.py has the table as published.
    #
    # What IS established is harder than a disagreement: every row predicts
    # more mass than the tree's whole volume times the density of its own wood
    # - see species_equation_is_physically_possible. That ceiling is now
    # computed from sourced basic densities rather than air-dry guesses, so the
    # violation is measured rather than understated.
    #
    # This comment used to end "...and the density is the one parameter here we
    # do have grounds for." That was wrong, and in the more embarrassing
    # direction: the coefficients at least carry a citation and are gated on it,
    # while the densities beside them carried neither a source nor a stated
    # basis and were used unconditionally. Three of the five now carry a
    # measured basic density out of Reyes et al. 1992, while the coefficients
    # beside them still cite a table they were transcribed out of incorrectly.
    # See docs/ml/WOOD_DENSITY_PROVENANCE.md.
    # The physical check is deliberately not conditional on the flag. species_db
    # is data: it ships inside the Docker image and an operator can edit a row
    # to `yes` without touching code, so it never passes through CI. The flag
    # records that a human read the paper; the ceiling is what catches them
    # being wrong about it.
    usable_species_equation = (
        species is not None
        and species.agb_a is not None
        and species.coefficients_verified
        and species_equation_is_physically_possible(species)
    )

    if forest_type is not None:
        # Thailand's own method, opted into explicitly. It takes no density -
        # the equations are fitted on D and H alone - so wood_density below is
        # reported for the volume cross-check and does not enter this AGB.
        from pipeline import tver

        if tver.implausible_sizes(forest_type, ((dbh_cm, height_m),)):
            # One published row predicts more than twice the mass of a solid
            # cylinder of ironwood, at every size. Reporting it as published in
            # tver.py is right; costing a customer's tree with it is not.
            raise ValueError(
                f"T-VER forest type {forest_type!r} predicts more mass than "
                f"solid wood at DBH {dbh_cm} cm, H {height_m} m — see "
                "docs/ml/ALLOMETRIC_COEFFICIENTS.md"
            )
        biomass_parts = tver.aboveground_biomass(forest_type, dbh_cm, height_m)
        method = "tver_forest_type"
        agb = biomass_parts.total_kg
        wood_density = species.wood_density if species else DEFAULT_WOOD_DENSITY_TROPICAL
        source = f"{tver.FOREST_TYPES[forest_type].name_th} — {tver.FOREST_TYPES[forest_type].source}"
    elif usable_species_equation and prefer_method != "chave_pantropical":
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

    def _to_co2eq(above_ground_kg: float) -> float:
        return above_ground_kg * (1.0 + root_ratio) * c_frac * CO2_PER_CARBON

    if method == "tver_forest_type":
        # The T-VER equations are fitted on D and H alone, so there is no
        # density to propagate here either, and the methodology publishes no
        # interval with them. Collapsing and saying so beats a ±0 that reads as
        # precision, and beats a density band around a number density never
        # touched.
        co2eq_low = co2eq_high = co2eq
        basis = (
            f"สมการตามชนิดป่าของ อบก. ({source}) — "
            "ไม่มีช่วงความไม่แน่นอนกำกับในระเบียบวิธี; "
            f"{DBH_BIAS_NOTE}"
        )
    elif method == "species_specific":
        # a·DBH^b·H^c does not take a density, so there is nothing to propagate.
        # The equation's own uncertainty is unknown to us, and reporting ±0
        # would read as precision, so the bounds collapse and say why.
        co2eq_low = co2eq_high = co2eq
        basis = (
            f"สมการเฉพาะชนิด ({source}) ไม่มีช่วงความไม่แน่นอนที่ตรวจสอบแล้ว; "
            f"{DBH_BIAS_NOTE}"
        )
    else:
        if species is not None:
            spread = WOOD_DENSITY_SPREAD_KNOWN_SPECIES
            rho_low = wood_density * (1.0 - spread)
            rho_high = wood_density * (1.0 + spread)
            # The ±10% is within-species variation, so it is centred on the
            # table value and says nothing about whether that value is the right
            # quantity. Three rows now carry a measured basic density out of
            # Reyes et al. 1992 and are centred on something real. The other two
            # were converted from an air-dry figure that itself has no source,
            # so the basis is right and the centre is still a guess, and the
            # reader has to be told which kind they are holding.
            density_caveat = (
                ""
                if species.density_verified
                else " — ค่าความหนาแน่นนี้แปลงหน่วยถูกต้องแล้ว "
                "แต่ค่าตั้งต้นยังไม่มีแหล่งอ้างอิงที่ตรวจสอบได้"
            )
            # Chave 2014 is a pantropical model for TREES. Bamboo is a grass: a
            # hollow culm with no secondary growth, no taper like a bole and no
            # entry in any of the wood density tables consulted here. The figure
            # is produced because refusing one of five listed target species
            # would be a larger change than this evidence asks for, but it is
            # not a biomass estimate in the sense the other four are.
            domain_caveat = (
                " — ⚠️ ไผ่เป็นพืชตระกูลหญ้า ไม่ใช่ไม้ยืนต้น "
                "สมการ Chave 2014 ไม่ครอบคลุม ตัวเลขนี้ใช้อ้างอิงคร่าว ๆ เท่านั้น"
                if species.name_sci.startswith("Bambusa")
                else ""
            )
            basis = (
                f"ความหนาแน่นไม้ {rho_low:.0f}-{rho_high:.0f} kg/m³ "
                f"(±{spread:.0%} รอบค่าของ {species.name_th}){density_caveat}"
                f"{domain_caveat}; "
                f"{CARBON_VALIDATION_NOTE}; {DBH_BIAS_NOTE}"
            )
        else:
            rho_low, rho_high = DEFAULT_WOOD_DENSITY_RANGE
            basis = (
                f"ไม่ทราบชนิดไม้ — ความหนาแน่นสมมติช่วง {rho_low:.0f}-{rho_high:.0f} kg/m³; "
                f"{CARBON_VALIDATION_NOTE}; {DBH_BIAS_NOTE}"
            )
        co2eq_low = _to_co2eq(calculate_agb_chave_pantropical(dbh_cm, height_m, rho_low))
        co2eq_high = _to_co2eq(calculate_agb_chave_pantropical(dbh_cm, height_m, rho_high))

    # The same tree, costed the other way.
    #
    # It is tempting to call this the mechanistic route - volume times density
    # is what mass is - and that would be wrong here. The volume handed in
    # comes from qsm.estimate_volume_taper, which is (π/4)·D²·H·form_factor.
    # Write both models out and they are the same shape:
    #
    #     Chave       AGB = 0.0673 · (ρ·D²·H)^0.976
    #     this route  AGB = ρ·D²·H · 0.461        (0.587 · π/4)
    #
    # Both are one-parameter functions of ρ·D²·H. The difference is an exponent
    # of 1.0 against 0.976 and a coefficient. This is a second allometric model,
    # not a measurement — and its coefficient was fitted to the same 65 temperate
    # trees any comparison would grade it on. That it wins there (10.3% against
    # 20.0%, and +0.55% bias against +18.14%) is what fitting does, not evidence
    # that it travels.
    #
    # What the comparison does establish is about Chave: its bias on that cohort
    # runs +25.9% in the smallest diameter quartile down to +13.0% in the
    # largest, so the mismatch is in the functional form and no scale factor
    # repairs it.
    #
    # So both are reported and neither is promoted. Chave stays primary because
    # its domain is tropical forest, which is where this product is aimed. How
    # far the two disagree is the honest measure of how little is settled.
    #
    # A genuine measurement of volume would be qsm.estimate_volume_sectional,
    # which integrates stacked cylinders up the real stem. It is not used: on
    # real TLS the rule-based wood/leaf split leaves crown points in the high
    # slices and it grossly overestimates. That is the thing worth building.
    co2eq_volume_route: float | None = None
    disagreement: float | None = None
    if volume_m3 is not None and volume_m3 > 0:
        co2eq_volume_route = _to_co2eq(volume_m3 * wood_density)
        if co2eq > 0:
            disagreement = abs(co2eq_volume_route - co2eq) / co2eq
            basis = (
                f"{basis}; วิธีปริมาตร×ความหนาแน่นให้ {co2eq_volume_route:,.0f} kg "
                f"(ต่างจากค่าหลัก {disagreement:.0%})"
            )
        # The band covered one unknown - which density - while a second sat
        # beside it unrepresented: which model. Two defensible models of the
        # same tree land 15% apart on the reference cohort, and an interval that
        # excludes the other one is claiming a confidence nobody has. Widening
        # to contain both does not make the estimate better; it stops the
        # interval from being narrower than what is known.
        co2eq_low = min(co2eq_low, co2eq_volume_route)
        co2eq_high = max(co2eq_high, co2eq_volume_route)

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
        co2eq_low_kg=co2eq_low,
        co2eq_high_kg=co2eq_high,
        uncertainty_basis=basis,
        co2eq_volume_route_kg=co2eq_volume_route,
        method_disagreement=disagreement,
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

    # Here the caller supplied the density, so the range is the same ±10%
    # within-species figure rather than the wide unknown-species one.
    spread = WOOD_DENSITY_SPREAD_KNOWN_SPECIES
    scale = (1.0 + root_to_shoot) * carbon_fraction * CO2_PER_CARBON
    co2eq_low = volume_m3 * wood_density * (1.0 - spread) * scale
    co2eq_high = volume_m3 * wood_density * (1.0 + spread) * scale

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
        co2eq_low_kg=co2eq_low,
        co2eq_high_kg=co2eq_high,
        uncertainty_basis=(
            f"ความหนาแน่นไม้ ±{spread:.0%} รอบ {wood_density:.0f} kg/m³ "
            f"(ไม่รวมความคลาดเคลื่อนของปริมาตร)"
        ),
    )
