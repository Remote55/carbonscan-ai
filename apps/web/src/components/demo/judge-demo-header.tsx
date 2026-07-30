import Image from 'next/image';

import { VISUAL_ASSETS } from '../../lib/visual-assets';
import type { DemoModeState } from '../../lib/demo-mode';
import { ModeBadge } from './mode-badge';

const JOURNEY = ['INPUT', 'VALIDATE', 'PIPELINE', 'RESULT', 'PROVENANCE'] as const;

export function JudgeDemoHeader({ state }: { state: Exclude<DemoModeState, { kind: 'booting' }> }) {
  const isLive = state.kind === 'production-live' || state.kind === 'local-live';

  return (
    <header className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-4">
        <a
          href="/"
          className="focus-ring rounded-sm font-medium uppercase tracking-[0.08em] text-forest-ink"
        >
          TreeQ Carbon
        </a>
        <p className="font-mono text-[0.625rem] uppercase tracking-[0.14em] text-canopy">
          Judge Demo · reliable evidence path
        </p>
      </div>

      <div className="relative isolate overflow-hidden rounded-[1.375rem] bg-deep-forest text-paper">
        <Image
          src={VISUAL_ASSETS.judge.src}
          alt=""
          fill
          priority
          sizes="(max-width: 1280px) 100vw, 1280px"
          className="-z-20 object-cover"
        />
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-deep-forest via-deep-forest/65 to-deep-forest/20" />

        <div className="grid min-h-[15.5rem] gap-8 p-6 sm:p-8 lg:grid-cols-[minmax(0,1fr)_minmax(32rem,0.9fr)] lg:items-end">
          <div>
            <p className="font-mono text-[0.625rem] uppercase tracking-[0.16em] text-lichen">
              Judge Demo / 3–5 minutes / reliable path
            </p>
            <h1 className="mt-4 max-w-2xl text-balance font-display text-3xl font-medium leading-tight sm:text-4xl">
              {isLive ? (
                <>
                  พร้อมรับ point cloud จริง
                  <br />
                  โดยยังเปิดหลักฐาน frozen ได้เสมอ
                </>
              ) : (
                <>
                  เริ่มจากหลักฐานที่ freeze แล้ว
                  <br />
                  และบอกข้อจำกัดทุกขั้น
                </>
              )}
            </h1>
            <div className="mt-5">
              <ModeBadge state={state} />
            </div>
          </div>

          <ol
            className="grid grid-cols-2 gap-2 sm:grid-cols-5"
            aria-label="เส้นทางสาธิตห้าขั้น"
          >
            {JOURNEY.map((step, index) => (
              <li
                key={step}
                className="rounded-xl border border-moss bg-deep-forest/75 px-3 py-2.5 backdrop-blur-sm"
              >
                <span className="block font-mono text-[0.5625rem] text-lichen">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <span className="mt-1 block font-mono text-[0.5625rem] tracking-[0.08em]">
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </header>
  );
}
