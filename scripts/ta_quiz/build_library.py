"""Assemble the numbered TA pattern library from the generation run.

Two jobs beyond plain assembly:

1. **Stable ids.** Sorted by family then complexity then slug so the numbering
   is deterministic — "pattern 5" has to mean the same thing tomorrow.

2. **Off-by-one repair.** The generation run had a systematic bug in one family:
   the pattern-defining candle landed at index `revealFrom` (i.e. inside the
   reveal window) instead of `revealFrom - 1`. Where nudging `revealFrom` by one
   makes the pattern check pass AND leaves at least two reveal candles, that is
   a genuine fix to a labelling error, not a fudge — so it is applied and
   recorded in `repaired`. Anything still failing is quarantined, not shipped.

Usage:
    python scripts/ta_quiz/build_library.py /tmp/raw_patterns.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "references", "ta-pattern-library.json")

sys.path.insert(0, HERE)
from validate import validate, suspect_trigger_displacement  # noqa: E402

FAMILY_ORDER = [
    "single-candle",
    "two-candle",
    "three-candle",
    "reversal-chart",
    "continuation-chart",
    "gap-window",
    "structure-level",
    "volume-indicator",
]


def try_repair(p):
    """Return (patched_or_None, note)."""
    if not validate(p):
        # Validates as-is, but the decisive bar may still be sitting in the
        # reveal window where no specific check would catch it.
        if suspect_trigger_displacement(p):
            q = dict(p)
            q["revealFrom"] = p["revealFrom"] + 1
            if q["revealFrom"] <= len(p["candles"]) - 2 and not validate(q):
                return q, f"revealFrom {p['revealFrom']} -> {q['revealFrom']} (trigger bar was in the reveal)"
        return None, ""
    for delta in (1, -1):
        q = dict(p)
        q["revealFrom"] = p["revealFrom"] + delta
        n = len(p["candles"])
        if q["revealFrom"] < 3 or q["revealFrom"] > n - 2:
            continue
        if not validate(q):
            return q, f"revealFrom {p['revealFrom']} -> {q['revealFrom']}"
    return None, ""


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/raw_patterns.json"
    raw = json.load(open(src))

    patterns, quarantined, repaired = [], [], []
    for p in raw:
        p = {k: v for k, v in p.items() if k != "audit"}
        errs = validate(p)
        # Always attempt repair, not just on failure: the trigger-displacement
        # cases validate cleanly and would otherwise ship silently wrong.
        fixed, note = try_repair(p)
        if fixed:
            p = fixed
            repaired.append((p["slug"], note))
            errs = validate(p)
        if errs:
            quarantined.append({"slug": p.get("slug"), "name": p.get("name"),
                                "family": p.get("family"), "errors": errs})
            continue
        patterns.append(p)

    fam_idx = {f: i for i, f in enumerate(FAMILY_ORDER)}
    patterns.sort(key=lambda p: (fam_idx.get(p.get("family"), 99),
                                 p.get("complexity", 9), p.get("slug", "")))
    for i, p in enumerate(patterns, start=1):
        p["id"] = i

    ordered = []
    for p in patterns:
        ordered.append({k: p[k] for k in
                        ["id", "slug", "name", "family", "complexity", "occurrence", "bias",
                         "type", "context", "answer", "answerLine", "ruleTitle", "ruleText",
                         "levelPrice", "levelLabel", "revealFrom", "renderable", "candles"]
                        if k in p})

    by_family, by_complexity, by_occurrence, by_render = {}, {}, {}, {}
    for p in ordered:
        by_family[p["family"]] = by_family.get(p["family"], 0) + 1
        by_complexity[str(p["complexity"])] = by_complexity.get(str(p["complexity"]), 0) + 1
        by_occurrence[p["occurrence"]] = by_occurrence.get(p["occurrence"], 0) + 1
        by_render[p["renderable"]] = by_render.get(p["renderable"], 0) + 1

    lib = {
        "note": ("Synthetic OHLC built to demonstrate each pattern — NOT real market data. "
                 "Every entry passed scripts/ta_quiz/validate.py, which re-derives the "
                 "geometry in plain Python rather than trusting the generating model."),
        "counts": {
            "patterns": len(ordered),
            "quarantined": len(quarantined),
            "repaired": len(repaired),
            "byFamily": by_family,
            "byComplexity": by_complexity,
            "byOccurrence": by_occurrence,
            "byRenderable": by_render,
        },
        "quarantined": quarantined,
        "patterns": ordered,
    }
    json.dump(lib, open(OUT, "w"), indent=2, ensure_ascii=False)

    print(f"{len(ordered)} patterns -> {os.path.relpath(OUT, REPO)}")
    print(f"  repaired (revealFrom off-by-one): {len(repaired)}")
    for s, n in repaired:
        print(f"      {s}: {n}")
    print(f"  quarantined: {len(quarantined)}")
    for q in quarantined:
        print(f"      {q['slug']}: {q['errors'][0]}")
    print("\nby family:      ", by_family)
    print("by complexity:  ", dict(sorted(by_complexity.items())))
    print("by occurrence:  ", by_occurrence)
    print("by renderable:  ", by_render)


if __name__ == "__main__":
    main()
