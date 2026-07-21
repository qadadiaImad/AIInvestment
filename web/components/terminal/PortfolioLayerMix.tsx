import type { PortfolioLayerExposure } from "@/lib/portfolio";
import { layerColor, layerLabel, pct, usd } from "@/lib/format";

// Distinct neutral swatches for the two non-AI-stack buckets that
// layerColor() would otherwise both paint the same generic grey
// ("unclassified" priced-but-off-universe positions vs. "cash") — kept
// local to this component since no other desk needs a cash/unclassified
// split.
const UNCLASSIFIED_COLOR = "#6b7280"; // zinc-500 — matches layerColor(null)
const CASH_COLOR = "#a1a1aa"; // zinc-400 — lighter, visually distinct from unclassified

function swatchColor(layer: string): string {
  if (layer === "cash") return CASH_COLOR;
  if (layer === "unclassified") return UNCLASSIFIED_COLOR;
  return layerColor(layer);
}

// Horizontal 100%-stacked bar of layer_exposure by weight_pct (percent-only
// on the bar itself), plus a legend row underneath. market_value_usd is
// shown ONLY in the legend, not on the bar — this component is used on the
// gated /terminal/portfolio page (dollar amounts allowed there), never on
// the capture card (PortfolioCaptureCard has its own percent-only mini bar
// built straight from PortfolioCardData, it does not reuse this
// component).
export default function PortfolioLayerMix({
  layerExposure,
}: {
  layerExposure: PortfolioLayerExposure[];
}) {
  const segments = layerExposure.filter((l) => l.weight_pct > 0);

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
        Layer mix
      </h2>

      <div className="h-6 w-full rounded-sm overflow-hidden flex border border-term-border">
        {segments.length === 0 ? (
          <div className="w-full h-full bg-[#1a2130]" />
        ) : (
          segments.map((l) => (
            <div
              key={l.layer}
              style={{
                width: `${l.weight_pct}%`,
                backgroundColor: swatchColor(l.layer),
              }}
              title={`${layerLabel(l.layer) === "—" ? l.layer.toUpperCase() : layerLabel(l.layer)} ${pct(l.weight_pct, 1)}`}
            />
          ))
        )}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {layerExposure.map((l) => (
          <div key={l.layer} className="flex items-center gap-1.5 text-[10.5px]">
            <span
              className="w-2.5 h-2.5 rounded-[2px] shrink-0"
              style={{ backgroundColor: swatchColor(l.layer) }}
            />
            <span className="text-zinc-300 uppercase tracking-wider">
              {l.layer === "cash" ? "CASH" : l.layer === "unclassified" ? "UNCLASSIFIED" : layerLabel(l.layer)}
            </span>
            <span className="text-term-muted tnum">{pct(l.weight_pct, 1)}</span>
            <span className="text-term-muted tnum">({usd(l.market_value_usd)})</span>
          </div>
        ))}
      </div>
    </section>
  );
}
