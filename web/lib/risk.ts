// Server-side loader for the Risk Analytics desk dataset
// (public/data/risk.json).
//
// Pattern mirrors getTaDeskData() in lib/ta.ts (itself mirroring
// getNewsData() in lib/data.ts): existsSync-guarded, try/catch around
// JSON.parse, module-singleton cache, NEVER throws. risk.json is produced by
// scripts/build_risk.py on the owner's machine and is NOT part of this
// repo's web build — the file may legitimately be absent (fresh clone, CI,
// Vercel build before the owner has run the puller). Every caller must
// degrade gracefully rather than 500.
//
// Types below mirror the risk.json contract verbatim (schema_version
// "risk-desk-v1") — do not rename fields, do not add per-leaf envelope
// objects. See docs/superpowers/specs/2026-07-14-risk-desk-design.md §4 for
// the binding field list.

import fs from "node:fs";
import path from "node:path";

export interface RiskParams {
  risk_free_rate_annual: number;
  risk_free_source: string; // "graph_analysis.json:macro.snapshot.dff" | "cli-default"
  window_trading_days: number;
  min_bars: number;
  periods_per_year: number;
  var_confidence_levels: number[];
  correlation_top_n: number;
  min_overlap_days: number;
}

export interface RiskPricesSource {
  provider: string;
  source_class: string;
  batch_retrieved_at: string | null;
}

export interface RiskUniverse {
  n_symbols_total: number;
  n_symbols_with_metrics: number;
  layers: string[];
}

export interface RiskStock {
  symbol: string;
  layer: string;
  prices_retrieved_at: string | null;
  last_price_date: string | null;
  n_bars_total: number | null;
  n_returns_window: number | null;
  day_change_pct: number | null;
  vol_annualized_pct: number | null;
  var95_1d_pct: number | null;
  var99_1d_pct: number | null;
  sharpe_1y: number | null;
  max_drawdown_1y_pct: number | null;
  beta_vs_spy: number | null;
  market_cap: number | null;
  warnings: string[];
}

export interface RiskLayer {
  layer: string;
  n_constituents: number;
  n_with_metrics: number;
  day_change_pct: number | null;
  day_change_basis: string | null; // "market_cap" | "equal_weighted_fallback" | null
  vol_equal_weighted_pct: number | null;
  vol_cap_weighted_pct: number | null;
  vol_cap_weighted_basis: string | null; // "market_cap" | "equal_weighted_fallback" | null
  median_var95_1d_pct: number | null;
  median_var99_1d_pct: number | null;
  worst_var95_1d_pct: number | null;
  worst_var95_symbol: string | null;
  best_sharpe_symbol: string | null;
  best_sharpe_1y: number | null;
  worst_sharpe_symbol: string | null;
  worst_sharpe_1y: number | null;
  worst_drawdown_symbol: string | null;
  worst_drawdown_1y_pct: number | null;
  warnings: string[];
}

// Shared shape for both correlation blocks.
export interface RiskCorrelationBlock {
  order: string[];
  matrix: (number | null)[][];
  window_trading_days: number;
  min_overlap_days: number;
  warnings: string[];
}

export interface RiskLayerCorrelationBlock extends RiskCorrelationBlock {
  l3_models_note: string;
}

export interface RiskTopStocksCandidateSkipped {
  symbol: string;
  reason: string;
}

export interface RiskTopStocksBlock extends RiskCorrelationBlock {
  ranked_by: string; // "market_cap" | "n_returns_window_fallback"
  candidates_considered: number;
  candidates_skipped: RiskTopStocksCandidateSkipped[];
}

export interface RiskCorrelations {
  layers: RiskLayerCorrelationBlock;
  top_stocks: RiskTopStocksBlock;
}

export interface RiskHeadlineWorstLayer {
  layer: string;
  day_change_pct: number | null;
}

export interface RiskHeadlineTopCorrelationPair {
  a: string;
  b: string;
  value: number;
}

export interface RiskHeadline {
  worst_layer: RiskHeadlineWorstLayer | null;
  universe_var95_1d_pct: number | null;
  top_correlation_pair: RiskHeadlineTopCorrelationPair | null;
}

export interface RiskData {
  generated_at: string;
  schema_version: string;
  source_class: string;
  disclaimer: string;
  params: RiskParams;
  prices_source: RiskPricesSource;
  benchmark_symbol: string;
  universe: RiskUniverse;
  warnings: string[];
  per_stock: RiskStock[];
  per_layer: RiskLayer[];
  correlations: RiskCorrelations;
  headline: RiskHeadline;
}

let cachedRisk: RiskData | null = null;
let riskLoaded = false;

// Reads public/data/risk.json. Returns null when the file is absent,
// unparseable, or malformed — never throws. Cached after first read (module
// singleton, matches getTaDeskData()/getSiteData() pattern).
export function getRiskData(): RiskData | null {
  if (riskLoaded) return cachedRisk;
  riskLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "risk.json");
  if (!fs.existsSync(file)) {
    cachedRisk = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    const parsed = JSON.parse(raw) as RiskData;
    if (
      !parsed ||
      !Array.isArray(parsed.per_stock) ||
      !Array.isArray(parsed.per_layer)
    ) {
      cachedRisk = null;
      return null;
    }
    cachedRisk = parsed;
  } catch {
    cachedRisk = null;
  }
  return cachedRisk;
}

// Buckets per_stock by layer in universe.layers order. All layer keys are
// always present (possibly empty arrays) so callers never need an existence
// check. Returns {} when risk.json is absent.
export function getRiskStocksByLayer(): Record<string, RiskStock[]> {
  const data = getRiskData();
  if (!data) return {};
  const buckets: Record<string, RiskStock[]> = {};
  for (const layer of data.universe.layers) buckets[layer] = [];
  for (const stock of data.per_stock) {
    if (!buckets[stock.layer]) buckets[stock.layer] = [];
    buckets[stock.layer].push(stock);
  }
  return buckets;
}

// Case-insensitive lookup by symbol. Mirrors getTaInstrument(). O(n) is fine
// at universe size (~90).
export function getRiskStock(symbol: string): RiskStock | null {
  const data = getRiskData();
  if (!data) return null;
  const needle = symbol.toUpperCase();
  return (
    data.per_stock.find((s) => s.symbol.toUpperCase() === needle) ?? null
  );
}
