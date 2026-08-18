# Reference sources

Primary sources this pipeline's constants are read out of, kept in the
repository so a number can be checked without a network round trip and without
trusting a summary of a summary.

## `USDA_GTR_SO-88_tropical_wood_densities.pdf`

Reyes, G.; Brown, S.; Chapman, J.; Lugo, A.E. 1992. *Wood densities of tropical
tree species.* General Technical Report SO-88. New Orleans, LA: U.S. Department
of Agriculture, Forest Service, Southern Forest Experiment Station. 15 p.

Downloaded 2026-08-14 from <https://www.srs.fs.usda.gov/pubs/gtr/gtr_so088.pdf>.
A work of the United States Government: **public domain**, no licence needed to
redistribute.

Why it is here: it is the source for every wood density in
`../species_db.csv`, and it states its basis explicitly — "wood density is
reported in ovendry weight grams per cubic centimeter of green volume" — which
is the basic specific gravity Chave 2014 takes and the thing this project had
previously got wrong. It also carries the air-dry-to-basic regression
implemented as `allometric.basic_density_from_air_dry`.

Table 2 lists 1,180 species across tropical Asia (428), America (470) and
Africa (282); the Asia section is the one used here. See
`../../../../docs/ml/WOOD_DENSITY_PROVENANCE.md`.

## What is deliberately not here

The Global Wood Density Database (Zanne et al. 2009, Dryad
doi:10.5061/dryad.234) would be the other primary source. It is served behind a
proof-of-work bot check that this environment does not pass, and the Zenodo
mirror returns 403. It remains the shortest route to citable densities for
*Afzelia xylocarpa* and *Bambusa spp.*, the two rows still uncited.

## `TGO_T-VER-S-TOOL-01-01_v2_tree_carbon.*` — not committed

Thailand Greenhouse Gas Management Organization (TGO), *T-VER-S-TOOL-01-01
การคำนวณการกักเก็บคาร์บอนของต้นไม้*, Version 02, effective 26 March 2025.

    https://tver.tgo.or.th/database/public/tools/1

This is the official Thai methodology for tree carbon accounting, and the
document `CLAUDE.md` means when it says to verify values against the TGO
forestry guideline before submission — note it is on version 2 of 2025, not the
2017 edition that note assumes. It is the source for the allometric findings in
`docs/ml/ALLOMETRIC_COEFFICIENTS.md`.

**The files are deliberately left out of git.** Unlike the USDA report above,
which is a US Government work and public domain by statute, TGO publishes this
for programme participants without stating redistribution terms. Recording the
equations and the citation is reporting facts; mirroring a 3 MB government
document without a licence is not, and this repository has spent too long
getting provenance right to be careless about it here.

Fetch it from the page above when needed — the Word version is the one to use,
because the PDF's fonts carry no ToUnicode map and every Thai character is lost
on extraction.
