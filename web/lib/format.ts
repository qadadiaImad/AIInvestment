// Display helpers. Null/undefined -> em dash.

export const DASH = "—";

export const LAYER_COLORS: Record<string, string> = {
  "L0-energy": "#f59e0b",
  "L1-chips": "#10b981",
  "L2-infra": "#3b82f6",
  "L3-models": "#8b5cf6",
  "L4-application": "#ec4899",
  "private-lab": "#ef4444",
};

export const LAYER_LABELS: Record<string, string> = {
  "L0-energy": "ENERGY",
  "L1-chips": "CHIPS",
  "L2-infra": "INFRA",
  "L3-models": "MODELS",
  "L4-application": "APPS",
  "private-lab": "LAB",
};

export const LAYER_ORDER = [
  "L0-energy",
  "L1-chips",
  "L2-infra",
  "L3-models",
  "L4-application",
];

export function layerColor(layer?: string | null): string {
  if (!layer) return "#6b7280";
  return LAYER_COLORS[layer] ?? "#6b7280";
}

export function layerLabel(layer?: string | null): string {
  if (!layer) return "—";
  return LAYER_LABELS[layer] ?? layer.toUpperCase();
}

function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

// Plain number, fixed decimals
export function num(v: number | null | undefined, dp = 2): string {
  if (!isNum(v)) return DASH;
  return v.toLocaleString("en-US", {
    minimumFractionDigits: dp,
    maximumFractionDigits: dp,
  });
}

// Percent value already in percentage points (e.g. 29.4 -> "29.4%")
export function pct(v: number | null | undefined, dp = 1): string {
  if (!isNum(v)) return DASH;
  return `${v.toFixed(dp)}%`;
}

// Ratio (x suffix)
export function ratio(v: number | null | undefined, dp = 2): string {
  if (!isNum(v)) return DASH;
  return `${v.toFixed(dp)}x`;
}

// Price
export function price(v: number | null | undefined): string {
  if (!isNum(v)) return DASH;
  return `$${v.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// Large USD amounts ($13.0B, $200B, $9.9M)
export function usd(v: number | null | undefined): string {
  if (!isNum(v)) return DASH;
  const abs = Math.abs(v);
  if (abs >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(1)}K`;
  return `$${v.toFixed(0)}`;
}

// Sign-aware percentage for performance: returns {text, cls}
export function signedPct(v: number | null | undefined, dp = 1): {
  text: string;
  cls: string;
} {
  if (!isNum(v)) return { text: DASH, cls: "text-zinc-500" };
  const text = `${v >= 0 ? "+" : ""}${v.toFixed(dp)}%`;
  const cls = v > 0 ? "text-emerald-400" : v < 0 ? "text-rose-400" : "text-zinc-300";
  return { text, cls };
}

export function dateOnly(v: string | null | undefined): string {
  if (!v) return DASH;
  // already date-like or ISO datetime
  return v.length >= 10 ? v.slice(0, 10) : v;
}

export function titleCase(s: string): string {
  return s
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ---- Resiliency health bands ----
// health > 70 green, 50-70 amber, < 50 red, null/no-data grey.
export const HEALTH_GREEN = "#10b981";
export const HEALTH_AMBER = "#f59e0b";
export const HEALTH_RED = "#ef4444";
export const HEALTH_GREY = "#6b7280";

export function healthColor(v: number | null | undefined): string {
  if (!isNum(v)) return HEALTH_GREY;
  if (v > 70) return HEALTH_GREEN;
  if (v >= 50) return HEALTH_AMBER;
  return HEALTH_RED;
}

export function healthBand(v: number | null | undefined): string {
  if (!isNum(v)) return "no data";
  if (v > 70) return "resilient";
  if (v >= 50) return "fragile";
  return "critical";
}

export function healthTextClass(v: number | null | undefined): string {
  if (!isNum(v)) return "text-zinc-500";
  if (v > 70) return "text-emerald-400";
  if (v >= 50) return "text-amber-400";
  return "text-rose-400";
}

// ---- TA desk (terminal) ----

export const TA_GROUP_ORDER = ["FX", "METALS", "ENERGY", "INDEX"] as const;

export const TA_GROUP_LABELS: Record<string, string> = {
  FX: "FX",
  METALS: "METALS",
  ENERGY: "ENERGY",
  INDEX: "INDEX",
};

export const TA_GROUP_COLORS: Record<string, string> = {
  FX: "#3b82f6",
  METALS: "#f59e0b",
  ENERGY: "#10b981",
  INDEX: "#a78bfa",
};

// trend.state values are lowercase bullish/bearish/mixed/unknown (matches
// the Python ta.py enum). trendColor() is a display color only.
export function trendColor(t?: string | null): string {
  if (t === "bullish") return "#34d399";
  if (t === "bearish") return "#fb7185";
  if (t === "mixed") return "#f59e0b";
  return "#6b7280"; // unknown/null
}

// The ONLY place that maps trend.state -> a human-facing label. Never
// hardcode "Uptrend"/"Downtrend"/"Mixed" elsewhere.
export function trendLabel(t?: string | null): string {
  return t === "bullish"
    ? "Uptrend"
    : t === "bearish"
      ? "Downtrend"
      : t === "mixed"
        ? "Mixed"
        : "—";
}

export function rsiColor(state?: string | null): string {
  if (state === "overbought") return "#fb7185";
  if (state === "oversold") return "#34d399";
  return "#9ca3af";
}

// ---- Risk desk (terminal/risk) ----
//
// Color-interpolation technique reused from lib/stress.ts's
// hexToRgb/rgbToHex/lerp/mix 3-stop ramp (that file stays scoped to the
// macro-stress feature — this is a fresh, local implementation, not an
// import). Rules (binding, see risk-desk design doc §"color rules"):
//   - Magnitude-only metrics (vol, VaR95/VaR99) are ALWAYS >= 0 -> sequential
//     grey -> amber -> red ONLY. Never diverging, never emerald/rose (that
//     pair is reserved for signed price-direction readouts everywhere else
//     on the site).
//   - Signed metrics (day_change_pct) -> diverging, reusing the EXISTING
//     emerald/rose brand pair from signedPct()/trendColor(), zinc-700 at
//     true zero.
//   - Correlation (-1..+1) -> diverging blue-white-red, a DIFFERENT hue pair
//     from the day% ramp so "price direction" and "co-movement" are never
//     visually conflated.
//   - Every tile/cell carries its numeric value as visible text; contrastText()
//     picks a safe text color for any of the above backgrounds.

function clamp01(v: number): number {
  return Math.min(1, Math.max(0, v));
}

function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
}

