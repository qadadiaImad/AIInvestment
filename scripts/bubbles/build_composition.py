"""Generate the Bubbles composition by adapting the shipped ep.2 one.

WHY ADAPT RATHER THAN AUTHOR. FairMarketEp2.tsx is ~1000 lines and almost
all of it is machinery that took this repo weeks to get right: the viseme
mouth tracks, the interact/idle acting, the hold-the-previous-exhibit wall
chain, the beat-scoped wall glow, the CAM_PULL/CAST framing, the panel
staging audit's assumptions. Retyping that for a third episode would be
re-earning bugs already paid for. Only the BEATS array and the graphics
menu are genuinely new, so only those are replaced.

The episode is NOT written over FairMarketEp3.tsx. That slot holds the
congressional-ban-vote episode - a different subject with its own recorded
VO on disk - and its script being rejected is not a reason to destroy it.
This ships as its own composition, titled "ep.3" on screen.

Beat timings here are ESTIMATES from word count. That is fine and expected:
retime_beats.py derives every start from the measured audio afterwards and
lands on exact total frames. Never hand-tune these.

  python scripts/bubbles/build_composition.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "remotion/src/compositions/FairMarketEp2.tsx"
DST = REPO / "remotion/src/compositions/Bubbles.tsx"

FPS = 30
WPS = 2.25          # slower than raw speech: PERFORM tags add up to 1.3s a line
GAP = 14            # frames of air between beats
LEAD = 6            # VO_DELAY already accounts for the rest

# speaker -> staging. Single-speaker beats dominate; the two-shots are
# placed by hand below where the beat is a genuine exchange.
SOLO = {
    "SOL": '[{poses: ["%s"], kind: "full", x: 790, y: FLOOR_Y, h: 930}]',
    "REX": '[{poses: ["%s"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}]',
}
TWO = ('[{poses: ["rex_skeptic"], kind: "full", x: 298, y: FLOOR_Y, h: 1000},\n'
       '            {poses: ["sol_finger"], kind: "full", x: 834, y: FLOOR_Y, h: 900}]')

SOL_POSE = ["sol_point", "sol_finger", "sol_point_v1", "sol_smug_v1"]
REX_POSE = ["rex_eager", "rex_skeptic", "rex_listen", "rex_shock"]

from beats_v2 import B   # the v2 voice pass; see that file for why
import patch_hold


# ── THE STINGS ─────────────────────────────────────────────────────────
# Ep.3 shipped four cuts with ZERO emphasis sounds while ep.1 - the one the
# owner called perfect - carries ten. "No pace, something is missing" is
# partly this: the kit that punctuates ep.1's beats was simply never wired
# into this episode.
#
# Every entry below is an id from scripts/audio/stingmap.json, which is the
# authority here and outranks anything I might think sounds good. What the
# map decides, and why each of these is the entry it is:
#
#   b03  derision-sting        faah            Sol puncturing Rex's bath-bubble
#                                              joke - aimed at Rex, not at any
#                                              real person's conduct
#   b05  shock-take            vine_boom_bass  a drawn take; house rule 10.8
#                                              overrides reaction-silence
#   b09  thesis-lands          core            "Just a machine. Four moving
#                                              parts." - the act-1 thesis
#   b18  riser-metallic-pivot  riser_metallic  Rex correcting his own wrong
#                                              conclusion ("it's an EXCUSE")
#   b23  trap-springs          whoosh_fire     the crowbar turning around on him
#   b33  money-line            core   0.33     "Everyone's responsible. Nobody's
#                                              the villain." - the sentence the
#                                              episode exists to deliver
#   b39  scale-reveal          core_tiktok     a number that IS the beat, and a
#                                              loss, so no win-coded sting
#   b47  shock-take            vine_boom_bass  the second drawn take
#   b52  sign-off-cut          whoosh          the cut to the end card
#
# Deliberately SILENT, each matching a taxonomy "none" entry: the cold open
# (b01), Rex's naive claims and wrong conclusions (b02, b07, b27), the
# Lehman line (b04 - a named real-world failure gets the same restraint as a
# named person's trade), and b28 "No.", which is the gravity-pause verbatim.
#
# Nine stings over 181s is 2.98/minute, just inside the map's cap of 3.
# Ep.1 sits at 3.06 and its own scorer calls that marginally over, so this
# does not follow ep.1 past the line.
#
# `after` means the sting fires once the line has finished speaking, which
# is the map's rule against telegraphing a beat before it lands. The two
# takes fire at 0, because there the sound IS the drawing's impact frame.
SFX = {
    "b03_sol_rent":      ("faah",           0.28, "after"),
    "b05_rex_what":      ("vine_boom_bass", 0.30, 0),
    "b09_sol_nomame":    ("core",           0.30, "after"),
    # The riser fires EARLY, not after the line, and it is the one exception
    # to the rule below for a reason: it is not marking a word. It is a
    # 2.8-second build that does not get loud until 1.3s in and peaks at
    # 1.7s, so placed after the line it peaks over the NEXT beat's dialogue
    # and does nothing for the pivot it exists to carry. At 5 it builds
    # under Rex working it out and resolves as he lands on "EXCUSE". This is
    # also the taxonomy's own offset for the entry.
    "b18_rex_excuse":    ("riser_metallic", 0.26, 5),
    "b23_sol_controlsyou": ("whoosh_fire",  0.30, "after"),
    "b33_sol_everyone":  ("core",           0.33, "after"),
    "b39_sol_trillion":  ("core_tiktok",    0.30, "after"),
    "b47_rex_what2":     ("vine_boom_bass", 0.30, 0),
    "b52_sol_time":      ("whoosh",         0.27, "after"),
}
VO_DIR = REPO / "remotion/public/audio/fairmarket_bubbles"


def vo_frames(stem: str) -> int:
    """Length of a recorded line, in frames. 0 if it isn't on disk yet."""
    import wave
    p = VO_DIR / (stem + ".wav")
    if not p.exists():
        return 0
    with wave.open(str(p)) as w:
        return int(round(w.getnframes() / w.getframerate() * FPS))


