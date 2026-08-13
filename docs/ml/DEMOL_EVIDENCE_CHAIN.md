# Where the accuracy numbers come from

Eighteen figures describe how well this pipeline measures a tree: DBH MAE,
height MAE, volume MAPE and their spreads, biases and worst cases, over the 65
destructively harvested trees of the Demol cohort. They are the project's whole
accuracy claim. They appear in the proposal, both READMEs, `PROJECT_SPEC.md`,
`PIPELINE.md`, `WOODLEAF_RESULTS.md` and the web dashboard.

Until 2026-08-13, nothing produced them.

## What was wrong

Two separate failures, and the second was only possible because of the first.

**The block was never derived.** The numbers were averaged from a per-tree table
that had already been rounded for display. That is not a guess — it is visible
in the arithmetic. Every linear statistic in the block was an exact multiple of
1/65 of a two-decimal sum:

| field | published | × 65 |
|---|---:|---:|
| `dbh_mae_cm` | 1.1673846154 | 75.88 |
| `dbh_bias_cm` | −0.5166153846 | −33.58 |
| `height_mae_m` | 0.5446153846 | 35.40 |
| `height_bias_m` | −0.052 | −3.38 |
| `dbh_worst_abs_cm` | 13.54 | — already 2 dp |

The volume figures show the same pattern at four decimals, which is how m³ was
displayed. Rounding each tree's error to the width of a printed column and then
averaging is a real bias, not a cosmetic one, and it is the reason the published
DBH MAE was 3% higher than the pipeline's.

There was already evidence of this in the repository.
`docs/evidence/pointnet_independent_eval/result.json` — the one accuracy
artefact that carried provenance, with a recorded commit, a protocol hash and a
frozen tree list — measured the same cohort with the same tlsep backend and
recorded `dbh_mae_cm = 1.1339` and `volume_mape_pct = 18.93`. The manifest said
1.1674 and 18.77. **The two disagreed for as long as both existed**, and nothing
compared them.

**Then the block went stale.** Five commits between `c498739a` and 2026-08-13
rewrote `qsm.py` — stem tracking, measured volume constants, the crown work.
Nothing required the published figures to be re-derived afterwards, so the
project went on advertising a pipeline measurably worse than the one it shipped.

**And the guard could not have caught either.** `sync_truth.py` protected the
block with:

```python
if validation["demol_65"].get("dbh_mae_cm") != 1.1673846154:
    raise ValueError("Demol DBH MAE must equal 1.1673846154 cm")
```

A literal in a script, compared against a copy of itself in a JSON file. It
could catch someone editing one of the two. It certified as correct a number no
evaluation had ever produced, and it checked one field out of eighteen.

## What the chain is now

```
Demol cohort (65 trees, 691 MB, not in git)
   |
   |  services/ml/scripts/derive_demol_evidence.py
   |  frozen protocol: tree ids, 20,000-point cap, sampling seed, QSM seed
   v
docs/evidence/demol_65/result.json     <- per-tree table at full precision,
   |                                      aggregates rounded once, after
   |                                      averaging, to 6 decimals
   |  sha256 + field-by-field
   v
docs/evidence/core_demo_manifest.json  <- validation.demol_65
   |
   |  scripts/sync_truth.py --write
   v
proposal, READMEs, PROJECT_SPEC, PIPELINE, WOODLEAF_RESULTS, dashboard
```

Three checks hold it together, and they fail in different ways on purpose:

| check | runs | catches |
|---|---|---|
| `sync_truth.py --check` | every push (CI) | manifest edited by hand; artefact edited; documents out of step; any of the 18 fields disagreeing |
| `derive_demol_evidence.py --check` | locally, on demand | the pipeline no longer reproducing the artefact; loss of determinism |
| `tests/test_published_evidence_is_current.py` | locally, in the suite | the same, as part of a normal test run |

The second and third need the cohort, so they skip on CI along with every other
ground-truth test — see [WHAT_CI_DOES_NOT_CHECK.md](WHAT_CI_DOES_NOT_CHECK.md).
CI can prove the published numbers match their artefact. Only a machine with the
data can prove the artefact matches reality.

## What changed in the figures

Re-derived through the frozen protocol at HEAD:

| field | published before | derived | |
|---|---:|---:|---|
| `dbh_mae_cm` | 1.1674 | **0.8983** | −23% |
| `dbh_rmse_cm` | 2.0750 | 1.2110 | −42% |
| `dbh_bias_cm` | −0.5166 | **−0.7976** | worse |
| `dbh_within_10_pct` | 64/65 | **65/65** | |
| `dbh_worst_abs_cm` | 13.54 | **3.95** | −71% |
| `height_mae_m` | 0.5446 | 0.5433 | −0.2% |
| `volume_mape_pct` | 18.7651 | **11.5206** | −39% |
| `volume_within_10_pct` | 18/65 | **32/65** | |

### Where the improvement came from

Not from the fit-quality gate, which is the obvious guess and is wrong.
`MIN_DBH_FIT_QUALITY` was raised from 0.20 to 0.80 on 2026-08-10, but
`compute_qsm` does not read it — the gate is applied by `single_tree.py` and
`main.py`, and the Demol evaluation calls `compute_qsm` directly. All 65 trees
were measurable before and after; none was refused.

The cause was established by running both versions of `qsm.py` over the same
points, the same tlsep labels and the same seeds, changing nothing else:

| `qsm.py` | DBH MAE | volume MAPE |
|---|---:|---:|
| at `c498739a` | 1.1339 cm | 18.93% |
| at HEAD | 0.8983 cm | 11.52% |

The old figures reproduce `pointnet_independent_eval/result.json`'s baseline
exactly, and the new ones reproduce the derived artefact exactly, so the whole
difference sits inside `qsm.py`. It is the stem-tracking and measured
volume-constant work — `baa1128`, `6eab139` — not a threshold.

### The figure that got worse

DBH bias moved from −0.52 cm to −0.80 cm. The pipeline systematically
under-reads stem diameter, and it under-reads it more than the project had been
claiming. The direction is expected — a circle fit through a partial scan of a
stem tends to sit inside the bark — but the size of it is not something the
above improvement excuses, and no measurement here explains why the newer stem
code reads smaller.

Carbon scales with DBH squared. A 0.8 cm under-read on a 30 cm stem is 5% of
basal area, which flows straight into the Chave estimate. That belongs in the
uncertainty discussion, not in a footnote.

## Refreshing the figures

Any change to `qsm.py`, `wood_leaf_separation.py`, `single_tree.py` or the
protocol changes these numbers. The sequence is:

```bash
python services/ml/scripts/derive_demol_evidence.py
```

Then repin the manifest from the artefact — the hash and all eighteen fields —
and run `python scripts/sync_truth.py --write` to carry them into the
documents. `sync_truth.py --check` will refuse anything typed by hand.

Do not edit `core_demo_manifest.json` directly. That is what produced the
figures this document exists to explain.
