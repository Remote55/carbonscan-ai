/**
 * What this deployment will accept, in one place.
 *
 * The landing page advertised "จำกัด 2 ล้านจุด หรือ 100 MB ต่อไฟล์" and the
 * viewer checked the file extension and nothing else. Someone choosing a 400 MB
 * scan had the whole thing read into an ArrayBuffer — with whatever that does to
 * a laptop — uploaded, and then rejected by the API, which is the one place the
 * limits were real.
 *
 * These mirror the API's TREEQ_DEMO_MAX_UPLOAD_SIZE_MB and
 * TREEQ_DEMO_MAX_POINTS. Two services cannot share a constant, so the
 * arrangement is that the client refuses early and the server refuses finally;
 * the client being out of date can only make it stricter than necessary, never
 * looser than the server.
 */

export const MAX_UPLOAD_MB = 100;
export const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;
export const MAX_UPLOAD_POINTS = 2_000_000;
export const ACCEPTED_EXTENSION = '.ply';

/** The sentence shown to a visitor. Same numbers as the checks below. */
export const LIMITS_LABEL_TH = `จำกัด ${(MAX_UPLOAD_POINTS / 1_000_000).toLocaleString(
  'th-TH',
)} ล้านจุด หรือ ${MAX_UPLOAD_MB} MB ต่อไฟล์`;

export type UploadRejection = { reason: string } | null;

/**
 * Why this file cannot be accepted, or null if it can.
 *
 * Checked before the file is read: the size is known from the picker, so the
 * expensive part never has to start.
 */
export function rejectFileBeforeReading(file: File): UploadRejection {
  if (!file.name.toLowerCase().endsWith(ACCEPTED_EXTENSION)) {
    return { reason: `รองรับเฉพาะไฟล์ ${ACCEPTED_EXTENSION} เท่านั้น` };
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    const mb = file.size / (1024 * 1024);
    return {
      reason:
        `ไฟล์ใหญ่ ${mb.toFixed(1)} MB เกินขีดจำกัด ${MAX_UPLOAD_MB} MB ` +
        `— ลองลดจำนวนจุดก่อนอัปโหลด`,
    };
  }
  if (file.size === 0) {
    return { reason: 'ไฟล์ว่าง' };
  }
  return null;
}

/**
 * Why a parsed cloud cannot be accepted, or null if it can.
 *
 * `declaredCount` is what the file's header claimed. It is checked as well as
 * the real total, because a header claiming fifty million points is a file
 * worth refusing whatever its body turned out to hold.
 */
export function rejectCloudAfterParsing(
  pointCount: number,
  declaredCount?: number,
): UploadRejection {
  if (pointCount === 0) {
    return { reason: 'ไฟล์นี้ไม่มีจุด (point) ที่อ่านได้' };
  }
  const claimed = declaredCount ?? pointCount;
  if (Math.max(pointCount, claimed) > MAX_UPLOAD_POINTS) {
    const millions = Math.max(pointCount, claimed) / 1_000_000;
    return {
      reason:
        `ไฟล์มี ${millions.toFixed(1)} ล้านจุด เกินขีดจำกัด ` +
        `${MAX_UPLOAD_POINTS / 1_000_000} ล้านจุด`,
    };
  }
  if (declaredCount !== undefined && declaredCount !== pointCount) {
    // Not a refusal. The file is usable; the header just does not match, and
    // the person looking at a point total deserves to know which number it is.
    return null;
  }
  return null;
}

/** A note to show when a file's header disagrees with its contents. */
export function headerMismatchNote(
  pointCount: number,
  declaredCount?: number,
): string | null {
  if (declaredCount === undefined || declaredCount === pointCount) return null;
  return (
    `ส่วนหัวไฟล์ระบุ ${declaredCount.toLocaleString('th-TH')} จุด ` +
    `แต่อ่านได้จริง ${pointCount.toLocaleString('th-TH')} จุด — ใช้ค่าที่อ่านได้จริง`
  );
}
