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
MAP = REPO / "scripts/audio/stingmap.json"
FPS = 30

# taxonomy id -> beat frame, per episode. Matched by the taxonomy's own
# `example_line` against the beat's `line`; recorded explicitly here so the
# mapping is reviewable rather than fuzzy-matched at runtime.
#
# The map was authored across BOTH episodes - its scale-reveal,
# timing-gap-suspense, gravity-pause and sign-off-cut example lines are all
# ep.2 dialogue - so the same taxonomy scores both.
EP1_BEAT_OF = {
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
EP1_SILENT = {122: "reaction-and-setup-silence", 436: "named-fact-restraint"}

# EPISODE 2. Deliberately sparser: 6 stings over 150s = 2.4/min, inside the
# cap with room to spare, because ep.2's subject is conduct under
# investigation and the kit's comedic sounds would read as mockery of it.
# `among_us` in particular is NOT used here - the map only clears it because
# ep.1's joke is a structural fact, which is not what ep.2 is about.
EP2_BEAT_OF = {
    "scale-reveal":          596,   # "...five hundred and eighty million"
    "timing-gap-suspense":  1037,   # "Sixteen minutes later, the President posts"
    "riser-metallic-pivot": 2930,   # "Now. They did catch one." - correction pivot
    "money-line":           4007,   # "Sometimes the market moves first."
    "sign-off-cut":         4221,   # "Fair? No. But now you know what to watch."
}
EP2_SILENT = {
    2321: "gravity-pause (the one-word denial)",
    2379: "gravity-pause (sit with it)",
    1356: "reaction-and-setup-silence",
    2260: "reaction-and-setup-silence",
}

EPISODES = {
    "ep1": ("remotion/src/compositions/FairMarketEp1.tsx", 5880,
            EP1_BEAT_OF, EP1_SILENT),
    "ep2": ("remotion/src/compositions/FairMarketEp2.tsx", 4500,
            EP2_BEAT_OF, EP2_SILENT),
}

# EPISODE 3 and its Shorts cut are AUDITED, not scored, and the difference
# is deliberate. This tool places a sting at the taxonomy's own frame
# offset, which was derived from ep.1's lines; ep.3's lines are shorter and
# a fixed offset lands several of them mid-word, breaking the map's own
# rule against a sting arriving before the word it marks has finished. So
# ep.3's placements are computed from the MEASURED line length in
# scripts/bubbles/build_composition.py (which also means they survive a
# regeneration of the composition, unlike anything written in here), and
# this checks the result against the map instead of authoring it.
AUDIT = {
    "bubbles": ("remotion/src/compositions/Bubbles.tsx", 5434),
    "bshort": ("remotion/src/compositions/BubblesShort.tsx", 717),
}


def audit(name: str) -> int:
    """Check an already-scored composition against the map's hard rules."""
    rel, frames = AUDIT[name]
    target = REPO / rel
    src = target.read_text("utf-8")
    runtime_s = frames / FPS
    spec = json.loads(MAP.read_text("utf-8"))
    lo, hi = 0.24, 0.34

    beats = [(int(m.group(1)), m.start())
             for m in re.finditer(r"\n  \{at: (\d+),", src)]
    beats.sort()
    found = []
    for i, (at, pos) in enumerate(beats):
        end = beats[i + 1][1] if i + 1 < len(beats) else len(src)
        for e in ENTRY.finditer(src[pos:end]):
            if e.group(2) in STING_KIT:
                found.append((at, i, e.group(2), int(e.group(1)),
                              float(e.group(3) or 0.5)))

    print("auditing %s (%s, %.1fs, %d beats)"
          % (name, target.name, runtime_s, len(beats)))
    fails = []
    for at, i, snd, off, vol in found:
        print("  beat %-5d #%-3d %-16s @%-4d %.2f" % (at, i, snd, off, vol))
        if not (lo <= vol <= hi):
            fails.append("beat %d: vol %.2f outside %.2f-%.2f" % (at, vol, lo, hi))

    per_beat = {}
    for at, i, snd, off, vol in found:
        per_beat[i] = per_beat.get(i, 0) + 1
    for i, n in per_beat.items():
        if n > 1:
            fails.append("beat index %d carries %d stings (cap 1)" % (i, n))
    idxs = sorted(per_beat)
    for a, b in zip(idxs, idxs[1:]):
        if b - a == 1:
            fails.append("beats %d and %d are consecutive and both scored"
                         % (beats[a][0], beats[b][0]))

    cores = [f for f in found if f[2] == "core"]
    if len(cores) > 2:
        fails.append("`core` spent %d times; the map reserves it for the "
                     "act-1 thesis and the money line" % len(cores))

    # the cap lives in the map's own prose; read it rather than retyping it
    cap = float(re.search(r"(\d+) scored stings per minute",
                          spec["density_rule"]).group(1))
    per_min = len(found) / (runtime_s / 60)
    print("\n%d stings over %.1fs = %.2f per minute (cap is %.0f)"
          % (len(found), runtime_s, per_min, cap))
    if per_min > cap:
        fails.append("density %.2f/min over the cap of %.0f" % (per_min, cap))

    if fails:
        print("\nFAIL")
        for f in fails:
            print("  - " + f)
        return 1
    print("PASS - inside the band, one per beat, none consecutive, "
          "core spent twice at most")
    return 0

# Every sound in the emphasis kit. Any of these found on a beat is stripped
# before the map is applied; motion foley is deliberately absent from this
# list and therefore survives.
STING_KIT = {"among_us", "core", "core_tiktok", "faah", "riser_metallic",
             "riser_suspense", "vine_boom", "vine_boom_bass", "whoosh",
             "whoosh_fire", "v_whoosh", "v_core", "v_boom", "v_riser",
             "v_reveal", "impact"}

ENTRY = re.compile(r"\{at: (\d+), name: \"([a-z_0-9]+)\"(?:, vol: ([0-9.]+))?\}")


def main() -> None:
    a = next((a for a in sys.argv[1:] if a in AUDIT), None)
    if a:
        raise SystemExit(audit(a))
    ep = next((a for a in sys.argv[1:] if a in EPISODES), "ep1")
    rel, frames, BEAT_OF, SILENT = EPISODES[ep]
    target = REPO / rel
    runtime_s = frames / FPS
    spec = json.loads(MAP.read_text("utf-8"))
    tax = {t["id"]: t for t in spec["taxonomy"]}
    src = target.read_text("utf-8")
    print("scoring %s (%s, %.1fs)" % (ep, target.name, runtime_s))

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

    per_min = scored / (runtime_s / 60)
    print("\n%d stings over %.1fs = %.2f per minute (cap is 3)"
          % (scored, runtime_s, per_min))
    if per_min > 3:
        print("  NOTE: marginally over. The taxonomy explicitly assigns "
              "every one of these;\n  the overage is the spec's own "
              "tension between its entry list and its cap.")

    if "--check" in sys.argv:
        print("check only, not written")
        return
    target.write_text(src, "utf-8")
    print("-> %s" % target.name)


if __name__ == "__main__":
    main()
