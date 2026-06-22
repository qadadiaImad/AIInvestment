"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { BacktestMetrics, BacktestScope } from "@/lib/data";
import StrategyModal from "./StrategyModal";
import EquityCurveChart, { type EquityLine } from "./EquityCurveChart";

type MetricKey = keyof BacktestMetrics;

function signCls(v: number): string {
  return v > 0 ? "text-emerald-400" : v < 0 ? "text-rose-400" : "text-zinc-300";
}
function fmtPct(v: number): string {
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}
function fmtSharpe(v: number): string {
  return v.toFixed(2);
}

const metricCols: { key: MetricKey; label: string }[] = [
  { key: "total_return", label: "Total Return %" },
  { key: "cagr", label: "CAGR %" },
  { key: "sharpe", label: "Sharpe" },
  { key: "max_drawdown", label: "Max DD %" },
];

function fmtMetric(key: MetricKey, v: number): string {
  return key === "sharpe" ? fmtSharpe(v) : fmtPct(v);
}
function metricCls(key: MetricKey, v: number): string {
  if (key === "sharpe") return "text-zinc-200";
  if (key === "max_drawdown") return "text-rose-400";
  return signCls(v);
}

interface Props {
  scopes: Record<string, BacktestScope>;
  scopeOrder: string[];
  defaultScope: string;
  params: { rebalance: string; fees_pct: number; fundamental_lag_days: number };
  strategyColors: string[];
  benchmarkColor: string;
}

