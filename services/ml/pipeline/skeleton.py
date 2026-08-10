"""Trace a crown as a branching skeleton — correct, and still not enough.

THE ALGORITHM IS RIGHT AND THE VOLUME IS STILL NOT USED. Both halves of that are
measured, and this module exists so the next person does not have to find out
again.

Crown volume is the one quantity in this pipeline no point touches: it is a
fitted whole-tree equation minus the measured stem, 54.2% MAPE against the
felled trees — unbiased on average at -1.8% and useless per tree at 0.21x to
3.24x. Two attempts have been made to measure it instead.

The first chopped the crown into axis-aligned cubes. That failed structurally: a
branch straddling a cube boundary is split across four columns and each column
contributes a cylinder of the full length, so a known cylinder read 3.89x.

This one fixes that by construction. Points are grouped into cover sets that
follow the wood rather than a grid; the sets are linked into a graph; a
breadth-first walk from the trunk gives each set its distance from the trunk in
hops; and each hop-layer is collapsed into its connected pieces, so a ring of
patches around a branch becomes the single cross-section it is. Each
cross-section contributes one cylinder whose length is the step to its parent.
Total length is the spanning tree's own length, counted once, whatever the
geometry does.

On synthetic geometry it works, and the tests hold it to that:

    full cylinder     0.97x        one-sided (half arc)   1.01x
    quarter arc       1.12x        a fork                 0.94x
    moved off the grid            identical to 3 decimals

The one-sided case is the one that matters for a laser scan, and getting it
right needed the axis position to be solved for rather than taken from the
section centroid — a scanner that sees half a branch leaves the centroid about
0.64 radii off centre, which read 0.49x before it was fixed.

ON REAL CROWNS IT DOES NOT WORK.

    skeleton traced           1490% MAPE, bias +1455%
    fitted equation - stem      54.2% MAPE, bias   -1.8%

FEXC2 is the clearest case: 26,872 crown points became a 148 m skeleton with an
implied mean branch radius of 9.1 cm, for a crown about 10 m across whose
branches are 1-5 cm. Both length and radius inflate, and for the same reason —
in a real crown the cover-set graph is a tangle. Branches touch, foliage that
survived the wood/leaf split bridges them, and hop distance stops corresponding
to distance along any one branch.

Sweeping the two parameters that control the tangling finds no stable regime:

    cover 0.10 link 0.25   +1185% bias    77 m skeleton
    cover 0.10 link 0.15     -70%          5 m
    cover 0.05 link 0.12      -3%         22 m
    cover 0.05 link 0.08     -83%          2 m
    cover 0.15 link 0.35   +1104%         54 m

A method whose answer travels from +1185% to -83% across plausible settings is
not a method waiting for the right value. The best of them, 70%, still loses to
the equation.

WHICH IS THE OPPOSITE OF THE STEM. There, following the trunk instead of fitting
each slice took the error from 934% to 12.7%: the algorithm was the problem and
fixing it fixed the answer. Here the algorithm is demonstrably right and the
input is the problem. Separating one branch from its neighbour needs point
density and a wood/leaf split that these clouds do not have, and no amount of
tracing invents it.

WHAT SHIPS: `traced_point_fraction`. How much of a crown connects back to the
trunk in a form that can be followed at all, which runs 0% to 73% across the
reference trees. That is a statement about the scan rather than the tree, and a
crown at 0% is one whose ~30% share of the tree's volume rests on an equation
and nothing else. compute_qsm reports it beside the numbers.

Shape follows TreeQSM (Raumonen et al. 2013) without its cylinder optimisation
or branch-order bookkeeping.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

#: Radius of a cover set. Each is a small patch of wood surface.
#:
#: Large enough to hold points from both sides of a thin branch, small enough
#: that the patch is shorter than the branch curves. TreeQSM uses a similar
#: scale and varies it with local density; this does not.
COVER_RADIUS_M = 0.10

#: Two cover sets are neighbours when their centres are within this. Slightly
#: more than twice the cover radius, so adjacent patches along a branch connect
#: while patches on different branches passing near each other usually do not.
LINK_RADIUS_M = 0.25

#: A cover set with fewer points than this says nothing reliable about a radius.
MIN_POINTS_PER_SET = 5

#: Bounds on a plausible branch radius. Below the first is scanner noise rather
#: than wood; above the second the patch has caught more than one branch.
MIN_BRANCH_RADIUS_M = 0.005
MAX_BRANCH_RADIUS_M = 0.25


@dataclass(frozen=True)
class Skeleton:
    """A crown traced as cylinders, and what could not be traced."""

    volume_m3: float
    #: Cylinders in the spanning tree — one per cover set that has a parent.
    n_segments: int
    #: Total skeleton length in metres.
    length_m: float
    #: Share of crown points that ended up inside a measured cylinder. The rest
    #: were unreachable from the trunk, too sparse, or implausibly thick.
    traced_point_fraction: float
    #: Cover sets the walk never reached — wood the scan left disconnected.
    n_unreachable_sets: int


def build_cover_sets(
    points: np.ndarray, *, radius: float = COVER_RADIUS_M
) -> tuple[np.ndarray, np.ndarray]:
    """Greedy ball cover: patches that follow the wood rather than a grid.

    Returns (label per point, centre per set). Every point gets exactly one
    label, which is what makes the volume below impossible to double count.
    """
    n = len(points)
    labels = np.full(n, -1, dtype=np.int64)
    tree = cKDTree(points)
    centres: list[np.ndarray] = []

    # Seeding in a fixed order keeps the result reproducible; the order itself
    # is arbitrary and the cover is not sensitive to it.
    for seed in range(n):
        if labels[seed] != -1:
            continue
        members = tree.query_ball_point(points[seed], radius)
        fresh = [index for index in members if labels[index] == -1]
        if not fresh:
            continue
        label = len(centres)
        labels[fresh] = label
        centres.append(points[fresh].mean(axis=0))

    return labels, np.asarray(centres) if centres else np.empty((0, 3))


def _radius_from_axis(
    member_points: np.ndarray, start: np.ndarray, direction: np.ndarray
) -> float | None:
    """Radius of the cylinder these points lie on, given its direction.

    Every point on a cylinder's surface is one radius from the axis, whichever
    side the scanner saw — but only from the *axis*. Measuring from the section's
    centroid is not the same thing: a scanner that sees half a branch leaves the
    centroid inside the arc, about 0.64 radii off centre, and every distance
    measured from there comes out short. On a synthetic half-cylinder that read
    0.49x the true volume, and on a quarter, 0.14x.

    So the direction comes from the skeleton and the position is solved for:
    slide the axis until the points are as nearly equidistant from it as they
    can be. That is a two-parameter fit in the plane across the branch, seeded
    from the centroid, and it is what makes a one-sided scan measurable.
    """
    if len(member_points) < 3:
        return None
    norm = np.linalg.norm(direction)
    if norm <= 0:
        return None
    unit = direction / norm

    offset = member_points - start
    along = offset @ unit
    perpendicular = offset - np.outer(along, unit)

    # Two axes spanning the plane across the branch.
    helper = np.array([1.0, 0.0, 0.0])
    if abs(float(unit @ helper)) > 0.9:
        helper = np.array([0.0, 1.0, 0.0])
    basis_u = np.cross(unit, helper)
    basis_u /= np.linalg.norm(basis_u)
    basis_v = np.cross(unit, basis_u)
    flat = np.column_stack([perpendicular @ basis_u, perpendicular @ basis_v])

    return _geometric_circle_radius(flat)


def _geometric_circle_radius(flat: np.ndarray, *, iterations: int = 12) -> float | None:
    """Radius of the circle best fitting 2D points, by Gauss-Newton.

    Minimises the spread of the distances rather than an algebraic residual.
    Algebraic fits (Kasa) are cheaper and were tried first; they are biased on
    short arcs and answer one with an enormous circle, which is the same trap
    documented in qsm._ransac_circle_fit. Iterating on the geometry does not
    have that failure.
    """
    if len(flat) < 3:
        return None
    centre = flat.mean(axis=0)
    for _ in range(iterations):
        offset = flat - centre
        distance = np.linalg.norm(offset, axis=1)
        if not np.all(np.isfinite(distance)) or np.any(distance < 1e-12):
            break
        unit_offset = offset / distance[:, None]
        mean_distance = float(distance.mean())
        # d(residual)/d(centre) = -unit_offset, plus the mean's own dependence.
        jacobian = -(unit_offset - unit_offset.mean(axis=0))
        residual = distance - mean_distance
        try:
            step, *_ = np.linalg.lstsq(jacobian, -residual, rcond=None)
        except np.linalg.LinAlgError:  # pragma: no cover - numerical pathology
            break
        if not np.all(np.isfinite(step)):
            break
        centre = centre + step
        if float(np.linalg.norm(step)) < 1e-6:
            break

    radius = float(np.median(np.linalg.norm(flat - centre, axis=1)))
    return radius if np.isfinite(radius) else None


def trace_crown(
    crown_points: np.ndarray,
    *,
    root_xyz: np.ndarray | None = None,
    cover_radius: float = COVER_RADIUS_M,
    link_radius: float = LINK_RADIUS_M,
    min_points_per_set: int = MIN_POINTS_PER_SET,
) -> Skeleton:
    """Trace and measure a crown.

    Args:
        crown_points: (N, 3) wood points above the stem.
        root_xyz: where the crown joins the trunk. The nearest cover set becomes
            the root of the walk. Defaults to the lowest point, which is where
            the stem was.

    Returns:
        Skeleton. Check ``traced_point_fraction`` before trusting the volume: a
        crown the scan left in disconnected fragments cannot be walked, and what
        is returned is then a floor rather than an estimate.
    """
    points = np.asarray(crown_points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {points.shape}")
    if len(points) < min_points_per_set:
        return Skeleton(0.0, 0, 0.0, 0.0, 0)

    labels, centres = build_cover_sets(points, radius=cover_radius)
    if len(centres) < 2:
        return Skeleton(0.0, 0, 0.0, 0.0, 0)

    members: list[list[int]] = [[] for _ in range(len(centres))]
    for index, label in enumerate(labels):
        members[label].append(index)

    # Neighbour graph over cover sets.
    centre_tree = cKDTree(centres)
    pairs = centre_tree.query_pairs(link_radius)
    adjacency: list[list[int]] = [[] for _ in range(len(centres))]
    for a, b in pairs:
        adjacency[a].append(b)
        adjacency[b].append(a)

    if root_xyz is None:
        root = int(np.argmin(centres[:, 2]))
    else:
        root = int(np.argmin(np.linalg.norm(centres - np.asarray(root_xyz, float), axis=1)))

    # Distance from the trunk, in hops. This is the coordinate the skeleton runs
    # along: sets the same number of hops from the root sit at the same place on
    # the branch, whichever side of it the scanner happened to see.
    depth = np.full(len(centres), -1, dtype=np.int64)
    depth[root] = 0
    queue = deque([root])
    while queue:
        current = queue.popleft()
        for neighbour in adjacency[current]:
            if depth[neighbour] == -1:
                depth[neighbour] = depth[current] + 1
                queue.append(neighbour)

    # One node per cross-section, not one per surface patch.
    #
    # A branch is a tube, so cover sets at the same height on opposite sides are
    # neighbours too, and a walk over sets alone travels around the
    # circumference as well as along the wood. On a 2 m cylinder that returned a
    # 3.9 m skeleton — the length nearly doubled by going round. Grouping each
    # hop-distance layer into its connected pieces collapses a ring of patches
    # into the single cross-section it is.
    layers: dict[int, list[int]] = {}
    for node in range(len(centres)):
        if depth[node] >= 0:
            layers.setdefault(int(depth[node]), []).append(node)

    sections = _sections_by_layer(layers, adjacency, centres, members)

    volume = 0.0
    length = 0.0
    segments = 0
    traced_points = 0
    for section in sections:
        if section.parent_centre is None or len(section.member_points) < min_points_per_set:
            continue
        direction = section.centre - section.parent_centre
        edge_length = float(np.linalg.norm(direction))
        if edge_length <= 0:
            continue
        radius = _radius_from_axis(
            points[section.member_points], section.parent_centre, direction
        )
        if radius is None or not (MIN_BRANCH_RADIUS_M <= radius <= MAX_BRANCH_RADIUS_M):
            continue
        volume += float(np.pi * radius * radius * edge_length)
        length += edge_length
        segments += 1
        traced_points += len(section.member_points)

    return Skeleton(
        volume_m3=volume,
        n_segments=segments,
        length_m=length,
        traced_point_fraction=float(traced_points / len(points)),
        n_unreachable_sets=int((depth < 0).sum()),
    )


@dataclass
class _Section:
    """One cross-section of one branch: a layer's worth of connected patches."""

    centre: np.ndarray
    parent_centre: np.ndarray | None
    member_points: list[int]


