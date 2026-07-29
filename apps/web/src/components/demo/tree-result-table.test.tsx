import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import type { ResultViewModel } from '../../lib/result-view-model';
import { TreeResultTable } from './tree-result-table';

const view: ResultViewModel = {
  counts: { detected: 5, measured: 3, excluded: 2 },
  countsLabel: {
    detected: 'ต้นไม้ที่ตรวจพบ',
    measured: 'ต้นไม้ที่คำนวณสำเร็จ',
    excluded: 'ไม่รวมผล',
  },
  diagnosticsStatus: 'available',
  measuredRows: [
    { treeId: 2, dbhCm: 33.62, heightM: 21.35, carbonKg: 484.15, co2eqKg: 1775.21 },
    { treeId: 3, dbhCm: 23.83, heightM: 17.04, carbonKg: 197.3, co2eqKg: 723.44 },
    { treeId: 5, dbhCm: 40.52, heightM: 16.67, carbonKg: 608.29, co2eqKg: 2230.41 },
  ],
  excludedRows: [
    {
      treeId: 1,
      stage: 'qsm',
      reasonCode: 'QSM_INVALID',
      reasonTh: 'วัดค่า DBH หรือความสูงไม่สำเร็จ',
    },
    {
      treeId: 4,
      stage: 'qsm',
      reasonCode: 'QSM_INVALID',
      reasonTh: 'วัดค่า DBH หรือความสูงไม่สำเร็จ',
    },
  ],
  totalCarbonKg: 1289.74,
  totalCo2eqKg: 4729.06,
  isCertifiedCredit: false,
};

describe('TreeResultTable', () => {
  it('keeps measured and excluded tree IDs in one ascending sequence', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);
    const rowPositions = [1, 2, 3, 4, 5].map((treeId) => markup.indexOf(`>${treeId}</th>`));

    expect(rowPositions.every((position) => position >= 0)).toBe(true);
    expect(rowPositions).toEqual([...rowPositions].sort((a, b) => a - b));
  });

  it('labels measured rows READY and excluded rows with their pipeline reason', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);
    const rows = markup.match(/<tr[^>]*>.*?<\/tr>/g) ?? [];
    const treeOne = rows.find((row) => row.includes('>1</th>'));
    const treeFour = rows.find((row) => row.includes('>4</th>'));

    expect(markup.match(/READY/g)).toHaveLength(3);
    expect(markup.match(/EXCLUDED/g)).toHaveLength(2);
    expect(treeOne).toContain('ไม่รวมผล');
    expect(treeOne).toContain('วัดค่า DBH หรือความสูงไม่สำเร็จ');
    expect(treeFour).toContain('ไม่รวมผล');
    expect(treeFour).toContain('วัดค่า DBH หรือความสูงไม่สำเร็จ');
  });

  it('keeps measurements tabular and confines the wide table to its own scroller', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);

    expect(markup).toContain('1,775.21');
    expect(markup).toContain('tabular-nums');
    expect(markup).toContain('overflow-x-auto');
    expect(markup).toContain('min-w-[44rem]');
  });
});
