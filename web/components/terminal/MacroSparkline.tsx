import type { MacroSparkPoint } from "@/lib/macro";

// Standalone hand-rolled SVG sparkline for MacroSeries.sparkline ({t,v}[]
// shape) — NOT a reuse of components/Sparkline.tsx, which is hardcoded to
// usd()/EPS HistoryPoint ({date,value}) shape and would be the wrong shape
// here. Server component, pure SVG, no client JS. Emerald/rose stroke by
// direction of travel (up = last point >= first point in window).
export default function MacroSparkline({
  points,
  width = 110,
  height = 24,
}: {
  points: MacroSparkPoint[];
  width?: number;
  height?: number;
}) {
  const pts = (points ?? []).filter(
    (p): p is MacroSparkPoint =>
      typeof p.v === "number" && Number.isFinite(p.v),
  );

  if (pts.length < 2) {
    return <span className="text-term-muted text-[11px]">—</span>;
  }

  const values = pts.map((p) => p.v);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 2;
  const w = width;
  const h = height;

  const coords = pts.map((p, i) => {
    const x = pad + (i / (pts.length - 1)) * (w - 2 * pad);
    const y = pad + (1 - (p.v - min) / range) * (h - 2 * pad);
    return [x, y] as const;
  });

  const path = coords
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");

  const first = values[0];
  const last = values[values.length - 1];
  const up = last >= first;
  const stroke = up ? "#34d399" : "#fb7185";
  const [lastX, lastY] = coords[coords.length - 1];

  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      className="overflow-visible"
      aria-hidden="true"
    >
      <path d={path} fill="none" stroke={stroke} strokeWidth={1.25} />
      <circle cx={lastX} cy={lastY} r={1.6} fill={stroke} />
    </svg>
  );
}
