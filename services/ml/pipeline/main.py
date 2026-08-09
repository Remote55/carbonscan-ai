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
from typing import Any, Literal

import click
import numpy as np

from pipeline.provenance import (
    ALGORITHM_MAP,
    checkpoint_identity,
    git_worktree_dirty,
    hash_points,
    resolve_git_commit,
)

PIPELINE_VERSION = "0.4.0"

# Class code for "ground, or not claimed by any tree" in the segmented PLY the
# viewer reads. Wood (0) and leaf (1) come from wood_leaf_separation; this third
# code exists only in the exported plot-wide cloud, which is why it lives here
# and not beside them.
GROUND_CLASS = 2


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
    #: Bounds from the plausible wood density range, which this pipeline never
    #: measures. Density only — allometric.CARBON_VALIDATION_NOTE says what is
    #: outside them, and uncertainty_basis carries it per tree.
    co2eq_low_kg: float | None = None
    co2eq_high_kg: float | None = None
    uncertainty_basis: str | None = None
    location: dict[str, float] = field(default_factory=dict)
    point_count: int = 0
    wood_leaf_iou: float | None = None


@dataclass(frozen=True)
class ExcludedSegment:
    """A detected tree segment that produced no measurement, and why.

    Segments used to be dropped silently, so a plot could report fewer trees
    than it detected with no way to tell which ones vanished or why.
    """

    tree_id: int
    stage: Literal["wood_leaf", "qsm"]
    reason_code: Literal["WOOD_EMPTY", "QSM_INVALID", "QSM_LOW_FIT_QUALITY"]


@dataclass
class PipelineDiagnostics:
    """Why the measured tree count differs from the detected tree count."""

    excluded_segments: list[ExcludedSegment] = field(default_factory=list)


@dataclass
class PipelineResult:
    """End-to-end pipeline output."""

    metadata: dict[str, Any]
    summary: dict[str, Any]
    trees: list[TreeResult]
    diagnostics: PipelineDiagnostics = field(default_factory=PipelineDiagnostics)


def pipeline_result_to_dict(result: PipelineResult) -> dict[str, Any]:
    """Serialize a result to the one JSON shape every runner and the API share.

    Keeping this in one place stops the CLI, the core demo and the judge demo
    from drifting apart, which is what let `diagnostics` be reported by some
    paths and not others.
    """
    return {
        "metadata": result.metadata,
        "summary": result.summary,
        "diagnostics": {
            "excluded_segments": [
                asdict(item) for item in result.diagnostics.excluded_segments
            ]
        },
        "trees": [asdict(tree) for tree in result.trees],
    }


