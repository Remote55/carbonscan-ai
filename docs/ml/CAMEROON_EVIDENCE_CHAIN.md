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
been applied.

```
14.735	3.469	-1.637
14.724	3.466	-1.728
14.749	3.410	-1.673
```

Mapping to the ground truth is by the integer in the directory name against
`ID`. IDs are not contiguous: 1–8, 11, 12, 15, 18, 28, 29, 31, 32, 52, 54–57,
59–76, 79, 80, 83, 85, 87–89, 91–106.

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
