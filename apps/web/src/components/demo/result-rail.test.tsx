import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { toResultViewModel } from '../../lib/result-view-model';
import { ResultRail } from './result-rail';

function visibleText(fragment: string) {
  return fragment.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

function definitionPairs(markup: string): Array<[term: string, description: string]> {
  const definitionList = markup.match(/<dl[^>]*>([\s\S]*?)<\/dl>/)?.[1] ?? '';

  return [...definitionList.matchAll(/<div[^>]*data-result-metric=""[^>]*>([\s\S]*?)<\/div>/g)].map(
    ([, group]) => {
      const term = group.match(/<dt[^>]*>([\s\S]*?)<\/dt>/)?.[1];
      const description = group.match(/<dd[^>]*>([\s\S]*?)<\/dd>/)?.[1];

      if (term === undefined || description === undefined) {
        throw new Error('Expected each result metric to contain a visible dt/dd pair');
      }

      return [visibleText(term), visibleText(description)];
    },
  );
}

function paragraphTexts(markup: string) {
  return [...markup.matchAll(/<p[^>]*>([\s\S]*?)<\/p>/g)].map(([, contents]) =>
    visibleText(contents),
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

    const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Frozen Evidence" integrity="manifest-verified" />);

    const pairs = definitionPairs(markup);
    const paragraphs = paragraphTexts(markup);

    expect(paragraphs).toContain('4.729 tCO₂e');
    expect(pairs).toEqual([
      ['คาร์บอนรวม ผลรวมจากต้นไม้ที่คำนวณสำเร็จ', '1,289.74 kg'],
      ['ต้นไม้ที่คำนวณสำเร็จ ต้นไม้ที่ผ่านการประเมินโครงสร้างทางเรขาคณิตสำเร็จ', '3 ต้น'],
      ['ต้นไม้ที่ตรวจพบ จำนวนต้นไม้ทั้งหมดที่ระบบจำแนกได้จาก Point Cloud', '5 ต้น'],
      [
        'ไม่รวมผล ข้อมูลที่วัดค่า DBH หรือความสูงไม่สำเร็จ และไม่ถูกนำไปคำนวณยอดคาร์บอนสุทธิ',
        '2 ต้น',
      ],
    ]);
  });

  it('omits detected and excluded numbers when diagnostics are unavailable', () => {
    const view = toResultViewModel({
      summary: {
        total_trees: 3,
        total_carbon_kg: 1289.74,
        total_co2eq_kg: 4729.06,
      },
    });

    const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Live Analysis" integrity="live-run" />);

    const pairs = definitionPairs(markup);

    expect(pairs).toEqual([
      ['คาร์บอนรวม ผลรวมจากต้นไม้ที่คำนวณสำเร็จ', '1,289.74 kg'],
      ['ต้นไม้ที่คำนวณสำเร็จ ต้นไม้ที่ผ่านการประเมินโครงสร้างทางเรขาคณิตสำเร็จ', '3 ต้น'],
      [
        'Diagnostics',
        'diagnostics unavailable ผลรุ่นนี้ไม่มีข้อมูลพอที่จะยืนยันจำนวนที่ตรวจพบหรือไม่รวมผล',
      ],
    ]);
  });

  it('states that the estimate is not a certified carbon credit', () => {
    const view = toResultViewModel({
      summary: {
        total_trees: 1,
        total_carbon_kg: 100,
        total_co2eq_kg: 366.67,
      },
    });

    const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Live Analysis" integrity="live-run" />);

    expect(paragraphTexts(markup)).toContain(
      'ค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง',
    );
  });
});

const VIEW = toResultViewModel({
  summary: {
    total_trees: 1,
    measured_trees: 1,
    detected_trees: 1,
    excluded_trees: 0,
    total_carbon_kg: 10,
    total_co2eq_kg: 36.7,
  },
  diagnostics: { excluded_segments: [] },
});

describe('what the heading claims', () => {
  /**
   * The heading read "ผลการประเมินที่ผ่านการยืนยันความสมบูรณ์" — results whose
   * integrity has been verified — in every case. This component is only
   * rendered by the live viewer, so that sentence appeared exclusively on the
   * results where nothing had been verified against anything.
   */

  it('does not claim verification for a live run', () => {
    const markup = renderToStaticMarkup(
      <ResultRail view={VIEW} modeLabel="Live analysis" integrity="live-run" />,
    );

    expect(markup).not.toContain('ผ่านการยืนยันความสมบูรณ์');
    expect(markup).toContain('ยังไม่มี manifest');
  });

  it('claims it only when a manifest was actually checked', () => {
    const markup = renderToStaticMarkup(
      <ResultRail view={VIEW} modeLabel="Frozen evidence" integrity="manifest-verified" />,
    );

    expect(markup).toContain('ผ่านการยืนยันความสมบูรณ์');
    expect(markup).toContain('ตรวจแฮชกับ manifest');
  });

  it('says something either way rather than going quiet', () => {
    for (const integrity of ['live-run', 'manifest-verified'] as const) {
      const markup = renderToStaticMarkup(
        <ResultRail view={VIEW} modeLabel="x" integrity={integrity} />,
      );
      expect(markup).toContain('ผลการประเมิน');
    }
  });
});
