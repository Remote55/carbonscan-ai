import { Upload } from 'lucide-react';

import {
  DEMO_ALLOWED_EXTENSIONS,
  DEMO_MAX_POINTS,
  DEMO_MAX_UPLOAD_BYTES,
  type UploadState,
} from '../../lib/demo-upload';

const megabytes = new Intl.NumberFormat('th-TH', { maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat('en-US');

function formatSize(bytes: number): string {
  return `${megabytes.format(bytes / (1024 * 1024))} MB`;
}

function selectedFile(state: UploadState) {
  return 'file' in state ? state.file : null;
}

export function UploadDropzone({
  state,
  onSelect,
}: {
  state: UploadState;
  onSelect: (file: File) => void;
}) {
  const busy = state.kind === 'uploading' || state.kind === 'processing';
  const file = selectedFile(state);
  const contract = `${DEMO_ALLOWED_EXTENSIONS.join(' · ')} · ${Math.round(
    DEMO_MAX_UPLOAD_BYTES / (1024 * 1024),
  )} MB · ${integer.format(DEMO_MAX_POINTS)} จุด`;

  return (
    <div
      className="rounded-2xl border border-dashed border-hairline bg-paper p-6 text-center sm:p-8"
      aria-live="polite"
    >
      <label
        className={`focus-within:ring-2 focus-within:ring-moss focus-within:ring-offset-2 focus-within:ring-offset-paper ${
          busy ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
        } block rounded-xl`}
      >
        <span className="mx-auto flex size-11 items-center justify-center rounded-full bg-lichen text-canopy">
          <Upload aria-hidden="true" className="size-5" />
        </span>
        <span className="mt-4 block font-display text-xl text-forest-ink">
          วางไฟล์ point cloud ที่นี่
        </span>
        <span className="mt-2 block font-mono text-[0.6875rem] text-canopy">{contract}</span>
        <span className="mt-3 block text-xs text-canopy">
          {busy ? 'กำลังทำงาน — เปลี่ยนไฟล์ไม่ได้' : 'คลิกเพื่อเลือกไฟล์'}
        </span>
        <input
          type="file"
          className="sr-only"
          accept={DEMO_ALLOWED_EXTENSIONS.join(',')}
          disabled={busy}
          onChange={(event) => {
            const picked = event.target.files?.[0];
            if (picked) onSelect(picked);
            event.target.value = '';
          }}
        />
      </label>

      {state.kind === 'idle' && <p className="mt-5 text-sm text-canopy">ยังไม่ได้เลือกไฟล์</p>}

      {state.kind === 'rejected' && (
        <p className="mt-5 rounded-xl border border-evidence-amber bg-gallery-ivory p-3 text-sm text-deep-forest">
          {state.reasonTh}
        </p>
      )}

      {file && (
        <p className="mt-5 text-sm text-canopy">
          <span className="font-mono text-xs text-forest-ink">{file.name}</span>
          <span aria-hidden="true"> · </span>
          {formatSize(file.sizeBytes)}
        </p>
      )}

      {state.kind === 'uploading' && (
        <p className="mt-2 text-sm text-canopy">กำลังอัปโหลด {state.file.name}…</p>
      )}

      {state.kind === 'processing' && (
        <p className="mt-2 text-sm text-canopy">
          กำลังประมวลผล {state.file.name} — ขั้นตอนนี้อาจใช้เวลาราวสิบวินาที
        </p>
      )}

      {state.kind === 'failed' && (
        <p className="mt-3 rounded-xl border border-clay bg-clay/10 p-3 text-sm text-clay">
          {state.messageTh}
        </p>
      )}
    </div>
  );
}
