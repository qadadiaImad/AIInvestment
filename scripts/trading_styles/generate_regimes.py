"""Generate the ten chart simulations for the trading-styles explainer.

One regime per trading style. Every series is produced HERE, deterministically,
from a seeded PRNG — not by a language model. That is a deliberate split of
labour: models write the copy, Python writes the numbers. Every prior attempt at
model-authored OHLC in this repo produced geometry that looked right and was
wrong (see scripts/ta_quiz/validate.py and the trigger-displacement repair), and
a chart that doesn't show what the narration claims is worse than no chart.

Each regime is built from an explicit price path, then the path is turned into
bars with wicks. Every bar is checked for OHLC integrity, and each regime
asserts the structural claim the video makes about it — a range that doesn't
touch its own boundaries, or a "breakout" that never clears its consolidation,
raises instead of rendering.

Usage:
    python scripts/trading_styles/generate_regimes.py
"""
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "trading_styles", "regimes.json")


def bars_from_path(path, rng, wick=0.35, body_noise=0.25):
    """Turn a close-price path into OHLC bars.

    Each bar opens at the previous close and closes at its path value; the
    wicks extend beyond the body by a fraction of the bar's own move, so a
    quiet bar gets small wicks and an active bar gets large ones. That keeps
    the texture honest: wick size tracks activity rather than being decorative.
    """
    out = []
    prev = path[0]
    for i, c in enumerate(path):
        o = prev
        move = abs(c - o)
        # A bar that barely moves still trades a little, or every doji is a line.
        scale = max(move, (max(path) - min(path)) * 0.012)
        o = o + rng.uniform(-body_noise, body_noise) * scale
        hi = max(o, c) + rng.uniform(0.05, wick) * scale
        lo = min(o, c) - rng.uniform(0.05, wick) * scale
        out.append({"o": round(o, 2), "h": round(hi, 2), "l": round(lo, 2), "c": round(c, 2)})
        prev = c
    return out


def troughs(bars, lo=True, guard=3):
    """Indices of local extrema, so trades can be placed on the actual series."""
    key = (lambda b: b["l"]) if lo else (lambda b: b["h"])
    cmp = (lambda a, b: a <= b) if lo else (lambda a, b: a >= b)
    out = []
    for i in range(guard, len(bars) - guard):
        if all(cmp(key(bars[i]), key(bars[j])) for j in range(i - guard, i + guard + 1) if j != i):
            out.append(i)
    return out


def check(bars, name):
    for i, b in enumerate(bars):
        assert b["h"] >= max(b["o"], b["c"]) - 1e-9, f"{name} bar {i}: high below body"
        assert b["l"] <= min(b["o"], b["c"]) + 1e-9, f"{name} bar {i}: low above body"
        assert b["h"] >= b["l"], f"{name} bar {i}: inverted"
    return bars


# --------------------------------------------------------------- regimes
# Each returns (bars, extras). `extras` carries anything the renderer needs to
# draw on top: horizontal levels, an event bar index, a moving average.

def microrange(rng):
    """Scalping: a tight band, lots of small two-way bars, no net progress."""
    base, n = 100.0, 52
    path = [base + math.sin(i / 2.4) * 0.55 + rng.uniform(-0.28, 0.28) for i in range(n)]
    bars = bars_from_path(path, rng, wick=0.55)
    span = max(b["h"] for b in bars) - min(b["l"] for b in bars)
    drift = abs(path[-1] - path[0])
    assert drift < span * 0.45, "microrange drifted - that is not a scalping tape"
    dips, pops = troughs(bars, True, 2), troughs(bars, False, 2)
    trades = []
    for d in dips[:3]:
        nxt = next((p for p in pops if p > d + 1), None)
        if nxt and nxt - d <= 5:
            trades += [{"kind": "entry", "bar": d, "label": "In"},
                       {"kind": "exit", "bar": nxt, "label": "Out"}]
    assert trades, "no quick round-trips found"
    return bars, {"levels": [], "trades": trades[:6],
                  "note": "range compresses; the edge is frequency, not distance"}


