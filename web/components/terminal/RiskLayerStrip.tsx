import Link from "next/link";
import type { RiskLayer } from "@/lib/risk";
import {
  DASH,
  layerLabel,
  pct,
  riskDivergingColor,
  riskMagnitudeColor,
  contrastText,
} from "@/lib/format";

// Domain ceilings for the sequential/diverging color scales at LAYER
// granularity (aggregates run calmer than single-name outliers, so these
// are tighter than the per-stock heatmap's domains).
const LAYER_DAY_CHANGE_DOMAIN = 5; // +/-5% full saturation
const LAYER_VAR_DOMAIN = 8; // 8% VaR95 -> full red
const LAYER_VOL_DOMAIN = 60; // 60% annualized vol -> full red

function Chip({ layer }: { layer: RiskLayer }) {
  const dayBg = riskDivergingColor(layer.day_change_pct, LAYER_DAY_CHANGE_DOMAIN);
  const varBg = riskMagnitudeColor(layer.median_var95_1d_pct, LAYER_VAR_DOMAIN);
  const volBg = riskMagnitudeColor(layer.vol_cap_weighted_pct, LAYER_VOL_DOMAIN);
  const sharpe = layer.best_sharpe_1y;
  const sharpeCls =
    layer.n_with_metrics === 0
      ? "text-zinc-500"
      : (layer.best_sharpe_1y ?? 0) >= 0
        ? "text-emerald-400"
        : "text-rose-400";

  return (
    <Link
      href="/terminal/risk"
      className="shrink-0 w-[168px] flex flex-col gap-2 rounded-sm border border-term-border bg-[#0e131d] px-3 py-2.5 hover:border-emerald-500/50 transition-colors"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-200">
          {layerLabel(layer.layer)}
        </span>
        <span className="text-[9.5px] text-term-muted tnum">
          {layer.n_with_metrics}/{layer.n_constituents}
        </span>
      </div>

      <div
        className="rounded-sm px-2 py-1 text-[13px] font-semibold tnum text-center"
        style={{ backgroundColor: dayBg, color: contrastText(dayBg) }}
      >
        {pct(layer.day_change_pct, 1)}
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        <div
          className="rounded-sm px-1.5 py-1 text-center"
          style={{ backgroundColor: varBg, color: contrastText(varBg) }}
        >
          <div className="text-[8.5px] uppercase tracking-wider opacity-80">VaR95</div>
          <div className="text-[11px] font-semibold tnum">
            {pct(layer.median_var95_1d_pct, 1)}
          </div>
        </div>
        <div
          className="rounded-sm px-1.5 py-1 text-center"
          style={{ backgroundColor: volBg, color: contrastText(volBg) }}
        >
          <div className="text-[8.5px] uppercase tracking-wider opacity-80">Vol</div>
          <div className="text-[11px] font-semibold tnum">
            {pct(layer.vol_cap_weighted_pct, 1)}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-[10px]">
        <span className="text-term-muted uppercase tracking-wider">Sharpe</span>
        <span className={`tnum font-semibold ${sharpeCls}`}>
          {sharpe != null ? sharpe.toFixed(2) : DASH}
        </span>
      </div>
    </Link>
  );
}

// Horizontally-scrollable strip of 5 layer chips (L0-L4, universe.layers
// order). VaR/vol use the sequential magnitude scale (never diverging);
// day% uses the diverging emerald/rose scale; Sharpe is plain colored text
// by sign only — deliberately NOT heat-mapped (a single-signed magnitude
// scale for Sharpe would be misleading, v1 cut per design doc §7.4).
export default function RiskLayerStrip({ layers }: { layers: RiskLayer[] }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:thin]">
      {layers.map((l) => (
        <Chip key={l.layer} layer={l} />
      ))}
    </div>
  );
}
