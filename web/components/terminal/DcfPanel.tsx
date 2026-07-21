"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  runDcfWithUpside,
  sensitivityGrid,
  type DcfDefaultInputs,
  type DcfRunParams,
} from "@/lib/dcf";
import { DASH, num, price, signedPct } from "@/lib/format";

// Sliders for g1/r/gT seeded from buildDefaultDcfInputs(), live-recomputed on
// every change — mirrors StressControls.tsx's controlled-value pattern
// (useState<DcfRunParams> initialized once from server-computed defaults
// passed as props, <input type="range"> per knob, a "Reset to defaults"
// button). Caller (app/stocks/[symbol]/page.tsx) only renders this when
// defaults.baseFcf.value is non-null — see the guard in the caller and the
// belt-and-suspenders null render below.

const GT_MIN = 0;
const GT_MAX = 0.05;
const GT_STEP = 0.0025;
const R_MAX = 0.2;
const R_STEP = 0.0025;
const R_MIN_MARGIN = 0.005; // gT + 0.5pp — keeps r > gT practically unreachable
const G1_MIN = -0.15;
const G1_MAX = 0.35;
const G1_STEP = 0.005;

function pctFmt(v: number, dp = 2): string {
  return `${(v * 100).toFixed(dp)}%`;
}

function fairValueColor(upsidePct: number | null): string {
  if (upsidePct == null) return "text-zinc-300";
  if (upsidePct > 5) return "text-emerald-400";
  if (upsidePct < -5) return "text-rose-400";
  return "text-amber-400";
}

function basisLabel(basis: "pfcf" | "ps_margin" | "none"): string {
  if (basis === "pfcf") return "price / P-FCF";
  if (basis === "ps_margin") return "price / P-S × FCF margin";
  return "unavailable";
}

