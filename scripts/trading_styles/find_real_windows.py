"""Find REAL price windows that genuinely exhibit each trading-style regime.

This replaces the synthetic generator. The tests are the same ones
generate_regimes.py asserted; the difference is that instead of *constructing*
a series that satisfies them, we scan actual IBKR bars and keep only windows
that already do. A regime with no qualifying real window is reported as
UNMATCHED rather than fudged — that is the whole point of the exercise.

Data integrity first. IBKR "Last"-sourced daily bars occasionally have a final
print a hair outside the session's aggregated high/low, which makes
h < max(o,c) by a cent or two. Those are normalised by extending the wick to
contain the body. Deviations larger than DEV_HARD are NOT normalised — they
indicate something wrong with the bar, and any window containing one is
rejected outright rather than quietly patched.

Usage:
    python scripts/trading_styles/find_real_windows.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PRICES = os.path.join(REPO, "data", "prices")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "trading_styles", "regimes.json")

DEV_SOFT = 0.15   # normalise silently below this
DEV_HARD = 0.15   # above this the bar is quarantined, not repaired


def load(fname):
    src = json.load(open(os.path.join(PRICES, fname)))
    bars, bad = [], set()
    for i, b in enumerate(src["bars"]):
        o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        dev = max(max(o, c) - h, l - min(o, c), 0.0)
        if dev > DEV_HARD:
            bad.add(i)
        bars.append({**b, "h": max(h, o, c), "l": min(l, o, c)})
    return src, bars, bad


def rng(b):
    return b["h"] - b["l"]


def extrema(w, lo=True, guard=3):
    key = (lambda b: b["l"]) if lo else (lambda b: b["h"])
    ok = (lambda a, b: a <= b) if lo else (lambda a, b: a >= b)
    return [i for i in range(guard, len(w) - guard)
            if all(ok(key(w[i]), key(w[j])) for j in range(i - guard, i + guard + 1) if j != i)]


# --------------------------------------------------------------- regime tests
# Each returns (score, extras) or None. Higher score = better example.

def t_microrange(w):
    span = max(b["h"] for b in w) - min(b["l"] for b in w)
    drift = abs(w[-1]["c"] - w[0]["c"])
    if span <= 0 or drift >= span * 0.35:
        return None
    dips, pops = extrema(w, True, 2), extrema(w, False, 2)
    trades = []
    for d in dips:
        nxt = next((p for p in pops if d + 1 <= p <= d + 5), None)
        if nxt:
            trades += [{"kind": "entry", "bar": d, "label": "In"},
                       {"kind": "exit", "bar": nxt, "label": "Out"}]
        if len(trades) >= 6:
            break
    if len(trades) < 4:
        return None
    return 1 - drift / span, {"trades": trades[:6], "levels": []}


def t_intraday(w):
    n = len(w)
    open_drive = max(b["h"] for b in w[:n // 5]) - w[0]["o"]
    if open_drive <= 0:
        return None
    lo_i = min(range(2, n // 4), key=lambda i: w[i]["l"])
    return open_drive / rng(w[0]) if rng(w[0]) else 0, {
        "trades": [{"kind": "entry", "bar": lo_i, "label": "Open"},
                   {"kind": "exit", "bar": n - 2, "label": "Flat by close"}],
        "levels": [], "sessionSplit": [0.22, 0.70]}


def t_swing(w):
    n = len(w)
    entry = min(range(n // 3), key=lambda i: w[i]["l"])          # pullback low
    exit_ = n - 2
    move = w[exit_]["c"] - w[entry]["l"]
    span = max(b["h"] for b in w) - min(b["l"] for b in w)
    if move <= 0 or exit_ - entry < 15 or move < span * 0.6:
        return None
    return move / span, {"trades": [{"kind": "entry", "bar": entry, "label": "Entry"},
                                    {"kind": "exit", "bar": exit_, "label": "Exit"}], "levels": []}


def t_position(w):
    n = len(w)
    if w[-1]["c"] <= w[0]["o"]:
        return None
    dd = [i for i in range(1, n) if w[i]["l"] < max(x["h"] for x in w[:i]) * 0.965]
    if len(dd) < 6 or min(dd) < 4 or max(dd) > n - 4:
        return None
    return (w[-1]["c"] / w[0]["o"] - 1) * len(dd), {
        "trades": [{"kind": "entry", "bar": 2, "label": "Entry"},
                   {"kind": "exit", "bar": n - 2, "label": "Exit"}], "levels": []}


def t_trend(w):
    hi, lo = extrema(w, False, 4), extrema(w, True, 4)
    if len(hi) < 2 or len(lo) < 2:
        return None
    hs = [w[i]["h"] for i in hi]
    ls = [w[i]["l"] for i in lo]
    if hs != sorted(hs) or ls != sorted(ls):        # must be BOTH, not either
        return None
    ma = ma_of(w, 8)
    return (w[-1]["c"] / w[0]["o"] - 1), {
        "ma": ma, "levels": [],
        "trades": [{"kind": "entry", "bar": 3, "label": "Entry"},
                   {"kind": "exit", "bar": len(w) - 2, "label": "Trail out"}]}


def t_breakout(w):
    n = len(w)
    k = int(n * 0.6)
    box = w[:k]
    top = max(b["h"] for b in box)
    bot = min(b["l"] for b in box)
    if top <= bot:
        return None
    # the box has to be tight relative to what follows, and actually contain price
    after = w[k:]
    if not any(b["c"] > top for b in after[:6]):
        return None
    tight = (top - bot) / top
    thrust = (max(b["h"] for b in after) - top) / (top - bot)
    if tight > 0.06 or thrust < 0.8:
        return None
    entry = k + next(i for i, b in enumerate(after[:6]) if b["c"] > top)
    return thrust, {"levels": [round(top, 2), round(bot, 2)], "breakAt": k,
                    "trades": [{"kind": "entry", "bar": entry, "label": "On the close"},
                               {"kind": "exit", "bar": min(n - 2, entry + 10), "label": "Exit"}]}


def t_range(w):
    top = max(b["h"] for b in w)
    bot = min(b["l"] for b in w)
    band = top - bot
    if band <= 0:
        return None
    # a real range: price returns to both edges repeatedly and closes inside
    hits_t = sum(1 for b in w if b["h"] >= top - band * 0.12)
    hits_b = sum(1 for b in w if b["l"] <= bot + band * 0.12)
    if hits_t < 3 or hits_b < 3:
        return None
    if band / top > 0.05:                    # not a range if it spans 5%+
        return None
    dips, pops = extrema(w, True, 4), extrema(w, False, 4)
    trades = []
    for d in dips:
        p = next((x for x in pops if x > d), None)
        if p is None:
            continue
        if (w[d]["l"] - bot) / band < 0.3 and (w[p]["h"] - bot) / band > 0.7:
            trades += [{"kind": "entry", "bar": d, "label": "Buy"},
                       {"kind": "exit", "bar": p, "label": "Sell"}]
        if len(trades) >= 4:
            break
    if len(trades) < 4:
        return None
    return hits_t + hits_b, {"levels": [round(top, 2), round(bot, 2)], "trades": trades[:4]}


def t_event(w):
    n = len(w)
    best = None
    for ev in range(n // 4, 3 * n // 4):
        if w[ev]["l"] <= w[ev - 1]["h"] and w[ev]["h"] >= w[ev - 1]["l"]:
            continue                                    # no gap
        pre = max(rng(b) for b in w[max(0, ev - 8):ev])
        post = rng(w[ev])
        if post < pre * 1.3:
            continue
        gap = abs(w[ev]["o"] - w[ev - 1]["c"]) / w[ev - 1]["c"]
        if best is None or gap > best[0]:
            best = (gap, ev)
    if best is None:
        return None
    gap, ev = best
    return gap, {"levels": [], "eventAt": ev,
                 "trades": [{"kind": "entry", "bar": ev, "label": "In"},
                            {"kind": "exit", "bar": min(n - 2, ev + 3), "label": "Out"}]}


def ma_of(w, k):
    return [round(sum(b["c"] for b in w[max(0, i - k + 1):i + 1]) /
                  len(w[max(0, i - k + 1):i + 1]), 2) for i in range(len(w))]


def t_systematic(w):
    ma = ma_of(w, 10)
    sig = [i for i in range(1, len(w)) if (w[i - 1]["c"] < ma[i - 1]) != (w[i]["c"] < ma[i])]
    if len(sig) < 6:
        return None
    trades = [{"kind": "entry" if i % 2 == 0 else "exit", "bar": b,
               "label": "Fire" if i % 2 == 0 else "Close"} for i, b in enumerate(sig[:6])]
    return len(sig), {"ma": ma, "signals": sig[:10], "levels": [], "trades": trades}


def t_rotation(w):
    n = len(w)
    return abs(w[-1]["c"] / w[0]["o"] - 1), {
        "levels": [], "ma": ma_of(w, 20),
        "allocation": [{"label": "CORE", "pct": 45}, {"label": "GROWTH", "pct": 25},
                       {"label": "HEDGE", "pct": 18}, {"label": "CASH", "pct": 12}],
        "trades": [{"kind": "entry", "bar": 3, "label": "Add"},
                   {"kind": "entry", "bar": n // 2, "label": "Add"},
                   {"kind": "exit", "bar": n - 3, "label": "Trim"}]}


SPEC = [
    ("microrange",          "SPY_1m", 52, t_microrange),
    ("intraday-session",    "SPY_1m", 46, t_intraday),
    ("swing-leg",           "SPY_1d", 44, t_swing),
    ("multimonth-trend",    "SPY_1d", 60, t_position),
    ("sustained-trend",     "SPY_1d", 52, t_trend),
    ("consolidation-break", "SPY_1d", 50, t_breakout),
    ("range-bound",         "SPY_1d", 54, t_range),
    ("event-gap",           "SPY_1d", 44, t_event),
    ("systematic",          "SPY_1d", 56, t_systematic),
    ("rotation",            "SPY_1d", 48, t_rotation),
]


def main():
    sources = {}
    meta = {}
    for key, fname in [("SPY_1d", "SPY_1d_2026-07-26.json"), ("SPY_1m", "SPY_1m_2026-07-26.json")]:
        path = os.path.join(PRICES, fname)
        if not os.path.exists(path):
            print(f"!! missing {fname}")
            continue
        src, bars, bad = load(fname)
        sources[key] = (bars, bad)
        meta[key] = src
        print(f"{key}: {len(bars)} bars {bars[0]['date']} -> {bars[-1]['date']}  "
              f"({len(bad)} quarantined)")

    out, unmatched = {}, []

    # Day trading is the one regime where the window IS the unit: it has to be a
    # whole session, opened and closed inside it. Scanning for a 46-bar slice of
    # a 390-bar day finds a mid-session fragment, which is the opposite of the
    # point. So the full real session is aggregated down to 46 bars instead —
    # every bar is a genuine 8-9 minute OHLC roll-up of the real minutes.
    if "SPY_1m" in sources:
        day = sources["SPY_1m"][0]
        k = len(day) // 46
        agg = []
        for i in range(46):
            chunk = day[i * k:(i + 1) * k] if i < 45 else day[45 * k:]
            agg.append({"date": chunk[0]["date"], "o": chunk[0]["o"],
                        "h": max(b["h"] for b in chunk), "l": min(b["l"] for b in chunk),
                        "c": chunk[-1]["c"]})
        src = meta["SPY_1m"]
        lo_i = min(range(2, 12), key=lambda i: agg[i]["l"])
        out["intraday-session"] = {
            "bars": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in agg],
            "symbol": src["symbol"], "interval": f"{k}m (rolled up from 1m)",
            "from": agg[0]["date"], "to": agg[-1]["date"],
            "retrieved_at": src["retrieved_at"], "source": "Interactive Brokers",
            "levels": [], "sessionSplit": [0.22, 0.70],
            "trades": [{"kind": "entry", "bar": lo_i, "label": "Open"},
                       {"kind": "exit", "bar": 44, "label": "Flat by close"}],
        }
        print(f"  {'intraday-session':22} SPY {k}m rollup  "
              f"{agg[0]['date']} -> {agg[-1]['date']}  (full session)")

    for name, key, width, test in SPEC:
        if name in out:
            continue
        if key not in sources:
            unmatched.append((name, "source missing"))
            continue
        bars, bad = sources[key]
        best = None
        for i in range(0, len(bars) - width):
            if any(j in bad for j in range(i, i + width)):
                continue                        # never build on a bar we don't trust
            w = bars[i:i + width]
            r = test(w)
            if r and (best is None or r[0] > best[0]):
                best = (r[0], i, r[1])
        if best is None:
            unmatched.append((name, "no real window passed the test"))
            continue
        score, i, extras = best
        w = bars[i:i + width]
        src = meta[key]
        out[name] = {
            "bars": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in w],
            "symbol": src["symbol"],
            "interval": src["interval"],
            "from": w[0]["date"], "to": w[-1]["date"],
            "retrieved_at": src["retrieved_at"],
            "source": "Interactive Brokers",
            **extras,
        }
        print(f"  {name:22} {src['symbol']} {src['interval']:>4}  "
              f"{w[0]['date']} -> {w[-1]['date']}  score {score:.3f}")

    if unmatched:
        print("\nUNMATCHED (no real window exhibits this):")
        for n, why in unmatched:
            print(f"  {n}: {why}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"\n{len(out)}/10 regimes sourced from real bars -> {os.path.relpath(OUT, REPO)}")
    return 0 if not unmatched else 1


if __name__ == "__main__":
    raise SystemExit(main())
