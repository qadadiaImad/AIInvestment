"""Generate the curated halal business-activity seed file.

APPROVED PLAN ADAPTATION (deviation from original plan): instead of hand-embedding
the DETAILED dict in this script, the generator READS the evidence pack produced by
the 2026-07-21 research fleet (data/halal/evidence_pack_2026-07-21.json, gitignored)
and merges those entries over the clean-default universe. This keeps the seed
reviewable and regenerable without embedding ~782 lines of evidence JSON inline.

OUTPUT: scripts/aiinvest/data/halal/business_activity.json (~128 entries), committed.

CLEAN-UP APPLIED: double-escaped sequences in INTU and APP note fields are
normalised to plain text before writing:
  - backslash-quote (\\") -> plain quote (")
  - double-backslash (\\\\) -> single backslash (\\)

Non-clean entries carry evidence (quote + source_url) enforced by
halal.validate_business_activity, which gates the output.

Educational/research only. Not investment or religious advice.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_PACK = _REPO / "data" / "halal" / "evidence_pack_2026-07-21.json"
_OUT = pathlib.Path(__file__).resolve().parent / "aiinvest" / "data" / "halal" / "business_activity.json"

REVIEWED = "2026-07-21"


def _normalize_escapes(text: str) -> str:
    """Collapse double-escaped sequences left by the research agent into plain text.

    The evidence pack was written by an agent that over-escaped strings in two fields:
    - INTU note: backslash-quote (\\\") -> plain double-quote
    - APP note: double-backslash (\\\\) in Windows path segments -> single backslash

    We process in order (double-backslash first to avoid collision with the
    backslash-quote pass).
    """
    if text is None:
        return text
    # Double backslash -> single backslash
    text = text.replace("\\\\", "\\")
    # Backslash-quote -> plain quote
    text = text.replace('\\"', '"')
    return text


def _clean_entry(e: dict) -> dict:
    """Return a copy of e with normalised note field."""
    out = dict(e)
    if out.get("note"):
        out["note"] = _normalize_escapes(out["note"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate business_activity.json from the evidence pack.")
    ap.add_argument(
        "--pack",
        default=str(_DEFAULT_PACK),
        help="Path to the evidence pack JSON (default: data/halal/evidence_pack_2026-07-21.json).",
    )
    ap.add_argument(
        "--out",
        default=str(_OUT),
        help="Output path (default: scripts/aiinvest/data/halal/business_activity.json).",
    )
    args = ap.parse_args(argv)

    # --- imports here so this script can be run from the scripts/ dir ---
    from aiinvest import ai_stack, halal, quantum_stack  # noqa: PLC0415

    pack_path = pathlib.Path(args.pack)
    if not pack_path.exists():
        print(f"ERROR: evidence pack not found at {pack_path}")
        print("  Run the research fleet to regenerate it, or pass --pack <path>.")
        return 1

    # Load and index the evidence pack by ticker
    pack_raw = json.loads(pack_path.read_text(encoding="utf-8"))
    pack = {e["ticker"]: _clean_entry(e) for e in pack_raw}

    # Build the full universe (AI + Quantum, bare symbols, sorted, de-duped)
    universe = sorted({t.split(":")[-1] for t in
                       ai_stack.all_tickers() + quantum_stack.all_tickers()})

    # Merge: evidence-pack entries override the clean default for non-clean names
    entries = []
    for sym in universe:
        if sym in pack:
            e = pack[sym]
            # Ensure required fields are present
            e.setdefault("last_reviewed", REVIEWED)
            e["ticker"] = sym
            entries.append(e)
        else:
            # Default: clean with no evidence required
            entries.append({
                "ticker": sym,
                "status": "clean",
                "categories": [],
                "impermissible_revenue_pct": None,
                "evidence": None,
                "methodology_notes": {},
                "note": None,
                "confidence": "high",
                "last_reviewed": REVIEWED,
            })

    # Validate before writing
    entry_dict = {e["ticker"]: e for e in entries}
    problems = halal.validate_business_activity(entry_dict, universe)
    if problems:
        print(f"VALIDATION ERRORS ({len(problems)}) — NOT writing output:")
        for p in problems:
            print(f"  - {p}")
        return 1

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    counts: dict[str, int] = {}
    for e in entries:
        counts[e["status"]] = counts.get(e["status"], 0) + 1

    print(f"Wrote {out_path} ({len(entries)} entries)")
    print(f"  breakdown: {counts}")
    print("  problems: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
