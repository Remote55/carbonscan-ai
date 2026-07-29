import Link from 'next/link';
import {
  ArrowRight,
  Leaf,
  ShieldCheck,
  Boxes,
  Scale,
  Upload,
  ScanLine,
  Calculator,
  BadgeCheck,
  Github,
} from 'lucide-react';

import { CORE_DEMO_EVIDENCE } from '@/generated/core-demo-evidence';

const script = { fontFamily: 'var(--font-pacifico)' } as const;
const { baseline, candidate } = CORE_DEMO_EVIDENCE;
const { wanHeldOut, demol65 } = CORE_DEMO_EVIDENCE.validation;

const FEATURES = [
  {
    icon: Leaf,
    title: 'Evidence-gated Wood–Leaf Segmentation',
    desc: `ใช้ ${baseline.backend} เป็น baseline ที่รันซ้ำได้ ส่วน ${candidate.displayName} ยังเป็น ${candidate.status} (Wan held-out: Wood IoU ${wanHeldOut.woodIoU}, Leaf IoU ${wanHeldOut.leafIoU})`,
  },
  {
    icon: ShieldCheck,
    title: 'Anti-Fraud — Planned',
    desc: 'การตรวจ EXIF, GPS และภาพซ้ำเป็น roadmap ยังไม่ใช่ความสามารถที่ผ่านการทดสอบใน prototype นี้',
  },
  {
    icon: Boxes,
    title: 'ตรวจสอบผลแบบ 3D',
    desc: '3D Viewer ใช้งานได้แล้ว ส่วน GIS และการผูกหลักฐานเชิงพื้นที่แบบครบวงจรยังเป็น Planned',
  },
  {
    icon: Scale,
    title: 'Allometric Carbon Estimate',
    desc: 'คำนวณชีวมวล คาร์บอน และ CO₂e ด้วย species_db.csv หรือ Chave fallback; ไม่ใช่การรับรอง carbon credit',
  },
];

const STEPS = [
  {
    icon: Upload,
    k: '01',
    title: 'อัปโหลด Point Cloud',
    desc: 'รับไฟล์ .las/.laz/.ply; เส้นทางถ่ายภาพมือถือและ photogrammetry ยังเป็น Planned',
  },
  {
    icon: ScanLine,
    k: '02',
    title: 'แยกลำต้น–ใบ + วัด',
    desc: 'tlsep baseline แยก wood/leaf แล้ววัด DBH ด้วย RANSAC, ความสูงจาก max-Z และ volume แบบ taper; PointNet++ ยัง Experimental',
  },
  {
    icon: Calculator,
    k: '03',
    title: 'คำนวณคาร์บอน',
    desc: 'แทนค่าลงสมการแอลโลเมตริก → ชีวมวลเหนือ/ใต้ดิน → คาร์บอน ×0.47 → CO₂e ×44/12',
  },
  {
    icon: BadgeCheck,
    k: '04',
    title: 'ตรวจสอบผล',
    desc: 'ดูผลและ provenance ใน 3D viewer; Marketplace, Payment และ Certificate ยังเป็น Planned',
  },
];

const METRICS = [
  {
    n: String(wanHeldOut.woodIoU),
    u: '',
    l: `Wood IoU · ${candidate.status} ${candidate.displayName} · Wan held-out`,
  },
  {
    n: String(wanHeldOut.leafIoU),
    u: '',
    l: `Leaf IoU · ${candidate.status} ${candidate.displayName} · Wan held-out`,
  },
  { n: String(demol65.dbhMaeCm), u: 'ซม.', l: 'DBH MAE · Demol isolated-tree · 65 ต้น' },
  { n: String(demol65.volumeMapePct), u: '%', l: 'Volume MAPE · Demol isolated-tree · 65 ต้น' },
];

const NAV = [
  { href: '#tech', label: 'เทคโนโลยี' },
  { href: '#how', label: 'วิธีทำงาน' },
  { href: '#proof', label: 'งานวิจัย' },
  { href: '/dashboard/viewer', label: '3D Viewer' },
];