def intraday_session(rng):
    """Day trading: an open drive, a midday lull, a close — flat by the bell."""
    n = 46
    path = []
    for i in range(n):
        t = i / (n - 1)
        if t < 0.22:            # opening drive
            v = 100 + t / 0.22 * 3.4
        elif t < 0.70:          # midday chop
            v = 103.4 + math.sin((t - 0.22) * 14) * 0.9 - (t - 0.22) * 1.1
        else:                   # afternoon trend into the close
            v = 102.6 + (t - 0.70) / 0.30 * 2.6
        path.append(v + rng.uniform(-0.22, 0.22))
    bars = bars_from_path(path, rng)
    assert max(path[:12]) > path[0] + 2, "no opening drive"
    entry = min(range(2, 10), key=lambda i: bars[i]["l"])
    exit_ = len(bars) - 3
    return bars, {"levels": [], "sessionSplit": [0.22, 0.70],
                  "trades": [{"kind": "entry", "bar": entry, "label": "Open"},
                             {"kind": "exit", "bar": exit_, "label": "Flat by close"}],
                  "note": "one session, opened and closed inside it"}


def swing_leg(rng):
    """Swing: a pullback, then one clean multi-day leg held through noise."""
    n = 44
    path = []
    for i in range(n):
        t = i / (n - 1)
        if t < 0.28:
            v = 100 - t / 0.28 * 4.2                       # the pullback
        else:
            v = 95.8 + (t - 0.28) / 0.72 * 13.5            # the leg
            v += math.sin((t - 0.28) * 18) * 1.15          # noise you must sit through
        path.append(v + rng.uniform(-0.35, 0.35))
    bars = bars_from_path(path, rng)
    assert path[-1] > path[0] + 8, "swing leg did not travel"
    entry = min(range(len(bars)), key=lambda i: bars[i]["l"])   # the pullback low
    exit_ = len(bars) - 3
    assert exit_ - entry > 15, "swing held for too few bars to read as a swing"
    return bars, {"levels": [],
                  "trades": [{"kind": "entry", "bar": entry, "label": "Entry"},
                             {"kind": "exit", "bar": exit_, "label": "Exit"}],
                  "note": "one leg, held across the noise inside it"}


def multimonth_trend(rng):
    """Position: a long grind up with two real drawdowns that are held through."""
    n = 60
    path = []
    for i in range(n):
        t = i / (n - 1)
        v = 100 + t * 34
        # Wide enough to last several bars — a one-bar dip is not a drawdown you
        # have to sit through, and sitting through it is the entire point.
        v -= 12.0 * math.exp(-((t - 0.34) ** 2) / 0.006)   # drawdown 1
        v -= 15.0 * math.exp(-((t - 0.71) ** 2) / 0.006)   # drawdown 2
        path.append(v + rng.uniform(-0.7, 0.7))
    bars = bars_from_path(path, rng, wick=0.4)
    dds = [i for i in range(1, n) if path[i] < max(path[:i]) - 5]
    assert len(dds) > 6, f"no drawdown deep enough to be worth holding through ({len(dds)})"
    entry, exit_ = 3, len(bars) - 3
    # The trade must actually span both drawdowns or the scene claims something
    # the chart does not show.
    assert entry < min(dds) and exit_ > max(dds), "position does not span the drawdowns"
    return bars, {"levels": [],
                  "trades": [{"kind": "entry", "bar": entry, "label": "Entry"},
                             {"kind": "exit", "bar": exit_, "label": "Exit"}],
                  "note": "two drawdowns, neither one exited"}


def sustained_trend(rng):
    """Trend: higher highs and higher lows, with the trend line that defines it."""
    n = 56
    path, peak, trough = [], [], []
    for i in range(n):
        t = i / (n - 1)
        v = 100 + t * 26 + math.sin(t * 11) * 2.6
        path.append(v + rng.uniform(-0.4, 0.4))
    bars = bars_from_path(path, rng)
    # verify the structure the narration claims: higher highs AND higher lows
    for i in range(4, n - 4):
        if all(path[i] >= path[j] for j in range(i - 4, i + 5)):
            peak.append(path[i])
        if all(path[i] <= path[j] for j in range(i - 4, i + 5)):
            trough.append(path[i])
    assert len(peak) >= 2 and peak == sorted(peak), "not higher highs"
    assert len(trough) >= 2 and trough == sorted(trough), "not higher lows"
    ma = [round(sum(path[max(0, i - 8):i + 1]) / len(path[max(0, i - 8):i + 1]), 2) for i in range(n)]
    return bars, {"levels": [], "ma": ma,
                  "trades": [{"kind": "entry", "bar": 4, "label": "Entry"},
                             {"kind": "exit", "bar": n - 3, "label": "Trail out"}],
                  "note": "higher highs and higher lows, still intact"}


