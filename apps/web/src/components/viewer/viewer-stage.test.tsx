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
  it('promises the colouring the pipeline can now deliver', () => {
    const markup = render({ labelled: false });

    expect(markup).toContain('ไฟล์นี้เก็บเฉพาะพิกัด');
    // /upload/analyze returns segmented_cloud_id and the viewer swaps to that
    // cloud, so offering to colour the picture is a promise the API keeps. It
    // was not always: this note used to commit only to numbers.
    expect(markup).toContain('ระบายสีให้');
  });

  it('still tells the truth when analysis ran but no cloud came back', () => {
    // segmented_cloud_id can be null, and the fetch can fail. The numbers are
    // valid either way, so this branch stays: it credits the separation to the
    // figures rather than to a picture that did not change.
    const markup = render({ labelled: false, analysed: true });

    expect(markup).toContain('ระบบแยกลำต้นกับใบไปแล้ว');
    expect(markup).toContain('ตัวเลขทางขวา');
    expect(markup).toContain('ยังเป็นสีเดียว');
  });

  it('shows the class legend only for a cloud that carries classes', () => {
    expect(render({ labelled: true })).toContain('(Wood)');
    expect(render({ labelled: false })).not.toContain('(Wood)');
    expect(render({ labelled: false, analysed: true })).not.toContain('(Wood)');
  });
});
