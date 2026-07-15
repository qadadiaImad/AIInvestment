import type { Metadata } from "next";
import Link from "next/link";
import { getPortfolioData, isPortfolioEmpty } from "@/lib/portfolio";
import { DASH, pct, ratio, usd } from "@/lib/format";
import TerminalSubNav from "@/components/terminal/TerminalSubNav";
import PortfolioLayerMix from "@/components/terminal/PortfolioLayerMix";
import PortfolioHoldingsTable from "@/components/terminal/PortfolioHoldingsTable";

// web/data/portfolio.json may not exist at Vercel build time (it's a
// gitignored, owner-generated file, computed from data/portfolio/
// positions.json by scripts/build_portfolio.py) — force dynamic rendering,
// same reasoning as terminal/risk and terminal/archetypes.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Portfolio · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

function StatTile({
  label,
  value,
  valueCls = "",
  sub,
}: {
  label: string;
  value: string;
  valueCls?: string;
  sub?: string;
}) {
  return (
    <div className="flex-1 min-w-[150px] flex flex-col gap-1 rounded-sm border border-term-border bg-[#0e131d] px-3 py-2.5">
      <span className="text-[9.5px] font-semibold uppercase tracking-wider text-term-muted">
        {label}
      </span>
      <span className={`text-[19px] font-bold tnum ${valueCls}`}>{value}</span>
      {sub && <span className="text-[10px] text-term-muted tnum">{sub}</span>}
    </div>
  );
}

