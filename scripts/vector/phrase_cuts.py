"""Find cut points inside a beat from the VO itself.

A cut lands cleanly on a breath, not mid-word. mouth_tracks.json already
carries a per-frame speech amplitude (0 = silence) for every line, so the
pauses are already measured — this reports the silent gaps in each beat's
track as candidate cut frames, in absolute composition frames.
"""
from __future__ import annotations

import json

from vector.visemes_ep1 import FIX

VO_DELAY = 6
# (beat start, vo key, beat length in frames, label)
BEATS = [
    (0,   "v1_sol_intro",        110, "SOL intro"),
    (110, "v2_rex_fundamentals",  85, "REX fundamentals"),
    (195, "v3_sol_ha",            60, "SOL HA!"),
    (255, "v4_sol_politics",      90, "SOL politics"),
    (345, "v5_rex_what",          55, "REX WHAT?!"),
    (400, "v6_sol_exhibit",      240, "SOL exhibit"),
    (640, "v7_rex_index",        100, "REX an INDEX?!"),
    (740, "v8_sol_legal",        155, "SOL all legal"),
    (895, "v9_rex_filings",      120, "REX filings"),
]


def gaps(track: list[int], min_len: int = 4) -> list[tuple[int, int]]:
    """Runs of silence (value 0) at least min_len frames long."""
    out, start = [], None
    for i, v in enumerate(track):
        if v == 0 and start is None:
            start = i
        elif v != 0 and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    if start is not None and len(track) - start >= min_len:
        out.append((start, len(track)))
    return out


def main() -> None:
    tracks = json.loads((FIX / "mouth_tracks.json").read_text("utf-8"))
    for at, key, length, label in BEATS:
        t = tracks[key]
        secs = length / 30
        print(f"\n{label}  (beat {at}, {length}f = {secs:.1f}s, "
              f"vo {len(t)}f)")
        found = []
        for g0, g1 in gaps(t):
            # mid-gap, in absolute composition frames
            cut = at + VO_DELAY + (g0 + g1) // 2
            if at + 12 < cut < at + length - 12:
                found.append(cut)
                print(f"   pause {g0:3d}-{g1:3d} -> cut at frame {cut}"
                      f"  (+{(cut - at) / 30:.1f}s into beat)")
        if not found:
            print("   (no interior pause long enough)")
        if secs >= 4:
            print(f"   ** {secs:.1f}s hold: needs "
                  f"{max(1, int(secs // 2))} extra shot(s)")


if __name__ == "__main__":
    main()
