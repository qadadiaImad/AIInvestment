"""Wire the explanatory exhibits + transition SFX into ep.1's beats.

Measured before touching anything: 23 of ep.1's 39 beats set no wall
content of their own and fell through to the default candlestick tape, so
the same chart was on screen for 59% of the episode. The owner's note was
"the candlestick chart is displayed too many times - only show the progress
of the chart once".

Three changes, together:

  * ONE beat keeps the tape (`wall: "chart"`), the one where watching the
    price actually advance is the point of the line.
  * TWELVE beats that introduce a new idea get a new object-forward
    explanatory exhibit.
  * The remaining ten beats HOLD the exhibit they are reacting to. That is
    in the composition itself (`heldExhibitAt`), not here - a reaction beat
    keeping the evidence up is better editing than cutting back to a tape,
    and it needed no new art.

This script wires PICTURE ONLY. Sound is not its business: the canonical
`scripts/audio/stingmap.json` owns every sting, caps them at <=3 per
minute, and marks specific lines as silence on compliance grounds. An
earlier version of this file also placed a transition on each of these
beats; that was wrong and `scripts/audio/score_from_stingmap.py` now
scores the episode instead.

  python scripts/vector/wire_explanatory.py [--check]
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EP1 = REPO / "remotion/src/compositions/FairMarketEp1.tsx"

# beat -> (exhibit or None, sfx name, volume)
WIRE = {
    122:  ("fundamentals_ledger", "v_whoosh", 0.26),
    692:  ("single_domino",       "v_reveal", 0.24),
    985:  ("filing_stacks",       "v_whoosh", 0.26),
    1796: ("obvious_idea",        "v_reveal", 0.26),
    2921: ("fund_machine",        "v_whoosh", 0.25),
    3100: ("paper_conveyor",      "v_core",   0.22),
    3532: ("melting_edge",        "v_reveal", 0.24),
    4007: ("volume_dial",         "v_riser",  0.26),
    4175: (None,                  "v_whoosh", 0.24),   # the one chart beat
    4326: ("redacted_filing",     "v_reveal", 0.24),
    4626: ("attention_map",       "v_whoosh", 0.26),
    5189: ("read_it_yourself",    "v_reveal", 0.24),
    5697: ("outro_plate",         "v_core",   0.26),
}


def main() -> None:
    src = EP1.read_text("utf-8")
    check = "--check" in sys.argv
    done = 0
    for at, (exhibit, sfx, vol) in sorted(WIRE.items()):
        # every target beat opens `{at: N, actors:` except the outro, which
        # opens `{at: N, title:`
        for tail in ("actors:", "title:"):
            anchor = "{at: %d, %s" % (at, tail)
            if anchor in src:
                break
        else:
            raise SystemExit("no anchor for beat %d" % at)

        head = "{at: %d,\n   " % at
        if exhibit:
            head += 'exhibit: "%s",\n   ' % exhibit
        else:
            head += 'wall: "chart",\n   '
        head += tail

        if 'exhibit: "%s"' % exhibit in src or (
                not exhibit and '{at: %d,\n   wall:' % at in src):
            print("  beat %-5d already wired" % at)
            continue
        if src.count(anchor) != 1:
            raise SystemExit("anchor for beat %d is not unique (%d)"
                             % (at, src.count(anchor)))
        src = src.replace(anchor, head)
        done += 1
        print("  beat %-5d %-22s %s" % (at, exhibit or "<keeps the chart>", sfx))

    if check:
        print("check only, not written")
        return
    EP1.write_text(src, "utf-8")
    print("wired %d beats -> %s" % (done, EP1.name))


if __name__ == "__main__":
    main()
