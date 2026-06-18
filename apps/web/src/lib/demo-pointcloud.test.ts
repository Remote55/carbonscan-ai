import { describe, expect, it } from "vitest";

import {
  CLASS_GROUND,
  CLASS_LEAF,
  CLASS_WOOD,
  generateDemoTree,
} from "./demo-pointcloud";

describe("generateDemoTree", () => {
  it("has positions length = classes length * 3", () => {
    const pc = generateDemoTree();
    expect(pc.positions.length).toBe(pc.classes.length * 3);
  });

  it("contains wood, leaf, and ground points", () => {
    const set = new Set(generateDemoTree().classes);
    expect(set.has(CLASS_WOOD)).toBe(true);
    expect(set.has(CLASS_LEAF)).toBe(true);
    expect(set.has(CLASS_GROUND)).toBe(true);
  });

  it("only emits known class ids (0,1,2)", () => {
    for (const c of generateDemoTree({ leafPoints: 50, trunkPoints: 50, groundPoints: 50 }).classes) {
      expect([CLASS_WOOD, CLASS_LEAF, CLASS_GROUND]).toContain(c);
    }
  });

  it("is deterministic for a fixed seed", () => {
    const a = generateDemoTree({ seed: 7 });
    const b = generateDemoTree({ seed: 7 });
    expect(Array.from(a.positions)).toEqual(Array.from(b.positions));
  });
});
