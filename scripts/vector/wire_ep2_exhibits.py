"""Wire episode 2's explanatory exhibits and its single chart beat.

Measured before touching anything: 19 of ep.2's 32 beats set no wall content
of their own and fell through to the candlestick tape, and a further 8 shots
carried `hideCard`, which used to swap the wall FOR that tape. Ep.2 had no
generated exhibits at all - only two code-drawn graphics and a few cards.

After this pass the wall resolves as:

  * 16 beats carry a new object-forward explanatory exhibit;
  * 4 reaction beats HOLD the exhibit they are reacting to (`heldExhibitAt`
    in the composition, not here);
  * the existing graphics and cards keep their beats;
  * exactly ONE beat shows the tape - "You stop assuming the news moves the
    market. Sometimes the market moves first." Watching price move before
    the news IS that line, so it is the one place the chart earns its keep.

Sound is NOT this script's business. `scripts/audio/score_from_stingmap.py
ep2` scores the episode from the canonical stingmap, which caps stings at
<=3/min and marks the one-word denial and the "sit with it" beat silent.

  python scripts/vector/wire_ep2_exhibits.py [--check]
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EP2 = REPO / "remotion/src/compositions/FairMarketEp2.tsx"

# beat -> exhibit name, or None for the one beat that keeps the tape
WIRE = {
    0:    "ep2_recap_filing",
    173:  "ep2_late_useless",
    479:  "ep2_dawn_clock",
    596:  "ep2_oil_position",
    886:  "ep2_inverted_bet",
    1356: "ep2_tell_me_coincidence",
    1495: "ep2_once_twice",
    2017: "ep2_running_total",
    2260: "ep2_so_caught",
    2379: "ep2_empty_docket",
    2930: "ep2_caught_one",
    3291: "ep2_provable",
    3374: "ep2_trail_leads",
    3931: "ep2_what_do_i_do",
    4007: None,                     # the one chart beat
    4221: "ep2_what_to_watch",
    4346: "ep2_outro_plate",
}


def main() -> None:
    src = EP2.read_text("utf-8")
    done = 0
    for at, exhibit in sorted(WIRE.items()):
        # every beat opens `{at: N, actors:` except the two title beats,
        # which open `{at: N, title:`
        for tail in ("actors:", "title:"):
            anchor = "{at: %d, %s" % (at, tail)
            if anchor in src:
                break
        else:
            raise SystemExit("no anchor for beat %d" % at)
        if src.count(anchor) != 1:
            raise SystemExit("beat %d anchor is not unique" % at)

        key = ('exhibit: "%s",' % exhibit) if exhibit else 'wall: "chart",'
        if key in src and exhibit:
            print("  beat %-5d already wired" % at)
            continue
        src = src.replace(anchor, "{at: %d,\n   %s\n   %s" % (at, key, tail))
        done += 1
        print("  beat %-5d %s" % (at, exhibit or "<keeps the chart>"))

    if "--check" in sys.argv:
        print("check only, not written")
        return
    EP2.write_text(src, "utf-8")
    print("wired %d beats -> %s" % (done, EP2.name))


if __name__ == "__main__":
    main()
