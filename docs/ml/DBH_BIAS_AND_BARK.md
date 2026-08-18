# Why the pipeline reads stems small

TreeQ measures DBH 0.80 cm low on average across the 65 Demol trees, and 50 of
the 65 read low. That is a systematic error, not scatter, and carbon scales with
roughly the square of diameter, so it goes straight into the number the product
exists to produce.

This documents what it is. Short version: **it is not a defect in this code, and
it is not fixable by measuring better.** It is the difference between what a
tape measures and what a laser sees on a rough-barked tree, and its size is set
by the species.

## It is not point density

The obvious first guess, and wrong. The published evaluation caps each tree at
20,000 points while `field_eval` and `pipeline.main` both default to 200,000 —
the product runs at ten times the density the evidence describes, which is worth
knowing on its own. Measuring the same 21 trees at each budget:

| points per tree | DBH bias | MAE |
|---|---:|---:|
| 20,000 | −0.780 cm | 0.888 cm |
| 60,000 | −0.885 cm | 1.058 cm |
| 200,000 | −0.809 cm | 1.026 cm |

Ten times the points moves the bias by 0.03 cm. Whatever this is, resolution
does not touch it — and the Zenodo record says why. The released clouds were
"downsampled to a point spacing of 10 or 15 mm" before publication, so the limit
is the spacing, not the count. Raising the budget draws more points from the
same grid.

A twenty-second tree, LXDC04, is left out of that table: at 20,000 points it
returned 118 cm against a taped 23.6, and at 60,000 and 200,000 it returned
23.5 and 23.0. That is the tree `qsm.MIN_DBH_FIT_QUALITY` was raised to refuse,
reappearing here because this comparison calls `compute_qsm` directly and the
gate lives a layer above it. Averaging it in would have made a fit failure look
like a density effect.

## It is not tree size

Bias sorted into size quartiles looks like a size effect — −0.53 cm on the
smallest quarter rising to −1.26 cm on the largest. It is not. Within a species
the correlation between diameter and relative error has no consistent sign
(+0.25, −0.52, +0.58, −0.09 for beech, ash, larch and pine), and comparing two
species over the same 25–38 cm band settles it:

| | n | bias |
|---|---:|---:|
| *Fagus sylvatica* 25–38 cm | 14 | −0.72% |
| *Pinus sylvestris* 25–38 cm | 23 | **−4.74%** |

Same diameters, six times the error. The size gradient was species composition.

## It is bark

Sorted by error, the four species in the cohort come out in exactly the order of
how rough their bark is:

| species | n | DBH bias | relative | MAE | implied AGB bias | bark |
|---|---:|---:|---:|---:|---:|---|
| *Pinus sylvestris* | 30 | −1.272 cm | −4.06% | 1.323 | −7.8% | thick, deeply fissured, plated |
| *Larix decidua* | 5 | −0.605 cm | −2.33% | 0.672 | −4.5% | thick, scaly, fissured |
| *Fraxinus excelsior* | 15 | −0.508 cm | −1.45% | 0.773 | −2.8% | moderately fissured |
| *Fagus sylvatica* | 15 | −0.201 cm | −0.67% | 0.249 | −1.3% | thin, smooth, unfissured |

The AGB column applies Chave 2014, where biomass goes as `(ρD²H)^0.976` and so
as `D^1.952`.

The mechanism is what the ordering suggests. A tape wraps around the outside of
the trunk and rides on the ridges of the bark, so it measures the circumference
of the ridge envelope. A circle fitted to a laser scan of that same trunk passes
through ridges *and* furrows and settles near the middle. The deeper the
fissures, the further apart the two answers, and beech — which has essentially
no fissures — shows almost no gap at all.

## The control that confirms it

The cohort's authors published their own QSM-derived DBH for these trees in the
same CSV (`qsm_DBHqsm`). The Zenodo record names what produced it: **TreeQSM
v2.3** — not a bespoke script, but the reference implementation of quantitative
structure modelling, run by different people on the same point clouds and
checked against the same tape. If the under-read were a flaw in this
repository's circle fit, that column would not show it.

It shows it, in the same order, slightly larger:

| species | TreeQSM v2.3 | TreeQ |
|---|---:|---:|
| *Pinus sylvestris* | −4.40% | −4.06% |
| *Larix decidua* | −4.17% | −2.33% |
| *Fraxinus excelsior* | −2.56% | −1.45% |
| *Fagus sylvatica* | −0.49% | −0.67% |
| **all 65** | **−3.05%** | **−2.54%** |

Per-tree, the two implementations' errors correlate at +0.78 and their
predictions at +0.994. They are wrong on the same trees, by similar amounts, in
the same direction. That is what a property of the data looks like, and not what
a bug looks like.

### Head to head

Same 65 trees, same taped ground truth:

| | MAE | bias | RMSE | worst |
|---|---:|---:|---:|---:|
| TreeQSM v2.3 (Demol et al.) | 1.095 cm | −0.961 cm | 1.593 | 8.17 cm |
| **TreeQ** | **0.898 cm** | **−0.798 cm** | **1.211** | **3.95 cm** |

TreeQ is closer to the tape on 42 of the 65 trees and better on every summary
statistic here.

This is not a controlled A/B — their number comes from their own TreeQSM v2.3
run at settings this repository cannot reproduce, and the dataset ships the
optimal QSMs rather than the parameters that selected them. It is a comparison
against a published reference figure, which is a weaker claim than a matched
experiment and still a meaningful one: TreeQSM is what a reader would otherwise
take as the accuracy attainable on this data.

## What follows for the product

**No bark correction is applied, and none should be from this evidence.** The
coefficients above are for four temperate species. The prototype targets teak,
dipterocarp, rubber, bamboo and *Afzelia*, whose bark ranges from the deep
fissuring of mature teak to the near-smooth culm of bamboo. Applying a
Scots-pine number to a teak stem would be exactly the sort of unsourced constant
this project has spent its evidence machinery removing — see
[WOOD_DENSITY_PROVENANCE.md](WOOD_DENSITY_PROVENANCE.md) for the same argument
about density.

What does follow:

- **The headline MAE describes a mixture, not a tree.** 0.898 cm is 1.32 cm for
  pine and 0.25 cm for beech. Any single accuracy figure for this pipeline is
  a statement about the species mix it was measured on.
- **The direction is known and one-sided.** TLS DBH reads low against tape, by
  something between roughly 0.5% and 4% here. Carbon estimates carry that
  through at nearly twice the rate. An uncertainty band that is symmetric about
  the estimate is misdescribing this.
- **Validating on Thai species needs Thai trees.** Nothing in this cohort
  predicts what teak bark does to a circle fit, and the temperate ordering is
  suggestive rather than transferable.
- **A tape is not truth either.** These are two different measurements of a
  trunk that is not round. The tape is the conventional reference for forestry,
  so it is the one to report against, but "error against tape" and "error"
  are not the same thing.

`tests/test_dbh_bias_by_species.py` pins the structure above. The species
breakdown runs on CI from the committed artefact; the comparison against the
reference QSM needs the cohort and skips there.
