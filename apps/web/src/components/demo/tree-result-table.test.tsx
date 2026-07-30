import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import type { ResultViewModel } from '../../lib/result-view-model';
import { contrastRatio, tokenHex } from '../../test-support/wcag';
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

  // A reviewer said the type sizes looked wrong, and they were: the status column
  // carried a 10px badge, a 12px reason and the row's own 14px, so three sizes sat
  // in one cell. Two are allowed now and each means something - 11px mono for
  // labels, body size for prose - so this fails if a third creeps back in.
  it('uses one label size and one content size, not three', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);
    const sizes = new Set(
      (markup.match(/text-(\[[^\]]+\]|xs|sm|base|lg|xl)/g) ?? []).map((match) => match),
    );

    expect(sizes).toEqual(new Set(['text-[0.6875rem]', 'text-sm']));
  });

  it('marks an excluded row in the dedicated red, not the softer error tone', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);
    const badge = markup.match(/<[a-z]+ class="([^"]*)"[^>]*>EXCLUDED</)?.[1];

    expect(badge).toContain('text-ember');
    expect(badge).toContain('font-bold');
    // clay still labels "Experimental" elsewhere, which is a state and not a
    // failure, so the two must not collapse into one colour.
    expect(badge).not.toContain('text-clay');
  });

  it('uses the AA light-surface text token for the small READY status', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);
    const measuredRow = (markup.match(/<tr[^>]*>.*?<\/tr>/g) ?? []).find((row) =>
      row.includes('READY'),
    );

    expect(measuredRow).toContain('text-canopy');
    expect(measuredRow).not.toContain('text-moss');
  });

  // Asserting the class name alone let a real failure through: EXCLUDED is 10px
  // text on the excluded row's own Gallery Ivory background, and the token used
  // there sat at 4.28:1 while the review recorded the fix as complete. Compute
  // the ratio against the surface each badge actually renders on.
  //
  // Read the token off the element that holds the badge text, never off the whole
  // row. Both rows carry `text-canopy` on their row header, which comes first in
  // the markup, so a row-wide match would report canopy for the excluded badge
  // and pass without ever looking at the colour that was actually broken.
  it('keeps both status badges at AA against the surface they render on', () => {
    const markup = renderToStaticMarkup(<TreeResultTable view={view} />);

    function badgeToken(label: string): string {
      const element = markup.match(new RegExp(`<[a-z]+ class="([^"]*)"[^>]*>${label}<`))?.[1];
      if (!element) throw new Error(`Missing badge element for ${label}`);
      const token = element.match(/text-(canopy|moss|clay|ember|forest-ink|deep-forest)\b/)?.[1];
      if (!token) throw new Error(`Badge ${label} has no resolvable colour token: ${element}`);
      return token;
    }

    const rows = markup.match(/<tr[^>]*>.*?<\/tr>/g) ?? [];
    const excludedRow = rows.find((row) => row.includes('EXCLUDED'));
    // The excluded row tints itself; the measured row inherits the card surface.
    expect(excludedRow).toContain('bg-gallery-ivory');

    expect(contrastRatio(tokenHex(badgeToken('READY')), tokenHex('paper'))).toBeGreaterThanOrEqual(
      4.5,
    );
    expect(
      contrastRatio(tokenHex(badgeToken('EXCLUDED')), tokenHex('gallery-ivory')),
    ).toBeGreaterThanOrEqual(4.5);
  });
});