export default function DcfPanel({
  symbol,
  defaults,
}: {
  symbol: string;
  defaults: DcfDefaultInputs;
}) {
  const baseFcfPerShare = defaults.baseFcf.value;

  const initialParams: DcfRunParams | null =
    baseFcfPerShare != null
      ? {
          baseFcfPerShare,
          growthY1: defaults.growth.rate,
          terminalGrowth: defaults.terminalGrowth,
          discountRate: defaults.discount.rate,
          years: defaults.years,
        }
      : null;

  const [params, setParams] = useState<DcfRunParams | null>(initialParams);

  const result = useMemo(() => {
    if (!params) return null;
    return runDcfWithUpside(params, defaults.currentPrice);
  }, [params, defaults.currentPrice]);

  const grid = useMemo(() => {
    if (!params) return null;
    return sensitivityGrid(params);
  }, [params]);

  // Underivable — renders nothing (base FCF/share couldn't be derived from
  // any real fundamentals field; never fabricate a fallback here).
  if (!params || !result) {
    return null;
  }

  const minDiscount = Math.round((params.terminalGrowth + R_MIN_MARGIN) / R_STEP) * R_STEP;

  function update(patch: Partial<DcfRunParams>) {
    setParams((prev) => {
      if (!prev) return prev;
      const next = { ...prev, ...patch };
      // Keep r > gT practically unreachable: if gT moved above r - margin,
      // pull r up with it.
      const floor = next.terminalGrowth + R_MIN_MARGIN;
      if (next.discountRate < floor) {
        next.discountRate = floor;
      }
      return next;
    });
  }

  function reset() {
    setParams(initialParams);
  }

  const isDefault =
    params.growthY1 === initialParams!.growthY1 &&
    params.terminalGrowth === initialParams!.terminalGrowth &&
    params.discountRate === initialParams!.discountRate;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">
        <Link
          href={`/terminal/card/dcf/${symbol}`}
          className="text-[10.5px] px-2 py-1 border border-term-border rounded-sm text-term-muted hover:text-emerald-400 hover:border-emerald-500/50"
        >
          Capture card →
        </Link>
      </div>

      {/* Always-visible toy-model banner, not gated behind interaction. */}
      <div className="text-[10px] px-2 py-1 rounded-sm border border-amber-500/40 bg-amber-500/10 text-amber-300 font-semibold uppercase tracking-wider w-fit">
        TOY MODEL — educational, not a price target
      </div>

      {/* Fair value vs price */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="flex flex-col gap-0.5">
          <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
            Fair value / share
          </span>
          <span className="text-[15px] font-bold tnum text-zinc-100">
            {result.fairValuePerShare != null ? price(result.fairValuePerShare) : DASH}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
            Current price
          </span>
          <span className="text-[15px] font-bold tnum text-zinc-100">
            {defaults.currentPrice != null ? price(defaults.currentPrice) : DASH}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
            Upside / (discount)
          </span>
          <span className={`text-[15px] font-bold tnum ${fairValueColor(result.upsidePct)}`}>
            {result.upsidePct != null ? signedPct(result.upsidePct).text : DASH}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
            Model
          </span>
          <span className="text-[15px] font-bold tnum text-zinc-100">
            {result.valid ? "Valid" : "Invalid"}
          </span>
        </div>
      </div>

      {!result.valid && result.error && (
        <div className="text-[10.5px] text-rose-400">⚠ {result.error}</div>
      )}

      {/* Sliders */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 rounded-sm border border-term-border bg-[#0e131d] p-3">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="dcf-g1" className="text-[10px] uppercase tracking-wider text-term-muted">
              Growth Y1
            </label>
            <span className="tnum text-[11px] text-zinc-100">{pctFmt(params.growthY1)}</span>
          </div>
          <input
            id="dcf-g1"
            type="range"
            min={G1_MIN}
            max={G1_MAX}
            step={G1_STEP}
            value={params.growthY1}
            onChange={(e) => update({ growthY1: Number(e.target.value) })}
            className="accent-emerald-500 w-full"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="dcf-gt" className="text-[10px] uppercase tracking-wider text-term-muted">
              Terminal growth
            </label>
            <span className="tnum text-[11px] text-zinc-100">{pctFmt(params.terminalGrowth)}</span>
          </div>
          <input
            id="dcf-gt"
            type="range"
            min={GT_MIN}
            max={GT_MAX}
            step={GT_STEP}
            value={params.terminalGrowth}
            onChange={(e) => update({ terminalGrowth: Number(e.target.value) })}
            className="accent-amber-500 w-full"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="dcf-r" className="text-[10px] uppercase tracking-wider text-term-muted">
              Discount rate
            </label>
            <span className="tnum text-[11px] text-zinc-100">{pctFmt(params.discountRate)}</span>
          </div>
          <input
            id="dcf-r"
            type="range"
            min={minDiscount}
            max={R_MAX}
            step={R_STEP}
            value={params.discountRate}
            onChange={(e) => update({ discountRate: Number(e.target.value) })}
            className="accent-sky-500 w-full"
          />
        </div>

        <div className="sm:col-span-3">
          <button
            type="button"
            onClick={reset}
            disabled={isDefault}
            className={`text-[10.5px] px-2 py-1 rounded-sm border border-term-border uppercase tracking-wider transition-colors ${
              isDefault
                ? "text-zinc-600 cursor-default"
                : "text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
            }`}
          >
            Reset to defaults
          </button>
        </div>
      </div>

      {/* 5-year cash-flow table */}
      <div className="overflow-x-auto">
        <table className="term">
          <thead>
            <tr>
              <th>Year</th>
              <th className="numcell">Growth</th>
              <th className="numcell">FCF/share</th>
              <th className="numcell">Discount factor</th>
              <th className="numcell">PV</th>
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row) => (
              <tr key={row.year}>
                <td className="tnum">{row.year}</td>
                <td className="numcell tnum">{pctFmt(row.growth)}</td>
                <td className="numcell tnum">{price(row.fcf)}</td>
                <td className="numcell tnum">{num(row.discountFactor, 3)}</td>
                <td className="numcell tnum">{price(row.pv)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={4} className="text-term-muted">
                Sum PV (stage 1)
              </td>
              <td className="numcell tnum">{price(result.sumPvStage1)}</td>
            </tr>
            <tr>
              <td colSpan={4} className="text-term-muted">
                Terminal value (undiscounted)
              </td>
              <td className="numcell tnum">
                {result.valid ? price(result.terminalValue) : DASH}
              </td>
            </tr>
            <tr>
              <td colSpan={4} className="text-term-muted">
                PV of terminal value
              </td>
              <td className="numcell tnum">
                {result.valid ? price(result.pvTerminalValue) : DASH}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* 3x3 sensitivity grid */}
      {grid && (
        <div className="overflow-x-auto">
          <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
            Sensitivity — fair value/share (rows: discount rate Δ1pt, cols: growth Y1 Δ2pt)
          </div>
          <table className="term">
            <thead>
              <tr>
                <th>r \ g1</th>
                {grid[0].map((cell) => (
                  <th key={cell.growthDelta} className="numcell">
                    {pctFmt(cell.growthY1, 1)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.map((row) => (
                <tr key={row[0].discountDelta}>
                  <td className="tnum">{pctFmt(row[0].discountRate, 1)}</td>
                  {row.map((cell) => (
                    <td
                      key={cell.growthDelta}
                      className={`numcell tnum ${
                        cell.discountDelta === 0 && cell.growthDelta === 0
                          ? "text-emerald-400 font-semibold"
                          : ""
                      }`}
                    >
                      {cell.valid && cell.fairValuePerShare != null
                        ? price(cell.fairValuePerShare)
                        : DASH}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Basis / source disclosure */}
      <div className="text-[9.5px] text-term-muted flex flex-col gap-0.5">
        <span>
          Base FCF/share: {basisLabel(defaults.baseFcf.basis)} · Growth source:{" "}
          {defaults.growth.source === "actual" ? "reported rev YoY (clamped)" : "methodology default"}{" "}
          · Discount rate source:{" "}
          {defaults.discount.source === "macro_dgs10"
            ? `10Y Treasury + equity risk premium`
            : "flat fallback (macro.json unavailable)"}
        </span>
      </div>

      <p className="text-[9.5px] leading-snug text-term-muted">
        2-stage free-cash-flow DCF: 5 explicit forecast years with growth
        fading linearly to the terminal rate, then Gordon-growth terminal
        value. A methodology exercise over public fundamentals — not a
        prediction, not a price target, not investment advice.
      </p>
    </div>
  );
}
