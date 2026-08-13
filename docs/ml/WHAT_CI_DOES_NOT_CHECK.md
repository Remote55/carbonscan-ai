# What a green CI tick does not mean

`CI ML` reports **649 passed, 35 skipped**. The same suite on a machine with the
data reports **683 passed, 1 skipped**.

The 35 are not marginal. They are the tests that compare this pipeline's output
against trees that were cut down and weighed:

| file | what it checks against ground truth |
|---|---|
| `test_qsm_calibration.py` | DBH from the circle fit vs taped DBH, and the fit-quality gate's motivating failure |
| `test_single_tree.py` | the single-tree path vs tape measurements |
| `test_stem_tracking.py` | tracked stem volume vs harvested stem volume |
| `test_skeleton.py` | crown tracing vs harvested crown volume — the negative result that keeps the tracer out of production |
| `test_plot_pipeline_real_trees.py` | the whole chain on real scans placed in a synthetic plot |
| `test_carbon_uncertainty.py` | the density range vs measured per-tree density |
| `test_backend_promotion_gate.py` | whether PointNet++ measures better than tlsep |

They skip because `services/ml/data/raw/zenodo_belgium/` and
`services/ml/woodleaf_pn2.pt` are not in git — point clouds for 65 trees and a
model checkpoint, far past what belongs in a repository. The skips are correct
behaviour, not a bug.

What was wrong is that they were **invisible**. `pytest -v` prints `SKIPPED` per
line among 688 lines and a count in the summary; nobody reads that as "the
accuracy evidence did not run". The CI step now passes `-rs`, which lists every
skip with its reason in the summary block, so the next person sees what did not
happen.

## What this means in practice

- **CI protects the code, not the measurement.** Ruff, mypy, the unit and
  synthetic tests, the doc-truth check, the Docker build and its live
  `/upload/analyze` call all run on every push. Nothing that compares a number
  to a felled tree does.
- **Accuracy claims have to be re-run locally.** Anyone changing
  `qsm.py`, `allometric.py`, `skeleton.py`, `wood_leaf_separation.py` or
  `single_tree.py` should run the full suite where the cohort is present before
  trusting a green tick.
- **A silent skip for the wrong reason would look identical.** A typo in a path,
  a renamed fixture, a missing import inside a `skipif` — all present as a skip.
  `-rs` is what makes those distinguishable from the expected ones.

## Getting the data

`docs/ml/DATASETS.md` has the sources. The Demol cohort is the destructive
dataset behind every number in this document set:

> Demol et al., destructively harvested trees with taped DBH, felled height and
> harvested stem and total volume — `data/raw/zenodo_belgium/`

Fetch it before claiming any accuracy figure has been checked.
