import { describe, expect, it } from 'vitest';

import {
  LIMITS_LABEL_TH,
  MAX_UPLOAD_BYTES,
  MAX_UPLOAD_POINTS,
  headerMismatchNote,
  rejectCloudAfterParsing,
  rejectFileBeforeReading,
} from './upload-limits';

/**
 * The landing page advertised these limits and the viewer enforced none of
 * them. A 400 MB scan was read into an ArrayBuffer, uploaded, and refused by
 * the API — the only place they were real.
 */

function file(name: string, size: number): File {
  return { name, size } as File;
}

describe('before the file is read', () => {
  it('accepts a normal ply', () => {
    expect(rejectFileBeforeReading(file('plot.ply', 5_000_000))).toBeNull();
  });

  it('refuses anything that is not a ply', () => {
    expect(rejectFileBeforeReading(file('scan.las', 1000))?.reason).toContain('.ply');
  });

  it('is not fooled by capitalisation', () => {
    expect(rejectFileBeforeReading(file('PLOT.PLY', 1000))).toBeNull();
  });

  it('refuses a file over the advertised size', () => {
    const reason = rejectFileBeforeReading(file('huge.ply', MAX_UPLOAD_BYTES + 1))?.reason;
    expect(reason).toContain('100 MB');
  });

  it('accepts one exactly at the limit', () => {
    expect(rejectFileBeforeReading(file('edge.ply', MAX_UPLOAD_BYTES))).toBeNull();
  });

  it('refuses an empty file', () => {
    expect(rejectFileBeforeReading(file('empty.ply', 0))).not.toBeNull();
  });
});

describe('after parsing', () => {
  it('accepts a cloud under the point limit', () => {
    expect(rejectCloudAfterParsing(500_000, 500_000)).toBeNull();
  });

  it('refuses a cloud over it', () => {
    expect(rejectCloudAfterParsing(MAX_UPLOAD_POINTS + 1)?.reason).toContain('ล้านจุด');
  });

  it('refuses a header claiming more than the limit even if the body is small', () => {
    // A file whose header claims fifty million points is worth refusing
    // whatever its body turned out to hold.
    expect(rejectCloudAfterParsing(10, 50_000_000)).not.toBeNull();
  });

  it('refuses a cloud with no readable points', () => {
    expect(rejectCloudAfterParsing(0)?.reason).toContain('ไม่มีจุด');
  });
});

describe('when a header disagrees with its file', () => {
  it('says so, with both numbers', () => {
    const note = headerMismatchNote(10, 1000);
    expect(note).toContain('1,000');
    expect(note).toContain('10');
  });

  it('stays quiet when they agree', () => {
    expect(headerMismatchNote(1000, 1000)).toBeNull();
  });

  it('stays quiet when the file never declared one', () => {
    expect(headerMismatchNote(1000, undefined)).toBeNull();
  });
});

describe('the advertised sentence', () => {
  it('is built from the numbers that are enforced', () => {
    expect(LIMITS_LABEL_TH).toContain(String(MAX_UPLOAD_POINTS / 1_000_000));
    expect(LIMITS_LABEL_TH).toContain(String(MAX_UPLOAD_BYTES / 1024 / 1024));
  });
});