def process_points(
    points: np.ndarray,
    *,
    wood_leaf_backend: str = "tlsep",
    model_path: str | None = None,
    default_species: str | None = None,
    segmented_ply_out: str | None = None,
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
        segmented_ply_out: optional path to write a per-point segmented PLY
            (whole plot: ground=2, non-ground split wood=0/leaf=1) for the viewer
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

    # Resolved before any work, not while building the result. These shell out
    # to git, and an image with no .git and no git binary therefore failed after
    # the whole analysis had run - minutes of compute discarded to report a
    # misconfiguration that was knowable at the first line. A run that cannot
    # say which code produced it should not start.
    repo_root = Path(__file__).resolve().parents[3]
    git_commit = resolve_git_commit(repo_root)
    git_dirty = git_worktree_dirty(repo_root)

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
    diagnostics = PipelineDiagnostics()

    # The viewer's copy of the classification, assembled from the per-tree labels
    # below rather than recomputed. Ground and anything the tree assignment did
    # not claim stay GROUND: unseen is not a class to guess at.
    plot_classes = (
        np.full(len(points), GROUND_CLASS, dtype=np.uint8) if segmented_ply_out else None
    )

    for tid in sorted(tree_clouds):
        tree_pts = tree_clouds[tid]
        labels = segmenter.segment(tree_pts)
        if plot_classes is not None:
            # extract_tree_points groups with `points[tree_ids == tid]`, a
            # boolean mask, so this writes back in the order it read out.
            # Recorded before the exclusions below: a tree that cannot be
            # measured is still a tree that was seen, and the result table lists
            # it, so the picture has to show it too.
            plot_classes[tree_ids == tid] = np.asarray(labels, dtype=np.uint8)
        wood = tree_pts[labels == wood_leaf_separation.WOOD]
        if len(wood) == 0:
            # No stem points to measure. Record it; an unexpected fault must
            # still propagate rather than be recorded as an exclusion.
            diagnostics.excluded_segments.append(
                ExcludedSegment(tree_id=int(tid), stage="wood_leaf", reason_code="WOOD_EMPTY")
            )
            continue
        q = qsm.compute_qsm(wood, seed=tid)
        if q.dbh_cm <= 0 or q.height_m <= 0:
            diagnostics.excluded_segments.append(
                ExcludedSegment(tree_id=int(tid), stage="qsm", reason_code="QSM_INVALID")
            )
            continue
        if q.model_quality < qsm.MIN_DBH_FIT_QUALITY:
            # The circle fit failed on this stem and said so. Reporting the
            # radius anyway is how one tree contributes a 92 cm DBH error to a
            # cohort whose MAE is about 1 cm. Note the seed above is the tree id,
            # so which trees hit this is a property of the segmentation order,
            # not something a fixed seed protects anyone from.
            diagnostics.excluded_segments.append(
                ExcludedSegment(
                    tree_id=int(tid), stage="qsm", reason_code="QSM_LOW_FIT_QUALITY"
                )
            )
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
                co2eq_low_kg=round(carbon.co2eq_low_kg, 2),
                co2eq_high_kg=round(carbon.co2eq_high_kg, 2),
                uncertainty_basis=carbon.uncertainty_basis,
                location={"x": round(cx, 3), "y": round(cy, 3)},
                point_count=len(tree_pts),
            )
        )

    if segmented_ply_out and plot_classes is not None:
        # Write the labels the measurements were taken from. This used to run a
        # second segmenter pass over every non-ground point at once, which is a
        # different computation: tlsep reads a point's class from its 20 nearest
        # neighbours, and a point between two crowns gets different neighbours
        # when the whole plot is handed over instead of one tree. The file went
        # to the viewer as "the result", so the picture on screen could disagree
        # with the numbers beside it. It was also the slowest step in the run.
        from pipeline.ply_export import write_segmented_ply

        write_segmented_ply(points, plot_classes, segmented_ply_out)

    _p("complete", 100)

    total_carbon = sum(t.carbon_kg or 0.0 for t in trees)
    total_co2 = sum(t.co2eq_kg or 0.0 for t in trees)
    # Summing the per-tree bounds treats the density error as fully correlated
    # across the plot, which for one species on one site it very nearly is.
    # Adding them in quadrature would assume each tree's wood is an independent
    # draw and would report a tighter plot total than we can support.
    total_co2_low = sum(t.co2eq_low_kg or 0.0 for t in trees)
    total_co2_high = sum(t.co2eq_high_kg or 0.0 for t in trees)
    detected = len(tree_clouds)
    measured = len(trees)
    excluded = len(diagnostics.excluded_segments)
    if detected != measured + excluded:  # pragma: no cover - guards a coding error
        raise RuntimeError(
            f"tree counts do not reconcile: detected={detected} "
            f"measured={measured} excluded={excluded}"
        )
    algorithms = dict(ALGORITHM_MAP)
    algorithms["wood_leaf"] = wood_leaf_backend
    return PipelineResult(
        metadata={
            "pipeline_version": PIPELINE_VERSION,
            "git_commit": git_commit,
            "git_dirty": git_dirty,
            "wood_leaf_backend": wood_leaf_backend,
            "checkpoint_sha256": (
                checkpoint_identity(model_path) if wood_leaf_backend == "pointnet" else None
            ),
            "input_sha256": hash_points(points),
            "algorithms": algorithms,
            "evidence_status": "baseline" if wood_leaf_backend == "tlsep" else "experimental",
            "candidate_status": (
                "candidate_not_evaluated"
                if wood_leaf_backend == "tlsep"
                else "not_promoted"
            ),
            "n_input_points": len(points),
            "status": "ok",
        },
        summary={
            # total_trees stays the measured count for backward compatibility.
            "total_trees": measured,
            "detected_trees": detected,
            "measured_trees": measured,
            "excluded_trees": excluded,
            "total_carbon_kg": round(total_carbon, 2),
            "total_co2eq_kg": round(total_co2, 2),
            "total_co2eq_low_kg": round(total_co2_low, 2),
            "total_co2eq_high_kg": round(total_co2_high, 2),
        },
        trees=trees,
        diagnostics=diagnostics,
    )


