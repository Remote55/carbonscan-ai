"""Pipeline orchestrator — chain the pipeline steps end-to-end.

CLI usage:
    python -m pipeline.main process --input plot.las --output results.json
    python -m pipeline.main process --input plot.las --backend pointnet --model woodleaf_pn2.pt

Programmatic:
    from pipeline.main import process_point_cloud, process_points
    result = process_point_cloud("plot.las")
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import click
import numpy as np


@dataclass
class TreeResult:
    """Per-tree analysis result."""

    tree_id: int
    species_sci: str | None = None
    species_confidence: float | None = None
    dbh_cm: float = 0.0
    height_m: float = 0.0
    crown_radius_m: float | None = None
    volume_m3: float | None = None
    biomass_kg: float | None = None
    carbon_kg: float | None = None
    co2eq_kg: float | None = None
    location: dict[str, float] = field(default_factory=dict)
    point_count: int = 0
    wood_leaf_iou: float | None = None


@dataclass
class PipelineResult:
    """End-to-end pipeline output."""

    metadata: dict[str, Any]
    summary: dict[str, Any]
    trees: list[TreeResult]


def process_points(
    points: np.ndarray,
    *,
    wood_leaf_backend: str = "tlsep",
    model_path: str | None = None,
    default_species: str | None = None,
    progress_callback: Any = None,
) -> PipelineResult:
    """Run the pipeline on an in-memory (N, 3) point cloud.

    Steps: ground classification -> height normalization -> CHM -> tree
    detection -> (per tree) wood/leaf -> QSM -> allometric carbon.
    (Species classification is Phase 2; `default_species` selects the
    allometric equation, else the Chave pantropical fallback is used.)

    Args:
        points: (N, 3) raw XYZ
        wood_leaf_backend: "tlsep" (PCA, default) or "pointnet" (needs model_path)
        model_path: PointNet++ checkpoint when backend="pointnet"
        default_species: scientific name for the allometric equation
        progress_callback: optional callable(stage: str, pct: int)
    """
    from pipeline import (
        allometric,
        canopy_height_model,
        ground_classification,
        height_normalization,
        qsm,
        tree_segmentation,
        wood_leaf_separation,
    )

    def _p(stage: str, pct: int) -> None:
        if progress_callback:
            progress_callback(stage, pct)

    _p("ground_classification", 10)
    ground_mask = ground_classification.classify_ground_array(points)

    _p("height_normalization", 25)
    norm = height_normalization.normalize_height_array(points, ground_mask)

    _p("canopy_height_model", 35)
    chm, transform = canopy_height_model.compute_chm_array(norm, resolution=0.5, min_height=0.5)

    _p("tree_segmentation", 45)
    labels_2d = tree_segmentation.watershed_segmentation(chm, min_height=3.0, min_distance=5)
    # min_height=0.2 (not the 1.5 default) so the breast-height slice (1.3 m)
    # survives — otherwise QSM can't measure DBH and every tree is dropped.
    tree_ids = tree_segmentation.assign_points_to_trees(norm, labels_2d, transform, min_height=0.2)
    tree_clouds = tree_segmentation.extract_tree_points(norm, tree_ids)

    _p("wood_leaf_separation", 60)
    segmenter = wood_leaf_separation.WoodLeafSegmenter(
        model_path=model_path, backend=wood_leaf_backend
    )
    if wood_leaf_backend == "pointnet":
        segmenter.load()

    trees: list[TreeResult] = []
    for tid in sorted(tree_clouds):
        tree_pts = tree_clouds[tid]
        labels = segmenter.segment(tree_pts)
        wood = tree_pts[labels == wood_leaf_separation.WOOD]
        if len(wood) == 0:
            continue
        q = qsm.compute_qsm(wood, seed=tid)
        if q.dbh_cm <= 0 or q.height_m <= 0:
            continue
        carbon = allometric.calculate_carbon(
            dbh_cm=q.dbh_cm, height_m=q.height_m, species_sci=default_species
        )
        cx, cy = float(tree_pts[:, 0].mean()), float(tree_pts[:, 1].mean())
        trees.append(
            TreeResult(
                tree_id=int(tid),
                species_sci=default_species,
                dbh_cm=round(q.dbh_cm, 2),
                height_m=round(q.height_m, 2),
                volume_m3=round(q.total_volume_m3, 4),
                biomass_kg=round(carbon.biomass_kg, 2),
                carbon_kg=round(carbon.carbon_kg, 2),
                co2eq_kg=round(carbon.co2eq_kg, 2),
                location={"x": round(cx, 3), "y": round(cy, 3)},
                point_count=len(tree_pts),
            )
        )

    _p("complete", 100)

    total_carbon = sum(t.carbon_kg or 0.0 for t in trees)
    total_co2 = sum(t.co2eq_kg or 0.0 for t in trees)
    return PipelineResult(
        metadata={
            "pipeline_version": "0.2.0",
            "wood_leaf_backend": wood_leaf_backend,
            "n_input_points": len(points),
            "status": "ok",
        },
        summary={
            "total_trees": len(trees),
            "total_carbon_kg": round(total_carbon, 2),
            "total_co2eq_kg": round(total_co2, 2),
        },
        trees=trees,
    )


def process_point_cloud(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    wood_leaf_backend: str = "tlsep",
    model_path: str | None = None,
    default_species: str | None = None,
    max_points: int = 200_000,
    progress_callback: Any = None,
) -> PipelineResult:
    """Load a point-cloud file and run the full pipeline.

    Args:
        input_path: .las / .laz / .ply / .txt / .xyz / .csv
        output_path: optional JSON output path
        (other args forwarded to process_points)
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if progress_callback:
        progress_callback("loading", 0)

    from pipeline.field_eval import load_point_cloud

    points = load_point_cloud(input_path, max_points=max_points)
    result = process_points(
        points,
        wood_leaf_backend=wood_leaf_backend,
        model_path=model_path,
        default_species=default_species,
        progress_callback=progress_callback,
    )
    result.metadata["input_file"] = str(input_path)

    if output_path:
        Path(output_path).write_text(
            json.dumps(
                {
                    "metadata": result.metadata,
                    "summary": result.summary,
                    "trees": [asdict(t) for t in result.trees],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return result


# --- CLI ---
@click.group()
def cli() -> None:
    """CarbonScan AI ML Pipeline CLI."""


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True))
@click.option("--output", "output_path", type=click.Path(), default="results.json")
@click.option("--backend", type=click.Choice(["tlsep", "pointnet"]), default="tlsep")
@click.option("--model", "model_path", type=click.Path(), default=None,
              help="PointNet++ checkpoint (required for --backend pointnet)")
@click.option("--species", "default_species", default=None, help="scientific name for allometric")
def process(input_path: str, output_path: str, backend: str, model_path: str | None,
            default_species: str | None) -> None:
    """Process a point cloud file end-to-end."""

    def _print_progress(stage: str, pct: int) -> None:
        click.echo(f"[{pct:3d}%] {stage}")

    result = process_point_cloud(
        input_path,
        output_path=output_path,
        wood_leaf_backend=backend,
        model_path=model_path,
        default_species=default_species,
        progress_callback=_print_progress,
    )
    click.echo(f"\nOK - {result.summary['total_trees']} trees, "
               f"{result.summary['total_carbon_kg']} kg C, "
               f"{result.summary['total_co2eq_kg']} kg CO2eq")
    click.echo(f"OK - output written to: {output_path}")


if __name__ == "__main__":
    cli()
