import type { ResultViewModel } from '../../lib/result-view-model';

export interface ResultRailProps {
  view: ResultViewModel;
  modeLabel: string;
}

const carbon = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const co2e = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

export function ResultRail({ view, modeLabel }: ResultRailProps) {
  const diagnosticsAvailable = view.diagnosticsStatus === 'available';

  return (
    <aside className="h-full rounded-[1.25rem] border border-hairline bg-paper px-6 py-7 text-forest-ink">
      <p className="font-mono text-[0.625rem] uppercase tracking-[0.14em] text-moss">
        Carbon summary / {modeLabel}
      </p>
      <h2 className="mt-3 font-display text-2xl font-semibold leading-tight">
        ผลคาร์บอนจากการวิเคราะห์
      </h2>

      <div className="mt-5 rounded-[0.875rem] bg-lichen p-[1.125rem]">
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
          note="Measured"
          value={`${view.counts.measured.toLocaleString()} ต้น`}
        />
        {diagnosticsAvailable ? (
          <>
            <MetricRow
              label={view.countsLabel.detected}
              note="Detected"
              value={`${view.counts.detected?.toLocaleString()} ต้น`}
            />
            <MetricRow
              label={view.countsLabel.excluded}
              note="Excluded from carbon total"
              value={`${view.counts.excluded?.toLocaleString()} ต้น`}
            />
          </>
        ) : (
          <div className="border-t border-hairline py-3">
            <p className="font-mono text-[0.625rem] uppercase tracking-[0.12em] text-evidence-amber">
              diagnostics unavailable
            </p>
            <p className="mt-1 text-xs leading-relaxed text-canopy">
              ผลรุ่นนี้ไม่มีข้อมูลพอที่จะยืนยันจำนวนที่ตรวจพบหรือไม่รวมผล
            </p>
          </div>
        )}
      </dl>

      {diagnosticsAvailable && view.excludedRows.length > 0 ? (
        <div className="mt-2 rounded-xl border border-evidence-amber bg-gallery-ivory p-3.5">
          <p className="text-sm font-medium text-evidence-amber">
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
    <div className="flex items-center justify-between gap-4 border-t border-hairline py-3">
      <div>
        <dt className="text-sm text-deep-forest">{label}</dt>
        <p className="font-mono text-[0.5625rem] uppercase tracking-wide text-moss">{note}</p>
      </div>
      <dd className="shrink-0 text-sm font-semibold tabular-nums">{value}</dd>
    </div>
  );
}
