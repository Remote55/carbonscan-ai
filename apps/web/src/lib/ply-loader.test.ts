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

  // This used to answer "ground" for every point of a file that says nothing
  // about classes, which is how five of the six judge test files - real laser
  // scans, coordinates only - came to render as a forest made entirely of
  // floor, under a legend advertising three classes. A raw scan is unlabelled,
  // and the loader has to say so rather than pick the least alarming answer.
  it("reports a file with no class property as unlabelled, and invents nothing", () => {
    const ply =
      "ply\nformat ascii 1.0\nelement vertex 2\n" +
      "property float x\nproperty float y\nproperty float z\n" +
      "end_header\n1 1 1\n2 2 2\n";
    const cloud = parsePly(enc.encode(ply).buffer);
    expect(Array.from(cloud.positions)).toEqual([1, 1, 1, 2, 2, 2]);
    expect(cloud.labelled).toBe(false);
  });

  it("reports a file that does carry classes as labelled", () => {
    const ply =
      "ply\nformat ascii 1.0\nelement vertex 2\n" +
      "property float x\nproperty float y\nproperty float z\nproperty uchar class\n" +
      "end_header\n1 1 1 0\n2 2 2 1\n";
    expect(parsePly(enc.encode(ply).buffer).labelled).toBe(true);
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
  it("carries the labelled flag through, so a big raw scan stays honest", () => {
    const n = 500;
    const cloud = {
      positions: new Float32Array(n * 3),
      classes: new Uint8Array(n),
      labelled: false,
    };
    expect(decimate(cloud, 100).labelled).toBe(false);
    expect(decimate({ ...cloud, labelled: true }, 100).labelled).toBe(true);
  });


  it("reduces point count to <= maxPoints", () => {
    const n = 1000;
    const positions = new Float32Array(n * 3);
    const classes = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      positions[i * 3] = i; // x encodes the original index
      classes[i] = i % 3;
    }
    const out = decimate({ positions, classes, labelled: true }, 100);
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
    const out = decimate({ positions, classes, labelled: true }, 100);
    for (let j = 0; j < out.classes.length; j++) {
      // original invariant: class === x % 3; must survive decimation
      expect(out.classes[j]).toBe(out.positions[j * 3] % 3);
    }
  });

  it("is a no-op when under the limit", () => {
    const positions = new Float32Array([0, 0, 0, 1, 1, 1]);
    const classes = new Uint8Array([0, 1]);
    const out = decimate({ positions, classes, labelled: true }, 100);
    expect(out.classes.length).toBe(2);
    expect(Array.from(out.positions)).toEqual([0, 0, 0, 1, 1, 1]);
  });

  it("is deterministic (seeded)", () => {
    const n = 500;
    const positions = new Float32Array(n * 3);
    const classes = new Uint8Array(n);
    for (let i = 0; i < n; i++) positions[i * 3] = i;
    const a = decimate({ positions, classes, labelled: true }, 50);
    const b = decimate({ positions, classes, labelled: true }, 50);
    expect(Array.from(a.positions)).toEqual(Array.from(b.positions));
  });
});
