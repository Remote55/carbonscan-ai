import Image from 'next/image';
import Link from 'next/link';

import { EditorialSection } from '../components/editorial/editorial-section';
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
    title: 'รับ point cloud',
    description: 'เริ่มจากข้อมูลจุดสามมิติที่เปิดดูและตรวจสอบย้อนกลับได้ใน judge demo',
  },
  {
    step: '02',
    title: 'แยก wood / leaf',
    description: `${baseline.backend} เป็น default baseline; ${candidate.displayName} ยังเป็น ${candidate.status}`,
  },
  {
    step: '03',
    title: 'วัด geometry',
    description:
      'หา DBH ความสูง และปริมาตรจากโครงสร้างของต้นไม้ โดยรายงานขอบเขต validation แยกจากกัน',
  },
  {
    step: '04',
    title: 'ประมาณ carbon stock',
    description:
      'แปลง geometry ผ่าน allometric equation พร้อม provenance; species classification ยังเป็น Stub',
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
              <h1 className="mt-7 max-w-[11ch] text-balance font-display text-5xl font-medium leading-[1.12] tracking-[-0.03em] text-forest-ink sm:text-6xl lg:text-[4rem]">
                อ่านคาร์บอนจากโครงสร้างจริงของต้นไม้
              </h1>
              <p className="mt-7 max-w-xl text-base leading-8 text-canopy sm:text-lg">
                แพลตฟอร์มต้นแบบประเมิน DBH ความสูง ชีวมวล คาร์บอน และ CO₂e จาก 3D point cloud พร้อม
                provenance ของ pipeline ที่ตรวจสอบย้อนกลับได้
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Button render={<Link href="/demo" />} variant="editorial" size="xl">
                  ทดลอง Demo Dataset
                </Button>
                <Button render={<Link href="/demo" />} variant="editorialOutline" size="xl">
                  อัปโหลด Point Cloud
                </Button>
              </div>
              <p className="mt-6 font-mono text-[0.625rem] uppercase leading-5 tracking-[0.08em] text-evidence-amber">
                {baseline.backend} = Default · {candidate.displayName} = {candidate.status} ·
                species stage = Stub
              </p>
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
              <div className="bg-deep-forest/90 absolute bottom-6 right-6 max-w-[16rem] rounded-[0.875rem] border border-moss px-4 py-3 text-paper backdrop-blur-sm">
                <p className="font-mono text-[0.5625rem] uppercase tracking-[0.08em]">
                  Field observation / 01
                </p>
                <p className="mt-2 text-sm font-medium">จากโครงสร้าง 3D สู่คาร์บอน</p>
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-4 shadow-sm">
            <p className="editorial-eyebrow px-1 pb-3">Measured evidence / do not round</p>
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
            eyebrow="01 / Problem"
            title="ปัญหาที่การวัดแบบเดิมทิ้งไว้"
            description="ตัวเลขคาร์บอนมีความหมายก็ต่อเมื่อย้อนกลับไปเห็นได้ว่า geometry มาจากไหน ผ่านขั้นตอนอะไร และข้อจำกัดอยู่ตรงจุดใด"
          >
            <div className="grid items-end gap-8 lg:grid-cols-12">
              <p className="max-w-3xl font-display text-3xl leading-snug text-deep-forest sm:text-4xl lg:col-span-8">
                เราไม่ได้เริ่มจากคำว่า “AI แม่นยำ” แต่เริ่มจากหลักฐานที่กรรมการเปิดดู แล้วถามต่อได้
              </p>
              <div className="border-l border-moss pl-5 text-sm leading-7 text-canopy lg:col-span-4">
                ขอบเขต prototype ยังไม่รวม mobile photogrammetry ที่ผ่านการ review, marketplace หรือ
                certification; ค่าที่แสดงเป็น carbon stock และ CO₂e estimate ไม่ใช่ certified credit
              </div>
            </div>
          </EditorialSection>
        </div>

        <div id="how" data-editorial-beat="journey">
          <EditorialSection
            className="bg-gallery-ivory"
            eyebrow="02 / Measurement journey"
            title="เส้นทางการวัดจากจุดสู่คาร์บอน"
            description="หนึ่ง narrative ต่อเนื่องจากข้อมูลสามมิติไปสู่ค่าประมาณ แทนการแยก feature เป็นการ์ดที่ดูมีน้ำหนักเท่ากัน"
          >
            <ol className="border-y border-hairline">
              {JOURNEY.map((item) => (
                <li
                  key={item.step}
                  className="grid gap-3 border-b border-hairline py-6 last:border-b-0 sm:grid-cols-[5rem_minmax(0,0.7fr)_minmax(0,1.3fr)] sm:items-baseline"
                >
                  <span className="font-mono text-xs text-evidence-amber">{item.step}</span>
                  <h3 className="font-display text-2xl text-forest-ink">{item.title}</h3>
                  <p className="max-w-2xl text-sm leading-7 text-canopy">{item.description}</p>
                </li>
              ))}
            </ol>
          </EditorialSection>
        </div>

        <div id="tech" data-editorial-beat="three-dimensional-evidence">
          <EditorialSection
            className="border-y border-hairline bg-paper"
            eyebrow="03 / Inspect the structure"
            title="หลักฐาน 3D ที่เปิดให้ตรวจสอบ"
            description="3D viewer เป็นพื้นที่ตรวจผลที่ทำงานแล้ว: wood, leaf และ provenance อยู่ในเรื่องเดียวกัน โดยไม่เปลี่ยนสถานะโมเดลจากหลักฐานที่ยังไม่ผ่าน gate"
          >
            <div className="overflow-hidden rounded-[1.75rem] bg-deep-forest text-paper shadow-[0_24px_60px_-24px_rgba(14,42,29,0.45)]">
              <div className="grid lg:grid-cols-12">
                <div className="border-paper/15 relative min-h-[20rem] overflow-hidden border-b lg:col-span-7 lg:border-b-0 lg:border-r">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(199,214,161,0.75)_0_1.4px,transparent_1.8px)] opacity-50 [background-size:18px_18px]" />
                  <div className="absolute inset-x-[18%] bottom-[12%] top-[12%] rounded-[48%] bg-[radial-gradient(ellipse_at_50%_22%,rgba(199,214,161,0.42),transparent_48%),linear-gradient(90deg,transparent_46%,rgba(178,138,64,0.8)_48%,rgba(178,138,64,0.8)_52%,transparent_54%)] blur-[0.2px]" />
                  <div className="border-lichen/40 bg-deep-forest/80 absolute left-6 top-6 rounded-full border px-3 py-1 font-mono text-[0.625rem] uppercase tracking-[0.1em] text-lichen">
                    Inspectable 3D evidence
                  </div>
                  <p className="absolute bottom-6 left-6 max-w-xs font-display text-2xl leading-snug">
                    เห็นจุดที่โมเดลเรียกว่า wood และ leaf ก่อนเชื่อตัวเลขปลายทาง
                  </p>
                </div>
                <dl className="space-y-0 lg:col-span-5">
                  <div className="border-paper/15 border-b p-6">
                    <dt className="font-mono text-[0.625rem] uppercase tracking-[0.12em] text-lichen">
                      Default backend
                    </dt>
                    <dd className="mt-2 font-display text-3xl">{baseline.backend}</dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      Implemented baseline และเส้นทางหลักของ demo
                    </p>
                  </div>
                  <div className="border-paper/15 border-b p-6">
                    <dt className="font-mono text-[0.625rem] uppercase tracking-[0.12em] text-evidence-amber">
                      Candidate status
                    </dt>
                    <dd className="mt-2 font-display text-3xl">
                      {candidate.displayName} / {candidate.status}
                    </dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      ไม่ถูก promote เป็น default จากผลที่เห็นบนหน้านี้
                    </p>
                  </div>
                  <div className="p-6">
                    <dt className="font-mono text-[0.625rem] uppercase tracking-[0.12em] text-lichen">
                      Reproducible core demo
                    </dt>
                    <dd className="mt-2 font-display text-3xl tabular-nums">
                      {coreDemo.totalTrees} trees
                    </dd>
                    <p className="mt-2 text-sm leading-6 text-mist">
                      ค่าจาก deterministic demo ไม่ใช่ accuracy benchmark
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
            eyebrow="04 / Evidence with limitations"
            title="Validation ที่รายงานตามขอบเขต"
            description="Wan held-out ใช้อธิบายผล segmentation ของ candidate ส่วน Demol 65 isolated trees ใช้อธิบาย geometry เท่านั้น ไม่ใช่ full-pipeline, allometric หรือ carbon validation"
          >
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-12">
              <div className="lg:col-span-4">
                <EvidenceMetric
                  label={`Wood IoU / ${candidate.status}`}
                  value={String(wanHeldOut.woodIoU)}
                  note="Wan held-out · best-epoch selection caveat"
                  tone="dark"
                />
              </div>
              <div className="lg:col-span-3">
                <EvidenceMetric
                  label={`Leaf IoU / ${candidate.status}`}
                  value={String(wanHeldOut.leafIoU)}
                  note="Wan held-out · segmentation evidence"
                  tone="lichen"
                />
              </div>
              <div className="lg:col-span-5">
                <EvidenceMetric
                  label="DBH MAE / geometry only"
                  value={`${demol65.dbhMaeCm} cm`}
                  note="Demol · 65 isolated trees · full precision"
                />
              </div>
            </div>

            <div className="mt-8 flex flex-col justify-between gap-6 border-t border-hairline pt-8 sm:flex-row sm:items-center">
              <p className="max-w-3xl text-sm leading-7 text-canopy">
                Species classifier = Stub. ค่า carbon stock และ CO₂e เป็น estimate; coefficients
                ยังต้อง verify กับ TGO Guideline 2017 และไม่มี claim เรื่อง marketplace
                หรือการรับรองเครดิต
              </p>
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
