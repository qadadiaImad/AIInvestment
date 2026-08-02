"""Episode 2 assets: IHS quiz fixture + walkthrough schedule + VO placements.

One script, three outputs, one source of timing truth:
  - remotion/src/fixtures/strategy_quiz_ihs_2026-08-02.json (synthetic,
    python-authored+validated candles: inverse head & shoulders, freeze
    before the neckline break)
  - content/probe/strategy_walkthrough2_props.json (real CL=F daily window,
    generic annos: shoulders/head/neckline/breakout, measured-move trade
    frame, event_times for the VO placer)
  - printed event map

    python scripts/strategy_reel/make_episode2_assets.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PROBE = os.path.join(REPO, "content", "probe")
FPS = 30

# ---------------------------------------------------------------- quiz (synthetic)
LEVEL = 100.0   # neckline
ENTRY, STOP, TARGET = 100.0, 97.6, 103.5  # measured move ~ neck + (neck-head)
C = [
    (99.0, 100.2, 98.4, 99.6), (99.6, 100.1, 98.9, 99.2),        # neck zone left
    (99.2, 99.5, 97.9, 98.2), (98.2, 98.6, 97.4, 97.8),          # left shoulder ~97.6
    (97.8, 99.3, 97.5, 99.0), (99.0, 100.1, 98.7, 99.8),         # rally to neckline
    (99.8, 99.9, 98.3, 98.6), (98.6, 98.8, 96.6, 96.9),          # down into head
    (96.9, 97.2, 96.3, 96.6), (96.6, 98.0, 96.4, 97.7),          # HEAD ~96.4
    (97.7, 99.4, 97.5, 99.1), (99.1, 100.0, 98.8, 99.7),         # rally to neckline
    (99.7, 99.8, 98.2, 98.5), (98.5, 98.7, 97.5, 97.8),          # right shoulder ~97.5
    (97.8, 98.9, 97.6, 98.6), (98.6, 99.8, 98.4, 99.5),          # back to neckline
    # ---- revealFrom = 16: does the neckline break? ----
    (99.5, 100.9, 99.3, 100.7),                                   # BREAKOUT
    (100.7, 101.8, 100.4, 101.5), (101.5, 102.6, 101.2, 102.3),
    (102.3, 103.7, 102.0, 103.4),                                 # target 103.5 trades
    (103.4, 103.9, 102.9, 103.6),
]
REVEAL = 16


def validate_quiz():
    for i, (o, h, l, c) in enumerate(C):
        assert h >= max(o, c) and l <= min(o, c), f"bar {i} wick"
    head = min(l for _, _, l, _ in C[:REVEAL])
    ls = min(l for _, _, l, _ in C[2:5])
    rs = min(l for _, _, l, _ in C[12:15])
    assert head < ls - 0.8 and head < rs - 0.8, "head must be deepest"
    assert abs(ls - rs) < 0.5, "shoulders roughly equal"
    assert max(h for _, h, _, _ in C[REVEAL:]) >= TARGET
    assert min(l for _, _, l, _ in C[REVEAL:]) > STOP


def quiz():
    validate_quiz()
    fx = {
        "kick": "STRATEGY QUIZ 2", "patternName": "INVERSE HEAD & SHOULDERS",
        "levelPrice": LEVEL, "levelLabel": "NECKLINE",
        "answer": "BUY", "answerLine": "Neckline broke. Measured move in play.",
        "ruleTitle": "The setup",
        "ruleText": "Three lows: shoulder, deeper head, shoulder. The line "
                    "across the highs between them is the neckline. A close "
                    "above it is the signal; target = neckline + the depth "
                    "of the head. Stop below the right shoulder.",
        "footer": "SYNTHETIC example — illustrative, not a real chart — "
                  "educational only, not financial advice",
        "revealFrom": REVEAL, "entry": ENTRY, "stop": STOP, "target": TARGET,
        "durationInFrames": 720,
        "candles": [{"o": o, "h": h, "l": l, "c": c} for o, h, l, c in C],
    }
    out = os.path.join(REPO, "remotion", "src", "fixtures",
                       "strategy_quiz_ihs_2026-08-02.json")
    json.dump(fx, open(out, "w"), indent=1)
    print(f"quiz OK {out}")


# ---------------------------------------------------------------- walkthrough (real)
START, PER, TAIL = 40, 7, 150
HOLD = {"l1": 40, "head": 46, "l2": 46, "neckdraw": 56, "breakout": 46, "trade": 150}


def walkthrough():
    w = json.load(open(os.path.join(PROBE, "strategy_real_window2.json")))
    bars, idx = w["bars"], w["indices"]
    n = len(bars)
    n2 = max(range(idx["head"], idx["l2"]), key=lambda i: bars[i]["h"])

    bar_start, f = [], START
    for i in range(n):
        bar_start.append(f)
        f += PER
        if i == idx["l1"]:
            f += HOLD["l1"]
        elif i == idx["head"]:
            f += HOLD["head"]
        elif i == idx["l2"]:
            f += HOLD["l2"] + HOLD["neckdraw"]
        elif i == idx["breakout"]:
            f += HOLD["breakout"] + HOLD["trade"]
    total = f + TAIL

    y = lambda i, k: bars[i][k]
    months = {"01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY",
              "06": "JUN", "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT",
              "11": "NOV", "12": "DEC"}
    dl = lambda t: f"{months[t[5:7]]} {int(t[8:10])} {t[0:4][2:]}'"
    dlab = lambda t: f"{months[t[5:7]]} {int(t[8:10])}"

    annos = [
        {"i": idx["l1"], "price": y(idx["l1"], "l"), "label": f"LEFT SHOULDER · {dlab(bars[idx['l1']]['t'])}",
         "color": "#22E07E", "at": bar_start[idx["l1"]] + PER + 4, "dy": 120},
        {"i": idx["head"], "price": y(idx["head"], "l"), "label": f"HEAD · {dlab(bars[idx['head']]['t'])}",
         "color": "#FFD166", "at": bar_start[idx["head"]] + PER + 4, "dy": 70},
        {"i": idx["l2"], "price": y(idx["l2"], "l"), "label": f"RIGHT SHOULDER · {dlab(bars[idx['l2']]['t'])}",
         "color": "#22E07E", "at": bar_start[idx["l2"]] + PER + 4, "dy": 60},
        {"i": idx["breakout"], "price": y(idx["breakout"], "h"),
         "label": f"NECKLINE BREAK · {dlab(bars[idx['breakout']]['t'])}",
         "color": "#F2F7F4", "at": bar_start[idx["breakout"]] + PER + 4, "dy": -170},
    ]
    neck_at = bar_start[idx["l2"]] + PER + HOLD["l2"]
    trade_at = bar_start[idx["breakout"]] + PER + HOLD["breakout"]
    tp_at = bar_start[idx["resolve"]] + PER

    props = {
        "bars": bars, "barStart": bar_start,
        "level": w["neck"], "entry": w["entry"], "stop": w["stop"],
        "target": w["target"], "rr": w["rr"],
        "idx": None, "resistDrawAt": None, "breakoutTagAt": None,
        "retestTagAt": None,
        "annos": annos,
        "neck": {"price": w["neck"], "label": "NECKLINE", "at": neck_at},
        "flashes": [annos[3]["at"]],
        "resolveI": idx["resolve"],
        "tradeFrameAt": trade_at, "tpAt": tp_at, "totalFrames": total,
        "header": "WTI CRUDE OIL — DAILY",
        "subheader": f"{dl(bars[0]['t'])} – {dl(bars[-1]['t'])} · REAL CHART",
        "eventDates": {"resolve": dlab(bars[idx["resolve"]]["t"])},
        "dateTicks": [{"i": i, "label": dlab(bars[i]["t"])} for i in range(0, n, max(1, n // 5))],
        "footer": ("REAL DATA — WTI crude futures (CL=F), daily · Yahoo Finance · "
                   f"retrieved {w['retrieved_at']} — educational, not financial advice"),
        "event_times_s": {
            "start": START / FPS,
            "l1": (bar_start[idx["l1"]] + PER) / FPS,
            "head": (bar_start[idx["head"]] + PER) / FPS,
            "l2": (bar_start[idx["l2"]] + PER) / FPS,
            "neck": neck_at / FPS,
            "breakout": (bar_start[idx["breakout"]] + PER) / FPS,
            "trade_frame": trade_at / FPS,
            "tp": tp_at / FPS,
            "end": total / FPS,
        },
    }
    out = os.path.join(PROBE, "strategy_walkthrough2_props.json")
    json.dump(props, open(out, "w"), indent=1)
    print(f"walk OK {out}: {n} bars, {total} frames = {total / FPS:.1f}s")
    print("events:", {k: round(v, 2) for k, v in props["event_times_s"].items()})


if __name__ == "__main__":
    quiz()
    walkthrough()
