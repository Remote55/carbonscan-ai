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
    return <p className="text-sm text-slate-600">ยังไม่มีผลรายต้น</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[36rem] border-collapse text-sm">
        <caption className="sr-only">ผลการวัดรายต้น รวมต้นที่ไม่รวมผล</caption>
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
            <th scope="col" className="py-2 pr-4 font-medium">ต้นที่</th>
            <th scope="col" className="py-2 pr-4 font-medium">DBH (ซม.)</th>
            <th scope="col" className="py-2 pr-4 font-medium">ความสูง (ม.)</th>
            <th scope="col" className="py-2 pr-4 font-medium">คาร์บอน (กก.)</th>
            <th scope="col" className="py-2 font-medium">CO₂e (กก.)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((entry) =>
            entry.kind === 'measured' ? (
              <tr key={`m-${entry.treeId}`} className="border-b border-slate-100">
                <th scope="row" className="py-2 pr-4 text-left font-mono font-normal text-slate-500">
                  {entry.treeId}
                </th>
                <td className="py-2 pr-4 tabular-nums">{decimal.format(entry.row.dbhCm)}</td>
                <td className="py-2 pr-4 tabular-nums">{decimal.format(entry.row.heightM)}</td>
                <td className="py-2 pr-4 tabular-nums">{decimal.format(entry.row.carbonKg)}</td>
                <td className="py-2 tabular-nums">{decimal.format(entry.row.co2eqKg)}</td>
              </tr>
            ) : (
              <tr key={`x-${entry.treeId}`} className="border-b border-slate-100 bg-amber-50/60">
                <th scope="row" className="py-2 pr-4 text-left font-mono font-normal text-slate-500">
                  {entry.treeId}
                </th>
                <td className="py-2 text-amber-900" colSpan={4}>
                  ไม่รวมผล — {entry.row.reasonTh}
                </td>
              </tr>
            ),
          )}
        </tbody>
      </table>
    </div>
  );
}
