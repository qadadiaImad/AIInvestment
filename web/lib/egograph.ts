// Client-safe ego-graph model for the /map per-company value-chain view.
//
// This module is intentionally free of any Node-only imports (e.g. node:fs) and
// of React, so it can be used from both Server and Client Components. It
// transforms the EXISTING capital_web ({nodes, edges}) for a focal company into
// an [Inputs] -> Company -> [Outputs] model (Bloomberg-SPLC style). No new data
// and no data-pipeline change.
//
// LEGAL/HONESTY: each Relation carries the curated edge's OWN certainty
// (filed / reported / rumored) + source_url, NEVER upgraded. Direction is
// classified PER EDGE TYPE (see RELATION_SEMANTICS), not by arrow direction.
// Educational/research only — not investment advice.

import type { CapitalWeb, GraphEdge, GraphNode } from "./data";

// ---------------------------------------------------------------------------
// Relation semantics — the SINGLE SOURCE OF TRUTH for edge-type direction.
// ---------------------------------------------------------------------------
//
// `flow` answers: what does this edge type mean about the src/dst pair?
//   src_buys_from_dst  — src is the customer, dst is the supplier
//                        (types: customer, compute_commitment, cloud_on)
//   src_supplies_dst   — src is the supplier, dst is the customer
//                        (types: infra_partner, supplier)
//   capital            — src invests in / owns dst; dst is the holding, src the
//                        backer (types: equity_stake, subsidiary, voting_power,
//                        acquired, spinout)
//   related            — unknown type; best-effort, labeled "related"

export type RelationFlow =
  | "src_buys_from_dst"
  | "src_supplies_dst"
  | "capital"
  | "related";

export type RelationKind = "supply" | "compute" | "capital" | "related";
export type RelationSide = "input" | "output";

export interface RelationSemantic {
  flow: RelationFlow;
}

export const RELATION_SEMANTICS: Record<string, RelationSemantic> = {
  customer: { flow: "src_buys_from_dst" },
  compute_commitment: { flow: "src_buys_from_dst" },
  // cloud_on — focal=src runs on dst's cloud => dst is the supplier/input, src
  // the customer/output (like compute_commitment).
  cloud_on: { flow: "src_buys_from_dst" },
  infra_partner: { flow: "src_supplies_dst" },
  // supplier — focal=src supplies dst => dst is the customer/output, src the
  // supplier/input (like infra_partner).
  supplier: { flow: "src_supplies_dst" },
  equity_stake: { flow: "capital" },
  subsidiary: { flow: "capital" },
  voting_power: { flow: "capital" },
  // acquired / spinout — capital ownership: src owns/acquired dst (dst is a
  // holding/output for focal=src; src is a backer/parent/input for focal=dst).
  acquired: { flow: "capital" },
  spinout: { flow: "capital" },
};

const RELATED: RelationSemantic = { flow: "related" };

function semanticFor(type: string): RelationSemantic {
  return RELATION_SEMANTICS[type] ?? RELATED;
}

// ---------------------------------------------------------------------------
// Public types.
// ---------------------------------------------------------------------------

export interface Relation {
  type: string;
  kind: RelationKind;
  side: RelationSide;
  certainty?: string;
  source_url?: string;
  as_of?: string;
  // Compact human-readable deal terms (e.g. "$40B · 1.2 GW · 1M TPUs").
  terms: string;
  raw: GraphEdge;
}

export interface Counterparty {
  id: string;
  name: string;
  layer?: string;
  side: RelationSide;
  // The dominant kind for the pair (kind of the highest-salience relation).
  kind: RelationKind;
  relations: Relation[];
  // Sort salience: usd if any, else relation count.
  score: number;
}

export interface EgoCounts {
  inputs: number;
  outputs: number;
}

export interface EgoModel {
  focal: GraphNode;
  inputs: Counterparty[];
  outputs: Counterparty[];
  counts: EgoCounts;
}

// ---------------------------------------------------------------------------
// Classification: given an edge incident to the focal, decide which SIDE the
// OTHER endpoint sits on (input vs output) and the relation kind.
// ---------------------------------------------------------------------------

interface Classification {
  otherId: string;
  side: RelationSide;
  kind: RelationKind;
}

function kindForType(type: string, flow: RelationFlow): RelationKind {
  if (flow === "capital") return "capital";
  if (flow === "related") return "related";
  // supply/compute flows
  if (type === "compute_commitment" || type === "cloud_on") return "compute";
  return "supply";
}

