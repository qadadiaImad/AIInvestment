import type { HistoryPoint } from "@/lib/data";
import { usd, num } from "@/lib/format";

interface Props {
  series?: HistoryPoint[];
  width?: number;
  height?: number;
  isEps?: boolean;
}

export default function Sparkline({
  series,
  width = 120,
  height = 30,
  isEps = false,
}: Props) {
  const points = (series ?? []).filter(
    (p): p is { date: string; value: number } =>
      typeof p.value === "number" && Number.isFinite(p.value)
  );

  if (points.length < 2) {
    return <span className="text-term-muted text-[11px]">—</span>;
  }

  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 2;
  const w = width;
  const h = height;

  const coords = points.map((p, i) => {
    const x = pad + (i / (points.length - 1)) * (w - 2 * pad);
    const y = pad + (1 - (p.value - min) / range) * (h - 2 * pad);
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

  const fmt = (v: number) => (isEps ? `$${num(v, 2)}` : usd(v));

  return (
    <span className="inline-flex items-center gap-2">
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
      <span className="text-[10.5px] text-term-muted tnum whitespace-nowrap">
        {fmt(first)} → <span className="text-zinc-300">{fmt(last)}</span>
      </span>
    </span>
  );
}
