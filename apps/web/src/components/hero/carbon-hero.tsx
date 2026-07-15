"use client";

/**
 * CarbonHero — landing hero with a rotating luminous point-cloud tree.
 *
 * The tree is rendered on a <canvas> as a real 3D point cloud (wood = amber,
 * leaf = mint), rotated + projected every frame. This mirrors the product:
 * CarbonScan segments wood/leaf point clouds to estimate biomass carbon.
 *
 * Drop-in: <CarbonHero /> — self-contained (styled-jsx), no external deps.
 * Swap the copy/stats below for your own. Respects prefers-reduced-motion.
 */
import { useEffect, useRef } from "react";

type Pt = {
  x: number; y: number; z: number; k: number; li: number;
  _x: number; _y: number; _z: number; _n: number; _sc: number;
};
type Mote = { x: number; y: number; vy: number; sz: number; ph: number; sp: number };

export default function CarbonHero() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const cv = canvasRef.current;
    if (!cv) return;
    const ctx = cv.getContext("2d");
    if (!ctx) return;

    const reduce = window.matchMedia("(prefers-reduced-motion:reduce)").matches;
    let W = 0, H = 0, DPR = 1;
    const resize = () => {
      DPR = Math.min(2, window.devicePixelRatio || 1);
      W = cv.clientWidth; H = cv.clientHeight;
      cv.width = W * DPR; cv.height = H * DPR;
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const sprite = (inner: string, mid: string, size: number) => {
      const c = document.createElement("canvas");
      c.width = c.height = size;
      const g = c.getContext("2d")!;
      const r = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
      r.addColorStop(0, inner); r.addColorStop(0.42, mid); r.addColorStop(1, "rgba(0,0,0,0)");
      g.fillStyle = r; g.beginPath(); g.arc(size / 2, size / 2, size / 2, 0, 7); g.fill();
      return c;
    };
    const SP = {
      wood: sprite("rgba(214,182,120,.9)", "rgba(120,150,86,.28)", 26),
      leaf: [
        sprite("rgba(41,110,78,.85)", "rgba(24,64,48,.2)", 30),
        sprite("rgba(96,206,138,.9)", "rgba(44,120,82,.24)", 30),
        sprite("rgba(168,255,196,.98)", "rgba(96,232,154,.26)", 30),
      ],
    };

    const rnd = (a: number, b: number) => a + Math.random() * (b - a);
    const pts: Pt[] = [];
    const push = (x: number, y: number, z: number, k: number, li: number) =>
      pts.push({ x, y, z, k, li, _x: 0, _y: 0, _z: 0, _n: 0, _sc: 0 });

    // trunk
    for (let i = 0; i < 300; i++) {
      const t = Math.pow(Math.random(), 0.7), y = -0.52 + t * 0.58;
      const rr = 0.04 * (1 - t * 0.55) * (0.5 + 0.6 * Math.random()), a = Math.random() * 6.283;
      push(Math.cos(a) * rr, y, Math.sin(a) * rr, 0, 0);
    }
    // branches
    for (let b = 0; b < 7; b++) {
      const by = rnd(-0.06, 0.16), az = rnd(0, 6.283), el = rnd(0.32, 0.92), ln = rnd(0.24, 0.46), sg = 30;
      for (let s = 0; s < sg; s++) {
        const tt = s / sg;
        push(
          Math.cos(az) * ln * tt * Math.cos(el) + rnd(-0.02, 0.02),
          by + ln * tt * Math.sin(el) + rnd(-0.02, 0.02),
          Math.sin(az) * ln * tt * Math.cos(el) + rnd(-0.02, 0.02), 0, 0
        );
      }
    }
    // canopy (leaf cloud) — a few lobes
    const lobes = [
      [0, 0.30, 0, 0.52, 0.44, 0.52], [-0.2, 0.16, 0.12, 0.28, 0.26, 0.26],
      [0.22, 0.2, -0.12, 0.3, 0.26, 0.28], [0, 0.5, 0, 0.26, 0.22, 0.26],
    ];
    for (let i = 0; i < 2700; i++) {
      const L = lobes[(Math.random() * lobes.length) | 0];
      const u = Math.random(), v = Math.random(), th = u * 6.283, ph = Math.acos(2 * v - 1), ra = Math.pow(Math.random(), 0.42);
      const x = L[0] + L[3] * ra * Math.sin(ph) * Math.cos(th);
      const y = L[1] + L[4] * ra * Math.cos(ph);
      const z = L[2] + L[5] * ra * Math.sin(ph) * Math.sin(th);
      const h = (y - 0.02) / 0.7;
      let li = h + ra * 0.5 + Math.random() * 0.4;
      li = li < 0.5 ? 0 : li < 1.05 ? 1 : 2;
      push(x, y, z, 1, li);
    }

    const motes: Mote[] = [];
    for (let i = 0; i < 34; i++)
      motes.push({ x: Math.random(), y: Math.random(), vy: rnd(0.006, 0.02), sz: rnd(2, 5), ph: Math.random() * 6.283, sp: rnd(0.6, 1.6) });

    let ang = 0, mx = 0, my = 0, tx = 0, ty = 0, raf = 0;
    const t0 = performance.now();
    const onMove = (e: PointerEvent) => { mx = e.clientX / window.innerWidth - 0.5; my = e.clientY / window.innerHeight - 0.5; };
    window.addEventListener("pointermove", onMove);

    const frame = (now: number) => {
      const t = (now - t0) / 1000;
      if (!reduce) ang += 0.0024;
      tx += (mx - tx) * 0.05; ty += (my - ty) * 0.05;
      ctx.clearRect(0, 0, W, H);
      const cxp = W * 0.63 + tx * 46, cyp = H * 0.55 + ty * 26, base = Math.min(W, H);

      ctx.globalCompositeOperation = "source-over";
      const gg = ctx.createRadialGradient(cxp, cyp, 0, cxp, cyp, base * 0.55);
      gg.addColorStop(0, "rgba(72,206,128,.16)"); gg.addColorStop(0.5, "rgba(30,120,72,.06)"); gg.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = gg; ctx.fillRect(0, 0, W, H);

      ctx.globalCompositeOperation = "lighter";
      const S = base * 0.6 * (1 + (reduce ? 0 : 0.018) * Math.sin(t * 0.8)), FOV = 2.4, tilt = 0.14 + ty * 0.16;
      const ca = Math.cos(ang), sa = Math.sin(ang), ct = Math.cos(tilt), st = Math.sin(tilt);
      for (const p of pts) {
        const x = p.x * ca - p.z * sa, z = p.x * sa + p.z * ca, y = p.y;
        const y2 = y * ct - z * st, z2 = y * st + z * ct; p._z = z2;
        const sc = FOV / (FOV + z2 * 1.25);
        p._x = cxp + x * sc * S; p._y = cyp - y2 * sc * S; p._n = (z2 + 0.7) / 1.4; p._sc = sc;
      }
      pts.sort((a, b) => a._z - b._z);
      const scl = S / (base * 0.6);
      for (const p of pts) {
        const n = p._n < 0 ? 0 : p._n > 1 ? 1 : p._n;
        const spr = p.k === 0 ? SP.wood : SP.leaf[p.li];
        const sz = (p.k === 0 ? 8 : 11) * (0.4 + n) * p._sc * scl;
        ctx.globalAlpha = (0.2 + 0.8 * n) * (p.k === 0 ? 0.9 : 1);
        ctx.drawImage(spr, p._x - sz / 2, p._y - sz / 2, sz, sz);
      }
      for (const m of motes) {
        if (!reduce) { m.y -= m.vy * 0.012; if (m.y < -0.05) { m.y = 1.05; m.x = Math.random(); } }
        const tw = reduce ? 0.5 : 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * m.sp + m.ph));
        ctx.globalAlpha = tw * 0.6;
        const sz = m.sz * (reduce ? 1 : 1 + 0.3 * Math.sin(t + m.ph));
        ctx.drawImage(SP.leaf[2], m.x * W - sz * 1.5, m.y * H - sz * 1.5, sz * 3, sz * 3);
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
    };
  }, []);

  return (
    <div className="wrap">
      <nav className="nav">
        <div className="brand"><span className="mark" /><b>CarbonScan<i> AI</i></b></div>
        <ul>
          <li><a href="#tech">เทคโนโลยี</a></li>
          <li><a href="#research">งานวิจัย</a></li>
          <li><a href="/dashboard/viewer">3D Viewer</a></li>
        </ul>
        <a className="pill" href="/login">เข้าสู่ระบบ</a>
      </nav>

      <canvas ref={canvasRef} className="scene" />
      <div className="grain" />
      <div className="vignette" />

      <section className="hero">
        <div className="copy">
          <span className="eyebrow rise d1"><span className="dot" />NSC 2026 · FOREST MEETS CODE</span>
          <h1 className="rise d2">Every tree holds<br />a number —<br /><span className="em">we make it&nbsp;glow.</span></h1>
          <p className="sub rise d3">
            แพลตฟอร์มวัดคาร์บอนชีวมวลต้นไม้จาก 3D point cloud ด้วย AI แยกลำต้น–ใบ
            แล้วคำนวณด้วยสมการมาตรฐาน (TGO · Chave · IPCC) โปร่งใส ตรวจสอบได้ทุกจุด
          </p>
          <div className="cta rise d4">
            <a className="btn primary" href="/dashboard/viewer">ทดลอง 3D Viewer</a>
            <a className="btn ghost" href="#research">ดูงานวิจัย</a>
          </div>
          <div className="stats rise d5">
            <div className="stat"><div className="n">1.17<small> ซม.</small></div><div className="l">ความคลาดเคลื่อน DBH<br />เทียบไม้โค่นจริง</div></div>
            <div className="stat"><div className="n">0.61</div><div className="l">Wood/Leaf IoU<br />บนไม้จริง (Wan 2021)</div></div>
            <div className="stat"><div className="n">100<small>×</small></div><div className="l">ลดต้นทุน<br />การประเมิน</div></div>
          </div>
        </div>
      </section>

      <style jsx>{`
        .wrap{position:relative;min-height:100svh;overflow:hidden;color:#EAF3EC;
          --serif:var(--font-fraunces),"Hoefler Text","Iowan Old Style",Georgia,serif;
          --thai:var(--font-sarabun),"Noto Sans Thai","Leelawadee UI",Tahoma,sans-serif;
          --mono:var(--font-jetbrains-mono),ui-monospace,"SF Mono",Consolas,monospace;
          background:radial-gradient(120% 90% at 68% 42%,#0c2c1f 0%,#071b13 42%,#04100b 74%,#020a07 100%),#04100b;
          font-family:var(--thai);}
        .wrap::before{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;
          background:radial-gradient(60% 50% at 66% 50%,rgba(70,200,130,.12),transparent 70%);}
        .scene{position:absolute;inset:0;width:100%;height:100%;z-index:2;display:block;opacity:0;animation:fade 2s ease .3s forwards;}
        .grain{position:absolute;inset:0;z-index:3;pointer-events:none;opacity:.5;mix-blend-mode:overlay;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.55'/%3E%3C/svg%3E");}
        .vignette{position:absolute;inset:0;z-index:3;pointer-events:none;
          box-shadow:inset 0 0 220px 60px rgba(0,0,0,.65),inset 0 -120px 160px -60px rgba(0,0,0,.7);}
        .nav{position:relative;z-index:5;display:flex;align-items:center;justify-content:space-between;padding:26px clamp(20px,5vw,72px);}
        .brand{display:flex;align-items:center;gap:12px;font-weight:600;letter-spacing:.02em;}
        .mark{width:30px;height:30px;border-radius:9px;position:relative;
          background:conic-gradient(from 210deg,#2D6A4F,#86EFAC,#2D6A4F);
          box-shadow:0 0 22px rgba(134,239,172,.45),inset 0 0 10px rgba(4,16,11,.5);}
        .mark::after{content:"";position:absolute;inset:6px;border-radius:5px;background:#04100b;box-shadow:inset 0 0 8px rgba(134,239,172,.55);}
        .brand b{font-family:var(--serif);font-weight:600;font-size:19px;}
        .brand b i{font-style:normal;color:#86EFAC;}
        .nav ul{display:flex;gap:30px;list-style:none;margin:0;padding:0;font-size:14px;color:#8FA99A;}
        .nav a{color:inherit;text-decoration:none;transition:color .25s;}
        .nav a:hover{color:#EAF3EC;}
        .pill{border:1px solid rgba(180,240,205,.10);border-radius:999px;padding:9px 18px;color:#EAF3EC;background:rgba(134,239,172,.05);transition:.25s;}
        .pill:hover{background:rgba(134,239,172,.14);border-color:rgba(134,239,172,.35);}
        @media(max-width:820px){.nav ul{display:none;}}
        .hero{position:relative;z-index:5;display:flex;align-items:center;min-height:calc(100svh - 84px);padding:0 clamp(20px,5vw,72px);}
        .copy{max-width:620px;}
        .eyebrow{display:inline-flex;align-items:center;gap:10px;font-family:var(--mono);
          font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:#86EFAC;padding:7px 14px;
          border:1px solid rgba(180,240,205,.10);border-radius:999px;background:rgba(134,239,172,.04);backdrop-filter:blur(4px);}
        .dot{width:6px;height:6px;border-radius:50%;background:#86EFAC;box-shadow:0 0 10px #86EFAC;animation:pulse 2.4s ease-in-out infinite;}
        h1{font-family:var(--serif);font-weight:600;
          letter-spacing:-.015em;line-height:1.02;font-size:clamp(44px,6.4vw,86px);margin:26px 0 0;text-wrap:balance;color:#F3FBF4;text-shadow:0 2px 40px rgba(0,0,0,.5);}
        .em{font-style:italic;background:linear-gradient(120deg,#7CF29C,#C6FFDB 55%,#4FD08A);
          -webkit-background-clip:text;background-clip:text;color:transparent;text-shadow:0 0 46px rgba(134,239,172,.35);}
        .sub{font-family:var(--thai);font-size:clamp(16px,1.7vw,19px);
          line-height:1.7;color:#C4D8CC;max-width:33em;margin:26px 0 0;}
        .cta{display:flex;flex-wrap:wrap;gap:14px;margin-top:36px;}
        .btn{font-size:15px;font-weight:600;border-radius:13px;padding:15px 26px;cursor:pointer;border:1px solid transparent;
          text-decoration:none;transition:transform .2s,box-shadow .3s,background .3s;font-family:var(--thai);}
        .primary{color:#05261a;background:linear-gradient(180deg,#9CF7B9,#5FD693);
          box-shadow:0 10px 34px -10px rgba(120,240,160,.6),inset 0 1px 0 rgba(255,255,255,.4);}
        .primary:hover{transform:translateY(-2px);box-shadow:0 18px 44px -12px rgba(120,240,160,.75);}
        .ghost{color:#EAF3EC;border-color:rgba(180,240,205,.10);background:rgba(255,255,255,.02);}
        .ghost:hover{border-color:rgba(134,239,172,.4);background:rgba(134,239,172,.07);}
        .stats{display:flex;gap:30px;margin-top:52px;flex-wrap:wrap;}
        .n{font-family:var(--serif);font-size:30px;color:#C6FFDB;font-variant-numeric:tabular-nums;line-height:1;}
        .n small{font-size:15px;color:#8FA99A;font-family:inherit;}
        .l{font-family:var(--thai);font-size:12.5px;color:#8FA99A;margin-top:7px;}
        .stat+.stat{border-left:1px solid rgba(180,240,205,.10);padding-left:30px;}
        .rise{opacity:0;transform:translateY(22px);animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards;}
        .d1{animation-delay:.15s}.d2{animation-delay:.32s}.d3{animation-delay:.5s}.d4{animation-delay:.66s}.d5{animation-delay:.82s}
        @keyframes rise{to{opacity:1;transform:none;}}
        @keyframes fade{to{opacity:1;}}
        @keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(.7);}}
        @media(prefers-reduced-motion:reduce){.rise,.scene{animation:none;opacity:1;transform:none;}}
      `}</style>
    </div>
  );
}
