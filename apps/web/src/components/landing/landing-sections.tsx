"use client";

/**
 * LandingSections — the dark "night-forest" body that continues below
 * <CarbonHero />: Technology, How-it-works pipeline, validation metrics,
 * a closing CTA, and the footer. Deliberately single-theme (branded dark)
 * to stay cohesive with the luminous point-cloud hero.
 *
 * Content mirrors the real project claims (IoU 0.61, ±1.17 cm DBH, TGO
 * allometrics) so the marketing surface stays honest.
 */
import Link from "next/link";
import {
  Leaf,
  ShieldCheck,
  Boxes,
  Scale,
  Upload,
  ScanLine,
  Calculator,
  BadgeCheck,
  ArrowRight,
  Github,
} from "lucide-react";

const FEATURES = [
  { icon: Leaf, title: "AI Wood–Leaf Segmentation", desc: "PointNet++ แยกลำต้นออกจากใบ ก่อนวัดขนาด — Mean IoU 0.61 บนไม้จริง (Wan et al. 2021)" },
  { icon: ShieldCheck, title: "Anti-Fraud โดยออกแบบ", desc: "ยึด GPS ละเอียด 6 ตำแหน่งทศนิยม + ตรวจ EXIF + กันภาพซ้ำฝั่งเซิร์ฟเวอร์" },
  { icon: Boxes, title: "ตรวจสอบได้จริงแบบ 3D", desc: "เปิดดูทุกต้นที่สนับสนุนได้ผ่าน 3D Viewer + หมุดพิกัดบนแผนที่ GPS" },
  { icon: Scale, title: "มาตรฐาน TGO", desc: "คำนวณด้วยสมการแอลโลเมตริกมาตรฐาน แปลงขนาดต้นไม้ → ชีวมวล → คาร์บอน → CO₂e" },
];

const STEPS = [
  { icon: Upload, k: "01", title: "อัปโหลด หรือ ถ่ายภาพ", desc: "รับไฟล์ LiDAR .las/.laz จากออดิเตอร์ หรือถ่ายภาพมือถือ 30–50 รูปรอบต้น" },
  { icon: ScanLine, k: "02", title: "AI แยกลำต้น–ใบ + วัด", desc: "Segment wood/leaf แล้ววัด DBH (ระดับอก 1.3 ม.) และความสูงด้วย QSM cylinder-fit" },
  { icon: Calculator, k: "03", title: "คำนวณคาร์บอน", desc: "แทนค่าลงสมการแอลโลเมตริก → ชีวมวลเหนือ/ใต้ดิน → คาร์บอน 0.47 → CO₂e ×44/12" },
  { icon: BadgeCheck, k: "04", title: "ตรวจสอบ & จับคู่", desc: "เปิดผลแบบโปร่งใสใน 3D viewer แล้วจับคู่ B2B carbon offset ให้องค์กร" },
];

const METRICS = [
  { n: "0.61", u: "", l: "Wood/Leaf IoU\nบนไม้จริง" },
  { n: "±1.17", u: "ซม.", l: "ค่าคลาดเคลื่อน DBH\nเทียบไม้โค่นจริง" },
  { n: "100", u: "×", l: "ลดต้นทุน\nการประเมิน" },
  { n: "<10", u: "นาที", l: "เวลาประมวลผล\nต่อแปลง" },
];

