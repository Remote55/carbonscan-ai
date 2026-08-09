"""Scale, which is the whole question for photogrammetry.

SfM reconstructs shape and not size, so a cloud built from photographs has no
unit. The reprojection error is identical whether the trunk is 30 cm or 30 km
across. Everything here is about refusing to produce a number when nothing in
the scene establishes what a unit is worth.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from photogrammetry.scale import (
    MAX_CORNER_DISAGREEMENT,
    ScaleEstimate,
    ScaleUnavailable,
    check_photoset_for_scale_reference,
    combine_scale_estimates,
    detect_marker_pixel_corners,
    generate_marker,
    scale_from_marker_corners,
)

cv2 = pytest.importorskip("cv2")
needs_aruco = pytest.mark.skipif(
    not hasattr(cv2, "aruco"), reason="opencv build has no aruco module"
)


def _square(side_units: float, *, rotate: float = 0.0, offset=(0.0, 0.0, 0.0)):
    """Four corners of a flat square, optionally turned in its own plane."""
    half = side_units / 2
    base = np.array(
        [[-half, -half, 0.0], [half, -half, 0.0], [half, half, 0.0], [-half, half, 0.0]]
    )
    c, s = math.cos(rotate), math.sin(rotate)
    spin = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    return base @ spin.T + np.asarray(offset)


class TestScaleFromCorners:
    def test_recovers_metres_per_unit(self):
        # A 0.2 m marker reconstructed 4 units across: 1 unit is 5 cm.
        estimate = scale_from_marker_corners(_square(4.0), marker_side_m=0.2)
        assert estimate.metres_per_unit == pytest.approx(0.05, rel=1e-9)
        assert estimate.sample_count == 6

    def test_does_not_care_where_the_marker_sits_or_how_it_is_turned(self):
        plain = scale_from_marker_corners(_square(4.0), marker_side_m=0.2)
        moved = scale_from_marker_corners(
            _square(4.0, rotate=0.7, offset=(12.0, -3.0, 8.0)), marker_side_m=0.2
        )
        assert moved.metres_per_unit == pytest.approx(plain.metres_per_unit, rel=1e-9)

    def test_scaling_a_cloud_puts_it_in_metres(self):
        estimate = scale_from_marker_corners(_square(4.0), marker_side_m=0.2)
        trunk = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [0.0, 0.0, 200.0]])
        assert estimate.apply(trunk)[1][0] == pytest.approx(0.15)
        assert estimate.apply(trunk)[2][2] == pytest.approx(10.0)

    def test_the_diagonals_are_used_not_just_the_sides(self):
        """Four sides alone cannot tell a square from a rhombus, and a rhombus
        implies a different scale. Six observations, not four."""
        # A true rhombus: all four sides exactly 4, interior angle 60 degrees.
        # Sides alone see a perfect square. The diagonals do not.
        h = 4.0 * math.sin(math.pi / 3)
        w = 4.0 * math.cos(math.pi / 3)
        rhombus = np.array(
            [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [4.0 + w, h, 0.0], [w, h, 0.0]]
        )

        lengths = [
            float(np.linalg.norm(rhombus[i] - rhombus[(i + 1) % 4])) for i in range(4)
        ]
        assert max(lengths) - min(lengths) < 1e-9, "the fixture is not a rhombus"

        with pytest.raises(ScaleUnavailable, match="disagree"):
            scale_from_marker_corners(rhombus, marker_side_m=0.2)

    def test_a_detection_that_is_not_square_is_refused(self):
        stretched = np.array(
            [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [4.0, 6.0, 0.0], [0.0, 6.0, 0.0]]
        )
        with pytest.raises(ScaleUnavailable):
            scale_from_marker_corners(stretched, marker_side_m=0.2)

    def test_small_reconstruction_noise_is_tolerated(self):
        rng = np.random.default_rng(0)
        noisy = _square(4.0) + rng.normal(0, 0.02, (4, 3))
        estimate = scale_from_marker_corners(noisy, marker_side_m=0.2)
        assert estimate.metres_per_unit == pytest.approx(0.05, rel=0.05)
        assert estimate.relative_spread < MAX_CORNER_DISAGREEMENT

    def test_non_finite_corners_are_refused_rather_than_producing_nan(self):
        broken = _square(4.0)
        broken[2][0] = np.nan
        with pytest.raises(ScaleUnavailable):
            scale_from_marker_corners(broken, marker_side_m=0.2)

    def test_a_degenerate_marker_is_refused(self):
        with pytest.raises(ScaleUnavailable):
            scale_from_marker_corners(np.zeros((4, 3)), marker_side_m=0.2)

    @pytest.mark.parametrize("bad_side", [0.0, -0.2])
    def test_a_nonsense_printed_size_is_a_programming_error(self, bad_side):
        with pytest.raises(ValueError):
            scale_from_marker_corners(_square(4.0), marker_side_m=bad_side)

    def test_wrong_shape_input_is_rejected(self):
        with pytest.raises(ValueError):
            scale_from_marker_corners(np.zeros((3, 3)), marker_side_m=0.2)


class TestCombining:
    def test_two_markers_that_agree_are_stronger_than_one(self):
        a = scale_from_marker_corners(_square(4.0), marker_side_m=0.2)
        b = scale_from_marker_corners(_square(8.0), marker_side_m=0.4)
        merged = combine_scale_estimates([a, b])
        assert merged.metres_per_unit == pytest.approx(0.05, rel=1e-9)
        assert merged.sample_count == 12

    def test_markers_that_disagree_are_refused_not_averaged(self):
        """Averaging a right answer with a wrong one produces a wrong answer
        that looks like it was measured twice."""
        a = ScaleEstimate(0.05, 6, 0.0, "a")
        b = ScaleEstimate(0.09, 6, 0.0, "b")
        with pytest.raises(ScaleUnavailable, match="disagree"):
            combine_scale_estimates([a, b])

    def test_nothing_to_combine_is_refused(self):
        with pytest.raises(ScaleUnavailable):
            combine_scale_estimates([])


@needs_aruco
class TestMarkerDetection:
    def test_a_generated_marker_is_found_again(self, tmp_path):
        path = generate_marker(tmp_path / "marker.png", marker_id=7, pixels=600)
        assert path.is_file()

        padded = tmp_path / "scene.png"
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        canvas = np.full((900, 900), 255, dtype=np.uint8)
        canvas[150:750, 150:750] = image
        cv2.imwrite(str(padded), canvas)

        found = detect_marker_pixel_corners(padded)
        assert 7 in found
        assert found[7].shape == (4, 2)

    def test_a_photograph_of_nothing_finds_nothing(self, tmp_path):
        blank = tmp_path / "blank.png"
        cv2.imwrite(str(blank), np.full((400, 400), 200, dtype=np.uint8))
        assert detect_marker_pixel_corners(blank) == {}

    def test_an_unreadable_file_is_reported_not_silently_empty(self, tmp_path):
        broken = tmp_path / "broken.png"
        broken.write_bytes(b"not an image")
        with pytest.raises(ValueError):
            detect_marker_pixel_corners(broken)


@needs_aruco
class TestPhotosetCheck:
    """Answered before reconstruction, which takes minutes to hours. A photo set
    with no marker produces a cloud that cannot be measured, however good it
    looks, and finding that out afterwards wastes the whole run."""

    def _scene(self, directory, count, *, with_marker):
        marker = cv2.imread(
            str(generate_marker(directory / "_marker.png", marker_id=3, pixels=400)),
            cv2.IMREAD_GRAYSCALE,
        )
        (directory / "_marker.png").unlink()
        for i in range(count):
            canvas = np.full((700, 700), 210, dtype=np.uint8)
            if with_marker:
                canvas[100:500, 100:500] = marker
            cv2.imwrite(str(directory / f"shot{i:02d}.png"), canvas)

    def test_a_set_with_markers_is_usable(self, tmp_path):
        self._scene(tmp_path, 5, with_marker=True)
        report = check_photoset_for_scale_reference(tmp_path)
        assert report["usable"] is True
        assert report["images_with_marker"] == 5
        assert report["marker_ids"] == [3]

    def test_a_set_without_markers_says_why_it_cannot_be_scaled(self, tmp_path):
        self._scene(tmp_path, 5, with_marker=False)
        report = check_photoset_for_scale_reference(tmp_path)
        assert report["usable"] is False
        assert "no unit" in str(report["reason"])

    def test_a_marker_in_only_one_photograph_is_not_enough(self, tmp_path):
        self._scene(tmp_path, 1, with_marker=True)
        self._scene(tmp_path / "extra", 0, with_marker=False)
        report = check_photoset_for_scale_reference(tmp_path)
        assert report["usable"] is False

    def test_a_missing_directory_is_an_error_not_an_empty_report(self, tmp_path):
        with pytest.raises(NotADirectoryError):
            check_photoset_for_scale_reference(tmp_path / "nope")
