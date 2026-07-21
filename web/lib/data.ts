import fs from "node:fs";
import path from "node:path";

// ---- Types matching public/data/site.json ----

export interface SourceRef {
  name: string;
  url: string;
}

export type LayerKey =
  | "L0-energy"
  | "L1-chips"
  | "L2-infra"
  | "L3-models"
  | "L4-application";

export type FundamentalValuationTag =
  | "Undervalued"
  | "Fairly Valued"
  | "Overvalued";

export interface Valuation {
  price: number | null;
  pe: number | null;
  profitability: string | null;
  fundamental_value?: number | null;
  fundamental_valuation?: FundamentalValuationTag | string | null;
  fundamental_discount_pct?: number | null;
  margin_of_safety_pct?: number | null;
}

export interface Returns {
  "1y"?: number | null;
  "3y"?: number | null;
  "5y"?: number | null;
}

export interface FundamentalValuePoint {
  date: string;
  value: number | null;
}

export interface Fundamentals {
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  fcf_margin: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  ps: number | null;
  pb: number | null;
  pfcf: number | null;
  rev_growth_yoy: number | null;
  eps_growth_yoy: number | null;
  sector: string | null;
  industry: string | null;
}

export interface Performance {
  perf_1y: number | null;
  perf_ytd: number | null;
  beta: number | null;
}

export interface PeerMetric {
  value: number | null;
  median: number | null;
  percentile: number | null;
  n: number | null;
}

export interface PeerComparison {
  industry?: Record<string, PeerMetric>;
  layer?: Record<string, PeerMetric>;
}

export interface HistoryPoint {
  date: string;
  value: number | null;
}

export interface History {
  annualTotalRevenue?: HistoryPoint[];
  annualGrossProfit?: HistoryPoint[];
  annualNetIncome?: HistoryPoint[];
  annualFreeCashFlow?: HistoryPoint[];
  annualDilutedEPS?: HistoryPoint[];
}

export interface Constraint {
  physical_bottleneck?: string | null;
  regulatory_bottleneck?: string | null;
  lead_time_note?: string | null;
}

export interface Catalyst {
  id: string;
  date: string | null;
  display?: string | null;
  title?: string | null;
  type: string | null;
  certainty?: string | null;
  source_class?: string | null;
  source_url?: string | null;
  note?: string | null;
}

export interface Counterparty {
  node: string;
  type: string;
  usd: number | null;
}

export interface LabExposure {
  lab: string;
  pct: number | null;
  usd?: number | null;
  certainty?: string | null;
}

export interface Relationships {
  counterparties?: Counterparty[];
  single_counterparty_flags?: unknown[];
  lab_exposure?: LabExposure[];
}

export interface Narrative {
  valuation_take?: string;
  bottleneck_rationale?: string;
  scenarios?: string[];
  risks?: string[];
  synthesis?: string;
  [k: string]: unknown;
}

export interface Stock {
  symbol: string;
  // AI layers are LayerKey (L0–L4); quantum layers are Q* strings — widened so
  // the merged dataset type-checks. sectors marks AI/Quantum membership.
  layer: LayerKey | string;
  sectors?: string[];
  as_of: string | null;
  tv_symbol?: string | null;
  returns?: Returns | null;
  fundamental_value_series?: FundamentalValuePoint[] | null;
  valuation: Valuation;
  fundamentals: Fundamentals;
  performance: Performance;
  peer_comparison: PeerComparison;
  history: History;
  constraint: Constraint;
  catalysts: Catalyst[];
  relationships: Relationships;
  risk_flags: string[];
  narrative: Narrative;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  ticker?: string;
  layer?: string;
  note?: string;
  // Bridge giants present in both chains carry ["AI","Quantum"]; otherwise the
  // single owning sector. Optional so AI-only data still type-checks.
  sectors?: string[];
}

export interface EdgeTransaction {
  date?: string | null;
  amount?: number | null;
  note?: string | null;
}

export interface GraphEdge {
  src: string;
  dst: string;
  type: string;
  // attrs is heterogeneous: numbers (usd, pct, power_gw…), strings (duration,
  // until, note), and an optional transactions array.
  attrs?: Record<
    string,
    number | string | null | EdgeTransaction[] | undefined
  >;
  certainty?: string;
  source_class?: string;
  source_url?: string;
  origin?: string;
  quote?: string;
  as_of?: string;
}

