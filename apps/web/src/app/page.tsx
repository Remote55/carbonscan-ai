'use client';

import { useMemo } from 'react';
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
import { generateDemoTree } from '@/lib/demo-pointcloud';
import { ViewerStage } from '@/components/viewer/viewer-stage';

const { baseline, candidate, coreDemo } = CORE_DEMO_EVIDENCE;
const { wanHeldOut, demol65 } = CORE_DEMO_EVIDENCE.validation;

const JOURNEY = [
  {
    step: '01',
    title: 'รับภาพสามมิติของต้นไม้',
    description:
      'รองรับข้อมูล Point Cloud จากเครื่องสแกน LiDAR หรือภาพถ่ายทางอากาศ',
    technical: [
      'point cloud รูปแบบ .ply',
      'จำกัด 2 ล้านจุด หรือ 100 MB ต่อไฟล์',
    ],
  },
  {
    step: '02',
    title: 'แยกลำต้นออกจากใบ',
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
  const demoForest = useMemo(() => {
    const treeConfigs = [
      {
        seed: 42,
        position: [-3.4, 0, 0] as const,
        scale: 0.88,
      },
      {
        seed: 84,
        position: [0, 0, 0] as const,
        scale: 1.08,
      },
      {
        seed: 126,
        position: [3.4, 0, 0] as const,
        scale: 0.94,
      },
    ];

    const trees = treeConfigs.map((config) => {
      const tree = generateDemoTree({
        seed: config.seed,
      });

      const transformedPositions = new Float32Array(
        tree.positions.length,
      );

      for (
        let index = 0;
        index < tree.positions.length;
        index += 3
      ) {
        const x = tree.positions[index];
        const y = tree.positions[index + 1];
        const z = tree.positions[index + 2];

        transformedPositions[index] =
          x * config.scale + config.position[0];

        transformedPositions[index + 1] =
          y * config.scale + config.position[1];

        transformedPositions[index + 2] =
          z * config.scale + config.position[2];
      }

      return {
        positions: transformedPositions,
        classes: tree.classes,
      };
    });

    const totalPositionLength = trees.reduce(
      (total, tree) => total + tree.positions.length,
      0,
    );

    const totalClassLength = trees.reduce(
      (total, tree) => total + tree.classes.length,
      0,
    );

    const positions = new Float32Array(totalPositionLength);
    const classes = new Uint8Array(totalClassLength);

    let positionOffset = 0;
    let classOffset = 0;

    trees.forEach((tree) => {
      positions.set(tree.positions, positionOffset);
      classes.set(tree.classes, classOffset);

      positionOffset += tree.positions.length;
      classOffset += tree.classes.length;
    });

    return {
      positions,
      classes,
      labelled: true,
      treeCount: trees.length,
    };
  }, []);

  const nPoints = demoForest.classes.length;

  return (
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
              <p className="editorial-eyebrow">
                TreeQ Carbon / NSC 2026 / Deep Tech
              </p>

              <h1 className="mt-7 max-w-[15ch] text-balance font-display text-[2.6rem] font-medium leading-[1.14] tracking-[-0.03em] text-forest-ink sm:text-5xl lg:text-[3.4rem]">
                ประเมินคาร์บอนสะสม จากโครงสร้างทางกายภาพของต้นไม้
              </h1>

              <p className="mt-7 max-w-xl text-base leading-8 text-canopy sm:text-lg">
                เพียงอัปโหลดข้อมูล Point Cloud
                ระบบจะวิเคราะห์ขนาดและโครงสร้างเพื่อประเมินปริมาณคาร์บอนสะสมอัตโนมัติ
                พร้อมแสดงหลักฐานอ้างอิงของแต่ละขั้นตอนอย่างโปร่งใส
              </p>

              <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
                <Button
                  render={<Link href="/demo" />}
                  variant="editorial"
                  size="xl"
                  className="w-full justify-center"
                >
                  ตัวอย่างผลการประเมิน
                </Button>

                <Button
                  render={<Link href="/dashboard/viewer" />}
                  variant="editorialOutline"
                  size="xl"
                  className="w-full justify-center"
                >
                  ทดลองอัปโหลดไฟล์
                </Button>

                <Button
                  render={<Link href="/dashboard/map" />}
                  variant="editorialOutline"
                  size="xl"
                  className="w-full justify-center"
                >
                  ดูแผนที่
                </Button>
              </div>

              <dl className="mt-7 flex flex-wrap gap-3">
                {[
                  {
                    term: 'แยกลำต้น–ใบ ที่ใช้จริง',
                    value: baseline.backend,
                    shipped: true,
                  },
                  {
                    term: candidate.displayName,
                    value: candidate.status,
                    shipped: false,
                  },
                  {
                    term: 'จำแนกชนิดพันธุ์',
                    value: 'Stub',
                    shipped: false,
                  },
                ].map((fact) => (
                  <div
                    key={fact.term}
                    className={`relative flex flex-col justify-center rounded-xl border bg-paper px-4 py-3 pl-5 shadow-sm transition-colors ${
                      fact.shipped
                        ? 'border-moss/40'
                        : 'border-evidence-amber/30'
                    }`}
                  >
                    <div
                      className={`absolute left-0 top-0 h-full w-1.5 rounded-l-xl ${
                        fact.shipped
                          ? 'bg-moss'
                          : 'bg-evidence-amber'
                      }`}
                    />

                    <dt className="editorial-eyebrow-th text-xs text-canopy/80">
                      {fact.term}
                    </dt>

                    <dd
                      className={`mt-1 text-sm font-semibold tracking-tight ${
                        fact.shipped
                          ? 'text-forest-ink'
                          : 'text-evidence-amber'
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

              <div className="absolute inset-0 bg-gradient-to-b from-deep-forest/5 via-deep-forest/15 to-deep-forest/80" />
            </div>
          </div>

          <div className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-4 shadow-sm">
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
            title="ข้อจำกัดของการสำรวจแบบเดิม"
            description="การประเมินคาร์บอนในปัจจุบันต้องอาศัยการลงพื้นที่สำรวจทีละต้น ซึ่งใช้ต้นทุนสูง ใช้เวลานาน และยากต่อการตรวจสอบแหล่งที่มาของตัวเลขในภายหลัง"
          >
            <p className="max-w-3xl font-display text-3xl leading-snug text-deep-forest sm:text-4xl">
              เราไม่ได้มุ่งเน้นแค่ความแม่นยำของ AI
              แต่เราสร้างแพลตฟอร์มที่เปิดหลักฐานให้ตรวจสอบย้อนกลับได้
            </p>
          </EditorialSection>
        </div>

        <div id="how" data-editorial-beat="journey">
          <EditorialSection
            className="bg-gallery-ivory"
            title="วิธีทำงาน"
            description="ระบบแปลงข้อมูล Point Cloud สู่ตัวเลขคาร์บอนสะสมผ่าน 4 ขั้นตอนหลัก โดยระบุเทคนิคและสมการที่ใช้อย่างชัดเจน"
          >
            <div className="relative border-y border-hairline py-4">
              <div className="absolute bottom-0 left-[6.5rem] top-0 hidden w-[1px] bg-hairline sm:block" />

              <ol className="relative z-10">
                {JOURNEY.map((item) => (
                  <li
                    key={item.step}
                    className="group grid gap-4 border-b border-hairline py-8 last:border-b-0 sm:grid-cols-[5rem_minmax(0,1fr)_minmax(0,1.2fr)] sm:gap-8 sm:border-b-0 sm:pb-12"
                  >
                    <div className="flex items-start">
                      <span className="flex h-10 w-10 items-center justify-center rounded-full border border-evidence-amber bg-gallery-ivory font-mono text-sm font-medium text-evidence-amber shadow-sm transition-colors group-hover:bg-evidence-amber group-hover:text-paper">
                        {item.step}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-display text-2xl font-medium text-forest-ink">
                        {item.title}
                      </h3>

                      <p className="mt-3 text-base leading-relaxed text-canopy">
                        {item.description}
                      </p>
                    </div>

                    <div className="rounded-xl border border-hairline/50 bg-paper p-5 shadow-sm">
                      <TechnicalDetail>
                        <ul className="space-y-2">
                          {item.technical.map((line) => (
                            <li
                              key={line}
                              className="flex items-start gap-2 text-sm text-forest-ink/80"
                            >
                              <span className="mt-1.5 block h-1.5 w-1.5 shrink-0 rounded-full bg-evidence-amber/60" />
                              <span>{line}</span>
                            </li>
                          ))}
                        </ul>
                      </TechnicalDetail>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </EditorialSection>
        </div>

        <div
          id="tech"
          data-editorial-beat="three-dimensional-evidence"
        >
          <EditorialSection
            className="border-y border-hairline bg-paper"
            title="ตรวจสอบโมเดล"
            description="ผู้ใช้สามารถหมุนดูโมเดล 3 มิติ เพื่อตรวจสอบผลการจำแนกส่วนลำต้นเป็นสีน้ำตาลและใบเป็นสีเขียวได้อย่างอิสระ ให้คุณมั่นใจในความถูกต้องของโครงสร้างก่อนเข้าสู่กระบวนการคำนวณชีวมวล"
          >
            <div className="overflow-hidden rounded-[1.75rem] bg-deep-forest text-paper shadow-[0_24px_60px_-24px_rgba(14,42,29,0.45)]">
              <div className="grid lg:grid-cols-12">
                <div className="relative min-h-[28rem] overflow-hidden border-b border-paper/15 lg:col-span-7 lg:border-b-0 lg:border-r">
                  <ViewerStage
                    title="ต้นไม้ตัวอย่างจำลอง 3 ต้น"
                    evidenceLabel="การจำแนกส่วนลำต้น (Wood) และใบ (Leaf) ด้วยอัลกอริทึมเชิงเรขาคณิต"
                    positions={demoForest.positions}
                    classes={demoForest.classes}
                    labelled={demoForest.labelled}
                  >
                    <span className="editorial-eyebrow-th rounded-full border border-moss bg-deep-forest/80 px-3 py-1.5 text-lichen backdrop-blur-sm">
                      {demoForest.treeCount} ต้น ·{' '}
                      {nPoints.toLocaleString()} จุด
                    </span>
                  </ViewerStage>
                </div>

                <div className="flex flex-col justify-between p-6 sm:p-8 lg:col-span-5">
                  <div className="space-y-4">
                    <div className="rounded-xl border border-paper/15 bg-paper/5 p-4 transition-colors hover:border-paper/30">
                      <div className="flex items-center justify-between">
                        <span className="editorial-eyebrow-th text-xs text-lichen">
                          วิธีที่ใช้จริง
                        </span>

                        <span className="rounded-full bg-moss/20 px-2.5 py-0.5 text-[10px] font-medium text-paper">
                          Production
                        </span>
                      </div>

                      <h4 className="mt-1 font-display text-2xl font-semibold text-paper">
                        {baseline.backend}
                      </h4>

                      <p className="mt-1.5 text-xs leading-relaxed text-mist">
                        วิเคราะห์โครงสร้างทรงพุ่มและลำต้นด้วยหลักการทางเรขาคณิต
                        3 มิติ
                      </p>
                    </div>

                    <div className="rounded-xl border border-paper/15 bg-paper/5 p-4 transition-colors hover:border-paper/30">
                      <div className="flex items-center justify-between">
                        <span className="editorial-eyebrow-th text-xs text-evidence-amber">
                          ตัวที่ยังทดลองอยู่
                        </span>

                        <span className="rounded-full bg-evidence-amber/20 px-2.5 py-0.5 text-[10px] font-medium text-evidence-amber">
                          Experimental
                        </span>
                      </div>

                      <h4 className="mt-1 font-display text-2xl font-semibold text-paper">
                        {candidate.displayName}
                      </h4>

                      <p className="mt-1.5 text-xs leading-relaxed text-mist">
                        โมเดลทดลอง AI ผลยังไม่ผ่านเกณฑ์ทดสอบ
                        จึงยังไม่ได้นำมาใช้งานจริงในระบบ (
                        {candidate.status})
                      </p>
                    </div>

                    <div className="rounded-xl border border-paper/15 bg-paper/5 p-4 transition-colors hover:border-paper/30">
                      <div className="flex items-center justify-between">
                        <span className="editorial-eyebrow-th text-xs text-lichen">
                          ชุดสาธิตที่รันซ้ำได้
                        </span>

                        <span className="rounded-full bg-paper/10 px-2.5 py-0.5 text-[10px] font-medium text-paper">
                          Benchmark
                        </span>
                      </div>

                      <h4 className="mt-1 font-display text-2xl font-semibold text-paper tabular-nums">
                        {coreDemo.totalTrees} ต้น
                      </h4>

                      <p className="mt-1.5 text-xs leading-relaxed text-mist">
                        ชุดข้อมูลสาธิตมาตรฐานเพื่อยืนยันความเสถียร
                        มีผลลัพธ์คงที่เสมอ
                      </p>
                    </div>
                  </div>

                  <div className="mt-6 border-t border-paper/15 pt-4 text-[11px] text-mist/80">
                    💡 คลิกค้างแล้วลากเพื่อหมุน หรือใช้ Scroll
                    เพื่อซูมดูจุด Point Cloud แบบ 3D ได้อย่างอิสระ
                  </div>
                </div>
              </div>
            </div>
          </EditorialSection>
        </div>

        <div id="proof" data-editorial-beat="validation">
          <EditorialSection
            className="bg-gallery-ivory"
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

            <div className="mt-10 border-t border-hairline pt-10">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-moss/20 bg-moss/5 p-6 sm:p-8">
                  <h4 className="font-display text-xl font-medium text-forest-ink">
                    ทดสอบแล้ว
                  </h4>

                  <ul className="mt-5 space-y-3 text-sm leading-relaxed text-canopy">
                    <li className="flex gap-2">
                      <span className="text-moss">•</span>

                      <span>
                        การแยกลำต้นและใบ:
                        อ้างอิงผลลัพธ์จากรอบการฝึกที่ดีที่สุด
                        ซึ่งอาจมีค่าประเมินสูงกว่าการใช้งานจริงเล็กน้อย
                      </span>
                    </li>

                    <li className="flex gap-2">
                      <span className="text-moss">•</span>

                      <span>
                        การประเมินโครงสร้าง:
                        ทดสอบเฉพาะความแม่นยำทางเรขาคณิต
                        ขนาดและความสูง จากข้อมูลต้นไม้จริง 65 ต้น
                      </span>
                    </li>
                  </ul>
                </div>

                <div className="rounded-2xl border border-ember/20 bg-ember/5 p-6 sm:p-8">
                  <h4 className="font-display text-xl font-medium text-ember">
                    ขอบเขตที่ยังไม่ได้ทดสอบ
                  </h4>

                  <ul className="mt-5 space-y-3 text-sm leading-relaxed text-canopy">
                    <li className="flex gap-2">
                      <span className="text-ember">•</span>
                      <span>
                        ระบบทั้งเส้นตั้งแต่รับไฟล์จนได้ค่าคาร์บอน
                      </span>
                    </li>

                    <li className="flex gap-2">
                      <span className="text-ember">•</span>
                      <span>
                        การแยกชนิดพันธุ์ที่ยังเป็นโครงเปล่า
                      </span>
                    </li>

                    <li className="flex gap-2">
                      <span className="text-ember">•</span>

                      <span>
                        จำเป็นต้องทดสอบภาคสนามเพิ่มเติมกับชนิดพันธุ์ไม้ในไทย
                        และสอบเทียบสมการ (TGO ปี 2017)
                        สู่การเป็นเครื่องมือ Digital MRV
                      </span>
                    </li>
                  </ul>
                </div>
              </div>

              <div className="mt-8 flex flex-col items-start justify-between gap-6 rounded-xl bg-gallery-ivory p-6 sm:flex-row sm:items-center">
                <p className="max-w-xl text-sm font-medium leading-relaxed text-forest-ink">
                  * ค่าคาร์บอนและ CO₂e ที่แสดงเป็นเพียง
                  &quot;ค่าประมาณ&quot;
                  ไม่ใช่เครดิตคาร์บอนที่ผ่านการรับรอง
                  และเราไม่ได้กล่าวอ้างเรื่องตลาดซื้อขายเครดิต
                </p>

                <Button
                  render={<Link href="/demo" />}
                  variant="editorial"
                  size="lg"
                  className="shrink-0"
                >
                  เปิดหลักฐานใน Demo
                </Button>
              </div>
            </div>
          </EditorialSection>
        </div>
      </main>

      <footer className="border-t border-hairline bg-paper py-8">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-5 text-sm text-canopy sm:flex-row sm:px-8">
          <span className="font-display text-base text-forest-ink">
            TreeQ Carbon Platform
          </span>

          <span>Prototype for NSC 2026 · หมวด 14</span>
        </div>
      </footer>

      <ScrollToTop />
    </div>
  );
}