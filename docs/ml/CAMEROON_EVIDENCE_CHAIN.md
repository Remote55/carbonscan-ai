# What is actually inside the Cameroon archive

Written from the extracted files on 2026-08-20, not from the paper. Where the
archive and the publication disagree, both are recorded and the archive wins,
because the archive is what the evaluation will read.

## The dataset

**Momo Takoudjou, S., Ploton, P., Sonké, B., Hackenberg, J., Griffon, S.,
de Coligny, F., Kamdem, N. G., Libalah, M., Mofack, G. I., Le Moguédec, G.,
Pélissier, R., & Barbier, N. (2018).** *Data from: Using terrestrial laser
scanning data to estimate large tropical trees biomass and calibrate allometric
models: a comparison with traditional destructive approach.* Dryad.
<https://doi.org/10.5061/dryad.10hq7>

Primary article: <https://doi.org/10.1111/2041-210X.12933>

| property | value |
|---|---|
| licence | **CC0 1.0** — public domain dedication, no attribution condition |
| downloaded | 2026-08-20, through the dataset page in a browser |
| file | `Trees.rar` |
| size | 1,018,816,227 bytes |
| MD5 | `8a847165f17e1e08ab5139db3a3cdf9c` |
| SHA-256 | `a12b7903d4d50a5987c16ae453f66a44e5de5dc1a7eaf280aa4343ac3bfbbb64` |
| extracted | 802 files, 4,627,468,471 bytes |
| location | `services/ml/data/raw/dryad_cameroon/` — excluded by `services/ml/.gitignore:26` (`data/raw/`) |

The MD5 is Dryad's own published digest, read from its API, so the download is
verified against the source rather than against a hash computed here. **Neither
the API download endpoint nor `file_stream` serves the archive**: the first
answers `401 must have current bearer token`, the second `403`, or an HTML page
when given a browser User-Agent. The file has to come through the dataset page.

## Layout

```
Trees/
├── database.xls          87,552 bytes — the ground truth, two sheets
├── Readme.txt            92 bytes — an email address, nothing else
├── Points_clouds/        62 directories, one .txt each
├── Edited_QSMs/          61 directories, one .csv each
├── Un-edited_QSMs/       396 .csv, 134 .ply, 41 .png
└── Stumps/               30 .wrp, 39 .txt, 6 .csv, 2 .asc, 2 .ply
```

## The ground truth

`database.xls`, sheet `datafinal_test2`: **61 data rows**, 34 columns, every row
sourced `Momo et al. (2017)`. Sheet `Meta_data` defines the columns.

Columns the evaluation needs:

| column | meaning, verbatim from `Meta_data` | unit |
|---|---|---|
| `ID` | Individual | — |
| `Genus`, `Species` | — | — |
| `DBH_dest` | "Diameter at breast height **or above buttresses if present** from destructive sampling" | cm |
| `H_tot_dest` | "Destructive Total height" | m |
| `Destructive AGB` | "Total aboveground biomass" | **Mg** |
| `WSG_ind` | "Individual wood density taken from all compartments" | g/cm³ |
| `Destructive stem/crown/stump/total volume` | — | m³ |
| `DBH_L` | "Diameter at breast height or above buttresses if present **from Terrestrial Laser Scanner**" | cm |
| `Hauteur_L` | "Total tree height **from Terrestrial Laser Scanner**" | m |

Measured ranges over the 61 rows:

| column | min | max | mean |
|---|---:|---:|---:|
| `DBH_dest` | 11.3 | 180.3 | 59.41 |
| `H_tot_dest` | 9.7 | 60.15 | 34.43 |
| `Destructive AGB` | 0.026 | 43.945 | 6.82 |
| `WSG_ind` | 0.337 | 0.813 | 0.535 |
| `DBH_L` | 10.8 | 186.6 | 58.17 |
| `Hauteur_L` | 8.794 | 53.624 | 33.73 |

**The ranges quoted in the abstract are the TLS columns, not the destructive
ones.** "diameters and AGB of up to 186.6 cm" is `DBH_L`; the largest tree
actually measured on the ground is 180.3 cm. Anything citing 186.6 cm as a
harvested diameter is citing a laser estimate.

Fifteen species. Most frequent: *Terminalia superba* (9), *Triplochiton
scleroxylon* (6), *Petersianthus macrocarpus* (6), *Pterocarpus soyauxii* (6).

## Is the biomass dry or fresh? Dry.

`Meta_data` says only "Total aboveground biomass (in Mg)". The moisture basis
decides whether comparing against Chave 2014 means anything at all, so it was
settled arithmetically rather than assumed.

Wood specific gravity is oven-dry mass over green volume, and `WSG_ind` is given
in g/cm³, which is numerically Mg/m³. So if `Destructive AGB` is an oven-dry
mass, dividing it by volume × WSG should give 1.

