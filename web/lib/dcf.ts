// web/lib/dcf.ts
// Pure, client-safe 2-stage FCF DCF. No I/O. Every function here is a plain
// function of its arguments — safe to call on every slider tick in a "use
// client" component, and reusable server-side for the capture card's fixed
// defaults. TOY MODEL: educational, not a price target. See CLAUDE.md rule 1
// (stamp everything) — callers stamp retrieved_at/as_of from the Stock they
// pulled these inputs from; this module does no stamping itself (pure math).
//
// Design decision (see docs/superpowers/specs Round-7 DCF design spec §0):
// `Stock` has neither `market_cap` nor `shares_outstanding`. Base FCF/share
// is instead derived algebraically from scale-invariant ratios
// (`price / pfcf`, or `price / ps * fcf_margin`) — never fabricated, never
// falls back to a market-cap-ratio mode that doesn't exist to fall back to.

import type { Stock } from "@/lib/data";
import type { MacroData } from "@/lib/macro";

// ---- Constants (methodology parameters, not fabricated facts) ----
export const GROWTH_FLOOR = -0.15;
export const GROWTH_CAP = 0.35;
export const GROWTH_DEFAULT = 0.08;
export const TERMINAL_GROWTH_DEFAULT = 0.025;
export const EQUITY_RISK_PREMIUM = 0.045;
export const FLAT_DISCOUNT_FALLBACK = 0.095;
export const DCF_YEARS = 5;

export type DcfBasis = "pfcf" | "ps_margin" | "none";
export type GrowthSource = "actual" | "default";
export type DiscountSource = "macro_dgs10" | "flat_fallback";

export interface DcfBaseFcf {
  value: number | null; // FCF per share, same unit as valuation.price; null = never faked
  basis: DcfBasis;
  reason: string | null; // set iff value === null
}

// price/pfcf primary, price/ps*fcf_margin fallback, null (never-fake) last resort.
export function deriveBaseFcfPerShare(
  stock: Pick<Stock, "valuation" | "fundamentals">,
): DcfBaseFcf {
  const price = stock.valuation?.price ?? null;
  const { pfcf, ps, fcf_margin } = stock.fundamentals ?? {};

  if (price == null) {
    return { value: null, basis: "none", reason: "no price" };
  }

  if (typeof pfcf === "number" && Number.isFinite(pfcf) && pfcf > 0) {
    return { value: price / pfcf, basis: "pfcf", reason: null };
  }

  if (
    typeof ps === "number" &&
    Number.isFinite(ps) &&
    ps > 0 &&
    typeof fcf_margin === "number" &&
    Number.isFinite(fcf_margin)
  ) {
    const revenuePerShare = price / ps;
    return { value: revenuePerShare * fcf_margin, basis: "ps_margin", reason: null };
  }

  return { value: null, basis: "none", reason: "pfcf and ps both unusable" };
}

export function deriveDefaultGrowth(
  stock: Pick<Stock, "fundamentals">,
): { rate: number; raw: number | null; source: GrowthSource } {
  const raw = stock.fundamentals?.rev_growth_yoy ?? null;
  if (raw == null || !Number.isFinite(raw)) {
    return { rate: GROWTH_DEFAULT, raw: null, source: "default" };
  }
  const clamped = Math.min(GROWTH_CAP, Math.max(GROWTH_FLOOR, raw));
  return { rate: clamped, raw, source: "actual" };
}

// macro=null (getMacroData() absent) OR DGS10 unresolvable -> flat fallback.
export function deriveDefaultDiscountRate(
  macro: MacroData | null,
): { rate: number; source: DiscountSource; dgs10: number | null } {
  if (macro) {
    const dgs10Series = (macro.series ?? []).find(
      (s) => s.symbol?.toUpperCase() === "10Y" || s.series_id === "DGS10",
    );
    const dgs10 = dgs10Series?.last ?? null;
    if (typeof dgs10 === "number" && Number.isFinite(dgs10)) {
      return {
        rate: dgs10 / 100 + EQUITY_RISK_PREMIUM,
        source: "macro_dgs10",
        dgs10,
      };
    }
  }
  return { rate: FLAT_DISCOUNT_FALLBACK, source: "flat_fallback", dgs10: null };
}

export interface DcfDefaultInputs {
  baseFcf: DcfBaseFcf;
  growth: { rate: number; raw: number | null; source: GrowthSource };
  terminalGrowth: number; // TERMINAL_GROWTH_DEFAULT
  discount: { rate: number; source: DiscountSource; dgs10: number | null };
  years: number; // DCF_YEARS
  currentPrice: number | null;
}

// Composes the three derive* functions above into one default bundle —
// what DcfPanel seeds its sliders with, and what the capture card renders
// verbatim (no sliders on the card).
export function buildDefaultDcfInputs(
  stock: Pick<Stock, "valuation" | "fundamentals">,
  macro: MacroData | null,
): DcfDefaultInputs {
  return {
    baseFcf: deriveBaseFcfPerShare(stock),
    growth: deriveDefaultGrowth(stock),
    terminalGrowth: TERMINAL_GROWTH_DEFAULT,
    discount: deriveDefaultDiscountRate(macro),
    years: DCF_YEARS,
    currentPrice: stock.valuation?.price ?? null,
  };
}

