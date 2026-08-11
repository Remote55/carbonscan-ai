# Wood density: what it does, and what nobody has checked

## Why this is the number that matters

Chave 2014 is the model every tree is costed with:

    AGB = 0.0673 × (ρ · D² · H)^0.976

The exponent is 0.976, so **ρ passes into the carbon figure almost
undiminished**. It is also the one parameter the pipeline never measures — it is
looked up from `services/ml/data/species_db.csv`.

The size of the lever, measured on one tree at DBH 30 cm and H 20 m:

| species | ρ (kg/m³) | CO₂e (kg) | vs the 600 default |
|---|---:|---:|---:|
| *(no species named)* | 600 | 1242.9 | — |
| Hevea brasiliensis | 580 | 1202.4 | −3.3% |
| Bambusa spp. | 650 | 1300.5 | +4.6% |
| Tectona grandis | 660 | 1364.0 | +9.7% |
| Dipterocarpus alatus | 720 | 1484.9 | +19.5% |
| Afzelia xylocarpa | 850 | 1746.1 | **+40.5%** |

Naming a species moves the answer by up to 45% across the table. That is the
largest single effect the product has on its own headline number.

## The problem

Until 2026-08-11 that number had **no source column and no verified flag**,
while the allometric coefficients in the same row had `agb_source` and
`coefficients_verified` — and were gated on them, so no species equation is ever
used. The product was refusing the cited quantity and trusting the uncited one.

It is probably also the wrong *kind* of number.

Chave takes ρ as **basic specific gravity**: oven-dry mass over green volume.
Timber tables overwhelmingly publish **air-dry density at 12% moisture content**,
which is the larger figure. They are not interchangeable, and using air-dry
overstates biomass roughly in proportion.

For the one species anything could be established:

- World Agroforestry's *Tectona grandis* profile: "Density of the wood is
  (min. 480) **610-750** (max. 850) kg/m³ **at 12% mc**"
- Global Wood Density Database (Zanne et al.): teak **0.60 g/cm³** basic = 600
- `species_db.csv` carries **660** — the middle of the air-dry range, 10% above
  the basic value

The reported uncertainty makes this worse rather than better. The ±10% band for
a named species comes from *within-species* variation, so it is centred on the
table value and says nothing about whether that value is the right quantity. For
teak the band is 594–726 and the reference basic density, 600, sits on its
bottom edge.

The other four rows have no source at all, so their basis is unknown rather than
merely unconfirmed.

## What was done

Nothing to the numbers. `species_db.csv` gained `density_basis`,
`density_source` and `density_verified`; `SpeciesParams` carries them; and
`uncertainty_basis` — which travels into the API response — now says that an
unverified density may be an air-dry figure. `GET /api/v1/upload/species`
returns `density_verified` beside `coefficients_verified`.

Replacing five densities on the strength of evidence for one species would be a
different guess, not a correction.

## What is left, and what blocked it

Read **basic** densities for all five species out of the Global Wood Density
Database and record each one with its citation, then flip `density_verified`.

That was attempted on 2026-08-11 and could not be completed from this
environment:

| source | outcome |
|---|---|
| `db.worldagroforestry.org/wd/inquire` (ICRAF wood density DB) | connection failed |
| `zenodo.org/api/records/13322441` (GWDD) | HTTP 403 |
| `fs.usda.gov` i-Tree Appendix 11 wood density table | HTTP 403 |
| `apps.worldagroforestry.org` species profiles | reachable, but gives air-dry at 12% mc, not basic |

Per-species web searches did not converge on citable basic densities for the
four species other than teak.

Anyone picking this up needs either the GWDD dataset itself or library access to
the primary literature. The R package `BIOMASS` bundles the GWDD as `wdData`,
which is the shortest route if R is available.

Two things to keep in mind while doing it:

1. **Check the basis of every value taken.** The mistake this document exists
   for is exactly the one that is easy to repeat.
2. **Bamboo is not a tree.** `Bambusa spp.` is a grass with a hollow culm; both
   a "wood density" and a pantropical tree allometric are shaky for it, and the
   row deserves its own note rather than the same treatment as the other four.
