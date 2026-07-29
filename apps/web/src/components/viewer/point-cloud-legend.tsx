/** Colour legend for the point-cloud viewer (matches CLASS_COLORS). */

const LEGEND = [
  { label: 'ลำต้น / กิ่ง (Wood)', color: '#8C5C38' },
  { label: 'ใบไม้ (Leaf)', color: '#4D995C' },
  { label: 'พื้นดิน (Ground)', color: '#B8A37D' },
] as const;

export function PointCloudLegend() {
  return (
    <div className="bg-deep-forest/80 flex flex-wrap gap-x-4 gap-y-2 rounded-xl border border-moss px-3.5 py-2.5">
      {LEGEND.map((item) => (
        <div key={item.label} className="flex items-center gap-2">
          <span
            className="ring-paper/20 inline-block size-2 rounded-full ring-1"
            style={{ backgroundColor: item.color }}
          />
          <span className="font-mono text-[0.625rem] uppercase tracking-wide text-paper">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}
