// Client-side macro-stress recompute for the AI capital web.
//
// Mirrors scripts/aiinvest/macro_stress.py (betas, channels, weights) closely
// enough to give the same ORDINAL signal. This is an *illustrative* recompute:
// the sliders supply deltas (Δ basis points on rates, Δ% on electricity) on top
// of the current macro snapshot — it is NOT a dollar-loss estimate.
//
// Pure functions only — no I/O, safe to run in the browser on every slider tick.
//
// Educational / research only — not investment advice.

import type { GraphEdge } from "@/lib/data";

// ---- Constants (mirrors macro_stress.py) ----

const NEOCLOUD = new Set(["CRWV", "NBIS", "IREN"]);
const HYPERSCALER = new Set(["MSFT", "AMZN", "GOOGL", "META"]);

export const CERTAINTY_W: Record<string, number> = {
  filed: 1.0,
  reported: 0.7,
  rumored: 0.3,
};

export const TYPE_BASE: Record<string, number> = {
  compute_commitment: 3.0,
  equity_stake: 2.0,
  voting_power: 2.0,
  subsidiary: 2.0,
  customer: 1.0,
  infra_partner: 1.0,
};

const ELEC_GAMMA = 0.15;
const DFF_REGIME_THRESHOLD = 5.5;
const RUMORED_DISCOUNT = 0.15;

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

// Rate-channel beta per +100 bps. compute_commitment splits by src class.
export function beta(edge: Pick<GraphEdge, "type" | "src">): number {
  if (edge.type === "compute_commitment") {
    if (NEOCLOUD.has(edge.src)) return 0.12;
    if (HYPERSCALER.has(edge.src)) return 0.03;
    return 0.06;
  }
  switch (edge.type) {
    case "equity_stake":
      return 0.08;
    case "customer":
      return 0.02;
    case "infra_partner":
      return 0.01;
    case "voting_power":
    case "subsidiary":
      return 0.0;
    default:
      return 0.0;
  }
}

function terminationDays(edge: GraphEdge): number | null {
  const v = edge.attrs?.termination_days;
  return typeof v === "number" ? v : null;
}

/**
 * Per-edge stress score in [0, 1] for coloring purposes.
 *
 * @param edge       graph edge (src, dst, type, certainty, attrs)
 * @param dRateBps   rate shock, Δ basis points on top of snapshot (0…+300)
 * @param dElecPct   electricity shock, Δ percent on top of snapshot (0…+50, so 30 ⇒ +30%)
 * @param dstLayer   layer of the destination node (e.g. "L2-infra")
 * @param srcLayer   layer of the source node (e.g. "L0-energy")
 * @param dffBase    baseline Fed-funds rate (snapshot dff) for the regime trigger
 *
 * 1.0 = unstressed (green) … 0.0 = fully stressed (red).
 */
export function edgeStress(
  edge: GraphEdge,
  dRateBps: number,
  dElecPct: number,
  dstLayer: string | undefined,
  srcLayer: string | undefined,
  dffBase: number,
): number {
  const b = beta(edge);

  // Channel 1 — rates. Only edge types with a positive beta react.
  let s = b > 0 ? Math.max(0, 1 - (b * dRateBps) / 100) : 1;

  // Termination amplifier: shorter lock-in → the stressed portion is amplified.
  const term = terminationDays(edge);
  if (term !== null && b > 0) {
    const amp = term <= 90 ? 1.5 : term <= 180 ? 1.2 : 1.0;
    if (amp > 1.0) s = 1 - (1 - s) * amp;
  }

  // Channel 2 — electricity. dElecPct is a percent (30 ⇒ fraction 0.30).
  const elecFrac = dElecPct / 100;
  if (srcLayer === "L0-energy") {
    // Energy producers benefit from higher prices; clamp to 1 for coloring
    // (no green-er than unstressed).
    const boost = Math.min(1, 1 + ELEC_GAMMA * elecFrac);
    s = Math.max(s, boost);
  } else if (dstLayer === "L2-infra") {
    // Datacenter / infra operators are squeezed by higher electricity prices.
    const factor = Math.max(0, 1 - ELEC_GAMMA * elecFrac);
    s = Math.min(1, s * factor);
  }

  // Channel 3 — rate-regime trigger: at elevated absolute rates, rumored deals
  // get an extra haircut.
  if (dffBase + dRateBps / 100 >= DFF_REGIME_THRESHOLD && edge.certainty === "rumored") {
    s -= RUMORED_DISCOUNT;
  }

  return clamp(s, 0, 1);
}

