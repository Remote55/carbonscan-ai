import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase-server';

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Middleware should already redirect, but double-check
  if (!user) redirect('/login');

  const userMetadata = user.user_metadata as {
    name?: string;
    role?: string;
  };

  return (
    <main className="container mx-auto px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="font-display text-4xl font-bold tracking-tight">
          ยินดีต้อนรับ, {userMetadata.name ?? user.email}
        </h1>
        <p className="mt-2 text-muted-foreground">
          คุณเข้าสู่ระบบเป็น{' '}
          <span className="font-medium text-foreground">{userMetadata.role ?? 'community'}</span>
        </p>

        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {/* Ready now — 3D Viewer */}
          <Link
            href="/dashboard/viewer"
            className="group rounded-xl border border-primary/30 bg-primary/5 p-6 transition-all hover:border-primary/60 hover:shadow-md"
          >
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">🌲 3D Point Cloud Viewer</h2>
              <span className="rounded-full bg-primary/15 px-2.5 py-0.5 text-xs font-medium text-primary">
                พร้อมใช้
              </span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              ดูต้นไม้แบบ 3 มิติ แยกสีลำต้น / ใบ / พื้นดิน — หมุน ซูม และลากไฟล์ .ply ที่ segment แล้วมาดูได้
            </p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary transition-all group-hover:gap-2">
              เปิด Viewer <span aria-hidden>→</span>
            </span>
          </Link>

          {/* Coming next */}
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="text-lg font-semibold">เร็ว ๆ นี้ (Phase ถัดไป)</h2>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
                อัปโหลด LiDAR (.las/.laz) แล้วประมวลผลอัตโนมัติ
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
                แผนที่ GIS แสดงตำแหน่งต้นไม้
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
                Marketplace ซื้อขาย Carbon Credit
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-6 text-sm text-muted-foreground">
          <span className="font-mono">User ID:</span>{' '}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{user.id}</code>
        </div>
      </div>
    </main>
  );
}