def _sections_by_layer(
    layers: dict[int, list[int]],
    adjacency: list[list[int]],
    centres: np.ndarray,
    members: list[list[int]],
) -> list[_Section]:
    """Collapse each hop-distance layer into its connected pieces.

    Two patches in the same layer belong to the same cross-section when they
    touch. Where a branch forks, the layer splits into two pieces and each gets
    its own cylinder — which is the only place this code knows a fork happened.
    """
    sections: list[_Section] = []
    previous: list[_Section] = []

    for hop in sorted(layers):
        nodes = layers[hop]
        node_set = set(nodes)
        # Connected components within the layer.
        unvisited = set(nodes)
        components: list[list[int]] = []
        while unvisited:
            start = unvisited.pop()
            component = [start]
            stack = [start]
            while stack:
                current = stack.pop()
                for neighbour in adjacency[current]:
                    if neighbour in node_set and neighbour in unvisited:
                        unvisited.discard(neighbour)
                        component.append(neighbour)
                        stack.append(neighbour)
            components.append(component)

        current_layer: list[_Section] = []
        for component in components:
            point_indices: list[int] = []
            for node in component:
                point_indices.extend(members[node])
            centre = centres[component].mean(axis=0)
            # The parent is whichever previous-layer section is nearest. A layer
            # is one hop from the last, so nearest is the branch it grew from.
            parent_centre = None
            if previous:
                distances = [float(np.linalg.norm(centre - s.centre)) for s in previous]
                parent_centre = previous[int(np.argmin(distances))].centre
            current_layer.append(_Section(centre, parent_centre, point_indices))

        sections.extend(current_layer)
        previous = current_layer

    return sections
