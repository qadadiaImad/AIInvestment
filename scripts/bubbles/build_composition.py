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
            "  {at: %d,\n%s   actors: %s,\n"
            "   shots: [{from: 0, k: %s, kEnd: %s}],\n"
            '   vo: "%s", speaker: "%s",\n   line: "%s"},'
            % (at, key, actors, k0, k1, vo, spk, esc))
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
