// Server-side loader for the owner's portfolio bundle
// (web/data/portfolio.json — NOT public/data/).
//
// PRIVACY (read before touching this file): web/public/** is served as a
// static asset by literal URL — the /terminal proxy matcher
// (web/proxy.ts, matcher: ["/terminal/:path*"]) never sees requests for
// files under public/, so anything placed there bypasses the terminal_key
// gate entirely. This module MUST read from
// path.join(process.cwd(), "data", "portfolio.json") — i.e. web/data/,
// a directory that is NOT public and NOT served by URL — never
// "public"/"data". This is the single most important line in this file;
// do not "fix" it to match lib/risk.ts's public/data/risk.json path, that
// would be a privacy regression.
//
// Pattern otherwise mirrors getRiskData() in lib/risk.ts / getArchetypeData()
// in lib/archetypes.ts: existsSync-guarded, try/catch around JSON.parse,
// module-singleton cache, NEVER throws. web/data/portfolio.json is produced
// by scripts/build_portfolio.py on the owner's machine (reading the
// gitignored data/portfolio/positions.json) and is NOT part of this repo's
// web build — the file may legitimately be absent (fresh clone, CI, Vercel
// build before the owner has run the pipeline). Every caller must degrade
// gracefully rather than 500.
//
// Types below mirror the web/data/portfolio.json contract verbatim
// (schema_version "portfolio-v1") — do not rename fields, do not add
// per-leaf envelope objects. See
// docs/superpowers/specs/2026-07-15-portfolio-design.md §5 for the binding
// field list.
//
// getPortfolioData() returns null ONLY when web/data/portfolio.json itself
// is absent/unparseable/structurally malformed (the build script has never
// been run). When the file exists but encodes the "no positions yet"
// empty-state bundle (positions_source.found === false), it is returned
// as-is — aggregates/risk are null in that bundle, and the page sources its
// empty-state copy from warnings[0] (defined once, in Python, not
// duplicated here).

import fs from "node:fs";
import path from "node:path";

export interface PortfolioPositionsSource {
  path: string;
  mtime: string | null;
  n_raw_rows: number;
  n_positions_after_merge: number;
  found: boolean;
}

export interface PortfolioPricesSource {
  provider: string;
  source_class: string;
  batch_retrieved_at: string | null;
}

export interface PortfolioSiteSource {
  generated_at: string | null;
}

export interface PortfolioParams {
  base_currency: string;
  window_trading_days: number;
  min_bars: number;
  rf_annual: number;
  rf_source: string;
  top_n_correlation: number;
  var_confidence: number;
}

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  lots_merged: number;
  cost_basis_per_share: number | null;
  cost_basis_total_usd: number | null;
  acquired_date: string | null;
  note: string | null;
  layer: string | null;
  last_price: number | null;
  price_as_of: string | null;
  price_source: string | null;
  market_value_usd: number | null;
  weight_pct: number | null;
  unrealized_pnl_usd: number | null;
  unrealized_pnl_pct: number | null;
  day_change_pct: number | null;
  day_change_usd: number | null;
  warnings: string[];
}

export interface PortfolioLayerExposure {
  layer: string;
  weight_pct: number;
  market_value_usd: number;
  n_positions: number;
}

export interface PortfolioConcentration {
  top1_weight_pct: number | null;
  top3_weight_pct: number | null;
  hhi: number | null;
  basis: string;
}

export interface PortfolioAggregates {
  total_value_usd: number;
  invested_value_usd: number;
  cash_usd: number;
  cash_weight_pct: number | null;
  total_cost_basis_usd: number | null;
  total_unrealized_pnl_usd: number | null;
  total_unrealized_pnl_pct: number | null;
  day_pnl_usd: number | null;
  day_pnl_pct: number | null;
  n_positions: number;
  n_positions_priced: number;
  n_positions_unpriced: number;
  layer_exposure: PortfolioLayerExposure[];
  concentration: PortfolioConcentration;
}

export interface PortfolioMaxPairwiseCorrelation {
  a: string;
  b: string;
  value: number;
}

export interface PortfolioSeriesExcluded {
  symbol: string;
  reason: string;
}

export interface PortfolioSeriesCoverage {
  n_holdings_included: number;
  n_holdings_total_priced: number;
  weight_coverage_pct: number;
  excluded: PortfolioSeriesExcluded[];
}

export interface PortfolioRisk {
  vol_annualized_pct: number | null;
  var95_1d_pct: number | null;
  sharpe_1y: number | null;
  beta_vs_spy: number | null;
  max_pairwise_correlation: PortfolioMaxPairwiseCorrelation | null;
  series_coverage: PortfolioSeriesCoverage;
  methodology_note: string;
  warnings: string[];
}