| ratio | n | median | mean | min | max |
|---|---:|---:|---:|---:|---:|
| `AGB / (total volume × WSG_ind)` | 61 | **1.0074** | 1.0045 | 0.899 | 1.159 |
| `AGB / ((total − stump) volume × WSG_ind)` | 61 | 1.1256 | 1.1520 | 0.948 | 1.417 |

Two conclusions, both load-bearing:

1. **`Destructive AGB` is oven-dry mass** — the quantity Chave 2014 predicts. A
   green mass would have landed near 1.5–2.5. The comparison is meaningful.
2. **It includes the stump.** The stump-exclusive ratio is 1.13, not 1.00, so
   subtracting the stump would introduce a 13% error.

The residual scatter (0.899–1.159) is expected: AGB was summed compartment by
compartment with each compartment's own density, while `WSG_ind` is one
whole-tree average.

## The point clouds

`Points_clouds/ID_<n>/<n>_sans_feuilles.txt` — one directory per tree, one file
inside. *Sans feuilles* is "without leaves": these are the manually leaf-stripped
clouds, which is why this cohort cannot score stage 5.

Format: **tab-separated X Y Z, no header, plain text, metres.** Coordinates are
in the scanner's own frame — Z is negative in places, so no normalisation has
been applied. **True for 56 of the 61 required trees. The other five are not
tab-separated, or carry a header, or both — see below before trusting this
sentence for a specific tree.**

```
14.735	3.469	-1.637
14.724	3.466	-1.728
14.749	3.410	-1.673
```

Mapping to the ground truth is by the integer in the directory name against
`ID`. IDs are not contiguous: 1–8, 11, 12, 15, 18, 28, 29, 31, 32, 52, 54–57,
59–76, 79, 80, 83, 85, 87–89, 91–106.

### Five clouds are not "tab-separated X Y Z, no header"

Found the same way `ID_56` was: by attempting to load all 61 required trees,
not by inspecting the archive up front.

| tree | file | irregularity |
|---|---|---|
| 31 | `31_sans_feuilles.txt` | opens with a one-line header, `"V1" "V2" "V3"` (an R `write.table` artefact) |
| 52 | `52_sans_feuilles.txt` | same header |
| 59 | `59_sans_feuilles.txt` | opens with `//X Y Z Scalar_field` (a CloudCompare comment) and carries a fourth column |
| 63 | `ID63_sans_feuilles.txt` | comma-delimited throughout, no header |
| 68 | `68_sans_feuilles.txt` | comma-delimited throughout, no header |

Every other line in all five is an ordinary X Y Z row once the header is
dropped and commas are read as the delimiter — nothing about the coordinates
themselves is unusual, and the fourth column on 59 is simply not read.
`pipeline/cameroon_eval.py`'s `_load_cloud` repairs the text and retries
through the same unmodified `demol_eval._load_xyz` rather than skipping the
tree: a cohort that quietly dropped five more trees on top of `ID_56` would be
the exact failure this evaluation exists to catch. The other 56 files are
untouched by this path and go through `_load_xyz` exactly as written.

### One tree has a cloud and no ground truth

**62 point-cloud directories, 61 database rows.** `ID_56` has
`Points_clouds/ID_56/` and no row in `database.xls`. Nothing in the archive
explains it. The loader must key on the database rather than on the directory
listing, or the cohort will silently become 62 trees, one of which cannot be
scored.

This is why the paper says 61 and the directory says 62.

## The authors' own TLS measurement fails on buttressed trees

`DBH_L` is the cohort authors' TLS-derived diameter, produced by their own
pipeline. Comparing it against `DBH_dest` measures their method, not ours — and
it is worth recording before ours runs, because it sets the bar and shows where
the difficulty is.

| cohort | n | mean `DBH_L − DBH_dest` | min | max |
|---|---:|---:|---:|---:|
| all trees | 61 | −1.24 cm | −63.60 | +26.10 |
| `DBH_dest` < 50 cm | 31 | **+0.30 cm** | −4.10 | +16.10 |
| `DBH_dest` ≥ 100 cm | 10 | **−6.29 cm** | −63.60 | +6.30 |

On trees under 50 cm the laser and the tape agree to a third of a centimetre. On
trees over a metre the laser can be 63 cm low. That is the buttress problem, and
it appears in a published reference implementation — so a comparable failure in
this pipeline is a property of the measurement problem at 1.30 m, not evidence
that the code is uniquely bad.

The `Meta_data` wording is the reason: both `DBH_dest` and `DBH_L` are taken
"at breast height **or above buttresses if present**". The ground truth is
therefore not always at 1.30 m, while `qsm.py` always fits its circle there.
**Comparing our DBH against `DBH_dest` on a buttressed tree is not comparing the
same measurement**, and the evaluation has to say which trees those are rather
than average over them.

## Also in the archive, not yet used

