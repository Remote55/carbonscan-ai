# Tropical validation, and the gap between what runs and what is published

**Date:** 2026-08-19 · **Status:** design, awaiting review

Every accuracy figure this project has ever published was measured on temperate
trees in Belgium. The product is aimed at tropical forests in Thailand. Nothing
in the chain has been checked against a tropical tree, and the allometric stage
— the one that turns a measurement into a carbon number — has never been checked
against a harvested mass at all, anywhere.

This document designs the work that closes both, using open data that costs
nothing and needs no field access. It also closes three places where the
published figures have drifted from the ones the pipeline produces, because that
drift is the same defect in the same week, and the demo drift is visible to the
public right now.

Every claim here is anchored to a file, a line, or a number that was measured.
Where something is a prediction rather than a measurement, it says so.

---

## 1. Why this, and why now

The competition is over and did not go our way. That removes the deadline that
shaped every earlier decision, and with it the reason to prefer a finished
prototype over a correct one. The remaining goals are the ones worth having: a
system that is scientifically defensible, a result worth publishing, and a tool
someone can actually use.

All three depend on the same missing thing. A pipeline validated on Belgian
temperate trees cannot be published as a tropical carbon tool, cannot be sold as
one, and cannot honestly be called correct.

Three facts settled the approach:

1. **The gap is closable with open data.** Sixty-one destructively harvested
   tropical trees, scanned before felling, are public domain (§3).
2. **The team is one person with no institution and no hardware.** Collecting
   field data is not available. Anything requiring a scanner, a permit, or a
   co-investigator is out.
3. **The algorithms are not the contribution and will not become it.** Published
   leaf-wood segmentation on tropical trees reaches mIoU 86.8%; `tlsep` scores
   external macro wood IoU 0.196 and the PointNet++ candidate 0.237
   (`docs/evidence/pointnet_independent_eval/result.json`). Competing on that
   metric means reimplementing LeWoS and PointsToWood, which are already open.
   The evidence infrastructure in this repository is unusual and the
   measurement chain it protects is the thing worth strengthening.

## 2. What this closes

`docs/evidence/core_demo_manifest.json` records what the Demol evaluation does
not cover, in its own words:

> "This does not validate full-pipeline stages 1-4, species classification,
> allometric biomass, carbon stock, CO2e, or certified credits."

The Cameroon cohort carries harvested above-ground biomass per tree. That closes
the allometric exclusion directly, and it does so on tropical trees, which closes
the climate exclusion at the same time.

| gap | before | after P1 |
|---|---|---|
| tropical validation | none | 61 trees, 15 species, semi-deciduous |
| allometric vs harvested mass | never checked | measured, per tree |
| Chave vs T-VER | two unvalidated models agreeing | both scored against harvested mass |
| error attribution | unknown | measurement share vs equation share, separated |

The third row matters most for what comes next. `docs/ml/TVER_EQUATIONS.md`
currently ends: *"Neither model has been checked against a Thai tree, so this is
agreement between two unvalidated models, not validation."* Cameroon does not
make either of them Thai, but semi-deciduous tropical forest is the forest type
T-VER's `mixed_deciduous` row covers, and it is the forest type teak grows in.
It is the closest check available without field work.

The fourth row decides where effort goes afterwards, and is the reason the
design runs two routes rather than one (§5).

## 3. The cohort

**Momo Takoudjou, S. et al. (2018).** *Data from: Using terrestrial laser
scanning data to estimate large tropical trees biomass and calibrate allometric
models: a comparison with traditional destructive approach.* Dryad.
<https://doi.org/10.5061/dryad.10hq7>

| property | value |
|---|---|
| licence | **CC0 1.0** — public domain, no attribution condition |
| size | 1.15 GB, one file `Trees.rar` |
| trees | 61, destructively harvested |
| species | 15 |
| site | semi-deciduous forest, eastern Cameroon |
| DBH | 10.8 – 186.6 cm, mean 58.4 ± 41.3 |
| height | 8.7 – 53.6 m, mean 33.7 ± 12.4 |
| AGB | up to 60 Mg |
| scanner | Leica C10, ≥3 positions per tree |
| leaves | removed manually by the original authors |
| primary article | <https://doi.org/10.1111/2041-210X.12933> |

