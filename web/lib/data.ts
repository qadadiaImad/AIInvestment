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
  layer: LayerKey;
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
  layer: LayerKey;
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
  layers: Record<LayerKey, string[]>;
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
  cached = parsed;
  return cached;
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