def consolidation_break(rng):
    """Breakout: a genuine box, then a close beyond it, then continuation."""
    n = 50
    top, bot, brk = 103.0, 99.4, 0.62
    path = []
    for i in range(n):
        t = i / (n - 1)
        if t < brk:
            v = 101.2 + math.sin(i / 1.9) * 1.55 + rng.uniform(-0.2, 0.2)
            v = min(top - 0.15, max(bot + 0.15, v))        # genuinely contained
        else:
            v = top + (t - brk) / (1 - brk) * 8.5 + rng.uniform(-0.3, 0.3)
        path.append(v)
    bars = bars_from_path(path, rng)
    k = int(n * brk)
    assert all(b["c"] <= top for b in bars[:k]), "box was not respected before the break"
    assert bars[k + 2]["c"] > top, "no close above the box"
    entry = k + 2                      # entry on the CLOSE beyond the box, not the wick
    exit_ = min(n - 3, entry + 12)
    return bars, {"levels": [round(top, 2), round(bot, 2)], "breakAt": k,
                  "trades": [{"kind": "entry", "bar": entry, "label": "On the close"},
                             {"kind": "exit", "bar": exit_, "label": "Exit"}],
                  "note": "contained, then a CLOSE beyond the box"}


def range_bound(rng):
    """Range: repeated touches of both boundaries, no breakout."""
    n = 54
    top, bot = 106.0, 98.0
    mid, amp = (top + bot) / 2, (top - bot) / 2
    path = [mid + math.sin(i / 4.3) * amp * 0.92 + rng.uniform(-0.3, 0.3) for i in range(n)]
    bars = bars_from_path(path, rng)
    hits_top = sum(1 for b in bars if b["h"] >= top - 0.9)
    hits_bot = sum(1 for b in bars if b["l"] <= bot + 0.9)
    assert hits_top >= 2 and hits_bot >= 2, f"range not tested both sides ({hits_top}/{hits_bot})"
    assert max(b["c"] for b in bars) <= top and min(b["c"] for b in bars) >= bot, "range broke"
    dips, pops = troughs(bars, True, 4), troughs(bars, False, 4)
    trades = []
    for d in dips[:2]:
        p = next((x for x in pops if x > d), None)
        if p:
            trades += [{"kind": "entry", "bar": d, "label": "Buy"},
                       {"kind": "exit", "bar": p, "label": "Sell"}]
    assert len(trades) >= 4, "a range trade needs at least two round-trips to read"
    # The claim of the scene: buy LOW in the range, sell HIGH. Verify it.
    for t in trades:
        v = bars[t["bar"]]["l"] if t["kind"] == "entry" else bars[t["bar"]]["h"]
        f = (v - bot) / (top - bot)
        if t["kind"] == "entry":
            assert f < 0.35, f"'Buy' marker at {f:.0%} of the range - that is not support"
        else:
            assert f > 0.65, f"'Sell' marker at {f:.0%} of the range - that is not resistance"
    return bars, {"levels": [top, bot], "trades": trades[:4],
                  "note": "both boundaries tested, neither broken"}


