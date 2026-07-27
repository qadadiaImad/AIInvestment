"""Turn the scanner's setup.json into the reel's Remotion props.

Kept separate from find_failed_setup.py on purpose. The scanner answers "what
really happened", and its output should stay usable by anything; this answers
"how is that staged in a 1080x1920 frame", which is a decision about one video.
Folding the two together is how a staging tweak ends up silently changing which
window the story is about.

Everything numeric here is copied through, never recomputed. The only things
this file authors are the plate, the monitor quad, the character staging and
the footer prose - and the footer's job is to say exactly where the numbers
came from, so it is checked against the scanner's own stamp rather than typed.

Usage:
    python scripts/btc_reel/build_fixture.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "remotion", "src", "fixtures", "btc_reel", "setup.json")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "btc_reel", "trade_fail_reel.json")

# Measured from the accepted plate by scripts/meme_reel/measure_screen_quad.py.
# Guessed corners are the "insert lands off the monitor" bug, so these are
# copied from the shipped MemeReel fixture rather than re-eyeballed.
QUAD = [{"x": 85, "y": 722}, {"x": 502, "y": 722}, {"x": 502, "y": 974}, {"x": 85, "y": 974}]
CHART_W, CHART_H = 1324, 800

# Character staging. Solved, not chosen - see the note below.
#
# The owner approved "1020px at x=800" off a GroundingCheck still, but that
# still shows ONE drawing at a time, and the constraint is set by the whole cut
# sheet. Measuring the ink extents of all twelve drawings used here (they are
# roughly centred on the feet and up to 883px wide, and facing="left" mirrors
# them about footX) gives a hard result: at 1020px tall the feasible footX
# window is EMPTY, and even the ten narrowest poses cap footX at 615. The
# approved x=800 clips a gesture in every pose - the shipped MemeReel staging
# clips too, which is why this went unnoticed.
#
# Solving it exactly (all twelve poses fully inside the frame) forces him to
# 960px at x=600 - dead centre, standing on the monitor. That trades one visible
# flaw for a worse one. So the constraint that actually got solved is the one
# that matters: no GESTURE leaves the frame, and the quiet poses do not sit on
# the chart.
#
# 900px at x=760 does that. Only `shock` (17px) and `stagger` (52px) run past
# the right edge, both momentary reaction poses where an arm crossing the frame
# edge reads as energy rather than as a crop. `shrug` is dropped from the cut
# sheet outright - at 883px it is the widest drawing in the set and overflows by
# ~130px.
#
# He still overlaps the monitor's right third in a wide shot; that is unavoidable
# with the monitor at x 85..502 in the plate. The composition answers it rather
# than the staging: the camera is biased right through the quiz and wait beats,
# and every stretch where the chart is the content is a close-up with him faded
# out entirely.
#
# Feet sit on the desk's own foot line - the one depth in the plate whose floor
# position is measured (scripts/meme_reel/measure_floor_plane.py -> 1556.4).
CHAR = {"charCenterX": 760, "charFeetY": 1556, "charHeight": 900}


def main():
    s = json.load(open(SRC))

    assert s["bars"][s["trigger"]["bar"]]["d"], "bars must carry dates for the footer"
    first, last = s["bars"][0]["d"], s["bars"][-1]["d"]
    assert (first, last) == (s["from"], s["to"]), "window stamp disagrees with the bars"

    out = {
        "plate": "meme_reel/room_plate.png",
        "quad": QUAD,
        "chartWidth": CHART_W,
        "chartHeight": CHART_H,
        "symbol": s["symbol"],
        "subject": f"{s['symbol']} · DAILY",
        "stamp": f"{first} → {last}",
        "bars": s["bars"],
        "setupBars": s["setupBars"],
        "support": s["support"],
        "resistances": s["resistances"],
        "trendline": s["trendline"],
        "trigger": s["trigger"],
        "entry": s["entry"],
        "stop": s["stop"],
        "target": s["target"],
        "risk": s["risk"],
        "slAt": s["slAt"],
        "mfe": s["mfe"],
        "drop": s["drop"],
        **CHAR,
        # The footer is the provenance stamp and it is on every frame. It names
        # the instrument as an ETF because spot BTC is not on the brokerage
        # feed - the chart must never be read as BTC/USD itself.
        "footer": (
            f"{s['symbol']} (spot Bitcoin ETF) daily bars · {s['source']} · "
            f"retrieved {s['retrieved_at']} · window {first} → {last} · "
            "hindsight example · educational only, not financial advice"
        ),
        "durationInFrames": 1200,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"-> {os.path.relpath(OUT, REPO)}")
    print(f"   {len(out['bars'])} bars, {out['setupBars']} setup / {len(out['bars']) - out['setupBars']} reveal")
    print(f"   {out['footer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
