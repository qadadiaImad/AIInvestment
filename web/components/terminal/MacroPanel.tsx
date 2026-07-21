import type { MacroSeries } from "@/lib/macro";
import { macroUnitLabel, macroValue, signedPct } from "@/lib/format";
import MacroSparkline from "@/components/terminal/MacroSparkline";

// Clone of InstrumentTile.tsx but a plain <div> (NOT a Link — no
// per-symbol detail page this round). Flat #0e131d background, no
// heat-tinting — this is a "read the number" desk, not the risk desk's
// "scan for outliers" heatmap.
export default function MacroPanel({ series }: { series: MacroSeries }) {
  const chg = signedPct(series.change_pct);

  return (
    <div className="min-h-[44px] flex flex-col gap-1.5 border border-term-border rounded-sm bg-[#0e131d] px-2.5 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="font-bold text-[13px] tracking-tight truncate">
          {series.symbol}
        </span>
        <span className="text-[9.5px] text-term-muted uppercase tracking-wider truncate">
          {series.display_name}
        </span>
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-[18px] font-bold tnum">
          {macroValue(series.last, series.unit_kind, series.decimals)}
        </span>
        <span className={`text-[11px] tnum ${chg.cls}`}>{chg.text}</span>
      </div>

      <MacroSparkline points={series.sparkline} width={110} height={24} />

      <div className="text-[10px] tnum text-term-muted truncate">
        {macroUnitLabel(series.unit, series.unit_kind)} · as of {series.as_of ?? "—"}
      </div>
    </div>
  );
}
