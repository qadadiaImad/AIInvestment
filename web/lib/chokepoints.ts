// Supply-chain chokepoint layer (Round 6). Data source: web/public/data/chokepoints.json —
// GENERATED, GITIGNORED (same tier as risk.json / archetypes.json / graph_analysis.json),
// produced by scripts/build_chokepoints.py on the owner's machine. NOT committed, NOT a
// Vercel build-time dependency — may legitimately be absent (fresh clone, CI, pre-pipeline
// Vercel build). Every caller must degrade gracefully, never 500. Curated INPUT lives at
// chokepoints_source.json (repo root, committed — see docs/superpowers/specs/
// 2026-07-15-chokepoints-design.md).
//
// LEGAL/HONESTY: every claim carries class fact|reported|rumored + source + retrieved_at
// (CLAUDE.md rule #5). Never launder a rumored claim into a fact — see headlineClaim().
//
// NO node:fs HERE — this file is imported by VALUE (not just `import type`) from several
// Client Components (CapitalGraph, MapExplorer, NodeDetailPanel, ChokepointSideList,
// ChokepointClaimsPanel, ChokepointBoard) for categoryColor()/severityBand()/etc., so it
// must stay bundleable client-side. Mirrors lib/news.ts / lib/conflict.ts /
// lib/congress_profile.ts: types + client-safe display helpers live here; the fs-reading
// getChokepointsData()/getChokepointById() live in lib/data.ts (server-only) and are
// re-exported there for convenience. This is a DEVIATION from the design spec's draft
// (which put the fs reader in this file, mirroring lib/risk.ts/lib/archetypes.ts) —
// those files' fs code never actually reaches a client bundle because every client
// component that touches them does so via `import type` only (verified this pass); this
// file's helpers are genuinely needed as runtime values in client components, so it
// follows the news.ts split instead. See build verification for the Turbopack error this
// avoided ("chunking context does not support external modules (request: node:fs)").

export type ChokepointCategory =
  | "fab_concentration"
  | "equipment_monopoly"
  | "memory"
  | "packaging"
  | "export_controls"
  | "power_grid"
  | "materials"
  | "other";

export type ClaimClass = "fact" | "reported" | "rumored";
export type SourceClass = "api" | "html" | "xhr-json" | "filing";

export interface ChokepointClaim {
  text: string;
  class: ClaimClass;
  source_name: string;
  source_url: string;
  source_class: SourceClass;
  retrieved_at: string; // UTC ISO-8601
  needs_verification: boolean;
}

export interface GraphCrossref {
  source_class: "computed";
  is_articulation: boolean;
  betweenness: number;
}

export interface Chokepoint {
  id: string; // kebab-slug, stable
  name: string;
  category: ChokepointCategory;
  layers: string[]; // subset of LAYER_ORDER
  severity_score: number; // 0-100, curated
  severity_rationale: string;
  summary: string;
  card_tagline: string; // capture-card headline only, never rendered elsewhere as fact
  description: string;
  node_ids: string[]; // capital_web.json ids -> /map ring highlight
  external_entities: string[];
  tickers: string[];
  claims: ChokepointClaim[];
  mitigation_watch: string[];
  last_reviewed: string;
  needs_verification: boolean; // rolled up by build_chokepoints.py
  graph_crossref?: GraphCrossref; // joined by build_chokepoints.py against graph_analysis.json
}

export interface ChokepointsValidation {
  node_crossref_warnings: string[];
  schema_ok: boolean;
}
export interface ChokepointsSummary {
  n_entries: number;
  by_category: Record<string, number>;
  by_layer: Record<string, number>;
  n_claims: number;
  n_fact: number;
  n_reported: number;
  n_rumored: number;
  n_needs_verification: number;
  n_node_ids_total: number;
  n_node_ids_resolved: number;
  n_node_ids_unresolved: number;
}
export interface ChokepointsData {
  schema_version: string; // "chokepoints-v1"
  generated_at: string;
  source_class: "computed";
  source: string;
  disclaimer: string;
  validation: ChokepointsValidation;
  summary: ChokepointsSummary;
  chokepoints: Chokepoint[];
}

// ---- category display metadata ----
export const CHOKEPOINT_CATEGORY_LABELS: Record<ChokepointCategory, string> = {
  fab_concentration: "Foundry / Advanced Node",
  equipment_monopoly: "Equipment Monopoly",
  memory: "Memory (HBM)",
  packaging: "Advanced Packaging",
  export_controls: "Export Controls",
  power_grid: "Grid & Power",
  materials: "Materials",
  other: "Other Structural",
};