export interface DcfYearRow {
  year: number; // 1..5
  growth: number; // g_t, decimal
  fcf: number; // FCF_t, absolute per-share
  discountFactor: number; // 1/(1+r)^t
  pv: number; // PV_t
}

export interface DcfRunParams {
  baseFcfPerShare: number;
  growthY1: number;
  terminalGrowth: number;
  discountRate: number;
  years?: number; // default DCF_YEARS; exposed for testing, not UI
}

export interface DcfResult {
  inputs: Required<DcfRunParams>;
  rows: DcfYearRow[];
  sumPvStage1: number;
  terminalValue: number; // undiscounted TV at year 5
  pvTerminalValue: number;
  fairValuePerShare: number | null; // null iff !valid
  valid: boolean; // false iff discountRate <= terminalGrowth
  error: string | null; // "discount rate must exceed terminal growth" when !valid
}

// The core pure DCF engine — formulas in spec §1. Guards r<=gT internally
// (defense in depth even though the UI also clamps sliders).
export function runDcf(params: DcfRunParams): DcfResult {
  const years = params.years ?? DCF_YEARS;
  const inputs: Required<DcfRunParams> = {
    baseFcfPerShare: params.baseFcfPerShare,
    growthY1: params.growthY1,
    terminalGrowth: params.terminalGrowth,
    discountRate: params.discountRate,
    years,
  };

  const { baseFcfPerShare, growthY1, terminalGrowth, discountRate } = inputs;

  const rows: DcfYearRow[] = [];
  let cumGrowthFactor = 1;
  for (let t = 1; t <= years; t++) {
    const g =
      years > 1
        ? growthY1 - (growthY1 - terminalGrowth) * ((t - 1) / (years - 1))
        : terminalGrowth;
    cumGrowthFactor *= 1 + g;
    const fcf = baseFcfPerShare * cumGrowthFactor;
    const discountFactor = 1 / Math.pow(1 + discountRate, t);
    const pv = fcf * discountFactor;
    rows.push({ year: t, growth: g, fcf, discountFactor, pv });
  }

  const sumPvStage1 = rows.reduce((acc, row) => acc + row.pv, 0);

  const valid = discountRate > terminalGrowth;
  const lastFcf = rows[rows.length - 1]?.fcf ?? baseFcfPerShare;

  if (!valid) {
    // Never surface NaN/Infinity, even internally — terminalValue/
    // pvTerminalValue are meaningless when invalid, so they're pinned to 0
    // rather than left to blow up through division by a non-positive
    // denominator.
    return {
      inputs,
      rows,
      sumPvStage1,
      terminalValue: 0,
      pvTerminalValue: 0,
      fairValuePerShare: null,
      valid: false,
      error: "discount rate must exceed terminal growth",
    };
  }

  const terminalValue = (lastFcf * (1 + terminalGrowth)) / (discountRate - terminalGrowth);
  const pvTerminalValue = terminalValue / Math.pow(1 + discountRate, years);
  const fairValuePerShare = sumPvStage1 + pvTerminalValue;

  return {
    inputs,
    rows,
    sumPvStage1,
    terminalValue,
    pvTerminalValue,
    fairValuePerShare,
    valid: true,
    error: null,
  };
}

// Adds price-comparison fields on top of runDcf() — the shape DcfPanel
// actually renders.
export interface DcfResultWithUpside extends DcfResult {
  currentPrice: number | null;
  upsidePct: number | null; // (fair - price)/price * 100, null if no price or !valid
}

export function runDcfWithUpside(
  params: DcfRunParams,
  currentPrice: number | null,
): DcfResultWithUpside {
  const result = runDcf(params);
  const hasPrice =
    typeof currentPrice === "number" && Number.isFinite(currentPrice) && currentPrice !== 0;
  const upsidePct =
    result.valid && hasPrice && result.fairValuePerShare != null
      ? ((result.fairValuePerShare - currentPrice) / currentPrice) * 100
      : null;
  return { ...result, currentPrice, upsidePct };
}

export interface SensitivityCell {
  discountDelta: number; // -0.01 | 0 | 0.01
  growthDelta: number; // -0.02 | 0 | 0.02
  discountRate: number;
  growthY1: number;
  fairValuePerShare: number | null;
  valid: boolean;
}

const DEFAULT_DISCOUNT_DELTAS = [-0.01, 0, 0.01];
const DEFAULT_GROWTH_DELTAS = [-0.02, 0, 0.02];

// 3x3 grid: discount +-1pt (rows) x growth +-2pt (columns), base case center.
// Pure — recomputes runDcf() 9x, cheap enough for every slider tick.
export function sensitivityGrid(
  params: DcfRunParams,
  discountDeltas: number[] = DEFAULT_DISCOUNT_DELTAS,
  growthDeltas: number[] = DEFAULT_GROWTH_DELTAS,
): SensitivityCell[][] {
  return discountDeltas.map((discountDelta) =>
    growthDeltas.map((growthDelta) => {
      const discountRate = params.discountRate + discountDelta;
      const growthY1 = params.growthY1 + growthDelta;
      const r = runDcf({ ...params, discountRate, growthY1 });
      return {
        discountDelta,
        growthDelta,
        discountRate,
        growthY1,
        fairValuePerShare: r.fairValuePerShare,
        valid: r.valid,
      };
    }),
  );
}
