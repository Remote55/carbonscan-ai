import Link from 'next/link';
import { ArrowRight, Sparkles, ShieldCheck, Globe2, LineChart } from 'lucide-react';

export default function HomePage() {
  return (
    <main className="min-h-screen">
      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <nav className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo.png"
              alt="CarbonScan AI logo"
              className="h-9 w-9 object-contain"
            />
            <span className="font-display text-lg font-bold tracking-tight">
              CarbonScan AI
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/marketplace"
              className="hidden text-sm font-medium text-muted-foreground hover:text-foreground sm:block"
            >
              Marketplace
            </Link>
            <Link
              href="/login"
              className="hidden text-sm font-medium text-muted-foreground hover:text-foreground sm:block"
            >
              เข้าสู่ระบบ
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              เริ่มใช้ฟรี
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="container mx-auto px-4 py-20 lg:py-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted px-4 py-1.5 text-sm">
              <Sparkles className="h-4 w-4 text-forest-500" />
              <span className="font-medium">NSC 2026 — Sustainable Innovation</span>
            </div>

            <h1 className="font-display text-balance text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
              แปลงต้นไม้เป็น{' '}
              <span className="bg-sustainable-gradient bg-clip-text text-transparent">
                Carbon Credits
              </span>{' '}
              ด้วย AI ที่โปร่งใส
            </h1>

            <p className="mt-6 text-balance text-lg text-muted-foreground sm:text-xl">
              แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ ด้วย LiDAR Point Cloud + AI Wood-Leaf Segmentation +
              B2B Carbon Offset Matchmaking ลดต้นทุนการตรวจสอบ 100 เท่า โปร่งใส 100%
            </p>

            <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex h-12 items-center gap-2 rounded-lg bg-primary px-6 text-base font-medium text-primary-foreground transition-all hover:bg-primary/90 hover:shadow-lg"
              >
                ลองใช้ฟรี
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/marketplace"
                className="inline-flex h-12 items-center gap-2 rounded-lg border border-border bg-background px-6 text-base font-medium transition-colors hover:bg-muted"
              >
                ดู Marketplace
              </Link>
            </div>

            <p className="mt-4 text-sm text-muted-foreground">
              ฟรีสำหรับชุมชน · ไม่ต้องบัตรเครดิต · พร้อมใช้ในเวลา 5 นาที
            </p>
          </div>
        </div>

        {/* Background gradient orb */}
        <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-forest-500/10 blur-3xl" />
      </section>

      {/* Features */}
      <section className="border-t border-border bg-muted/30">
        <div className="container mx-auto px-4 py-20">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              เทคโนโลยีที่ขับเคลื่อน
            </h2>
            <p className="mt-4 text-muted-foreground">
              ผสาน 3D Point Cloud Processing, Deep Learning และ Cloud Architecture
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: Sparkles,
                title: 'AI Wood-Leaf Segmentation',
                desc: 'PointNet++ แยกใบและลำต้นได้แม่นยำ IoU ≥ 0.70',
              },
              {
                icon: ShieldCheck,
                title: 'Anti-Fraud System',
                desc: 'GPS 6-decimal + EXIF + Server-side dedup',
              },
              {
                icon: Globe2,
                title: 'Verifiable 3D',
                desc: 'ดูทุกต้นไม้ที่สนับสนุนผ่าน 3D Viewer + GPS Map',
              },
              {
                icon: LineChart,
                title: 'TGO Standard',
                desc: 'คำนวณตามสมการแอลโลเมตริกมาตรฐาน',
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="rounded-xl border border-border bg-card p-6 transition-all hover:shadow-md"
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-forest-500/10">
                  <feature.icon className="h-5 w-5 text-forest-500" />
                </div>
                <h3 className="font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-t border-border">
        <div className="container mx-auto px-4 py-20">
          <div className="grid gap-12 sm:grid-cols-3">
            {[
              { stat: '100×', label: 'ลดต้นทุนการประเมิน' },
              { stat: '5 ชนิด', label: 'ไม้เศรษฐกิจที่รองรับ' },
              { stat: '< 10 นาที', label: 'เวลาประมวลผล/แปลง' },
            ].map((item, i) => (
              <div key={i} className="text-center">
                <div className="font-display text-5xl font-bold text-forest-500">
                  {item.stat}
                </div>
                <div className="mt-2 text-sm text-muted-foreground">{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/30">
        <div className="container mx-auto px-4 py-12">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/logo.png"
                alt="CarbonScan AI logo"
                className="h-7 w-7 object-contain"
              />
              <span className="text-sm text-muted-foreground">
                © 2026 CarbonScan AI · NSC 2026 หมวด 14
              </span>
            </div>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <Link href="/about" className="hover:text-foreground">
                About
              </Link>
              <Link href="https://github.com/Remote55/carbonscan-ai" className="hover:text-foreground">
                GitHub
              </Link>
              <Link href="/privacy" className="hover:text-foreground">
                Privacy
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
