import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import type { UploadState } from '../../lib/demo-upload';
import { compositeOver, contrastRatio, tokenHex } from '../../test-support/wcag';
import { UploadDropzone } from './upload-dropzone';

const file = { name: 'plot.ply', sizeBytes: 1_741_642 };

function render(state: UploadState): string {
  return renderToStaticMarkup(<UploadDropzone state={state} onSelect={() => undefined} />);
}

describe('UploadDropzone', () => {
  it('states the contract the API actually enforces, and never offers LAS or LAZ', () => {
    const markup = render({ kind: 'idle' });

    expect(markup).toContain('.ply');
    expect(markup).toContain('100 MB');
    expect(markup).toContain('2,000,000 จุด');
    expect(markup).not.toContain('.las');
    expect(markup).not.toContain('.laz');
  });

  it('keeps the chosen filename on screen while the run is in flight', () => {
    for (const state of [
      { kind: 'uploading', file } as const,
      { kind: 'processing', file } as const,
    ]) {
      const markup = render(state);
      expect(markup).toContain('plot.ply');
    }
  });

  it('disables the input while a run is in flight so the file cannot be swapped', () => {
    expect(render({ kind: 'processing', file })).toContain('disabled');
    expect(render({ kind: 'idle' })).not.toContain('disabled');
  });

  // The failure message is the one piece of copy that only ever appears when
  // something has already gone wrong, so it is the worst place for unreadable
  // text. It renders on a bg-clay/10 tint, and Tailwind composites that in sRGB:
  // contrast has to be measured against the resulting surface, not against
  // either token on its own. Measured that way the original pairing was 4.10:1.
  it('keeps the failure message at AA against the tint it renders on', () => {
    const markup = render({ kind: 'failed', file, messageTh: 'ติดต่อบริการวิเคราะห์ไม่ได้' });

    const error = markup.match(/<p class="[^"]*bg-clay\/10[^"]*"[^>]*>[^<]*<\/p>/)?.[0];
    expect(error).toBeDefined();

    const clay = tokenHex('clay');
    const surface = compositeOver(clay, tokenHex('paper'), 0.1);
    expect(contrastRatio(clay, surface)).toBeGreaterThanOrEqual(4.5);
  });

  it('explains a rejected file on a surface that stays readable', () => {
    const markup = render({ kind: 'rejected', reasonTh: 'โหมดเดโมรับเฉพาะไฟล์ .ply เท่านั้น' });

    expect(markup).toContain('โหมดเดโมรับเฉพาะไฟล์ .ply เท่านั้น');
    expect(
      contrastRatio(tokenHex('deep-forest'), tokenHex('gallery-ivory')),
    ).toBeGreaterThanOrEqual(4.5);
  });
});