def process_point_cloud(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    wood_leaf_backend: str = "tlsep",
    model_path: str | None = None,
    default_species: str | None = None,
    segmented_ply_out: str | None = None,
    max_points: int = 200_000,
    progress_callback: Any = None,
) -> PipelineResult:
    """Load a point-cloud file and run the full pipeline.

    Args:
        input_path: .las / .laz / .ply / .txt / .xyz / .csv
        output_path: optional JSON output path
        segmented_ply_out: optional path to write a per-point segmented PLY
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
        segmented_ply_out=segmented_ply_out,
        progress_callback=progress_callback,
    )
    result.metadata["input_file"] = str(input_path)

    if output_path:
        Path(output_path).write_text(
            json.dumps(
                pipeline_result_to_dict(result),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return result


# --- CLI ---
@click.group()
def cli() -> None:
    """TreeQ Carbon Platform ML Pipeline CLI."""


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True))
@click.option("--output", "output_path", type=click.Path(), default="results.json")
@click.option("--backend", type=click.Choice(["tlsep", "pointnet"]), default="tlsep")
@click.option("--model", "model_path", type=click.Path(), default=None,
              help="PointNet++ checkpoint (required for --backend pointnet)")
@click.option("--species", "default_species", default=None, help="scientific name for allometric")
@click.option("--segmented-ply", "segmented_ply_out", type=click.Path(), default=None,
              help="write a per-point segmented PLY (wood/leaf/ground) for the 3D viewer")
def process(input_path: str, output_path: str, backend: str, model_path: str | None,
            default_species: str | None, segmented_ply_out: str | None) -> None:
    """Process a point cloud file end-to-end."""

    def _print_progress(stage: str, pct: int) -> None:
        click.echo(f"[{pct:3d}%] {stage}")

    result = process_point_cloud(
        input_path,
        output_path=output_path,
        wood_leaf_backend=backend,
        model_path=model_path,
        default_species=default_species,
        segmented_ply_out=segmented_ply_out,
        progress_callback=_print_progress,
    )
    click.echo(f"\nOK - {result.summary['total_trees']} trees, "
               f"{result.summary['total_carbon_kg']} kg C, "
               f"{result.summary['total_co2eq_kg']} kg CO2eq")
    click.echo(f"OK - output written to: {output_path}")
    if segmented_ply_out:
        click.echo(f"OK - segmented PLY written to: {segmented_ply_out}")


@cli.command("eval-realdata")
@click.option("--dataset", type=click.Choice(["wan", "shivalik"]), required=True)
@click.option("--root", required=True, type=click.Path(exists=True))
@click.option("--backend", "backends", default="tlsep",
              help="comma-separated backends: tlsep,pointnet")
@click.option("--model", "model_path", type=click.Path(), default=None,
              help="PointNet++ checkpoint (required for backend pointnet)")
@click.option("--out", "output_path", type=click.Path(), default="realdata_iou.json")
@click.option("--max-points", default=200_000, type=int)
@click.option("--label-col", default=3, type=int, help="(wan) label column index")
@click.option("--wood-labels", default="0",
              help="(wan) comma-separated label values that mean wood")
def eval_realdata(dataset: str, root: str, backends: str, model_path: str | None,
                  output_path: str, max_points: int, label_col: int,
                  wood_labels: str) -> None:
    """Zero-shot wood/leaf IoU on a real labelled dataset (wan | shivalik)."""
    from pipeline import realdata_eval

    root_path = Path(root)
    backend_list = [b.strip() for b in backends.split(",") if b.strip()]
    trees: list[tuple[str, Any, Any]] = []

    if dataset == "wan":
        wood_vals = [float(x) for x in wood_labels.split(",") if x.strip()]
        files = sorted([*root_path.glob("*.txt"), *root_path.glob("*.csv")])
        for f in files:
            try:
                pts, gt = realdata_eval.load_labelled_cloud(
                    f, label_col=label_col, wood_labels=wood_vals
                )
            except Exception as exc:  # skip unreadable file, keep going
                click.echo(f"skip {f.name}: {exc}")
                continue
            trees.append((f.stem, pts, gt))
    else:  # shivalik: pair "<stem>.las" with wood-only "<stem>_wood.las"
        for f in sorted([*root_path.glob("*.las"), *root_path.glob("*.laz")]):
            if f.stem.endswith("_wood"):
                continue
            wood_only = f.with_name(f"{f.stem}_wood{f.suffix}")
            if not wood_only.exists():
                click.echo(f"skip {f.name}: missing wood-only file {wood_only.name}")
                continue
            try:
                pts, gt = realdata_eval.derive_labels_from_woodonly(f, wood_only)
                wood_frac = float(np.mean(gt == 0))
                if wood_frac in (0.0, 1.0):
                    click.echo(
                        f"warn {f.name}: wood_frac={wood_frac} — check tol or file pairing"
                    )
            except Exception as exc:  # skip unreadable/mismatched file, keep going
                click.echo(f"skip {f.name}: {exc}")
                continue
            trees.append((f.stem, pts, gt))

    if not trees:
        raise click.ClickException(f"no trees found under {root_path}")

    result = realdata_eval.evaluate_dataset(
        trees, backends=backend_list, model_path=model_path, max_points=max_points
    )
    Path(output_path).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for backend, s in result["summary"].items():
        click.echo(
            f"[{backend}] trees={s['n_trees']} "
            f"wood_iou={s['mean_wood_iou']} leaf_iou={s['mean_leaf_iou']} "
            f"mean_iou={s['mean_iou']}"
        )
    click.echo(f"OK - output written to: {output_path}")


if __name__ == "__main__":
    cli()
