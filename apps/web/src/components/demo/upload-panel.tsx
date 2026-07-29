import React from 'react';

import {
  DEMO_ALLOWED_EXTENSIONS,
  DEMO_MAX_POINTS,
  DEMO_MAX_UPLOAD_BYTES,
  type UploadState,
} from '../../lib/demo-upload';

const megabytes = new Intl.NumberFormat('th-TH', { maximumFractionDigits: 1 });

function formatSize(bytes: number): string {
  return `${megabytes.format(bytes / (1024 * 1024))} MB`;
}

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
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <h2 className="text-base font-semibold text-slate-900">วิเคราะห์ไฟล์ของคุณเอง</h2>
      <p className="mt-2 text-sm text-slate-600">
        รับไฟล์ {DEMO_ALLOWED_EXTENSIONS.join(' · ')} ไม่เกิน{' '}
        {Math.round(DEMO_MAX_UPLOAD_BYTES / (1024 * 1024))} MB และไม่เกิน{' '}
        {new Intl.NumberFormat('th-TH').format(DEMO_MAX_POINTS)} จุด — ตรงกับที่ API บังคับจริง
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <label
          className={`cursor-pointer rounded-full border border-emerald-900 px-5 py-2.5 text-sm font-semibold text-emerald-950 ${
            busy ? 'pointer-events-none opacity-40' : 'hover:bg-emerald-50'
          }`}
        >
          เลือกไฟล์
          <input
            type="file"
            className="sr-only"
            accept={DEMO_ALLOWED_EXTENSIONS.join(',')}
            disabled={busy}
            onChange={(event) => {
              const picked = event.target.files?.[0];
              if (picked) onSelect(picked);
              // Let the same file be picked again after a reset.
              event.target.value = '';
            }}
          />
        </label>

        {state.kind === 'ready' && (
          <button
            type="button"
            className="rounded-full bg-emerald-950 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-900"
            onClick={onStart}
          >
            เริ่มวิเคราะห์
          </button>
        )}

        {(state.kind === 'complete' || state.kind === 'failed') && (
          <button
            type="button"
            className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            onClick={onReset}
          >
            เริ่มใหม่
          </button>
        )}
      </div>

      <div className="mt-5 text-sm" aria-live="polite">
        {state.kind === 'idle' && <p className="text-slate-500">ยังไม่ได้เลือกไฟล์</p>}

        {state.kind === 'rejected' && (
          <p className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
            {state.reasonTh}
          </p>
        )}

        {state.kind === 'ready' && (
          <p className="text-slate-700">
            <span className="font-mono text-xs text-slate-500">{state.file.name}</span> ·{' '}
            {formatSize(state.file.sizeBytes)}
          </p>
        )}

        {busy && (
          <p className="text-slate-700">
            {state.kind === 'uploading'
              ? `กำลังอัปโหลด ${state.file.name}…`
              : 'อัปโหลดครบแล้ว กำลังประมวลผล point cloud — ขั้นตอนนี้ใช้เวลาราวสิบวินาที'}
          </p>
        )}

        {state.kind === 'failed' && (
          <p className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900">
            <span className="font-mono text-xs">{state.file.name}</span> — {state.messageTh}
          </p>
        )}
      </div>
    </section>
  );
}
