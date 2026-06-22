// Client-safe news types + display helpers.
//
// This module is intentionally free of any Node-only imports (e.g. node:fs) so
// it can be used from both Server and Client Components. lib/data.ts re-exports
// these for convenience.
//
// LEGAL/HONESTY: every article carries a certainty label — filed / reported /
// rumored — and never launders a rumor into a fact. Graph-edge badges carry the
// CURATED edge's own certainty + source_url; certainty is NEVER upgraded from
// news. Candidate edges are ALWAYS unverified and are NEVER auto-added to the
// graph — they are a review queue for /map only.

// Certainty buckets, ordered weakest → strongest claim of verification.
export type Certainty = "filed" | "reported" | "rumored";

// A reference to a CURATED capital-web edge that a news article touches. The
// fields mirror the curated edge (src/dst/type/attrs/certainty/source_url/
// as_of) — the certainty is the edge's OWN curated certainty, not derived from
// the news article.
export interface GraphEdgeRef {
  src: string;
  dst: string;
  type: string;
  // attrs is heterogeneous: numbers (usd, pct, power_gw…), strings, null.
  attrs?: Record<string, number | string | null | undefined>;
  certainty?: string;
  source_url?: string;
  as_of?: string;
}

// A POSSIBLE new deal detected in news between two tagged entities for which NO
// curated edge yet exists. ALWAYS unverified; certainty is reported|rumored
// only. Never asserts a relationship — it is a candidate for /map review.
export interface CandidateEdge {
  src: string;
  dst: string;
  type_guess: string;
  evidence_title: string;
  certainty: "reported" | "rumored";
  url: string;
  detected_at: string;
  unverified: true;
}

export interface NewsArticle {
  title: string;
  url: string;
  source: string;
  published: string | null;
  summary?: string | null;
  tickers: string[];
  certainty: Certainty | string;
  retrieved_at: string;
  source_class: "news-api" | "news-rss" | string;
  graph_edges?: GraphEdgeRef[];
  candidate_edges?: CandidateEdge[];
}

export interface NewsData {
  generated_at: string;
  key_mode: "finnhub" | "yahoo" | string;
  source_class: "news-api" | "news-rss" | string;
  n_tickers_requested: number;
  n_tickers_covered: number;
  n_articles: number;
  http_failed: string[];
  disclaimer: string;
  window_days: number;
  articles: NewsArticle[];
  candidate_edges: CandidateEdge[];
}

// Visual + label metadata for a certainty bucket. Colors echo the terminal
// palette used elsewhere (sky/amber/zinc). `filed` = strongest (sourced from a
// filing), `reported` = a news outlet reported it, `rumored` = weakest.
export interface CertaintyMeta {
  label: string;
  // Tailwind classes for a small chip (text + border + bg).
  chipCls: string;
  // Short human description for tooltips.
  note: string;
}

const CERTAINTY_META: Record<Certainty, CertaintyMeta> = {
  filed: {
    label: "FILED",
    chipCls: "text-sky-300 border-sky-500/50 bg-sky-500/10",
    note: "Sourced from an official filing or disclosure.",
  },
  reported: {
    label: "REPORTED",
    chipCls: "text-emerald-300 border-emerald-500/50 bg-emerald-500/10",
    note: "Reported by a news outlet — not independently verified here.",
  },
  rumored: {
    label: "RUMORED",
    chipCls: "text-amber-300 border-amber-500/50 bg-amber-500/10",
    note: "Rumored / unconfirmed — treat as speculation, not fact.",
  },
};

const CERTAINTY_FALLBACK: CertaintyMeta = {
  label: "UNLABELED",
  chipCls: "text-zinc-400 border-zinc-600 bg-zinc-700/20",
  note: "No certainty label — treat with caution.",
};

export function certaintyMeta(c: Certainty | string | null | undefined): CertaintyMeta {
  if (c && Object.prototype.hasOwnProperty.call(CERTAINTY_META, c)) {
    return CERTAINTY_META[c as Certainty];
  }
  return CERTAINTY_FALLBACK;
}

// Human-readable badge for a curated graph edge that a news item touches, e.g.
// "compute_commitment · $40B · reported". Deal terms are pulled from the edge's
// own attrs (usd / pct / power_gw) and the certainty is the edge's OWN curated
// certainty — never upgraded from news.
export function edgeBadge(ref: GraphEdgeRef): string {
  const parts: string[] = [];
  parts.push(ref.type);
  const terms = edgeTerms(ref);
  if (terms) parts.push(terms);
  if (ref.certainty) parts.push(ref.certainty);
  return parts.join(" · ");
}

// Format the deal terms from an edge's attrs into a compact string (e.g.
// "$40B", "10%", "1.2 GW"). Returns "" when no recognized term is present.
export function edgeTerms(ref: GraphEdgeRef): string {
  const a = ref.attrs;
  if (!a) return "";
  const bits: string[] = [];
  const usdVal = a.usd;
  if (typeof usdVal === "number" && Number.isFinite(usdVal)) {
    bits.push(usdCompact(usdVal));
  }
  const pctVal = a.pct;
  if (typeof pctVal === "number" && Number.isFinite(pctVal)) {
    bits.push(`${pctVal}%`);
  }
  const gwVal = a.power_gw;
  if (typeof gwVal === "number" && Number.isFinite(gwVal)) {
    bits.push(`${gwVal} GW`);
  }
  return bits.join(" · ");
}

// Compact USD formatter (self-contained so this module stays client-safe and
// free of cross-module coupling; mirrors lib/format.usd).
function usdCompact(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(1)}K`;
  return `$${v.toFixed(0)}`;
}
