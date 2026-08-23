# Thailand's own allometric equations

`pipeline/tver.py` implements the allometric table from **T-VER-S-TOOL-01-01
Version 02**, *การคำนวณการกักเก็บคาร์บอนของต้นไม้*, effective 26 March 2025,
published by the Thailand Greenhouse Gas Management Organization (TGO) at
<https://tver.tgo.or.th>, Appendix 2 Table 2.

This is the method a Thai forestry carbon project is actually accounted by. For
a product aimed at Thai carbon markets that matters more than a pantropical fit
does, and `CLAUDE.md` has always said to verify against it before submission.

## How it differs in shape

**Indexed by forest type, not species.** There is no T-VER equation for teak;
there is one for the mixed deciduous forest teak grows in. A stand is classified
once and every tree in it uses the same equation.

**Three components, summed.** `WT = WS + WB + WL` — stem, branch and leaf are
separate fits. Using the stem coefficient alone as whole-tree biomass is the
mistake `species_db.csv` shipped for a year;
[ALLOMETRIC_COEFFICIENTS.md](ALLOMETRIC_COEFFICIENTS.md) has that story.

**No density term.** The fits take D and H alone, so naming a species changes
nothing about the biomass, and there is no density band to propagate.

## The table

D is DBH in cm, H is total height in m, W is kg.

| forest type | stem | branch | leaf | source |
|---|---|---|---|---|
| ป่าดิบแล้ง / ป่าดิบเขา | `0.0509 (D²H)^0.919` | `0.00893 (D²H)^0.977` | `0.0140 (D²H)^0.669` | Tsutsumi et al. 1983 |
| ป่าดิบชื้น | `0.0396 (D²H)^0.9326` | `0.006003 (D²H)^1.027` | reciprocal | Ogawa et al. 1965 |
| ป่าเต็งรัง / ป่าเบญจพรรณ | `0.0396 (D²H)^0.933` | `0.00349 (D²H)^1.030` | reciprocal | Ogawa et al. 1965 |
| ป่าสนเขา (สนสองใบ) | `0.2141 (D²H)^0.9814` | `0.00002 (D²H)^1.4561` | `0.00072 (D²H)^1.0138` | สุนันทา 2531 |
| ป่าสนเขา (สนสามใบ) | `0.02698 (D²H)^0.946` | `0.00018 (D²H)^1.455` | `0.00072 (D²H)^1.094` | พงษ์ศักดิ์ 2524 |
| ไม้โกงกาง (*Rhizophora* spp.) | `0.05466 (D²H)^0.945` | `0.01579 (D²H)^0.9124` | `0.0678 (D²H)^0.5806` | Komiyama et al. 1987 |
| ป่าชายเลนชนิดอื่น | `0.0449 (D²H)^0.9549` | `0.02412 (D²H)^0.8649` | `0.09422 (D²H)^0.5439` | Komiyama et al. 1987 |

"reciprocal" is Ogawa's leaf term, `WL = [28/(WS+WB) + 0.025]⁻¹`, which
saturates near 40 kg however large the tree grows — the behaviour a crown has
and a power law does not.

**The two Ogawa rows are not interchangeable.** Both carry a stem coefficient of
0.0396 and differ in every exponent and in the branch term. Reading one as the
other is precisely how a real published coefficient ended up in a `species_db`
row it does not belong to.

## What it gives on a 30 cm, 20 m tree

| forest type | stem | branch | leaf | total AGB |
|---|---:|---:|---:|---:|
| ป่าดิบแล้ง / ป่าดิบเขา | 414.3 | 128.3 | 9.8 | **552.4 kg** |
| ป่าดิบชื้น | 368.3 | 140.8 | 12.5 | **521.5 kg** |
| ป่าเต็งรัง / ป่าเบญจพรรณ | 369.7 | 84.3 | 11.5 | **465.5 kg** |
| ไม้โกงกาง | 574.0 | 120.5 | 20.0 | **714.5 kg** |
| ป่าชายเลนชนิดอื่น | 519.5 | 115.5 | 19.4 | **654.5 kg** |
| ป่าสนเขา (สนสามใบ) | 286.1 | 279.7 | 32.6 | **598.4 kg** |
| ป่าสนเขา (สนสองใบ) | 3211.7 | 31.4 | 14.8 | **3258.0 kg** ⚠️ |

