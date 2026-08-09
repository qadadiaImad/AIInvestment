"""Generate the 20-second Shorts cut as its own composition.

WHY ITS OWN COMPOSITION rather than a trim of the full episode: the short
is not an excerpt, it is a different edit with different lines. A trim of a
190-second explainer opens on a greeting and loses the viewer in a second
and a half.

THE HOOK CHANGED FROM THE DRAFT. The workflow opened on "Lehman didn't
break the market" with Rex answering "biggest bankruptcy ever". That
superlative is almost certainly true and I could not verify it this
session, and an unsourced superlative in the first two seconds of the most
widely seen asset is the worst possible place to put one. So the hook is
now the strongest thing that IS verified: the NASDAQ took until 23 April
2015 to regain its March 2000 peak. Fifteen years. That is a better hook
anyway - a number nobody expects beats a name everybody recognises.

  python scripts/bubbles/build_short.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "remotion/src/compositions/Bubbles.tsx"
DST = REPO / "remotion/src/compositions/BubblesShort.tsx"

FPS = 30
WPS = 2.25          # slower than raw speech: PERFORM tags add up to 1.3s a line
GAP = 10
TAIL = 52          # a beat of held image at the end so the loop can breathe

SOLO = {
    "SOL": '[{poses: ["%s"], kind: "full", x: 790, y: FLOOR_Y, h: 930}]',
    "REX": '[{poses: ["%s"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}]',
}
SOL_POSE = ["sol_point", "sol_finger", "sol_point_v1", "sol_smug_v1"]
REX_POSE = ["rex_eager", "rex_skeptic", "rex_listen", "rex_shock"]

from beats_v2 import SHORT as B


# ONE sting, and one only. 24s at the stingmap's cap of 3/minute buys 1.2,
# and a Shorts cut is exactly where the temptation is to spray the kit at
# it. s2 is the shock-take: a drawn single-exclamation reaction, which is
# the taxonomy entry that overrides reaction-silence (house rule 10.8 -
# a take with no anchored hit reads as static).
SFX = {"s2_rex_fifteen": ("vine_boom_hit", 0.26, 0)}


def sfx_for(stem: str) -> str:
    if stem not in SFX:
        return ""
    name, vol, at = SFX[stem]
    return '   sfx: [{at: %d, name: "%s", vol: %s}],\n' % (at, name, vol)


def dur(line: str) -> int:
    return max(40, int(round(len(line.split()) / WPS * FPS)) + 6)


def main() -> None:
    src = SRC.read_text("utf-8")
    at, out = 0, []
    for i, (spk, vo, line, kind, val, pose) in enumerate(B):
        poses = SOL_POSE if spk == "SOL" else REX_POSE
        key = ""
        if kind == "E":
            key = '   exhibit: "%s",\n' % val
        elif kind == "G":
            key = '   graphic: "%s",\n' % val
        k0, k1 = (1.0, 1.10) if i % 2 == 0 else (1.05, 1.14)
        out.append(
            "  {at: %d,\n%s%s   actors: %s,\n"
            "   shots: [{from: 0, k: %s, kEnd: %s}],\n"
            '   vo: "%s", speaker: "%s",\n   line: "%s"},'
            % (at, key, sfx_for(vo), SOLO[spk] % poses[pose % len(poses)],
               k0, k1, vo, spk, line.replace('"', '\\"')))
        at += dur(line) + GAP
    total = at + TAIL

    a = src.index("const BEATS: Beat[] = [")
    b = src.index("\n];", a)
    src = src[:a] + "const BEATS: Beat[] = [\n" + "\n\n".join(out) + src[b:]
    src = src.replace("BUBBLES_FRAMES", "BUBBLES_SHORT_FRAMES")
    src = src.replace("export const Bubbles:", "export const BubblesShort:")
    src = src.replace("audio/fairmarket_bubbles/", "audio/fairmarket_bshort/")
    src = src.replace("mouth_tracks_bubbles.json", "mouth_tracks_bshort.json")
    src = re.sub(r"export const BUBBLES_SHORT_FRAMES = \d+;.*",
                 "export const BUBBLES_SHORT_FRAMES = %d;   // %.1fs"
                 % (total, total / FPS), src, count=1)

    DST.write_text(src, "utf-8")
    print("%d beats, %d frames (%.1fs) -> %s"
          % (len(B), total, total / FPS, DST.name))
    for s, v, l, *_ in B:
        print("  %-16s %-4s %s" % (v, s, l))
    json.dump([dict(vo=v, speaker=s, line=l) for s, v, l, *_ in B],
              open(REPO / "data/bubbles/short_lines.json", "w"), indent=1)


if __name__ == "__main__":
    main()
