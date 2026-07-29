import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { toResultViewModel } from '../../lib/result-view-model';
import { ResultRail } from './result-rail';

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

    expect(markup).toContain('ต้นไม้ที่คำนวณสำเร็จ');
    expect(markup).toContain('ต้นไม้ที่ตรวจพบ');
    expect(markup).toContain('ไม่รวมผล');
    expect(markup).toContain('4.729 tCO₂e');
    expect(markup).toContain('1,289.74 kg');
    expect(markup).toContain('3');
    expect(markup).toContain('5');
    expect(markup).toContain('2');
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

    expect(markup).toContain('diagnostics unavailable');
    expect(markup).toContain('ต้นไม้ที่คำนวณสำเร็จ');
    expect(markup).not.toContain('ต้นไม้ที่ตรวจพบ');
    expect(markup).not.toContain('>0 ต้น<');
    expect(markup).not.toContain('>2 ต้น<');
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