Compare the cohort already in use — Demol et al. 2021, Zenodo 4557401,
CC-BY-4.0, 65 Belgian temperate trees. Cameroon's trees are roughly three times
the diameter and twice the height. This is not a similar cohort in a different
place; it is a harder one.

**Unverified until the archive is opened.** The abstract and the article
establish that leaf-stripped point clouds and harvest measurements both exist,
but not their file layout, formats, or per-tree pairing. `load_cameroon_cohort`
cannot be written until `Trees.rar` is extracted and inspected. That inspection
is step 1 of the implementation order (§12) and its findings are recorded before
any evaluation code is written.

A second dataset provides context rather than input:

**Demol, M. et al. (2025).** *Global dataset of co-incident TLS-derived and
harvested tree biomass.* NERC EDS CEDA.
<http://data.ceda.ac.uk/neodc/tls/data/global/tls_tree_biomass/> — Open Access,
Permitted Use: Any, 4 files, 101 KB. 391 trees, 111 species, DBH 8.5–180.3 cm,
AGB 13.5–43,950 kg. Derived values only, no point clouds. Its authors include
Demol, Calders and Momo Takoudjou, so both cohorts used here appear in it. It is
how the resulting numbers get positioned against the published field, and it
belongs to P3, not P1.

## 4. Scope

**In scope.** Loading the Cameroon cohort; running the QSM geometry stage and
the allometric stage against it; scoring both against harvested ground truth;
attributing error between measurement and equation; comparing Chave 2014 against
T-VER `mixed_deciduous` on the same trees; publishing the result whatever it
says; and closing the three publication-surface drifts in §9.

**Out of scope, deliberately.**

- **Wood/leaf evaluation.** The Cameroon clouds are already leaf-stripped, so
  they cannot score stage 5. That work needs its own labelled cohorts and is P2.
- **Stages 1–4.** Cameroon trees are isolated, like Demol. Ground segmentation,
  normalization, CHM and tree segmentation remain unvalidated on real plots.
- **Any recalibration.** See §6. This is the load-bearing constraint.
- **Species classification.** Still a stub, and Cameroon's 15 species do not
  overlap the five target species.
- **Adopting T-VER as the default.** P1 measures it. Changing the number the
  product reports is a separate decision with its own evidence.

## 5. Architecture

Everything mirrors the Demol path, which already works. No new structural
concepts are introduced.

```
services/ml/pipeline/cameroon_eval.py           mirrors demol_eval.py
services/ml/scripts/derive_cameroon_evidence.py mirrors derive_demol_evidence.py
services/ml/tests/test_cameroon_eval.py         mirrors test_demol_eval.py
docs/evidence/cameroon_61/result.json           same schema as demol_65/result.json
docs/ml/CAMEROON_EVIDENCE_CHAIN.md              mirrors DEMOL_EVIDENCE_CHAIN.md
```

`cameroon_eval.py` reuses the shape of `demol_eval.py`: a frozen `CameroonTree`
dataclass, `load_cameroon_cohort()`, `evaluate_cameroon_cohort()`, `_aggregate()`.
The result document keeps the existing keys — `schema_version`, `dataset`,
`derivation`, `gate`, `metrics`, `per_tree`, `protocol` — and adds mass fields
that Demol has no ground truth for.

The new block joins `core_demo_manifest.json` under `validation.cameroon_61`,
which means `sync_truth.py --check`, the capability matrix, and the CI
verification step pick it up without further work.

### Two routes, one comparison

The cohort supplies both taped DBH and felled height alongside the point clouds.
Running the chain twice — once from the cloud, once from the tape — separates
two errors that are otherwise indistinguishable:

```
                    point cloud (leaf-stripped)      taped DBH, felled height
                              │                                │
                              ▼                                ▼
                    qsm.compute_qsm()                   (ground truth)
                    DBH, height, volume                          │
                              │                                  │
                              ├──────────► measurement error ◄───┤
                              ▼                                  ▼
                    allometric.calculate_carbon()   allometric.calculate_carbon()
                      Chave │ T-VER                   Chave │ T-VER
                              │                                  │
                              └────────► harvested AGB ◄─────────┘
```

