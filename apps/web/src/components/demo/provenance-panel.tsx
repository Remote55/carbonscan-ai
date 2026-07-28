/**
 * Where the numbers came from, and what they are not.
 *
 * This is the closing beat of the judge journey: everything above is a claim,
 * and this panel is what makes the claim checkable. It only ever renders values
 * carried by the verified manifest, so it cannot describe a run that did not
 * happen.
 */
import type { FrozenDemoManifest } from '../../lib/frozen-demo';

export function ProvenancePanel({ manifest }: { manifest: FrozenDemoManifest }) {
  const facts: Array<{ label: string; value: string; mono?: boolean }> = [
    { label: 'Commit ที่ใช้วิเคราะห์', value: manifest.analyzed_commit.slice(0, 12), mono: true },
    { label: 'Worktree สะอาดตอนวิเคราะห์', value: manifest.git_dirty ? 'ไม่' : 'ใช่' },
    { label: 'รุ่นของไปป์ไลน์', value: manifest.pipeline.version, mono: true },
    { label: 'วิธีแยกลำต้น–ใบ', value: `${manifest.pipeline.backend} · baseline ที่ใช้จริง` },
    { label: 'การจำแนกชนิดพันธุ์', value: manifest.pipeline.species },
    { label: 'PointNet++', value: 'Experimental · ยังไม่ถูกเลื่อนเป็นค่าตั้งต้น' },
  ];

  return (
    <section aria-labelledby="provenance-heading" className="text-sm">
      <h2 id="provenance-heading" className="text-base font-semibold text-slate-900">
        ที่มาของผลลัพธ์
      </h2>

      <dl className="mt-4 grid gap-2 sm:grid-cols-2">
        {facts.map((fact) => (
          <div
            key={fact.label}
            className="flex items-baseline justify-between gap-4 rounded-xl border border-slate-200 px-4 py-3"
          >
            <dt className="text-slate-500">{fact.label}</dt>
            <dd className={fact.mono ? 'font-mono text-slate-900' : 'text-slate-900'}>
              {fact.value}
            </dd>
          </div>
        ))}
      </dl>

      <p className="mt-4 rounded-2xl bg-slate-100 p-4 leading-6 text-slate-700">
        ค่า CO₂e เป็นค่าประมาณจากชีวมวล <strong>ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรองหรือซื้อขายได้</strong>{' '}
        ชุดข้อมูลนี้เป็น fixture ที่ให้ผลเดิมทุกครั้งเพื่อแสดงว่าทำซ้ำได้ ไม่ใช่ชุดตรวจสอบความแม่นยำ
      </p>
    </section>
  );
}
