"""Measure the episode against explicit pacing thresholds.

The Kurzgesagt-style reference in .claude/skills/educational-video-creator
states numbers rather than vibes: no more than ~3s without a visual
change, scenes 3-8s, and 0.3-1.0s of TRANSITION between segments. This
reports where we sit against those, so "it does not feel fluid" becomes a
measurement instead of an opinion.

Usage:  python -m vector.pacing_audit
"""
from __future__ import annotations

FPS = 30

# (beat start, [shot offsets], label) — mirrors BEATS in FairMarketEp1.tsx
BEATS = [
    (0,    [0, 56],              "SOL intro"),
    (110,  [0, 60],              "REX fundamentals"),
    (195,  [0],                  "SOL HA!"),
    (255,  [0, 30, 74],          "SOL politics (2-shot)"),
    (345,  [0],                  "REX WHAT?!"),
    (400,  [0, 58, 88, 138, 171, 190], "SOL exhibit"),
    (640,  [0, 47],              "REX index"),
    (740,  [0, 64, 119],         "SOL legal"),
    (895,  [0, 54],              "A2 REX copy"),
    (995,  [0, 46],              "A2 SOL six weeks"),
    (1090, [0],                  "A2 REX six weeks?"),
    (1145, [0, 62, 118, 152],    "A2 SOL edge"),
    (1340, [0],                  "A2 REX useless"),
    (1410, [0, 58, 120],         "A2 SOL map"),
    (1565, [0, 50],              "closer"),
    (1685, [0],                  "outro"),
]
END = 1800

# thresholds from references/script-and-narration.md
MAX_STATIC_S = 3.0
SCENE_MIN_S, SCENE_MAX_S = 3.0, 8.0
TRANSITION_S = (0.3, 1.0)


def main() -> None:
    shots = []
    for i, (at, offs, label) in enumerate(BEATS):
        nxt = BEATS[i + 1][0] if i + 1 < len(BEATS) else END
        for j, o in enumerate(offs):
            start = at + o
            end = at + offs[j + 1] if j + 1 < len(offs) else nxt
            shots.append((start, end - start, label, j == 0))

    print(f"{'shot':>4} {'start':>6} {'len_s':>6}  beat")
    long_holds = []
    for k, (start, dur, label, is_first) in enumerate(shots, 1):
        s = dur / FPS
        flag = ""
        if s > MAX_STATIC_S:
            flag = "  <-- over 3s single framing"
            long_holds.append((k, label, s))
        print(f"{k:>4} {start:>6} {s:>6.2f}  {label}{flag}")

    total_s = END / FPS
    n = len(shots)
    print(f"\n{n} shots in {total_s:.1f}s -> one cut every {total_s / n:.2f}s")
    print(f"beats: {len(BEATS)} -> one beat every {total_s / len(BEATS):.2f}s")

    print(f"\nHOLDS over {MAX_STATIC_S}s in a single framing: {len(long_holds)}")
    for k, label, s in long_holds:
        print(f"  shot {k:>2}  {s:.2f}s  {label}")

    cuts = n - 1
    print(f"\nTRANSITIONS: {cuts} cuts, ALL hard cuts (0.00s).")
    print(f"  reference range for a segment change: "
          f"{TRANSITION_S[0]}-{TRANSITION_S[1]}s")
    print(f"  time currently spent transitioning: 0.0s of {total_s:.1f}s (0%)")
    print("\nNote the shape of the problem: our cut RATE is fast "
          f"({total_s / n:.2f}s/shot, faster than the 3-8s reference scene), "
          "but every cut is instantaneous and nothing carries across it. "
          "Cutting more often with less continuity is what reads as choppy "
          "rather than fluid.")


if __name__ == "__main__":
    main()
