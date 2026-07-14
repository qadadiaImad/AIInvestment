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
