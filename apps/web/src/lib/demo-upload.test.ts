import { describe, expect, it } from 'vitest';

import {
  DEMO_MAX_UPLOAD_BYTES,
  checkSelection,
  uploadReducer,
  type UploadState,
} from './demo-upload';
import type { ResultForView } from './result-view-model';

const file = { name: 'plot.ply', sizeBytes: 2048 };

const result: ResultForView = {
  summary: { total_trees: 3, total_carbon_kg: 120, total_co2eq_kg: 440 },
};

describe('checkSelection', () => {
  it('accepts PLY in any case', () => {
    for (const name of ['plot.ply', 'PLOT.PLY', 'a.b.Ply']) {
      expect(checkSelection(name, 2048).kind).toBe('accepted');
    }
  });

  it('rejects an extension the pipeline cannot read', () => {
    const check = checkSelection('photo.jpg', 2048);
    expect(check.kind).toBe('rejected');
    if (check.kind === 'rejected') expect(check.reasonTh).toContain('.ply');
  });

  // The platform reads LAS/LAZ, but validate_upload refuses them while
  // TREEQ_DEMO_MODE is on. Offering them here would let a judge pick a file the
  // API answers 400 to, which is worse than not offering them at all.
  it('rejects LAS and LAZ, which demo mode refuses even though the pipeline reads them', () => {
    expect(checkSelection('plot.las', 2048).kind).toBe('rejected');
    expect(checkSelection('plot.laz', 2048).kind).toBe('rejected');
  });

  it('rejects a file at one byte over the server limit, and accepts it at the limit', () => {
    expect(checkSelection('plot.ply', DEMO_MAX_UPLOAD_BYTES).kind).toBe('accepted');
    expect(checkSelection('plot.ply', DEMO_MAX_UPLOAD_BYTES + 1).kind).toBe('rejected');
  });

  it('rejects an empty file rather than uploading nothing', () => {
    expect(checkSelection('plot.ply', 0).kind).toBe('rejected');
  });
});

describe('uploadReducer', () => {
  it('walks a successful run from selection to result', () => {
    let state: UploadState = { kind: 'idle' };
    state = uploadReducer(state, { type: 'SELECT', ...file });
    expect(state.kind).toBe('ready');
    state = uploadReducer(state, { type: 'START' });
    expect(state.kind).toBe('uploading');
    state = uploadReducer(state, { type: 'PHASE', phase: 'processing' });
    expect(state.kind).toBe('processing');
    state = uploadReducer(state, { type: 'SUCCEEDED', result });
    expect(state).toEqual({ kind: 'complete', file, result });
  });

  it('ignores a second file picked while a run is in flight', () => {
    const running: UploadState = { kind: 'processing', file };
    const next = uploadReducer(running, {
      type: 'SELECT',
      name: 'other.ply',
      sizeBytes: 4096,
    });
    expect(next).toBe(running);
  });

  it('drops a reply that arrives after the screen was reset', () => {
    const reset = uploadReducer({ kind: 'processing', file }, { type: 'RESET' });
    expect(uploadReducer(reset, { type: 'SUCCEEDED', result })).toEqual({ kind: 'idle' });
    expect(uploadReducer(reset, { type: 'FAILED', messageTh: 'พัง' })).toEqual({ kind: 'idle' });
  });

  it('will not start a run before a file is accepted', () => {
    const rejected = uploadReducer(
      { kind: 'idle' },
      { type: 'SELECT', name: 'photo.jpg', sizeBytes: 10 },
    );
    expect(rejected.kind).toBe('rejected');
    expect(uploadReducer(rejected, { type: 'START' })).toBe(rejected);
  });

  it('keeps the failed file on screen so the judge knows which one failed', () => {
    const failed = uploadReducer(
      { kind: 'processing', file },
      { type: 'FAILED', messageTh: 'บริการวิเคราะห์ไม่พร้อมใช้งาน' },
    );
    expect(failed).toEqual({
      kind: 'failed',
      file,
      messageTh: 'บริการวิเคราะห์ไม่พร้อมใช้งาน',
    });
  });
});
