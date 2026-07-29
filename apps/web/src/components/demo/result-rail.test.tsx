import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { toResultViewModel } from '../../lib/result-view-model';
import { ResultRail } from './result-rail';

function definitionPairs(markup: string) {
  const definitionList = markup.match(/<dl[^>]*>([\s\S]*?)<\/dl>/)?.[1] ?? '';

  return new Map(
    [
      ...definitionList.matchAll(
        /<div[^>]*data-result-metric=""[^>]*aria-label="([^"]+)"[^>]*>([\s\S]*?)<\/div>/g,
      ),
    ].map(([, accessibleName, contents]) => [accessibleName, contents]),
  );
}

describe('ResultRail', () => {
  it('labels measured trees and explains exclusions', () => {
    const view = toResultViewModel({
      summary: {
        total_trees: 3,
        measured_trees: 3,
        detected_trees: 5,
        excluded_trees: 2,
        total_carbon_kg: 1289.74,
        total_co2eq_kg: 4729.06,
      },
      diagnostics: {
        excluded_segments: [
          { tree_id: 1, stage: 'qsm', reason_code: 'QSM_INVALID' },
          { tree_id: 4, stage: 'qsm', reason_code: 'QSM_INVALID' },
        ],
      },
    });

    const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Frozen Evidence" />);

    const pairs = definitionPairs(markup);

    expect(markup).toContain('4.729 tCO₂e');
    expect([...pairs.keys()]).toEqual([
      'คาร์บอนรวม — 1,289.74 kg',
      'ต้นไม้ที่คำนวณสำเร็จ — 3 ต้น',
      'ต้นไม้ที่ตรวจพบ — 5 ต้น',
      'ไม่รวมผล — 2 ต้น',
    ]);
    for (const contents of pairs.values()) {
      expect(contents).toMatch(/^<dt[\s\S]*<\/dt>\s*<dd[\s\S]*<\/dd>$/);
    }
    expect(markup).not.toContain('จำนวนต้นไม้');
  });

  it('omits detected and excluded numbers when diagnostics are unavailable', () => {
    const view = toResultViewModel({
      summary: {
        total_trees: 3,
        total_carbon_kg: 1289.74,
        total_co2eq_kg: 4729.06,
      },
    });

    const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Live Analysis" />);

    const pairs = definitionPairs(markup);

    expect(markup).toContain('diagnostics unavailable');
    expect([...pairs.keys()]).toEqual([
      'คาร์บอนรวม — 1,289.74 kg',
      'ต้นไม้ที่คำนวณสำเร็จ — 3 ต้น',
      'Diagnostics — diagnostics unavailable',
    ]);
    for (const contents of pairs.values()) {
      expect(contents).toMatch(/^<dt[\s\S]*<\/dt>\s*<dd[\s\S]*<\/dd>$/);
    }
  });

  it('states that the estimate is not a certified carbon credit', () => {
    const view = toResultViewModel({
      summary: {
        total_trees: 1,
        total_carbon_kg: 100,
        total_co2eq_kg: 366.67,
      },
    });

    const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Live Analysis" />);

    expect(markup).toContain('ค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง');
  });
});
