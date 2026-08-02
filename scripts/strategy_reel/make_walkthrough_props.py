"""Compile the real-Brent walkthrough schedule (Act 4).

Single source of timing truth: this script converts the scanner's window
(strategy_real_window.json) into a fully precomputed frame schedule — bar
print frames, annotation draw frames, trade-frame act, TP hit — consumed
verbatim by StrategyWalkthrough.tsx AND by the VO placer. Print pacing
pauses at teaching checkpoints (line draw, breakout, retest/trade frame)
exactly as a human instructor would.

    python scripts/strategy_reel/make_walkthrough_props.py
Writes content/probe/strategy_walkthrough_props.json (incl. event_times).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "content", "probe", "strategy_real_window.json")
OUT = os.path.join(REPO, "content", "probe", "strategy_walkthrough_props.json")

FPS = 30
START = 40           # first bar prints here (header settles first)
PER = 9              # frames per bar while tape runs
HOLD_LINE = 54       # pause after touch2: resistance line draws + tag
HOLD_BREAK = 44      # pause at breakout: tag + flash
HOLD_RETEST = 160    # pause at retest: arrow, trade frame, and the full entry/stop/target narration
TAIL = 150           # after last bar: TP banner + date stamp + breathing room


def main():
    w = json.load(open(SRC))
    idx = w["indices"]
    n = len(w["bars"])

    bar_start, f = [], START
    for i in range(n):
        bar_start.append(f)
        f += PER
        if i == idx["touch2"]:
            f += HOLD_LINE
        elif i == idx["breakout"]:
            f += HOLD_BREAK
        elif i == idx["retest"]:
            f += HOLD_RETEST
    total = f + TAIL

    resist_draw = bar_start[idx["touch2"]] + PER + 6
    breakout_tag = bar_start[idx["breakout"]] + PER
    retest_tag = bar_start[idx["retest"]] + PER + 4
    trade_frame_at = retest_tag + 30
    tp_at = bar_start[idx["resolve"]] + PER

    months = {"01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY",
              "06": "JUN", "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT",
              "11": "NOV", "12": "DEC"}

    def dlabel(t):
        y, m, d = t.split("-")
        return f"{months[m]} {int(d)}"

    date_ticks = [{"i": i, "label": dlabel(w["bars"][i]["t"])}
                  for i in range(0, n, max(1, n // 5))]

    props = {
        "bars": w["bars"],
        "barStart": bar_start,
        "level": w["level"], "entry": w["entry"],
        "stop": w["stop"], "target": w["target"], "rr": w["rr"],
        "idx": idx,
        "resistDrawAt": resist_draw,
        "breakoutTagAt": breakout_tag,
        "retestTagAt": retest_tag,
        "tradeFrameAt": trade_frame_at,
        "tpAt": tp_at,
        "totalFrames": total,
        "header": "BRENT CRUDE — DAILY",
        "subheader": f"{dlabel(w['bars'][0]['t'])} – {dlabel(w['bars'][-1]['t'])} 2020 · REAL CHART",
        "eventDates": {k: dlabel(v) for k, v in w["dates"].items()},
        "dateTicks": date_ticks,
        "footer": ("REAL DATA — Brent crude futures (BZ=F), daily · Yahoo Finance · "
                   f"retrieved {w['retrieved_at']} — educational, not financial advice"),
        "event_times_s": {
            "start": START / FPS,
            "printing": (START + 8 * PER) / FPS,
            "resist": resist_draw / FPS,
            "breakout": breakout_tag / FPS,
            "retest": retest_tag / FPS,
            "trade_frame": trade_frame_at / FPS,
            "tp": tp_at / FPS,
            "end": total / FPS,
        },
    }
    json.dump(props, open(OUT, "w"), indent=1)
    print(f"OK {OUT}: {n} bars, total {total} frames = {total / FPS:.1f}s")
    print("events(s):", {k: round(v, 2) for k, v in props["event_times_s"].items()})


if __name__ == "__main__":
    main()