def sfx_for(stem: str) -> str:
    """The `sfx:` line for a beat, or "" if the map leaves it silent."""
    if stem not in SFX:
        return ""
    name, vol, when = SFX[stem]
    at = when if isinstance(when, int) else 6 + vo_frames(stem) - 2
    return '   sfx: [{at: %d, name: "%s", vol: %s}],\n' % (at, name, vol)


def dur(line: str) -> int:
    words = len(line.split())
    return max(48, int(round(words / WPS * FPS)) + LEAD)


def build_beats() -> tuple[str, int]:
    at = 0
    out = []
    for i, (spk, vo, line, kind, val, pose, two) in enumerate(B):
        poses = (SOL_POSE if spk == "SOL" else REX_POSE)
        actors = TWO if two else SOLO[spk] % poses[pose % len(poses)]
        key = ""
        if kind == "E":
            key = '   exhibit: "%s",\n' % val
        elif kind == "G":
            key = '   graphic: "%s",\n' % val
        # a gentle push that never lands, alternating direction per beat
        k0, k1 = (1.0, 1.08) if i % 2 == 0 else (1.04, 1.12)
        esc = line.replace('"', '\\"')
        out.append(
            "  {at: %d,\n%s%s   actors: %s,\n"
            "   shots: [{from: 0, k: %s, kEnd: %s}],\n"
            '   vo: "%s", speaker: "%s",\n   line: "%s"},'
            % (at, key, sfx_for(vo), actors, k0, k1, vo, spk, esc))
        at += dur(line) + GAP
    return "\n\n".join(out), at


def main() -> None:
    src = SRC.read_text("utf-8")
    beats, total = build_beats()

    # ---- swap the beats -------------------------------------------
    a = src.index("const BEATS: Beat[] = [")
    b = src.index("\n];", a)
    src = src[:a] + "const BEATS: Beat[] = [\n" + beats + src[b:]

    # ---- identity --------------------------------------------------
    src = src.replace("EP2_FRAMES", "BUBBLES_FRAMES")
    src = src.replace("FairMarketEp2", "Bubbles")
    src = src.replace("audio/fairmarket_ep2/", "audio/fairmarket_bubbles/")
    # THE MOUTH TRACKS. Missing this is what killed the lip-sync and the
    # blinks in the first three cuts: the composition kept importing ep.2's
    # track file, whose keys are ep.2's VO stems, so NONE of this episode's
    # 52 stems matched and every mouth stayed shut. The viseme machinery was
    # working perfectly on data that did not describe this episode.
    src = src.replace("mouth_tracks_ep2.json", "mouth_tracks_bubbles.json")
    src = re.sub(r"export const BUBBLES_FRAMES = \d+;.*",
                 "export const BUBBLES_FRAMES = %d;   // %.0fs"
                 % (total, total / FPS), src, count=1)

    # ---- graphics menu ---------------------------------------------
    src = src.replace(
        'import {CountdownExhibit, StackExhibit, TickerTape} from "../motion/Infographic";',
        'import {BigNumberExhibit, TickerTape} from "../motion/Infographic";\n'
        'import {SeriesExhibit} from "../motion/Series";\n'
        'import {MachineParts, MachineLoop} from "../motion/Machine";')
    src = src.replace(
        '  graphic?: "countdown_16" | "stack_26";',
        '  graphic?: "fedfunds" | "caseshiller" | "drawdown2008" | "unrate"\n'
        '    | "dotcom" | "wealth" | "machine_parts" | "machine_loop";')

    # the render chain: one SeriesExhibit branch covers all five series
    a = src.index('            ) : cur.graphic === "countdown_16" ? (')
    b = src.index('            ) : cur.card ?', a)
    src = src[:a] + """            ) : cur.graphic === "machine_parts" ? (
              <MachineParts since={since} w={WALL.w} h={WALL.h} />
            ) : cur.graphic === "machine_loop" ? (
              <MachineLoop since={since} w={WALL.w} h={WALL.h} />
            ) : cur.graphic === "wealth" ? (
              <BigNumberExhibit since={since} w={WALL.w} h={WALL.h}
                kicker="HOUSEHOLD NET WORTH LOST" value="$11.5 TRILLION"
                caption="peak 2007 Q3 to trough 2009 Q1, a fall of 16.3%"
                foot="Federal Reserve Z.1, households and nonprofits - FRED TNWBSHNO" />
            ) : cur.graphic ? (
              <SeriesExhibit name={cur.graphic as never}
                since={since} w={WALL.w} h={WALL.h} />
""" + src[b:]

    # graphics must be holdable too, or reaction beats after a data
    # panel fall through to the tape. A build step, not a hand edit -
    # it was lost once already to a regeneration.
    src = patch_hold.apply(src)

    DST.write_text(src, "utf-8")
    print("%d beats, %d frames (%.1fs) -> %s"
          % (len(B), total, total / FPS, DST.name))
    kinds = {}
    for _, _, _, k, v, _, _ in B:
        kinds[k] = kinds.get(k, 0) + 1
    print("  wall:", kinds)
    print("  exhibits:", sorted({v for _, _, _, k, v, _, _ in B if k == "E"}))
    print("  graphics:", sorted({v for _, _, _, k, v, _, _ in B if k == "G"}))
    json.dump([dict(vo=v, speaker=s, line=l) for s, v, l, *_ in B],
              open(REPO / "data/bubbles/lines.json", "w"), indent=1)


if __name__ == "__main__":
    main()
