import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ViewerStage } from './viewer-stage';

/**
 * What the stage says about a cloud it cannot colour.
 *
 * The canvas itself does not render here - it waits for a measured aspect that
 * only a real layout provides - which is exactly why these notes are worth a
 * unit test: they are the part of the stage that makes a claim.
 */

function render(props: { labelled: boolean; analysed?: boolean }) {
  return renderToStaticMarkup(
    <ViewerStage
      title="แปลงทดสอบ"
      evidenceLabel="ทดสอบ"
      positions={new Float32Array([0, 0, 0])}
      classes={new Uint8Array([0])}
      {...props}
    />,
  );
}

describe('ViewerStage — what it says about an unclassified cloud', () => {
  it('offers no colouring it cannot deliver before analysis', () => {
    const markup = render({ labelled: false });

    expect(markup).toContain('ไฟล์นี้เก็บเฉพาะพิกัด');
    // The pipeline returns numbers. Anything implying the picture will change
    // is a promise /upload/analyze cannot keep.
    expect(markup).toContain('ผลจะออกมาเป็นตัวเลข');
    expect(markup).not.toMatch(/สีจะขึ้น|ระบายสีให้|เปลี่ยนเป็นสี/);
  });

  it('after analysis, credits the separation but not to this picture', () => {
    const markup = render({ labelled: false, analysed: true });

    expect(markup).toContain('ระบบแยกลำต้นกับใบไปแล้ว');
    expect(markup).toContain('ตัวเลขทางขวา');
    // Still the file the browser parsed, and it has to keep saying so.
    expect(markup).toContain('ยังเป็นสีเดียว');
  });

  it('shows the class legend only for a cloud that carries classes', () => {
    expect(render({ labelled: true })).toContain('(Wood)');
    expect(render({ labelled: false })).not.toContain('(Wood)');
    expect(render({ labelled: false, analysed: true })).not.toContain('(Wood)');
  });
});
