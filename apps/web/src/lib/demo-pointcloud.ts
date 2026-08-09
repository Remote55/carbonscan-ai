/**
 * Synthetic tree point cloud generator — for the 3D viewer demo.
 *
 * Produces a recognizable tree (ground + trunk + branches + canopy) with a
 * per-point class label so the viewer can colour wood / leaf / ground without
 * needing the backend. Deterministic given a seed.
 *
 * Classes match the ML pipeline: 0 = WOOD, 1 = LEAF, 2 = GROUND.
 */

export const CLASS_WOOD = 0;
export const CLASS_LEAF = 1;
export const CLASS_GROUND = 2;

export interface PointCloud {
  /** flat XYZ, length = nPoints * 3 */
  positions: Float32Array;
  /** per-point class id (0=wood, 1=leaf, 2=ground), length = nPoints */
  classes: Uint8Array;
  /**
   * Whether `classes` means anything.
   *
   * A raw laser scan carries coordinates and nothing else - which point is
   * trunk and which is leaf is what the pipeline works out, not something the
   * scanner records. The loader used to fill that absence in with "ground",
   * so a whole unlabelled plot rendered as though the system had classified it
   * and decided the forest was floor. This flag exists so nothing downstream
   * can present a classification that was never made: when it is false, treat
   * `classes` as absent, not as data.
   */
  labelled: boolean;
  /**
   * What a loaded file's header claimed its vertex count was.
   *
   * Present only for clouds parsed from a PLY, and kept separate from
   * `classes.length` on purpose: the header is a claim by whoever wrote the
   * file, and the two disagreeing is a fact about the upload worth surfacing
   * rather than resolving silently in the header's favour. Undefined for
   * generated clouds, which have no claim to check.
   */
  declaredCount?: number;
}

/** Tiny seedable PRNG (mulberry32) — keeps the demo deterministic. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface DemoTreeOptions {
  seed?: number;
  height?: number; // trunk+canopy height (m)
  dbh?: number; // trunk diameter (m)
  groundPoints?: number;
  trunkPoints?: number;
  leafPoints?: number;
  branches?: number;
}

/**
 * Generate a synthetic single-tree point cloud centered at the origin.
 */
export function generateDemoTree(options: DemoTreeOptions = {}): PointCloud {
  const {
    seed = 42,
    height = 12,
    dbh = 0.4,
    groundPoints = 2000,
    trunkPoints = 1500,
    leafPoints = 5000,
    branches = 8,
  } = options;

  const rng = mulberry32(seed);
  const xs: number[] = [];
  const cls: number[] = [];
  const push = (x: number, y: number, z: number, c: number) => {
    xs.push(x, y, z);
    cls.push(c);
  };

  // Z is up. Ground = a disc at z=0.
  const groundRadius = Math.max(height * 0.4, 4);
  for (let i = 0; i < groundPoints; i++) {
    const r = Math.sqrt(rng()) * groundRadius;
    const a = rng() * Math.PI * 2;
    push(r * Math.cos(a), r * Math.sin(a), (rng() - 0.5) * 0.1, CLASS_GROUND);
  }

  // Trunk = tapering cylinder of wood points, z 0 -> trunkTop.
  const trunkTop = height * 0.6;
  for (let i = 0; i < trunkPoints; i++) {
    const z = rng() * trunkTop;
    const taper = 1 - 0.4 * (z / trunkTop);
    const radius = (dbh / 2) * taper;
    const a = rng() * Math.PI * 2;
    push(radius * Math.cos(a), radius * Math.sin(a), z, CLASS_WOOD);
  }

  // Branches = wood lines from the upper trunk into the canopy.
  for (let b = 0; b < branches; b++) {
    const zStart = trunkTop * (0.7 + 0.3 * rng());
    const az = rng() * Math.PI * 2;
    const elev = Math.PI / 6 + (rng() * Math.PI) / 6;
    const len = height * (0.2 + 0.15 * rng());
    const n = 40;
    for (let i = 0; i < n; i++) {
      const t = i / n;
      push(
        len * t * Math.cos(az) * Math.cos(elev) + (rng() - 0.5) * 0.05,
        len * t * Math.sin(az) * Math.cos(elev) + (rng() - 0.5) * 0.05,
        zStart + len * t * Math.sin(elev),
        CLASS_WOOD,
      );
    }
  }

  // Canopy = leaf points filling an ellipsoid at the top.
  const crownCenterZ = height * 0.78;
  const crownR = Math.max(height * 0.32, 2);
  const crownH = height * 0.42;
  for (let i = 0; i < leafPoints; i++) {
    const a = rng() * Math.PI * 2;
    const el = Math.asin(rng() * 2 - 1);
    const rf = Math.cbrt(rng());
    push(
      crownR * rf * Math.cos(el) * Math.cos(a),
      crownR * rf * Math.cos(el) * Math.sin(a),
      crownCenterZ + (crownH / 2) * rf * Math.sin(el),
      CLASS_LEAF,
    );
  }

  // Labelled by construction: this generator decides each point's class as it
  // places it, so there is no classification being implied that did not happen.
  return { positions: new Float32Array(xs), classes: new Uint8Array(cls), labelled: true };
}
