import { describe, it, expect, vi, afterEach } from "vitest";

// getChokepointsData()/getChokepointById() live in lib/data.ts (not
// lib/chokepoints.ts — that file must stay node:fs-free, see its header)
// and are module-singleton cached (existsSync-guarded, try/catch
// JSON.parse, never throws — mirrors getNewsData() immediately above them).
// We mock node:fs so these tests never touch the real filesystem (in
// particular, never public/data/chokepoints.json — pipeline-owned, out of
// this round's write scope) and reset the module registry between cases so
// each test gets a fresh cache.

function claim(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    text: "Example claim.",
    class: "reported",
    source_name: "Example Outlet",
    source_url: "https://example.com/article",
    source_class: "html",
    retrieved_at: "2026-07-15T16:00:00Z",
    needs_verification: false,
    ...overrides,
  };
}

function cp(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "tsmc-advanced-node",
    name: "TSMC leading-edge fab concentration (Taiwan)",
    category: "fab_concentration",
    layers: ["L1-chips"],
    severity_score: 92,
    severity_rationale: "No qualified alternative at comparable yield/volume.",
    summary: "Sub-7nm logic runs through one company, on one island.",
    card_tagline: "ONE EARTHQUAKE AWAY",
    description: "TSMC manufactures the overwhelming majority of leading-edge logic.",
    node_ids: ["TSM"],
    external_entities: [],
    tickers: ["NVDA"],
    claims: [claim()],
    mitigation_watch: ["TSMC Arizona ramp"],
    last_reviewed: "2026-07-15",
    needs_verification: false,
    ...overrides,
  };
}

const HAPPY = {
  schema_version: "chokepoints-v1",
  generated_at: "2026-07-15T16:00:00Z",
  source_class: "computed",
  source: "chokepoints_source.json (curated) cross-referenced against capital_web.json + graph_analysis.json",
  disclaimer: "Educational research only — not financial advice.",
  validation: { node_crossref_warnings: [], schema_ok: true },
  summary: {
    n_entries: 2,
    by_category: { fab_concentration: 1, memory: 1 },
    by_layer: { "L1-chips": 2 },
    n_claims: 2,
    n_fact: 0,
    n_reported: 2,
    n_rumored: 0,
    n_needs_verification: 0,
    n_node_ids_total: 2,
    n_node_ids_resolved: 2,
    n_node_ids_unresolved: 0,
  },
  chokepoints: [
    cp(),
    cp({
      id: "hbm-memory-concentration",
      name: "HBM concentration",
      category: "memory",
      node_ids: ["MU"],
    }),
  ],
};

async function loadFresh(mockFs: {
  existsSync: (p: string) => boolean;
  readFileSync: () => string;
}) {
  vi.resetModules();
  vi.doMock("node:fs", () => ({ default: mockFs, ...mockFs }));
  return import("./data");
}

describe("getChokepointsData", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("returns null when the file is absent (existsSync guard, never throws)", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getChokepointsData()).toBeNull();
  });

  it("returns null on unparseable JSON (try/catch, never throws)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => "{not json" });
    expect(mod.getChokepointsData()).toBeNull();
  });

  it("returns null on structurally malformed JSON (missing chokepoints array)", async () => {
    const mod = await loadFresh({
      existsSync: () => true,
      readFileSync: () => JSON.stringify({ schema_version: "x" }),
    });
    expect(mod.getChokepointsData()).toBeNull();
  });

  it("parses and caches a well-formed bundle (module singleton)", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    const first = mod.getChokepointsData();
    expect(first).not.toBeNull();
    expect(first?.chokepoints).toHaveLength(2);
    expect(mod.getChokepointsData()).toBe(first);
  });
});

describe("getChokepointById", () => {
  afterEach(() => {
    vi.doUnmock("node:fs");
    vi.resetModules();
  });

  it("finds a chokepoint by id", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getChokepointById("hbm-memory-concentration")?.name).toBe("HBM concentration");
  });

  it("returns undefined for an unknown id", async () => {
    const mod = await loadFresh({ existsSync: () => true, readFileSync: () => JSON.stringify(HAPPY) });
    expect(mod.getChokepointById("does-not-exist")).toBeUndefined();
  });

  it("returns undefined when data is absent", async () => {
    const mod = await loadFresh({ existsSync: () => false, readFileSync: () => "" });
    expect(mod.getChokepointById("tsmc-advanced-node")).toBeUndefined();
  });
});