function rgbToHex(r: number, g: number, b: number): string {
  const c = (n: number) => Math.round(Math.min(255, Math.max(0, n))).toString(16).padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
}

function lerpN(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function mixHex(c1: string, c2: string, t: number): string {
  const [r1, g1, b1] = hexToRgb(c1);
  const [r2, g2, b2] = hexToRgb(c2);
  return rgbToHex(lerpN(r1, r2, t), lerpN(g1, g2, t), lerpN(b1, b2, t));
}

const RISK_GREY = "#3f3f46"; // zinc-700 — calm
const RISK_AMBER = "#f59e0b"; // caution
const RISK_RED = "#ef4444"; // danger

// Sequential grey -> amber -> red for magnitude-only metrics (vol,
// var95_1d_pct, var99_1d_pct). `domainMax` is the value that maps to full
// red (e.g. a sensible per-metric ceiling); values are clamped into [0,1]
// first. Null -> grey (no-data, same convention as healthColor()).
export function riskMagnitudeColor(
  v: number | null | undefined,
  domainMax: number,
): string {
  if (!isNum(v) || !isNum(domainMax) || domainMax <= 0) return RISK_GREY;
  const t = clamp01(v / domainMax);
  if (t <= 0.5) return mixHex(RISK_GREY, RISK_AMBER, t / 0.5);
  return mixHex(RISK_AMBER, RISK_RED, (t - 0.5) / 0.5);
}

// Text-color companion to riskMagnitudeColor — same 3 bands, Tailwind
// classes (no interpolation needed for text, coarser bands read fine).
export function riskMagnitudeTextClass(
  v: number | null | undefined,
  domainMax: number,
): string {
  if (!isNum(v) || !isNum(domainMax) || domainMax <= 0) return "text-zinc-500";
  const t = clamp01(v / domainMax);
  if (t < 0.35) return "text-zinc-300";
  if (t < 0.7) return "text-amber-400";
  return "text-rose-400";
}

const RISK_DIVERGING_DOWN = "#fb7185"; // rose-400, matches signedPct()/trendColor()
const RISK_DIVERGING_ZERO = "#3f3f46"; // zinc-700
const RISK_DIVERGING_UP = "#34d399"; // emerald-400, matches trendColor()

// Diverging rose -> zinc-700 -> emerald for signed metrics (day_change_pct
// only). `domainAbsMax` is the |value| that maps to full saturation on
// either side. Reuses the site's existing positive/negative price-move hue
// pair — never invents new colors for a signed readout.
export function riskDivergingColor(
  v: number | null | undefined,
  domainAbsMax: number,
): string {
  if (!isNum(v) || !isNum(domainAbsMax) || domainAbsMax <= 0) return "#27272a";
  const t = clamp01(Math.abs(v) / domainAbsMax);
  if (v >= 0) return mixHex(RISK_DIVERGING_ZERO, RISK_DIVERGING_UP, t);
  return mixHex(RISK_DIVERGING_ZERO, RISK_DIVERGING_DOWN, t);
}

const CORR_NEG = "#3b82f6"; // blue-500
const CORR_ZERO = "#f4f4f5"; // zinc-100 (white-ish)
const CORR_POS = "#dc2626"; // red-600

// Diverging blue-white-red for correlation matrix cells only, fixed domain
// [-1, 1]. Deliberately a DIFFERENT hue pair from riskDivergingColor() so
// "price direction" (emerald/rose) and "co-movement" (blue/red) are never
// visually conflated. Null (missing pair / dropped from `order`) -> neutral
// grey.
export function correlationColor(v: number | null | undefined): string {
  if (!isNum(v)) return "#27272a";
  const c = Math.min(1, Math.max(-1, v));
  if (c >= 0) return mixHex(CORR_ZERO, CORR_POS, c);
  return mixHex(CORR_ZERO, CORR_NEG, -c);
}

// ---- Macro desk (terminal/macro) ----

import type { MacroGroup, MacroRegimeKey, MacroUnitKind } from "@/lib/macro";

export const MACRO_GROUP_ORDER: MacroGroup[] = [
  "RATES",
  "INFLATION",
  "LIQUIDITY_VOL",
  "ENERGY",
];

export const MACRO_GROUP_LABELS: Record<string, string> = {
  RATES: "RATES",
  INFLATION: "INFLATION",
  LIQUIDITY_VOL: "LIQUIDITY & VOL",
  ENERGY: "ENERGY",
};

// ENERGY reuses LAYER_COLORS["L0-energy"] deliberately — ties the macro
// ENERGY group visually to the L0 chip color used everywhere else in the
// terminal (energy is Layer 0 of the AI stack).
export const MACRO_GROUP_COLORS: Record<string, string> = {
  RATES: "#3b82f6",
  INFLATION: "#a78bfa",
  LIQUIDITY_VOL: "#06b6d4",
  ENERGY: LAYER_COLORS["L0-energy"],
};

// Categorical traffic-light chip color — NOT interpolated (unlike
// riskMagnitudeColor/riskDivergingColor above). Table is FINAL per macro
// desk design doc §6/§10.6:
//   green  = curve:normal | real_rate:accommodative | liquidity:expanding | vix:complacent|normal
//   amber  = curve:flat   | real_rate:neutral        | liquidity:flat      | vix:elevated
//   red    = curve:inverted | real_rate:restrictive  | liquidity:contracting | vix:stressed
//   grey   = state == null (no-data, same convention as healthColor())
export function regimeColor(key: MacroRegimeKey, state: string | null): string {
  const GREEN = "#34d399";
  const AMBER = "#f59e0b";
  const RED = "#fb7185";
  const GREY = "#6b7280";
  if (state == null) return GREY;
  if (key === "curve") {
    return state === "normal" ? GREEN : state === "flat" ? AMBER : RED;
  }
  if (key === "real_rate") {
    return state === "accommodative" ? GREEN : state === "neutral" ? AMBER : RED;
  }
  if (key === "liquidity") {
    return state === "expanding" ? GREEN : state === "flat" ? AMBER : RED;
  }
  // vix
  return state === "complacent" || state === "normal"
    ? GREEN
    : state === "elevated"
      ? AMBER
      : RED;
}

// The ONLY place that maps a regime chip's raw state string -> a
// human-facing label. Never hardcode title-cased state strings elsewhere.
export function regimeLabel(state: string | null): string {
  return state == null ? DASH : titleCase(state);
}

// unit_kind -> display string. The ONE place that maps unit_kind -> a
// formatted text value for a MacroSeries. usd_millions divides by 1000 and
// renders "$B" for DISPLAY ONLY — the stamped number in macro.json stays
// raw FRED-native millions, never rescaled at pull time.
export function macroValue(
  v: number | null,
  unitKind: MacroUnitKind,
  decimals: number,
): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  if (unitKind === "pct") return `${v.toFixed(decimals)}%`;
  if (unitKind === "usd_millions") {
    return `$${(v / 1000).toLocaleString("en-US", { maximumFractionDigits: 0 })}B`;
  }
  if (unitKind === "usd_small") return `$${v.toFixed(decimals)}`;
  return v.toFixed(decimals); // index
}

