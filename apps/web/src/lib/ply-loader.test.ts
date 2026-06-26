import { describe, expect, it } from "vitest";

import { decimate, parsePly } from "./ply-loader";

const enc = new TextEncoder();

/** Build a binary_little_endian PLY (float x,y,z + uchar class) buffer. */
function buildBinaryPly(points: number[][], classes: number[]): ArrayBuffer {
  const header =
    "ply\n" +
    "format binary_little_endian 1.0\n" +
    `element vertex ${points.length}\n` +
    "property float x\nproperty float y\nproperty float z\nproperty uchar class\n" +
    "end_header\n";
  const head = enc.encode(header);
  const body = new ArrayBuffer(points.length * 13);
  const dv = new DataView(body);
  for (let i = 0; i < points.length; i++) {
    const o = i * 13;
    dv.setFloat32(o, points[i][0], true);
    dv.setFloat32(o + 4, points[i][1], true);
    dv.setFloat32(o + 8, points[i][2], true);
    dv.setUint8(o + 12, classes[i]);
  }
  const out = new Uint8Array(head.length + body.byteLength);
  out.set(head, 0);
  out.set(new Uint8Array(body), head.length);
  return out.buffer;
}

describe("parsePly — ascii", () => {
  it("parses positions and classes from a small ascii sample", () => {
    const ply =
      "ply\nformat ascii 1.0\nelement vertex 3\n" +
      "property float x\nproperty float y\nproperty float z\nproperty uchar class\n" +
      "end_header\n0 0 0 0\n1 2 3 1\n4 5 6 2\n";
    const { positions, classes } = parsePly(enc.encode(ply).buffer);
    expect(Array.from(positions)).toEqual([0, 0, 0, 1, 2, 3, 4, 5, 6]);
    expect(Array.from(classes)).toEqual([0, 1, 2]);
  });

  it("defaults to ground (2) when there is no class property", () => {
    const ply =
      "ply\nformat ascii 1.0\nelement vertex 2\n" +
      "property float x\nproperty float y\nproperty float z\n" +
      "end_header\n1 1 1\n2 2 2\n";
    const { positions, classes } = parsePly(enc.encode(ply).buffer);
    expect(Array.from(positions)).toEqual([1, 1, 1, 2, 2, 2]);
    expect(Array.from(classes)).toEqual([2, 2]);
  });
});

describe("parsePly — binary_little_endian", () => {
  it("round-trips a hand-built binary buffer", () => {
    const buf = buildBinaryPly(
      [
        [1, 2, 3],
        [4, 5, 6],
      ],
      [0, 1],
    );
    const { positions, classes } = parsePly(buf);
    expect(Array.from(positions)).toEqual([1, 2, 3, 4, 5, 6]);
    expect(Array.from(classes)).toEqual([0, 1]);
  });

  it("handles a property order with class before xyz is still matched by name", () => {
    // class first, then x/y/z — parser must locate by property name, not order
    const header =
      "ply\nformat binary_little_endian 1.0\nelement vertex 1\n" +
      "property uchar class\nproperty float x\nproperty float y\nproperty float z\n" +
      "end_header\n";
    const head = enc.encode(header);
    const body = new ArrayBuffer(13);
    const dv = new DataView(body);
    dv.setUint8(0, 1);
    dv.setFloat32(1, 7, true);
    dv.setFloat32(5, 8, true);
    dv.setFloat32(9, 9, true);
    const out = new Uint8Array(head.length + 13);
    out.set(head, 0);
    out.set(new Uint8Array(body), head.length);
    const { positions, classes } = parsePly(out.buffer);
    expect(Array.from(positions)).toEqual([7, 8, 9]);
    expect(Array.from(classes)).toEqual([1]);
  });
});

describe("decimate", () => {
  it("reduces point count to <= maxPoints", () => {
    const n = 1000;
    const positions = new Float32Array(n * 3);
    const classes = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      positions[i * 3] = i; // x encodes the original index
      classes[i] = i % 3;
    }
    const out = decimate({ positions, classes }, 100);
    expect(out.classes.length).toBeLessThanOrEqual(100);
    expect(out.positions.length).toBe(out.classes.length * 3);
  });

  it("keeps positions and classes paired", () => {
    const n = 1000;
    const positions = new Float32Array(n * 3);
    const classes = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      positions[i * 3] = i;
      classes[i] = i % 3;
    }
    const out = decimate({ positions, classes }, 100);
    for (let j = 0; j < out.classes.length; j++) {
      // original invariant: class === x % 3; must survive decimation
      expect(out.classes[j]).toBe(out.positions[j * 3] % 3);
    }
  });

  it("is a no-op when under the limit", () => {
    const positions = new Float32Array([0, 0, 0, 1, 1, 1]);
    const classes = new Uint8Array([0, 1]);
    const out = decimate({ positions, classes }, 100);
    expect(out.classes.length).toBe(2);
    expect(Array.from(out.positions)).toEqual([0, 0, 0, 1, 1, 1]);
  });

  it("is deterministic (seeded)", () => {
    const n = 500;
    const positions = new Float32Array(n * 3);
    const classes = new Uint8Array(n);
    for (let i = 0; i < n; i++) positions[i * 3] = i;
    const a = decimate({ positions, classes }, 50);
    const b = decimate({ positions, classes }, 50);
    expect(Array.from(a.positions)).toEqual(Array.from(b.positions));
  });
});
