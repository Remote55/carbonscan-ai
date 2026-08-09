"""What an analysis actually imports, versus what the image installs.

The container installs a hand-picked subset of services/ml/pyproject.toml,
because the full set drags in pandas, geopandas, rasterio, opencv and torch for
code an analysis never runs. That subset is only safe while it stays a superset
of what the analyse path imports, and nothing at runtime enforces that — the
failure mode is an ImportError in production on a route that worked locally.

So this reads the Dockerfile's own list and compares it against the imports in
the modules a request touches, including the lazy ones inside functions: a
deferred import still needs the package on disk when it fires.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ML_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ML_ROOT / "pipeline"
DOCKERFILE = ML_ROOT.parent / "api" / "Dockerfile"

#: Modules a POST /upload/analyze reaches, directly or through main.
ANALYSE_PATH = [
    "main",
    "ground_classification",
    "height_normalization",
    "canopy_height_model",
    "tree_segmentation",
    "wood_leaf_separation",
    "qsm",
    "allometric",
    "ply_export",
    "provenance",
    "field_eval",
]

#: Distribution name -> the name you import. Only where they differ.
IMPORT_NAME = {
    "scikit-image": "skimage",
    "scikit-learn": "sklearn",
    "opencv-python-headless": "cv2",
    "pyyaml": "yaml",
    "pillow": "PIL",
}

#: Imported by a module on the analyse path but deliberately NOT installed.
#: torch sits inside WoodLeafSegmenter.load(), which only the pointnet backend
#: calls; the production backend is tlsep. If this deployment ever offers
#: pointnet, torch moves into the image and comes off this list.
DELIBERATELY_ABSENT = {"torch"}


def _third_party_imports(path: Path) -> set[str]:
    """Every non-stdlib top-level module the file imports, lazy ones included."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    local = {"pipeline", "training", "scripts"}
    return {m for m in found if m not in sys.stdlib_module_names and m not in local}


def _dockerfile_packages() -> set[str]:
    """Import names for the pinned packages in the Dockerfile's ML pip install."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    names: set[str] = set()
    for raw in re.findall(r'"([A-Za-z0-9_.\-]+(?:\[[^\]]*\])?)[><=!]{1,2}[^"]*"', text):
        dist = raw.split("[")[0].lower()
        names.add(IMPORT_NAME.get(dist, dist.replace("-", "_")))
    return names


@pytest.mark.skipif(not DOCKERFILE.exists(), reason="API Dockerfile not present")
def test_the_image_installs_everything_an_analysis_imports():
    installed = _dockerfile_packages()
    assert installed, "parsed no packages from the Dockerfile — the parser is broken"

    missing: dict[str, set[str]] = {}
    for name in ANALYSE_PATH:
        path = PIPELINE / f"{name}.py"
        if not path.exists():
            continue
        gap = _third_party_imports(path) - installed - DELIBERATELY_ABSENT
        if gap:
            missing[name] = gap
    assert not missing, (
        f"these imports are not in the image: {missing}. Add them to the "
        "Dockerfile's pip install, or move the import off the analyse path."
    )


@pytest.mark.skipif(not DOCKERFILE.exists(), reason="API Dockerfile not present")
def test_torch_is_only_reachable_through_the_pointnet_backend():
    """The saving that keeps this image near 1 GB instead of near 3.

    If torch ever moves to module scope, importing wood_leaf_separation loads it
    on every request and the tlsep deployment pays for a backend it never uses.
    """
    source = (PIPELINE / "wood_leaf_separation.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] != "torch" for a in node.names), (
                "torch is imported at module scope"
            )
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "torch", (
                "torch is imported at module scope"
            )


#: Heavy packages in services/ml/pyproject.toml that the image leaves out.
#: torch alone is larger than everything else in the image combined.
EXCLUDED_FROM_IMAGE = [
    "torch",
    "pandas",
    "geopandas",
    "rasterio",
    "cv2",
    "sklearn",
    "shapely",
    "pyproj",
    "httpx",
    "matplotlib",
]


def test_a_real_analysis_loads_none_of_the_packages_the_image_omits():
    """The static check above reads source; this one runs a plot through the
    pipeline in a clean interpreter and looks at sys.modules afterwards. If a
    transitive import pulls one of these in, the container would fail on its
    first request and no amount of source reading would have said so.
    """
    program = (
        "import os, sys, json\n"
        "os.environ['TREEQ_GIT_COMMIT'] = '0' * 40\n"
        "os.environ['TREEQ_GIT_DIRTY'] = 'false'\n"
        "import numpy as np\n"
        "import pipeline.main\n"
        "rng = np.random.default_rng(0)\n"
        "pts = np.column_stack([rng.uniform(0, 20, 3000), rng.uniform(0, 20, 3000),"
        " rng.uniform(0, 12, 3000)])\n"
        "pipeline.main.process_points(pts)\n"
        f"heavy = {EXCLUDED_FROM_IMAGE!r}\n"
        "print(json.dumps([h for h in heavy if h in sys.modules]))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=str(ML_ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    loaded = json.loads(completed.stdout.strip().splitlines()[-1])
    assert loaded == [], (
        f"an analysis loaded {loaded}, which the container does not install"
    )


def test_the_provenance_env_vars_the_dockerfile_sets_are_the_ones_read():
    """The image bakes TREEQ_GIT_COMMIT; provenance.py reads it. A rename on
    either side turns every containerised run into a startup failure."""
    from pipeline.provenance import COMMIT_ENV_VAR, DIRTY_ENV_VAR

    text = DOCKERFILE.read_text(encoding="utf-8")
    assert f"{COMMIT_ENV_VAR}=" in text
    assert f"{DIRTY_ENV_VAR}=" in text


def test_the_dockerfile_points_ml_dir_at_where_it_copies_the_pipeline():
    """ML_DIR is where pipeline_runner looks; COPY is where the code lands. If
    they disagree the API starts, reports healthy, and fails every analysis —
    which is the exact failure this Dockerfile was rewritten to remove."""
    text = DOCKERFILE.read_text(encoding="utf-8")

    ml_dir = re.search(r"ML_DIR=(\S+)", text)
    assert ml_dir, "ML_DIR is not set — pipeline_runner would look in the repo layout"
    target = ml_dir.group(1).rstrip("/")

    workdirs = re.findall(r"^WORKDIR\s+(\S+)", text, re.MULTILINE)
    assert workdirs, "no WORKDIR, so a relative COPY destination is unresolvable"
    workdir = workdirs[-1].rstrip("/")

    destinations = set()
    for dest in re.findall(r"^COPY\s+.*?\s(\S+)\s*$", text, re.MULTILINE):
        dest = dest.rstrip("/")
        if dest.startswith("/"):
            destinations.add(dest)
        else:
            destinations.add(f"{workdir}/{dest.removeprefix('./')}")

    for needed in (f"{target}/pipeline", f"{target}/data"):
        assert needed in destinations, (
            f"nothing is copied to {needed}; COPY destinations resolve to "
            f"{sorted(destinations)}"
        )
