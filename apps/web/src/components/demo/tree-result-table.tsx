/**
 * Per-tree results, with the excluded segments in the same table.
 *
 * Keeping them together is the point: the measured rows alone have gaps in the
 * tree ids, and a judge reading `2, 3, 5` cannot tell whether 1 and 4 failed,
 * were never detected, or were quietly discarded. Listing them inline answers
 * that without anyone having to ask.
 */
import type { ResultViewModel } from '../../lib/result-view-model';

const decimal = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function TreeResultTable({ view }: { view: ResultViewModel }) {
  const rows = [
    ...view.measuredRows.map((row) => ({ kind: 'measured' as const, treeId: row.treeId, row })),
    ...view.excludedRows.map((row) => ({ kind: 'excluded' as const, treeId: row.treeId, row })),
  ].sort((a, b) => a.treeId - b.treeId);

  if (rows.length === 0) {
    return <p className="text-sm text-canopy">ยังไม่มีผลรายต้น</p>;
  }

  return (
    <div className="max-w-full overflow-x-auto overscroll-x-contain">
      <table className="w-full min-w-[44rem] border-collapse text-sm">
        <caption className="sr-only">ผลการวัดรายต้น รวมต้นที่ไม่รวมผล</caption>
        <thead>
          <tr className="border-b border-hairline bg-gallery-ivory text-left font-mono text-[0.6875rem] uppercase tracking-wide text-canopy">
            <th scope="col" className="px-3 py-3 font-medium">
              ต้นที่
            </th>
            <th scope="col" className="px-3 py-3 font-medium">
              DBH (ซม.)
            </th>
            <th scope="col" className="px-3 py-3 font-medium">
              ความสูง (ม.)
            </th>
            <th scope="col" className="px-3 py-3 font-medium">
              คาร์บอน (กก.)
            </th>
            <th scope="col" className="px-3 py-3 font-medium">
              CO₂e (กก.)
            </th>
            <th scope="col" className="px-3 py-3 font-medium">
              สถานะ
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((entry) =>
            entry.kind === 'measured' ? (
              <tr key={`m-${entry.treeId}`} className="border-b border-hairline">
                <th scope="row" className="px-3 py-3 text-left font-mono font-normal text-canopy">
                  {entry.treeId}
                </th>
                <td className="px-3 py-3 tabular-nums">{decimal.format(entry.row.dbhCm)}</td>
                <td className="px-3 py-3 tabular-nums">{decimal.format(entry.row.heightM)}</td>
                <td className="px-3 py-3 tabular-nums">{decimal.format(entry.row.carbonKg)}</td>
                <td className="px-3 py-3 tabular-nums">{decimal.format(entry.row.co2eqKg)}</td>
                <td className="px-3 py-3 font-mono text-[0.6875rem] font-medium tracking-wide text-canopy">
                  READY
                </td>
              </tr>
            ) : (
              <tr
                key={`x-${entry.treeId}`}
                className="border-b border-evidence-amber bg-gallery-ivory"
              >
                <th scope="row" className="px-3 py-3 text-left font-mono font-normal text-canopy">
                  {entry.treeId}
                </th>
                <td className="px-3 py-3 text-canopy">—</td>
                <td className="px-3 py-3 text-canopy">—</td>
                <td className="px-3 py-3 text-canopy">—</td>
                <td className="px-3 py-3 text-canopy">—</td>
                {/* Red and bold, at the designer's request: this is the one status
                    a judge must not skim past, and the muted terracotta read as
                    decoration next to READY. The cell also used to carry three
                    type sizes - a 10px badge, a 12px reason, and the row's own 14px
                    - so the column looked accidental. Now it is two, and they mean
                    something: 11px mono for the label, body size for the prose. */}
                <td className="px-3 py-3 text-deep-forest">
                  <span className="block font-mono text-[0.6875rem] font-bold tracking-wide text-ember">
                    EXCLUDED
                  </span>
                  <span className="mt-1 block text-sm leading-6">
                    ไม่รวมผล — {entry.row.reasonTh}
                  </span>
                </td>
              </tr>
            ),
          )}
        </tbody>
      </table>
    </div>
  );
}