export default function StrategiesInteractive({
  scopes,
  scopeOrder,
  defaultScope,
  params,
  strategyColors,
  benchmarkColor,
}: Props) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [scopeKey, setScopeKey] = useState<string>(defaultScope);

  const scope = scopes[scopeKey] ?? scopes[defaultScope];
  const { strategies, benchmark } = scope;

  const colorOf = (i: number) => strategyColors[i % strategyColors.length];

  // Chart lines: benchmark first (so strategies render on top), then strategies.
  const lines: EquityLine[] = useMemo(
    () => [
      { name: benchmark.name, color: benchmarkColor, equity: benchmark.equity },
      ...strategies.map((s, i) => ({
        name: s.name,
        color: colorOf(i),
        equity: s.equity,
      })),
    ],
    // colorOf is derived from a stable prop array
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [strategies, benchmark, benchmarkColor]
  );
  const open = strategies.find((s) => s.key === openKey) ?? null;
  const openColor = open ? colorOf(strategies.findIndex((s) => s.key === open.key)) : "";

  // Metrics table rows: strategies (clickable) then benchmark (not clickable).
  const rows = [
    ...strategies.map((s, i) => ({
      key: s.key,
      label: s.name,
      color: colorOf(i),
      metrics: s.metrics,
      clickable: true as const,
    })),
    {
      key: "__benchmark__",
      label: benchmark.name,
      color: benchmarkColor,
      metrics: benchmark.metrics,
      clickable: false as const,
    },
  ];

  // Best per column (higher is better; max_drawdown least-negative is best).
  const bestByCol: Record<MetricKey, number> = {
    total_return: -Infinity,
    cagr: -Infinity,
    sharpe: -Infinity,
    max_drawdown: -Infinity,
  };
  for (const col of metricCols) {
    let best = -Infinity;
    for (const r of rows) {
      const v = r.metrics[col.key];
      if (v > best) best = v;
    }
    bestByCol[col.key] = best;
  }

  function activate(key: string) {
    setOpenKey(key);
  }
  function rowKeyDown(e: React.KeyboardEvent, key: string) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      activate(key);
    }
  }

  return (
    <>
      {/* Scope selector + params caption */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <label className="flex items-center gap-2 text-[11px] text-zinc-300">
          <span className="uppercase tracking-wider text-term-muted text-[10px]">
            Scope
          </span>
          <select
            value={scopeKey}
            onChange={(e) => {
              setScopeKey(e.target.value);
              setOpenKey(null);
            }}
            aria-label="Backtest scope (AI layer)"
            className="rounded border border-term-border bg-[#11182a] px-2 py-1 text-[11px] text-zinc-200 focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/50"
          >
            {scopeOrder
              .filter((k) => scopes[k])
              .map((k) => (
                <option key={k} value={k} className="bg-[#11182a] text-zinc-200">
                  {scopes[k].label} ({scopes[k].universe})
                </option>
              ))}
          </select>
        </label>
        <span className="text-[10.5px] text-term-muted tnum">
          top {scope.top_n} of {scope.universe} names · {params.rebalance} ·{" "}
          {params.fees_pct}% fees · {params.fundamental_lag_days}d fundamental lag
        </span>
      </div>

      {/* Combined equity curve */}
      <section className="rounded border border-term-border bg-[#0d1220] px-3 py-3">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Growth of $1 — strategies vs. benchmark
        </h2>
        <EquityCurveChart lines={lines} />
      </section>

      {/* Metrics table */}
      <section className="rounded border border-term-border overflow-x-auto">
        <table className="w-full text-[11.5px] border-collapse">
          <thead>
            <tr className="bg-[#11182a] text-term-muted uppercase tracking-wider text-[10px]">
              <th className="text-left font-semibold px-3 py-2">Strategy</th>
              {metricCols.map((c) => (
                <th key={c.key} className="text-right font-semibold px-3 py-2">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.key}
                role={r.clickable ? "button" : undefined}
                tabIndex={r.clickable ? 0 : undefined}
                aria-label={r.clickable ? `Open ${r.label} details` : undefined}
                onClick={r.clickable ? () => activate(r.key) : undefined}
                onKeyDown={r.clickable ? (e) => rowKeyDown(e, r.key) : undefined}
                className={`border-t border-term-border/60 hover:bg-[#11182a]/60 ${
                  r.clickable
                    ? "cursor-pointer focus:outline-none focus:bg-[#11182a] focus:ring-1 focus:ring-emerald-500/50"
                    : ""
                }`}
              >
                <td className="px-3 py-1.5">
                  <span className="inline-flex items-center gap-2">
                    <span
                      className="inline-block w-3 h-[2px]"
                      style={{ background: r.color }}
                    />
                    <span className="text-zinc-200">{r.label}</span>
                  </span>
                </td>
                {metricCols.map((c) => {
                  const v = r.metrics[c.key];
                  const isBest = v === bestByCol[c.key];
                  return (
                    <td
                      key={c.key}
                      className={`px-3 py-1.5 text-right tnum ${metricCls(c.key, v)} ${
                        isBest ? "font-bold" : ""
                      }`}
                    >
                      {fmtMetric(c.key, v)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Per-strategy cards */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {strategies.map((s, i) => {
          const color = colorOf(i);
          return (
            <div
              key={s.key}
              role="button"
              tabIndex={0}
              aria-label={`Open ${s.name} details`}
              onClick={() => activate(s.key)}
              onKeyDown={(e) => rowKeyDown(e, s.key)}
              className="cursor-pointer rounded border border-term-border bg-[#0d1220] px-3 py-3 flex flex-col gap-2.5 transition-colors hover:border-emerald-500/50 hover:bg-[#11182a]/40 focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/50"
            >
              <div className="flex items-center gap-2">
                <span
                  className="inline-block w-3 h-3 rounded-sm shrink-0"
                  style={{ background: color }}
                />
                <h3 className="text-[12px] font-semibold text-zinc-200">{s.name}</h3>
              </div>

              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
                <Metric label="Total Return" value={fmtPct(s.metrics.total_return)} cls={signCls(s.metrics.total_return)} />
                <Metric label="CAGR" value={fmtPct(s.metrics.cagr)} cls={signCls(s.metrics.cagr)} />
                <Metric label="Sharpe" value={fmtSharpe(s.metrics.sharpe)} cls="text-zinc-200" />
                <Metric label="Max DD" value={fmtPct(s.metrics.max_drawdown)} cls="text-rose-400" />
              </div>

              <div>
                <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
                  Current holdings
                </div>
                <div className="flex flex-wrap gap-1">
                  {s.current_holdings.length === 0 ? (
                    <span className="text-[10.5px] text-term-muted">—</span>
                  ) : (
                    s.current_holdings.map((sym) => (
                      <Link
                        key={sym}
                        href={`/stocks/${sym}`}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded-sm border border-term-border bg-[#11182a] px-1.5 py-0.5 text-[10px] tnum text-zinc-300 hover:border-emerald-500/70 hover:text-emerald-400 transition-colors"
                      >
                        {sym}
                      </Link>
                    ))
                  )}
                </div>
              </div>

              <div className="text-[9.5px] text-term-muted mt-auto pt-1">
                Click for definition, methodology &amp; portfolio →
              </div>
            </div>
          );
        })}
      </section>

      {open && (
        <StrategyModal
          strategy={open}
          color={openColor}
          onClose={() => setOpenKey(null)}
        />
      )}
    </>
  );
}

function Metric({ label, value, cls }: { label: string; value: string; cls: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-term-muted">{label}</span>
      <span className={`tnum font-semibold ${cls}`}>{value}</span>
    </div>
  );
}