- **Route B against harvested AGB** is the equation's error, with measurement
  removed. It is the first honest answer to "how wrong is Chave on a tropical
  tree", and the first to "is T-VER better".
- **Route A minus route B** is the measurement's contribution.
- **Route A against harvested AGB** is what a user of the product would get.

Without the split, a bad end-to-end number cannot be assigned to a cause, and
the next sprint would be a guess.

## 6. Cameroon is held out. This is not negotiable.

`qsm.TOTAL_TREE_FORM_FACTOR` is 0.587, measured on the 65 Belgian trees.
`pipeline/tver.py` already names the hazard of carrying it further:

> "0.587 was measured on 65 Belgian temperate trees; applying it to tropical
> crowns is the same category of mistake this module documents"

The tempting move, once Cameroon numbers look poor, is to refit the taper
constants on Cameroon and report the improvement. That is fitting and testing on
one dataset. It is the exact defect this project already punished PointNet++
for: `docs/PROJECT_SPEC.md` records that the Wan held-out split also selected the
best epoch, and the candidate is barred from promotion partly for it.

**Rule.** The evaluation runs with the constants calibrated on Belgium,
unchanged. Results are reported as they come out. Recalibration is permitted
only after a split is declared and committed *before* anyone looks at the
held-out half, and any recalibrated figure is reported separately from this one,
never in place of it.

`protocol` in `cameroon_61/result.json` records the constants used and the commit
they came from, so a later reader can check that this rule held.

## 7. Metrics

Geometry metrics keep the Demol field names exactly, so the two cohorts are
directly comparable:

`dbh_mae_cm`, `dbh_rmse_cm`, `dbh_bias_cm`, `dbh_mape_pct`, `dbh_within_10_pct`,
`dbh_worst_pct`, `dbh_worst_abs_cm`, `height_mae_m`, `height_rmse_m`,
`height_bias_m`, `height_mape_pct`, `height_within_10_pct`, `volume_mae_m3`,
`volume_mape_pct`, `volume_bias_m3`, `volume_within_10_pct`, `volume_worst_pct`

New, because Demol has no harvested mass:

| field | meaning |
|---|---|
| `agb_mape_pct`, `agb_bias_kg`, `agb_within_20_pct` | route A against harvested mass — what a user gets |
| `agb_equation_only_mape_pct` | route B: allometric error with measurement removed |
| `agb_measurement_share_pct` | route A minus route B |
| `chave_vs_tver` | Chave 2014 against T-VER `mixed_deciduous`, per tree and aggregate |

`within_20_pct` rather than the `within_10_pct` used for geometry: ±20% is the
band biomass models are conventionally judged in, and Chave 2014 does not claim
better. Both are reported, so a reader who disagrees can use the other.

`chave_vs_tver` uses `mixed_deciduous` because eastern Cameroon is
semi-deciduous forest, which is the row T-VER assigns that stand type. The
choice is recorded in `protocol` rather than inferred at read time. No other
T-VER row is scored: picking the best-fitting one after seeing the answers is
the selection error §6 exists to prevent.
| `dbh_bias_by_size_band` | bias in 4 DBH bands — the buttress question, measured |
| `ransac_inlier_ratio_by_size_band` | fit quality by size; the pipeline already computes it per tree and the field exists on `TreeResult` |

`dbh_bias_by_size_band` is the one to read first. `docs/ml/DBH_BIAS_AND_BARK.md`
established that the Belgian under-read of −0.80 cm is bark, ordered by fissure
depth, and not tree size — across trees far smaller than these. Whether that
holds at 186 cm, where the stem at 1.30 m is buttressed and is not a circle at
all, is unknown and is exactly what this band tells us.

## 8. Error handling

Reuse `ExcludedSegment` and its `reason_code`. A tree the pipeline cannot
measure is counted and named, never dropped — the behaviour
`PipelineDiagnostics` already enforces.

