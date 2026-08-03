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

          {/* The map. Its card said it showed survey-plot positions in Songkhla,
              which would be a claim about data we hold; it draws a base map and
              one example pin. The badge says so rather than "พร้อมใช้งานบางส่วน". */}
          <Link
            href="/dashboard/map"
            className="group rounded-xl border border-border bg-card p-6 transition-all hover:border-primary/60 hover:shadow-md"
          >
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">🗺️ แผนที่</h2>
              <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                ตัวอย่างการแสดงผล
              </span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              แสดงแผนที่พื้นที่จังหวัดสงขลาพร้อมหมุดตัวอย่างหนึ่งจุด
              ยังไม่ได้เชื่อมกับข้อมูลแปลงสำรวจจริง และต้องใช้อินเทอร์เน็ตเพื่อโหลดภาพแผนที่
            </p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary transition-all group-hover:gap-2">
              เปิดแผนที่ <span aria-hidden>→</span>
            </span>
          </Link>
        </div>

        {/* This list was a card in the grid until the map replaced it, taking
            three disclosures with it. They belong on the page a signed-in user
            lands on, not only on the landing page. */}
        <div className="mt-6 rounded-xl border border-border bg-card p-6">
          <h2 className="text-lg font-semibold">อยู่ในแผนถัดไป</h2>
          <ul className="mt-3 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
              อัปโหลดไฟล์ LiDAR (.las/.laz) แล้วประมวลผลให้อัตโนมัติ
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
              จำแนกชนิดพันธุ์ไม้อัตโนมัติ (ตอนนี้ผู้ใช้ระบุเอง)
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
              เชื่อมแผนที่กับตำแหน่งแปลงที่สแกนจริง
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
              ระบบซื้อขายคาร์บอนเครดิต
            </li>
          </ul>
        </div>

        <div className="mt-6 text-sm text-muted-foreground">
          <span>รหัสผู้ใช้</span>{' '}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{user.id}</code>
        </div>
      </div>
    </main>
  );
}
