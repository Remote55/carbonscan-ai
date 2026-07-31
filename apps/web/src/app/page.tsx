import Image from 'next/image';
import Link from 'next/link';

import { EditorialSection } from '../components/editorial/editorial-section';
import { TechnicalDetail } from '../components/editorial/technical-detail';
import { EvidenceMetric } from '../components/evidence/evidence-metric';
import { AppHeader } from '../components/layout/app-header';
import { Button } from '../components/ui/button';
import { CORE_DEMO_EVIDENCE } from '../generated/core-demo-evidence';
import { VISUAL_ASSETS } from '../lib/visual-assets';

const { baseline, candidate, coreDemo } = CORE_DEMO_EVIDENCE;
const { wanHeldOut, demol65 } = CORE_DEMO_EVIDENCE.validation;

const JOURNEY = [
  {
    step: '01',
    title: 'รับภาพสามมิติของต้นไม้',
    description:
      'ไฟล์จากเครื่องสแกนเลเซอร์ หรือจากการถ่ายต้นไม้หลายมุมแล้วประกอบเป็นทรงสามมิติ ระบบแสดงเป็นกลุ่มจุดที่หมุนดูได้',
    technical: 'point cloud รูปแบบ .ply · จำกัด 2 ล้านจุด หรือ 100 MB ต่อไฟล์',
  },
  {
    step: '02',
    title: 'แยกลำต้นออกจากใบ',
    description:
      'ต้องรู้ก่อนว่าจุดไหนคือเนื้อไม้ จุดไหนคือใบ เพราะคาร์บอนเก็บอยู่ในเนื้อไม้เป็นหลัก ตอนนี้ใช้วิธีคำนวณจากรูปทรง ยังไม่ได้ใช้ AI',
    technical: `${baseline.backend} เป็นตัวที่ใช้จริง · ${candidate.displayName} ยังเป็น ${candidate.status} ไม่ได้ถูกนำมาใช้ · Wood IoU ${wanHeldOut.woodIoU}`,
  },
  {
    step: '03',
    title: 'วัดขนาดต้นไม้',
    description:
      'วัดเส้นผ่านศูนย์กลางลำต้นที่ระดับอก ความสูงทั้งต้น และปริมาตรเนื้อไม้ จากรูปทรงที่แยกได้',
    technical: `DBH ที่ระดับ 1.3 เมตร · ปริมาตรจาก QSM ทรงกระบอก · คลาดเคลื่อนเฉลี่ย ${demol65.dbhMaeCm} ซม. บนต้นไม้จริง 65 ต้น`,
  },
  {
    step: '04',
    title: 'คำนวณคาร์บอน',
    description:
      'เอาขนาดที่วัดได้เข้าสมการมาตรฐาน ได้เป็นน้ำหนักชีวมวล คาร์บอน และ CO₂ พร้อมบันทึกว่าใช้สมการไหน',
    technical:
      'สมการ Chave 2014 · ชีวมวลใต้ดิน = เหนือดิน × 0.24 · คาร์บอน = ชีวมวล × 0.47 · CO₂e = คาร์บอน × 44/12 (IPCC 2006) · การแยกชนิดพันธุ์ยังเป็นโครงเปล่า',
  },
] as const;

