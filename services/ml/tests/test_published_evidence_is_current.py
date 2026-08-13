"""Does the pipeline still produce the figures this project publishes?

`docs/evidence/demol_65/result.json` is the derived source for the eighteen
Demol accuracy figures in `docs/evidence/core_demo_manifest.json`, which
`scripts/build_truth_aligned_report.py` and `scripts/sync_truth.py` copy into
the proposal, the READMEs and the dashboard. `sync_truth.py --check` verifies
that the manifest and the documents agree with that artefact, and it runs on
every push.

Nothing there re-runs the pipeline. That is this file's job, and it is the gap
that let the published figures go wrong twice:

- The block was originally averaged from a per-tree table already rounded for
  display. Every linear statistic in it was an exact multiple of 1/65 of a
  two-decimal sum, and `docs/evidence/pointnet_independent_eval/result.json` --
  the one artefact that did carry provenance -- recorded a different DBH MAE
  for the same cohort and the same backend. The two disagreed for as long as
  both existed.
- The stem-tracking and volume-constant work in `qsm.py` then moved the real DBH
  MAE to 0.898 cm and volume MAPE to 11.52%, and the published block did not
  move at all, so the project went on advertising a pipeline measurably worse
  than the one it ships.

The sha256 tripwire in `test_independent_eval.py` catches an edit to the
measurement code. It cannot catch a code change that is deliberate and
declared, which is what that work was. `docs/ml/DEMOL_EVIDENCE_CHAIN.md` records
how the cause was pinned down: it is not the fit-quality gate, which
`compute_qsm` does not read.

LOCAL ONLY. The Demol cohort is 691 MB and not in git, so this skips on CI
along with 34 other tests -- see `docs/ml/WHAT_CI_DOES_NOT_CHECK.md`. It takes
about four minutes. Run it before trusting any accuracy figure in the report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ML_ROOT = Path(__file__).resolve().parent.parent
COHORT = ML_ROOT / "data" / "raw" / "zenodo_belgium"
ARTEFACT = ML_ROOT.parent.parent / "docs" / "evidence" / "demol_65" / "result.json"

needs_cohort = pytest.mark.skipif(
    not (COHORT / "Destructive_and_qsm_data_DEMOL.csv").is_file(),
    reason="Demol cohort not present (691 MB, not in git)",
)

#: How far a fresh run may sit from the published artefact before it is stale.
#:
#: Not a precision claim. The protocol fixes the tree list, the point cap and
#: both seeds, so an unchanged pipeline reproduces the artefact exactly -- two
#: full runs were compared field by field when it was written. The tolerance is
#: here so a harmless refactor or a platform float difference does not fail the
#: build, while a change of the size this file exists for -- 23% on DBH, 39% on
#: volume -- does.
TOLERANCES = {
    "dbh_mae_cm": 0.10,
    "height_mae_m": 0.05,
    "volume_mape_pct": 2.00,
}


@pytest.fixture(scope="module")
def published() -> dict[str, Any]:
    return json.loads(ARTEFACT.read_text(encoding="utf-8"))["metrics"]


@pytest.fixture(scope="module")
def measured() -> dict[str, Any]:
    """A fresh run of the derivation the published artefact came from.

    Imports the script rather than reimplementing it. A test that recomputed
    the statistics its own way would pass while the script that writes the
    published file was broken, which is a failure mode this area has a history
    of.
    """
    sys.path.insert(0, str(ML_ROOT / "scripts"))
    try:
        from derive_demol_evidence import derive
    finally:
        sys.path.pop(0)

    return derive()["metrics"]


@needs_cohort
@pytest.mark.parametrize("field", sorted(TOLERANCES))
def test_the_headline_figures_have_not_drifted(field, published, measured):
    drift = measured[field] - published[field]

    assert abs(drift) < TOLERANCES[field], (
        f"published {field} {published[field]}, measured {measured[field]} "
        f"({drift:+.4f}). Re-run scripts/derive_demol_evidence.py and repin "
        "the manifest from it -- do not hand-edit either to match."
    )


@needs_cohort
def test_every_published_field_still_reproduces(published, measured):
    """The three above are what the documents quote; these are the rest.

    Exact equality, because they come from the same seeded protocol through the
    same code. A difference here is either a real change to the measurement or
    a loss of determinism, and both need someone to look.
    """
    disagreeing = {
        field: (value, measured.get(field))
        for field, value in published.items()
        if measured.get(field) != value
    }

    assert not disagreeing, (
        f"published figures no longer reproduce: {disagreeing}. Re-run "
        "scripts/derive_demol_evidence.py --check for the full comparison."
    )


@needs_cohort
def test_the_cohort_is_still_whole(measured):
    """65 trees. A gate that started refusing them would leave every figure
    above describing a different cohort while still looking reasonable."""
    assert measured["trees"] == 65, (
        f"the run measured {measured['trees']} trees, not 65 -- the published "
        "per-tree statistics describe a cohort that no longer exists"
    )
