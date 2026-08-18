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

> ⚠️ **Superseded on 2026-08-14. Teak was not fine.** Its density was an air-dry
> 660, which inflated its Chave value by about 20% — just enough to meet a
> mis-transcribed equation coming the other way. With the measured basic 525,
> teak diverges from Chave like the other four (1.11× at DBH 10 cm, 1.37× at
> 80 cm), and the moisture-content table below reads 6% for teak only because of
> the same inflated density. Two wrong numbers agreeing is not agreement. See
> the section at the end of this file, and `WOOD_DENSITY_PROVENANCE.md`.

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

---

## Where the coefficients actually came from (2026-08-14)

They were mis-transcribed from **Thailand's own official methodology**.

`T-VER-S-TOOL-01-01 Version 02`, *การคำนวณการกักเก็บคาร์บอนของต้นไม้*, effective
26 March 2025, published by the Thailand Greenhouse Gas Management Organization
(TGO) at <https://tver.tgo.or.th>. A copy is in `services/ml/data/reference/`.
This is the document `CLAUDE.md` has always said to verify against before
submission; it is on version 2 of 2025, not the 2017 edition that note assumes.

Its Table 2 gives allometric equations **by Thai forest type**, each as three
components summed:

| forest type | equation | source |
|---|---|---|
| ป่าดิบชื้น (tropical rain) | `WS = 0.0509 (D²H)^0.919`, `WB = 0.00893 (D²H)^0.977`, `WL = 0.0140 (D²H)^0.669` | Tsutsumi et al. 1983 |
| ป่าเต็งรัง / ป่าเบญจพรรณ (deciduous dipterocarp, mixed deciduous) | `WS = 0.0396 (D²H)^0.933`, `WB = 0.00349 (D²H)^1.030`, `WL = (28/(WS+WB) + 0.025)⁻¹` | Ogawa et al. 1965 |
| ป่าสนเขา (pine) | two sets, สนสองใบ and สนสามใบ | สุนันทา 2531; พงษ์ศักดิ์ 2524 |
| ป่าชายเลน (mangrove) | Rhizophora and other species | Komiyama et al. 1987 |
| ปาล์ม, ไผ่, เถาวัลย์ | palm, four named bamboos, lianas | Pearson et al. 2005; Kutintara 1995; others |

`WT = WS + WB + WL`, where WS is stem, WB branch, WL leaf, D is DBH in cm and H
total height in m.

Now compare `species_db.csv`:

| row | shipped | in T-VER |
|---|---|---|
| *Tectona grandis* | `a = 0.0509`, `D^2.150 · H^0.700` | `0.0509` is the **stem-only** coefficient of the **rain forest** equation, whose form is `(D²H)^0.919` = `D^1.838 · H^0.919` |
| *Dipterocarpus alatus* | `a = 0.0396`, `D^2.380 · H^0.800` | `0.0396` is the **stem-only** coefficient of the **deciduous** equation, form `(D²H)^0.933` |

The leading coefficients match exactly, twice. That is not coincidence — it is
the same table, transcribed wrong in three separate ways:

1. **The functional form was changed.** `a·(D²H)^k` became `a·D^b·H^c` with
   exponents that are not `2k` and `k`.
2. **Stem biomass was used as whole-tree biomass.** `WS` is one of three
   components; the row uses it as AGB.
3. **Forest-type equations were labelled as species equations.** T-VER has no
   per-species equation for teak or *Dipterocarpus*; it has equations for the
   forest they grow in — and teak is not rain forest.

`agb_source` in every row now records this. Nothing costed changes, because
`coefficients_verified` was already `no` on all five and the physical-ceiling
guard refuses them regardless, so every tree goes to Chave.

### A caution about the ceiling

On a DBH 30 cm, H 20 m teak the models give:

| | AGB (kg) |
|---|---:|
| T-VER rain forest (Tsutsumi) | 552 |
| T-VER deciduous (Ogawa) | 466 |
| `species_db` row as shipped | 621 |
| Chave 2014 at ρ = 525 | 511 |
| **physical ceiling used by the guard** | **436** |

Thailand's official equations and Chave are **both above the ceiling**. That
does not make them wrong; it makes the ceiling suspect. It is
`(π/4)·D²·H·0.587·ρ`, and `TOTAL_TREE_FORM_FACTOR = 0.587` was measured on 65
Belgian temperate trees. Applying it to tropical crowns is the same category of
mistake this document is about.

The guard's threshold of 1.5× absorbs this — the rows it rejects are 2.3–3.3×
over — but the margin is smaller than it looks, and the form factor needs a
tropical measurement before the ceiling is quoted as physics.

### What would close this

Implement the T-VER equations as what they are: **forest-type** models returning
`WS + WB + WL`, selected by forest type rather than species, cited to
`T-VER-S-TOOL-01-01 v2`. That is Thailand's official method, which matters more
for a Thai carbon product than a pantropical fit does — and it is a different
shape from the current `a·D^b·H^c` per-species table, so it is a change to
design rather than to five numbers.
