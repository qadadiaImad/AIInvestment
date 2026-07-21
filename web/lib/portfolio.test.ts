import { describe, it, expect, vi, afterEach } from "vitest";

// getPortfolioData() is a module-singleton cache (existsSync-guarded,
// try/catch JSON.parse, never throws — mirrors getRiskData()/
// getArchetypeData()). We mock node:fs so these tests never touch the real
// filesystem (in particular, never web/data/portfolio.json — that path is
// pipeline-owned/gitignored and may not exist in this environment) and
// reset the module registry between cases so each test gets a fresh cache.
//
// PRIVACY REGRESSION GUARD: one test below asserts the reader opens
// path.join(process.cwd(), "data", "portfolio.json") — NOT
// "public"/"data" — since public/** bypasses the /terminal proxy gate.

const RISK_BLOCK = {
  vol_annualized_pct: 28.4,
  var95_1d_pct: -2.9,
  sharpe_1y: 0.85,
  beta_vs_spy: 1.32,
  max_pairwise_correlation: { a: "MSFT", b: "NVDA", value: 0.61 },
  series_coverage: {
    n_holdings_included: 2,
    n_holdings_total_priced: 2,
    weight_coverage_pct: 100.0,
    excluded: [],
  },
  methodology_note: "fixed-weight proxy note",
  warnings: [],
};

const HAPPY: unknown = {
  generated_at: "2026-07-14T18:32:00Z",
  schema_version: "portfolio-v1",
  source_class: "computed",
  disclaimer: "Educational research only — not financial advice.",
  positions_source: {
    path: "data/portfolio/positions.json",
    mtime: "2026-07-14T09:11:00Z",
    n_raw_rows: 3,
    n_positions_after_merge: 2,
    found: true,
  },
  prices_source: {
    provider: "yahoo-finance-chart-api",
    source_class: "api",
    batch_retrieved_at: "2026-07-14T06:00:00Z",
  },
  site_source: { generated_at: "2026-07-14T06:05:00Z" },
  params: {
    base_currency: "USD",
    window_trading_days: 252,
    min_bars: 60,
    rf_annual: 0.04,
    rf_source: "cli-default",
    top_n_correlation: 5,
    var_confidence: 0.95,
  },
  positions: [
    {
      symbol: "NVDA",
      quantity: 10.0,
      lots_merged: 1,
      cost_basis_per_share: 400.0,
      cost_basis_total_usd: 4000.0,
      acquired_date: "2024-01-10",
      note: "core position",
      layer: "L1-chips",
      last_price: 550.0,
      price_as_of: "2026-07-14",
      price_source: "prices_file",
      market_value_usd: 5500.0,
      weight_pct: 44.4265,
      unrealized_pnl_usd: 1500.0,
      unrealized_pnl_pct: 37.5,
      day_change_pct: 10.0,
      day_change_usd: 500.0,
      warnings: [],
    },
    {
      symbol: "MSFT",
      quantity: 20.0,
      lots_merged: 1,
      cost_basis_per_share: 250.0,
      cost_basis_total_usd: 5000.0,
      acquired_date: "2024-02-01",
      note: null,
      layer: "L2-infra",
      last_price: 294.0,
      price_as_of: "2026-07-14",
      price_source: "prices_file",
      market_value_usd: 5880.0,
      weight_pct: 47.4959,
      unrealized_pnl_usd: 880.0,
      unrealized_pnl_pct: 17.6,
      day_change_pct: -2.0,
      day_change_usd: -120.0,
      warnings: [],
    },
    {
      symbol: "ZZZQ",
      quantity: 5.0,
      lots_merged: 1,
      cost_basis_per_share: null,
      cost_basis_total_usd: null,
      acquired_date: null,
      note: null,
      layer: null,
      last_price: null,
      price_as_of: null,
      price_source: null,
      market_value_usd: null,
      weight_pct: null,
      unrealized_pnl_usd: null,
      unrealized_pnl_pct: null,
      day_change_pct: null,
      day_change_usd: null,
      warnings: ["ZZZQ: no price data available"],
    },
  ],
  aggregates: {
    total_value_usd: 12380.0,
    invested_value_usd: 11380.0,
    cash_usd: 1000.0,
    cash_weight_pct: 8.0775,
    total_cost_basis_usd: 9000.0,
    total_unrealized_pnl_usd: 2380.0,
    total_unrealized_pnl_pct: 26.4444,
    day_pnl_usd: 380.0,
    day_pnl_pct: 3.1667,
    n_positions: 3,
    n_positions_priced: 2,
    n_positions_unpriced: 1,
    layer_exposure: [
      { layer: "L0-energy", weight_pct: 0.0, market_value_usd: 0.0, n_positions: 0 },
      { layer: "L1-chips", weight_pct: 44.4265, market_value_usd: 5500.0, n_positions: 1 },
      { layer: "L2-infra", weight_pct: 47.4959, market_value_usd: 5880.0, n_positions: 1 },
      { layer: "L3-models", weight_pct: 0.0, market_value_usd: 0.0, n_positions: 0 },
      { layer: "L4-application", weight_pct: 0.0, market_value_usd: 0.0, n_positions: 0 },
      { layer: "unclassified", weight_pct: 0.0, market_value_usd: 0.0, n_positions: 0 },
      { layer: "cash", weight_pct: 8.0775, market_value_usd: 1000.0, n_positions: 0 },
    ],
    concentration: {
      top1_weight_pct: 51.6696,
      top3_weight_pct: 100.0,
      hhi: 0.50055,
      basis: "invested_value_excluding_cash",
    },
  },
  risk: RISK_BLOCK,
  warnings: [],
};

