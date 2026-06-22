// Client-safe correlational committee-overlap signal helpers.
//
// This module is intentionally free of any Node-only imports (e.g. node:fs) so
// it can be used from both Server and Client Components. lib/data.ts re-exports
// these for convenience.
//
// LEGAL/HONESTY: the signal is STRICTLY correlational. It states only two
// verifiable facts joined by a stated heuristic: (1) the member factually
// serves on the committee(s), and (2) the traded stock is in the sector, where
// the committee has a curated/approximate jurisdiction over that sector.
// `certainty` is hard-coded to "correlational" — no other value is permitted.
// Causal or accusatory framing is banned everywhere.

export interface ConflictSignal {
  certainty: "correlational";
  sector: string;
  committees: string[];
  rationale: string;
}

// Required rationale template — a signal's rationale MUST equal this exact
// string (with {committee}/{sector} filled in). `committee` is the
// human-joined committee list.
export function expectedConflictRationale(
  committee: string,
  sector: string,
): string {
  return (
    `Serves on the ${committee} Committee, which has jurisdiction over the ` +
    `${sector} sector. This is a correlational overlap only — not evidence ` +
    `of wrongdoing, insider trading, or any improper conduct.`
  );
}

// Validator: returns true only for a well-formed, strictly-correlational
// signal whose rationale matches the required template. Any deviation (wrong
// certainty, missing fields, altered phrasing) is rejected so accusatory or
// causal language can never reach the UI.
export function isValidConflictSignal(
  sig: ConflictSignal | null | undefined,
): sig is ConflictSignal {
  if (!sig) return false;
  if (sig.certainty !== "correlational") return false;
  if (!sig.sector || typeof sig.sector !== "string") return false;
  if (!Array.isArray(sig.committees) || sig.committees.length === 0)
    return false;
  if (sig.committees.some((c) => !c || typeof c !== "string")) return false;
  if (!sig.rationale || typeof sig.rationale !== "string") return false;
  const expected = expectedConflictRationale(
    sig.committees.join(", "),
    sig.sector,
  );
  return sig.rationale === expected;
}