/** Base (pre-stress) weight for an edge: certainty_w × type_base. */
export function baseWeight(edge: Pick<GraphEdge, "type" | "certainty">): number {
  const cw = CERTAINTY_W[edge.certainty ?? "reported"] ?? 0.5;
  const tb = TYPE_BASE[edge.type] ?? 1.0;
  return cw * tb;
}

export interface StressInputs {
  dRateBps: number;
  dElecPct: number;
  dffBase: number;
  /** node id → layer */
  layerById: Map<string, string | undefined>;
}

/** Compute the stress score for one edge given shared inputs. */
export function scoreEdge(edge: GraphEdge, inp: StressInputs): number {
  return edgeStress(
    edge,
    inp.dRateBps,
    inp.dElecPct,
    inp.layerById.get(edge.dst),
    inp.layerById.get(edge.src),
    inp.dffBase,
  );
}

/**
 * Network Stress Index, reported 0–100.
 *
 * index = (1 − weightedMean(stress, baseWeight)) × 100
 *
 * 0 = no stress (all edges at 1.0); 100 = fully stressed. Returns 0 when there
 * are no edges / zero total weight.
 */
export function networkStressIndex(
  edges: GraphEdge[],
  inp: StressInputs,
): number {
  let wsum = 0;
  let wstress = 0;
  for (const e of edges) {
    const w = baseWeight(e);
    wsum += w;
    wstress += w * scoreEdge(e, inp);
  }
  if (wsum === 0) return 0;
  const weightedMean = wstress / wsum;
  return clamp((1 - weightedMean) * 100, 0, 100);
}

// ---- Color ramp: green (#10b981) at 1.0 → amber → red (#ef4444) at 0 ----

function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
}

function rgbToHex(r: number, g: number, b: number): string {
  const c = (n: number) =>
    Math.round(clamp(n, 0, 255)).toString(16).padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function mix(c1: string, c2: string, t: number): string {
  const [r1, g1, b1] = hexToRgb(c1);
  const [r2, g2, b2] = hexToRgb(c2);
  return rgbToHex(lerp(r1, r2, t), lerp(g1, g2, t), lerp(b1, b2, t));
}

const STRESS_GREEN = "#10b981";
const STRESS_AMBER = "#f59e0b";
const STRESS_RED = "#ef4444";

/**
 * Map a stress score in [0,1] to a color.
 * 1.0 → green, 0.5 → amber, 0.0 → red. Values are clamped.
 */
export function stressColor(score: number): string {
  const s = clamp(score, 0, 1);
  if (s >= 0.5) {
    // green ↔ amber over [1.0, 0.5]
    const t = (1 - s) / 0.5; // 0 at s=1, 1 at s=0.5
    return mix(STRESS_GREEN, STRESS_AMBER, t);
  }
  // amber ↔ red over [0.5, 0.0]
  const t = (0.5 - s) / 0.5; // 0 at s=0.5, 1 at s=0
  return mix(STRESS_AMBER, STRESS_RED, t);
}

/** Build a node-id → layer map from capital_web nodes. */
export function buildLayerMap(
  nodes: { id: string; layer?: string }[],
): Map<string, string | undefined> {
  const m = new Map<string, string | undefined>();
  for (const n of nodes) m.set(n.id, n.layer);
  return m;
}
