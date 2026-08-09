/**
 * Client-side PLY loader for the 3D viewer (ply-viewer spec §3.2).
 *
 * Parses ascii + binary_little_endian PLY into the same {positions, classes}
 * shape the demo generator uses, then decimates large clouds so the browser
 * stays responsive. Properties are located by name (x, y, z float + class
 * uchar); a file without a `class` property is reported as unlabelled rather
 * than assigned a class it never carried.
 *
 * Out of scope: binary_big_endian, per-tree clouds, streaming/octree.
 */

import { type PointCloud } from "./demo-pointcloud";

interface PlyProperty {
  name: string;
  type: string;
  size: number;
}

const TYPE_SIZE: Record<string, number> = {
  char: 1, uchar: 1, int8: 1, uint8: 1,
  short: 2, ushort: 2, int16: 2, uint16: 2,
  int: 4, uint: 4, int32: 4, uint32: 4,
  float: 4, float32: 4, double: 8, float64: 8,
};

const asciiDecoder = new TextDecoder("latin1");

/** Tiny seedable PRNG (mulberry32) — keeps decimation deterministic. */
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

/** Byte index just past the first occurrence of `needle` (ascii) in `bytes`. */
function indexAfter(bytes: Uint8Array, needle: string): number {
  outer: for (let i = 0; i <= bytes.length - needle.length; i++) {
    for (let j = 0; j < needle.length; j++) {
      if (bytes[i + j] !== needle.charCodeAt(j)) continue outer;
    }
    return i + needle.length;
  }
  return -1;
}

interface ParsedHeader {
  format: "ascii" | "binary_little_endian";
  count: number;
  properties: PlyProperty[];
  bodyStart: number;
}

function parseHeader(bytes: Uint8Array): ParsedHeader {
  const end = indexAfter(bytes, "end_header");
  if (end < 0) throw new Error("Invalid PLY: missing end_header");
  // Skip to the byte after the newline that terminates the end_header line.
  let bodyStart = end;
  while (bodyStart < bytes.length && bytes[bodyStart] !== 0x0a) bodyStart++;
  bodyStart++;

  const headerText = asciiDecoder.decode(bytes.subarray(0, end));
  const lines = headerText.split(/\r?\n/).map((l) => l.trim());

  let format: ParsedHeader["format"] | null = null;
  let count = 0;
  const properties: PlyProperty[] = [];
  let inVertexElement = false;

  for (const line of lines) {
    if (line.startsWith("format ")) {
      const f = line.split(/\s+/)[1];
      if (f === "ascii") format = "ascii";
      else if (f === "binary_little_endian") format = "binary_little_endian";
      else throw new Error(`Unsupported PLY format: ${f}`);
    } else if (line.startsWith("element ")) {
      const [, name, n] = line.split(/\s+/);
      inVertexElement = name === "vertex";
      if (inVertexElement) count = parseInt(n, 10);
    } else if (line.startsWith("property ") && inVertexElement) {
      const parts = line.split(/\s+/);
      // "property <type> <name>" (list properties are unsupported / not emitted by us)
      if (parts[1] === "list") throw new Error("PLY list properties are unsupported");
      const type = parts[1];
      const name = parts[2];
      const size = TYPE_SIZE[type];
      if (!size) throw new Error(`Unsupported PLY property type: ${type}`);
      properties.push({ name, type, size });
    }
  }

  if (!format) throw new Error("Invalid PLY: missing format line");
  return { format, count, properties, bodyStart };
}

function readNumber(view: DataView, offset: number, type: string): number {
  switch (type) {
    case "float":
    case "float32":
      return view.getFloat32(offset, true);
    case "double":
    case "float64":
      return view.getFloat64(offset, true);
    case "uchar":
    case "uint8":
      return view.getUint8(offset);
    case "char":
    case "int8":
      return view.getInt8(offset);
    case "short":
    case "int16":
      return view.getInt16(offset, true);
    case "ushort":
    case "uint16":
      return view.getUint16(offset, true);
    case "int":
    case "int32":
      return view.getInt32(offset, true);
    case "uint":
    case "uint32":
      return view.getUint32(offset, true);
    default:
      throw new Error(`Unsupported PLY property type: ${type}`);
  }
}

