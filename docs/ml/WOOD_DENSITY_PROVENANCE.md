# Wood density: the largest lever, and where its numbers now come from

## Why this is the number that matters

Chave 2014 is the model every tree is costed with:

    AGB = 0.0673 × (ρ · D² · H)^0.976

The exponent is 0.976, so **ρ passes into the carbon figure almost
undiminished**. It is also the one parameter the pipeline never measures — it is
looked up from `services/ml/data/species_db.csv`.

The size of the lever, on one tree at DBH 30 cm and H 20 m:

| species | ρ (kg/m³) | CO₂e (kg) | vs the default |
|---|---:|---:|---:|
| *(no species named)* | 570 | 1182.2 | — |
| *Bambusa spp.* | 533 | 1071.5 | −9.4% |
| *Tectona grandis* | 525 | 1091.0 | −7.7% |
| *Hevea brasiliensis* | 530 | 1101.1 | −6.9% |
| *Dipterocarpus alatus* | 610 | 1263.1 | +6.8% |
| *Afzelia xylocarpa* | 693 | 1430.6 | **+21.0%** |

Naming a species still moves the answer by 34% across the table. That is the
largest single effect the product has on its own headline number.

## What was wrong

Until 2026-08-11 that number had **no source column and no verified flag**,
while the allometric coefficients in the same row had `agb_source` and
`coefficients_verified` — and were gated on them, so no species equation is ever
used. The product was refusing the cited quantity and trusting the uncited one.

It was also the wrong *kind* of number. Chave takes ρ as **basic specific
gravity**: oven-dry mass over green volume. Timber tables overwhelmingly publish
**air-dry density at 12% moisture content**, which is the larger figure. They
are not interchangeable, and using air-dry overstates biomass roughly in
proportion.

On 2026-08-11 that was recorded as a suspicion, on the strength of one species,
and the numbers were deliberately left alone: replacing five densities on
evidence for one would have been a different guess, not a correction.

## What settled it

**Reyes, Brown, Chapman and Lugo 1992**, *Wood densities of tropical tree
species*, USDA Forest Service General Technical Report SO-88. Public domain; a
copy is in `services/ml/data/reference/`.

It is the right source for two reasons. It states its basis explicitly — "wood
density is reported in ovendry weight grams per cubic centimeter of green
volume", which is exactly Chave's ρ — and it has a **tropical Asia** section of
428 species, which is the continent this product is for.

It also carries the conversion, because its authors hit the same problem: "most
of the data for these regions were in lb/ft³ volume at 12-percent moisture". So
they regressed one on the other using Chudnoff (1984), 379 trees, r² = 0.988:

    basic = 0.0134 + 0.800 × air_dry_at_12%      (both g/cm³)

### The two routes agree

Put the values this project shipped through that regression, and compare against
what SO-88 measured directly:

| species | shipped | → converted | SO-88 measured (tropical Asia) |
|---|---:|---:|---|
| *Tectona grandis* | 660 | **541** | **0.50 and 0.55** from two sources |
| *Dipterocarpus alatus* | 720 | **589** | genus 0.52–0.62; `Dipterocarpus spp.` 0.61 |
| *Hevea brasiliensis* | 580 | 477 | **0.53** |

Teak converts to 541 and lands between the two independent measurements of 0.50
and 0.55. *Dipterocarpus* converts to 589 and lands inside the genus range. Two
routes, no shared arithmetic, same answer.

**That is what moves the air-dry diagnosis from suspicion to finding.** Every
density this project shipped behaved as an air-dry figure, because that is what
they were.

## What the rows carry now

| species | ρ | basis | verified |
|---|---:|---|---|
| *Tectona grandis* | 525 | measured basic, SO-88 (mean of 0.50 and 0.55) | ✅ |
| *Dipterocarpus alatus* | 610 | measured basic, SO-88 `Dipterocarpus spp.` | ✅ |
| *Hevea brasiliensis* | 530 | measured basic, SO-88 | ✅ |
| *Afzelia xylocarpa* | 693 | 850 air-dry, converted | ❌ |
| *Bambusa spp.* | 533 | 650 air-dry, converted | ❌ |

The two unverified rows had no Asian entry in SO-88. Converting them fixes the
*basis* — they are at least the right quantity now — but the figure that went
into the conversion still has no source, and `density_verified` stays false so
`uncertainty_basis` keeps saying so.

The default for an unknown species, which on the production path is every tree,
moved from an uncited 600 to **570**: the mean of SO-88's 428 tropical Asian
species (SE 0.007). The same table gives 0.60 for tropical America and 0.50 for
tropical Africa, so "pantropical" spans a 20% range and the old value was the
wrong end of it for Thailand.

### What that cost

Every named species now reports **less** carbon, because every density was
air-dry and basic density is smaller. On the DBH 30 cm / H 20 m tree, CO₂e falls
from 1364 → 1091 kg for teak and from 1746 → 1431 kg for *Afzelia*. The
deterministic core demo fell 20%.

That is a correction, not a regression. The pipeline was overstating biomass.

## Bamboo is still not a tree

`Bambusa spp.` is a grass with a hollow culm, no secondary growth and no entry in
any wood density table consulted here. Chave 2014 is a pantropical model for
trees and does not cover it.

The row is costed anyway, because refusing one of five listed target species is
a larger change than this evidence asks for — but `uncertainty_basis` now says
plainly that the model does not cover it, and
`tests/test_density_provenance.py::test_bamboo_says_the_model_does_not_cover_it`
keeps that sentence there.

If bamboo matters to the product, it needs its own model, not a better ρ.

## What is left

- ***Afzelia xylocarpa* and *Bambusa spp.* still have no cited density.** SO-88
  has no Asian *Afzelia*. Someone with library access, or the Global Wood
  Density Database itself, can close these two.
- **GWDD was not reachable.** `datadryad.org` serves it behind a proof-of-work
  bot check that this environment does not pass, and the Zenodo copy returned
  403. The R package `BIOMASS` bundles it as `wdData`, which is the shortest
  route if R is available.
- **None of this is validated against a Thai tree.** SO-88 is a compilation of
  tropical Asian species from the literature, not a measurement of the trees
  this product will scan. See `CARBON_VALIDATION_NOTE` in `allometric.py`.
- **The allometric coefficients are still ungated.** Four of five species
  equations predict a mass above the physical ceiling — see
  `ALLOMETRIC_COEFFICIENTS.md`. Correcting ρ does not touch that.
