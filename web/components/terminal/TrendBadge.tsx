import { trendColor, trendLabel } from "@/lib/format";

// Mirrors LayerChip.tsx exactly — same chip shape/sizing, TA-desk colors.
export default function TrendBadge({ state }: { state?: string | null }) {
  const color = trendColor(state);
  return (
    <span
      className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm align-middle"
      style={{
        color,
        border: `1px solid ${color}`,
        backgroundColor: `${color}1a`,
      }}
    >
      {trendLabel(state)}
    </span>
  );
}
