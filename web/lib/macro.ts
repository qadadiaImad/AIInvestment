// Server-side loader for the Macro Desk dataset (public/data/macro.json).
//
// Pattern mirrors getRiskData() in lib/risk.ts (itself mirroring
// getTaDeskData() in lib/ta.ts / getNewsData() in lib/data.ts):
// existsSync-guarded, try/catch around JSON.parse, module-singleton cache,
// NEVER throws. macro.json is produced by scripts/pull_macro.py on the
// owner's machine (FRED is egress-blocked in this sandbox) and is NOT part
// of this repo's web build — the file may legitimately be absent (fresh
// clone, CI, Vercel build before the owner has run the puller). Every
// caller must degrade gracefully rather than 500.
//
// Types below mirror the macro.json contract verbatim (schema_version
// "macro-desk-v1") — do not rename fields, do not add per-leaf envelope
// objects. See
// docs/superpowers/specs/2026-07-14-macro-desk-design.md §2/§5/§10.4 for
// the binding field list.

import fs from "node:fs";
import path from "node:path";

export type MacroGroup = "RATES" | "INFLATION" | "LIQUIDITY_VOL" | "ENERGY";
export type MacroUnitKind = "pct" | "usd_millions" | "usd_small" | "index";
export type MacroTransform = "level" | "yoy_pct";
export type MacroRegimeKey = "curve" | "real_rate" | "liquidity" | "vix";

export interface MacroSparkPoint {
  t: string;
  v: number;
}

export interface MacroSeries {
  series_id: string;
  symbol: string;
  display_name: string;
  group: MacroGroup;
  frequency: "daily" | "weekly" | "monthly";
  unit: string;
  unit_kind: MacroUnitKind;
  decimals: number;
  transform: MacroTransform;
  last: number | null;
  previous: number | null;
  change_abs: number | null;
  change_pct: number | null;
  value_1y_ago: number | null;
  change_1y_pct: number | null;
  as_of: string | null;
  history_window_days: number;
  sparkline: MacroSparkPoint[];
  retrieved_at: string;
  source: string;
  source_class: "api";
  source_url: string;
  warnings: string[];
}

export interface MacroRegimeChip {
  key: MacroRegimeKey;
  label: string;
  state: string | null;
  value: number | null;
  value_label: string | null;
  basis: string;
  rule: string;
  as_of: string | null;
}

export interface MacroRegime {
  headline: string;
  chips: MacroRegimeChip[]; // always length 4, fixed order curve/real_rate/liquidity/vix
}

export interface MacroData {
  generated_at: string;
  schema_version: string;
  source: string;
  source_class: string;
  disclaimer: string;
  series: MacroSeries[];
  regime: MacroRegime;
  warnings: string[];
}

let cachedMacro: MacroData | null = null;
let macroLoaded = false;

// Reads public/data/macro.json. Returns null when the file is absent,
// unparseable, or malformed — never throws. Cached after first read (module
// singleton, matches getRiskData()/getTaDeskData() pattern).
export function getMacroData(): MacroData | null {
  if (macroLoaded) return cachedMacro;
  macroLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "macro.json");
  if (!fs.existsSync(file)) {
    cachedMacro = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    const parsed = JSON.parse(raw) as MacroData;
    if (
      !parsed ||
      !Array.isArray(parsed.series) ||
      !Array.isArray(parsed.regime?.chips)
    ) {
      cachedMacro = null;
      return null;
    }
    cachedMacro = parsed;
  } catch {
    cachedMacro = null;
  }
  return cachedMacro;
}

const MACRO_GROUPS: MacroGroup[] = ["RATES", "INFLATION", "LIQUIDITY_VOL", "ENERGY"];

// Buckets series by the 4 MacroGroup keys. All 4 keys are always present
// (possibly empty arrays) so callers never need an existence check. Returns
// all-empty buckets when macro.json is absent.
export function getMacroGroups(): Record<MacroGroup, MacroSeries[]> {
  const buckets: Record<MacroGroup, MacroSeries[]> = {
    RATES: [],
    INFLATION: [],
    LIQUIDITY_VOL: [],
    ENERGY: [],
  };
  const data = getMacroData();
  if (!data) return buckets;
  for (const series of data.series) {
    if (MACRO_GROUPS.includes(series.group)) {
      buckets[series.group].push(series);
    }
  }
  return buckets;
}

// Case-insensitive lookup by symbol. O(n) is fine at n=8.
export function getMacroSeries(symbol: string): MacroSeries | null {
  const data = getMacroData();
  if (!data) return null;
  const needle = symbol.toUpperCase();
  return (
    data.series.find((s) => s.symbol.toUpperCase() === needle) ?? null
  );
}