export interface CapitalWeb {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ScreenerRow {
  symbol: string;
  layer: LayerKey | string;
  sector?: string;
  sectors?: string[];
  price: number | null;
  pe: number | null;
  net_margin: number | null;
  roe: number | null;
  rev_growth_yoy: number | null;
  perf_1y: number | null;
  next_catalyst: string | null;
  fundamental_value?: number | null;
  fundamental_discount_pct?: number | null;
  ret_1y?: number | null;
  ret_5y?: number | null;
}

export interface SiteData {
  generated_at: string;
  disclaimer: string;
  sources: SourceRef[];
  // AI layers (L*) plus, after merge, quantum layers (Q*). Widened to string
  // keys so both coexist in one record.
  layers: Record<string, string[]>;
  stocks: Record<string, Stock>;
  capital_web: CapitalWeb;
  screener: ScreenerRow[];
}

let cached: SiteData | null = null;

export function getSiteData(): SiteData {
  if (cached) return cached;
  const file = path.join(process.cwd(), "public", "data", "site.json");
  const raw = fs.readFileSync(file, "utf-8");
  const parsed = JSON.parse(raw) as SiteData;
  // Enrich screener rows with fundamental-value fields sourced from each
  // stock's valuation block (the screener array in site.json omits them).
  for (const row of parsed.screener) {
    const v = parsed.stocks[row.symbol]?.valuation;
    if (v) {
      row.fundamental_value = v.fundamental_value ?? null;
      row.fundamental_discount_pct = v.fundamental_discount_pct ?? null;
    }
  }

  // Tag every AI datum with sector "AI" (implicit membership made explicit so
  // the merged dataset can be sector-filtered). Stocks, screener rows, and
  // capital_web nodes all gain a sectors array including "AI".
  for (const sym of Object.keys(parsed.stocks)) {
    parsed.stocks[sym].sectors = ["AI"];
  }
  for (const row of parsed.screener) {
    row.sector = "AI";
    row.sectors = ["AI"];
  }
  for (const node of parsed.capital_web.nodes) {
    node.sectors = ["AI"];
  }

  // Merge the Quantum sector (web/public/data/quantum.json) if present. Absent
  // → AI-only, unchanged. Stocks are disjoint (simple union); capital_web nodes
  // overlap at bridge giants (dedupe by id, union sectors); edges union (dedupe
  // by src+dst+type); layers union (AI L* + quantum Q* keys coexist).
  mergeQuantum(parsed);

  // Merge the Congress sector (web/public/data/congress_stocks.json) if present.
  // Absent → unchanged. Same stock schema as quantum.json but sector "Congress"
  // and empty capital_web. Stocks are disjoint from AI/quantum by construction
  // (simple union); screener rows concat (each row sector "Congress"); no
  // capital_web merge (congress capital_web is empty); no layers added.
  mergeCongressStocks(parsed);

  // Merge curated/foreign additions (web/public/data/extra_stocks.json) if present.
  mergeExtraStocks(parsed);

  cached = parsed;
  return cached;
}

function edgeKey(e: GraphEdge): string {
  //  (ASCII unit separator): collision-proof like the previous NUL separator,
  // but not a NUL byte — NULs made git treat this file as binary, which broke
  // every merge on it (both sides of the 2026-07-21 fork conflicted here).
  return `${e.src}${e.dst}${e.type}`;
}

function mergeQuantum(parsed: SiteData): void {
  const file = path.join(process.cwd(), "public", "data", "quantum.json");
  if (!fs.existsSync(file)) return;
  let quantum: SiteData;
  try {
    const raw = fs.readFileSync(file, "utf-8");
    quantum = JSON.parse(raw) as SiteData;
  } catch {
    return;
  }

  // Stocks: disjoint union. Each quantum stock carries sector "Quantum".
  for (const sym of Object.keys(quantum.stocks ?? {})) {
    const stock = quantum.stocks[sym];
    stock.sectors = ["Quantum"];
    parsed.stocks[sym] = stock;
  }

  // Screener: concat; each quantum row carries sector "Quantum".
  for (const row of quantum.screener ?? []) {
    row.sector = "Quantum";
    row.sectors = ["Quantum"];
    // Enrich fundamental-value fields from the merged stock, mirroring AI rows.
    const v = parsed.stocks[row.symbol]?.valuation;
    if (v) {
      row.fundamental_value = v.fundamental_value ?? null;
      row.fundamental_discount_pct = v.fundamental_discount_pct ?? null;
    }
    parsed.screener.push(row);
  }

  // Capital-web nodes: union, dedupe by id. Bridge giants present in both →
  // sectors = ["AI","Quantum"]. Quantum-only nodes → ["Quantum"].
  const nodeById = new Map<string, GraphNode>();
  for (const node of parsed.capital_web.nodes) nodeById.set(node.id, node);
  for (const qnode of quantum.capital_web?.nodes ?? []) {
    const existing = nodeById.get(qnode.id);
    if (existing) {
      const merged = new Set([...(existing.sectors ?? []), "Quantum"]);
      existing.sectors = [...merged];
    } else {
      qnode.sectors = ["Quantum"];
      nodeById.set(qnode.id, qnode);
      parsed.capital_web.nodes.push(qnode);
    }
  }

  // Capital-web edges: union, dedupe by (src,dst,type).
  const seenEdges = new Set(parsed.capital_web.edges.map(edgeKey));
  for (const edge of quantum.capital_web?.edges ?? []) {
    const key = edgeKey(edge);
    if (seenEdges.has(key)) continue;
    seenEdges.add(key);
    parsed.capital_web.edges.push(edge);
  }

  // Layers: union — keep both AI L* and quantum Q* keys.
  for (const [key, syms] of Object.entries(quantum.layers ?? {})) {
    parsed.layers[key] = syms;
  }
}

function mergeCongressStocks(parsed: SiteData): void {
  const file = path.join(
    process.cwd(),
    "public",
    "data",
    "congress_stocks.json",
  );
  if (!fs.existsSync(file)) return;
  let congress: SiteData;
  try {
    const raw = fs.readFileSync(file, "utf-8");
    congress = JSON.parse(raw) as SiteData;
  } catch {
    return;
  }

  // Stocks: disjoint union. Each congress stock carries sector "Congress".
  for (const sym of Object.keys(congress.stocks ?? {})) {
    const stock = congress.stocks[sym];
    stock.sectors = ["Congress"];
    parsed.stocks[sym] = stock;
  }

  // Screener: concat; each congress row carries sector "Congress".
  for (const row of congress.screener ?? []) {
    row.sector = "Congress";
    row.sectors = ["Congress"];
    // Enrich fundamental-value fields from the merged stock, mirroring AI rows.
    const v = parsed.stocks[row.symbol]?.valuation;
    if (v) {
      row.fundamental_value = v.fundamental_value ?? null;
      row.fundamental_discount_pct = v.fundamental_discount_pct ?? null;
    }
    parsed.screener.push(row);
  }

  // No capital_web merge: congress_stocks capital_web is empty by construction.
  // No layers added: congress stocks resolve via getStock/getAllSymbols only.
}

// Curated / foreign single-stock additions (e.g. Kalray, Euronext Paris). Each entry
// carries its OWN sector; merged like the others so /stocks/[sym] + the screener pick it up.
function mergeExtraStocks(parsed: SiteData): void {
  const file = path.join(process.cwd(), "public", "data", "extra_stocks.json");
  if (!fs.existsSync(file)) return;
  let extra: SiteData;
  try {
    extra = JSON.parse(fs.readFileSync(file, "utf-8")) as SiteData;
  } catch {
    return;
  }
  for (const sym of Object.keys(extra.stocks ?? {})) {
    const stock = extra.stocks[sym];
    const sec = (stock as { sector?: string }).sector ?? "AI";
    stock.sectors = [sec];
    parsed.stocks[sym] = stock;
  }
  for (const row of extra.screener ?? []) {
    const sec = (row as { sector?: string }).sector ?? "AI";
    row.sector = sec;
    row.sectors = [sec];
    const v = parsed.stocks[row.symbol]?.valuation;
    if (v) {
      row.fundamental_value = v.fundamental_value ?? null;
      row.fundamental_discount_pct = v.fundamental_discount_pct ?? null;
    }
    parsed.screener.push(row);
  }
}

export function getStock(symbol: string): Stock | undefined {
  return getSiteData().stocks[symbol];
}

// ---- Backtests (public/data/backtests.json) ----

export interface BacktestMetrics {
  total_return: number;
  cagr: number;
  sharpe: number;
  max_drawdown: number;
}

export type EquityPoint = [string, number];

export interface BenchmarkSeries {
  name: string;
  equity: EquityPoint[];
  metrics: BacktestMetrics;
}

export interface Holding {
  symbol: string;
  rank: number;
  entered: string;
  reason: string;
}

export interface StrategySeries extends BenchmarkSeries {
  key: string;
  definition: string;
  methodology: string;
  decision_date: string;
  holdings: Holding[];
  current_holdings: string[];
}

export interface BacktestScope {
  label: string;
  top_n: number;
  universe: number;
  benchmark: BenchmarkSeries;
  strategies: StrategySeries[];
}

export type BacktestScopeKey =
  | "all"
  | "L0-energy"
  | "L1-chips"
  | "L2-infra"
  | "L4-application";

export interface BacktestsData {
  generated_at: string;
  window: { start: string; end: string; universe: number };
  params: {
    rebalance: string;
    fees_pct: number;
    fundamental_lag_days: number;
  };
  survivorship_warning: string;
  scopes: Record<string, BacktestScope>;
}

let cachedBacktests: BacktestsData | null = null;

export function getBacktests(): BacktestsData {
  if (cachedBacktests) return cachedBacktests;
  const file = path.join(process.cwd(), "public", "data", "backtests.json");
  const raw = fs.readFileSync(file, "utf-8");
  cachedBacktests = JSON.parse(raw) as BacktestsData;
  return cachedBacktests;
}

export function getAllSymbols(): string[] {
  return Object.keys(getSiteData().stocks).sort();
}

// ---- Graph resiliency analysis (public/data/graph_analysis.json) ----

export interface ResiliencyComponents {
  concentration: number;
  spof: number;
  redundancy: number;
  certainty: number;
}

export interface ResiliencyNode {
  id: string;
  name: string;
  layer: string;
  health: number | null;
  components: ResiliencyComponents;
  ens: number | null;
  flags: string[];
  pagerank: number;
  betweenness: number;
  in_scc: boolean;
  is_articulation: boolean;
  in_degree: number;
  out_degree: number;
}

export interface ResiliencyGraphStats {
  n_nodes: number;
  n_edges: number;
  articulation_points: string[];
  bridges: [string, string][];
  largest_scc_size: number;
  fragility_ratio: number;
  assortativity: number;
}

export interface LayerHealth {
  mean: number;
  min: number;
  max: number;
  n: number;
}

export interface TopSpof {
  id: string;
  name: string;
  layer: string;
  betweenness: number;
}

export interface MacroSnapshot {
  dff: number;
  dgs10: number;
  elec: number;
  retrieved_at: string;
}

export interface Macro {
  snapshot: MacroSnapshot;
  scenario_note: string;
}

export interface EdgeStress {
  src: string;
  dst: string;
  type: string;
  stress_score: number;
  stressed_weight: number;
}

export interface Cascade {
  scenario: string;
  seeds: string[];
  direction: "forward" | "reverse";
  affected_count: number;
  reach: number;
}

export interface GraphAnalysis {
  generated_at: string;
  disclaimer: string;
  graph: ResiliencyGraphStats;
  nodes: ResiliencyNode[];
  layers: Record<string, LayerHealth>;
  overall_health: number;
  top_spofs: TopSpof[];
  macro: Macro;
  edge_stress: EdgeStress[];
  cascades: Cascade[];
}

let cachedGraphAnalysis: GraphAnalysis | null = null;

export function getGraphAnalysis(): GraphAnalysis {
  if (cachedGraphAnalysis) return cachedGraphAnalysis;
  const file = path.join(
    process.cwd(),
    "public",
    "data",
    "graph_analysis.json",
  );
  const raw = fs.readFileSync(file, "utf-8");
  cachedGraphAnalysis = JSON.parse(raw) as GraphAnalysis;
  return cachedGraphAnalysis;
}

// ---- Congressional trades (public/data/congress.json) ----

// Correlational committee/sector overlap signal attached to a trade.
// Definition + validator live in the client-safe lib/conflict.ts (no node:fs)
// so Client Components can import them; re-exported here for convenience.
export type { ConflictSignal } from "./conflict";
export { expectedConflictRationale, isValidConflictSignal } from "./conflict";
import type { ConflictSignal } from "./conflict";

// Member-profile enrichment (ideology + sponsored legislation). Definitions +
// client-safe helpers live in lib/congress_profile.ts (no node:fs); re-exported
// here for convenience.
export type { Ideology, SponsoredBill, SponsoredSummary } from "./congress_profile";
export { ideologyLabel, ideologyPosition } from "./congress_profile";
import type { Ideology, SponsoredSummary } from "./congress_profile";

export interface CommitteePolicyMapEntry {
  committee: string;
  policy_areas: string[];
}

export interface CongressPartyBreakdown {
  Democrat?: number;
  Republican?: number;
  Independent?: number;
  unknown?: number;
}

export interface CongressTrade {
  politician: string;
  state: string | null;
  party: string | null;
  year: number | null;
  ticker: string | null;
  sector: string | null;
  asset: string | null;
  txn_type: string | null; // "P" (purchase) | "S" (sale) | "E" (exchange) ...
  txn_date: string | null;
  filing_date: string | null;
  reporting_lag_days: number | null;
  amount_range_low: number | null;
  amount_range_high: number | null;
  source: string | null;
  conflict_signal?: ConflictSignal | null;
}

export interface CongressSectorTopItem {
  sector: string;
  n: number;
}

export interface CongressPolitician {
  politician: string;
  state: string | null;
  party: string | null;
  n_trades: number;
  n_buys: number;
  n_sells: number;
  est_volume_low: number;
  est_volume_high: number;
  top_sectors: CongressSectorTopItem[];
  last_trade_date: string | null;
  committees?: string[] | null;
  jurisdiction_sectors?: string[] | null;
  // Member-profile enrichment (all optional → today's congress.json still
  // type-checks unchanged). ideology = a statistical measure of voting
  // patterns (Voteview), not a personal judgment.
  ideology?: Ideology | null;
  policy_areas?: string[] | null;
  sponsored?: SponsoredSummary | null;
}

export interface CongressSector {
  sector: string;
  n_trades: number;
  n_buys: number;
  n_sells: number;
  est_volume_low: number;
  est_volume_high: number;
  n_politicians: number;
}

export interface CongressTotals {
  n_trades: number;
  n_politicians: number;
  n_tickers: number;
  n_sectors: number;
  date_min: string | null;
  date_max: string | null;
  n_scanned_skipped: number;
  est_volume_low: number;
  est_volume_high: number;
  n_conflict_flagged?: number;
  n_politicians_matched?: number;
  party_breakdown?: CongressPartyBreakdown;
  n_with_ideology?: number;
  bills_enabled?: boolean;
}

export interface CongressData {
  generated_at: string;
  source: string;
  source_class?: string;
  disclaimer: string;
  totals: CongressTotals;
  by_politician: CongressPolitician[];
  by_sector: CongressSector[];
  trades: CongressTrade[];
  // Member-profile enrichment top-level fields (optional → backward-compatible).
  ideology_note?: string;
  committee_policy_map?: CommitteePolicyMapEntry[];
  committee_policy_map_note?: string;
  member_source?: string;
  member_match_coverage?: {
    n_politicians: number;
    n_matched: number;
    coverage_pct: number;
    n_unmatched: number;
    unmatched: string[];
  };
}

let cachedCongress: CongressData | null = null;

export function getCongressData(): CongressData {
  if (cachedCongress) return cachedCongress;
  const file = path.join(process.cwd(), "public", "data", "congress.json");
  const raw = fs.readFileSync(file, "utf-8");
  cachedCongress = JSON.parse(raw) as CongressData;
  return cachedCongress;
}

// ---- Per-ticker congress summary (for the "Why consider" explainer) ----

// Public-record facts only: WHO traded a given ticker and the net buy/sell
// counts as disclosed in House/Senate PTRs. This is STRICTLY CORRELATIONAL —
// nothing here is, or implies, a signal, recommendation, or accusation.
export interface CongressSymbolPolitician {
  politician: string;
  party: string | null;
  n: number;
}

export interface CongressSymbolRecentTrade {
  politician: string;
  party: string | null;
  txn_type: string | null;
  txn_date: string | null;
  amount_range_low: number | null;
  amount_range_high: number | null;
}

export interface CongressSymbolSummary {
  n_trades: number;
  n_buys: number;
  n_sells: number;
  est_volume_low: number;
  est_volume_high: number;
  n_politicians: number;
  politicians: CongressSymbolPolitician[];
  recent: CongressSymbolRecentTrade[];
}

const CONGRESS_SYMBOL_TOP_POLITICIANS = 6;
const CONGRESS_SYMBOL_RECENT = 6;

export function getCongressForSymbol(
  symbol: string,
): CongressSymbolSummary | null {
  const data = getCongressData();
  const trades = (data.trades ?? []).filter((t) => t.ticker === symbol);
  if (trades.length === 0) return null;

  let n_buys = 0;
  let n_sells = 0;
  let est_volume_low = 0;
  let est_volume_high = 0;
  const byPolitician = new Map<
    string,
    { politician: string; party: string | null; n: number }
  >();

  for (const t of trades) {
    if (t.txn_type === "P") n_buys += 1;
    else if (t.txn_type === "S") n_sells += 1;
    est_volume_low += t.amount_range_low ?? 0;
    est_volume_high += t.amount_range_high ?? 0;
    const entry = byPolitician.get(t.politician);
    if (entry) entry.n += 1;
    else
      byPolitician.set(t.politician, {
        politician: t.politician,
        party: t.party,
        n: 1,
      });
  }

  const politicians = [...byPolitician.values()]
    .sort((a, b) => b.n - a.n)
    .slice(0, CONGRESS_SYMBOL_TOP_POLITICIANS);

  // Newest first; undated trades sink to the bottom (NaN-safe parse).
  const ts = (d: string | null | undefined): number => {
    if (!d) return -Infinity;
    const parsed = Date.parse(d);
    return Number.isNaN(parsed) ? -Infinity : parsed;
  };
  const recent: CongressSymbolRecentTrade[] = [...trades]
    .sort((a, b) => ts(b.txn_date) - ts(a.txn_date))
    .slice(0, CONGRESS_SYMBOL_RECENT)
    .map((t) => ({
      politician: t.politician,
      party: t.party,
      txn_type: t.txn_type,
      txn_date: t.txn_date,
      amount_range_low: t.amount_range_low,
      amount_range_high: t.amount_range_high,
    }));

  return {
    n_trades: trades.length,
    n_buys,
    n_sells,
    est_volume_low,
    est_volume_high,
    n_politicians: byPolitician.size,
    politicians,
    recent,
  };
}

// ---- News feed (public/data/news.json) ----

// Types + client-safe display helpers live in lib/news.ts (no node:fs) so
// Client Components can import them; re-exported here for convenience.
export type {
  Certainty,
  GraphEdgeRef,
  CandidateEdge,
  NewsArticle,
  NewsData,
  CertaintyMeta,
} from "./news";
export { certaintyMeta, edgeBadge, edgeTerms } from "./news";
import type { NewsData } from "./news";

// `null` is a valid, explicit state: the news.json may not have been generated
// yet (the pull step is guarded). Callers (the /news page) must handle null.
let cachedNews: NewsData | null = null;
let newsLoaded = false;

export function getNewsData(): NewsData | null {
  if (newsLoaded) return cachedNews;
  newsLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "news.json");
  if (!fs.existsSync(file)) {
    cachedNews = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    cachedNews = JSON.parse(raw) as NewsData;
  } catch {
    cachedNews = null;
  }
  return cachedNews;
}