Chave 2014 on the same tree gives 511 kg at ρ = 525 and 591 kg at ρ = 610, so
six of the seven bracket it. Neither model has been checked against a Thai tree,
so this is agreement between two unvalidated models, not validation.

## One row is not physically possible

`ป่าสนเขา (สนสองใบ)` predicts **3258 kg** on that tree. A solid cylinder of the
same dimensions machined from wood denser than lignum vitae weighs 1414 kg. The
equation exceeds the mass of solid wood by 2.3×, and it does so at every size
tested — 10, 30, 50 and 80 cm — which points at the coefficient rather than the
exponent. Its three-needle sibling carries 0.02698 where this carries 0.2141 —
a factor of **7.94**, not the order of magnitude an earlier draft of this
paragraph claimed, and close enough to a moved decimal point to suggest one
without reproducing it.

The branch coefficients differ too, by a factor of 9.0, which that earlier draft
missed by looking only at the stem. It changes nothing: the two-needle branch
fit is the *smaller* of the pair, contributing 31 kg where three-needle
contributes 280, while the stem term contributes 3,212 kg against 286. The whole
discrepancy lives in the stem coefficient.

Three independent estimates put the true figure at 350–630 kg — Chave 2014
across a plausible pine density range, the same table's three-needle row, and
cylinder volume times a pine form factor times density. See
[`docs/paper/2026-08-23-tver-implausible-row.md`](../paper/2026-08-23-tver-implausible-row.md).

`tver.py` reports it as published. A national methodology is not this
repository's to silently correct, and a "fix" would be a guess about which digit
moved. `calculate_carbon` refuses to cost a tree with it, because reporting the
table faithfully and handing a customer a 3.2-tonne tree are different jobs.

### Why this bound and not the other one

`qsm.TOTAL_TREE_FORM_FACTOR` gives a ceiling of `(π/4)·D²·H·0.587·ρ`, which is
what `allometric.species_equation_is_physically_possible` uses. 0.587 was
measured on 65 Belgian temperate trees, and that ceiling flags Chave itself and
most of the T-VER table — see the caution in
[ALLOMETRIC_COEFFICIENTS.md](ALLOMETRIC_COEFFICIENTS.md).

A solid cylinder of 1000 kg/m³ wood is not a fit. Nothing that grows can exceed
it, on any continent, under any form factor. Six of the seven rows sit at 0.29×
to 0.83× of it; the seventh sits at 2.3×.

## Using it

```python
calculate_carbon(dbh_cm=30, height_m=20, forest_type="mixed_deciduous")
```

Opt-in, and never the default. Chave stays the production model, and the reason
is not preference: T-VER has not been checked against a tree this pipeline
measured either, and neither has Chave. Switching the number the product reports
is a decision that needs evidence attached, not a refactor.

Root:shoot, carbon fraction and 44/12 are unchanged — T-VER supplies AGB and the
rest of the chain is the same one every other route uses. The reported interval
collapses, because the methodology publishes no uncertainty with these equations
and a density band around a model that takes no density would be an invention.

## What is still missing

- **Classifying the forest.** Nothing in the pipeline decides which forest type
  a scan is standing in; the caller passes it. That is a real gap between this
  and a T-VER-aligned product.
- **The other tables.** Appendix 2 also carries per-group equations for palms,
  four named bamboos, lianas and four fruit crops, several keyed on basal
  diameter `D₀` rather than DBH. Bamboo is one of this project's five target
  species and is not covered by anything implemented here — see the note in
  [WOOD_DENSITY_PROVENANCE.md](WOOD_DENSITY_PROVENANCE.md).
- **Below-ground.** T-VER takes root:shoot from its own Appendix 1 table by
  species; this pipeline uses the IPCC 0.24 default. Aligning that is a separate
  piece of work.
- **Validation.** Still none, for either model, against a destructively
  harvested tropical tree.