export interface PortfolioData {
  generated_at: string;
  schema_version: string;
  source_class: string;
  disclaimer: string;
  positions_source: PortfolioPositionsSource;
  prices_source: PortfolioPricesSource;
  site_source: PortfolioSiteSource;
  params: PortfolioParams;
  positions: PortfolioPosition[];
  aggregates: PortfolioAggregates | null;
  risk: PortfolioRisk | null;
  warnings: string[];
}

let cachedPortfolio: PortfolioData | null = null;
let portfolioLoaded = false;

// Reads web/data/portfolio.json (server-only, NOT public/). Returns null
// when the file is absent, unparseable, or structurally malformed — never
// throws. Cached after first read (module singleton, matches
// getRiskData()/getArchetypeData() pattern).
export function getPortfolioData(): PortfolioData | null {
  if (portfolioLoaded) return cachedPortfolio;
  portfolioLoaded = true;
  // NOT path.join(process.cwd(), "public", "data", ...) — see file-header
  // privacy note. web/data/ is not served by URL.
  const file = path.join(process.cwd(), "data", "portfolio.json");
  if (!fs.existsSync(file)) {
    cachedPortfolio = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    const parsed = JSON.parse(raw) as PortfolioData;
    if (
      !parsed ||
      !Array.isArray(parsed.positions) ||
      !Array.isArray(parsed.warnings) ||
      typeof parsed.positions_source !== "object" ||
      parsed.positions_source === null
    ) {
      cachedPortfolio = null;
      return null;
    }
    cachedPortfolio = parsed;
  } catch {
    cachedPortfolio = null;
  }
  return cachedPortfolio;
}

// Convenience predicate for pages: true when there is nothing shareable /
// nothing to render beyond the empty state — either the bundle was never
// generated (null) or it was generated but encodes the "no positions file
// yet" degrade (positions_source.found === false).
export function isPortfolioEmpty(data: PortfolioData | null): boolean {
  return data === null || data.positions_source.found === false;
}

// ---- Capture-card privacy transform ----
//
// PortfolioCardData is a STRUCTURALLY NARROWER type than PortfolioData: it
// omits every *_usd field on purpose, so that an accidental future
// `<PortfolioCaptureCard data={fullPortfolioData} />` wire-up fails to
// typecheck instead of silently leaking a dollar figure onto a screenshot.
// toCardData() below does an EXPLICIT field-by-field pick — never a spread
// (a spread would let dollar fields pass through structurally, defeating
// the whole point of the narrower prop type).

export interface PortfolioCardLayerExposure {
  layer: string;
  weight_pct: number;
}

export interface PortfolioCardConcentration {
  top1_weight_pct: number | null;
  top3_weight_pct: number | null;
  hhi: number | null;
}

export interface PortfolioCardRisk {
  vol_annualized_pct: number | null;
  var95_1d_pct: number | null;
  sharpe_1y: number | null;
  beta_vs_spy: number | null;
}

export interface PortfolioCardData {
  generated_at: string;
  layer_exposure: PortfolioCardLayerExposure[];
  total_unrealized_pnl_pct: number | null;
  day_pnl_pct: number | null;
  concentration: PortfolioCardConcentration;
  risk: PortfolioCardRisk | null;
  n_positions: number;
}

export function toCardData(data: PortfolioData): PortfolioCardData {
  const agg = data.aggregates;
  const risk = data.risk;
  return {
    generated_at: data.generated_at,
    layer_exposure: (agg?.layer_exposure ?? []).map((l) => ({
      layer: l.layer,
      weight_pct: l.weight_pct,
    })),
    total_unrealized_pnl_pct: agg ? agg.total_unrealized_pnl_pct : null,
    day_pnl_pct: agg ? agg.day_pnl_pct : null,
    concentration: {
      top1_weight_pct: agg ? agg.concentration.top1_weight_pct : null,
      top3_weight_pct: agg ? agg.concentration.top3_weight_pct : null,
      hhi: agg ? agg.concentration.hhi : null,
    },
    risk: risk
      ? {
          vol_annualized_pct: risk.vol_annualized_pct,
          var95_1d_pct: risk.var95_1d_pct,
          sharpe_1y: risk.sharpe_1y,
          beta_vs_spy: risk.beta_vs_spy,
        }
      : null,
    n_positions: agg ? agg.n_positions : 0,
  };
}

// Positions ordered for display: priced positions by weight_pct desc first,
// unpriced (weight_pct === null) last, preserving source order within each
// group. Pure/no I/O — safe to unit test directly.
export function sortPositionsForDisplay(
  positions: PortfolioPosition[],
): PortfolioPosition[] {
  const priced = positions.filter((p) => p.weight_pct != null);
  const unpriced = positions.filter((p) => p.weight_pct == null);
  priced.sort((a, b) => (b.weight_pct ?? 0) - (a.weight_pct ?? 0));
  return [...priced, ...unpriced];
}