// ---- Halal screening (public/data/halal.json) ----
// Types + client-safe helpers live in lib/halal.ts (no node:fs); re-exported.
export type {
  HalalData,
  HalalVerdict,
  HalalOverall,
  HalalStandardResult,
  HalalTestResult,
  HalalBusiness,
  HalalPurification,
  HalalAlert,
  HalalAlertsData,
} from "./halal";
export { overallLabel, overallTone, fmtRatioPct } from "./halal";
import type { HalalData, HalalAlertsData } from "./halal";

let cachedHalal: HalalData | null = null;
let halalLoaded = false;

export function getHalalData(): HalalData | null {
  if (halalLoaded) return cachedHalal;
  halalLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "halal.json");
  if (!fs.existsSync(file)) {
    cachedHalal = null;
    return null;
  }
  try {
    cachedHalal = JSON.parse(fs.readFileSync(file, "utf-8")) as HalalData;
  } catch {
    cachedHalal = null;
  }
  return cachedHalal;
}

// ---- Halal compliance-change alerts (public/data/halal_alerts.json) ----
// Null-safe: absent or corrupt file returns null (file is generated by the
// export_halal.py diff engine and may legitimately be absent until Task-12 runs).
// Pattern mirrors getNewsData() exactly.
let cachedHalalAlerts: HalalAlertsData | null = null;
let halalAlertsLoaded = false;

