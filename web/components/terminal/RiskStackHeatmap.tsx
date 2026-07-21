"use client";

import { useState } from "react";
import type { RiskLayer, RiskStock } from "@/lib/risk";
import {
  contrastText,
  layerColor,
  layerLabel,
  pct,
  riskDivergingColor,
  riskMagnitudeColor,
} from "@/lib/format";
import RiskHeatmapTile from "@/components/terminal/RiskHeatmapTile";

type Metric = "day" | "var95" | "vol";

const METRICS: { key: Metric; label: string }[] = [
  { key: "day", label: "DAY %" },
  { key: "var95", label: "VaR95" },
  { key: "vol", label: "VOL" },
];

// Per-stock (single-name) domain ceilings — wider than the layer-strip's
// aggregate domains since one name can swing much harder than a
// diversified layer aggregate.
const DAY_CHANGE_DOMAIN = 8; // +/-8% -> full saturation
const VAR_DOMAIN = 12; // 12% VaR95 -> full red
const VOL_DOMAIN = 100; // 100% annualized vol -> full red

function metricFor(stock: RiskStock, metric: Metric): number | null {
  if (metric === "day") return stock.day_change_pct;
  if (metric === "var95") return stock.var95_1d_pct;
  return stock.vol_annualized_pct;
}

function colorFor(value: number | null, metric: Metric): string {
  if (metric === "day") return riskDivergingColor(value, DAY_CHANGE_DOMAIN);
  if (metric === "var95") return riskMagnitudeColor(value, VAR_DOMAIN);
  return riskMagnitudeColor(value, VOL_DOMAIN);
}

// One mosaic section PER LAYER (reuses GroupSection.tsx's section-header
// idiom, keyed by AI layer). Metric toggle (day% | VaR95 | vol) is local
// client state — the only client-side bit of this page.
export default function RiskStackHeatmap({
  layers,
  stocksByLayer,
}: {
  layers: RiskLayer[];
  stocksByLayer: Record<string, RiskStock[]>;
}) {
  const [metric, setMetric] = useState<Metric>("day");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-1.5">
        {METRICS.map((m) => (
          <button
            key={m.key}
            type="button"
            onClick={() => setMetric(m.key)}
            className={
              metric === m.key
                ? "px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider rounded-sm border border-emerald-500/60 text-emerald-400 bg-emerald-500/10"
                : "px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider rounded-sm border border-term-border text-term-muted hover:text-zinc-200"
            }
          >
            {m.label}
          </button>
        ))}
      </div>

      {layers.map((layer) => {
        const stocks = (stocksByLayer[layer.layer] ?? [])
          .slice()
          .sort((a, b) => (b.market_cap ?? -1) - (a.market_cap ?? -1));
        const color = layerColor(layer.layer);

        return (
          <section key={layer.layer} className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: color }}
                aria-hidden="true"
              />
              <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
                {layerLabel(layer.layer)}
              </h2>
              <span className="text-[10px] text-term-muted">{stocks.length}</span>
            </div>

            {stocks.length === 0 ? (
              <div className="rounded-sm border border-term-border bg-[#0e131d] px-3 py-3 text-[11px] text-term-muted">
                No direct listed constituents — see correlation footnote.
              </div>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {(() => {
                  const layerMaxMcap =
                    stocks.reduce(
                      (max, x) => (x.market_cap != null ? Math.max(max, x.market_cap) : max),
                      0,
                    ) || 1;
                  return stocks.map((s) => {
                    const value = metricFor(s, metric);
                    const bg = colorFor(value, metric);
                    return (
                      <RiskHeatmapTile
                        key={s.symbol}
                        symbol={s.symbol}
                        marketCap={s.market_cap}
                        layerMaxMcap={layerMaxMcap}
                        bgColor={bg}
                        textColor={contrastText(bg)}
                        valueLabel={pct(value, 1)}
                      />
                    );
                  });
                })()}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