// Display unit caption matching macroValue()'s rescaling: usd_millions values
// are rendered in $B, so their caption must say "$B", not the raw FRED "$M".
export function macroUnitLabel(unit: string, unitKind: MacroUnitKind): string {
  return unitKind === "usd_millions" ? "$B" : unit;
}

// Thin wrapper reusing riskDivergingColor — no reimplementation. Used for
// macro series change badges (change_pct) at panel granularity.
export function macroChangeColor(
  v: number | null,
  domainAbsMax: number,
): string {
  return riskDivergingColor(v, domainAbsMax);
}

// WCAG-ish relative-luminance check for text-on-variable-background safety.
// Used by heatmap tiles and correlation matrix cells — every tile/cell must
// carry its numeric value as visible text, never hue-alone encoding.
export function contrastText(bgHex: string): "#0b0f17" | "#e5e7eb" {
  const [r, g, b] = hexToRgb(bgHex);
  // sRGB -> relative luminance (simplified, gamma-approximated — sufficient
  // for a binary light/dark text pick, not a certified WCAG contrast ratio).
  const srgb = [r, g, b].map((c) => c / 255);
  const lin = srgb.map((c) =>
    c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4),
  );
  const luminance = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
  return luminance > 0.5 ? "#0b0f17" : "#e5e7eb";
}