const EMPTY_STATE: unknown = {
  generated_at: "2026-07-14T18:32:00Z",
  schema_version: "portfolio-v1",
  source_class: "computed",
  disclaimer: "Educational research only — not financial advice.",
  positions_source: {
    path: "data/portfolio/positions.json",
    mtime: null,
    n_raw_rows: 0,
    n_positions_after_merge: 0,
    found: false,
  },
  prices_source: {
    provider: "yahoo-finance-chart-api",
    source_class: "api",
    batch_retrieved_at: null,
  },
  site_source: { generated_at: null },
  params: {
    base_currency: "USD",
    window_trading_days: 252,
    min_bars: 60,
    rf_annual: 0.04,
    rf_source: "cli-default",
    top_n_correlation: 5,
    var_confidence: 0.95,
  },
  positions: [],
  aggregates: null,
  risk: null,
  warnings: [
    "no positions file found at data/portfolio/positions.json — copy positions.example.json and edit it with your holdings",
  ],
};

async function loadFresh(mockFs: {
  existsSync: (p: string) => boolean;
  readFileSync: () => string;
}) {
  vi.resetModules();
  vi.doMock("node:fs", () => ({ default: mockFs, ...mockFs }));
  return import("./portfolio");
}

describe("getPortfolioData", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("returns null when the file is absent (existsSync guard, never throws)", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getPortfolioData()).toBeNull();
  });

  it("returns null on unparseable JSON (try/catch, never throws)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => "{not json" });
    expect(mod.getPortfolioData()).toBeNull();
  });

  it("returns null on structurally malformed JSON (missing positions/warnings/positions_source)", async () => {
    const mod = await loadFresh({
      existsSync: () => true,
      readFileSync: () => JSON.stringify({ schema_version: "x" }),
    });
    expect(mod.getPortfolioData()).toBeNull();
  });

  it("parses and caches a well-formed happy-path bundle (module singleton)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    const first = mod.getPortfolioData();
    expect(first).not.toBeNull();
    expect(first?.positions).toHaveLength(3);
    expect(first?.positions_source.found).toBe(true);
    // Cached: a second call returns the same reference without re-reading.
    expect(mod.getPortfolioData()).toBe(first);
  });

  it("returns the parsed object as-is (not null) for a well-formed empty-state bundle", async () => {
    const mod = await loadFresh({
      existsSync: () => true,
      readFileSync: () => JSON.stringify(EMPTY_STATE),
    });
    const data = mod.getPortfolioData();
    expect(data).not.toBeNull();
    expect(data?.positions_source.found).toBe(false);
    expect(data?.aggregates).toBeNull();
    expect(data?.risk).toBeNull();
    expect(data?.warnings[0]).toMatch(/no positions file found/);
  });

  it("reads from data/portfolio.json under process.cwd() — NEVER public/data (privacy regression guard)", async () => {
    const seen: string[] = [];
    const mod = await loadFresh({
      existsSync: (p: string) => {
        seen.push(p);
        return true;
      },
      readFileSync: () => JSON.stringify(HAPPY),
    });
    mod.getPortfolioData();
    expect(seen).toHaveLength(1);
    const p = seen[0];
    expect(p.endsWith(["data", "portfolio.json"].join("/")) || p.includes(`${"data"}/portfolio.json`)).toBe(
      true,
    );
    expect(p).not.toMatch(/public[\\/]+data/);
  });
});

