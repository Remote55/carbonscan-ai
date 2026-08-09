/**
 * Per-tree results, with the excluded segments in the same table.
 *
 * Keeping them together is the point: the measured rows alone have gaps in the
 * tree ids, and a judge reading `2, 3, 5` cannot tell whether 1 and 4 failed,
 * were never detected, or were quietly discarded. Listing them inline answers
 * that without anyone having to ask.
 */
import {
  FIT_QUALITY_UNCERTAIN,
  type MeasuredRow,
  type ResultViewModel,
} from '../../lib/result-view-model';

/**
 * What to say about one measured row beyond its numbers.
 *
 * Two things the pipeline knows and the table used to drop: how well the circle
 * fit explained the stem, and how far the second carbon model lands from the
 * first. A table where every row looks equally certain is a table that hides
 * which rows are not.
 */
function rowCaveat(row: MeasuredRow): string | null {
  const notes: string[] = [];
  if (row.dbhFitQuality !== null && row.dbhFitQuality < FIT_QUALITY_UNCERTAIN) {
    notes.push(`วงกลมที่ฟิตกับลำต้นอธิบายจุดได้ ${Math.round(row.dbhFitQuality * 100)}%`);
  }
  if (row.methodDisagreement !== null && row.methodDisagreement >= 0.2) {
    notes.push(`สองวิธีคำนวณต่างกัน ${Math.round(row.methodDisagreement * 100)}%`);
  }
  return notes.length > 0 ? notes.join(' · ') : null;
}

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
                  {rowCaveat(entry.row) ? (
                    <>
                      <span className="text-evidence-amber">CHECK</span>
                      <span className="mt-1 block font-sans text-sm font-normal normal-case tracking-normal text-forest-ink/75">
                        {rowCaveat(entry.row)}
                      </span>
                    </>
                  ) : (
                    'READY'
                  )}
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
                {/* The whole cell is red, badge and reason together, at the
                    designer's second pass: a red label above dark-green prose read as
                    two separate things, when it is one message - this tree produced no
                    measurement, and here is why. Ember clears AA on this row's own
                    Gallery Ivory background at 5.79:1, so the reason line is legible
                    at body size rather than merely coloured. */}
                <td className="px-3 py-3 text-ember">
                  <span className="block font-mono text-[0.6875rem] font-bold tracking-wide">
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