export function getHalalAlerts(): HalalAlertsData | null {
  if (halalAlertsLoaded) return cachedHalalAlerts;
  halalAlertsLoaded = true;
  const file = path.join(
    process.cwd(),
    "public",
    "data",
    "halal_alerts.json",
  );
  if (!fs.existsSync(file)) {
    cachedHalalAlerts = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    cachedHalalAlerts = JSON.parse(raw) as HalalAlertsData;
  } catch {
    cachedHalalAlerts = null;
  }
  return cachedHalalAlerts;
}

// Articles that tag a given symbol, newest first, capped. Null-safe: returns
// [] when news.json is absent / unparseable. `published` is parsed NaN-safely
// for the sort (undated articles sink to the bottom).
import type { NewsArticle } from "./news";

const SYMBOL_NEWS_CAP = 12;

export function getNewsForSymbol(symbol: string): NewsArticle[] {
  const data = getNewsData();
  if (!data) return [];
  const ts = (d: string | null | undefined): number => {
    if (!d) return -Infinity;
    const t = Date.parse(d);
    return Number.isNaN(t) ? -Infinity : t;
  };
  return (data.articles ?? [])
    .filter((a) => (a.tickers ?? []).includes(symbol))
    .sort((a, b) => ts(b.published) - ts(a.published))
    .slice(0, SYMBOL_NEWS_CAP);
}

