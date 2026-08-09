"""Give a photogrammetric cloud a unit.

Structure from Motion reconstructs shape, not size. Two photo sets of the same
trunk produce clouds that differ by an arbitrary factor, and nothing in the
reconstruction can tell you which one is metres — the reprojection error is
identical at any scale. A diameter read off an unscaled cloud is a number with
no unit attached, and printing "cm" next to it does not supply one.

Something of known size has to appear in the photographs. A printed ArUco
marker is the cheapest such thing: a sheet of A4, free to produce, detected
without training, and it double-checks itself because a square has four corners
whose six pairwise distances must agree.

This module does not run SfM. It answers one question — how many metres is a
reconstruction unit worth — and refuses when the evidence does not support an
answer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np

#: The marker dictionary a printed target should use. 4x4_50 has the largest
#: modules for a given paper size, which is what survives being photographed
#: from five metres away in a forest.
DEFAULT_ARUCO_DICT = "DICT_4X4_50"

#: Corner-distance measurements are expected to agree with each other. A square
#: seen at an angle still has four equal sides and two equal diagonals once the
#: pose is solved; large disagreement means the detection is not a flat square,
#: so the scale it implies is not trustworthy.
MAX_CORNER_DISAGREEMENT = 0.08


class ScaleUnavailable(RuntimeError):
    """No defensible metres-per-unit could be derived.

    Raised rather than returning 1.0 or a guess. A cloud with the wrong scale
    produces a diameter that looks entirely normal and is wrong by whatever
    factor SfM happened to choose, and nothing downstream can detect that.
    """


@dataclass(frozen=True)
class ScaleEstimate:
    """How many metres one reconstruction unit is worth, and how well we know."""

    metres_per_unit: float
    #: How many independent observations went into it.
    sample_count: int
    #: Relative spread across those observations. Small means the observations
    #: agree; large means they do not and the mean is hiding that.
    relative_spread: float
    source: str

    def apply(self, points: np.ndarray) -> np.ndarray:
        """Return a copy of `points` in metres."""
        return np.asarray(points, dtype=np.float64) * self.metres_per_unit


def _aruco():
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - opencv is a hard dependency
        raise ScaleUnavailable("opencv is required to detect markers") from exc
    if not hasattr(cv2, "aruco"):
        raise ScaleUnavailable("this opencv build has no aruco module")
    return cv2


def generate_marker(
    output_path: str | Path,
    *,
    marker_id: int = 0,
    pixels: int = 1200,
    dictionary: str = DEFAULT_ARUCO_DICT,
) -> Path:
    """Write a printable marker.

    Print it at a measured size, put it in the frame beside the trunk, and pass
    that measured side length to `scale_from_marker`. The printed size is the
    only thing in the whole pipeline that carries a real unit, so measure the
    paper rather than trusting the printer's scaling.
    """
    cv2 = _aruco()
    catalogue = getattr(cv2.aruco, dictionary, None)
    if catalogue is None:
        raise ValueError(f"unknown ArUco dictionary: {dictionary}")
    board = cv2.aruco.getPredefinedDictionary(catalogue)
    image = cv2.aruco.generateImageMarker(board, marker_id, pixels)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise OSError(f"could not write marker to {path}")
    return path


def _corner_distances(corners: np.ndarray) -> tuple[list[float], list[float]]:
    """Side and diagonal lengths of a quadrilateral, in whatever unit it is in."""
    sides = [
        float(np.linalg.norm(corners[i] - corners[(i + 1) % 4])) for i in range(4)
    ]
    diagonals = [
        float(np.linalg.norm(corners[0] - corners[2])),
        float(np.linalg.norm(corners[1] - corners[3])),
    ]
    return sides, diagonals


def scale_from_marker_corners(
    corners_in_cloud: np.ndarray,
    *,
    marker_side_m: float,
    source: str = "aruco marker corners",
) -> ScaleEstimate:
    """Metres per unit, from one marker's four reconstructed corners.

    Args:
        corners_in_cloud: (4, 3) corner positions in reconstruction units, in
            order around the square.
        marker_side_m: the printed side length, measured with a ruler.

    The four sides and two diagonals give six observations of the same ratio
    once the diagonals are divided by sqrt(2). They should agree; if they do
    not, the detection is not a flat square and its scale is refused rather
    than averaged into something plausible-looking.
    """
    corners = np.asarray(corners_in_cloud, dtype=np.float64)
    if corners.shape != (4, 3):
        raise ValueError(f"expected 4 corners of 3 coordinates, got {corners.shape}")
    if not np.all(np.isfinite(corners)):
        raise ScaleUnavailable("marker corners contain non-finite coordinates")
    if marker_side_m <= 0:
        raise ValueError(f"marker side must be positive, got {marker_side_m}")

    sides, diagonals = _corner_distances(corners)
    observations = sides + [d / math.sqrt(2.0) for d in diagonals]
    if min(observations) <= 0:
        raise ScaleUnavailable("marker corners are degenerate — zero-length side")

    mean = float(np.mean(observations))
    spread = float(np.max(observations) - np.min(observations)) / mean
    if spread > MAX_CORNER_DISAGREEMENT:
        raise ScaleUnavailable(
            f"marker corners disagree by {spread:.1%} about how big the square is, "
            f"above the {MAX_CORNER_DISAGREEMENT:.0%} bar — the detection is not a "
            "flat square, so the scale it implies is not usable"
        )

    return ScaleEstimate(
        metres_per_unit=marker_side_m / mean,
        sample_count=len(observations),
        relative_spread=spread,
        source=source,
    )


def combine_scale_estimates(estimates: list[ScaleEstimate]) -> ScaleEstimate:
    """Merge several markers' answers, refusing if they disagree.

    More than one marker in the scene is worth having: two independent answers
    that agree is evidence, and one answer is only an assertion. Disagreement
    means at least one detection is wrong, and taking the mean would bury that.
    """
    if not estimates:
        raise ScaleUnavailable("no scale observations")
    values = [e.metres_per_unit for e in estimates]
    mean = float(np.mean(values))
    if mean <= 0:
        raise ScaleUnavailable("scale observations are not positive")
    spread = (max(values) - min(values)) / mean
    if len(values) > 1 and spread > MAX_CORNER_DISAGREEMENT:
        raise ScaleUnavailable(
            f"markers disagree about scale by {spread:.1%}; at least one detection "
            "is wrong and averaging them would hide which"
        )
    return ScaleEstimate(
        metres_per_unit=mean,
        sample_count=sum(e.sample_count for e in estimates),
        relative_spread=spread,
        source=f"{len(estimates)} marker(s)",
    )


def detect_marker_pixel_corners(
    image_path: str | Path,
    *,
    dictionary: str = DEFAULT_ARUCO_DICT,
) -> dict[int, np.ndarray]:
    """Find markers in one photograph. Returns {marker_id: (4, 2) pixel corners}.

    This locates the marker in the image. Turning that into a scale needs the
    corners' positions in the reconstruction, which only SfM can supply — see
    scale_from_marker_corners. Kept separate so the detection can be checked on
    a photograph before any reconstruction has been attempted.
    """
    cv2 = _aruco()
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"could not read image: {path}")

    catalogue = getattr(cv2.aruco, dictionary, None)
    if catalogue is None:
        raise ValueError(f"unknown ArUco dictionary: {dictionary}")
    detector = cv2.aruco.ArucoDetector(
        cv2.aruco.getPredefinedDictionary(catalogue),
        cv2.aruco.DetectorParameters(),
    )
    corners, ids, _rejected = detector.detectMarkers(image)
    if ids is None or len(ids) == 0:
        return {}
    return {
        int(marker_id): np.asarray(corner, dtype=np.float64).reshape(4, 2)
        for marker_id, corner in zip(ids.flatten(), corners, strict=True)
    }


def check_photoset_for_scale_reference(
    image_dir: str | Path,
    *,
    dictionary: str = DEFAULT_ARUCO_DICT,
    min_images_with_marker: int = 3,
) -> dict[str, object]:
    """Can this photo set be scaled at all? Answer before running SfM.

    Reconstruction takes minutes to hours. Discovering afterwards that nobody
    put a marker in the frame wastes all of it, and the resulting cloud is
    unusable for measurement no matter how good it looks.
    """
    directory = Path(image_dir)
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    suffixes = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    images = sorted(p for p in directory.iterdir() if p.suffix.lower() in suffixes)

    seen: dict[int, int] = {}
    with_marker = 0
    for image in images:
        try:
            found = detect_marker_pixel_corners(image, dictionary=dictionary)
        except (ValueError, FileNotFoundError):
            continue
        if found:
            with_marker += 1
        for marker_id in found:
            seen[marker_id] = seen.get(marker_id, 0) + 1

    usable = with_marker >= min_images_with_marker
    return {
        "image_count": len(images),
        "images_with_marker": with_marker,
        "marker_ids": sorted(seen),
        "per_marker_image_count": seen,
        "usable": usable,
        "reason": (
            ""
            if usable
            else (
                f"a marker appears in {with_marker} of {len(images)} photographs; "
                f"at least {min_images_with_marker} are needed for its corners to be "
                "reconstructed reliably. Without one, the cloud has no unit and any "
                "diameter measured from it is meaningless."
            )
        ),
    }
