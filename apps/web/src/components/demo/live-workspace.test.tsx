import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import type { RuntimeCredentials } from '../../lib/demo-runtime';
import type { ResultForView } from '../../lib/result-view-model';
import { DemoShell, uploadErrorMessageTh } from './demo-shell';
import { DemoApiError } from '../../lib/demo-api';

const credentials: RuntimeCredentials = {
  endpoint: 'http://127.0.0.1:8000',
  token: 'a'.repeat(64),
};

const liveMode = {
  kind: 'local-live' as const,
  credentials,
  pipelineVersion: '0.4.0',
};

const file = { name: 'plot.ply', sizeBytes: 4096 };

const liveResult: ResultForView = {
  summary: {
    total_trees: 3,
    total_carbon_kg: 1289.74,
    total_co2eq_kg: 4729.06,
    detected_trees: 5,
    measured_trees: 3,
    excluded_trees: 2,
  },
  diagnostics: {
    excluded_segments: [
      { tree_id: 4, stage: 'wood_leaf', reason_code: 'WOOD_EMPTY' },
      { tree_id: 5, stage: 'qsm', reason_code: 'QSM_INVALID' },
    ],
  },
  trees: [
    { tree_id: 1, dbh_cm: 30.1, height_m: 18.2, carbon_kg: 500, co2eq_kg: 1834 },
    { tree_id: 2, dbh_cm: 25.4, height_m: 15.8, carbon_kg: 400, co2eq_kg: 1467 },
    { tree_id: 3, dbh_cm: 22.0, height_m: 14.1, carbon_kg: 389.74, co2eq_kg: 1428.06 },
  ],
};

function renderLive(upload: Parameters<typeof DemoShell>[0]['upload']) {
  return renderToStaticMarkup(
    <DemoShell
      mode={liveMode}
      frozenLoad={{ kind: 'loading' }}
      upload={upload}
      onUseFrozen={() => undefined}
    />,
  );
}

describe('DemoShell live mode', () => {
  it('offers a live run instead of promising one in a later stage', () => {
    const markup = renderLive({ kind: 'idle' });
    expect(markup).toContain('วิเคราะห์ไฟล์ของคุณเอง');
    expect(markup).toContain('0.4.0');
    expect(markup).not.toContain('next demo stage');
  });

  it('states the demo accepts only PLY, matching what the API enforces', () => {
    const markup = renderLive({ kind: 'idle' });
    expect(markup).toContain('.ply · 100 MB · 2,000,000 จุด');
    expect(markup).not.toContain('.las');
    expect(markup).not.toContain('.laz');
  });

  it('names the file being processed so a slow run is not mistaken for a hang', () => {
    const markup = renderLive({ kind: 'processing', file });
    expect(markup).toContain('กำลังประมวลผล');
    expect(markup).toContain('plot.ply');
    expect(markup).toContain('aria-live="polite"');
    expect(markup).toContain('disabled=""');
  });

  // The whole point of the frozen route is that its bytes were checked against a
  // manifest. A live run has no manifest, so if this panel ever appeared beside
  // live numbers it would lend them an authority they do not have.
  it('never shows the provenance panel beside a live result', () => {
    const markup = renderLive({ kind: 'complete', file, result: liveResult });
    expect(markup).toContain('1,289.74');
    expect(markup).not.toContain('ที่มาของผลลัพธ์');
    expect(markup).not.toContain('Commit ที่ใช้วิเคราะห์');
    expect(markup).toContain('ไม่มี manifest ให้ตรวจแฮช');
  });

  it('explains excluded trees on a live run, exactly as the frozen route does', () => {
    const markup = renderLive({ kind: 'complete', file, result: liveResult });
    expect(markup).toContain('ต้นไม้ที่ตรวจพบ');
    expect(markup).toContain('ไม่พบจุดลำต้นหลังแยกลำต้น–ใบ จึงวัดขนาดไม่ได้');
  });
});

describe('uploadErrorMessageTh', () => {
  it('tells the judge what to do about each failure the API can return', () => {
    expect(uploadErrorMessageTh(new DemoApiError(413, 'x'))).toContain('ใหญ่');
    expect(uploadErrorMessageTh(new DemoApiError(400, 'x'))).toContain('.ply');
    expect(uploadErrorMessageTh(new DemoApiError(401, 'x'))).toContain('launcher');
    expect(uploadErrorMessageTh(new DemoApiError(429, 'x'))).toContain('ถี่');
    expect(uploadErrorMessageTh(new DemoApiError(502, 'x'))).toContain('เซิร์ฟเวอร์');
    expect(uploadErrorMessageTh(new Error('offline'))).toContain('ติดต่อบริการวิเคราะห์ไม่ได้');
  });
});
