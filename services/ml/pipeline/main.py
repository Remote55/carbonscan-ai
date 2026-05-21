"""Pipeline orchestrator — chain all 8 steps end-to-end.

CLI usage:
    python -m pipeline.main process --input plot.las --output results.json

Programmatic:
    from pipeline.main import process_point_cloud
    result = process_point_cloud("plot.las")
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import click


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


def process_point_cloud(
    input_path: str | Path,
    output_path: str | Path | None = None,
    progress_callback: Any = None,
) -> PipelineResult:
    """Run the full 8-step ML pipeline on a point cloud.

    Args:
        input_path: Path to .las / .laz / .ply file
        output_path: Optional path to save JSON result
        progress_callback: Optional callable(stage: str, progress: int) -> None

    Returns:
        PipelineResult with metadata, summary, and per-tree results.

    Raises:
        FileNotFoundError: if input doesn't exist
        ValueError: if file format unsupported

    TODO Phase 1-2:
        - Wire up all 8 steps
        - Add proper logging via structlog
        - Add error recovery (fail one tree → continue others)
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    def _progress(stage: str, pct: int) -> None:
        if progress_callback:
            progress_callback(stage, pct)

    # Stub implementation — Phase 1 will implement real logic
    _progress("loading", 0)
    # TODO: cloud = read_las(input_path)

    _progress("ground_classification", 10)
    # TODO: cloud = ground_classification.run(cloud)

    _progress("height_normalization", 25)
    # TODO: cloud = height_normalization.run(cloud)

    _progress("canopy_height_model", 35)
    # TODO: chm = canopy_height_model.compute(cloud)

    _progress("tree_segmentation", 45)
    # TODO: trees = tree_segmentation.detect(cloud, chm)

    _progress("wood_leaf_separation", 60)
    # TODO: trees = [wood_leaf_separation.predict(t) for t in trees]

    _progress("qsm", 80)
    # TODO: for t in trees: t.volume = qsm.compute(t.wood_points)

    _progress("allometric", 95)
    # TODO: for t in trees: t.carbon = allometric.calculate(...)

    _progress("complete", 100)

    result = PipelineResult(
        metadata={
            "input_file": str(input_path),
            "pipeline_version": "0.1.0",
            "status": "stub — not yet implemented",
        },
        summary={"total_trees": 0, "total_carbon_kg": 0},
        trees=[],
    )

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
def process(input_path: str, output_path: str) -> None:
    """Process a point cloud file."""

    def _print_progress(stage: str, pct: int) -> None:
        click.echo(f"[{pct:3d}%] {stage}")

    result = process_point_cloud(
        input_path,
        output_path=output_path,
        progress_callback=_print_progress,
    )
    click.echo(f"\n✓ {result.summary.get('total_trees', 0)} trees processed")
    click.echo(f"✓ Output written to: {output_path}")


if __name__ == "__main__":
    cli()
