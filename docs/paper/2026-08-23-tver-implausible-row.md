# One row of Thailand's national tree-carbon methodology predicts more mass than solid wood

**Draft technical note — 2026-08-23**

## Abstract

Thailand's voluntary carbon programme, T-VER, specifies tree biomass through a
table of allometric equations published by the Thailand Greenhouse Gas
Management Organization (TGO) in `T-VER-S-TOOL-01-01` Version 02, effective
26 March 2025. The table carries seven forest types, each with separate stem,
branch and leaf fits on `D²H`.

Six of the seven rows behave. The seventh — hill pine, two-needle
(*ป่าสนเขา, สนสองใบ*) — predicts **3,258 kg** of above-ground biomass for a tree
30 cm in diameter and 20 m tall. A solid cylinder of the same dimensions
machined from wood denser than any traded timber weighs **1,414 kg**. The
equation exceeds the mass of solid wood by a factor of **2.30**, and it does so
at every size tested, from 10 cm to 80 cm diameter.

Three independent estimates place the true figure between 350 and 630 kg. The
row's own sibling in the same table — hill pine, three-needle — gives 598 kg.
The discrepancy is confined to one coefficient: the two-needle stem term carries
`a = 0.2141` where the three-needle carries `a = 0.02698`, a factor of 7.94.

This note reports the arithmetic and does not diagnose its cause. Whether the
error entered at transcription into the guideline or was present in the 1988
source it cites cannot be determined without the primary document.

---

## 1. Why this matters more than an arithmetic slip

T-VER is not advisory. It is the methodology a Thai forestry carbon project is
accounted by, and the biomass figure it produces flows directly into the carbon
stock a project claims and, ultimately, into credits. An equation that
overstates biomass by a factor of five overstates the credits by the same
factor.

The affected forest type is narrow — hill pine, two-needle, which in Thailand is
*Pinus merkusii* — so the exposure is bounded. But the row is published, in
force, and indistinguishable in presentation from the six rows that are sound.

## 2. The equation as published

Appendix 2, Table 2 gives each forest type three fits of the form
`W = a · (D²H)^b`, with `D` in centimetres, `H` in metres and `W` in kilograms,
summed as `WT = WS + WB + WL`.

The two hill pine rows, side by side:

| | stem | branch | leaf | cited source |
|---|---|---|---|---|
| two-needle | `0.2141 (D²H)^0.9814` | `0.00002 (D²H)^1.4561` | `0.00072 (D²H)^1.0138` | สุนันทา (2531) |
| three-needle | `0.02698 (D²H)^0.946` | `0.00018 (D²H)^1.455` | `0.00072 (D²H)^1.094` | พงษ์ศักดิ์ (2524) |

The leaf coefficients `a` are identical at `0.00072`, and all four exponents are
close — stem `0.9814` against `0.946`, branch `1.4561` against `1.455`. Two
coefficients differ: the branch `a` by a factor of 9.0, and the stem `a` by
7.94.

Only the stem difference matters to the total. At 30 cm and 20 m the branch term
contributes 31 kg to the two-needle prediction against 280 kg for three-needle —
the two-needle branch fit is the *smaller* of the pair — while the stem term
contributes 3,212 kg against 286 kg. The whole discrepancy lives in one number.

## 3. Three independent checks, and what they agree on

Take a hill pine 30 cm in diameter at breast height and 20 m tall — an ordinary
mature tree, well inside the range these equations are meant to serve.

| estimate | above-ground biomass |
|---|---:|
| **T-VER, two-needle** | **3,258.0 kg** |
| T-VER, three-needle (same table) | 598.4 kg |
| Chave et al. 2014 pantropical, ρ = 450 kg/m³ | 439.2 kg |
| Chave et al. 2014 pantropical, ρ = 550 kg/m³ | 534.3 kg |
| Chave et al. 2014 pantropical, ρ = 650 kg/m³ | 628.9 kg |
| Geometry: cylinder × form factor 0.45 × ρ 550 | 349.9 kg |
| Geometry: cylinder × form factor 0.50 × ρ 550 | 388.8 kg |
| **Absolute bound: solid cylinder at ρ = 1000 kg/m³** | **1,413.7 kg** |

Three methods that share no arithmetic — a second row of the same national
table, a pantropical model fitted on thousands of destructively harvested trees,
and elementary geometry — converge on 350 to 630 kg. The three-needle row at
598 kg sits in the middle of that range.

The two-needle row sits at 3,258 kg: **6.1× the Chave estimate**, **5.4× its own
sibling row**, and **2.30× the mass of a solid wooden cylinder** of the same
dimensions.

### 3.1 On the absolute bound

The bound deserves a word, because it is the only claim here that requires no
model at all.