describe("isPortfolioEmpty", () => {
  it("is true for null", () => {
    return import("./portfolio").then((mod) => {
      expect(mod.isPortfolioEmpty(null)).toBe(true);
    });
  });

  it("is true when positions_source.found is false", async () => {
    const mod = await import("./portfolio");
    expect(mod.isPortfolioEmpty(EMPTY_STATE as import("./portfolio").PortfolioData)).toBe(true);
  });

  it("is false for a happy-path bundle", async () => {
    const mod = await import("./portfolio");
    expect(mod.isPortfolioEmpty(HAPPY as import("./portfolio").PortfolioData)).toBe(false);
  });
});

describe("toCardData — privacy transform", () => {
  it("never includes a *_usd-named key at any depth of its output", async () => {
    const mod = await import("./portfolio");
    const card = mod.toCardData(HAPPY as import("./portfolio").PortfolioData);
    const json = JSON.stringify(card);
    expect(json).not.toMatch(/_usd/);
    // No literal dollar sign either, and no digit sequence that could read
    // as a raw dollar amount smuggled into a string field.
    expect(json).not.toMatch(/\$\d/);
  });

  it("picks percentage/ratio fields through correctly", async () => {
    const mod = await import("./portfolio");
    const card = mod.toCardData(HAPPY as import("./portfolio").PortfolioData);
    expect(card.day_pnl_pct).toBeCloseTo(3.1667, 4);
    expect(card.total_unrealized_pnl_pct).toBeCloseTo(26.4444, 4);
    expect(card.concentration.top3_weight_pct).toBe(100.0);
    expect(card.concentration.hhi).toBeCloseTo(0.50055, 5);
    expect(card.risk?.vol_annualized_pct).toBe(28.4);
    expect(card.risk?.beta_vs_spy).toBe(1.32);
    expect(card.layer_exposure).toEqual([
      { layer: "L0-energy", weight_pct: 0.0 },
      { layer: "L1-chips", weight_pct: 44.4265 },
      { layer: "L2-infra", weight_pct: 47.4959 },
      { layer: "L3-models", weight_pct: 0.0 },
      { layer: "L4-application", weight_pct: 0.0 },
      { layer: "unclassified", weight_pct: 0.0 },
      { layer: "cash", weight_pct: 8.0775 },
    ]);
    expect(card.n_positions).toBe(3);
    expect(card.generated_at).toBe("2026-07-14T18:32:00Z");
  });

  it("degrades cleanly (nulls, not throws) when aggregates/risk are null", async () => {
    const mod = await import("./portfolio");
    const card = mod.toCardData(EMPTY_STATE as import("./portfolio").PortfolioData);
    expect(card.layer_exposure).toEqual([]);
    expect(card.total_unrealized_pnl_pct).toBeNull();
    expect(card.day_pnl_pct).toBeNull();
    expect(card.concentration).toEqual({ top1_weight_pct: null, top3_weight_pct: null, hhi: null });
    expect(card.risk).toBeNull();
    expect(card.n_positions).toBe(0);
  });
});

describe("sortPositionsForDisplay", () => {
  it("orders priced positions by weight_pct desc, unpriced last", async () => {
    const mod = await import("./portfolio");
    const positions = (HAPPY as import("./portfolio").PortfolioData).positions;
    const sorted = mod.sortPositionsForDisplay(positions);
    expect(sorted.map((p) => p.symbol)).toEqual(["MSFT", "NVDA", "ZZZQ"]);
  });

  it("is a no-op on an empty array", async () => {
    const mod = await import("./portfolio");
    expect(mod.sortPositionsForDisplay([])).toEqual([]);
  });
});