def event_gap(rng):
    """News: quiet, a gap on the print, a violent two-way bar, then a new level."""
    n = 44
    ev = 20
    path = []
    for i in range(n):
        if i < ev:
            path.append(100 + rng.uniform(-0.3, 0.3))
        elif i == ev:
            path.append(107.4)                             # the gap
        elif i < ev + 5:
            path.append(107.4 + math.sin((i - ev) * 2.2) * 2.4 + rng.uniform(-0.6, 0.6))
        else:
            path.append(106.2 + (i - ev - 5) * 0.13 + rng.uniform(-0.5, 0.5))
    bars = bars_from_path(path, rng, wick=0.8)
    # A gap is an OPEN above the prior high, not merely a big up-bar. The path
    # builder opens every bar at the previous close, so the event bar has to be
    # rewritten explicitly or it renders as a long green candle instead.
    prior_high = bars[ev - 1]["h"]
    gap_open = round(prior_high + 5.4, 2)
    bars[ev] = {
        "o": gap_open,
        "h": round(max(gap_open, path[ev]) + 2.1, 2),
        "l": round(min(gap_open, path[ev]) - 0.6, 2),
        "c": round(path[ev], 2),
    }
    assert bars[ev]["l"] > bars[ev - 1]["h"], "no actual gap on the event bar"
    pre = max(b["h"] for b in bars[:ev]) - min(b["l"] for b in bars[:ev])
    post = max(b["h"] for b in bars[ev:ev + 5]) - min(b["l"] for b in bars[ev:ev + 5])
    assert post > pre * 2.5, "event did not expand range - that is not a news reaction"
    return bars, {"levels": [], "eventAt": ev,
                  "trades": [{"kind": "entry", "bar": ev + 1, "label": "In"},
                             {"kind": "exit", "bar": ev + 4, "label": "Out"}],
                  "note": "range expands the instant the print lands"}


def systematic(rng):
    """Algorithmic: the same rule fires repeatedly, without discretion."""
    n = 58
    path = [100 + i * 0.22 + math.sin(i / 3.1) * 2.4 + rng.uniform(-0.3, 0.3) for i in range(n)]
    bars = bars_from_path(path, rng)
    ma = [round(sum(path[max(0, i - 6):i + 1]) / len(path[max(0, i - 6):i + 1]), 2) for i in range(n)]
    # every cross of the average is a signal — mechanical, no judgement
    sigs = [i for i in range(1, n) if (path[i - 1] < ma[i - 1]) != (path[i] < ma[i])]
    assert len(sigs) >= 5, "a rule that fires twice does not read as systematic"
    # Alternating in/out on the same rule - no discretion anywhere.
    trades = [{"kind": "entry" if i % 2 == 0 else "exit", "bar": b,
               "label": "Fire" if i % 2 == 0 else "Close"} for i, b in enumerate(sigs[:6])]
    return bars, {"levels": [], "ma": ma, "signals": sigs[:8], "trades": trades,
                  "note": "one rule, fired every time it triggered"}


def rotation(rng):
    """Portfolio: position size is the variable, not the entry."""
    n = 48
    path = [100 + i * 0.30 + math.sin(i / 6.5) * 3.0 + rng.uniform(-0.4, 0.4) for i in range(n)]
    bars = bars_from_path(path, rng)
    return bars, {
        "levels": [],
        "allocation": [
            {"label": "CORE", "pct": 45}, {"label": "GROWTH", "pct": 25},
            {"label": "HEDGE", "pct": 18}, {"label": "CASH", "pct": 12},
        ],
        "trades": [{"kind": "entry", "bar": 4, "label": "Add"},
                   {"kind": "entry", "bar": 20, "label": "Add"},
                   {"kind": "exit", "bar": 40, "label": "Trim"}],
        "note": "the same chart, sized differently",
    }


REGIMES = {
    "microrange": microrange, "intraday-session": intraday_session,
    "swing-leg": swing_leg, "multimonth-trend": multimonth_trend,
    "sustained-trend": sustained_trend, "consolidation-break": consolidation_break,
    "range-bound": range_bound, "event-gap": event_gap,
    "systematic": systematic, "rotation": rotation,
}


def main():
    out = {}
    for i, (name, fn) in enumerate(REGIMES.items()):
        rng = random.Random(1000 + i * 37)   # fixed per regime: renders are reproducible
        bars, extras = fn(rng)
        check(bars, name)
        out[name] = {"bars": bars, **extras}
        span = max(b["h"] for b in bars) - min(b["l"] for b in bars)
        print(f"{name:22} {len(bars):>3} bars  range {span:6.2f}  {extras.get('note','')}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"\n-> {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
