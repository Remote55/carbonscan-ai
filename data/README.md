# 📊 Data Directory

> Datasets, samples, and ground-truth data
>
> **⚠️ Large files gitignored** — see `.gitignore`

---

## Structure

```
data/
├── README.md              (this file)
├── samples/               Sample point cloud files (small, for testing)
│   ├── sample_plot_1.las  (~5 MB, public domain)
│   └── README.md          What each sample is
├── raw/                   Downloaded datasets (gitignored)
│   ├── neon/              NEON LiDAR data
│   └── pl@ntnet/          Plant images
├── processed/             Preprocessed for training (gitignored)
│   ├── neon/
│   └── annotations/
└── ground-truth/          Calibration data (own measurements)
    ├── calibration_2026/  Plot calibration trees
    └── README.md
```

---

## How to Download

### NEON LiDAR (for training)
```bash
# Get API token from https://data.neonscience.org/myaccount
export NEON_TOKEN="your_token"

python services/ml/scripts/download_neon.py \
    --site OSBS \
    --year 2022 \
    --output data/raw/neon/OSBS_2022/
```

### Sample Files (committed for tests)
อยู่ใน `data/samples/` — ดาวน์โหลดจาก:
- lidR sample: https://github.com/r-lidar/lidR/wiki

---

## Naming Conventions

```
{source}_{site}_{year}_{type}.{ext}

Examples:
- neon_OSBS_2022_pointcloud.las
- own_chiangmai_2026_calibration.las
- inat_tectona_2024.zip
```

---

## Size Estimates

| Dataset | Size |
|---|---|
| 1 NEON plot | 500MB - 2GB |
| 5-10 NEON plots (train) | ~10GB |
| Pl@ntNet images (5 species, 1000 ea) | ~5GB |
| Calibration ground truth (~20 trees) | < 100MB |

---

## ⚠️ Data Quality

- [ ] No duplicates
- [ ] Consistent SRID (use EPSG:4326 for GPS, EPSG:32647 for Thailand UTM)
- [ ] Document source + license
- [ ] Backup raw → don't modify in place
