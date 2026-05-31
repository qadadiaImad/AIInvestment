import type { Metadata } from "next";
import { getBacktests } from "@/lib/data";
import StrategiesInteractive from "@/components/StrategiesInteractive";

export const metadata: Metadata = {
  title: "Strategies · AI STACK",
  description:
    "Illustrative, survivorship-biased backtests of rules-based strategies over the AI value chain. Educational research only — not financial advice and not a trading system.",
};

const BENCHMARK_COLOR = "#d1d5db";
// Strategy palette: green / amber / violet, then cycle with extras.
const STRATEGY_COLORS = ["#10b981", "#f59e0b", "#8b5cf6", "#3b82f6", "#ec4899"];

const SCOPE_ORDER = [
  "all",
  "L0-energy",
  "L1-chips",
  "L2-infra",
  "L4-application",
];

export default function StrategiesPage() {
  const bt = getBacktests();
  const { window: win, params, scopes, survivorship_warning } = bt;

  return (
    <div className="flex flex-col px-3 py-3 gap-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          Strategies — illustrative backtests
        </h1>
        <span className="text-[10.5px] text-term-muted tnum">
          {win.start} → {win.end} · {params.rebalance} · {params.fees_pct}% fees ·{" "}
          {params.fundamental_lag_days}d fundamental lag
        </span>
      </div>

      {/* WARNING banner — impossible to miss */}
      <div
        role="alert"
        className="rounded border-2 border-amber-500/80 bg-amber-500/10 px-3 py-2.5 text-amber-200"
      >
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-amber-300">
          <span className="text-amber-400">▲</span>
          Survivorship-biased · illustrative only
        </div>
        <p className="mt-1 text-[11.5px] leading-relaxed text-amber-100/90">
          {survivorship_warning}
        </p>
      </div>

      {/* Scope dropdown + equity curve + clickable metrics table + cards → modal */}
      <StrategiesInteractive
        scopes={scopes}
        scopeOrder={SCOPE_ORDER}
        defaultScope="all"
        params={params}
        strategyColors={STRATEGY_COLORS}
        benchmarkColor={BENCHMARK_COLOR}
      />

      <p className="text-[10px] leading-relaxed text-term-muted border-t border-term-border pt-2">
        These backtests are <strong className="text-zinc-300">educational illustrations only</strong>.
        They are computed on today&apos;s surviving AI-stack names — they are{" "}
        <strong className="text-zinc-300">survivorship-biased</strong>, may embed lookahead
        in the signal, and ignore real-world frictions beyond a flat fee assumption.
        They are <strong className="text-zinc-300">not financial advice</strong> and{" "}
        <strong className="text-zinc-300">not a trading system</strong>. Past
        (hypothetical) performance does not predict future results.
      </p>
    </div>
  );
}
