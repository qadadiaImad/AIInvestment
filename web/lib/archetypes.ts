// Server-side loader for the investor-archetype scorecard dataset
// (public/data/archetypes.json).
//
// Pattern mirrors getRiskData() in lib/risk.ts (itself mirroring
// getTaDeskData()/getNewsData()): existsSync-guarded, try/catch around
// JSON.parse, module-singleton cache, NEVER throws. archetypes.json is
// produced by scripts/build_archetypes.py on the owner's machine (a pure,
// zero-network "computed" step over site.json) and is NOT part of this
// repo's web build — the file may legitimately be absent (fresh clone, CI,
// Vercel build before the owner has run the pipeline). Every caller must
// degrade gracefully rather than 500.
//
// Types below mirror the archetypes.json contract verbatim (schema_version
// "archetypes-v1") — do not rename fields. This is a rule-based, zero-LLM
// deterministic scorecard: see docs/superpowers/specs/2026-07-14-archetypes-
// design.md §6-7 for the binding field list (§7 is the authoritative web-
// reader shape, corrected from Design B's original draft).

import fs from "node:fs";
import path from "node:path";

export type ArchetypeKey = "graham" | "buffett" | "lynch";
export type Comparator = "gt" | "ge" | "le";
export type CriterionUnit = "x" | "pct" | "num";
export type ArchetypeVerdict =
  | "strong_fit"
  | "partial_fit"
  | "poor_fit"
  | "not_evaluable";

export interface ArchetypeCriterion {
  key: string;
  label: string;
  field: string;
  comparator: Comparator;
  unit: CriterionUnit;
  threshold: number;
  actual: number | null;
  evaluable: boolean;
  pass: boolean | null;
  weight: number;
  note: string | null;
}

export interface ArchetypeScorecard {
  score: number | null;
  verdict: ArchetypeVerdict;
  n_pass: number;
  n_evaluable: number;
  n_total: number;
  evaluable_weight_pct: number;
  criteria: ArchetypeCriterion[];
  likes: string[];
  concerns: string[];
}

export interface ArchetypeStockRecord {
  symbol: string;
  layer: string;
  as_of: string | null;
  archetypes: Record<ArchetypeKey, ArchetypeScorecard>;
  warnings: string[];
}

export interface ArchetypeMethodologyCriterion {
  key: string;
  label: string;
  field: string;
  comparator: Comparator;
  unit: CriterionUnit;
  threshold: number;
  weight: number;
  note?: string | null;
}

export interface ArchetypeMethodology {
  name: string;
  criteria: ArchetypeMethodologyCriterion[];
  excluded_criteria: string[];
}

export interface ArchetypeTopEntry {
  symbol: string;
  score: number;
}

export interface ArchetypeCounts {
  strong_fit: number;
  partial_fit: number;
  poor_fit: number;
  not_evaluable: number;
}

export interface ArchetypeSource {
  name: string;
  path: string;
  generated_at: string | null;
}

export interface ArchetypeUniverse {
  n_symbols: number;
  layers: string[];
}

export interface ArchetypeData {
  schema_version: string;
  methodology_version: string;
  generated_at: string;
  source_class: string;
  disclaimer: string;
  source: ArchetypeSource;
  min_evaluable_criteria: number;
  min_evaluable_weight_pct: number;
  universe: ArchetypeUniverse;
  methodology: Record<ArchetypeKey, ArchetypeMethodology>;
  per_stock: ArchetypeStockRecord[];
  top: Record<ArchetypeKey, ArchetypeTopEntry[]>;
  counts: Record<ArchetypeKey, ArchetypeCounts>;
  warnings: string[];
}

let cachedArchetypes: ArchetypeData | null = null;
let archetypesLoaded = false;

// Reads public/data/archetypes.json. Returns null when the file is absent,
// unparseable, or malformed — never throws. Cached after first read (module
// singleton, matches getRiskData()/getTaDeskData()/getMacroData() pattern).
export function getArchetypeData(): ArchetypeData | null {
  if (archetypesLoaded) return cachedArchetypes;
  archetypesLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "archetypes.json");
  if (!fs.existsSync(file)) {
    cachedArchetypes = null;
    return null;
  }
  try {
    const raw = fs.readFileSync(file, "utf-8");
    const parsed = JSON.parse(raw) as ArchetypeData;
    if (!parsed || !Array.isArray(parsed.per_stock) || !parsed.top || !parsed.counts) {
      cachedArchetypes = null;
      return null;
    }
    cachedArchetypes = parsed;
  } catch {
    cachedArchetypes = null;
  }
  return cachedArchetypes;
}

// Case-insensitive lookup by symbol. Mirrors getRiskStock(). O(n) is fine
// at universe size (~46).
export function getArchetypeForSymbol(symbol: string): ArchetypeStockRecord | null {
  const data = getArchetypeData();
  if (!data) return null;
  const needle = symbol.toUpperCase();
  return (
    data.per_stock.find((s) => s.symbol.toUpperCase() === needle) ?? null
  );
}

// data?.per_stock ?? [] — the whole universe, in source order.
export function getArchetypeRows(): ArchetypeStockRecord[] {
  return getArchetypeData()?.per_stock ?? [];
}

// data?.top[archetype].slice(0, n) ?? [] — top N strong/partial-fit names
// for one archetype, score desc (ties symbol asc), as pre-sorted upstream.
export function getArchetypeTopN(
  archetype: ArchetypeKey,
  n = 5,
): ArchetypeTopEntry[] {
  const data = getArchetypeData();
  if (!data) return [];
  return (data.top[archetype] ?? []).slice(0, n);
}
