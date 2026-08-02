/**
 * Where to put the camera so a point cloud fills the frame.
 *
 * The viewer used a camera fixed at [10, 8, 14] looking at [0, 5, 0]. That was
 * tuned by eye against the 12 m demo tree, so every other cloud was framed by
 * accident: a 25 m scan overflowed and a small one sat in the middle of an
 * empty stage. The designer's note was that the tree is small enough to have to
 * squint at, which is the same defect seen from the other side.
 *
 * So compute it. The maths is a fit of the cloud's bounding box into the
 * camera frustum, which means it holds for any cloud rather than for one.
 */

/** Camera parameters for a cloud, in world (Y-up) space. */
export interface CloudFraming {
  position: [number, number, number];
  target: [number, number, number];
  /** Point radius that keeps the cloud legible at that distance. */
  pointSize: number;
}

/**
 * Direction from the subject to the camera, as a unit vector. This is the old
 * camera's angle - about 10 degrees above the horizon, three-quarter view -
 * kept deliberately: it is the framing everyone on the team recognises, and
 * only the distance was ever wrong.
 */
const VIEW_DIRECTION = normalise([10, 3, 14]);
const FOV_DEGREES = 50;

/** Air around the cloud, so orbiting a little does not immediately clip it. */
const MARGIN = 1.1;

const FALLBACK: CloudFraming = {
  position: [10, 8, 14],
  target: [0, 5, 0],
  pointSize: 0.05,
};

function normalise([x, y, z]: [number, number, number]): [number, number, number] {
  const length = Math.hypot(x, y, z);
  return [x / length, y / length, z / length];
}

/**
 * Frame a cloud given as flat XYZ triples in pipeline coordinates (Z-up).
 *
 * The viewer rotates the cloud -90 degrees about X to stand it up, so a
 * pipeline point (x, y, z) is drawn at world (x, z, -y). The bounds are
 * converted here rather than in the caller, so this function and the mesh
 * cannot disagree about which axis is up.
 *
 * `aspect` is the canvas width over its height. It has to be the real one: a
 * forest plot is far wider than it is tall, so the horizontal fit decides the
 * distance, and guessing a square viewport parks the camera about twice as far
 * back as a landscape stage needs - which is how a plot ends up as a small
 * patch in the middle of a large empty frame.
 */
export function frameCloud(positions: Float32Array, aspect = 1): CloudFraming {
  if (positions.length < 3) return FALLBACK;

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;

  for (let i = 0; i < positions.length; i += 3) {
    const x = positions[i];
    const y = positions[i + 1];
    const z = positions[i + 2];
    if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
    if (z < minZ) minZ = z;
    if (z > maxZ) maxZ = z;
  }

  if (!Number.isFinite(minX) || !Number.isFinite(minZ)) return FALLBACK;

  // Pipeline (x, y, z) is drawn at world (x, z, -y).
  const centre: [number, number, number] = [
    (minX + maxX) / 2,
    (minZ + maxZ) / 2,
    -(minY + maxY) / 2,
  ];

  const halfHeight = (maxZ - minZ) / 2;
  // Half the diagonal of the footprint: the widest the cloud can be from any
  // angle the camera might be orbited to.
  const halfFootprint = Math.hypot(maxX - minX, maxY - minY) / 2;

  const halfFov = (FOV_DEGREES / 2) * (Math.PI / 180);
  const elevation = Math.asin(VIEW_DIRECTION[1]);

  // Seen from an elevated camera, a standing cloud takes up its height times
  // the cosine of that elevation, plus part of its footprint tilted into view.
  const halfVertical = halfHeight * Math.cos(elevation) + halfFootprint * Math.sin(elevation);

  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? aspect : 1;
  const distance =
    Math.max(
      halfVertical / Math.tan(halfFov),
      halfFootprint / (Math.tan(halfFov) * safeAspect),
    ) * MARGIN;

  if (!Number.isFinite(distance) || distance <= 0) return FALLBACK;

  return {
    position: [
      centre[0] + VIEW_DIRECTION[0] * distance,
      centre[1] + VIEW_DIRECTION[1] * distance,
      centre[2] + VIEW_DIRECTION[2] * distance,
    ],
    target: centre,
    // Points are drawn with size attenuation, so a fixed radius turns a tall
    // cloud into a sparse haze and a small one into paste. Tie it to the
    // subject instead: about a two-hundredth of its height.
    pointSize: Math.min(0.2, Math.max(0.02, (maxZ - minZ) / 200)),
  };
}
