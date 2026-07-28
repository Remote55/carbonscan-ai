import { describe, expect, it } from "vitest";

import type { AnalyzeResponse } from "./api";
import { reasonLabel, toResultViewModel } from "./result-view-model";

const BASE = {
  metadata: { status: "ok" },
  trees: [],
} as unknown as AnalyzeResponse;

const RESPONSE_WITH_DIAGNOSTICS: AnalyzeResponse = {
  ...BASE,
  summary: {
    total_trees: 18,
    total_carbon_kg: 25400.58,
    total_co2eq_kg: 93135,
    detected_trees: 20,
    measured_trees: 18,
    excluded_trees: 2,
  },
  diagnostics: {
    excluded_segments: [
      { tree_id: 11, stage: "wood_leaf", reason_code: "WOOD_EMPTY" },
      { tree_id: 17, stage: "qsm", reason_code: "QSM_INVALID" },
    ],
  },
};

/** A result stored by pipeline 0.3.0, before diagnostics existed. */
const LEGACY_RESPONSE: AnalyzeResponse = {
  ...BASE,
  summary: { total_trees: 18, total_carbon_kg: 25400.58, total_co2eq_kg: 93135 },
};

describe("toResultViewModel", () => {
  it("reports total_trees as measured, never as detected", () => {
    const vm = toResultViewModel(RESPONSE_WITH_DIAGNOSTICS);

    expect(vm.counts).toEqual({ detected: 20, measured: 18, excluded: 2 });
    expect(vm.countsLabel.measured).toBe("ต้นไม้ที่คำนวณสำเร็จ");
    expect(vm.countsLabel.detected).toBe("ต้นไม้ที่ตรวจพบ");
    expect(vm.countsLabel.excluded).toBe("ไม่รวมผล");
  });

  it("does not invent zero when diagnostics are absent", () => {
    const vm = toResultViewModel(LEGACY_RESPONSE);

    expect(vm.counts.measured).toBe(18);
    expect(vm.counts.detected).toBeNull();
    expect(vm.counts.excluded).toBeNull();
    expect(vm.diagnosticsStatus).toBe("unavailable");
    expect(vm.excludedRows).toEqual([]);
  });

  it("distinguishes a run that excluded nothing from one that never reported", () => {
    const vm = toResultViewModel({
      ...BASE,
      summary: {
        total_trees: 18,
        total_carbon_kg: 1,
        total_co2eq_kg: 2,
        detected_trees: 18,
        measured_trees: 18,
        excluded_trees: 0,
      },
      diagnostics: { excluded_segments: [] },
    });

    expect(vm.counts.excluded).toBe(0);
    expect(vm.diagnosticsStatus).toBe("available");
  });

  it("explains each excluded segment in Thai", () => {
    const vm = toResultViewModel(RESPONSE_WITH_DIAGNOSTICS);

    expect(vm.diagnosticsStatus).toBe("available");
    expect(vm.excludedRows).toEqual([
      {
        treeId: 11,
        stage: "wood_leaf",
        reasonCode: "WOOD_EMPTY",
        reasonTh: expect.stringContaining("ไม่พบจุดลำต้น"),
      },
      {
        treeId: 17,
        stage: "qsm",
        reasonCode: "QSM_INVALID",
        reasonTh: expect.stringContaining("DBH หรือความสูง"),
      },
    ]);
  });

  it("never presents the estimate as a certified credit", () => {
    const vm = toResultViewModel(RESPONSE_WITH_DIAGNOSTICS);

    expect(vm.totalCarbonKg).toBe(25400.58);
    expect(vm.totalCo2eqKg).toBe(93135);
    expect(vm.isCertifiedCredit).toBe(false);
  });

  it("treats counts that do not reconcile as untrustworthy rather than rendering them", () => {
    const vm = toResultViewModel({
      ...BASE,
      summary: {
        total_trees: 18,
        total_carbon_kg: 1,
        total_co2eq_kg: 2,
        detected_trees: 20,
        measured_trees: 18,
        excluded_trees: 5, // 18 + 5 != 20
      },
      diagnostics: { excluded_segments: [] },
    });

    expect(vm.diagnosticsStatus).toBe("unavailable");
    expect(vm.counts.detected).toBeNull();
    expect(vm.counts.excluded).toBeNull();
  });
});

describe("reasonLabel", () => {
  it("maps only typed reason codes", () => {
    expect(reasonLabel("WOOD_EMPTY")).toContain("ไม่พบจุดลำต้น");
    expect(reasonLabel("QSM_INVALID")).toContain("DBH หรือความสูง");
  });
});
