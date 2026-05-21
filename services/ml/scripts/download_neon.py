"""Download NEON LiDAR sample data for training.

Usage:
    python -m scripts.download_neon --site OSBS --year 2022 --output data/raw/neon/

NEON Data Product:
    DP1.30003.001 — Discrete return LiDAR point cloud

Get API token: https://data.neonscience.org/myaccount

TODO Phase 1: Implement using NEON API v0 endpoints.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def download_neon_plot(site: str, year: int, output_dir: Path, token: str | None = None) -> Path:
    """Download a single NEON site/year of LiDAR data.

    Args:
        site: NEON site code (e.g., 'OSBS', 'BART', 'TALL')
        year: Year of data
        output_dir: Where to save downloaded .las files
        token: NEON API token (optional, public data available without)

    Returns:
        Path to downloaded directory
    """
    raise NotImplementedError("Implement in Phase 1 — use NEON API v0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="OSBS", help="NEON site code")
    parser.add_argument("--year", type=int, default=2022)
    parser.add_argument("--output", type=Path, default=Path("data/raw/neon"))
    args = parser.parse_args()

    download_neon_plot(args.site, args.year, args.output)
