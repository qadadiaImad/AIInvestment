// Client-safe member-profile helpers (ideology + sponsored legislation).
//
// This module is intentionally free of any Node-only imports (e.g. node:fs) so
// it can be used from both Server and Client Components, mirroring lib/conflict.ts.
// lib/data.ts re-exports these for convenience.
//
// LEGAL/HONESTY: ideology here is a DW-NOMINATE first-dimension score from
// Voteview — a STATISTICAL MEASURE OF ROLL-CALL VOTING PATTERNS, not a personal
// judgment about any individual. The thresholds below mirror the Python
// implementation (scripts/aiinvest/member_profile.py) exactly so the labeled
// Lib↔Con axis the UI renders matches the data layer. Sponsored legislation is
// verbatim public record. Nothing here infers motive.

// Ideology block attached to a politician. `dim1`/`dim2` are DW-NOMINATE
// dimensions; `label` is the bucketed descriptor; `position` is dim1 mapped to
// a 0..1 Lib→Con axis position. Any field may be null when unmatched.
export interface Ideology {
  dim1: number | null;
  dim2: number | null;
  label: "Liberal" | "Moderate" | "Conservative" | null;
  position: number | null;
}

// One verbatim public-record sponsored bill.
export interface SponsoredBill {
  number: string;
  type: string;
  title: string;
  policy_area: string | null;
  introduced_date: string | null;
  latest_action: string | null;
}

// Summary of a member's sponsored legislation (public record). Present only
// when a congress.gov key was available at build time; otherwise null on the
// politician.
export interface SponsoredSummary {
  n: number;
  top_policy_areas: { area: string; n: number }[];
  recent: SponsoredBill[];
}

// Bucket a DW-NOMINATE 1st-dimension score into a descriptor. Mirrors the
// Python thresholds: < -0.25 → Liberal, > 0.25 → Conservative, between →
// Moderate, null/NaN → null.
export function ideologyLabel(
  dim1: number | null | undefined,
): "Liberal" | "Moderate" | "Conservative" | null {
  if (dim1 == null || Number.isNaN(dim1)) return null;
  if (dim1 < -0.25) return "Liberal";
  if (dim1 > 0.25) return "Conservative";
  return "Moderate";
}

// Map a DW-NOMINATE 1st-dimension score (~[-1, 1]) to a 0..1 axis position
// (0 = most liberal, 1 = most conservative): clamp((dim1 + 1) / 2, 0, 1).
export function ideologyPosition(
  dim1: number | null | undefined,
): number | null {
  if (dim1 == null || Number.isNaN(dim1)) return null;
  const pos = (dim1 + 1) / 2;
  if (pos < 0) return 0;
  if (pos > 1) return 1;
  return pos;
}
