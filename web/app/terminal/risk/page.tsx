import type { Metadata } from "next";
import Link from "next/link";
import { getRiskData, getRiskStocksByLayer } from "@/lib/risk";
import TerminalSubNav from "@/components/terminal/TerminalSubNav";
import RiskLayerStrip from "@/components/terminal/RiskLayerStrip";
import RiskStackHeatmap from "@/components/terminal/RiskStackHeatmap";
import RiskCorrelationMatrix from "@/components/terminal/RiskCorrelationMatrix";

// risk.json may not exist at Vercel build time (it's a gitignored, owner-
// generated file) — force dynamic rendering, same reasoning as
// terminal/[symbol]/page.tsx.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Risk Desk · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default function RiskDeskPage() {
  const data = getRiskData();
  const stocksByLayer = getRiskStocksByLayer();

  return (
    <div className="flex flex-col">
      <TerminalSubNav currentPath="/terminal/risk" />

      <div className="px-3 py-3 flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-lg font-bold tracking-tight">RISK DESK</h1>
          <div className="flex items-center gap-3">
            <span className="text-[10.5px] text-term-muted tnum">
              {data ? `Updated ${data.generated_at}` : ""}
            </span>
            {data && (
              <Link
                href="/terminal/card/risk"
                className="text-[10.5px] px-2 py-1 border border-term-border rounded-sm text-term-muted hover:text-emerald-400 hover:border-emerald-500/50"
              >
                Capture card →
              </Link>
            )}
          </div>
        </div>

        {!data ? (
          <div className="border border-term-border rounded-sm bg-[#0e131d] px-4 py-10 flex flex-col items-center justify-center text-center gap-2">
            <p className="text-[13px] text-zinc-300">
              Risk desk data not generated yet.
            </p>
            <p className="text-[11px] text-term-muted">
              Run build_risk.py on the owner&apos;s machine.
            </p>
          </div>
        ) : (
          <>
            {/* indicative disclaimer banner */}
            <div className="rounded-sm border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200 leading-relaxed">
              <span className="font-semibold uppercase tracking-wider text-amber-300">
                Indicative only.
              </span>{" "}
              VaR is historical/non-parametric, 1-day, 95% confidence — not a
              dollar-loss guarantee, not investment advice.
            </div>

            <RiskLayerStrip layers={data.per_layer} />

            <RiskStackHeatmap layers={data.per_layer} stocksByLayer={stocksByLayer} />

            <section className="flex flex-col gap-2">
              <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
                Correlation
              </h2>
              <RiskCorrelationMatrix
                layers={data.correlations.layers}
                topStocks={data.correlations.top_stocks}
              />
            </section>

            {data.warnings.length > 0 && (
              <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
                {data.warnings.map((w, i) => (
                  <span key={i}>⚠ {w}</span>
                ))}
              </div>
            )}

            {/* footer disclaimer */}
            <section className="border-t border-term-border pt-3">
              <p className="text-term-muted text-[11px] leading-relaxed">
                {data.disclaimer} Historical risk measures (volatility, VaR,
                Sharpe, drawdown, correlation) are backward-looking and do
                not predict future losses. Educational / research only — not
                investment advice.
              </p>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
