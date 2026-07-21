import { describe, it, expect, vi, afterEach } from "vitest";

// getArchetypeData() is a module-singleton cache (existsSync-guarded,
// try/catch JSON.parse, never throws — mirrors getRiskData() in
// lib/risk.ts). We mock node:fs so these tests never touch the real
// filesystem (in particular, never public/data/archetypes.json — that file
// is pipeline-owned and out of this round's write scope) and reset the
// module registry between cases so each test gets a fresh cache.

const HAPPY: unknown = {
  schema_version: "archetypes-v1",
  methodology_version: "graham-buffett-lynch-v1.0",
  generated_at: "2026-07-15T00:00:00Z",
  source_class: "computed",
  disclaimer: "Rule-based scorecard — not a prediction, not investment advice.",
  source: { name: "site.json", path: "web/public/data/site.json", generated_at: "2026-07-14T12:00:00Z" },
  min_evaluable_criteria: 3,
  min_evaluable_weight_pct: 50,
  universe: { n_symbols: 2, layers: ["L1-chips"] },
  methodology: {
    graham: { name: "Graham — Defensive Value", criteria: [], excluded_criteria: [] },
    buffett: { name: "Buffett — Quality Moat", criteria: [], excluded_criteria: [] },
    lynch: { name: "Lynch — Growth at a Reasonable Price", criteria: [], excluded_criteria: [] },
  },
  per_stock: [
    {
      symbol: "NVDA",
      layer: "L1-chips",
      as_of: "2026-07-14",
      archetypes: {
        graham: { score: 43, verdict: "poor_fit", n_pass: 3, n_evaluable: 7, n_total: 7, evaluable_weight_pct: 100, criteria: [], likes: [], concerns: [] },
        buffett: { score: 88, verdict: "strong_fit", n_pass: 6, n_evaluable: 7, n_total: 7, evaluable_weight_pct: 100, criteria: [], likes: [], concerns: [] },
        lynch: { score: 40, verdict: "poor_fit", n_pass: 2, n_evaluable: 4, n_total: 5, evaluable_weight_pct: 85, criteria: [], likes: [], concerns: [] },
      },
      warnings: [],
    },
    {
      symbol: "avgo",
      layer: "L1-chips",
      as_of: "2026-07-14",
      archetypes: {
        graham: { score: 91, verdict: "strong_fit", n_pass: 7, n_evaluable: 7, n_total: 7, evaluable_weight_pct: 100, criteria: [], likes: [], concerns: [] },
        buffett: { score: 60, verdict: "partial_fit", n_pass: 4, n_evaluable: 7, n_total: 7, evaluable_weight_pct: 100, criteria: [], likes: [], concerns: [] },
        lynch: { score: null, verdict: "not_evaluable", n_pass: 0, n_evaluable: 2, n_total: 5, evaluable_weight_pct: 40, criteria: [], likes: [], concerns: [] },
      },
      warnings: [],
    },
  ],
  top: {
    graham: [{ symbol: "AVGO", score: 91 }],
    buffett: [{ symbol: "NVDA", score: 88 }, { symbol: "AVGO", score: 60 }],
    lynch: [],
  },
  counts: {
    graham: { strong_fit: 1, partial_fit: 0, poor_fit: 1, not_evaluable: 0 },
    buffett: { strong_fit: 1, partial_fit: 1, poor_fit: 0, not_evaluable: 0 },
    lynch: { strong_fit: 0, partial_fit: 0, poor_fit: 1, not_evaluable: 1 },
  },
  warnings: [],
};

async function loadFresh(mockFs: { existsSync: (p: string) => boolean; readFileSync: () => string }) {
  vi.resetModules();
  vi.doMock("node:fs", () => ({ default: mockFs, ...mockFs }));
  return import("./archetypes");
}

describe("getArchetypeData", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("returns null when the file is absent (existsSync guard, never throws)", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getArchetypeData()).toBeNull();
  });

  it("returns null on unparseable JSON (try/catch, never throws)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => "{not json" });
    expect(mod.getArchetypeData()).toBeNull();
  });

  it("returns null on structurally malformed JSON (missing per_stock/top/counts)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify({ schema_version: "x" }) });
    expect(mod.getArchetypeData()).toBeNull();
  });

  it("parses and caches a well-formed bundle (module singleton)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    const first = mod.getArchetypeData();
    expect(first).not.toBeNull();
    expect(first?.per_stock).toHaveLength(2);
    // Cached: a second call returns the same reference without re-reading.
    expect(mod.getArchetypeData()).toBe(first);
  });
});

describe("getArchetypeForSymbol", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("is case-insensitive", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getArchetypeForSymbol("nvda")?.symbol).toBe("NVDA");
    expect(mod.getArchetypeForSymbol("AVGO")?.symbol).toBe("avgo");
  });

  it("returns null for an unknown symbol", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getArchetypeForSymbol("ZZZZ")).toBeNull();
  });

  it("returns null when data is absent", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getArchetypeForSymbol("NVDA")).toBeNull();
  });
});

describe("getArchetypeRows", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("returns per_stock when present", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getArchetypeRows()).toHaveLength(2);
  });

  it("returns [] when data is absent", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getArchetypeRows()).toEqual([]);
  });
});

describe("getArchetypeTopN", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("slices top[archetype] to n", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getArchetypeTopN("buffett", 1)).toEqual([{ symbol: "NVDA", score: 88 }]);
    expect(mod.getArchetypeTopN("buffett", 5)).toHaveLength(2);
  });

  it("returns [] for an archetype with no strong/partial fits", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getArchetypeTopN("lynch")).toEqual([]);
  });

  it("returns [] when data is absent", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getArchetypeTopN("graham")).toEqual([]);
  });
});
