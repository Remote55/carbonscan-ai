import React from 'react';

import type { UploadState } from '../../lib/demo-upload';
import { Button } from '../ui/button';
import { UploadDropzone } from './upload-dropzone';

/**
 * The live-run control. Presentational on purpose: every decision about what may
 * happen next lives in `uploadReducer`, so this renders one state and reports
 * intent back, and a test can drive it through each branch with no DOM events.
 */
export function UploadPanel({
  state,
  onSelect,
  onStart,
  onReset,
}: {
  state: UploadState;
  onSelect: (file: File) => void;
  onStart: () => void;
  onReset: () => void;
}) {
  const busy = state.kind === 'uploading' || state.kind === 'processing';

  return (
    <section className="rounded-[1.25rem] border border-hairline bg-paper p-5 sm:p-7">
      <div className="mb-6">
        <p className="editorial-eyebrow">Live upload</p>
        <h2 className="mt-2 font-display text-2xl text-forest-ink">วิเคราะห์ไฟล์ของคุณเอง</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-canopy">
          UI ใช้ขีดจำกัดเดียวกับ demo API และคงชื่อไฟล์ไว้ตลอดการประมวลผล
        </p>
      </div>

      <UploadDropzone state={state} onSelect={onSelect} />

      <div className="mt-5 flex flex-wrap items-center gap-3">
        {state.kind === 'ready' && (
          <Button type="button" variant="editorial" size="xl" onClick={onStart}>
            เริ่มวิเคราะห์
          </Button>
        )}

        {(state.kind === 'complete' || state.kind === 'failed') && (
          <Button type="button" variant="editorialOutline" size="xl" onClick={onReset}>
            เริ่มใหม่
          </Button>
        )}

        {busy && (
          <span className="font-mono text-[0.6875rem] uppercase tracking-[0.12em] text-canopy">
            {state.kind === 'uploading' ? 'Uploading' : 'Pipeline processing'}
          </span>
        )}
      </div>
    </section>
  );
}
