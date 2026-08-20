# Cameroon destructive ground truth, 61 trees

Extracted from `database.xls` sheet `datafinal_test2` in the Dryad archive by
`scripts/extract_cameroon_ground_truth.py`. Re-verify with `--check`.

**Source:** Momo Takoudjou, S. et al. (2018), Dryad,
<https://doi.org/10.5061/dryad.10hq7> — **CC0 1.0**, which is why this table can
be committed. The point clouds are not: they are 1.29 GB and stay under
`data/raw/`, excluded by `.gitignore`.

`docs/ml/CAMEROON_EVIDENCE_CHAIN.md` records what the archive contains and how
these columns were established, including the arithmetic showing `agb_dest_kg`
is oven-dry mass including the stump.

## Columns

| column | source column | unit | note |
|---|---|---|---|
| `tree_id` | `ID` | — | 61 of the archive's 62 clouds; `ID_56` has no destructive row |
| `genus`, `species` | `Genus`, `Species` | — | 15 species |
| `dbh_dest_cm` | `DBH_dest` | cm | **at 1.30 m, or above buttresses if present** — the archive does not say which trees |
| `height_dest_m` | `H_tot_dest` | m | felled height |
| `agb_dest_kg` | `Destructive AGB` | kg | archive gives Mg; oven-dry, stump-inclusive |
| `wsg_ind_kg_m3` | `WSG_ind` | kg/m³ | archive gives g/cm³ |
| `volume_total_dest_m3` | `Destructive total volume` | m³ | includes the stump |
| `volume_stem_dest_m3` | `Destructive stem volume` | m³ | stem only |
| `dbh_tls_cm` | `DBH_L` | cm | the authors' own TLS-derived diameter |
| `height_tls_m` | `Hauteur_L` | m | the authors' own TLS-derived height |
| `volume_total_reference_qsm_m3` | `TLS edited total volume_5` | m³ | the authors' hand-corrected QSM, branches under 5 cm excluded |

The last three are not ground truth. They are a published reference
implementation on the same point clouds, and exist here so this pipeline can be
scored against a competent method rather than only against the tape.

`volume_total_reference_qsm_m3` comes from the `_5` family of columns, which
exclude branches thinner than 5 cm. It is therefore **not** directly comparable
to `volume_total_dest_m3`; it is comparable to what a QSM can see. Any figure
derived from it has to say so.
