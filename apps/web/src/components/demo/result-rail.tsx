import type { ResultViewModel } from '../../lib/result-view-model';

export interface ResultRailProps {
  view: ResultViewModel;
  modeLabel: string;
  /**
   * Whether these numbers came with something to check them against.
   *
   * `manifest-verified` means the artifact's hashes were compared to a
   * published manifest before rendering. `live-run` means the pipeline produced
   * them a moment ago and there is nothing to verify against — which is normal,
   * and not the same claim.
   *
   * The heading used to read "ผลการประเมินที่ผ่านการยืนยันความสมบูรณ์" in every
   * case. The only place this component is rendered is the live viewer, so that
   * sentence appeared exclusively on the results where it was untrue.
   */
  integrity: 'manifest-verified' | 'live-run';
}

const HEADING: Record<ResultRailProps['integrity'], string> = {
  'manifest-verified': 'ผลการประเมินที่ผ่านการยืนยันความสมบูรณ์',
  'live-run': 'ผลการประเมินจากการวิเคราะห์รอบนี้',
};

const SUBHEADING: Record<ResultRailProps['integrity'], string> = {
  'manifest-verified': 'ไฟล์ผลลัพธ์ถูกตรวจแฮชกับ manifest ที่เผยแพร่ไว้',
  'live-run': 'คำนวณสดจากไฟล์ที่อัปโหลด ยังไม่มี manifest ให้ตรวจสอบย้อนหลัง',
};

const carbon = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const co2e = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

export function ResultRail({ view, modeLabel, integrity }: ResultRailProps) {
  const diagnosticsAvailable = view.diagnosticsStatus === 'available';

  return (
    <aside className="h-full rounded-[1.25rem] border border-hairline bg-paper px-6 py-7 text-forest-ink">
      <p className="font-mono text-[0.625rem] uppercase tracking-[0.14em] text-canopy">
        Carbon summary / {modeLabel}
      </p>
      <h2 className="mt-3 font-display text-2xl font-semibold leading-tight">
        {HEADING[integrity]}
      </h2>
      <p className="mt-2 text-xs leading-relaxed text-forest-ink/70">
        {SUBHEADING[integrity]}
      </p>

      <div className="mt-5 rounded-xl bg-lichen p-[1.125rem]">
        <p className="text-xs font-medium text-deep-forest">CO₂ เทียบเท่า</p>
        <p className="mt-1 text-3xl font-semibold tabular-nums">
          {co2e.format(view.totalCo2eqKg / 1000)} tCO₂e
        </p>
        <p className="mt-2 font-mono text-[0.625rem] uppercase tracking-wide text-canopy">
          {view.counts.measured.toLocaleString()} {view.countsLabel.measured}
        </p>
      </div>

      <dl className="mt-3">
        <MetricRow
          label="คาร์บอนรวม"
          note="ผลรวมจากต้นไม้ที่คำนวณสำเร็จ"
          value={`${carbon.format(view.totalCarbonKg)} kg`}
        />
        <MetricRow
          label={view.countsLabel.measured}
          note="ต้นไม้ที่ผ่านการประเมินโครงสร้างทางเรขาคณิตสำเร็จ"
          value={`${view.counts.measured.toLocaleString()} ต้น`}
        />
        {diagnosticsAvailable ? (
          <>
            <MetricRow
              label={view.countsLabel.detected}
              note="จำนวนต้นไม้ทั้งหมดที่ระบบจำแนกได้จาก Point Cloud"
              value={`${view.counts.detected?.toLocaleString()} ต้น`}
            />
            {/* The supplied line said these fail a density threshold. There is
                no density threshold in the pipeline - a segment is excluded
                when the wood points come back empty or the QSM fit is invalid,
                which is what the per-tree reason underneath already says. This
                keeps the writer's sentence and its actual cause. */}
            <MetricRow
              label={view.countsLabel.excluded}
              note="ข้อมูลที่วัดค่า DBH หรือความสูงไม่สำเร็จ และไม่ถูกนำไปคำนวณยอดคาร์บอนสุทธิ"
              value={`${view.counts.excluded?.toLocaleString()} ต้น`}
            />
          </>
        ) : (
          <div
            data-result-metric=""
            aria-label="Diagnostics — diagnostics unavailable"
            className="flex items-start justify-between gap-4 border-t border-hairline py-3"
          >
            <dt className="text-sm text-deep-forest">Diagnostics</dt>
            <dd className="max-w-[13rem] text-right">
              <span className="block font-mono text-[0.625rem] uppercase tracking-[0.12em] text-deep-forest">
                diagnostics unavailable
              </span>
              <span className="mt-1 block text-xs leading-relaxed text-canopy">
                ผลรุ่นนี้ไม่มีข้อมูลพอที่จะยืนยันจำนวนที่ตรวจพบหรือไม่รวมผล
              </span>
            </dd>
          </div>
        )}
      </dl>

      {diagnosticsAvailable && view.excludedRows.length > 0 ? (
        <div className="mt-2 rounded-xl border border-evidence-amber bg-gallery-ivory p-3.5">
          <p className="text-sm font-medium text-deep-forest">
            เหตุผลที่ไม่รวมผล {view.excludedRows.length.toLocaleString()} ต้น
          </p>
          <ul className="mt-1.5 space-y-1 text-xs leading-relaxed text-deep-forest">
            {view.excludedRows.map((row) => (
              <li key={`${row.treeId}-${row.reasonCode}`}>
                ต้นที่ {row.treeId}: {row.reasonTh}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="mt-4 border-t border-hairline pt-4 text-xs leading-relaxed text-canopy">
        ค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง
      </p>
    </aside>
  );
}

function MetricRow({ label, note, value }: { label: string; note: string; value: string }) {
  return (
    <div
      data-result-metric=""
      aria-label={`${label} — ${value}`}
      className="flex items-center justify-between gap-4 border-t border-hairline py-3"
    >
      <dt className="text-sm text-deep-forest">
        <span className="block">{label}</span>
        <span className="block font-mono text-[0.5625rem] uppercase tracking-wide text-canopy">
          {note}
        </span>
      </dt>
      <dd className="shrink-0 text-sm font-semibold tabular-nums">{value}</dd>
    </div>
  );
}
