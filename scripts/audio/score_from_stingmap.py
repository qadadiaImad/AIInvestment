"""Re-score ep.1's stings from scripts/audio/stingmap.json.

WHY THIS EXISTS. The owner asked for "more transition audio", and an
earlier pass in this session duly put a transition on nearly every beat.
Then the canonical stingmap landed on disk and that pass turned out to
break it in four concrete ways:

  * DENSITY. The map caps scored stings at <=3 per minute. A sting on
    every beat is ~12/min.
  * A COMPLIANCE RAIL. The map's `named-fact-restraint` entry names the
    line "July 2022. The Speaker's household sold NVIDIA - days before..."
    as SILENCE ONLY, because a sting under a real, named person's
    disclosed conduct reads as an accusation soundtrack and the episode's
    own footer cannot undo that. The earlier pass scored exactly that beat.
  * THE FLOOR. Hold beats were scored at 0.15-0.16; the house band is a
    fixed 0.24-0.34.
  * ONE STING PER BEAT. Beat 122 ended up with a transition on top of its
    existing motion hit, and the map marks that line silent anyway.

So the map wins over the earlier pass, and over this script's author. What
is preserved of the owner's intent is that stings are now placed
deliberately rather than sprinkled: ten beats scored, each with the exact
sound / frame / volume the map specifies, and two beats explicitly silent.

WHAT THIS DOES NOT TOUCH. Toon motion foley - `sfx_whip` on a head turn,
`sfx_poof` on a vanish, `sfx_pop` - is not a sting. It is anchored to a
drawing under the animation rules in CLAUDE.md 10.8 and stays exactly where
it is. Only the emphasis kit is re-scored.

  python scripts/audio/score_from_stingmap.py [--check]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EP1 = REPO / "remotion/src/compositions/FairMarketEp1.tsx"
MAP = REPO / "scripts/audio/stingmap.json"

FPS = 30
RUNTIME_S = 5880 / FPS

# taxonomy id -> ep.1 beat frame. Matched by the taxonomy's own
# `example_line` against the beat's `line`; recorded explicitly here so the
# mapping is reviewable rather than fuzzy-matched at runtime.
BEAT_OF = {
    "derision-sting":        217,    # "HA! ...Fundamentals."
    "thesis-lands":          299,    # "Sometimes... it trades on POLITICS."
    "shock-take":            393,    # "WHAT?!"
    "riser-metallic-pivot":  859,    # "...like a leaderboard."
    "absurd-reveal":        1892,    # "They made it an INDEX?!"
    "naive-plan-comic":     2417,    # "Then I'll just copy them!"
    "trap-springs":         2537,    # "...with a filing from six weeks ago?"
    "money-line":           2722,    # "The trade is public. The edge is not."
    "sign-off-cut":         5189,    # "Fair? No. But now you can read it."
    "scale-reveal":         5296,    # "Five hundred million dollars..."
}
# Explicit silences the map names, kept here so they are visible as a
# decision rather than as an absence.
SILENT = {122: "reaction-and-setup-silence", 436: "named-fact-restraint"}

# Every sound in the emphasis kit. Any of these found on a beat is stripped
# before the map is applied; motion foley is deliberately absent from this
# list and therefore survives.
STING_KIT = {"among_us", "core", "core_tiktok", "faah", "riser_metallic",
             "riser_suspense", "vine_boom", "vine_boom_bass", "whoosh",
             "whoosh_fire", "v_whoosh", "v_core", "v_boom", "v_riser",
             "v_reveal", "impact"}

ENTRY = re.compile(r"\{at: (\d+), name: \"([a-z_0-9]+)\"(?:, vol: ([0-9.]+))?\}")


def main() -> None:
    spec = json.loads(MAP.read_text("utf-8"))
    tax = {t["id"]: t for t in spec["taxonomy"]}
    src = EP1.read_text("utf-8")

    # ---- 1. strip every emphasis sting, leave motion foley alone -------
    # The character class is `[^\]]*`, NOT `.*?`. An sfx array contains no
    # inner `]`, so this cannot run past its own closing bracket - whereas
    # a non-greedy `.*?` happily matched across `sfx: [...], actors: [...]`
    # on beats where those share a line and deleted the actors with it.
    def strip(m: re.Match) -> str:
        kept = [e.group(0) for e in ENTRY.finditer(m.group(1))
                if e.group(2) not in STING_KIT]
        return "sfx: [%s]," % ", ".join(kept) if kept else "\x00"

    before = len(ENTRY.findall(src))
    src = re.sub(r"sfx: \[([^\]]*)\],", strip, src)
    # remove the emptied entries along with their own line or inline space
    src = re.sub(r"\n[ ]*\x00", "", src)
    src = re.sub(r"\x00[ ]*", "", src)
    after = len(ENTRY.findall(src))
    print("stripped %d emphasis stings (%d motion hits kept)"
          % (before - after, after))

    # ---- 2. apply the map --------------------------------------------
    scored = 0
    for tid, at in sorted(BEAT_OF.items(), key=lambda kv: kv[1]):
        t = tax[tid]
        entry = ('{at: %d, name: "%s", vol: %s}'
                 % (t["at"], t["sound"], t["vol"]))

        # Work inside this beat's own span. A beat may already carry motion
        # foley, and adding a second `sfx:` key to the same object literal
        # is a TypeScript error, so an existing array is MERGED into rather
        # than duplicated. Stings sort ahead of foley only by frame order.
        # The span ends at the NEXT beat, whether or not a blank line
        # separates them. Requiring "\n\n  {at:" ran two adjacent beats
        # together and put the sign-off sting on the following beat.
        start = src.index("{at: %d," % at)
        nxt = re.search(r"\n  \{at: \d+,", src[start + 1:])
        end = (start + 1 + nxt.start()) if nxt else src.index("\n];", start)
        span = src[start:end]

        if "sfx: [" in span:
            span = span.replace("sfx: [", "sfx: [%s, " % entry, 1)
        else:
            span = span.replace("{at: %d," % at,
                                "{at: %d,\n   sfx: [%s]," % (at, entry), 1)
        src = src[:start] + span + src[end:]
        scored += 1
        print("  %-22s beat %-5d %-16s @%-3d %.2f"
              % (tid, at, t["sound"], t["at"], t["vol"]))

    for at, tid in sorted(SILENT.items()):
        print("  %-22s beat %-5d SILENT (per the map)" % (tid, at))

    per_min = scored / (RUNTIME_S / 60)
    print("\n%d stings over %.1fs = %.2f per minute (cap is 3)"
          % (scored, RUNTIME_S, per_min))
    if per_min > 3:
        print("  NOTE: marginally over. The taxonomy explicitly assigns "
              "every one of these;\n  the overage is the spec's own "
              "tension between its entry list and its cap.")

    if "--check" in sys.argv:
        print("check only, not written")
        return
    EP1.write_text(src, "utf-8")
    print("-> %s" % EP1.name)


if __name__ == "__main__":
    main()
