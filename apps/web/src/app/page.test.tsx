import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import HomePage from './page';

describe('Landing evidence contract', () => {
  it('leads to the judge demo and reports validation without rounding', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain('href="/demo"');
    expect(markup).toContain('ทดลอง Demo Dataset');
    expect(markup).toContain('อัปโหลด Point Cloud');
    expect(markup).toContain('0.418');
    expect(markup).toContain('0.808');
    expect(markup).toContain('1.1673846154');
    expect(markup).toContain('PointNet++');
    expect(markup).toContain('Experimental');
    expect(markup).toContain('species');
    expect(markup).not.toContain('93.135');
  });

  it('renders exactly the four evidence-led editorial beats', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup.split('data-editorial-beat=').length - 1).toBe(4);
    expect(markup).toContain('ปัญหาที่การวัดแบบเดิมทิ้งไว้');
    expect(markup).toContain('เส้นทางการวัดจากจุดสู่คาร์บอน');
    expect(markup).toContain('หลักฐาน 3D ที่เปิดให้ตรวจสอบ');
    expect(markup).toContain('Validation ที่รายงานตามขอบเขต');
  });
});
