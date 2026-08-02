const LEGEND = [
  { label: 'ลำต้น / กิ่ง (Wood)', color: '#8C5C38' },
  { label: 'ใบไม้ (Leaf)', color: '#4D995C' },
  { label: 'พื้นดิน (Ground)', color: '#B8A37D' },
] as const;

export function PointCloudLegend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-2 rounded-xl border border-moss bg-deep-forest/80 px-3.5 py-2.5">
      {LEGEND.map((item) => (
        <div key={item.label} className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="inline-block size-3 rounded-full border-2 border-paper"
            style={{ backgroundColor: item.color }}
          />

          <span className="text-[0.625rem] font-medium tracking-wide text-paper">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}