- `Edited_QSMs/ID_<n>/<n>.csv` — 61 files, one per tree, cylinder tables with
  columns `Id, Lenght, TopWidth, Width, Volume, XX1, XX2, YY1, YY2, ZZ1, ZZ2`.
  These are the authors' hand-corrected QSMs and are the reference this
  pipeline's volumes can be compared against.
- `Un-edited_QSMs/` — the same before correction, with `.ply` renderings.
- `Stumps/` — separate stump scans, `.wrp` (Geomagic) and `.asc`.
- `database.xls` also carries `TLS un-edited` and `TLS edited` volumes per
  compartment, and a `_5` family of columns excluding branches under 5 cm
  diameter.

## What the archive does not answer

- **Why `ID_56` has no ground-truth row.** Excluded during harvest, lost, or a
  numbering error — nothing says.
- **Which trees were buttressed**, and for those, at what height `DBH_dest` was
  actually taken. `Meta_data` says "or above buttresses if present" and gives no
  per-tree flag. This is the largest open question for the evaluation, because it
  decides which trees a 1.30 m circle fit can be scored against at all.
- **The scanner's registration error**, and whether the clouds are single-scan or
  registered multi-scan. The article says at least three positions per tree; the
  archive carries no per-tree registration residual.
- **Point spacing per tree.** The Demol cohort ships downsampled to 10–15 mm and
  says so; nothing here states a spacing, so it has to be measured per cloud
  before any density-sensitive claim.
- **Whether `WSG_ind` is the density used to build `Destructive AGB`**, or an
  independent measurement. The ratio near 1.00 says they are consistent; it does
  not prove they are independent, so `WSG_ind` must not be treated as an
  independent check on the biomass.

## Provenance of this document

Every number here was computed from the extracted archive on 2026-08-20 with the
project virtualenv, reading `database.xls` through `xlrd` and the point clouds
directly. `xlrd` was installed into the virtualenv to read the file and is
deliberately **not** a project dependency — nothing in the pipeline reads `.xls`.

## Evaluation results

Derived 2026-08-20 by `services/ml/scripts/derive_cameroon_evidence.py`, committed
at `docs/evidence/cameroon_61/result.json` (sha256
`6fdf6121b9c1e7dca984ff46eac8846fae39d0bdb5c4b7a3563cccb14de2e231`), wired into
`docs/evidence/core_demo_manifest.json` as `validation.cameroon_61`. Reproduce
with:

```bash
cd services/ml && .venv/Scripts/python.exe scripts/derive_cameroon_evidence.py --check
```