function classify(edge: GraphEdge, focalId: string): Classification | null {
  const focalIsSrc = edge.src === focalId;
  const focalIsDst = edge.dst === focalId;
  if (!focalIsSrc && !focalIsDst) return null;

  const otherId = focalIsSrc ? edge.dst : edge.src;
  const { flow } = semanticFor(edge.type);
  const kind = kindForType(edge.type, flow);

  let side: RelationSide;
  switch (flow) {
    case "src_buys_from_dst":
      // src buys from dst -> dst is the supplier (input), src is the customer
      // (output).  focal = src -> other (dst) is an INPUT.
      side = focalIsSrc ? "input" : "output";
      break;
    case "src_supplies_dst":
      // src supplies dst -> dst is the customer (output), src is the supplier
      // (input).  focal = src -> other (dst) is an OUTPUT.
      side = focalIsSrc ? "output" : "input";
      break;
    case "capital":
      // src invests in / owns dst -> dst is the holding (capital-out / output),
      // src is the backer (capital-in / input).  focal = src -> other (dst) is
      // an OUTPUT (a holding); focal = dst -> other (src) is an INPUT (a backer).
      side = focalIsSrc ? "output" : "input";
      break;
    default:
      // related (unknown type): best-effort. focal = src -> output, else input.
      side = focalIsSrc ? "output" : "input";
      break;
  }

  return { otherId, side, kind };
}

// ---------------------------------------------------------------------------
// Term formatting.
// ---------------------------------------------------------------------------

// Compact USD formatter (self-contained so this module stays client-safe and
// free of cross-module coupling; mirrors lib/news.usdCompact).
function usdCompact(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(1)}K`;
  return `$${v.toFixed(0)}`;
}

// Compact count formatter for hardware units (e.g. 1000000 -> "1M").
function countCompact(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${trimZero(v / 1e9)}B`;
  if (abs >= 1e6) return `${trimZero(v / 1e6)}M`;
  if (abs >= 1e3) return `${trimZero(v / 1e3)}K`;
  return `${v}`;
}

function trimZero(v: number): string {
  return Number.isInteger(v) ? `${v}` : v.toFixed(1);
}

type AttrValue = number | string | null | undefined | unknown[];
type Attrs = Record<string, AttrValue> | undefined;

function numAttr(a: NonNullable<Attrs>, ...keys: string[]): number | null {
  for (const k of keys) {
    const v = a[k];
    if (typeof v === "number" && Number.isFinite(v)) return v;
  }
  return null;
}

function strAttr(a: NonNullable<Attrs>, ...keys: string[]): string | null {
  for (const k of keys) {
    const v = a[k];
    if (typeof v === "string" && v.trim() !== "") return v.trim();
  }
  return null;
}

// Compact deal terms: pick the few high-signal attr keys and omit the rest.
// Order: money -> power -> compute units -> percentage -> product/note.
// e.g. "$40B · 1.2 GW · 1M TPUs · H100 GPUs".
export function formatTerms(attrs: Attrs): string {
  if (!attrs) return "";
  const bits: string[] = [];

  // Money: usd or any *_usd key.
  let usd = numAttr(attrs, "usd");
  if (usd === null) {
    for (const k of Object.keys(attrs)) {
      if (k.endsWith("_usd")) {
        const v = attrs[k];
        if (typeof v === "number" && Number.isFinite(v)) {
          usd = v;
          break;
        }
      }
    }
  }
  if (usd !== null) bits.push(usdCompact(usd));

  // Power.
  const gw = numAttr(attrs, "power_gw");
  if (gw !== null) bits.push(`${trimZero(gw)} GW`);
  const mw = numAttr(attrs, "power_mw");
  if (mw !== null) bits.push(`${trimZero(mw)} MW`);

  // Compute units.
  const tpus = numAttr(attrs, "tpus");
  if (tpus !== null) bits.push(`${countCompact(tpus)} TPUs`);
  const gpus = numAttr(attrs, "gpus");
  if (gpus !== null) bits.push(`${countCompact(gpus)} GPUs`);

  // Stake percentage.
  const pct = numAttr(attrs, "pct", "stake_pct");
  if (pct !== null) bits.push(`${trimZero(pct)}%`);

  // Product / free-text note (low priority, single value).
  const product = strAttr(attrs, "product", "products");
  if (product) bits.push(product);
  else {
    const note = strAttr(attrs, "note", "description");
    if (note) bits.push(note);
  }

  return bits.join(" · ");
}

// Salience contribution of a single edge's terms (usd dominates).
function edgeUsd(attrs: Attrs): number {
  if (!attrs) return 0;
  let usd = numAttr(attrs, "usd");
  if (usd === null) {
    for (const k of Object.keys(attrs)) {
      if (k.endsWith("_usd")) {
        const v = attrs[k];
        if (typeof v === "number" && Number.isFinite(v)) {
          usd = v;
          break;
        }
      }
    }
  }
  return usd ?? 0;
}

