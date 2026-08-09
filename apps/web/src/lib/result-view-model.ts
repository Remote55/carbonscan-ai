/**
 * Adapts a pipeline result into exactly what the workspace is allowed to show.
 *
 * The pipeline reports three counts and, since 0.4.0, why each detected segment
 * produced no measurement. Two failure modes matter here and both are silent if
 * you map the response straight onto the UI:
 *
 *  1. `summary.total_trees` is the *measured* count. Labelling it "detected"
 *     hides every excluded segment and makes a gap in tree IDs unexplainable.
 *  2. A result stored before 0.4.0 has no counts at all. Rendering the missing
 *     values as `0` would claim it excluded nothing, which it never reported.
 *
 * So detected/excluded stay `null` when absent, and the workspace shows
 * "diagnostics unavailable" rather than a number nobody computed.
 */
import type { AnalyzeExcludedSegment, ExcludedReasonCode } from './api';

/**
 * Only the parts of a result this adapter reads. Keeping it structural lets the
 * frozen bundle and a live API response share one workspace without the frozen
 * type having to carry metadata the workspace never renders.
 */
export interface ResultForView {
  summary: {
    total_trees: number;
    total_carbon_kg: number;
    total_co2eq_kg: number;
    detected_trees?: number | null;
    measured_trees?: number | null;
    excluded_trees?: number | null;
  };
  diagnostics?: { excluded_segments?: AnalyzeExcludedSegment[] } | null;
  trees?: Array<{
    tree_id: number;
    dbh_cm: number;
    height_m: number;
    carbon_kg?: number | null;
    co2eq_kg?: number | null;
  }>;
}

const REASON_LABELS_TH: Record<ExcludedReasonCode, string> = {
  WOOD_EMPTY: 'ไม่พบจุดลำต้นหลังแยกลำต้น–ใบ จึงวัดขนาดไม่ได้',
  QSM_INVALID: 'ไม่สามารถประเมินค่า DBH หรือความสูงได้',
  QSM_LOW_FIT_QUALITY: 'วงกลมที่ฟิตกับลำต้นไม่แนบพอ ค่า DBH ที่ได้จึงไม่น่าเชื่อถือ',
};

const COUNT_LABELS_TH = {
  detected: 'ต้นไม้ที่ตรวจพบ',
  measured: 'ต้นไม้ที่คำนวณสำเร็จ',
  excluded: 'ไม่รวมผล',
} as const;

/** Thai explanation for a reason code the pipeline actually emitted. */
export function reasonLabel(code: ExcludedReasonCode): string {
  return REASON_LABELS_TH[code];
}

export interface ExcludedRow {
  treeId: number;
  stage: 'wood_leaf' | 'qsm';
  reasonCode: ExcludedReasonCode;
  reasonTh: string;
}

export interface MeasuredRow {
  treeId: number;
  dbhCm: number;
  heightM: number;
  carbonKg: number;
  co2eqKg: number;
}

export interface ResultViewModel {
  counts: { detected: number | null; measured: number; excluded: number | null };
  countsLabel: typeof COUNT_LABELS_TH;
  diagnosticsStatus: 'available' | 'unavailable';
  measuredRows: MeasuredRow[];
  excludedRows: ExcludedRow[];
  totalCarbonKg: number;
  totalCo2eqKg: number;
  /** A biomass estimate is never a certified or tradable credit. */
  isCertifiedCredit: false;
}

export function toResultViewModel(response: ResultForView): ResultViewModel {
  const summary = response.summary;
  const measured = summary.measured_trees ?? summary.total_trees;
  const detected = summary.detected_trees ?? null;
  const excluded = summary.excluded_trees ?? null;
  const segments = response.diagnostics?.excluded_segments ?? null;
  const measuredRows: MeasuredRow[] = (response.trees ?? []).map((tree) => ({
    treeId: tree.tree_id,
    dbhCm: tree.dbh_cm,
    heightM: tree.height_m,
    carbonKg: tree.carbon_kg ?? 0,
    co2eqKg: tree.co2eq_kg ?? 0,
  }));

  // Trust the counts only when the run reported all three, they reconcile, and
  // the segment list matches the excluded count. Anything else is a contract
  // the UI cannot explain, so it reports "unavailable" instead of guessing.
  const reconciles =
    detected !== null &&
    excluded !== null &&
    segments !== null &&
    detected === measured + excluded &&
    segments.length === excluded;

  if (!reconciles) {
    return {
      counts: { detected: null, measured, excluded: null },
      countsLabel: COUNT_LABELS_TH,
      diagnosticsStatus: 'unavailable',
      measuredRows,
      excludedRows: [],
      totalCarbonKg: summary.total_carbon_kg,
      totalCo2eqKg: summary.total_co2eq_kg,
      isCertifiedCredit: false,
    };
  }

  return {
    counts: { detected, measured, excluded },
    countsLabel: COUNT_LABELS_TH,
    diagnosticsStatus: 'available',
    measuredRows,
    excludedRows: segments.map((segment) => ({
      treeId: segment.tree_id,
      stage: segment.stage,
      reasonCode: segment.reason_code,
      reasonTh: reasonLabel(segment.reason_code),
    })),
    totalCarbonKg: summary.total_carbon_kg,
    totalCo2eqKg: summary.total_co2eq_kg,
    isCertifiedCredit: false,
  };
}
