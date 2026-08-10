'use client';

/**
 * The last resort: an error thrown inside the root layout itself.
 *
 * error.tsx cannot catch that, because it renders *inside* the layout that
 * failed. This file replaces the whole document, so it carries its own <html>
 * and <body> and cannot rely on anything the layout sets up — no fonts, no
 * globals.css, no theme provider. Hence the inline styles: a stylesheet the
 * failing layout was responsible for loading is exactly what might be missing.
 */

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="th">
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.25rem',
          padding: '1.5rem',
          textAlign: 'center',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          background: '#0b0f0d',
          color: '#e8ece9',
        }}
      >
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600, margin: 0 }}>
          ระบบขัดข้อง
        </h1>
        <p style={{ margin: 0, maxWidth: '38rem', fontSize: '0.875rem', opacity: 0.75 }}>
          โหลดหน้าเว็บไม่สำเร็จ ลองรีเฟรชอีกครั้ง
        </p>
        <button
          type="button"
          onClick={reset}
          style={{
            border: 'none',
            borderRadius: '0.375rem',
            background: '#e8ece9',
            color: '#0b0f0d',
            padding: '0.5rem 1rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          ลองใหม่
        </button>
        {error.digest ? (
          <p style={{ margin: 0, fontSize: '0.75rem', opacity: 0.6 }}>
            รหัสอ้างอิง: <code style={{ fontFamily: 'monospace' }}>{error.digest}</code>
          </p>
        ) : null}
      </body>
    </html>
  );
}
