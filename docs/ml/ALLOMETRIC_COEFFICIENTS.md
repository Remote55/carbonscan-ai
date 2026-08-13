# The five species equations, and why none of them is used

`species_db.csv` carries `AGB = a · DBH^b · H^c` for five species. Every row has
`coefficients_verified = no`, so every tree is costed with Chave 2014 instead.
This is what happens if you flip one to `yes`.

## What was measured

Each equation against Chave 2014 at the same density, along a plausible height
curve (`H = 0.6·DBH + 2`):

| species | a | b | c | DBH 10 | 20 | 30 | 50 | 80 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Tectona grandis | 0.0509 | 2.150 | 0.700 | 1.01 | 0.99 | 0.97 | 0.95 | 0.92 |
| Afzelia xylocarpa | 0.0612 | 2.420 | 0.660 | 1.62 | 1.88 | 2.03 | 2.22 | 2.41 |
| Bambusa spp. | 0.1310 | 2.280 | 0.590 | 2.83 | 2.86 | 2.85 | 2.81 | 2.76 |
| Dipterocarpus alatus | 0.0396 | 2.380 | 0.800 | 1.51 | 1.84 | 2.05 | 2.35 | 2.66 |
| Hevea brasiliensis | 0.0464 | 2.330 | 0.720 | 1.65 | 1.85 | 1.97 | 2.12 | 2.26 |

Then against a physical ceiling. A tree cannot weigh more than its own volume
times the density of its wood, and this repository has measured the whole-tree
form factor on 65 destructively harvested trees
(`qsm.TOTAL_TREE_FORM_FACTOR = 0.587`):

    ceiling = (π/4) · D² · H · 0.587 · ρ

Above-ground biomass belongs at or below that — the volume covers the whole
above-ground tree, and AGB excludes roots.

| species | eq / ceiling @ DBH 30 | @ 50 | @ 80 |
|---|---:|---:|---:|
| Tectona grandis | 1.13 | 1.06 | 1.00 |
| Hevea brasiliensis | 2.30 | 2.39 | 2.46 |
| Afzelia xylocarpa | 2.35 | 2.49 | 2.60 |
| Dipterocarpus alatus | 2.39 | 2.64 | 2.88 |
| Bambusa spp. | 3.32 | 3.16 | 3.00 |

Chave itself lands at about 1.16 of that ceiling, which is the slack in the
bound: the form factor is a cohort mean (0.573–0.601 between sites) and ρ is a
table value of uncertain basis. The four rows are not inside that slack.

**Four of the five equations predict more mass than the tree can hold.** That is
not a disagreement between fits; it is impossible. The ceiling is if anything
too generous, because it is computed from densities that look air-dry and
therefore too high — see `WOOD_DENSITY_PROVENANCE.md`.

## The previous diagnosis was wrong

`allometric.py` said the four had "the shape of a unit error". Two things rule
that out:

- A unit error — grams read as kilograms — is a factor of **1000**. These are
  2.3× to 3.3×.
- It is not "four of five in the same direction". **Teak is fine**: 1.07 of the
  ceiling, and within 8% of Chave across the whole diameter range. Whatever went
  wrong with the other four did not happen to a row using the same columns.

## What fits the numbers

Green mass rather than oven-dry. Dividing each ratio into an implied moisture
content, wet basis:

| species | mean eq/ceiling | implied moisture content |
|---|---:|---:|
| Hevea brasiliensis | 2.39 | 58% |
| Afzelia xylocarpa | 2.48 | 60% |
| Dipterocarpus alatus | 2.64 | 62% |
| Bambusa spp. | 3.16 | 68% |
| Tectona grandis | 1.07 | 6% |

Every one lands inside the range for fresh wood, teak comes out dry, and bamboo
— the largest ratio — is highest, which is what a hollow culm should be.

**This is a hypothesis fitted to five points after the fact.** It explains the
magnitudes and the ordering, and it is not confirmed. Confirming it means
reading the four papers and checking what the response variable was:

- Tsutsumi et al. 1983 — *Tectona grandis* (the row that already works)
- Ogawa et al. 1965 — *Dipterocarpus alatus*
- Yiping et al. 2010 — *Bambusa* spp.
- Chiarucci et al. 2014 — *Hevea brasiliensis*
- *Afzelia xylocarpa* is listed as "Generic Thai dense hardwood (Chave 2014
  adjusted)", so it has no primary source to read — that row should probably be
  deleted rather than verified.

If the hypothesis holds, the fix is a moisture correction with each paper's own
stated moisture content, not a single factor.

## The guard

`species_equation_is_physically_possible()` refuses any row whose equation
exceeds the ceiling by more than `MAX_AGB_OVER_PHYSICAL_CEILING` (1.5) at DBH
30, 50 or 80 cm.

It is checked **independently of `coefficients_verified`**, on purpose.
`species_db.csv` is data: it ships inside the Docker image and an operator can
edit a row to `yes` without touching code, so that flag never passes through CI.
The flag records that a human read the paper; the ceiling catches them being
wrong about it. `prefer_method="species_specific"` does not override it either.

Three sizes rather than one because a wrong exponent is harmless on saplings and
badly wrong on the large trees that hold the carbon. None of the current rows
needs that — each is already over the ceiling at DBH 10 — so the case is
constructed in `test_equation_plausibility.py` rather than assumed.

Nothing costed changes today. Every row is unverified, so every tree was already
going to Chave; the guard is there for the day somebody changes that.