export default function LandingSections() {
  return (
    <div className="lp">
      {/* ── Technology ─────────────────────────────── */}
      <section id="tech" className="sec">
        <header className="head">
          <span className="eyebrow"><span className="dot" />TECHNOLOGY</span>
          <h2>เทคโนโลยีที่<span className="em"> ขับเคลื่อน</span></h2>
          <p className="lead">ผสาน 3D point-cloud processing, deep learning และ cloud architecture ในไปป์ไลน์เดียว</p>
        </header>
        <div className="grid feats">
          {FEATURES.map((f) => (
            <article key={f.title} className="card">
              <span className="ico"><f.icon size={20} strokeWidth={1.6} /></span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ── How it works ──────────────────────────── */}
      <section id="how" className="sec">
        <header className="head">
          <span className="eyebrow"><span className="dot" />PIPELINE</span>
          <h2>จากต้นไม้ <span className="em">สู่ตัวเลขที่ตรวจสอบได้</span></h2>
          <p className="lead">สี่ขั้นตอน โปร่งใสทุกจุด ตั้งแต่ข้อมูลดิบจนถึงคาร์บอนเครดิต</p>
        </header>
        <ol className="grid steps">
          {STEPS.map((s) => (
            <li key={s.k} className="step">
              <div className="stepTop">
                <span className="num">{s.k}</span>
                <span className="ico sm"><s.icon size={18} strokeWidth={1.6} /></span>
              </div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ── Validation / proof ────────────────────── */}
      <section id="research" className="sec proof">
        <header className="head">
          <span className="eyebrow"><span className="dot" />VALIDATION</span>
          <h2>พิสูจน์ด้วย<span className="em"> ไม้จริง</span></h2>
          <p className="lead">ไม่ใช่แค่เดโม — วัดกับข้อมูลไม้โค่นจริงและชุดข้อมูลงานวิจัยที่เปิดสาธารณะ</p>
        </header>
        <div className="metrics">
          {METRICS.map((m) => (
            <div key={m.l} className="metric">
              <div className="mn">{m.n}<small>{m.u}</small></div>
              <div className="ml">{m.l}</div>
            </div>
          ))}
        </div>
        <p className="foot-note">
          รองรับไม้เศรษฐกิจ 5 ชนิด (สัก · ยางนา · ไผ่ · ยางพารา · มะค่าโมง) — ประเมิน biomass ด้วยสมการ
          Chave et al. (2014) และมาตรฐาน TGO/IPCC
        </p>
      </section>

      {/* ── CTA ───────────────────────────────────── */}
      <section className="cta">
        <div className="ctaInner">
          <h2>พร้อมเปลี่ยนต้นไม้<br /><span className="em">ให้เป็นตัวเลขที่เชื่อถือได้?</span></h2>
          <p className="lead">เริ่มฟรีสำหรับชุมชน ไม่ต้องใช้บัตรเครดิต พร้อมใช้ใน 5 นาที</p>
          <div className="btns">
            <Link className="btn primary" href="/signup">เริ่มใช้ฟรี<ArrowRight size={18} /></Link>
            <Link className="btn ghost" href="/dashboard/viewer">ทดลอง 3D Viewer</Link>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────── */}
      <footer className="foot">
        <div className="brand"><span className="mark" /><b>CarbonScan<i> AI</i></b></div>
        <span className="copy">© 2026 CarbonScan AI · NSC 2026 หมวด 14</span>
        <Link className="gh" href="https://github.com/Remote55/carbonscan-ai"><Github size={16} />GitHub</Link>
      </footer>

      <style jsx>{`
        .lp{
          --serif:var(--font-fraunces),"Hoefler Text","Iowan Old Style",Georgia,serif;
          --thai:var(--font-sarabun),"Noto Sans Thai","Leelawadee UI",Tahoma,sans-serif;
          --mono:var(--font-jetbrains-mono),ui-monospace,"SF Mono",Consolas,monospace;
          --ink:#EAF3EC;--muted:#9DB3A6;--dim:#6E877A;--mint:#86EFAC;--bright:#C6FFDB;
          --line:rgba(180,240,205,.10);
          position:relative;color:var(--ink);font-family:var(--thai);
          background:linear-gradient(180deg,#04100b 0%,#061a12 40%,#04120c 100%);
          padding-top:1px;
        }
        .sec{max-width:1180px;margin:0 auto;padding:clamp(64px,9vw,120px) clamp(20px,5vw,72px);}
        .head{max-width:640px;}
        .eyebrow{display:inline-flex;align-items:center;gap:9px;font-family:var(--mono);font-size:11.5px;
          letter-spacing:.26em;text-transform:uppercase;color:var(--mint);padding:6px 13px;border-radius:999px;
          border:1px solid var(--line);background:rgba(134,239,172,.04);}
        .dot{width:6px;height:6px;border-radius:50%;background:var(--mint);box-shadow:0 0 10px var(--mint);}
        h2{font-family:var(--serif);font-weight:600;letter-spacing:-.015em;line-height:1.05;
          font-size:clamp(30px,4.4vw,52px);margin:20px 0 0;text-wrap:balance;color:#F3FBF4;}
        .em{font-style:italic;background:linear-gradient(120deg,#7CF29C,#C6FFDB 60%,#4FD08A);
          -webkit-background-clip:text;background-clip:text;color:transparent;}
        .lead{font-size:clamp(15px,1.5vw,18px);line-height:1.7;color:var(--muted);margin:18px 0 0;max-width:34em;}
        .grid{display:grid;gap:18px;margin-top:clamp(40px,6vw,64px);}
        .feats{grid-template-columns:repeat(4,1fr);}
        .steps{grid-template-columns:repeat(4,1fr);list-style:none;padding:0;counter-reset:none;}
        @media(max-width:900px){.feats{grid-template-columns:repeat(2,1fr);}.steps{grid-template-columns:repeat(2,1fr);}}
        @media(max-width:560px){.feats,.steps{grid-template-columns:1fr;}}

        .card{position:relative;border:1px solid var(--line);border-radius:18px;padding:26px 24px;
          background:linear-gradient(180deg,rgba(134,239,172,.045),rgba(4,16,11,.2));
          transition:transform .3s cubic-bezier(.2,.7,.2,1),border-color .3s,box-shadow .3s;overflow:hidden;}
        .card::after{content:"";position:absolute;inset:0;border-radius:18px;pointer-events:none;
          background:radial-gradient(120% 80% at 50% -10%,rgba(134,239,172,.12),transparent 60%);opacity:0;transition:opacity .3s;}
        .card:hover{transform:translateY(-4px);border-color:rgba(134,239,172,.32);box-shadow:0 22px 48px -24px rgba(80,220,140,.5);}
        .card:hover::after{opacity:1;}
        .ico{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:13px;
          color:#05261a;background:linear-gradient(180deg,#9CF7B9,#5FD693);
          box-shadow:0 8px 22px -8px rgba(120,240,160,.6),inset 0 1px 0 rgba(255,255,255,.4);}
        .ico.sm{width:38px;height:38px;border-radius:11px;}
        .card h3,.step h3{font-family:var(--serif);font-weight:600;font-size:19px;color:#EEFBF0;margin:18px 0 0;letter-spacing:-.01em;}
        .card p,.step p{font-size:13.5px;line-height:1.62;color:var(--muted);margin:9px 0 0;}

        .step{position:relative;border:1px solid var(--line);border-radius:18px;padding:24px 22px;
          background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(4,16,11,.15));}
        .stepTop{display:flex;align-items:center;justify-content:space-between;}
        .num{font-family:var(--mono);font-size:26px;font-weight:600;color:transparent;
          -webkit-text-stroke:1px rgba(134,239,172,.5);letter-spacing:.02em;}

        .proof{text-align:left;}
        .metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:clamp(40px,6vw,60px);
          background:var(--line);border:1px solid var(--line);border-radius:20px;overflow:hidden;}
        .metric{background:#050f0b;padding:34px 20px;text-align:center;}
        .mn{font-family:var(--serif);font-size:clamp(34px,4.6vw,52px);line-height:1;color:var(--bright);
          font-variant-numeric:tabular-nums;letter-spacing:-.02em;}
        .mn small{font-family:var(--thai);font-size:.42em;color:var(--dim);margin-left:3px;letter-spacing:0;}
        .ml{font-size:12.5px;color:var(--muted);margin-top:12px;white-space:pre-line;line-height:1.5;}
        @media(max-width:760px){.metrics{grid-template-columns:repeat(2,1fr);}}
        .foot-note{font-size:13px;color:var(--dim);margin-top:22px;line-height:1.65;max-width:52em;}

        .cta{border-top:1px solid var(--line);position:relative;overflow:hidden;}
        .cta::before{content:"";position:absolute;inset:0;pointer-events:none;
          background:radial-gradient(70% 120% at 50% 0%,rgba(96,220,140,.16),transparent 60%);}
        .ctaInner{position:relative;max-width:760px;margin:0 auto;padding:clamp(64px,9vw,110px) clamp(20px,5vw,48px);text-align:center;}
        .cta h2{font-size:clamp(30px,4.8vw,54px);}
        .cta .lead{margin-left:auto;margin-right:auto;}
        .btns{display:flex;flex-wrap:wrap;gap:14px;justify-content:center;margin-top:36px;}
        .btn{display:inline-flex;align-items:center;gap:8px;font-family:var(--thai);font-size:15px;font-weight:600;
          border-radius:13px;padding:15px 26px;text-decoration:none;border:1px solid transparent;
          transition:transform .2s,box-shadow .3s,background .3s,border-color .3s;}
        .primary{color:#05261a;background:linear-gradient(180deg,#9CF7B9,#5FD693);
          box-shadow:0 12px 34px -12px rgba(120,240,160,.7),inset 0 1px 0 rgba(255,255,255,.4);}
        .primary:hover{transform:translateY(-2px);box-shadow:0 20px 46px -14px rgba(120,240,160,.85);}
        .ghost{color:var(--ink);border-color:var(--line);background:rgba(255,255,255,.02);}
        .ghost:hover{border-color:rgba(134,239,172,.4);background:rgba(134,239,172,.07);}

        .foot{border-top:1px solid var(--line);max-width:1180px;margin:0 auto;
          padding:30px clamp(20px,5vw,72px);display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;}
        .brand{display:flex;align-items:center;gap:11px;font-weight:600;}
        .mark{width:26px;height:26px;border-radius:8px;position:relative;
          background:conic-gradient(from 210deg,#2D6A4F,#86EFAC,#2D6A4F);box-shadow:0 0 16px rgba(134,239,172,.4);}
        .mark::after{content:"";position:absolute;inset:5px;border-radius:4px;background:#04100b;}
        .brand b{font-family:var(--serif);font-weight:600;font-size:16px;}
        .brand b i{font-style:normal;color:var(--mint);}
        .copy{font-size:12.5px;color:var(--dim);}
        .gh{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--muted);text-decoration:none;transition:color .25s;}
        .gh:hover{color:var(--ink);}

        @media(prefers-reduced-motion:reduce){.card{transition:none;}}
      `}</style>
    </div>
  );
}
