import type { ReactNode } from 'react';

import { PointCloudLegend } from './point-cloud-legend';
import { PointCloudViewer, type PointCloudViewerProps } from './point-cloud-viewer';

export type ViewerStageProps = PointCloudViewerProps & {
  title: string;
  evidenceLabel: string;
  /** Has the pipeline run on this cloud? Only changes what the note says. */
  analysed?: boolean;
  children?: ReactNode;
};

export function ViewerStage({
  title,
  evidenceLabel,
  analysed = false,
  children,
  positions,
  classes,
  labelled,
  pointSize,
  className,
}: ViewerStageProps) {
  return (
    <section
      className={`overflow-hidden rounded-[1.75rem] bg-forest-ink text-paper shadow-[0_22px_58px_-18px_rgba(14,42,29,0.22)] ${className ?? ''}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4 px-5 pb-4 pt-5 sm:px-6">
        <div className="min-w-0">
          {/* Thai, and therefore not font-mono: the mono face carries no Thai
              glyphs, so it would fall back silently and render a size smaller
              than everything around it. */}
          <p className="editorial-eyebrow-th text-lichen">{evidenceLabel}</p>
          <h2 className="mt-1 truncate text-sm font-medium text-paper">{title}</h2>
        </div>
        {children}
      </div>

      <PointCloudViewer
        positions={positions}
        classes={classes}
        labelled={labelled}
        pointSize={pointSize}
        className="border-lichen/15 h-[30rem] w-full border-y lg:h-[40rem]"
      />

      <div className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        {/* The legend names three classes. Showing it over a raw scan would
            advertise a separation that has not been computed. The two notes
            below are split because the honest answer changes once the pipeline
            has run: the separation does happen, but /upload/analyze returns
            metadata, summary and trees - no point cloud - so this picture is
            still the file the browser parsed and cannot be recoloured from the
            result. Saying "press analyse and it will colour in" was a promise
            the API cannot keep. */}
        {labelled ? (
          <PointCloudLegend />
        ) : analysed ? (
          <p className="max-w-2xl text-xs leading-relaxed text-lichen">
            ระบบแยกลำต้นกับใบไปแล้วในขั้นตอนคำนวณ — ผลอยู่ในตัวเลขทางขวา
            ส่วนภาพนี้ยังเป็นไฟล์ที่เบราว์เซอร์อ่านตอนคุณเปิด จึงยังเป็นสีเดียว
          </p>
        ) : (
          <p className="max-w-2xl text-xs leading-relaxed text-lichen">
            ไฟล์นี้เก็บเฉพาะพิกัด ยังไม่มีข้อมูลแยกลำต้น ใบ และพื้นดิน จึงแสดงเป็นสีเดียว —
            กด <span className="font-semibold text-paper">วิเคราะห์คาร์บอน</span>{' '}
            เพื่อให้ระบบแยกและคำนวณ ผลจะออกมาเป็นตัวเลข
          </p>
        )}
        <p className="font-mono text-[0.625rem] uppercase tracking-[0.1em] text-lichen">
          Drag: orbit · Wheel: zoom · Right drag: pan
        </p>
      </div>
    </section>
  );
}