`qsm.py`'s taper constants (`TOTAL_TREE_FORM_FACTOR = 0.587`, `STEM_FORM_FACTOR
= 0.403`) are unchanged from `baa1128`, where they were fitted on the 65
Belgian Demol trees. Nothing here recalibrated them, per the spec's section 6.
`max_points = 20,000`, `sample_seed = qsm_seed = 0`, matching the Demol
protocol so the two cohorts sit in one table. 61 trees in the ground truth, 62
clouds available (`ID_56` excluded — no destructive row). 60 of 61 produced a
measurement.

Read in the order below, because each item depends on the one before it to
mean anything.

### 1. The headline: DBH where the tape and the fit describe the same thing

`dbh_mae_cm_small_stems` (`gt_dbh_cm` < 50 cm, n=31, the subset where
buttressing is not a confound): **1.68 cm**, bias -0.83 cm.

Demol (65 temperate Belgian trees, all sizes, no size restriction needed):
0.90 cm. This pipeline is worse on tropical stems even restricted to the fair
comparison — about 1.9x the error — but not badly worse, and in the same
order of magnitude as the archive's own published TLS method, which agrees
with the tape to a mean **+0.30 cm** bias on this exact 31-tree subset (a bias,
not an MAE, so not perfectly like-for-like, but the closest number available).
This pipeline's bias on the same 31 trees is -0.83 cm, and its error against
that same reference method (not the tape) is -1.13 cm bias / 2.08 cm MAE.

### 2. DBH by size band: does it degrade more than a published method on the same clouds

| band | n | bias vs tape (cm) | MAE vs tape (cm) | bias vs reference TLS (cm) | MAE vs reference TLS (cm) | mean fit quality |
|---|---:|---:|---:|---:|---:|---:|
| under 50 cm | 31 | -0.83 | 1.68 | -1.13 | 2.08 | 0.913 |
| 50-100 cm | 20 | +8.86 | 11.55 | +9.97 | 16.65 | 0.496 |
| 100 cm and over | 9 | -41.68 | 43.56 | -34.79 | 35.60 | 0.334 |

Published reference (`DBH_L`, measured from the archive before any of this
pipeline's code ran — see above): mean bias +0.30 cm under 50 cm (31 trees),
-6.29 cm at 100 cm and over (10 trees — one more than the 9 this pipeline
could measure; tree 60 at 120.5 cm is the difference, see item 5).

The spec's section 14 asked a narrower question than "does it degrade": does
it degrade **more than a published method on the same clouds**. It does, by a
wide margin — -41.68 cm mean bias here against the reference method's -6.29 cm
on a near-identical band. This pipeline is not merely finding the large-tree
problem every method finds in this archive; it is finding it considerably
harder than a competent published implementation does.

Part of the reason is structural rather than a fit-quality problem alone.
`qsm.measure_dbh` calls `_ransac_circle_fit` with its default
`max_radius_m=0.6`, and that function rejects every candidate circle with a
radius above 0.6 m **during the RANSAC search itself**, not only in the
`np.clip(dbh_cm, 0.0, 120.0)` line that runs afterward. A trunk whose true
diameter exceeds 120 cm cannot be correctly measured by this code **by
construction**, independent of point density or scan quality: the search
space the fitter is allowed to consider never contains the right answer. Five
of the nine trees in the "100 cm and over" band have a taped DBH above 120 cm
(2, 6, 12, 64, 100 — 134.5 to 180.3 cm), and across all 60 measured trees the
largest reported `measured_dbh_cm` is 117.9 cm — no tree, however large, is
ever reported above that. Checked directly: none of the five has a sparse
breast-height slice (tree 100 has 24,713 raw points there, tree 12 has
15,881), so this is the ceiling operating as designed, not a data shortage.
The constant is commented in `qsm.py` as calibrated for "the species in
scope" — the Belgian genera plus the five Thai species this product targets,
none of which run this large. It was not raised for this evaluation, per the
spec's section 6 (no recalibration on this cohort), and this finding should
not be read as evidence the constant is wrong for its intended targets —
only that it makes any Cameroon tree over 120 cm diameter unmeasurable by
this pipeline regardless of scan quality, which is a sharper and more
specific claim than "large trees are hard here."

Below that ceiling, large stems are still frequently poor for reasons the
ceiling does not explain: tree 5 (107.0 cm) reads -40.45 cm off, tree 99
(108.5 cm) reads 0.02 cm off, both under 120 cm. Mean fit quality in the
50-100 cm and 100-and-over bands (0.496 and 0.334) sits well under the 0.80
`MIN_DBH_FIT_QUALITY` gate applied elsewhere in the pipeline (`single_tree.py`,
`main.py`, not this evaluation, which calls `compute_qsm` directly — see the
`gate` block in `result.json`). Most of this pipeline's large-tree
measurements here would have been refused outright rather than reported, had
that gate applied.

### 2b. What the product actually reports, which is not what section 2 measures

The paragraph above says the gate would have refused most large-tree
measurements. That was left qualitative, and quantifying it changes the
headline:

| population | n | DBH MAE |
|---|---:|---:|
| every measurable tree | 60 | 11.25 cm |
| **trees the shipped gate reports** | **27** | **1.37 cm** |
| stems under 50 cm (the unconfounded subset) | 31 | 1.68 cm |

`main.py:244` and `single_tree.py:165` both refuse any stem scoring below
`qsm.MIN_DBH_FIT_QUALITY` (0.80) and emit `QSM_LOW_FIT_QUALITY` instead of a
number. This evaluation bypasses that, correctly, because it is measuring the
geometry stage rather than the product — but it means the 11.25 cm figure
includes 33 trees the pipeline would have declined to measure. **All five trees
over the 120 cm ceiling are among them**, scoring 0.205 to 0.556.

So the number a user of this pipeline receives is 1.37 cm across 27 tropical
trees, against Demol's 0.90 cm on 65 temperate ones. Publishing only the
all-measurable figure understated the shipped product by a factor of eight.
That is the same defect as publishing a superseded accuracy figure, pointing
the other way — a claim the evidence does not support, made against ourselves,
and this project has now made it in both directions.

Note the gate-applied figure is *better* than the small-stem one. The gate is
not a size filter: it refuses badly-fitted small stems too, and 6 of the 31
trees under 50 cm fail it — trees 3, 15, 32, 69, 79 and 93.

**The gate is not a correctness test and does not catch everything.** Tree 95
scores a perfect 1.000 and reads 11.48 cm against a taped 20.4 — a 44% error
reported with full confidence. `result.json` names it in
`metrics.gate_passed_worst_tree` so the limit travels with the figure.

### 2c. Why the 120 cm ceiling was not raised

The obvious response to section 2 is to raise `max_radius_m` from 0.6. It was
measured before being attempted, and the measurement says not to.

**Raising the bound trades a systematic underestimate for an unstable one.**
Refitting the five over-ceiling trees at successively looser bounds, and two
controls that the shipped bound already measures well:

| tree | taped | r@0.6 | r@1.0 | r@1.5 | r@2.0 |
|---|---:|---:|---:|---:|---:|
| 6 | 165.0 | 94.3 | 191.7 | 229.9 | 229.9 |
| 12 | 180.3 | 102.7 | 197.6 | 197.6 | 197.6 |
| 100 | 153.4 | 56.7 | 161.6 | 161.6 | **379.3** |
| 99 | 108.5 | **108.5** | 108.5 | **256.8** | 256.8 |
| 57 | 98.8 | 117.9 | **129.9** | 129.9 | 129.9 |
| 1 | 34.0 | 34.0 | 34.0 | 34.0 | 34.0 |

Tree 99 is measured exactly right at the shipped bound and destroyed at 1.5.
Tree 57 gets worse at 1.0. The giants improve in magnitude but overshoot on
four of five. Small trees are untouched throughout.

**More points do not fix it either.** Holding the bound at 0.6 and raising
`max_points` from 20,000 to 400,000 — twenty times the data, with the
breast-height slice growing from 9 to 214 points on tree 12:

| tree | taped | 20k | 100k | 400k |
|---|---:|---:|---:|---:|
| 12 | 180.3 | 102.7 | 87.4 | 55.8 |
| 100 | 153.4 | 56.7 | 89.3 | 111.4 |
| 5 | 107.0 | 66.5 | 66.9 | 67.1 |

Tree 12 gets *worse* with twenty times the points. Tree 5 does not move for
either the bound or the budget.

**The reason is that there is no circle to find.** Measured fit-free — bin each
breast-height slice into 36 sectors around its own centroid, and take the
standard deviation of point-to-centroid distance:

| tree | taped | slice points | sectors occupied | radial spread |
|---|---:|---:|---:|---:|
| 1 | 34.0 | 272 | 35/36 (97%) | **2.0 cm** |
| 57 | 98.8 | 393 | 32/36 (89%) | 40.2 cm |
| 2 | 134.5 | 195 | 30/36 (83%) | 42.8 cm |
| 100 | 153.4 | 109 | 27/36 (75%) | 54.1 cm |
| 99 | 108.5 | 448 | 22/36 (61%) | 46.5 cm |
| 6 | 165.0 | 31 | 11/36 (31%) | 52.8 cm |
| 12 | 180.3 | 9 | 5/36 (14%) | 12.2 cm |

Tree 1, which the pipeline measures exactly, has its points at a near-constant
distance from the centre — a ring, which is what a circular trunk is. Every
large tree scatters by 40 to 54 cm. **The cross-section at 1.30 m on these
trees is not a circle**, so a circle fit has no correct answer available at any
search bound. The bound is the only thing keeping the output in a plausible
range, which is why loosening it produces 379 cm on tree 100.

That reframes the ceiling. It is not a wrong constant to be corrected; it is a
guard rail on a model that does not apply to buttressed stems. Making the model
apply — fitting a non-circular cross-section, or measuring above the buttress
as the cohort's own field crew did — is real work and is not a constant change.
Until then the honest behaviour is the one the pipeline already has: refuse.

### 3. Route B: how wrong is Chave on a tropical tree, with measurement removed

Costed from the tape and the felled height directly — no point cloud, no QSM.

| model | mean APE | median APE | predicted/harvested ratio (median, range) |
|---|---:|---:|---|
| Chave 2014 | 23.44% | **14.00%** | 1.096 (0.709-2.326) |
| T-VER `mixed_deciduous` | 30.46% | 20.85% | 0.981 (0.494-2.113) |

(These ratios reproduce Task 4's ad hoc pre-commit check — median 1.0962,
range 0.709-2.326 for Chave and median 0.9807, range 0.494-2.113 for T-VER —
essentially exactly, which is the wiring sanity check the plan asked for.)

Chave 2014 is closer to the harvested mass on more trees (37 of 61) than
T-VER (24 of 61), and closer on both aggregate statistics. `TVER_EQUATIONS.md`
currently ends "agreement between two unvalidated models, not validation" —
this is the first time either has been scored against a weighed tree, and
Chave wins that score. T-VER's median ratio (0.981) sits closer to 1 than
Chave's (1.096), though: its higher APE comes from a wider spread of per-tree
misses (range 0.494-2.113 against Chave's 0.709-2.326 is similar in width but
centered differently), not from being more biased on the typical tree.

### 4. measurement_share_pct: does the error live in stage 6 or stage 8

| model | route A mean / median APE | route B mean / median APE | measurement share, mean / median |
|---|---:|---:|---:|
| Chave | 38.28% / 27.30% | 23.44% / 14.00% | +14.56 / +5.80 pts |
| T-VER | 39.59% / 29.30% | 30.46% / 20.85% | +9.42 / +4.11 pts |

On the median tree, measurement adds a real but secondary amount of error —
for Chave, about a fifth of route A's total (5.80 of 27.30 points), the rest
being the equation's own miss even when fed the tape directly. The mean tells
a different-shaped story, pulled up by a right-skewed handful of trees where
measurement error dominates completely: tree 89 (61.4 cm) has a Chave
measurement share of +200.87 points — the point-cloud measurement made that
tree's AGB estimate far worse than the tape would have. Tree 104 (98.5 cm)
has -49.78 points — the opposite, the measurement more accurate than the
tape-derived route. Both patterns exist in this cohort. The typical-tree
finding (allometry is the larger share of route A's error) is the opposite
emphasis from what the spec's prediction implied, and it would be actively
misleading applied to any one specific large or poorly-fit tree, where
measurement can dominate entirely in either direction.

### 5. Excluded: 1 of 61

| tree | taped DBH | taped height | reason |
|---|---:|---:|---|
| 60 (*Erythrophleum suaveolens*) | 120.5 cm | 44.5 m | fewer than 5 wood points survived at breast height after the point-budget cap; `measure_dbh` returned `(0.0, 0.0)` |

Checked directly rather than assumed: tree 60's **raw, uncapped** cloud (2.45
million points) has 630 points in the 1.15-1.45 m breast-height slice — a
healthy count, comparable to other trees. The `max_points=20,000` cap this
protocol shares with Demol subsamples that down to roughly 11, too few for a
reliable fit. This is the caveat `DEMOL_EVIDENCE_CHAIN.md` already carries in
the abstract — "it measures a pipeline running at one tenth the product's
point budget" (the product defaults to 200,000) — made concrete: at this
cohort's point budget, one tree's breast-height slice starves specifically
because of the cap, not because the data was not there. `max_points` was
fixed before this run per the spec's instruction not to tune it after seeing
a result, so this tree stays excluded rather than re-measured at a different
budget.

Separately, and independently of the exclusion: tree 60's cloud never
reaches above 17.7 m in height, raw and uncapped, though its taped/felled
height is 44.5 m. Most plausibly this is a ground-based TLS occlusion limit
on this specific emergent — the archive states at least three scan
positions per tree but carries no per-tree registration or occlusion record,
so this is an inference, not a confirmed cause. Had this tree been
measurable for DBH, its reported height would have been wildly wrong for a
reason entirely outside this pipeline's control.

### The repaired clouds carry no visible penalty

Five trees (31, 52, 59, 63, 68) had their raw point-cloud text repaired
before parsing — see `IRREGULAR_CLOUD_FORMAT_TREE_IDS` in
`pipeline/cameroon_eval.py` and "Five clouds are not..." above.
`cloud_was_repaired=true` for exactly these five in every `per_tree` row in
`result.json`, and none of the five is the excluded tree or an extreme
outlier: their DBH errors (-1.91, -0.39, -0.32, -9.71, -0.58 cm for 52, 59,
68, 63, 31 respectively) sit inside the same range as unrepaired trees of
comparable size. The one double-digit error among them (tree 63, -9.71 cm at
90.5 cm DBH) is consistent with the 50-100 cm band's general pattern, not
with a parsing artefact.

### Volume

`volume_mape_pct` (measured total volume vs the destructive total, oven-dry,
stump-inclusive, 60 measurable trees): **33.28%**, against Demol's 11.52%.
`volume_vs_reference_qsm_mape_pct` (against the authors' own edited QSM
total, the fairer basis — both are what a QSM can see, see
`data/cameroon_61/README.md`): a similar 29.95%.

The spec predicted volume would degrade more than DBH, and it does, on both
cohorts: Demol's own DBH-to-volume MAPE ratio is about 3.7x (3.07% to
11.52%); Cameroon's is about 2.6x (12.96% to 33.28%). So this ordering is not
unique to the tropical cohort — it already held for Demol, at a smaller
absolute scale — but the absolute volume error here is far worse,
consistent with a form factor calibrated on four Belgian genera of a very
different size and taper being applied to trees up to three times their
diameter.

Worst single-tree volume miss: tree 12 (*Triplochiton scleroxylon*, the
cohort's largest at 180.3 cm DBH, 54.2 m tall), measured at 24.2 m3 against a
destructive 92.9 m3 and a reference QSM of 98.0 m3 — two independent
figures that agree the tree is roughly four times the volume this pipeline
reported. Tree 12 is one of the five trees item 2's 120 cm ceiling predicts
should fail this way, and it does.

### Scoring the spec's section 14 predictions

| prediction | outcome |
|---|---|
| "The geometry will degrade, most at the large end." | **Confirmed, and sharper than predicted.** Not just degradation but, for 5 of 9 trees over 100 cm, a hard 120 cm measurement ceiling in `qsm.measure_dbh` that makes the true value unreachable regardless of scan quality (item 2). |
| "...not *whether* our DBH degrades on big stems, but whether it degrades **more than a published method does on the same clouds**." | **Confirmed as worse.** -41.68 cm mean bias here against the reference method's -6.29 cm on a comparable band. |
| "The volume figure will degrade more [than DBH]." | **Confirmed**, though the ordering itself already held for Demol. 33.28% volume MAPE against 12.96% DBH MAPE here (all measurable trees), and far worse in absolute terms than Demol's 11.52%/3.07%. |
| "The equation comparison is genuinely open... If [route B does well where route A does not], the finding is that the measurement is the weak link, not the allometry." | **Partly wrong.** Route B is not simply fine: Chave's own median APE against harvested mass, tape-fed, is 14.00%, and T-VER's is 20.85% — both carry real error before measurement enters at all. On the median tree the equation is the *larger* share of route A's total error (item 4), the opposite emphasis from the prediction's framing — though measurement dominates completely, in either direction, for a right-skewed subset of individual trees. |

### What this still does not validate

Unchanged from the spec's section 15: stages 1-4 (isolated trees, no real
plot end to end), stage 5 (these clouds arrive already leaf-stripped by the
original authors, so no wood/leaf accuracy claim is made here), stage 7
(still a stub), and Thailand (Cameroon is tropical, semi-deciduous forest and
not Thai; T-VER is scored on African trees because that is the closest check
available without field access, not because it has been validated on a Thai
tree). Carbon credits are unaffected: nothing here makes any output a
tradable or certified credit.

## Can the pipeline tell a buttressed stem on its own?

Spec section 8. The archive has no per-tree buttress flag (see "What the
archive does not answer" above), so `model_quality` — what `qsm.QsmResult`
and this evaluation's `result.json` call the value section 8 and Task 6 of
the implementation plan call `ransac_inlier_ratio` (both names refer to
`QsmResult.model_quality`, documented in `qsm.py` as "0-1 fit quality
(RANSAC inlier ratio for DBH)") — is the only signal computed from the cloud
that could either partition this cohort at evaluation time or warn a real
user, who has neither a tape nor a database. Task 5's per-band means (0.913
/ 0.496 / 0.334, under 50 / 50-100 / 100-and-over) suggested the signal
exists; this task checks whether it separates the trees where our DBH and
`DBH_dest` actually diverge, which is a stricter and different question than
whether it correlates with size — fit quality falling with size could simply
mean big trunks are harder to fit.

Analysis done entirely from the committed `result.json`. Neither
`derive_cameroon_evidence.py` nor `result.json` was touched by this task —
confirmed by `git status` showing only `pipeline/cameroon_eval.py` and
`tests/test_cameroon_eval.py` changed, and by `sync_truth.py --check`
continuing to pass unmodified.

### The measured relationship

One statistic was computed: Spearman rank correlation between
`model_quality` and `abs(dbh_error_cm)`, across the 60 measurable trees.

| population | n | Spearman rho (model_quality vs abs(dbh_error_cm)) | p |
|---|---:|---:|---:|
| all measurable trees | 60 | -0.72 | 6e-11 |
| excluding the 5 over-ceiling trees (2, 6, 12, 64, 100) | 55 | -0.68 | 8e-9 |
| under 50 cm only (buttressing not a confound) | 31 | -0.48 | 0.006 |
| 50 cm and over only | 29 | -0.48 | 0.009 |

The five trees whose taped DBH exceeds the 120 cm RANSAC search ceiling
(`qsm._ransac_circle_fit`'s `max_radius_m=0.6`, see item 2 above) are not
carrying the whole effect: removing them drops rho from -0.72 to -0.68, not
to zero. The signal also survives inside the confound-free under-50 cm band
alone (rho=-0.48, p=0.006), which says something the size-band means alone
could not — even where buttressing cannot be the explanation, because the
archive's own reference TLS agrees with the tape to +0.30 cm down there, a
low inlier ratio still tracks a larger DBH error. So `model_quality` is not
a *pure* buttress detector; it is a general "how much to trust this circle"
signal that happens to concentrate on large stems in this cohort, because
large stems are where the fit struggles most. That is a narrower and more
honest claim than "it detects buttressing", and it is the one this data
supports.

Two trees make the imperfection concrete rather than abstract. Tree 99
(108.5 cm gt, `model_quality` 0.346) has `dbh_error_cm` +0.02 — a
low-confidence fit that happened to land almost exactly right. Tree 95
(20.4 cm gt, `model_quality` 1.000, comfortably inside the unconfounded
band) has `dbh_error_cm` -8.92 cm, 44% relative — a perfect-looking fit that
was not particularly accurate. Neither tree breaks the aggregate
relationship, and both are reasons this is reported as a correlation with
known exceptions, not as a rule that always holds tree by tree.

### `DBH_FIT_BUTTRESS_SUSPECT` is added

The correlation holds with and without the over-ceiling five, and holds
(more weakly, but significantly) inside the unconfounded band alone: the
inlier ratio separates the divergent trees. `pipeline/cameroon_eval.py`
gains `dbh_fit_buttress_suspect_reason(measured_dbh_cm, model_quality)`,
returning the reason code `DBH_FIT_BUTTRESS_SUSPECT` when both:

- `measured_dbh_cm >= UNCONFOUNDED_MAX_DBH_CM` (50 cm — this module's
  existing boundary for "buttressing is not a confound below here", reused
  rather than duplicated with a second 50 cm constant)
- `model_quality < DBH_FIT_BUTTRESS_SUSPECT_MAX_INLIER_RATIO` (0.60)

The size gate reads `measured_dbh_cm`, not `gt_dbh_cm`: a live pipeline run
has no ground truth to gate on, and this whole reason code exists because a
real user does not either.

`DBH_FIT_BUTTRESS_SUSPECT_MAX_INLIER_RATIO = 0.60` was chosen from the
threshold sweep below, not guessed in advance. "false alarm" means flagged
despite `gt_dbh_cm < 50` — inside the band where the archive's own
reference TLS agrees with the tape to +0.30 cm, so there is close to
nothing there for the flag to be right about being suspicious of:

| threshold | n flagged (of 60) | false alarms | notable miss |
|---:|---:|---:|---|
| 0.30 | 10 | 0 | tree 12 (-77.59 cm) |
| 0.40 | 14 | 0 | tree 12 (-77.59 cm) |
| 0.50 | 19 | 0 | tree 12 (-77.59 cm) |
| **0.60** | **23** | **0** | tree 63 (-9.71 cm) |
| 0.70 | 26 | 0 | adds trees 31, 74: errors under 0.6 cm |

0.60 is where tree 12 — 180.3 cm gt, -77.59 cm error, the single largest
error in the confounded population after the four other over-ceiling trees
— stops being missed, at zero cost in false alarms. The next threshold up,
0.70, only adds two trees whose actual error is under a centimetre: more
noise than signal. Without the size gate, 0.60 alone would also flag two
under-50 cm trees (tree 3, -1.46 cm; tree 32, -2.38 cm); the reused
`UNCONFOUNDED_MAX_DBH_CM` gate removes both at no cost elsewhere in the
sweep.

At this threshold, 23 of 60 measurable trees are flagged. All 9 trees in
the `100_and_over` band are flagged (including all 5 over-ceiling trees),
and 14 of the 20 trees in the `50_to_100` band. Mean `abs(dbh_error_cm)` is
26.30 cm for the flagged trees against 1.90 cm for the rest — about a 14x
separation.

What it still misses, stated rather than buried: tree 63 (90.5 cm gt,
-9.71 cm error, `model_quality` 0.603) sits just above the line and is not
flagged. That error is smaller than the 50-100 cm band's own MAE (11.55 cm,
`result.json`'s `metrics.dbh_bias_by_size_band`), so tree 63 is not an
outlier the flag conspicuously failed on — it is a middling error in a band
where middling errors are the norm, sitting just past a threshold that had
to be drawn somewhere.

### `DBH_ABOVE_CALIBRATED_RANGE` is added unconditionally

No correlation was needed for this one — only the range
`qsm.TOTAL_TREE_FORM_FACTOR` and `qsm.STEM_FORM_FACTOR` were fitted over,
which is a fact about the 65-tree Demol calibration cohort
(`docs/evidence/demol_65/result.json`), not a statistic measured on this
one. The largest `gt_dbh_cm` in that cohort is 46.63239833 cm
(`FORM_FACTOR_CALIBRATION_MAX_DBH_CM`); `dbh_above_calibrated_range_reason`
returns `DBH_ABOVE_CALIBRATED_RANGE` whenever `measured_dbh_cm` exceeds it.

31 of the 60 measurable Cameroon trees do — a majority of this cohort,
including 2 of the 31 trees under the 50 cm buttress boundary (trees 3 and
15, whose measured DBH lands at 47.04 cm and 47.36 cm despite a
`gt_dbh_cm` under 50 of 48.5 cm and 44.3 cm respectively). Every tree in the
`50_to_100` and `100_and_over` bands exceeds it. Item 2 above already found
that the largest `measured_dbh_cm` this pipeline ever reports is 117.91 cm,
for a tree taped at 180.3 cm, with nothing in the output distinguishing
that number from a trustworthy one — this reason code is that distinction.
It is a diagnostic predicate here, not an enforced refusal:
`cameroon_eval.py` calls `qsm.compute_qsm` directly, so nothing in this
evaluation stops a volume from being computed and reported for a tree past
this range. Wiring an actual refusal into the live pipeline (`main.py`,
alongside `QSM_LOW_FIT_QUALITY`) would be a separate change, outside this
task's scope.

### The discipline

One statistic was tried — Spearman rank correlation of `model_quality`
against `abs(dbh_error_cm)` — and it separated the divergent trees, so no
second statistic was ever tried looking for a better correlation. The
threshold (0.60) was chosen by sweeping candidate values of that one
statistic against the false-alarm count and the largest miss, the same
style `qsm.py`'s own `MIN_DBH_FIT_QUALITY` comment uses to justify its 0.80,
not by searching for a differently-computed quantity until one worked.
