import { describe, expect, it } from 'vitest';

import { generateDemoTree } from './demo-pointcloud';
import { frameCloud } from './viewer-framing';

/** Half the frustum height at a given distance, for the viewer's 50-degree fov. */
function halfFrustumAt(distance: number) {
  return distance * Math.tan((25 * Math.PI) / 180);
}

/** Build a box-shaped cloud: `width` across in x and y, `height` tall in z. */
function boxCloud(width: number, height: number): Float32Array {
  const half = width / 2;
  const corners: number[] = [];
  for (const x of [-half, half]) {
    for (const y of [-half, half]) {
      for (const z of [0, height]) {
        corners.push(x, y, z);
      }
    }
  }
  return new Float32Array(corners);
}

function distanceBetween(a: readonly number[], b: readonly number[]) {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}

describe('frameCloud', () => {
  it('looks at the middle of the cloud, in world coordinates', () => {
    // 10 wide, 20 tall, sitting on z = 0. The viewer stands the cloud up, so
    // the centre it should look at is 10 above the origin in world Y.
    const framing = frameCloud(boxCloud(10, 20));

    expect(framing.target[0]).toBeCloseTo(0, 5);
    expect(framing.target[1]).toBeCloseTo(10, 5);
    expect(framing.target[2]).toBeCloseTo(0, 5);
  });

  it('fits a tall cloud in the frame rather than cropping it', () => {
    const height = 25;
    const framing = frameCloud(boxCloud(8, height));
    const distance = distanceBetween(framing.position, framing.target);

    // The whole height has to be inside the frustum at that distance...
    expect(halfFrustumAt(distance) * 2).toBeGreaterThan(height);
    // ...without pushing so far back that the subject is a speck. A quarter of
    // the frame left as margin is generous; more than that is the bug being
    // fixed here.
    expect(halfFrustumAt(distance) * 2).toBeLessThan(height * 1.75);
  });

  it('moves back for a bigger cloud instead of cropping it', () => {
    const near = distanceBetween(
      frameCloud(boxCloud(8, 10)).position,
      frameCloud(boxCloud(8, 10)).target,
    );
    const far = distanceBetween(
      frameCloud(boxCloud(8, 30)).position,
      frameCloud(boxCloud(8, 30)).target,
    );

    expect(far).toBeGreaterThan(near * 2);
  });

  it('fits a wide, flat cloud sideways as well as vertically', () => {
    // A plot is wider than it is tall, so the footprint is what has to fit.
    const framing = frameCloud(boxCloud(40, 6));
    const distance = distanceBetween(framing.position, framing.target);
    const halfDiagonal = Math.hypot(40, 40) / 2;

    expect(halfFrustumAt(distance)).toBeGreaterThan(halfDiagonal);
  });

  it('frames the demo tree more closely than the hand-tuned camera it replaces', () => {
    // The old camera sat at [10, 8, 14] looking at [0, 5, 0]: distance 17.46.
    // The point of computing this is that the subject gets bigger, so a value
    // at or above the old one means the change achieved nothing.
    const framing = frameCloud(generateDemoTree({ seed: 42 }).positions);
    const distance = distanceBetween(framing.position, framing.target);

    expect(distance).toBeLessThan(17.46);
    expect(distance).toBeGreaterThan(10);
  });

  it('keeps the camera above the horizon and off to one side', () => {
    const framing = frameCloud(boxCloud(10, 12));

    expect(framing.position[1]).toBeGreaterThan(framing.target[1]);
    expect(framing.position[0]).toBeGreaterThan(0);
    expect(framing.position[2]).toBeGreaterThan(0);
  });

  it('scales the point size with the subject so a tall cloud is not a haze', () => {
    expect(frameCloud(boxCloud(8, 30)).pointSize).toBeGreaterThan(
      frameCloud(boxCloud(8, 10)).pointSize,
    );
    expect(frameCloud(boxCloud(8, 10_000)).pointSize).toBeLessThanOrEqual(0.2);
    expect(frameCloud(boxCloud(8, 0.001)).pointSize).toBeGreaterThanOrEqual(0.02);
  });

  it('falls back to the known-good camera rather than producing NaN', () => {
    for (const broken of [
      new Float32Array(0),
      new Float32Array([1, 2]),
      new Float32Array([NaN, NaN, NaN]),
      new Float32Array([Infinity, 0, 0]),
    ]) {
      const framing = frameCloud(broken);
      expect(framing.position.every(Number.isFinite)).toBe(true);
      expect(framing.target.every(Number.isFinite)).toBe(true);
      expect(framing.pointSize).toBeGreaterThan(0);
    }
  });

  it('survives a cloud that is a single point', () => {
    const framing = frameCloud(new Float32Array([3, 4, 5]));

    expect(framing.position.every(Number.isFinite)).toBe(true);
    expect(framing.pointSize).toBeGreaterThan(0);
  });
});
