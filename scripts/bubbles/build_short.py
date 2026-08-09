"""Generate the Shorts cut as its own composition.

WHY ITS OWN COMPOSITION rather than a trim of the full episode: the short
is not an excerpt, it is a different edit with different lines. A trim of a
170-second explainer opens on a greeting and loses the viewer in a second
and a half.

V2, and it is longer on purpose. The owner: "short needs to be enhanced ...
stack more information and maybe speed up prononciation". v1 was 7 beats
carrying two ideas in 24s. This is 13 beats carrying FIVE verified figures
in ~35s, spoken 1.30x faster. The trade is deliberate and worth saying out
loud: it is half again as long, for two and a half times the content and a
faster read. Still well inside what Shorts accepts.

Every number is a facts.json slot. The beat list and the reasoning behind
its ordering live in beats_v2.SHORT.

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
GAP = 0             # folded into the per-beat hold below
TAIL = 52          # a beat of held image at the end so the loop can breathe

SOLO = {
    "SOL": '[{poses: ["%s"], kind: "full", x: 790, y: FLOOR_Y, h: 930}]',
    "REX": '[{poses: ["%s"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}]',
}
SOL_POSE = ["sol_point", "sol_finger", "sol_point_v1", "sol_smug_v1"]
REX_POSE = ["rex_eager", "rex_skeptic", "rex_listen", "rex_shock"]

from beats_v2 import SHORT as B


# ONE sting, and one only. ~25s at the stingmap's cap of 3/minute buys 1.2,
# and a Shorts cut is exactly where the temptation is to spray the kit at it.
#
# v1 put it on the shock-take, but v2 has no single-exclamation take to hang
# it on - and a sting keyed to a stem that no longer exists is silently
# nothing, which is precisely how this episode once shipped with none at
# all. So it moves to the taxonomy's `thesis-lands`: "No villain. Just a
# machine. Four parts." is the turn the whole cut exists to reach, and core
# is the sound the map reserves for exactly that.
SFX = {"s5_sol_novillain": ("core", 0.30, "after")}
VO_DIR = REPO / "remotion/public/audio/fairmarket_bshort"


def vo_frames(stem: str) -> int:
    import wave
    p = VO_DIR / (stem + ".wav")
    if not p.exists():
        return 0
    with wave.open(str(p)) as w:
        return int(round(w.getnframes() / w.getframerate() * FPS))


def sfx_for(stem: str) -> str:
    if stem not in SFX:
        return ""
    name, vol, when = SFX[stem]
    at = when if isinstance(when, int) else 6 + vo_frames(stem) - 2
    return '   sfx: [{at: %d, name: "%s", vol: %s}],\n' % (at, name, vol)


# ── THE HOLD AFTER EACH LINE ───────────────────────────────────────────
# Owner, on the shipped cut: "feels a lot truncated and artificial".
# Measured against ep.1, which he calls perfect:
#
#                    speech rate      hold after a line
#   ep.1 APPROVED    3.89 syl/s       med 0.78s, range 14-40 frames
#   short (shipped)  4.64 syl/s       med 0.50s, range 14-15 frames
#
# Two separate faults, and both were mine. The rate is fixed in
# make_all_vo_local (1.30x -> 1.10x). This is the other one, and it is not
# simply "too tight" - it is too tight AND perfectly regular. Scaling the
# word-count estimate's slack stopped working once the lines got longer at
# 1.10x: `est - need` went to nothing, every beat fell to the floor, and
# every cut landed the same distance after every line. ep.1's holds run 14
# to 40 frames and correlate with line length not at all (r = 0.09) - the
# variety is editorial, not arithmetic.
#
# So the hold is chosen by what the beat DOES. A beat that puts something
# new on the wall has to be read, and gets a full second. A reaction over a
# held wall is a cut-in, and gets half of that. Mean lands at 23 frames,
# which is ep.1's median exactly.
HOLD_NEW = 26        # E or G: new wall content the viewer has to take in
HOLD_REACT = 15      # H: a reaction over the wall that is already there


def dur(vo: str, kind: str) -> int:
    a = vo_frames(vo)
    if not a:
        return max(40, 6 + 30)
    return 6 + a + (HOLD_REACT if kind == "H" else HOLD_NEW)


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
        at += dur(vo, kind)
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
