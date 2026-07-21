import Link from "next/link";

// One mosaic tile — server component, no own state (rendered by the client
// RiskStackHeatmap parent, which owns the metric-toggle state and passes
// down the already-resolved color + label for the selected metric).
//
// Width (not full 2D treemap area) is proportional to sqrt(market_cap),
// normalized WITHIN the tile's own layer group by the caller (layerMaxMcap
// is that group's max, not the universe's max) — a true 2D treemap's
// packing math produces illegible tiny rectangles on a 375px phone and
// fights with wanting real >=44px-tall tap targets, so this stays a simple
// width-varying flex tile, same idiom as InstrumentTile.tsx.
export default function RiskHeatmapTile({
  symbol,
  marketCap,
  layerMaxMcap,
  bgColor,
  textColor,
  valueLabel,
}: {
  symbol: string;
  marketCap: number | null;
  layerMaxMcap: number;
  bgColor: string;
  textColor: string;
  valueLabel: string;
}) {
  const frac =
    marketCap != null && marketCap > 0 && layerMaxMcap > 0
      ? Math.sqrt(marketCap / layerMaxMcap)
      : 0;
  const width = Math.min(200, Math.max(72, 72 + 128 * frac));

  return (
    <Link
      href={`/stocks/${symbol}`}
      className="shrink-0 flex flex-col items-center justify-center gap-0.5 rounded-sm border border-black/20 hover:opacity-90 transition-opacity"
      style={{ width, height: 56, backgroundColor: bgColor, color: textColor }}
    >
      <span className="text-[12px] font-bold tracking-tight tnum">{symbol}</span>
      <span className="text-[10.5px] font-semibold tnum opacity-90">{valueLabel}</span>
    </Link>
  );
}
