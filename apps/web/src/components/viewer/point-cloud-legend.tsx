/** Colour legend for the point-cloud viewer (matches CLASS_COLORS). */

const LEGEND = [
  { label: "ลำต้น / กิ่ง (Wood)", color: "#8C5C38" },
  { label: "ใบไม้ (Leaf)", color: "#4D995C" },
  { label: "พื้นดิน (Ground)", color: "#B8A37D" },
] as const;

export function PointCloudLegend() {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-2">
      {LEGEND.map((item) => (
        <div key={item.label} className="flex items-center gap-2 text-sm">
          <span
            className="inline-block h-3 w-3 rounded-full ring-1 ring-foreground/10"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-muted-foreground">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
