"""Find a REAL occurrence of a TA pattern and emit a TradingQuiz fixture.

The pattern library ships synthetic OHLC. It is validated and it demonstrates
the geometry, but it looks like what it is: too few bars, too clean a trend, not
enough of the noise a real tape has. This scans actual IBKR bars for a genuine
occurrence instead, with enough surrounding context that the chart reads as a
chart rather than a diagram.

Same discipline as scripts/trading_styles/find_real_windows.py — the detector
either finds a window that already satisfies the definition, or it reports
nothing found. It never nudges data to fit.

Usage:
    python scripts/ta_quiz/find_real_pattern.py breakout-retest
    python scripts/ta_quiz/find_real_pattern.py --list
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PRICES = os.path.join(REPO, "data", "prices")
FIXDIR = os.path.join(REPO, "remotion", "src", "fixtures", "ta_quiz")

DURATION = 546          # must match TRADING_QUIZ_MIN_FRAMES
SETUP = 62              # context bars before the decision point
REVEAL = 12             # bars of "what happened next"
DEV_HARD = 0.15         # bars deviating more than this are not trusted


def load(fname):
    src = json.load(open(os.path.join(PRICES, fname)))
    bars, bad = [], set()
    for i, b in enumerate(src["bars"]):
        o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        if max(max(o, c) - h, l - min(o, c), 0.0) > DEV_HARD:
            bad.add(i)
        bars.append({**b, "h": max(h, o, c), "l": min(l, o, c)})
    return src, bars, bad


# ------------------------------------------------------------------ detectors
# Each takes the SETUP window and returns (score, level, extras) or None.
# `level` is the price line the reel draws; the decision point is the last bar.

def breakout_retest(w):
    """Bullish breakout and retest.

    A resistance that held at least twice, a CLOSE above it, a pullback that
    touches it from above without closing back below, and a hold. The retest is
    the whole point: the level that rejected price becomes the floor it bounces
    from, and the trade is the bounce, not the break.
    """
    n = len(w)
    # Resistance from the first 60% of the window: the highest level touched
    # at least twice within a tight band.
    base = w[: int(n * 0.6)]
    cands = sorted({round(b["h"], 2) for b in base}, reverse=True)
    best = None
    for lvl in cands[:40]:
        band = lvl * 0.004                       # 0.4% — a level, not a line
        touches = [i for i, b in enumerate(base) if abs(b["h"] - lvl) <= band]
        if len(touches) < 2 or max(touches) - min(touches) < 5:
            continue
        if any(b["c"] > lvl + band for b in base):   # must have held, not broken
            continue

        after = w[len(base):]
        brk = next((i for i, b in enumerate(after) if b["c"] > lvl + band), None)
        if brk is None or brk > len(after) - 8:
            continue

        # the retest: a later bar dips to the level from above and does not close under
        # The retest must be a genuine return to the level, not the very next
        # bar still wobbling around the break. At least three bars later, and
        # price must have travelled away from the level in between — otherwise
        # "break then retest" is just one noisy session.
        post = after[brk + 1:]
        away = False
        ret = None
        for j, b in enumerate(post):
            if b["l"] > lvl + band * 4:
                away = True
            if away and j >= 2 and b["l"] <= lvl + band * 1.6 and b["c"] >= lvl - band:
                ret = j
                break
        if ret is None or ret > len(post) - 3:
            continue
        # and it holds — no close below the level after the retest
        held = all(b["c"] >= lvl - band * 1.5 for b in post[ret:])
        if not held:
            continue

        bi_brk = len(base) + brk
        bi_ret = len(base) + brk + 1 + ret
        if bi_ret > n - 3:                        # retest must be inside the setup
            continue
        # Reward a clean, well-separated retest over a merely long touch list.
        strength = min(len(touches), 6) + (bi_ret - bi_brk) * 0.6
        if best is None or strength > best[0]:
            best = (
                strength,
                round(lvl, 2),
                {
                    "breakAt": bi_brk,
                    "retestAt": bi_ret,
                    "touches": len(touches),
                },
            )
    return best


DETECTORS = {"breakout-retest": breakout_retest}

COPY = {
    "breakout-retest": {
        "patternName": "BREAKOUT & RETEST",
        "levelLabelFmt": "RESISTANCE {lvl} · HELD {n}x",
        "answer": "BUY",
        "answerLine": "The level that rejected price became the floor it bounced from.",
        "ruleTitle": "Why the retest matters",
        "ruleText": (
            "A close above a level that has held repeatedly flips it from resistance to "
            "support. The trade is not the break — most breaks get sold. It is the RETEST: "
            "price comes back to the level and holds above it on a closing basis. No retest, "
            "or a close back below, and there is no setup."
        ),
    }
}


def main():
    if "--list" in sys.argv:
        for k in DETECTORS:
            print(k)
        return 0
    if len(sys.argv) < 2:
        print("give a pattern key, or --list", file=sys.stderr)
        return 1
    key = sys.argv[1]
    if key not in DETECTORS:
        print(f"no detector for '{key}'. Try --list.", file=sys.stderr)
        return 1
    det, copy = DETECTORS[key], COPY[key]

    found = []
    for fname in sorted(f for f in os.listdir(PRICES) if f.endswith(".json")):
        src, bars, bad = load(fname)
        if src.get("interval") != "1d" or len(bars) < SETUP + REVEAL + 5:
            continue
        for i in range(len(bars) - SETUP - REVEAL):
            if any(j in bad for j in range(i, i + SETUP + REVEAL)):
                continue
            w = bars[i : i + SETUP]
            r = det(w)
            if not r:
                continue
            # Re-anchor: the interesting question is asked AT the retest, not
            # twenty bars later. Setup ends two bars after price comes back to
            # the level, so the viewer is looking at "it returned - does it
            # hold?" rather than at an outcome that already resolved.
            abs_ret = i + r[2]["retestAt"]
            end = abs_ret + 2
            start = end - SETUP
            if start < 0 or end + REVEAL > len(bars):
                continue
            if any(j in bad for j in range(start, end + REVEAL)):
                continue
            w = bars[start:end]
            r = (r[0], r[1], {**r[2],
                              "breakAt": r[2]["breakAt"] + i - start,
                              "retestAt": abs_ret - start})
            rev = bars[end : end + REVEAL]
            # the reveal has to actually go the way the answer claims
            if copy["answer"] == "BUY" and rev[-1]["c"] <= w[-1]["c"]:
                continue
            if copy["answer"] == "SELL" and rev[-1]["c"] >= w[-1]["c"]:
                continue
            found.append((r[0], start, r[1], r[2], src, w, rev))

    if not found:
        print(f"no real occurrence of '{key}' found in {PRICES}", file=sys.stderr)
        return 2

    found.sort(key=lambda x: -x[0])
    score, i, lvl, extras, src, w, rev = found[0]
    allbars = w + rev
    move = (rev[-1]["c"] / w[-1]["c"] - 1) * 100

    print(f"{len(found)} real occurrences; best scores {score:.2f}")
    print(f"  {src['symbol']} {src['interval']}  {w[0]['date']} -> {rev[-1]['date']}")
    print(f"  resistance {lvl}, held {extras['touches']}x")
    print(f"  break at bar {extras['breakAt']} ({w[extras['breakAt']]['date']}), "
          f"retest at {extras['retestAt']} ({w[extras['retestAt']]['date']})")
    print(f"  reveal: {w[-1]['c']} -> {rev[-1]['c']} = {move:+.1f}%")

    fixture = {
        "kick": "REAL CHART",
        "indexLabel": "#82",
        "subject": f"{src['symbol']} · DAILY · {w[0]['date']} → {rev[-1]['date']}",
        "patternName": copy["patternName"],
        "levelPrice": lvl,
        "levelLabel": copy["levelLabelFmt"].format(lvl=lvl, n=extras["touches"]),
        "answer": copy["answer"],
        "answerLabel": f"IT HELD  {move:+.1f}%",
        "answerLine": copy["answerLine"],
        "ruleTitle": copy["ruleTitle"],
        "ruleText": copy["ruleText"],
        "footer": (f"{src['symbol']} daily bars, IBKR, pulled {src['retrieved_at'][:10]} · "
                   f"Educational only — not financial advice · Historical example — DYOR"),
        "revealFrom": len(w),
        "patternSpan": max(2, len(w) - extras["retestAt"]),   # break -> retest -> now
        "durationInFrames": DURATION,
        "candles": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in allbars],
    }
    out = os.path.join(FIXDIR, f"real_{key.replace('-', '_')}.json")
    os.makedirs(FIXDIR, exist_ok=True)
    json.dump(fixture, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n{len(allbars)} candles -> {os.path.relpath(out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
