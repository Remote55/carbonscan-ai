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

        <div className="mt-12 rounded-xl border border-border bg-card p-8">
          <h2 className="text-xl font-semibold">เริ่มต้นใช้งาน</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Dashboard ยังอยู่ใน Phase 1 — features ที่จะมา:
          </p>
          <ul className="mt-4 space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-primary" />
              อัปโหลดไฟล์ LiDAR (.las/.laz)
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-primary" />
              ดูต้นไม้ของคุณบนแผนที่ GIS
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-primary" />
              3D Point Cloud Viewer
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-primary" />
              Marketplace สำหรับ Carbon Credit
            </li>
          </ul>
        </div>

        <div className="mt-6 text-sm text-muted-foreground">
          <span className="font-mono">User ID:</span>{' '}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{user.id}</code>
        </div>
      </div>
    </main>
  );
}
