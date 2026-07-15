import type { PortfolioPosition } from "@/lib/portfolio";
import { sortPositionsForDisplay } from "@/lib/portfolio";
import { DASH, dateOnly, layerLabel, num, price, signedPct, usd } from "@/lib/format";

function Cell({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-2.5 py-1.5 tnum whitespace-nowrap ${className}`}>{children}</td>;
}

// One row per positions[] entry, ordered by weight_pct desc (priced) then
// unpriced/unknown-symbol rows last (sortPositionsForDisplay — pure helper,
// unit-tested in lib/portfolio.test.ts). Dollar columns render here — this
// table is only ever mounted on the gated /terminal/portfolio page, never
// on the capture card.
export default function PortfolioHoldingsTable({
  positions,
}: {
  positions: PortfolioPosition[];
}) {
  const rows = sortPositionsForDisplay(positions);

  return (
    <div className="overflow-x-auto rounded-sm border border-term-border">
      <table className="w-full text-[11px] border-collapse">
        <thead>
          <tr className="border-b border-term-border text-term-muted uppercase tracking-wider text-[9.5px]">
            <th className="px-2.5 py-1.5 text-left">Symbol</th>
            <th className="px-2.5 py-1.5 text-left">Layer</th>
            <th className="px-2.5 py-1.5 text-right">Qty</th>
            <th className="px-2.5 py-1.5 text-right">Last</th>
            <th className="px-2.5 py-1.5 text-right">Mkt Value</th>
            <th className="px-2.5 py-1.5 text-right">Weight</th>
            <th className="px-2.5 py-1.5 text-right">Cost Basis</th>
            <th className="px-2.5 py-1.5 text-right">Unrealized P&amp;L</th>
            <th className="px-2.5 py-1.5 text-right">Day Chg</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={9} className="px-2.5 py-4 text-center text-term-muted">
                No positions.
              </td>
            </tr>
          ) : (
            rows.map((p) => {
              const unpriced = p.market_value_usd == null;
              const pnl = signedPct(p.unrealized_pnl_pct, 1);
              const day = signedPct(p.day_change_pct, 1);
              const fallback = p.price_source === "site_json_fallback";
              return (
                <tr
                  key={p.symbol}
                  className={`border-b border-term-border/60 last:border-b-0 ${unpriced ? "opacity-50" : ""}`}
                >
                  <Cell className="text-left font-semibold text-zinc-100">
                    {p.symbol}
                    {p.lots_merged > 1 && (
                      <span className="ml-1 text-[9.5px] font-normal text-term-muted">
                        ({p.lots_merged} lots)
                      </span>
                    )}
                    {unpriced && (
                      <span className="ml-1.5 inline-flex items-center px-1 py-px text-[8.5px] font-semibold uppercase tracking-wider rounded-sm border border-zinc-600 text-zinc-500">
                        unpriced
                      </span>
                    )}
                  </Cell>
                  <Cell className="text-left text-zinc-300">{layerLabel(p.layer)}</Cell>
                  <Cell className="text-right">{num(p.quantity, p.quantity % 1 === 0 ? 0 : 2)}</Cell>
                  <Cell className={`text-right ${fallback ? "text-zinc-500" : ""}`}>
                    {p.last_price != null ? (
                      <span title={fallback ? "site.json fallback quote — no day-change" : undefined}>
                        {price(p.last_price)}
                        <span className="ml-1 text-[9px] text-term-muted">{dateOnly(p.price_as_of)}</span>
                      </span>
                    ) : (
                      DASH
                    )}
                  </Cell>
                  <Cell className="text-right">{usd(p.market_value_usd)}</Cell>
                  <Cell className="text-right">
                    {p.weight_pct != null ? `${p.weight_pct.toFixed(1)}%` : DASH}
                  </Cell>
                  <Cell className="text-right text-zinc-400">{usd(p.cost_basis_total_usd)}</Cell>
                  <Cell className={`text-right font-semibold ${pnl.cls}`}>
                    {p.unrealized_pnl_usd != null ? `${usd(p.unrealized_pnl_usd)} ` : ""}
                    {pnl.text}
                  </Cell>
                  <Cell className={`text-right font-semibold ${day.cls}`}>
                    {p.day_change_usd != null ? `${usd(p.day_change_usd)} ` : ""}
                    {day.text}
                  </Cell>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
