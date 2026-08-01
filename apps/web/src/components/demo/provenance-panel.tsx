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
  return (
    <section aria-labelledby="provenance-heading" className="text-sm text-forest-ink">
      <p className="editorial-eyebrow">Audit / provenance / reproducibility</p>
      <h2 id="provenance-heading" className="mt-2 font-display text-2xl">
        ที่มาของผลลัพธ์
      </h2>
      <p className="mt-2 max-w-3xl leading-6 text-canopy">
        ข้อมูลอ้างอิงถูกดึงจาก Manifest ที่ผ่านการตรวจสอบ Checksum
        เพื่อรับประกันความสามารถในการทำซ้ำ
      </p>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <AuditGroup title="Run identity">
          <AuditFact label="Schema" value={String(manifest.schema_version)} mono />
          <AuditFact label="Release status" value={manifest.release.status} mono />
          <AuditFact
            label="Worktree at analysis"
            value={manifest.git_dirty ? 'DIRTY' : 'CLEAN'}
            mono
          />
        </AuditGroup>

        <AuditGroup title="Git commit">
          <AuditFact
            label="Analyzed commit"
            value={manifest.analyzed_commit}
            displayValue={manifest.analyzed_commit.slice(0, 12)}
            mono
          />
        </AuditGroup>

        <AuditGroup title="Input / artifact hashes" className="lg:col-span-2">
          {Object.entries(manifest.artifacts).map(([label, artifact]) => (
            <div
              key={label}
              className="grid gap-1 border-b border-hairline py-3 last:border-b-0 sm:grid-cols-[7rem_minmax(0,1fr)] sm:gap-4"
            >
              <p className="font-mono text-[0.625rem] uppercase tracking-wide text-canopy">
                {label}
              </p>
              <div className="min-w-0">
                <p className="text-xs text-canopy">
                  {artifact.path} · {artifact.size_bytes.toLocaleString('en-US')} bytes
                </p>
                <p className="mt-1 break-all font-mono text-[0.6875rem] leading-5">
                  {artifact.sha256}
                </p>
              </div>
            </div>
          ))}
        </AuditGroup>

        <AuditGroup title="Pipeline / backend">
          <AuditFact label="Pipeline version" value={manifest.pipeline.version} mono />
          <AuditFact label="Wood / leaf backend" value={manifest.pipeline.backend} mono />
          <p className="mt-3 border-t border-hairline pt-3 text-xs leading-5 text-canopy">
            โมเดล PointNet++ กำหนดสิทธิ์อยู่ในระดับ{' '}
            <strong className="font-medium text-clay">Experimental</strong>{' '}
            โดยผลลัพธ์ชุดนี้อ้างอิงการประมวลผลผ่าน {manifest.pipeline.backend}
          </p>
        </AuditGroup>

        <AuditGroup title="Species status">
          <AuditFact label="Stage 7" value={manifest.pipeline.species} mono />
          <p className="mt-3 border-t border-hairline pt-3 text-xs leading-5 text-canopy">
            ระบบจำแนกสายพันธุ์ปัจจุบันเป็นเพียงโครงสร้างจำลอง
            ผลลัพธ์จึงไม่อ้างอิงจากการอนุมานของโมเดล AI
          </p>
        </AuditGroup>

        <AuditGroup title="Allometric source">
          <p className="leading-6 text-canopy">
            Pipeline รองรับ <span className="font-mono text-forest-ink">species_db.csv</span> และ
            Chave fallback แต่ manifest นี้ไม่บันทึกว่า artifact ใช้เส้นทางใด
            จึงไม่อ้างแหล่งสมการเฉพาะ run
          </p>
        </AuditGroup>

        <AuditGroup title="Limitations" emphasis>
          <p className="font-mono text-[0.625rem] uppercase tracking-wide text-evidence-amber">
            Dataset scope
          </p>
          <p className="mt-2 leading-6 text-mist">
            deterministic fixture สำหรับตรวจ reproducibility ไม่ใช่ชุดตรวจสอบ accuracy หรือ carbon
            validation
          </p>
          <p className="mt-3 border-t border-canopy pt-3 leading-6 text-mist">
            ค่า CO₂e เป็นค่าประมาณจากชีวมวล{' '}
            <strong className="font-semibold text-paper">
              ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรองหรือซื้อขายได้
            </strong>
          </p>
        </AuditGroup>
      </div>
    </section>
  );
}

function AuditGroup({
  title,
  children,
  className = '',
  emphasis = false,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  emphasis?: boolean;
}) {
  return (
    <section
      aria-label={title}
      className={`rounded-2xl border p-4 ${
        emphasis ? 'border-deep-forest bg-deep-forest text-paper' : 'border-hairline bg-paper'
      } ${className}`}
    >
      <h3
        className={`font-mono text-[0.625rem] uppercase tracking-[0.12em] ${
          emphasis ? 'text-lichen' : 'text-canopy'
        }`}
      >
        {title}
      </h3>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function AuditFact({
  label,
  value,
  displayValue = value,
  mono = false,
}: {
  label: string;
  value: string;
  displayValue?: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-hairline py-2 first:pt-0 last:border-b-0 last:pb-0">
      <span className="text-canopy">{label}</span>
      <span
        className={`min-w-0 break-all text-right ${mono ? 'font-mono text-xs' : ''}`}
        title={value}
      >
        {displayValue}
      </span>
    </div>
  );
}