export default function HomePage() {
  return (
    // AppHeader renders its own <header><nav>, and the footer is contentinfo, so
    // neither belongs inside <main>: nesting them there put three landmarks
    // inside the one that is supposed to hold only the page's main content, and
    // left a screen reader jumping to "main" at the top of the navigation.
    <div className="min-h-screen overflow-x-hidden bg-gallery-ivory text-forest-ink">
      <a
        href="#main-content"
        className="sr-only rounded-full bg-canopy px-5 py-3 text-sm font-medium text-paper focus:not-sr-only focus:absolute focus:left-5 focus:top-4 focus:z-50"
      >
        ข้ามไปยังเนื้อหาหลัก
      </a>

      <div className="mx-auto max-w-7xl px-5 pt-4 sm:px-8">
        <AppHeader />
      </div>

      <main id="main-content">
        <section className="mx-auto max-w-7xl px-5 pb-8 pt-6 sm:px-8">
          <div className="grid grid-cols-1 gap-8 lg:min-h-[35.625rem] lg:grid-cols-12">
            <div className="flex flex-col justify-center lg:col-span-6 lg:pr-8">
              <p className="editorial-eyebrow">TreeQ Carbon / NSC 2026 / Deep Tech</p>
              {/* "ประเมิน", not "อ่าน". The headline used to say the platform reads
                  carbon off a tree, which is the one claim this project cannot make:
                  the number comes from an allometric estimate carrying 18.8% volume
                  MAPE, not from a reading. A page whose whole argument is that it
                  reports its own limits cannot overclaim in its largest type.
                  "ทางกายภาพ" over "จริง" for the same reason - it names what is
                  actually measured, which is geometry.
                  Wider max-width and a smaller lg size because the honest phrasing is
                  49 characters against 33; measured at both demo viewports so the
                  metrics card below still clears the fold. */}
              <h1 className="mt-7 max-w-[15ch] text-balance font-display text-[2.6rem] font-medium leading-[1.14] tracking-[-0.03em] text-forest-ink sm:text-5xl lg:text-[3.4rem]">
                ประเมินคาร์บอนสะสม จากโครงสร้างทางกายภาพของต้นไม้
              </h1>
              <p className="mt-7 max-w-xl text-base leading-8 text-canopy sm:text-lg">
                ใส่ภาพสามมิติของต้นไม้เข้าไป ระบบจะวัดขนาดลำต้นกับความสูง
                แล้วคำนวณว่าต้นไม้ต้นนั้นเก็บคาร์บอนไว้เท่าไร พร้อมบอกที่มาของตัวเลขทุกตัว
              </p>
              {/* The viewer is open to visitors, so this goes straight there.
                  It used to route through /login, which was true until the
                  sign-in requirement was lifted and then quietly was not. */}
              <div className="mt-8 flex flex-wrap gap-3">
                <Button render={<Link href="/demo" />} variant="editorial" size="xl">
                  ดูหลักฐานที่ตรวจแฮชแล้ว
                </Button>
                <Button
                  render={<Link href="/dashboard/viewer" />}
                  variant="editorialOutline"
                  size="xl"
                >
                  ลองอัปโหลดไฟล์ของคุณ
                </Button>
              </div>
              {/* These three facts are the point of the whole project, and they
                  were set as one line of 10px uppercase text that read like
                  leftover debug output - a reviewer asked whether it mattered or
                  should just be deleted. It matters: it is what stops the page
                  claiming a trained classifier and a promoted model it does not
                  have. So each fact gets a label, a readable size, and a border
                  that says at a glance which are shipped and which are not.
                  Solid backgrounds on purpose - the palette tokens hold hex
                  values, so Tailwind's `/opacity` shorthand on them can emit CSS
                  the browser drops, and the tint silently disappears. */}
              <dl className="mt-7 flex flex-wrap gap-2">
                {[
                  { term: 'แยกลำต้น–ใบ ที่ใช้จริง', value: baseline.backend, shipped: true },
                  { term: candidate.displayName, value: candidate.status, shipped: false },
                  { term: 'จำแนกชนิดพันธุ์', value: 'Stub', shipped: false },
                ].map((fact) => (
                  <div
                    key={fact.term}
                    className={`rounded-xl border bg-paper px-3.5 py-2.5 ${
                      fact.shipped ? 'border-moss' : 'border-evidence-amber'
                    }`}
                  >
                    <dt className="editorial-eyebrow-th text-canopy">{fact.term}</dt>
                    <dd
                      className={`mt-1 text-sm font-semibold ${
                        fact.shipped ? 'text-forest-ink' : 'text-evidence-amber'
                      }`}
                    >
                      {fact.value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="relative min-h-[25rem] overflow-hidden rounded-[1.75rem] shadow-[0_28px_68px_-18px_rgba(14,42,29,0.18)] lg:col-span-6 lg:min-h-[35.625rem]">
              <Image
                src={VISUAL_ASSETS.landing.src}
                alt="ป่าปกคลุมด้วยหมอก"
                fill
                priority
                sizes="(min-width: 1024px) 48vw, 100vw"
                className="object-cover"
              />
              <div className="from-deep-forest/5 via-deep-forest/15 to-deep-forest/80 absolute inset-0 bg-gradient-to-b" />
            </div>
          </div>

          <div className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-4 shadow-sm">
            <p className="editorial-eyebrow-th px-1 pb-3 text-canopy">ตัวเลขที่วัดได้จริง — ไม่ปัดเศษ</p>
            <div className="grid gap-3 md:grid-cols-3">
              <EvidenceMetric
                label="Wood IoU"
                value={String(wanHeldOut.woodIoU)}
                note={`Wan held-out / ${candidate.status}`}
              />
              <EvidenceMetric
                label="Leaf IoU"
                value={String(wanHeldOut.leafIoU)}
                note={`Wan held-out / ${candidate.status}`}
              />
              <EvidenceMetric
                label="DBH MAE"
                value={`${demol65.dbhMaeCm} cm`}
                note="Demol / 65 isolated trees"
              />
            </div>
          </div>
        </section>

        <div data-editorial-beat="problem">
          <EditorialSection
            className="border-t border-hairline bg-paper"
            eyebrow="01"
            title="ทำไมต้องวัดใหม่"
            description="การวัดคาร์บอนต้นไม้ทุกวันนี้ต้องส่งคนเข้าไปวัดทีละต้น ใช้เวลา และพอได้ตัวเลขมาแล้วก็ตรวจย้อนไม่ได้ว่ามาจากต้นไหน วัดด้วยวิธีอะไร"
          >
            <div className="grid items-end gap-8 lg:grid-cols-12">
              <p className="max-w-3xl font-display text-3xl leading-snug text-deep-forest sm:text-4xl lg:col-span-8">
                เราไม่ได้เริ่มจากคำว่า “AI แม่นยำ” แต่เริ่มจากหลักฐานที่ใครก็เปิดดู แล้วถามต่อได้
              </p>
              <div className="border-l border-moss pl-5 text-sm leading-7 text-canopy lg:col-span-4">
                ตอนนี้ทำได้กับไฟล์สามมิติที่มีอยู่แล้วเท่านั้น ยังไม่รองรับการถ่ายด้วยมือถือ
                ไม่มีระบบซื้อขาย และไม่ใช่การรับรองเครดิตคาร์บอน
              </div>
            </div>
          </EditorialSection>
        </div>

        <div id="how" data-editorial-beat="journey">
          <EditorialSection
            className="bg-gallery-ivory"
            eyebrow="02"
            title="วัดยังไง"
            description="จากกลุ่มจุดสามมิติ กลายเป็นตัวเลขคาร์บอนได้ด้วยสี่ขั้น แต่ละขั้นบอกได้ว่าทำอะไรและใช้อะไรคำนวณ"
          >
            <ol className="border-y border-hairline">
              {JOURNEY.map((item) => (
                <li
                  key={item.step}
                  className="grid gap-3 border-b border-hairline py-6 last:border-b-0 sm:grid-cols-[5rem_minmax(0,0.7fr)_minmax(0,1.3fr)] sm:items-baseline"
                >
                  <span className="font-mono text-xs text-evidence-amber">{item.step}</span>
                  <h3 className="font-display text-2xl text-forest-ink">{item.title}</h3>
                  <div className="max-w-2xl">
                    <p className="text-base leading-7 text-canopy">{item.description}</p>
                    <TechnicalDetail>{item.technical}</TechnicalDetail>
                  </div>
                </li>
              ))}
            </ol>
          </EditorialSection>
        </div>

        <div id="tech" data-editorial-beat="three-dimensional-evidence">
          <EditorialSection
            className="border-y border-hairline bg-paper"
            eyebrow="03"
            title="ขอดูของจริง"
            description="หมุนดูต้นไม้ได้เอง จุดสีน้ำตาลคือส่วนที่ระบบตัดสินว่าเป็นเนื้อไม้ สีเขียวคือใบ ถ้าไม่เห็นด้วยกับที่ระบบแบ่ง จะเห็นตั้งแต่ตรงนี้ ก่อนไปดูตัวเลข"
          >
            <div className="overflow-hidden rounded-[1.75rem] bg-deep-forest text-paper shadow-[0_24px_60px_-24px_rgba(14,42,29,0.45)]">
              <div className="grid lg:grid-cols-12">
                <div className="border-paper/15 relative min-h-[20rem] overflow-hidden border-b lg:col-span-7 lg:border-b-0 lg:border-r">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(199,214,161,0.75)_0_1.4px,transparent_1.8px)] opacity-50 [background-size:18px_18px]" />
                  <div className="absolute inset-x-[18%] bottom-[12%] top-[12%] rounded-[48%] bg-[radial-gradient(ellipse_at_50%_22%,rgba(199,214,161,0.42),transparent_48%),linear-gradient(90deg,transparent_46%,rgba(178,138,64,0.8)_48%,rgba(178,138,64,0.8)_52%,transparent_54%)] blur-[0.2px]" />
                  <div className="border-lichen/40 bg-deep-forest/80 editorial-eyebrow-th absolute left-6 top-6 rounded-full border px-3 py-1 text-lichen">
                    เปิดดูได้ทุกจุด
                  </div>
                  <p className="absolute bottom-6 left-6 max-w-xs font-display text-2xl leading-snug">
                    ดูให้เห็นก่อนว่าระบบแบ่งลำต้นกับใบตรงไหน แล้วค่อยเชื่อตัวเลข
                  </p>
                </div>
                <dl className="space-y-0 lg:col-span-5">
                  <div className="border-paper/15 border-b p-6">
                    <dt className="editorial-eyebrow-th text-lichen">วิธีที่ใช้จริง</dt>
                    <dd className="mt-2 font-display text-3xl">{baseline.backend}</dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      คำนวณจากรูปทรง เป็นเส้นทางหลักของระบบตอนนี้
                    </p>
                  </div>
                  <div className="border-paper/15 border-b p-6">
                    <dt className="editorial-eyebrow-th text-evidence-amber">ตัวที่ยังทดลองอยู่</dt>
                    <dd className="mt-2 font-display text-3xl">
                      {candidate.displayName} / {candidate.status}
                    </dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      ผลยังสู้วิธีเดิมไม่ได้ จึงยังไม่ได้เอามาใช้จริง
                    </p>
                  </div>
                  <div className="p-6">
                    <dt className="editorial-eyebrow-th text-lichen">ชุดสาธิตที่รันซ้ำได้</dt>
                    <dd className="mt-2 font-display text-3xl tabular-nums">
                      {coreDemo.totalTrees} ต้น
                    </dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      เป็นชุดข้อมูลตายตัวไว้ตรวจว่ารันซ้ำแล้วได้ผลเดิม ไม่ใช่ตัววัดความแม่นยำ
                    </p>
                  </div>
                </dl>
              </div>
            </div>
          </EditorialSection>
        </div>

        <div id="proof" data-editorial-beat="validation">
          <EditorialSection
            className="bg-gallery-ivory"
            eyebrow="04"
            title="เชื่อได้แค่ไหน"
            description="เราทดสอบไปสามชุด แต่ละชุดบอกได้แค่บางเรื่อง และมีขั้นที่ยังไม่ได้ทดสอบเลย"
          >
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-12">
              <div className="lg:col-span-4">
                <EvidenceMetric
                  label={`Wood IoU / ${candidate.status}`}
                  value={String(wanHeldOut.woodIoU)}
                  note="ชุด Wan held-out · เป็นค่าจาก epoch ที่ดีที่สุด จึงเข้าข้างตัวเองเล็กน้อย"
                  tone="dark"
                />
              </div>
              <div className="lg:col-span-3">
                <EvidenceMetric
                  label={`Leaf IoU / ${candidate.status}`}
                  value={String(wanHeldOut.leafIoU)}
                  note="ชุด Wan held-out · วัดการแยกลำต้นกับใบ เท่านั้น"
                  tone="lichen"
                />
              </div>
              <div className="lg:col-span-5">
                <EvidenceMetric
                  label="DBH MAE / geometry only"
                  value={`${demol65.dbhMaeCm} cm`}
                  note="ชุด DemoL · ต้นไม้แยกเดี่ยว 65 ต้น · แสดงเต็มไม่ปัดเศษ"
                />
              </div>
            </div>

            <div className="mt-8 flex flex-col justify-between gap-6 border-t border-hairline pt-8 sm:flex-row sm:items-center">
              <div className="max-w-3xl space-y-4 text-base leading-7 text-canopy">
                <div>
                  <p className="font-semibold text-forest-ink">ทดสอบแล้ว</p>
                  <p className="mt-1">
                    การแยกลำต้นกับใบ — แต่ใช้ชุดข้อมูลเดียวกันนี้ตอนเลือกรอบเทรนที่ดีที่สุด
                    ค่าที่ได้จึงเข้าข้างตัวเอง · การวัดขนาดต้นไม้จริง 65 ต้น — วัดขนาดอย่างเดียว
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-ember">ยังไม่ได้ทดสอบ</p>
                  {/* TGO 2017 is named on purpose. The plain-language rewrite
                      dropped it once, and it is the one line that shows this was
                      checked against the Thai standard rather than against a
                      paper from somewhere else. */}
                  <p className="mt-1">
                    ระบบทั้งเส้นตั้งแต่รับไฟล์จนได้ค่าคาร์บอน · สมการชีวมวลกับข้อมูลต้นไม้จริงในไทย
                    และค่าสัมประสิทธิ์ที่ยังต้องสอบทานกับแนวทาง TGO ปี 2017 ·
                    การแยกชนิดพันธุ์ที่ยังเป็นโครงเปล่า
                  </p>
                </div>
                <p>
                  ค่าคาร์บอนและ CO₂e ที่แสดงเป็นค่าประมาณ ไม่ใช่เครดิตคาร์บอนที่ผ่านการรับรอง
                  และเราไม่ได้กล่าวอ้างเรื่องตลาดซื้อขายเครดิต
                </p>
              </div>
              <Button render={<Link href="/demo" />} variant="editorial" size="xl">
                เปิดหลักฐานใน Demo
              </Button>
            </div>
          </EditorialSection>
        </div>
      </main>

      <footer className="border-t border-hairline bg-paper py-8">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-5 text-sm text-canopy sm:flex-row sm:px-8">
          <span className="font-display text-base text-forest-ink">TreeQ Carbon Platform</span>
          <span>Prototype for NSC 2026 · หมวด 14</span>
        </div>
      </footer>
    </div>
  );
}
