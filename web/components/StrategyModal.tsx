"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import type { StrategySeries } from "@/lib/data";

function signCls(v: number): string {
  return v > 0 ? "text-emerald-400" : v < 0 ? "text-rose-400" : "text-zinc-300";
}

function fmtPct(v: number): string {
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function fmtSharpe(v: number): string {
  return v.toFixed(2);
}

// Color the leading signed percentage inside a reason string, if any.
function renderReason(reason: string) {
  const m = reason.match(/([+-]?\d[\d,]*\.?\d*%)/);
  if (!m) return <span className="text-zinc-300">{reason}</span>;
  const idx = m.index ?? 0;
  const before = reason.slice(0, idx);
  const pct = m[0];
  const after = reason.slice(idx + pct.length);
  const num = parseFloat(pct.replace(/[+,%]/g, ""));
  const cls = pct.startsWith("-") || num < 0 ? "text-rose-400" : "text-emerald-400";
  return (
    <span className="text-zinc-300">
      {before}
      <span className={cls}>{pct}</span>
      {after}
    </span>
  );
}

interface Props {
  strategy: StrategySeries;
  color: string;
  onClose: () => void;
}

export default function StrategyModal({ strategy, color, onClose }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);

  // Esc to close + focus the close button + lock background scroll.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  const m = strategy.metrics;
  const metricStrip: { label: string; value: string; cls: string }[] = [
    { label: "CAGR", value: fmtPct(m.cagr), cls: signCls(m.cagr) },
    { label: "Sharpe", value: fmtSharpe(m.sharpe), cls: "text-zinc-200" },
    { label: "Max DD", value: fmtPct(m.max_drawdown), cls: "text-rose-400" },
    { label: "Total Return", value: fmtPct(m.total_return), cls: signCls(m.total_return) },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 px-3 py-8 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={`${strategy.name} — strategy details`}
      onClick={onClose}
    >
      <div
        className="w-full max-w-[720px] rounded border border-term-border bg-[#0d1220] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-term-border px-4 py-3">
          <div className="flex items-center gap-2 min-w-0">
            <span
              className="inline-block w-3 h-3 rounded-sm shrink-0"
              style={{ background: color }}
            />
            <h2 className="text-[13px] font-semibold text-zinc-100 truncate">
              {strategy.name}
            </h2>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 rounded-sm border border-term-border px-2 py-0.5 text-[12px] text-term-muted hover:border-rose-500/70 hover:text-rose-400 transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="flex flex-col gap-4 px-4 py-4">
          {/* Definition */}
          <section>
            <h3 className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
              Definition
            </h3>
            <p className="text-[11.5px] leading-relaxed text-zinc-300">
              {strategy.definition}
            </p>
          </section>

          {/* Methodology */}
          <section>
            <h3 className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
              How this backtest is computed
            </h3>
            <p className="text-[11.5px] leading-relaxed text-zinc-300">
              {strategy.methodology}
            </p>
          </section>

          {/* Metrics strip */}
          <section className="grid grid-cols-4 gap-2">
            {metricStrip.map((s) => (
              <div
                key={s.label}
                className="rounded border border-term-border bg-[#11182a] px-2 py-1.5 text-center"
              >
                <div className="text-[9px] uppercase tracking-wider text-term-muted">
                  {s.label}
                </div>
                <div className={`tnum text-[12px] font-semibold ${s.cls}`}>
                  {s.value}
                </div>
              </div>
            ))}
          </section>

          {/* Current portfolio */}
          <section>
            <h3 className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1.5">
              Current portfolio as of {strategy.decision_date}
            </h3>
            {strategy.holdings.length === 0 ? (
              <p className="text-[11px] text-term-muted">— no current holdings</p>
            ) : (
              <div className="rounded border border-term-border overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                  <thead>
                    <tr className="bg-[#11182a] text-term-muted uppercase tracking-wider text-[9px]">
                      <th className="text-right font-semibold px-2 py-1.5">Rank</th>
                      <th className="text-left font-semibold px-2 py-1.5">Symbol</th>
                      <th className="text-left font-semibold px-2 py-1.5">Entered</th>
                      <th className="text-left font-semibold px-2 py-1.5">Why</th>
                    </tr>
                  </thead>
                  <tbody>
                    {strategy.holdings
                      .slice()
                      .sort((a, b) => a.rank - b.rank)
                      .map((h) => (
                        <tr
                          key={h.symbol}
                          className="border-t border-term-border/60 hover:bg-[#11182a]/60"
                        >
                          <td className="px-2 py-1.5 text-right tnum text-term-muted">
                            {h.rank}
                          </td>
                          <td className="px-2 py-1.5">
                            <Link
                              href={`/stocks/${h.symbol}`}
                              className="tnum text-zinc-200 hover:text-emerald-400 transition-colors"
                            >
                              {h.symbol}
                            </Link>
                          </td>
                          <td className="px-2 py-1.5 tnum text-term-muted">
                            {h.entered}
                          </td>
                          <td className="px-2 py-1.5 text-[10.5px]">
                            {renderReason(h.reason)}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Footer disclaimer */}
          <p className="border-t border-term-border pt-2.5 text-[10px] text-term-muted">
            Educational illustration · survivorship-biased · not financial advice.
          </p>
        </div>
      </div>
    </div>
  );
}
