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

describe("measured rows", () => {
  it("exposes one row per measured tree, keeping the pipeline's own ids", () => {
    const vm = toResultViewModel({
      ...RESPONSE_WITH_DIAGNOSTICS,
      trees: [
        { tree_id: 2, dbh_cm: 33.62, height_m: 18.4, carbon_kg: 484.15, co2eq_kg: 1775.9 },
        { tree_id: 3, dbh_cm: 23.83, height_m: 14.1, carbon_kg: 197.3, co2eq_kg: 723.8 },
        { tree_id: 5, dbh_cm: 40.52, height_m: 21.7, carbon_kg: 608.29, co2eq_kg: 2231.7 },
      ],
    });

    expect(vm.measuredRows.map((row) => row.treeId)).toEqual([2, 3, 5]);
    expect(vm.measuredRows[0]).toEqual({
      treeId: 2,
      dbhCm: 33.62,
      heightM: 18.4,
      carbonKg: 484.15,
      co2eqKg: 1775.9,
      // Null rather than absent: a result stored by an older pipeline carries
      // none of these, and a row must not imply a quality nobody reported.
      dbhFitQuality: null,
      co2eqVolumeRouteKg: null,
      methodDisagreement: null,
    });
  });

  it("carries the fit quality and the second estimate when the pipeline reports them", () => {
    const vm = toResultViewModel({
      ...RESPONSE_WITH_DIAGNOSTICS,
      trees: [
        {
          tree_id: 2,
          dbh_cm: 33.62,
          height_m: 18.4,
          carbon_kg: 484.15,
          co2eq_kg: 1775.9,
          dbh_fit_quality: 0.42,
          co2eq_volume_route_kg: 1540.2,
          method_disagreement: 0.1327,
        },
      ],
    });

    expect(vm.measuredRows[0].dbhFitQuality).toBe(0.42);
    expect(vm.measuredRows[0].co2eqVolumeRouteKg).toBe(1540.2);
    expect(vm.measuredRows[0].methodDisagreement).toBe(0.1327);
  });

  it("keeps the ids that are missing visible through the excluded rows", () => {
    const vm = toResultViewModel({
      ...RESPONSE_WITH_DIAGNOSTICS,
      trees: [{ tree_id: 2, dbh_cm: 1, height_m: 1, carbon_kg: 1, co2eq_kg: 1 }],
    });

    // A judge asking "why does it jump?" must be able to read the answer off
    // the same result, not infer it from a gap.
    expect(vm.measuredRows.map((row) => row.treeId)).toEqual([2]);
    expect(vm.excludedRows.map((row) => row.treeId)).toEqual([11, 17]);
  });

  it("has no rows when the run reported no trees", () => {
    expect(toResultViewModel(LEGACY_RESPONSE).measuredRows).toEqual([]);
  });
});

describe("reasonLabel", () => {
  it("maps only typed reason codes", () => {
    expect(reasonLabel("WOOD_EMPTY")).toContain("ไม่พบจุดลำต้น");
    expect(reasonLabel("QSM_INVALID")).toContain("DBH หรือความสูง");
  });
});