A cylinder 30 cm across and 20 m tall has a volume of 1.414 m³. Filled with wood
at 1000 kg/m³ it weighs 1,414 kg. That density is chosen deliberately above the
plausible range: balsa is about 160 kg/m³, oak about 700, and lignum vitae —
among the densest traded timbers — about 1,200 air-dry. Nothing that grows is
a solid cylinder: a stem tapers, a crown is mostly air, and most wood floats.
The bound is therefore generous by a wide margin, and it is not a fit, a model
or a calibration. It is the mass of the wood if the tree were a machined billet.

An equation predicting 2.3× that figure is not merely inaccurate.

### 3.2 The ratio holds at every size

If the problem were the exponent, the discrepancy would grow or shrink with
tree size. It does not:

| D (cm) | H (m) | predicted | solid-wood bound | ratio |
|---:|---:|---:|---:|---:|
| 10 | 8 | 152.2 kg | 62.8 kg | 2.42× |
| 30 | 20 | 3,258.0 kg | 1,413.7 kg | 2.30× |
| 50 | 30 | 13,345.7 kg | 5,890.5 kg | 2.27× |
| 80 | 40 | 45,195.8 kg | 20,106.2 kg | 2.25× |

A near-constant ratio across an eightfold range of diameter points at the
multiplicative coefficient, not the exponent.

## 4. Where the error probably is, and what cannot be established here

The evidence above is consistent with a single mistyped coefficient. `0.2141`
against `0.02698` is close to a factor of 8; a decimal point moved one place
would give a factor of 10. Neither reproduces the other exactly, so a simple
misplaced decimal does not fully explain it.

**What cannot be determined from the published guideline alone** is where the
error entered. Three possibilities remain open:

1. a transcription error when the 1988 source was compiled into the guideline;
2. an error in the original source, สุนันทา (2531), carried forward faithfully;
3. a difference in units or in the definition of `WS` between the two pine
   sources that the table does not record.

Settling this requires the primary thesis, which was not consulted for this
note. Until it is, the finding is that **the equation as published cannot be
correct**, not that any particular party made a particular mistake.

## 5. What a project using this row should do

The practical consequence is narrow and specific. A project on two-needle hill
pine that applied Appendix 2 Table 2 as written has a biomass figure roughly
five to six times too high, and therefore a carbon stock and a credit volume
inflated by the same factor.

Nothing in this note affects the other six forest types. They were checked
against the same bound and sit between 0.33× and 0.51× of it — comfortably
inside what a real tree can weigh.

## 6. Limitations

- **The primary source was not consulted.** สุนันทา (2531) was not obtained.
- **No two-needle pine was weighed for this note.** The check is against a
  physical bound, a second equation, and a pantropical model — not against a
  harvested tree of this species.
- **Chave 2014 is itself a model.** It is used here as one of three converging
  lines of evidence, not as ground truth. Its agreement with the geometric
  estimate and with the three-needle row is what carries weight, not any single
  number.
- **The wood density used for the Chave comparison is a plausible range for
  pine, not a measurement of Thai *Pinus merkusii*.** The conclusion is not
  sensitive to it: the row exceeds the absolute bound regardless of density,
  because that bound assumes solid wood.
- **Only whole-tree totals were checked.** The stem, branch and leaf terms were
  not validated separately against any source.

## 7. Reproducing this

Every figure above comes from a transcription of the table in code, and can be
re-derived in one command.

```bash
python -c "from pipeline import tver; \
b = tver.aboveground_biomass('pine_two_needle', 30, 20); \
print(b.total_kg, tver.solid_cylinder_mass_kg(30, 20))"
```

The transcription is `services/ml/pipeline/tver.py`, documented in
`docs/ml/TVER_EQUATIONS.md`. `tver.implausible_sizes()` reports which sizes, if
any, a given forest type predicts an impossible mass at; for `pine_two_needle`
it returns every size tested.

The table is reported in code exactly as published. It is not this repository's
place to silently correct a national methodology, and a corrected coefficient
would be a guess about which digit moved. The consuming function refuses to cost
a tree with this row rather than emitting a number, on the grounds that
reporting the table faithfully and handing someone a 3.2-tonne pine are
different jobs.

## References

- **TGO (2025).** `T-VER-S-TOOL-01-01` Version 02, *การคำนวณการกักเก็บคาร์บอนของ
  ต้นไม้*, effective 26 March 2025, Appendix 2 Table 2. Thailand Greenhouse Gas
  Management Organization. <https://tver.tgo.or.th>
- **Chave, J. et al. (2014).** Improved allometric models to estimate the
  aboveground biomass of tropical trees. *Global Change Biology* 20(10),
  3177–3190.
- **สุนันทา (2531)** and **พงษ์ศักดิ์ (2524)**, cited by TGO as the sources of the
  two hill pine rows. Not consulted for this note.

---

## Status of this draft

Not submitted anywhere. Written from a transcription of the published table and
checked against two models and one physical bound.

**Before this goes further, two things should happen.** The primary source
should be obtained, which would turn section 4 from three open possibilities
into an answer. And TGO should be told directly — a published methodology in
force is a different kind of object from a paper, and the people who can correct
it should not have to find out from a preprint.
