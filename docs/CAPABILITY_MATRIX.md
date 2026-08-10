# TreeQ Carbon Platform — Capability Matrix

> Generated from `docs/evidence/core_demo_manifest.json`; do not edit by hand.

Baseline: `tlsep` (`Implemented`).
Candidate: PointNet++ (`Experimental`, not promoted).

| Capability | Status | Actual implementation | Evidence | Allowed claim |
|---|---|---|---|---|
| 1. Ground segmentation | Implemented | Grid ground heuristic: the k-th lowest point per cell, k capped at 3 | services/ml/pipeline/ground_classification.py | Operational heuristic; not Cloth Simulation Filter (CSF). |
| 2. Height normalization | Implemented | K-nearest-neighbor inverse-distance interpolation of ground height | services/ml/pipeline/height_normalization.py | Implemented as KNN-IDW terrain normalization. |
| 3. Canopy height model | Implemented | Grid maximum Z with morphological filling/smoothing | services/ml/pipeline/canopy_height_model.py | Operational CHM; not the full multi-threshold pit-free algorithm. |
| 4. Individual-tree segmentation | Implemented | Local-maxima markers plus watershed segmentation | services/ml/pipeline/tree_segmentation.py | Implemented watershed tree segmentation. |
| 5a. Wood/leaf baseline | Implemented | tlsep/PCA geometric classifier selected as the stable default | services/ml/pipeline/wood_leaf_separation.py; services/ml/pipeline/main.py | Reproducible baseline/fallback; no real-data accuracy claim is assigned to tlsep here. |
| 5b. PointNet++ wood/leaf candidate | Experimental | PointNet++ backend exists but is not the promoted default | docs/evidence/pointnet_independent_eval/result.json; SHA-256 58921ee2bc38af67d6d5a9c080840e83ca59439cb4ac151cf26c59e059534096 | Reviewed independent verdict FAIL_METRICS; candidate external macro Wood IoU 0.23728726507501768; remains Experimental and not default-promoted. |
| 6. QSM-derived geometry | Implemented | RANSAC circle DBH with a least-squares refit on the consensus set, maximum-Z height, and two taper equations calibrated to harvested stem and whole-tree volume; the crown is their difference, not a measured branch model | services/ml/pipeline/qsm.py | Operational geometry estimate with known volume limitations; not full TreeQSM branch-axis modelling. |
| 7. Species classification | Stub | Interface placeholder; pipeline uses a caller-supplied default species or no species | services/ml/pipeline/species_classifier.py; services/ml/pipeline/main.py | No trained ResNet species classifier is integrated. |
| 8. Allometric carbon calculation | Implemented | Chave 2014 pantropical, at the named species' wood density when one is given; the species-specific equations in species_db.csv are gated off until their coefficients are checked against the cited papers | services/ml/pipeline/allometric.py; services/ml/data/species_db.csv | Produces biomass, carbon stock, and CO2e estimates; coefficient verification against TGO 2017 remains required. |
| Deterministic core demo | Implemented | Seeded synthetic fixture is executed twice and normalized JSON/PLY hashes must match | services/ml/scripts/run_core_demo.py; docs/evidence/core_demo_manifest.json | Reproducibility evidence for one core path, not an accuracy benchmark. |
| Web 3D result viewer | Implemented | Next.js dashboard viewer renders segmented PLY results and tree summaries | apps/web/src/components/viewer/point-cloud-viewer.tsx; apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx | Implemented web visualization; generated evidence labels must accompany demo claims. |
| Mobile capture flow | Experimental | Flutter capture and result screens exist, but Supabase initialization and the reviewed end-to-end path are incomplete | apps/mobile/lib/main.dart; apps/mobile/lib/features/tree_scan/presentation/tree_scan_screen.dart | Prototype UI only; not a verified production scan-to-carbon flow. |
| Production API/worker deployment | Planned | Current verified demo uses a local backend exposed through a temporary tunnel | AGENTS.md; docs/PROJECT_SPEC.md | Not continuously deployed as a production ML service. |
| Carbon marketplace and payments | Planned | Product concept only; no complete transaction/payment path | docs/PROJECT_SPEC.md | Roadmap item, not an implemented B2B marketplace. |
| Certified carbon credits | Planned | No MRV registry verification, project certification, issuance, or retirement workflow | docs/PROJECT_SPEC.md | Carbon stock and CO2e estimates must not be described as certified or tradable credits. |