// ---------------------------------------------------------------------------
// Kind metadata for the UI (label + Tailwind color class).
// ---------------------------------------------------------------------------

export interface RelationKindMeta {
  label: string;
  colorCls: string;
}

const KIND_META: Record<RelationKind, RelationKindMeta> = {
  supply: {
    label: "Supply",
    colorCls: "text-sky-300 border-sky-500/50 bg-sky-500/10",
  },
  compute: {
    label: "Compute",
    colorCls: "text-violet-300 border-violet-500/50 bg-violet-500/10",
  },
  capital: {
    label: "Capital",
    colorCls: "text-emerald-300 border-emerald-500/50 bg-emerald-500/10",
  },
  related: {
    label: "Related",
    colorCls: "text-zinc-400 border-zinc-600 bg-zinc-700/20",
  },
};

export function relationKindMeta(kind: RelationKind): RelationKindMeta {
  return KIND_META[kind] ?? KIND_META.related;
}

// ---------------------------------------------------------------------------
// buildEgoModel — the core transform.
// ---------------------------------------------------------------------------

// A pair key combines the other endpoint with the side, so a pair that is BOTH
// an input and an output (rare) yields two Counterparties (one per side).
function pairKey(otherId: string, side: RelationSide): string {
  return `${side}::${otherId}`;
}

export function buildEgoModel(web: CapitalWeb, focalId: string): EgoModel {
  const nodeById = new Map<string, GraphNode>();
  for (const n of web.nodes) nodeById.set(n.id, n);

  const focal: GraphNode =
    nodeById.get(focalId) ??
    ({ id: focalId, name: focalId, type: "unknown" } as GraphNode);

  // Aggregate edges into counterparties keyed by (side, otherId).
  const byPair = new Map<string, Counterparty>();

  for (const edge of web.edges) {
    const c = classify(edge, focalId);
    if (!c) continue;

    const rel: Relation = {
      type: edge.type,
      kind: c.kind,
      side: c.side,
      certainty: edge.certainty,
      source_url: edge.source_url,
      as_of: edge.as_of,
      terms: formatTerms(edge.attrs),
      raw: edge,
    };

    const key = pairKey(c.otherId, c.side);
    let cp = byPair.get(key);
    if (!cp) {
      const node = nodeById.get(c.otherId);
      cp = {
        id: c.otherId,
        name: node?.name ?? c.otherId,
        layer: node?.layer,
        side: c.side,
        kind: c.kind,
        relations: [],
        score: 0,
      };
      byPair.set(key, cp);
    }
    cp.relations.push(rel);
  }

  // Finalize: compute salience score and dominant kind per counterparty.
  for (const cp of byPair.values()) {
    let usdTotal = 0;
    let topUsd = -1;
    let topKind = cp.relations[0]?.kind ?? "related";
    for (const r of cp.relations) {
      const u = edgeUsd(r.raw.attrs);
      usdTotal += u;
      if (u > topUsd) {
        topUsd = u;
        topKind = r.kind;
      }
    }
    cp.kind = topKind;
    // usd salience dominates; when no usd, score is the relation count so the
    // count-desc tiebreak below still works via the same field.
    cp.score = usdTotal > 0 ? usdTotal : cp.relations.length;
    // Stable order of relations within a counterparty: by usd desc then type.
    cp.relations.sort((a, b) => {
      const ua = edgeUsd(a.raw.attrs);
      const ub = edgeUsd(b.raw.attrs);
      if (ub !== ua) return ub - ua;
      return a.type.localeCompare(b.type);
    });
  }

  const inputs: Counterparty[] = [];
  const outputs: Counterparty[] = [];
  for (const cp of byPair.values()) {
    (cp.side === "input" ? inputs : outputs).push(cp);
  }

  sortBySalience(inputs);
  sortBySalience(outputs);

  return {
    focal,
    inputs,
    outputs,
    counts: { inputs: inputs.length, outputs: outputs.length },
  };
}

// Sort by usd salience desc, then relation count desc, then name asc.
function sortBySalience(list: Counterparty[]): void {
  list.sort((a, b) => {
    const aUsd = hasUsd(a);
    const bUsd = hasUsd(b);
    if (aUsd && bUsd && a.score !== b.score) return b.score - a.score;
    if (aUsd !== bUsd) return aUsd ? -1 : 1; // priced pairs first
    if (a.relations.length !== b.relations.length)
      return b.relations.length - a.relations.length;
    return a.name.localeCompare(b.name);
  });
}

function hasUsd(cp: Counterparty): boolean {
  return cp.relations.some((r) => edgeUsd(r.raw.attrs) > 0);
}
