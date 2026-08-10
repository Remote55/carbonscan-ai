/**
 * The 404 page. Without one, Next.js serves its unstyled default, which drops
 * a visitor out of the site's design with no route back into it.
 */

import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="space-y-3">
        <p className="font-mono text-sm text-muted-foreground">404</p>
        <h1 className="text-2xl font-semibold tracking-tight">ไม่พบหน้าที่ต้องการ</h1>
        <p className="max-w-prose text-sm text-muted-foreground">
          ลิงก์อาจหมดอายุหรือถูกย้ายไปแล้ว
        </p>
      </div>
      <Link
        href="/"
        className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background transition-opacity hover:opacity-90"
      >
        กลับหน้าแรก
      </Link>
    </main>
  );
}