/** Decorative out-of-focus leaf (nature-template accent). */
function LeafBlob({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true" fill="none">
      <path
        fill="currentColor"
        d="M50 4C70 24 88 44 88 66c0 18-16 30-38 30S12 84 12 66C12 44 30 24 50 4Z"
      />
      <path
        stroke="currentColor"
        strokeOpacity=".55"
        strokeWidth="2.5"
        strokeLinecap="round"
        d="M50 16v70M50 42l20-14M50 60l22-16M50 42 30 28M50 60 28 44"
      />
    </svg>
  );
}

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#fbfaf6] font-sans text-forest-900 antialiased">
      {/* ─────────────── HERO ─────────────── */}
      <section className="relative isolate flex min-h-[92vh] flex-col overflow-hidden">
        {/* illustrated forest dusk backdrop */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-b from-[#04140d] via-[#0b2b1d] to-[#17462f]" />
          {/* sun glow */}
          <div className="absolute left-1/2 top-[42%] h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(190,242,170,.45),rgba(120,220,150,.12)_45%,transparent_68%)] blur-2xl" />
          {/* layered hills + pines */}
          <svg
            className="absolute inset-0 h-full w-full"
            viewBox="0 0 1440 900"
            preserveAspectRatio="xMidYMid slice"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M0,470 C240,435 480,455 720,450 C960,445 1200,462 1440,448 L1440,900 L0,900 Z"
              fill="#123f2a"
              fillOpacity=".85"
            />
            <path
              d="M0,528 C260,498 520,518 780,514 C1040,510 1240,528 1440,520 L1440,900 L0,900 Z"
              fill="#0c3220"
            />
            <path
              d="M0,588 C300,562 560,582 820,578 C1080,574 1280,592 1440,584 L1440,900 L0,900 Z"
              fill="#071f14"
            />
            {/* pines on the near ridge */}
            <g fill="#05170e">
              <path d="M205,588 l-16,0 l16,-38 l16,38 z" />
              <path d="M235,588 l-11,0 l11,-26 l11,26 z" />
              <path d="M1040,586 l-18,0 l18,-42 l18,42 z" />
              <path d="M1075,586 l-12,0 l12,-28 l12,28 z" />
              <path d="M1260,588 l-14,0 l14,-32 l14,32 z" />
            </g>
          </svg>
          {/* mist */}
          <div className="absolute left-0 top-[48%] h-32 w-full bg-[radial-gradient(60%_100%_at_50%_50%,rgba(200,240,210,.16),transparent_70%)] blur-xl" />
          {/* grain */}
          <div
            className="absolute inset-0 opacity-40 mix-blend-overlay"
            style={{
              backgroundImage:
                "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.5'/%3E%3C/svg%3E\")",
            }}
          />
          {/* readability scrim */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#04140d]/85 via-[#04140d]/40 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#fbfaf6] to-transparent" />
        </div>

        {/* decorative leaves */}
        <LeafBlob className="pointer-events-none absolute -left-16 top-24 h-64 w-64 rotate-[18deg] text-forest-400/30 blur-[2px]" />
        <LeafBlob className="pointer-events-none absolute -right-10 bottom-32 h-52 w-52 -rotate-[150deg] text-forest-300/25 blur-[3px]" />

        {/* nav */}
        <header className="relative z-20">
          <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="bg-forest-gradient grid h-9 w-9 place-items-center rounded-xl shadow-lg shadow-black/30 ring-1 ring-white/10">
                <Leaf className="h-5 w-5 text-white" />
              </span>
              <span className="text-lg font-bold tracking-tight text-white">
                TreeQ<span className="text-forest-300"> Carbon</span>
              </span>
            </Link>
            <div className="hidden items-center gap-8 text-sm font-medium text-white/75 md:flex">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="transition hover:text-white">
                  {n.label}
                </Link>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="hidden text-sm font-medium text-white/75 transition hover:text-white sm:block"
              >
                เข้าสู่ระบบ
              </Link>
              <Link
                href="/demo"
                className="inline-flex items-center gap-1.5 rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-forest-800 shadow-lg shadow-black/20 transition hover:bg-forest-50"
              >
                ดูเดโม <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </nav>
        </header>

        {/* hero copy */}
        <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 items-center px-6">
          <div className="max-w-2xl py-16">
            <p style={script} className="animate-fade-in text-2xl text-forest-300 sm:text-3xl">
              Nature, measured.
            </p>
            <h1 className="mt-3 animate-slide-up text-5xl font-extrabold leading-[1.06] tracking-tight text-white sm:text-6xl lg:text-7xl">
              ประเมินการกักเก็บ{' '}
              <span className="bg-gradient-to-r from-forest-300 via-emerald-200 to-lime-200 bg-clip-text text-transparent">
                คาร์บอนจากต้นไม้
              </span>{' '}
              ด้วย AI ที่โปร่งใส
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/80">
              แพลตฟอร์มประเมินชีวมวล คาร์บอน และ CO₂e จาก 3D point cloud พร้อม provenance ของ
              pipeline การรับรองและออก carbon credit อย่างเป็นทางการอยู่นอกขอบเขต prototype นี้
            </p>
            {/* The demo leads, because it is the only route that shows real
                results without an account. Signup led here before, which meant
                anyone arriving to evaluate the work hit a login wall first and
                had no way to discover /demo at all. */}
            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/demo"
                className="inline-flex h-12 items-center gap-2 rounded-full bg-gradient-to-b from-forest-400 to-forest-600 px-7 text-base font-semibold text-white shadow-xl shadow-forest-900/40 transition hover:-translate-y-0.5 hover:shadow-2xl hover:shadow-forest-900/50"
              >
                ดูผลจริง ไม่ต้องสมัคร <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/signup"
                className="inline-flex h-12 items-center rounded-full border border-white/25 bg-white/5 px-7 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/10"
              >
                สมัครใช้งาน
              </Link>
            </div>
            <dl className="mt-12 flex flex-wrap gap-x-10 gap-y-5">
              {[
                { n: String(wanHeldOut.woodIoU), l: `Wood IoU · ${candidate.status} / Wan` },
                { n: String(wanHeldOut.leafIoU), l: `Leaf IoU · ${candidate.status} / Wan` },
                { n: `${demol65.dbhMaeCm} ซม.`, l: 'DBH MAE · Demol 65 ต้น' },
              ].map((s) => (
                <div key={s.l} className="border-l border-white/15 pl-4 first:border-0 first:pl-0">
                  <dt className="font-display text-3xl font-bold tabular-nums text-white">{s.n}</dt>
                  <dd className="mt-1 text-xs text-white/60">{s.l}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* ─────────────── TECHNOLOGY ─────────────── */}
      <section id="tech" className="bg-[#fbfaf6] py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="max-w-2xl">
            <p style={script} className="text-xl text-forest-500">
              Our technology
            </p>
            <h2 className="mt-1 text-4xl font-bold tracking-tight text-forest-900 sm:text-5xl">
              เทคโนโลยีที่ขับเคลื่อน
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-forest-900/55">
              ผสาน 3D point-cloud processing, deep learning และ cloud architecture ในไปป์ไลน์เดียว
            </p>
          </div>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group rounded-3xl border border-forest-100 bg-white p-7 shadow-sm transition duration-300 hover:-translate-y-1.5 hover:border-forest-200 hover:shadow-xl hover:shadow-forest-900/5"
              >
                <div className="group-hover:bg-forest-gradient grid h-12 w-12 place-items-center rounded-2xl bg-forest-50 text-forest-600 transition duration-300 group-hover:text-white">
                  <f.icon className="h-6 w-6" strokeWidth={1.7} />
                </div>
                <h3 className="mt-5 font-semibold text-forest-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-forest-900/55">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─────────────── PIPELINE ─────────────── */}
      <section id="how" className="border-y border-forest-100 bg-forest-50/50 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="max-w-2xl">
            <p style={script} className="text-xl text-forest-500">
              How it works
            </p>
            <h2 className="mt-1 text-4xl font-bold tracking-tight text-forest-900 sm:text-5xl">
              จากต้นไม้ สู่ตัวเลขที่ตรวจสอบได้
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-forest-900/55">
              สี่ขั้นตอนตั้งแต่ข้อมูลดิบถึงค่าประเมินคาร์บอน โดยแยกสิ่งที่ทำได้แล้วออกจาก roadmap
            </p>
          </div>
          <ol className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s) => (
              <li
                key={s.k}
                className="relative rounded-3xl bg-white p-7 shadow-sm ring-1 ring-forest-100"
              >
                <div className="flex items-center justify-between">
                  <span className="font-display text-4xl font-bold text-forest-200">{s.k}</span>
                  <span className="bg-forest-gradient grid h-11 w-11 place-items-center rounded-xl text-white shadow-md shadow-forest-900/20">
                    <s.icon className="h-5 w-5" strokeWidth={1.7} />
                  </span>
                </div>
                <h3 className="mt-5 font-semibold text-forest-900">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-forest-900/55">{s.desc}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ─────────────── VALIDATION ─────────────── */}
      <section id="proof" className="bg-forest-gradient relative overflow-hidden py-24 text-white">
        <LeafBlob className="pointer-events-none absolute -right-16 -top-10 h-72 w-72 rotate-[200deg] text-white/10" />
        <LeafBlob className="pointer-events-none absolute -left-12 bottom-0 h-56 w-56 text-black/10" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="max-w-2xl">
            <p style={script} className="text-xl text-forest-200">
              Evidence with limitations
            </p>
            <h2 className="mt-1 text-4xl font-bold tracking-tight sm:text-5xl">
              หลักฐานบนข้อมูลต้นไม้จริง
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/70">
              รายงานผลแยก wood/leaf บน Wan held-out และ geometry บน Demol isolated-tree 65
              ต้นตามขอบเขตที่ทดสอบจริง
            </p>
          </div>
          <div className="mt-14 grid grid-cols-2 gap-x-6 gap-y-10 lg:grid-cols-4">
            {METRICS.map((m) => (
              <div key={m.l} className="border-l border-white/20 pl-5">
                <div className="font-display text-5xl font-bold tabular-nums text-white">
                  {m.n}
                  {m.u && <span className="ml-1 text-xl font-medium text-white/60">{m.u}</span>}
                </div>
                <div className="mt-2 text-sm leading-snug text-white/70">{m.l}</div>
              </div>
            ))}
          </div>
          <p className="mt-12 max-w-3xl text-sm leading-relaxed text-white/60">
            ฐานสมการ allometric มีข้อมูล 5 ชนิดและใช้ Chave et al. (2014) เป็น fallback แต่ species
            classifier ยังเป็น Stub และผล Demol ข้างต้นไม่ใช่การ validate biomass, carbon หรือ
            carbon credit
          </p>
        </div>
      </section>

      {/* ─────────────── CTA ─────────────── */}
      <section className="bg-[#fbfaf6] px-6 py-24">
        <div className="relative mx-auto max-w-4xl overflow-hidden rounded-[2.5rem] bg-forest-900 px-8 py-16 text-center text-white shadow-2xl shadow-forest-900/20">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-[radial-gradient(60%_120%_at_50%_0%,rgba(124,229,156,.25),transparent_70%)]" />
          <div className="relative">
            <p style={script} className="text-2xl text-forest-300">
              Ready when you are
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
              พร้อมเปลี่ยนต้นไม้ให้เป็นตัวเลขที่ตรวจสอบที่มาได้?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-white/70">
              เปิดดู 3D viewer และหลักฐานของ core demo ได้ โดยความสามารถที่ยังเป็น
              Experimental/Planned จะระบุไว้ตรงไปตรงมา
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                href="/signup"
                className="inline-flex h-12 items-center gap-2 rounded-full bg-white px-7 text-base font-semibold text-forest-800 shadow-lg transition hover:-translate-y-0.5 hover:bg-forest-50"
              >
                เริ่มใช้ฟรี <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/dashboard/viewer"
                className="inline-flex h-12 items-center rounded-full border border-white/25 px-7 text-base font-semibold text-white transition hover:bg-white/10"
              >
                ทดลอง 3D Viewer
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────── FOOTER ─────────────── */}
      <footer className="bg-[#06180f] py-10 text-white/60">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="bg-forest-gradient grid h-8 w-8 place-items-center rounded-lg">
              <Leaf className="h-4 w-4 text-white" />
            </span>
            <span className="text-sm font-semibold text-white">
              TreeQ<span className="text-forest-300"> Carbon</span>
            </span>
          </div>
          <span className="text-xs">© 2026 TreeQ Carbon Platform · NSC 2026 หมวด 14</span>
          <Link
            href="https://github.com/Remote55/carbonscan-ai"
            className="inline-flex items-center gap-1.5 text-sm transition hover:text-white"
          >
            <Github className="h-4 w-4" /> GitHub
          </Link>
        </div>
      </footer>
    </main>
  );
}