// Spread across the hue wheel so up to 8 simultaneous ring colors stay distinguishable
// (warm/cool alternation, colorblind-conscious). NOT reused 1:1 from LAYER_COLORS/
// ARCHETYPE_COLORS/MACRO_GROUP_COLORS — those are fills on a different visual channel
// (node body vs. this feature's ring/glow); within THIS legend all values are distinct.
export const CHOKEPOINT_CATEGORY_COLORS: Record<ChokepointCategory, string> = {
  fab_concentration: "#fb923c", // orange-400
  equipment_monopoly: "#d946ef", // fuchsia-500
  memory: "#22d3ee", // cyan-400
  packaging: "#facc15", // yellow-400
  export_controls: "#f43f5e", // rose-500
  power_grid: "#14b8a6", // teal-500
  materials: "#a3e635", // lime-400
  other: "#94a3b8", // slate-400
};

export function categoryColor(c: ChokepointCategory): string {
  return CHOKEPOINT_CATEGORY_COLORS[c] ?? "#6b7280";
}
export function categoryLabel(c: ChokepointCategory): string {
  return CHOKEPOINT_CATEGORY_LABELS[c] ?? c;
}

// ---- severity bands (curated severity_score, distinct from graph_crossref.betweenness) ----
const SEVERITY_RED = "#ef4444";
const SEVERITY_AMBER = "#f59e0b";
const SEVERITY_GREY = "#6b7280";

export function severityColor(score: number): string {
  if (score >= 75) return SEVERITY_RED;
  if (score >= 40) return SEVERITY_AMBER;
  return SEVERITY_GREY;
}
export function severityBand(score: number): "CRITICAL" | "ELEVATED" | "MODERATE" {
  if (score >= 75) return "CRITICAL";
  if (score >= 40) return "ELEVATED";
  return "MODERATE";
}

// ---- claim-class badge metadata ----
// Strongest -> weakest color ramp mirrors lib/news.ts's certaintyMeta() (filed=sky,
// reported=emerald, rumored=amber) for a consistent "how sure are we" visual grammar
// site-wide, even though the vocabulary here (fact/reported/rumored) is distinct from
// news.ts's (filed/reported/rumored) by design (different provenance systems).
export interface ClaimClassMeta {
  label: string;
  chipCls: string;
  note: string;
}
const CLAIM_CLASS_META: Record<ClaimClass, ClaimClassMeta> = {
  fact: {
    label: "FACT",
    chipCls: "text-sky-300 border-sky-500/50 bg-sky-500/10",
    note: "Grounded in a primary source (filing, regulatory rule, official statement).",
  },
  reported: {
    label: "REPORTED",
    chipCls: "text-emerald-300 border-emerald-500/50 bg-emerald-500/10",
    note: "Reported by credible secondary sources — not independently re-verified here.",
  },
  rumored: {
    label: "RUMORED",
    chipCls: "text-amber-300 border-amber-500/50 bg-amber-500/10",
    note: "Speculative / unconfirmed — treat as color, not conclusion.",
  },
};
export function claimClassMeta(c: ClaimClass): ClaimClassMeta {
  return CLAIM_CLASS_META[c];
}

// The single most important guardrail in this file: pick the claim a capture card is
// allowed to headline. NEVER returns a rumored claim (CLAUDE.md rule #5). Prefers
// fact > reported; returns null if the chokepoint has no fact/reported claims, so the
// card renders its documented fallback instead of ever mislabeling a rumor as stronger.
export function headlineClaim(cp: Chokepoint): ChokepointClaim | null {
  const fact = cp.claims.find((c) => c.class === "fact");
  if (fact) return fact;
  const reported = cp.claims.find((c) => c.class === "reported");
  return reported ?? null;
}

const CLASS_RANK: Record<ClaimClass, number> = { fact: 0, reported: 1, rumored: 2 };
export function sortedClaims(cp: Chokepoint): ChokepointClaim[] {
  return [...cp.claims].sort((a, b) => CLASS_RANK[a.class] - CLASS_RANK[b.class]);
}

// Chokepoints touching a given capital_web node id — used by NodeDetailPanel's "Linked
// chokepoints" row and CapitalGraph's ring-highlight lookup.
export function chokepointsForNode(data: ChokepointsData, nodeId: string): Chokepoint[] {
  return data.chokepoints.filter((cp) => cp.node_ids.includes(nodeId));
}

export const CATEGORY_ORDER: ChokepointCategory[] = [
  "fab_concentration",
  "equipment_monopoly",
  "packaging",
  "memory",
  "export_controls",
  "power_grid",
  "materials",
  "other",
];
export function groupByCategory(
  data: ChokepointsData,
): { category: ChokepointCategory; items: Chokepoint[] }[] {
  return CATEGORY_ORDER.map((category) => ({
    category,
    items: data.chokepoints
      .filter((cp) => cp.category === category)
      .sort((a, b) => b.severity_score - a.severity_score),
  })).filter((g) => g.items.length > 0);
}
