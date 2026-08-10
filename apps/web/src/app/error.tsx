'use client';

/**
 * What a user sees when a page throws.
 *
 * There was no error.tsx anywhere in this app, so any thrown error reached
 * Next.js's production fallback: a blank page reading "Application error: a
 * client-side exception has occurred", with no way to retry and nothing to
 * quote when reporting it.
 *
 * `digest` is the identifier Next.js attaches to a server-side error and the
 * only thing that ties this screen to a server log line, so it is shown rather
 * than hidden. The error message itself is not: on the server Next.js redacts
 * it in production precisely because it can carry internals, and displaying
 * whatever survives would be inconsistent between environments.
 */

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // The browser console is the only sink this app has. Logging the whole
    // error object keeps the stack reachable in development, where it is not
    // redacted.
    console.error('Unhandled page error', error);
  }, [error]);

  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">เกิดข้อผิดพลาดในหน้านี้</h1>
        <p className="max-w-prose text-sm text-muted-foreground">
          ระบบไม่สามารถแสดงหน้านี้ได้ ข้อมูลการวิเคราะห์ของคุณไม่ได้หายไป
          ลองใหม่อีกครั้งได้เลย
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background transition-opacity hover:opacity-90"
        >
          ลองใหม่
        </button>
        <a
          href="/"
          className="rounded-md border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
        >
          กลับหน้าแรก
        </a>
      </div>

      {error.digest ? (
        <p className="text-xs text-muted-foreground">
          รหัสอ้างอิงสำหรับแจ้งปัญหา:{' '}
          <code className="rounded bg-muted px-1.5 py-0.5 font-mono">{error.digest}</code>
        </p>
      ) : null}
    </main>
  );
}
