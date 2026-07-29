/**
 * The live-upload state machine for the judge demo.
 *
 * This is the demo's most failure-prone moment: a judge picks an unknown file
 * while three people watch. Keeping the decisions in a reducer means every
 * branch is reachable from a test, instead of living in conditionals scattered
 * across an effect where only the happy path ever runs.
 *
 * Three rules the UI must not break, all encoded here rather than in the view:
 *
 *  1. The limits are the server's, and the server's demo limits are narrower
 *     than the platform's. `validate_upload` accepts six formats in general but
 *     rejects everything except PLY once `TREEQ_DEMO_MODE` is on, so offering
 *     `.las` here would hand the judge a file the API answers 400 to. The size
 *     limit is `TREEQ_DEMO_MAX_UPLOAD_SIZE_MB`, not the 500 MB general one.
 *  2. A run in flight cannot be replaced. A second file picked mid-analysis is
 *     ignored, so a double click cannot leave the screen describing one file
 *     while the request carries another.
 *  3. A late reply cannot repaint a screen that moved on. After a reset the
 *     previous request may still resolve; its result is dropped instead of
 *     appearing under whatever the judge is looking at now.
 */
import type { ResultForView } from './result-view-model';

/** Mirrors `TREEQ_DEMO_MAX_UPLOAD_SIZE_MB` in the API's demo settings. */
export const DEMO_MAX_UPLOAD_BYTES = 100 * 1024 * 1024;

/**
 * What `validate_upload` allows while `TREEQ_DEMO_MODE` is on. Deliberately not
 * `ANALYZE_EXTENSIONS`: demo mode narrows the platform's six formats to PLY
 * alone, because that is the only one the header validator can bound before the
 * pipeline reads it.
 */
export const DEMO_ALLOWED_EXTENSIONS = ['.ply'] as const;

/** Mirrors `TREEQ_DEMO_MAX_POINTS`; the API reads it from the PLY header. */
export const DEMO_MAX_POINTS = 2_000_000;

export interface SelectedFile {
  name: string;
  sizeBytes: number;
}

export type UploadPhase = 'uploading' | 'processing';

export type UploadState =
  | { kind: 'idle' }
  | { kind: 'rejected'; reasonTh: string }
  | { kind: 'ready'; file: SelectedFile }
  | { kind: 'uploading'; file: SelectedFile }
  | { kind: 'processing'; file: SelectedFile }
  | { kind: 'complete'; file: SelectedFile; result: ResultForView }
  | { kind: 'failed'; file: SelectedFile; messageTh: string };

export type UploadEvent =
  | { type: 'SELECT'; name: string; sizeBytes: number }
  | { type: 'START' }
  | { type: 'PHASE'; phase: UploadPhase }
  | { type: 'SUCCEEDED'; result: ResultForView }
  | { type: 'FAILED'; messageTh: string }
  | { type: 'RESET' };

function extensionOf(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot === -1 ? '' : name.slice(dot).toLowerCase();
}

function formatMegabytes(bytes: number): string {
  return String(Math.round(bytes / (1024 * 1024)));
}

export type SelectionCheck =
  | { kind: 'accepted'; file: SelectedFile }
  | { kind: 'rejected'; reasonTh: string };

/** Decides whether a picked file is one the demo API would accept. */
export function checkSelection(name: string, sizeBytes: number): SelectionCheck {
  const extension = extensionOf(name);
  if (!DEMO_ALLOWED_EXTENSIONS.includes(extension as (typeof DEMO_ALLOWED_EXTENSIONS)[number])) {
    return {
      kind: 'rejected',
      reasonTh: 'โหมดเดโมรับเฉพาะไฟล์ .ply เท่านั้น',
    };
  }
  if (sizeBytes <= 0) {
    return { kind: 'rejected', reasonTh: 'ไฟล์นี้ว่าง จึงไม่มีจุดให้ประมวลผล' };
  }
  if (sizeBytes > DEMO_MAX_UPLOAD_BYTES) {
    return {
      kind: 'rejected',
      reasonTh: `ไฟล์ใหญ่เกิน ${formatMegabytes(DEMO_MAX_UPLOAD_BYTES)} MB ที่เซิร์ฟเวอร์เดโมรับได้`,
    };
  }
  return { kind: 'accepted', file: { name, sizeBytes } };
}

type InFlightState = Extract<UploadState, { kind: 'uploading' | 'processing' }>;

/** A type predicate, so the branches below keep the file the run started with. */
function inFlight(state: UploadState): state is InFlightState {
  return state.kind === 'uploading' || state.kind === 'processing';
}

export function uploadReducer(state: UploadState, event: UploadEvent): UploadState {
  switch (event.type) {
    case 'RESET':
      return { kind: 'idle' };

    case 'SELECT': {
      // Rule 2: a run already in flight owns the screen until it settles.
      if (inFlight(state)) return state;
      const check = checkSelection(event.name, event.sizeBytes);
      return check.kind === 'accepted'
        ? { kind: 'ready', file: check.file }
        : { kind: 'rejected', reasonTh: check.reasonTh };
    }

    case 'START':
      if (state.kind !== 'ready') return state;
      return { kind: 'uploading', file: state.file };

    case 'PHASE':
      if (!inFlight(state)) return state;
      return event.phase === 'processing'
        ? { kind: 'processing', file: state.file }
        : { kind: 'uploading', file: state.file };

    case 'SUCCEEDED':
      // Rule 3: only a request this screen is still waiting for may paint.
      if (!inFlight(state)) return state;
      return { kind: 'complete', file: state.file, result: event.result };

    case 'FAILED':
      if (!inFlight(state)) return state;
      return { kind: 'failed', file: state.file, messageTh: event.messageTh };

    default:
      return state;
  }
}