export default function PortfolioDeskPage() {
  const data = getPortfolioData();
  const empty = isPortfolioEmpty(data);
  const agg = data?.aggregates ?? null;
  const risk = data?.risk ?? null;

  return (
    <div className="flex flex-col">
      <TerminalSubNav currentPath="/terminal/portfolio" />

      <div className="px-3 py-3 flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-lg font-bold tracking-tight">PORTFOLIO</h1>
          <div className="flex items-center gap-3">
            <span className="text-[10.5px] text-term-muted tnum">
              {data ? `Updated ${data.generated_at}` : ""}
            </span>
            {!empty && (
              <Link
                href="/terminal/card/portfolio"
                className="text-[10.5px] px-2 py-1 border border-term-border rounded-sm text-term-muted hover:text-emerald-400 hover:border-emerald-500/50"
              >
                Capture card →
              </Link>
            )}
          </div>
        </div>

        {empty ? (
          <div className="border border-term-border rounded-sm bg-[#0e131d] px-4 py-10 flex flex-col items-center justify-center text-center gap-2">
            <p className="text-[13px] text-zinc-300">
              {data
                ? // Bundle exists but was generated from a missing positions
                  // file — surface the exact copy-the-template message
                  // Python already produced, defined once, not duplicated
                  // here.
                  data.warnings[0]
                : "Portfolio data not generated yet."}
            </p>
            {!data && (
              <p className="text-[11px] text-term-muted">
                Run build_portfolio.py on the owner&apos;s machine.
              </p>
            )}
          </div>
        ) : (
          data && (
            <>
              {/* fixed-weight-proxy / NFA disclaimer banner */}
              <div className="rounded-sm border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200 leading-relaxed">
                <span className="font-semibold uppercase tracking-wider text-amber-300">
                  Indicative only.
                </span>{" "}
                Historical risk measures (volatility, VaR, Sharpe, beta,
                correlation) are backward-looking, computed on a
                fixed-weight proxy series (see methodology note below), and
                do not predict future losses. Not investment advice.
              </div>

              {/* Summary strip — dollar amounts render here, this page is
                  behind the terminal_key gate. */}
              <div className="flex flex-wrap gap-2">
                <StatTile label="Total Value" value={usd(agg?.total_value_usd)} />
                <StatTile
                  label="Day P&L"
                  value={`${usd(agg?.day_pnl_usd)} (${pct(agg?.day_pnl_pct, 2)})`}
                  valueCls={
                    (agg?.day_pnl_usd ?? 0) > 0
                      ? "text-emerald-400"
                      : (agg?.day_pnl_usd ?? 0) < 0
                        ? "text-rose-400"
                        : ""
                  }
                />
                <StatTile
                  label="Unrealized P&L"
                  value={`${usd(agg?.total_unrealized_pnl_usd)} (${pct(agg?.total_unrealized_pnl_pct, 2)})`}
                  valueCls={
                    (agg?.total_unrealized_pnl_usd ?? 0) > 0
                      ? "text-emerald-400"
                      : (agg?.total_unrealized_pnl_usd ?? 0) < 0
                        ? "text-rose-400"
                        : ""
                  }
                />
                <StatTile
                  label="Cash"
                  value={usd(agg?.cash_usd)}
                  sub={agg ? `${pct(agg.cash_weight_pct, 1)} of book` : undefined}
                />
              </div>

              {agg && <PortfolioLayerMix layerExposure={agg.layer_exposure} />}

              <section className="flex flex-col gap-2">
                <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
                  Holdings ({data.positions.length})
                </h2>
                <PortfolioHoldingsTable positions={data.positions} />
              </section>

              {/* Concentration + risk panel */}
              <section className="flex flex-col gap-2">
                <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
                  Concentration &amp; risk
                </h2>
                <div className="flex flex-wrap gap-2">
                  <StatTile label="Top 1 weight" value={pct(agg?.concentration.top1_weight_pct, 1)} />
                  <StatTile label="Top 3 weight" value={pct(agg?.concentration.top3_weight_pct, 1)} />
                  <StatTile
                    label="HHI"
                    value={agg?.concentration.hhi != null ? agg.concentration.hhi.toFixed(3) : DASH}
                  />
                  <StatTile label="Vol (ann.)" value={pct(risk?.vol_annualized_pct, 1)} />
                  <StatTile label="VaR95 1D" value={pct(risk?.var95_1d_pct, 1)} />
                  <StatTile label="Sharpe (1y)" value={ratio(risk?.sharpe_1y, 2)} />
                  <StatTile label="Beta vs SPY" value={ratio(risk?.beta_vs_spy, 2)} />
                  <StatTile
                    label="Max pairwise corr."
                    value={
                      risk?.max_pairwise_correlation
                        ? `${risk.max_pairwise_correlation.a}↔${risk.max_pairwise_correlation.b} ${risk.max_pairwise_correlation.value.toFixed(2)}`
                        : DASH
                    }
                  />
                </div>

                {risk ? (
                  <>
                    <div className="rounded-sm border border-term-border bg-[#0e131d] px-3 py-2.5 text-[11px] text-zinc-300 leading-relaxed">
                      {risk.methodology_note}
                    </div>
                    <p className="text-[10.5px] text-term-muted">
                      Risk series covers {pct(risk.series_coverage.weight_coverage_pct, 1)} of
                      invested value by weight ({risk.series_coverage.n_holdings_included}/
                      {risk.series_coverage.n_holdings_total_priced} priced holdings included).
                      {risk.series_coverage.weight_coverage_pct < 80 && (
                        <span className="text-amber-400">
                          {" "}
                          Below 80% coverage — treat vol/VaR/Sharpe/beta as indicative only.
                        </span>
                      )}
                    </p>
                    {risk.warnings.length > 0 && (
                      <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
                        {risk.warnings.map((w, i) => (
                          <span key={i}>⚠ {w}</span>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-[10.5px] text-term-muted">
                    No holdings have sufficient price history for a risk series (need
                    &gt;={data.params.min_bars} return bars each). Vol/VaR/Sharpe/beta above
                    show as {DASH}.
                  </p>
                )}
              </section>

              {(data.warnings.length > 0 ||
                data.positions.some((p) => p.warnings.length > 0)) && (
                <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
                  {data.warnings.map((w, i) => (
                    <span key={`b-${i}`}>⚠ {w}</span>
                  ))}
                  {data.positions.flatMap((p) =>
                    p.warnings.map((w, i) => <span key={`${p.symbol}-${i}`}>⚠ {w}</span>),
                  )}
                </div>
              )}

              {/* provenance line */}
              <p className="text-[10px] text-term-muted">
                Positions: {data.positions_source.path} (updated{" "}
                {data.positions_source.mtime ?? DASH}) · Prices: {data.prices_source.provider} (
                {data.prices_source.batch_retrieved_at ?? DASH})
              </p>

              {/* footer disclaimer */}
              <section className="border-t border-term-border pt-3">
                <p className="text-term-muted text-[11px] leading-relaxed">
                  {data.disclaimer} Historical risk measures (volatility, VaR, Sharpe, beta,
                  correlation) are backward-looking and do not predict future losses.
                  Educational / research only — not investment advice.
                </p>
              </section>
            </>
          )
        )}
      </div>
    </div>
  );
}