/** Parse a PLY (ascii or binary_little_endian) into {positions, classes}. */
export function parsePly(buffer: ArrayBuffer): PointCloud {
  const bytes = new Uint8Array(buffer);
  const { format, count, properties, bodyStart } = parseHeader(bytes);

  const ix = properties.findIndex((p) => p.name === "x");
  const iy = properties.findIndex((p) => p.name === "y");
  const iz = properties.findIndex((p) => p.name === "z");
  if (ix < 0 || iy < 0 || iz < 0) throw new Error("PLY missing x/y/z properties");
  const ic = properties.findIndex((p) => p.name === "class");
  // A raw scan has coordinates and nothing else. Leaving classes zero-filled
  // and saying so beats filling them in: the renderer keys off `labelled`, and
  // an invented class is a claim the pipeline never made.
  const labelled = ic >= 0;

  // `count` is a number in a file somebody uploaded. It is a claim about the
  // body, not a measurement of it, and the two used to be assumed equal: the
  // arrays were allocated from the header and never trimmed. A header reading
  // `element vertex 1000000` over ten rows of data produced a million-point
  // cloud — 999,990 of them zeroes stacked at the origin, rendered, and counted
  // everywhere the length was read. Allocate from the header, fill from the
  // body, then keep only what the body actually contained.
  const positions = new Float32Array(count * 3);
  const classes = new Uint8Array(count);
  let written = 0;

  if (format === "ascii") {
    const text = asciiDecoder.decode(bytes.subarray(bodyStart));
    const rows = text.split(/\r?\n/);
    for (let r = 0; written < count && r < rows.length; r++) {
      const row = rows[r].trim();
      if (!row) continue;
      const tok = row.split(/\s+/);
      if (tok.length <= Math.max(ix, iy, iz, labelled ? ic : 0)) continue;
      const x = parseFloat(tok[ix]);
      const y = parseFloat(tok[iy]);
      const z = parseFloat(tok[iz]);
      // A row that does not parse is not a point at the origin.
      if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;
      positions[written * 3] = x;
      positions[written * 3 + 1] = y;
      positions[written * 3 + 2] = z;
      if (labelled) classes[written] = parseInt(tok[ic], 10) & 0xff;
      written++;
    }
  } else {
    const stride = properties.reduce((s, p) => s + p.size, 0);
    const offsets: number[] = [];
    let acc = 0;
    for (const p of properties) {
      offsets.push(acc);
      acc += p.size;
    }
    // Reading past the body throws a RangeError on a DataView, so a truncated
    // or over-declared file used to take the whole viewer down rather than
    // showing the points it does have.
    const available = stride > 0 ? Math.floor((buffer.byteLength - bodyStart) / stride) : 0;
    const readable = Math.min(count, Math.max(0, available));
    const view = new DataView(buffer, bodyStart);
    for (let i = 0; i < readable; i++) {
      const base = i * stride;
      positions[i * 3] = readNumber(view, base + offsets[ix], properties[ix].type);
      positions[i * 3 + 1] = readNumber(view, base + offsets[iy], properties[iy].type);
      positions[i * 3 + 2] = readNumber(view, base + offsets[iz], properties[iz].type);
      if (labelled) {
        classes[i] = readNumber(view, base + offsets[ic], properties[ic].type) & 0xff;
      }
    }
    written = readable;
  }

  return {
    positions: written === count ? positions : positions.slice(0, written * 3),
    classes: written === count ? classes : classes.slice(0, written),
    labelled,
    declaredCount: count,
  };
}

/**
 * Downsample to at most `maxPoints` points (seeded, deterministic) keeping
 * positions/classes index-paired. Returns the cloud unchanged when small.
 */
export function decimate(cloud: PointCloud, maxPoints = 200_000): PointCloud {
  const n = cloud.classes.length;
  if (n <= maxPoints) return cloud;

  // Partial Fisher-Yates: pick maxPoints distinct indices with a fixed seed,
  // then sort them so spatial ordering (and output) stays deterministic.
  const idx = new Uint32Array(n);
  for (let i = 0; i < n; i++) idx[i] = i;
  const rng = mulberry32(0x9e3779b9);
  for (let i = 0; i < maxPoints; i++) {
    const j = i + Math.floor(rng() * (n - i));
    const tmp = idx[i];
    idx[i] = idx[j];
    idx[j] = tmp;
  }
  const chosen = Array.from(idx.subarray(0, maxPoints)).sort((a, b) => a - b);

  const positions = new Float32Array(maxPoints * 3);
  const classes = new Uint8Array(maxPoints);
  for (let k = 0; k < maxPoints; k++) {
    const s = chosen[k];
    positions[k * 3] = cloud.positions[s * 3];
    positions[k * 3 + 1] = cloud.positions[s * 3 + 1];
    positions[k * 3 + 2] = cloud.positions[s * 3 + 2];
    classes[k] = cloud.classes[s];
  }
  return { positions, classes, labelled: cloud.labelled };
}
