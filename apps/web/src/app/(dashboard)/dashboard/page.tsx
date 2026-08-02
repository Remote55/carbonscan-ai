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
        {/* Thai throughout, at the designer's report that this page switched
            between the two languages line by line. English stays only where it
            is a name a Thai word would not replace - LiDAR, .ply, the file
            extensions - not for ordinary UI words like Viewer or Planned. */}
        <p className="mt-2 text-muted-foreground">
          คุณเข้าสู่ระบบเป็น{' '}
          <span className="font-medium text-foreground">
            {userMetadata.role === 'community' || !userMetadata.role
              ? 'ผู้ใช้ทั่วไป'
              : userMetadata.role}
          </span>
        </p>

        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {/* Ready now — 3D Viewer */}
          <Link
            href="/dashboard/viewer"
            className="group rounded-xl border border-primary/30 bg-primary/5 p-6 transition-all hover:border-primary/60 hover:shadow-md"
          >
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">🌲 โมเดล 3 มิติ</h2>
              <span className="rounded-full bg-primary/15 px-2.5 py-0.5 text-xs font-medium text-primary">
                พร้อมใช้
              </span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              ดูต้นไม้แบบ 3 มิติ แยกสีลำต้น ใบ และพื้นดิน หมุนและซูมได้
              หรือลากไฟล์ .ply ที่แยกลำต้นกับใบแล้วเข้ามาดู
            </p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary transition-all group-hover:gap-2">
              เปิดโมเดล 3 มิติ <span aria-hidden>→</span>
            </span>
          </Link>

          {/* Coming next */}
          <Link
  href="/dashboard/map"
  className="group rounded-xl border border-primary/30 bg-primary/5 p-6 transition-all hover:border-primary/60 hover:shadow-md"
>
  <div className="flex items-center justify-between gap-2">
    <h2 className="text-lg font-semibold">🗺️ ดูแผนที่ </h2>
    <span className="rounded-full bg-primary/15 px-2.5 py-0.5 text-xs font-medium text-primary">
      พร้อมใช้งานบางส่วน
    </span>
  </div>
  <p className="mt-2 text-sm text-muted-foreground">
    เปิดดูแผนที่และตำแหน่งแปลงสำรวจคาร์บอนในเขตจังหวัดสงขลา 
  </p>
  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary transition-all group-hover:gap-2">
    ดูแผนที่ <span aria-hidden>→</span>
  </span>
</Link>
        </div>

        <div className="mt-6 text-sm text-muted-foreground">
          <span>รหัสผู้ใช้</span>{' '}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{user.id}</code>
        </div>
      </div>
    </main>
  );
}
