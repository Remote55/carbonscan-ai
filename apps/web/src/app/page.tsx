import Image from 'next/image';
import Link from 'next/link';

import { EditorialSection } from '../components/editorial/editorial-section';
import { TechnicalDetail } from '../components/editorial/technical-detail';
import { EvidenceMetric } from '../components/evidence/evidence-metric';
import { AppHeader } from '../components/layout/app-header';
import { ScrollToTop } from '../components/layout/scroll-to-top';
import { Button } from '../components/ui/button';
import { CORE_DEMO_EVIDENCE } from '../generated/core-demo-evidence';
import { VISUAL_ASSETS } from '../lib/visual-assets';

const { baseline, candidate, coreDemo } = CORE_DEMO_EVIDENCE;
const { wanHeldOut, demol65 } = CORE_DEMO_EVIDENCE.validation;

const JOURNEY = [
  {
    step: '01',
    title: 'รับภาพสามมิติของต้นไม้',
    description: 'รองรับข้อมูล Point Cloud จากเครื่องสแกน LiDAR หรือภาพถ่ายทางอากาศ',
    technical: ['point cloud รูปแบบ .ply', 'จำกัด 2 ล้านจุด หรือ 100 MB ต่อไฟล์'],
  },
  {
    step: '02',
    title: 'แยกลำต้นออกจากใบ',
    // "อย่างแม่นยำ" was in the supplied copy and is out, at the writer's
    // agreement: Wood IoU is 0.418 and that number is printed on this page.
    description:
      'คัดแยกจุดที่เป็นลำต้นออกจากใบไม้ด้วยอัลกอริทึมเชิงเรขาคณิต เพื่อลดความคลาดเคลื่อนในการคำนวณชีวมวล',
    technical: [
      `${baseline.backend} เป็นตัวที่ใช้จริง`,
      `${candidate.displayName} ยังเป็น ${candidate.status} ไม่ได้ถูกนำมาใช้`,
      `Wood IoU ${wanHeldOut.woodIoU}`,
    ],
  },
  {
    step: '03',
    title: 'วัดขนาดต้นไม้',
    description:
      'ประเมินขนาดลำต้นและความสูงรวม และสร้างแบบจำลองทรงกระบอก เพื่อคำนวณปริมาตรเนื้อไม้',
    technical: [
      'DBH ที่ระดับ 1.3 เมตร',
      'ปริมาตรจาก QSM ทรงกระบอก',
      `คลาดเคลื่อนเฉลี่ย ${demol65.dbhMaeCm} ซม. บนต้นไม้จริง 65 ต้น`,
    ],
  },
  {
    step: '04',
    title: 'คำนวณคาร์บอน',
    description:
      'คำนวณปริมาณชีวมวล คาร์บอนสะสม และ CO₂e ตามสมการแอลโลเมตริกอ้างอิงมาตรฐาน พร้อมระบบบันทึกแหล่งที่มาของข้อมูล',
    technical: [
      'สมการ Chave 2014',
      'ชีวมวลใต้ดิน = เหนือดิน × 0.24',
      'คาร์บอน = ชีวมวล × 0.47',
      'CO₂e = คาร์บอน × 44/12 (IPCC 2006)',
      'การแยกชนิดพันธุ์ยังเป็นโครงเปล่า',
    ],
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
              {/* "ในทุกขั้นตอน" was in the supplied copy and is out, at the
                  writer's agreement. The supervisor read that exact claim on
                  the demo page and asked whether we really state a limit at
                  every step. We do not - there are limits recorded for three
                  validation sets and stages with none - so the page says
                  "ของแต่ละขั้นตอน" instead. */}
              <p className="mt-7 max-w-xl text-base leading-8 text-canopy sm:text-lg">
                เพียงอัปโหลดข้อมูล Point Cloud ระบบจะวิเคราะห์ขนาดและโครงสร้างเพื่อประเมินปริมาณ
                คาร์บอนสะสมอัตโนมัติ พร้อมแสดงหลักฐานอ้างอิงของแต่ละขั้นตอนอย่างโปร่งใส
              </p>
              {/* The viewer is open to visitors, so this goes straight there.
                  It used to route through /login, which was true until the
                  sign-in requirement was lifted and then quietly was not. */}
              <div className="mt-8 flex flex-wrap gap-3">
                <Button render={<Link href="/demo" />} variant="editorial" size="xl">
                  ดูตัวอย่างผลการประเมิน
                </Button>
                <Button
                  render={<Link href="/dashboard/viewer" />}
                  variant="editorialOutline"
                  size="xl"
                >
                  ทดลองอัปโหลดไฟล์
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
            {/* "ไม่ปัดเศษ" stays on the end of the supplied label. The three
                numbers below are printed at full precision on purpose, and the
                label is what tells a reader that is deliberate rather than
                sloppy. */}
            <p className="editorial-eyebrow-th px-1 pb-3 text-canopy">
              ผลการประเมินจากชุดทดสอบอิสระ — แสดงเต็มไม่ปัดเศษ
            </p>
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
            title="ข้อจำกัดของการสำรวจแบบเดิม"
            description="การประเมินคาร์บอนในปัจจุบันต้องอาศัยการลงพื้นที่สำรวจทีละต้น ซึ่งใช้ต้นทุนสูง ใช้เวลานาน และยากต่อการตรวจสอบแหล่งที่มาของตัวเลขในภายหลัง"
          >
            {/* The scope note that sat beside this quote is gone at the team
                lead's request. Both claims that must survive - not a certified
                credit, no marketplace - are still made in "ความแม่นยำ", so
                removing the box costs the page a repetition rather than a
                limit. What it does drop is the one line saying phone
                photography is not supported yet; nothing on the page claims it
                is, but nothing says it is not either. */}
            <p className="max-w-3xl font-display text-3xl leading-snug text-deep-forest sm:text-4xl">
              เราไม่ได้มุ่งเน้นแค่ความแม่นยำของ AI
              แต่เราสร้างแพลตฟอร์มที่เปิดหลักฐานให้ตรวจสอบย้อนกลับได้
            </p>
          </EditorialSection>
        </div>

        <div id="how" data-editorial-beat="journey">
          <EditorialSection
            className="bg-gallery-ivory"
            eyebrow="02"
            title="วิธีทำงาน"
            description="ระบบแปลงข้อมูล Point Cloud สู่ตัวเลขคาร์บอนสะสมผ่าน 4 ขั้นตอนหลัก โดยระบุเทคนิคและสมการที่ใช้อย่างชัดเจน"
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
                    {/* A list, not one line joined by separators. A reviewer
                        asked for the dots to go; they were doing the job a
                        bullet does, less legibly, and Thai text runs long
                        enough that the line wrapped mid-fact. */}
                    <TechnicalDetail>
                      <ul className="list-disc space-y-1 pl-5">
                        {item.technical.map((line) => (
                          <li key={line}>{line}</li>
                        ))}
                      </ul>
                    </TechnicalDetail>
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
            title="ตรวจสอบโมเดล"
            description="ผู้ใช้สามารถหมุนดูโมเดล 3 มิติ เพื่อตรวจสอบผลการจำแนกส่วนลำต้นเป็นสีน้ำตาลและใบเป็นสีเขียวได้อย่างอิสระ ให้คุณมั่นใจในความถูกต้องของโครงสร้างก่อนเข้าสู่กระบวนการคำนวณชีวมวล"
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
                      วิเคราะห์ด้วยหลักการทางเรขาคณิต
                    </p>
                  </div>
                  <div className="border-paper/15 border-b p-6">
                    <dt className="editorial-eyebrow-th text-evidence-amber">ตัวที่ยังทดลองอยู่</dt>
                    <dd className="mt-2 font-display text-3xl">
                      {candidate.displayName} / {candidate.status}
                    </dd>
                    {/* The supplied line read "อยู่ระหว่างเตรียมความพร้อมสู่การ
                        ใช้งานจริง", which reads as on track to ship. The
                        recorded verdict is FAIL_METRICS - it lost to the
                        baseline - so this says that instead, at the writer's
                        agreement. */}
                    <p className="mt-2 text-sm leading-6 text-mist">
                      โมเดลทดลอง ผลยังไม่ผ่านเกณฑ์ จึงยังไม่ได้ใช้งานจริง
                    </p>
                  </div>
                  <div className="p-6">
                    <dt className="editorial-eyebrow-th text-lichen">ชุดสาธิตที่รันซ้ำได้</dt>
                    <dd className="mt-2 font-display text-3xl tabular-nums">
                      {coreDemo.totalTrees} ต้น
                    </dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      ชุดข้อมูลสาธิตเพื่อยืนยันความเสถียร มีผลลัพธ์คงที่เสมอ
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
            title="ความแม่นยำ"
            description="ผลการประเมินอ้างอิงจากการทดสอบชุดข้อมูล 3 ชุด โดยเราเปิดเผยข้อจำกัดของระบบอย่างตรงไปตรงมา เพื่อให้เห็นขอบเขตที่แพลตฟอร์มสามารถทำได้ในปัจจุบัน"
          >
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-12">
              <div className="lg:col-span-4">
                <EvidenceMetric
                  label={`Wood IoU / ${candidate.status}`}
                  value={String(wanHeldOut.woodIoU)}
                  note="ชุด Wan held-out เป็นค่าจากรอบเทรนที่ดีที่สุด จึงเข้าข้างตัวเองเล็กน้อย"
                  tone="dark"
                />
              </div>
              <div className="lg:col-span-3">
                <EvidenceMetric
                  label={`Leaf IoU / ${candidate.status}`}
                  value={String(wanHeldOut.leafIoU)}
                  note="ชุด Wan held-out วัดการแยกลำต้นกับใบเท่านั้น"
                  tone="lichen"
                />
              </div>
              <div className="lg:col-span-5">
                <EvidenceMetric
                  label="DBH MAE / geometry only"
                  value={`${demol65.dbhMaeCm} cm`}
                  note="ชุด DemoL จากต้นไม้แยกเดี่ยว 65 ต้น แสดงเต็มไม่ปัดเศษ"
                />
              </div>
            </div>

            <div className="mt-8 flex flex-col justify-between gap-6 border-t border-hairline pt-8 sm:flex-row sm:items-center">
              <div className="max-w-3xl space-y-4 text-base leading-7 text-canopy">
                <div>
                  <p className="font-semibold text-forest-ink">ทดสอบแล้ว</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    <li>
                      การแยกลำต้นและใบ: อ้างอิงผลลัพธ์จากรอบการฝึกที่ดีที่สุด
                      ซึ่งอาจมีค่าประเมินสูงกว่าการใช้งานจริงเล็กน้อย
                    </li>
                    <li>
                      การประเมินโครงสร้าง: ทดสอบเฉพาะความแม่นยำทางเรขาคณิต ขนาดและความสูง
                      จากข้อมูลต้นไม้จริง 65 ต้น
                    </li>
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-ember">ยังไม่ได้ทดสอบ</p>
                  {/* TGO 2017 is named on purpose. The plain-language rewrite
                      dropped it once, and it is the one line that shows this was
                      checked against the Thai standard rather than against a
                      paper from somewhere else. */}
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    <li>ระบบทั้งเส้นตั้งแต่รับไฟล์จนได้ค่าคาร์บอน</li>
                    <li>การแยกชนิดพันธุ์ที่ยังเป็นโครงเปล่า</li>
                    <li>
                      ระบบจำเป็นต้องได้รับการทดสอบภาคสนามเพิ่มเติมกับชนิดพันธุ์ไม้ในป่าเขตร้อนของไทย
                      รวมถึงการสอบเทียบสมการกับแนวทางขององค์การบริหารจัดการก๊าซเรือนกระจก (TGO ปี 2017)
                      เพื่อเตรียมความพร้อมสู่การเป็นเครื่องมือ Digital MRV ในอนาคต
                    </li>
                  </ul>
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
      <ScrollToTop />
    </div>
  );
}
