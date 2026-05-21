-- =============================================================================
-- CarbonScan AI — Seed Species Database
-- =============================================================================
-- Insert the 5 pilot tree species with verified allometric coefficients.
-- Run AFTER `alembic upgrade head` succeeds.
--
-- Source of truth: services/ml/data/species_db.csv
-- Tested in: services/ml/tests/test_allometric.py (16/16 passing)
-- =============================================================================

INSERT INTO species_db (
    name_sci, name_th, name_en, wood_density,
    agb_a, agb_b, agb_c, agb_source,
    root_to_shoot_ratio, carbon_fraction
) VALUES
    (
        'Tectona grandis',
        'สัก',
        'Teak',
        660,
        0.0509, 2.150, 0.700,
        'Tsutsumi et al. 1983 (Thai monsoon forest)',
        0.24, 0.47
    ),
    (
        'Dipterocarpus alatus',
        'ยางนา',
        'Yang Na (Gurjun)',
        720,
        0.0396, 2.380, 0.800,
        'Ogawa et al. 1965 (Thai monsoon forest)',
        0.24, 0.47
    ),
    (
        'Bambusa spp.',
        'ไผ่ (ไผ่ทั่วไป)',
        'Bamboo',
        650,
        0.131, 2.280, 0.590,
        'Yiping et al. 2010 (Bamboo allometry, INBAR)',
        0.20, 0.47
    ),
    (
        'Hevea brasiliensis',
        'ยางพารา',
        'Para Rubber',
        580,
        0.0464, 2.330, 0.720,
        'Chiarucci et al. 2014 (Rubber plantation)',
        0.24, 0.47
    ),
    (
        'Afzelia xylocarpa',
        'มะค่าโมง',
        'Makha',
        850,
        0.0612, 2.420, 0.660,
        'Generic Thai dense hardwood (Chave 2014 adjusted)',
        0.24, 0.47
    )
ON CONFLICT (name_sci) DO UPDATE SET
    name_th = EXCLUDED.name_th,
    name_en = EXCLUDED.name_en,
    wood_density = EXCLUDED.wood_density,
    agb_a = EXCLUDED.agb_a,
    agb_b = EXCLUDED.agb_b,
    agb_c = EXCLUDED.agb_c,
    agb_source = EXCLUDED.agb_source,
    root_to_shoot_ratio = EXCLUDED.root_to_shoot_ratio,
    carbon_fraction = EXCLUDED.carbon_fraction;

-- Verify
SELECT name_sci, name_th, wood_density, agb_a, agb_b, agb_c
FROM species_db
ORDER BY wood_density DESC;