// ---- Supply-chain chokepoint layer (public/data/chokepoints.json) ----

// Types + client-safe display helpers live in lib/chokepoints.ts (fs-reading
// exception documented there) so Client Components can import them;
// re-exported here for convenience, mirroring the news.ts pattern above.
// getChokepointsData()/getChokepointById() (the fs-reading exception) are
// defined directly below, NOT in lib/chokepoints.ts — that file is imported
// by VALUE from several Client Components (see its file header), so it must
// stay free of node:fs.
export type {
  ChokepointCategory,
  ClaimClass,
  SourceClass,
  ChokepointClaim,
  GraphCrossref,
  Chokepoint,
  ChokepointsValidation,
  ChokepointsSummary,
  ChokepointsData,
  ClaimClassMeta,
} from "./chokepoints";
export {
  categoryColor,
  categoryLabel,
  severityColor,
  severityBand,
  claimClassMeta,
  headlineClaim,
  sortedClaims,
  chokepointsForNode,
  groupByCategory,
  CATEGORY_ORDER,
  CHOKEPOINT_CATEGORY_LABELS,
  CHOKEPOINT_CATEGORY_COLORS,
} from "./chokepoints";
import type { ChokepointsData, Chokepoint } from "./chokepoints";

// GUARDED, NEVER THROWS — mirrors getNewsData() immediately above and
// getTaDeskData()/getArchetypeData(). chokepoints.json is generated on the
// owner's machine (scripts/build_chokepoints.py) and NOT committed — it may
// legitimately be absent (fresh clone, CI, pre-pipeline Vercel build).
// Callers (page components) must handle `null` with an empty state.
let cachedChokepoints: ChokepointsData | null | undefined;

export function getChokepointsData(): ChokepointsData | null {
  if (cachedChokepoints !== undefined) return cachedChokepoints;
  try {
    const file = path.join(process.cwd(), "public", "data", "chokepoints.json");
    if (!fs.existsSync(file)) {
      cachedChokepoints = null;
      return cachedChokepoints;
    }
    const raw = fs.readFileSync(file, "utf-8");
    const parsed = JSON.parse(raw) as ChokepointsData;
    if (!parsed || !Array.isArray(parsed.chokepoints)) {
      cachedChokepoints = null;
      return cachedChokepoints;
    }
    cachedChokepoints = parsed;
  } catch {
    cachedChokepoints = null;
  }
  return cachedChokepoints;
}

export function getChokepointById(id: string): Chokepoint | undefined {
  return getChokepointsData()?.chokepoints.find((cp) => cp.id === id);
}