Two reason codes are added, both predicted rather than observed, and both are
removed from the design if the data does not produce them:

- `DBH_FIT_BUTTRESS_SUSPECT` — the breast-height circle fit returns a low inlier
  ratio on a large stem. The threshold is chosen from the measured distribution
  in step 4 of §12, not guessed now.
- `DBH_ABOVE_CALIBRATED_RANGE` — DBH exceeds the range the taper constants were
  fitted over. This one is a refusal, not a warning: the system declines to cost
  a tree it has never been checked on. It follows the precedent
  `calculate_carbon` already sets by refusing the T-VER pine row that predicts
  more mass than solid wood.

Refusing to answer is a feature here. A carbon number for a tree three times
larger than anything the constants were fitted on is worse than no number.

## 9. The publication surface

Three places publish figures that the pipeline no longer produces. All three
are the same defect — a number written once and never re-derived — and it is the
defect commit `f9f1773` ("the core demo published a pipeline three releases
old") closed for the core demo alone.

### 9.1 The live demo publishes carbon computed from densities since corrected

The committed demo artefacts were analysed at `e88e616`, **28 commits back**.
Five commits since then change what the pipeline reports:

| commit | effect |
|---|---|
| `8cf3058` | all five wood densities were air-dry; Chave takes basic |
| `4541f89` | refuse an equation predicting a mass the tree cannot have |
| `cf00f98` | the bark finding in DBH |
| `e0f11ba` | density provenance |
| `7fb408f` | DBH fit gate raised 0.20 → 0.80 |

The size of the error is not an estimate. `8cf3058`'s own commit message states
it:

> "Every carbon figure falls. Teak on a DBH 30 cm, H 20 m tree goes 1364 → 1091
> kg CO2e; **the judge demo goes 4748.95 → 3798.38.**"

<https://treeqcarbon.vercel.app/demo> reports **4,748.95 kg CO₂e** today, under
a `CHECKSUM VERIFIED` badge. The correct figure was computed on 2026-08-18 and
written into the commit that computed it. The public number overstates CO₂e by
**25%**.

The checksums are correct. They verify artefacts built by a pipeline that has
since been fixed. That is the failure mode worth naming: a verification badge
proves an artefact is unaltered, not that it is current.

No CI job guards this. `.github/workflows/` contains no reference to
`public/demo`, and `services/ml/tests/test_judge_demo.py` tests the generator —
reproducibility, path-freeness, provenance rejection — not whether the published
artefacts match the current pipeline.

**Fix.** A test that regenerates the demo artefacts and compares hashes against
the committed ones, wired into `CI Web` and `CI ML` on the paths that can change
them. It is the `--manifest` check that `f9f1773` added, applied to the artefacts
the public actually sees.

### 9.2 README publishes pre-correction accuracy figures

| field | `README.md:85-87` | `core_demo_manifest.json` → `validation.demol_65` |
|---|---:|---:|
| DBH MAE | 1.1673846154 cm | **0.898318** |
| Height MAE | 0.5446153846 m | **0.543323** |
| Volume MAPE | 18.7650916186 % | **11.520556** |

`docs/ml/DEMOL_EVIDENCE_CHAIN.md:97` labels the left column "published before"
and shows the right one is 23% and 39% better. `AGENTS.md` and
`docs/PROJECT_SPEC.md` carry the same stale values. The live site already shows
the correct 0.90.

`sync_truth.py --check` passes, and correctly: `validate_demol` now compares the
manifest against a re-derivable artefact, which was the right fix. What it does
not do is compare the manifest against the markdown tables that quote it.

This under-sells the pipeline rather than over-selling it, which makes it a
smaller ethical problem and an equally large truth problem. `README.md` is
listed as current truth in `docs/DOCUMENT_STATUS.md`.

**Fix.** Extend `sync_truth.py` to parse the published figures out of the
markdown tables in `README.md`, `AGENTS.md` and `docs/PROJECT_SPEC.md` and
require them to equal the manifest. The same check then guards the Cameroon
block from the day it is added.

### 9.3 Deleted capabilities still claimed

`apps/mobile/` has zero tracked files and does not exist on disk; it was removed
at `8ce6021` under `docs/decisions/0007-drop-the-photo-path.md`. Still claiming
it:

- `README.md:57` — capability table: "Mobile capture flow | Experimental"
- `docs/CAPABILITY_MATRIX.md:21` — cites `apps/mobile/lib/main.dart` as evidence
- `README.md:178`, `AGENTS.md:31`, `AGENTS.md:72`
- `.github/workflows/ci-ml.yml` — watches `apps/mobile/README.md`

`apps/web/src/app/page.tsx:34` tells visitors the system accepts *"ภาพถ่ายทาง
อากาศ"*. ADR 0007 removed that path.

**Fix.** Delete the claims. Add a test that fails when the capability matrix
cites a file that does not exist — the matrix is generated from the manifest, so
the evidence path is data and can be checked.

## 10. File map

| file | change |
|---|---|
| `services/ml/pipeline/cameroon_eval.py` | new |
| `services/ml/scripts/derive_cameroon_evidence.py` | new |
| `services/ml/tests/test_cameroon_eval.py` | new |
| `services/ml/tests/test_published_artifacts_are_current.py` | new — §9.1 |
| `services/ml/pipeline/qsm.py` | add the two reason codes; no constant changes |
| `services/ml/pipeline/allometric.py` | expose route-B costing from supplied DBH/H |
| `scripts/sync_truth.py` | check markdown tables against the manifest — §9.2 |
| `docs/evidence/cameroon_61/result.json` | new, committed whatever it says |
| `docs/evidence/core_demo_manifest.json` | add `validation.cameroon_61` |
| `docs/ml/CAMEROON_EVIDENCE_CHAIN.md` | new |
| `docs/ml/WHAT_CI_DOES_NOT_CHECK.md` | add the new skips |
| `docs/CAPABILITY_MATRIX.md` | regenerated; mobile row removed |
| `README.md`, `AGENTS.md`, `docs/PROJECT_SPEC.md` | corrected figures; mobile claims removed |
| `apps/web/src/app/page.tsx` | remove the aerial-photograph claim |
| `apps/web/public/demo/*` | regenerated at HEAD |
| `.github/workflows/ci-ml.yml` | drop the `apps/mobile/README.md` path; add the artefact gate |
| `services/ml/.gitignore` scope | `data/raw/dryad_cameroon/` excluded, as `zenodo_belgium` is |

## 11. Testing and CI

`test_cameroon_eval.py` follows `test_demol_eval.py`: skip when the cohort is
absent, with a reason `-rs` prints, and record the new skips in
`WHAT_CI_DOES_NOT_CHECK.md` beside the existing table. The gap between "passed
in CI" and "passed with the data" stays visible, which is the property that file
exists to preserve.

The §9 gates run in CI and must not skip. They need no cohort — they compare
committed artefacts against a pipeline CI already builds.

## 12. Implementation order

1. **Close §9.** The publication surface is wrong today, the public number is
   25% high, and none of the fix depends on the cohort. Doing it first also
   means the Cameroon block is guarded by the extended `sync_truth` from the
   moment it lands. Start the 1.15 GB download alongside it.
2. **Open the archive and write down what is in it.** Extract to
   `services/ml/data/raw/dryad_cameroon/`, record formats, per-tree pairing and
   the harvest columns in `CAMEROON_EVIDENCE_CHAIN.md`. No evaluation code is
   written until this exists, because §5 assumes a layout nobody has seen.
3. `load_cameroon_cohort()` and its tests.
4. Route A: geometry against taped DBH and felled height. Read
   `dbh_bias_by_size_band` and decide the `DBH_FIT_BUTTRESS_SUSPECT` threshold
   from the measured distribution.
5. Route B and the mass metrics; Chave against T-VER.
6. Derive, commit, wire into the manifest, regenerate the capability matrix.
7. `CAMEROON_EVIDENCE_CHAIN.md`, written the way `DEMOL_EVIDENCE_CHAIN.md` is:
   what was expected, what was measured, and where they differ.

## 13. Acceptance criteria

- `docs/evidence/cameroon_61/result.json` exists, is committed, and
  `derive_cameroon_evidence.py --check` re-derives it byte-for-byte.
- The manifest carries `validation.cameroon_61` and `sync_truth.py --check`
  passes with the markdown check enabled.
- Every published accuracy figure in `README.md`, `AGENTS.md` and
  `docs/PROJECT_SPEC.md` equals the manifest, enforced by a test.
- The committed demo artefacts regenerate to identical hashes at HEAD, enforced
  by a test that runs in CI.
- No document claims a capability whose evidence file does not exist.
- `protocol` records the taper constants and their origin commit, and they are
  Belgium's.
- The result is committed and published whether it is good or bad.

## 14. What the result is likely to be

A prediction, recorded before the measurement so it can be scored:

**The geometry will degrade, most at the large end.** RANSAC circle fitting at
1.30 m assumes a circular cross-section. Large tropical trees are buttressed at
that height, and the mean DBH here is 58 cm against Belgium's much smaller
trees. `dbh_bias_by_size_band` should show the top band diverging.

**The volume figure will degrade more.** The taper equations were fitted to
temperate stems whose form differs from a 50 m tropical emergent, and the whole
form factor is Belgian.

**The equation comparison is genuinely open.** Chave 2014 is a pantropical fit
and Cameroon is inside its domain, so route B may do well even where route A
does not. If that happens, the finding is that the measurement is the weak link,
not the allometry — which points the next sprint at stage 6 rather than stage 8.

If these predictions hold, P1 produces the sentence:

> A carbon pipeline calibrated on temperate trees reports AGB with X% error on
> large tropical trees, of which Y% is measurement and Z% is allometry.

That is worth publishing, and people running REDD+ projects in the tropics want
to know it. `docs/evidence/pointnet_independent_eval/result.json` is already
committed carrying `FAIL_METRICS`; this follows that precedent.

## 15. What P1 still does not validate

Stated here so it cannot be forgotten when the numbers are quoted:

- **Stages 1–4.** Isolated trees again. No real plot has been validated
  end-to-end.
- **Stage 5.** The Cameroon clouds arrive leaf-stripped. Wood/leaf remains
  scored only on the external cohort at 0.196.
- **Stage 7.** Still a stub.
- **Thailand.** Cameroon is tropical, semi-deciduous, and not Thai. T-VER is a
  Thai methodology being scored on African trees. That is closer than anything
  available today and is not the same as validation in Thailand.
- **Carbon credits.** Unchanged. Nothing here makes any output a tradable or
  certified credit.

---

## Appendix: the program this belongs to

| # | sub-project | closes | data | depends on |
|---|---|---|---|---|
| **P1** | this document | tropical geometry + allometry; publication surface | Dryad CC0, 1.15 GB | — |
| P2 | tropical wood/leaf benchmark | stage 5 on tropical trees; LeWoS and PointsToWood as baselines | ISPRS 148-tree cohort, Paracou (Zenodo 8398853), Shivalik, Owen et al. (Zenodo 13268500) | independent of P1 |
| P3 | global context | positions our figures against 391 published trees | CEDA, 101 KB | P1 |
| P4 | the evidence framework as the contribution | the writeup | none | P1–P3 |

P4 is where the novelty is. The fail-closed promotion gate, `sync_truth`, the
generated capability matrix and the T-VER physical-possibility finding are not
things other forest-carbon repositories have, and the finding that a national
methodology publishes an equation exceeding the mass of solid wood is the
demonstration that makes the case for the framework better than any description
of it would.

## Appendix: an unresolved product question

The landing page argues that the system lowers cost and reaches remote farmers.
That argument was built for the phone-photograph path, which ADR 0007 removed.
A scanner-only system requires the user to already own a TLS instrument.

The honest user of this system is someone who has scans and needs them turned
into defensible carbon numbers with provenance: a forest researcher, a
verification body, an organisation that has commissioned a survey. Not a farmer.

This is not a copy edit and it is not in P1's scope. It is recorded here because
the landing page will keep making a claim the architecture no longer supports
until it is decided.
