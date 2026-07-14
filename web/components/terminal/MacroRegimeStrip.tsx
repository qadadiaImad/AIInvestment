import type { MacroRegimeChip } from "@/lib/macro";
import { regimeColor, regimeLabel } from "@/lib/format";

// Reuses TrendBadge's pill visual idiom (color text + 1px border +
// 1a-alpha fill) inline rather than importing TrendBadge itself — TrendBadge
// is hardcoded to trend.state's bullish/bearish/mixed/unknown vocabulary via
// trendColor()/trendLabel(), the wrong vocabulary for a regime chip.
function Chip({ chip }: { chip: MacroRegimeChip }) {
  const color = regimeColor(chip.key, chip.state);
  return (
    <div
      className="shrink-0 w-[190px] flex flex-col gap-1.5 rounded-sm border border-term-border bg-[#0e131d] px-3 py-2.5"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-200 truncate">
          {chip.label}
        </span>
      </div>
      <span
        className="inline-flex items-center gap-1.5 self-start px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm"
        style={{
          color,
          border: `1px solid ${color}`,
          backgroundColor: `${color}1a`,
        }}
      >
        {regimeLabel(chip.state)}
      </span>
      <span className="text-[13px] font-semibold tnum text-zinc-100">
        {chip.value_label}
      </span>
      <span className="text-[9.5px] text-term-muted leading-snug">
        {chip.basis}
      </span>
    </div>
  );
}

// Horizontally-scrollable strip of exactly 4 chips from regime.chips —
// never resorted client-side (fixed order curve/real_rate/liquidity/vix).
export default function MacroRegimeStrip({
  chips,
}: {
  chips: MacroRegimeChip[];
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:thin]">
      {chips.map((chip) => (
        <Chip key={chip.key} chip={chip} />
      ))}
    </div>
  );
}
