// Server-side loader for the TA desk dataset (public/data/ta_desk.json).
//
// Pattern mirrors getNewsData() in lib/data.ts: existsSync-guarded, try/catch
// around JSON.parse, module-singleton cache, NEVER throws. The concurrent
// agent that pulls TA data (scripts/pull_ta.py) is not part of this repo's
// web build — the file may legitimately be absent (fresh clone, CI, Vercel
// build before the owner has run the puller on their machine). Every caller
// must degrade gracefully rather than 500.
//
// Types below mirror the ta_desk.json contract verbatim — do not add
// per-leaf envelope objects (value/raw/unit/dirty/source/...), do not rename
// `pp` -> `p`, do not rename session keys away from tokyo/london/new_york.

import fs from "node:fs";
import path from "node:path";

export type TaGroup = "FX" | "METALS" | "ENERGY" | "INDEX";
export type TaAssetClass = "fx" | "commodity" | "index";
export type TrendState = "bullish" | "bearish" | "mixed" | "unknown";
export type RsiState = "overbought" | "neutral" | "oversold";

export interface TaPrice {
  last: number | null;
  previous_close: number | null;
  day_change_pct: number | null;
  day_change_abs: number | null;
}

export interface TaTrend {
  state: TrendState;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
  price_above_sma20: boolean | null;
  price_above_sma50: boolean | null;
  price_above_sma200: boolean | null;
  sma50_above_sma200: boolean | null;
}

export interface TaRsi {
  value: number | null;
  state: RsiState | null;
}

export interface TaAtr {
  value: number | null;
  upper_1x: number | null;
  lower_1x: number | null;
  upper_2x: number | null;
  lower_2x: number | null;
}

export interface TaDailyPivots {
  basis_date: string | null;
  pp: number | null;
  r1: number | null;
  r2: number | null;
  r3: number | null;
  s1: number | null;
  s2: number | null;
  s3: number | null;
}

export interface TaPrevDayOhlc {
  date: string | null;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  change_pct: number | null;
}

export interface TaFiftyTwoWeek {
  high: number | null;
  low: number | null;
  position_pct: number | null;
}

export interface TaLevels {
  daily_pivots: TaDailyPivots;
  previous_day_ohlc: TaPrevDayOhlc;
  fifty_two_week: TaFiftyTwoWeek;
}

export interface TaNearestLevel {
  label: string;
  value: number;
  distance_pct: number | null;
}

export interface TaSessionWindow {
  window_utc: string;
  high: number | null;
  low: number | null;
  bar_count: number;
  complete: boolean;
}

export interface TaSessions {
  date: string;
  tokyo: TaSessionWindow;
  london: TaSessionWindow;
  new_york: TaSessionWindow;
}

export interface TaSparklinePoint {
  t: string;
  c: number;
}

export interface TaInstrument {
  symbol: string;
  display_name: string;
  asset_class: TaAssetClass;
  group: TaGroup;
  yahoo_symbol: string;
  tv_symbol: string;
  retrieved_at: string;
  source_url_daily: string;
  source_url_intraday: string;
  price: TaPrice;
  trend: TaTrend;
  rsi14: TaRsi;
  atr14: TaAtr;
  levels: TaLevels;
  nearest_level: TaNearestLevel | null;
  sessions: TaSessions;
  sparkline: TaSparklinePoint[];
  warnings: string[];
}

export interface TaDeskData {
  generated_at: string;
  schema_version: string;
  source: string;
  source_class: string;
  disclaimer: string;
  groups: TaGroup[];
  instruments: TaInstrument[];
}

let cachedTa: TaDeskData | null = null;
let taLoaded = false;

// Reads public/data/ta_desk.json. Returns null when the file is absent,
// unparseable, or malformed — never throws. Cached after first read (module
// singleton, matches getSiteData()/getNewsData() pattern).
export function getTaDeskData(): TaDeskData | null {
  if (taLoaded) return cachedTa;
  taLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "ta_desk.json");
  if (!fs.existsSync(file)) {
    cachedTa = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    const parsed = JSON.parse(raw) as TaDeskData;
    if (!parsed || !Array.isArray(parsed.instruments)) {
      cachedTa = null;
      return null;
    }
    cachedTa = parsed;
  } catch {
    cachedTa = null;
  }
  return cachedTa;
}

// Case-insensitive lookup by symbol. O(n) is fine at n=11.
export function getTaInstrument(symbol: string): TaInstrument | null {
  const data = getTaDeskData();
  if (!data) return null;
  const needle = symbol.toUpperCase();
  return (
    data.instruments.find((i) => i.symbol.toUpperCase() === needle) ?? null
  );
}

const TA_GROUPS: TaGroup[] = ["FX", "METALS", "ENERGY", "INDEX"];

// Buckets instruments by group. All 4 keys are always present (possibly
// empty arrays) so callers never need an existence check.
export function getTaGroups(): Record<TaGroup, TaInstrument[]> {
  const buckets: Record<TaGroup, TaInstrument[]> = {
    FX: [],
    METALS: [],
    ENERGY: [],
    INDEX: [],
  };
  const data = getTaDeskData();
  if (!data) return buckets;
  for (const inst of data.instruments) {
    if (TA_GROUPS.includes(inst.group)) {
      buckets[inst.group].push(inst);
    }
  }
  return buckets;
}
