// Client-safe halal screening types + display helpers.
//
// This module is intentionally free of any Node-only imports (e.g. node:fs) so
// it can be used from both Server and Client Components. lib/data.ts re-exports
// these for convenience and adds the server-side getHalalData() loader.

export type HalalOverall =
  | "halal"
  | "not_halal"
  | "questionable"
  | "insufficient_data";

export type HalalTestStatus = "pass" | "fail" | "unknown";

export interface HalalTestResult {
  id: string;
  label: string;
  numerator_value: number | null;
  denominator_value: number | null;
  ratio: number | null;
  threshold: number;
  margin: number | null;
  status: HalalTestStatus;
  citation: string;
}

export interface HalalStandardResult {
  key: string;
  name: string;
  status: HalalTestStatus;
  tests: HalalTestResult[];
  activity_status: HalalTestStatus | "unknown";
  activity_threshold_pct: number;
  activity_citation: string;
}

export interface HalalBusiness {
  status: string;
  categories?: string[];
  impermissible_revenue_pct?: { value: number | null; basis?: string } | null;
  evidence?: {
    quote: string;
    source_url: string;
    retrieved_at: string;
  } | null;
  methodology_notes?: Record<string, { stance: string; reason: string }>;
  note?: string | null;
  confidence?: string;
  last_reviewed?: string;
}

export interface HalalPurification {
  per_share: number | null;
  status: "computed" | "insufficient_data";
  missing: string | null;
  basis: string | null;
}

export interface HalalVerdict {
  symbol: string;
  layer: string | null;
  overall: HalalOverall;
  overall_basis: string;
  standards: Record<string, HalalStandardResult>;
  business: HalalBusiness;
  purification: HalalPurification;
  inputs_asof: string | null;
}

export interface HalalData {
  generated_at: string;
  disclaimer: string;
  methodology_note: string;
  conventions: string[];
  verdicts: Record<string, HalalVerdict>;
}

// Display helpers (unit-tested in halal.test.ts):

export function overallLabel(o: HalalOverall): string {
  return {
    halal: "Halal",
    not_halal: "Not halal",
    questionable: "Questionable",
    insufficient_data: "Insufficient data",
  }[o];
}

export function overallTone(
  o: HalalOverall,
): "pass" | "fail" | "warn" | "muted" {
  return {
    halal: "pass",
    not_halal: "fail",
    questionable: "warn",
    insufficient_data: "muted",
  }[o] as "pass" | "fail" | "warn" | "muted";
}

export function fmtRatioPct(r: number | null): string {
  if (r === null || r === undefined || Number.isNaN(r)) return "—";
  return `${(r * 100).toFixed(2)}%`;
}

/**
 * Compute the total purification amount for a holder.
 *
 * @param perShare - Purification amount per share (from HalalVerdict.purification.per_share).
 *                   null → insufficient data; propagate null.
 * @param shares   - Number of shares held. Must be > 0; otherwise null.
 * @returns Total purification amount, or null when inputs are missing/invalid.
 */
export function purificationAmount(
  perShare: number | null,
  shares: number,
): number | null {
  if (perShare === null) return null;
  if (shares <= 0) return null;
  return perShare * shares;
}
