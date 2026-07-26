"""Check a generated parts sheet has proportions that can actually assemble.

This exists because a parts sheet was rigged without checking, and the pieces
did not fit each other: the hand came out 98% as long as the forearm (a hand is
about a third of a forearm), and the upper arm was 1.6x the forearm instead of
roughly matching it. Rigged, that reads as detached floating hands and wrong-
looking arms — which is exactly what it looked like.

The generator draws each piece independently with no constraint between them,
so nothing forces them into a consistent body. This is the gate: run it BEFORE
rigging, and regenerate if it fails.

Usage:
    python scripts/meme_reel/validate_parts.py remotion/public/meme_reel/char2/manifest_PARTS.json
"""
import json
import sys

# (name, expression, expected, tolerance, why)
# Ratios are of ink HEIGHT unless the name says width.
CHECKS = [
    ("upper arm : forearm", lambda d: d["forearm"]["h"] / d["upper_arm"]["h"], 0.85, 0.18,
     "the forearm is close to the upper arm in length; a short forearm reads as a broken elbow"),
    ("hand : forearm", lambda d: d["hand"]["h"] / d["forearm"]["h"], 0.38, 0.16,
     "a hand is roughly a third of a forearm; anything near 1.0 reads as a detached blob"),
    ("thigh : shin", lambda d: d["shin"]["h"] / d["thigh"]["h"], 0.92, 0.16,
     "thigh and shin are close in length"),
    ("thigh width : torso width", lambda d: d["thigh"]["w"] / d["torso"]["w"], 0.42, 0.14,
     "a thigh much wider than half the torso reads as a slab, and two of them merge"),
    ("head : torso", lambda d: d["head"]["h"] / d["torso"]["h"], 0.95, 0.30,
     "cartoon head is large but not larger than the whole torso"),
    ("leg : arm", lambda d: (d["thigh"]["h"] + d["shin"]["h"]) / (d["upper_arm"]["h"] + d["forearm"]["h"]), 1.25, 0.35,
     "legs are longer than arms, but not by more than about half again"),
]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    man = json.load(open(sys.argv[1], encoding="utf-8"))
    d = {p["name"]: p for p in man["parts"]}

    missing = [n for n in ("head", "torso", "upper_arm", "forearm", "hand", "thigh", "shin")
               if n not in d]
    if missing:
        print(f"MISSING PARTS: {', '.join(missing)}")
        return 1

    print(f"\nparts sheet: {man.get('source', sys.argv[1])}\n")
    fails = 0
    for name, fn, want, tol, why in CHECKS:
        got = fn(d)
        ok = abs(got - want) <= tol
        if not ok:
            fails += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<26} {got:5.2f}   want {want:.2f} +-{tol:.2f}")
        if not ok:
            print(f"        -> {why}")

    print()
    if fails:
        print(f"  {fails} PROPORTION FAILURE(S) — regenerate the sheet, do not rig it.\n")
    else:
        print("  PASS — the pieces can assemble into a consistent body.\n")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
