import { describe, it, expect } from "vitest";
import {
  headlineClaim,
  sortedClaims,
  chokepointsForNode,
  groupByCategory,
  severityBand,
  type Chokepoint,
  type ChokepointsData,
} from "./chokepoints";

// This file is imported by VALUE from Client Components (see its file
// header) and deliberately has NO node:fs — the fs-reading
// getChokepointsData()/getChokepointById() live in lib/data.ts instead and
// are tested in lib/data.chokepoints.test.ts. These tests cover the
// client-safe display/derivation helpers only.

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
  } as unknown as Chokepoint;
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
} as unknown as ChokepointsData;

describe("headlineClaim (fact/reported/rumored guardrail)", () => {
  it("never returns a rumored claim: prefers fact over reported", () => {
    const entry = cp({
      claims: [
        claim({ class: "rumored", text: "rumor" }),
        claim({ class: "reported", text: "reported thing" }),
        claim({ class: "fact", text: "fact thing" }),
      ],
    });
    expect(headlineClaim(entry)?.class).toBe("fact");
    expect(headlineClaim(entry)?.text).toBe("fact thing");
  });

  it("falls back to reported when no fact claim exists", () => {
    const entry = cp({
      claims: [claim({ class: "rumored" }), claim({ class: "reported", text: "reported thing" })],
    });
    expect(headlineClaim(entry)?.class).toBe("reported");
  });

  it("returns null when only rumored claims exist — never fabricates confidence", () => {
    const entry = cp({ claims: [claim({ class: "rumored" })] });
    expect(headlineClaim(entry)).toBeNull();
  });
});

describe("sortedClaims", () => {
  it("orders fact before reported before rumored without relabeling", () => {
    const entry = cp({
      claims: [
        claim({ class: "rumored", text: "r" }),
        claim({ class: "fact", text: "f" }),
        claim({ class: "reported", text: "rep" }),
      ],
    });
    expect(sortedClaims(entry).map((c) => c.class)).toEqual(["fact", "reported", "rumored"]);
  });
});

describe("chokepointsForNode", () => {
  it("filters chokepoints touching a given node id", () => {
    expect(chokepointsForNode(HAPPY, "TSM").map((c) => c.id)).toEqual(["tsmc-advanced-node"]);
    expect(chokepointsForNode(HAPPY, "MU").map((c) => c.id)).toEqual(["hbm-memory-concentration"]);
    expect(chokepointsForNode(HAPPY, "ZZZZ")).toEqual([]);
  });
});

describe("groupByCategory", () => {
  it("groups by category in CATEGORY_ORDER, severity-descending within group", () => {
    const data = {
      ...HAPPY,
      chokepoints: [
        cp({ id: "a", category: "memory", severity_score: 50 }),
        cp({ id: "b", category: "fab_concentration", severity_score: 92 }),
        cp({ id: "c", category: "memory", severity_score: 68 }),
      ],
    } as unknown as ChokepointsData;
    const groups = groupByCategory(data);
    expect(groups.map((g) => g.category)).toEqual(["fab_concentration", "memory"]);
    const memoryGroup = groups.find((g) => g.category === "memory");
    expect(memoryGroup?.items.map((i) => i.id)).toEqual(["c", "a"]);
  });
});

describe("severityBand / severityColor", () => {
  it("bands at the documented thresholds", () => {
    expect(severityBand(92)).toBe("CRITICAL");
    expect(severityBand(75)).toBe("CRITICAL");
    expect(severityBand(74)).toBe("ELEVATED");
    expect(severityBand(40)).toBe("ELEVATED");
    expect(severityBand(39)).toBe("MODERATE");
    expect(severityBand(0)).toBe("MODERATE");
  });
});
