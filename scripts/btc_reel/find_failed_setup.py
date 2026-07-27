"""Find a REAL bullish setup on IBIT that failed, plus the structure to draw.

The story the reel tells is "the obvious answer was wrong": a textbook bullish
setup at a level that had held repeatedly, which any reasonable reader of the
chart would call a bounce, and which then broke. That only teaches something if
it actually happened, so this scans real bars for it rather than composing one.

Three things are produced, all derived from the bars:

  structure   swing pivots, ranked support/resistance zones, and at most one
              trendline - the things the reel draws while the chart builds.
  setup       the support zone, the bullish trigger bar that formed at it, and
              the entry/stop/target that follow from them.
  outcome     what the next bars did. The window is only accepted if the stop
              was hit BEFORE the target, because that is the story.

Nothing is nudged. If no window in the series satisfies all of it, that is
reported as UNMATCHED rather than relaxed until something passes - the whole
point of the piece is that the loss was real.

Usage:
    python scripts/btc_reel/find_failed_setup.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "data", "prices", "IBIT_1d_2026-07-27.json")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "btc_reel", "setup.json")

SETUP_BARS = 70      # context the viewer sees before the decision
REVEAL_BARS = 14     # what happens next
PIVOT_N = 3          # fractal half-width: a swing high is the highest of 2N+1
ZONE_BAND = 0.022    # 2.2% - a level is a zone, not a line
DEV_HARD = 0.15


# ----------------------------------------------------------------- structure

def pivots(bars, n=PIVOT_N):
    """Fractal swing points. A swing high is the highest high of 2n+1 bars.

    Chosen over ZigZag because it is causal and parameter-light: each pivot is
    confirmed n bars after it forms, which is exactly when the reel is allowed
    to draw it. ZigZag would let the chart mark a pivot before the data that
    confirms it has printed, which reads as the chart knowing the future.
    """
    hi, lo = [], []
    for i in range(n, len(bars) - n):
        w = bars[i - n:i + n + 1]
        if bars[i]["h"] >= max(b["h"] for b in w):
            hi.append(i)
        if bars[i]["l"] <= min(b["l"] for b in w):
            lo.append(i)
    return hi, lo


def zones(bars, idxs, use_high, band=ZONE_BAND):
    """Cluster pivots into price zones, scored by touches and recency.

    Score is touches + a recency bonus, because a level tested three times last
    month matters more to the next bar than one tested four times a year ago.
    Zones are then de-overlapped so the reel never draws two lines that are
    really the same level.
    """
    key = (lambda b: b["h"]) if use_high else (lambda b: b["l"])
    pts = sorted(((key(bars[i]), i) for i in idxs), reverse=True)
    out = []
    used = set()
    for price, i in pts:
        if i in used:
            continue
        members = [(p, j) for p, j in pts if abs(p - price) <= price * band and j not in used]
        if len(members) < 2:
            continue
        for _, j in members:
            used.add(j)
        lvl = sum(p for p, _ in members) / len(members)
        last = max(j for _, j in members)
        recency = last / max(1, len(bars) - 1)
        out.append({
            "price": round(lvl, 2),
            "touches": len(members),
            "bars": sorted(j for _, j in members),
            "lastTouch": last,
            "score": round(len(members) + recency * 2.5, 3),
        })
    out.sort(key=lambda z: -z["score"])
    # drop zones that sit inside a stronger one
    keep = []
    for z in out:
        if all(abs(z["price"] - k["price"]) > k["price"] * band for k in keep):
            keep.append(z)
    return keep


def trendline(bars, idxs, use_high):
    """Best straight line through swing points, by touches then by span.

    Every pair of pivots defines a candidate; a candidate is valid only if no
    bar CLOSES through it (wicks are allowed to pierce - that is what makes a
    trendline a zone of interest rather than a wall). The winner is the line
    the most pivots sit on.
    """
    key = (lambda b: b["h"]) if use_high else (lambda b: b["l"])
    best = None
    for a in range(len(idxs)):
        for b in range(a + 1, len(idxs)):
            i, j = idxs[a], idxs[b]
            if j - i < 8:
                continue
            m = (key(bars[j]) - key(bars[i])) / (j - i)
            c = key(bars[i]) - m * i
            at = lambda x: m * x + c
            # no closes through it, between the anchors and after
            bad = False
            for k in range(i, len(bars)):
                v = at(k)
                if use_high and bars[k]["c"] > v * 1.006:
                    bad = True
                    break
                if not use_high and bars[k]["c"] < v * 0.994:
                    bad = True
                    break
            if bad:
                continue
            touches = sum(
                1 for k in idxs if i <= k <= len(bars) - 1 and abs(key(bars[k]) - at(k)) <= at(k) * 0.012
            )
            if touches < 2:
                continue
            score = touches * 10 + (j - i)
            if best is None or score > best["score"]:
                best = {"m": m, "c": c, "from": i, "to": len(bars) - 1,
                        "touches": touches, "score": score,
                        "y0": round(at(i), 2), "y1": round(at(len(bars) - 1), 2)}
    return best


# --------------------------------------------------------------------- setup

def bullish_trigger(bars, i, support):
    """Is bar i a textbook bullish reversal AT the support zone?

    Deliberately the obvious readings - hammer, bullish engulfing, strong
    rejection wick - because the story requires the viewer to agree with the
    character. A setup only the author can see is not a trap, it is a trick.
    """
    k = bars[i]
    prev = bars[i - 1]
    rng = k["h"] - k["l"]
    if rng <= 0:
        return None
    near = abs(k["l"] - support) <= support * 0.02 or k["l"] < support < k["c"]
    if not near:
        return None
    body = abs(k["c"] - k["o"])
    lower = min(k["o"], k["c"]) - k["l"]
    if k["c"] > k["o"] and lower >= body * 1.6 and lower >= rng * 0.4:
        return "HAMMER AT SUPPORT"
    if k["c"] > k["o"] and prev["c"] < prev["o"] and k["c"] >= prev["o"] and k["o"] <= prev["c"]:
        return "BULLISH ENGULFING AT SUPPORT"
    if k["c"] > k["o"] and lower >= rng * 0.5:
        return "REJECTION OFF SUPPORT"
    return None


def main():
    src = json.load(open(SRC))
    allbars = []
    bad = set()
    for i, b in enumerate(src["bars"]):
        o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        if max(max(o, c) - h, l - min(o, c), 0.0) > DEV_HARD:
            bad.add(i)
        allbars.append({**b, "h": max(h, o, c), "l": min(l, o, c)})

    results = []
    for start in range(0, len(allbars) - SETUP_BARS - REVEAL_BARS):
        end = start + SETUP_BARS
        if any(j in bad for j in range(start, end + REVEAL_BARS)):
            continue
        w = allbars[start:end]
        rev = allbars[end:end + REVEAL_BARS]

        hi_p, lo_p = pivots(w)
        sup = zones(w, lo_p, use_high=False)
        res = zones(w, hi_p, use_high=True)
        if not sup:
            continue

        # The support the setup fires at must be the strongest one near price.
        last = w[-1]["c"]
        near_sup = [z for z in sup if z["price"] < last and (last - z["price"]) / last < 0.10]
        if not near_sup:
            continue
        s = near_sup[0]

        # the trigger has to be one of the last few bars - the decision is NOW
        trig = None
        for i in range(len(w) - 3, len(w)):
            name = bullish_trigger(w, i, s["price"])
            if name:
                trig = (i, name)
        if not trig:
            continue
        ti, tname = trig

        entry = w[-1]["c"]
        stop = round(min(b["l"] for b in w[ti:]) * 0.995, 2)
        if stop >= entry:
            continue
        risk = entry - stop
        target = round(entry + 2 * risk, 2)

        sl_at = next((i for i, b in enumerate(rev) if b["l"] <= stop), None)
        tp_at = next((i for i, b in enumerate(rev) if b["h"] >= target), None)
        # THE STORY: the stop has to be hit, and hit first.
        if sl_at is None or (tp_at is not None and tp_at <= sl_at):
            continue

        # The drawn resistance has to sit ABOVE the entry, or the chart shows a
        # "resistance" line under price and the structure reads as nonsense.
        res = [z for z in res if z["price"] > entry * 1.01]

        # How far the trade went the RIGHT way before it broke, in R.
        mfe = (max(b["h"] for b in rev[:sl_at + 1]) - entry) / risk

        tl = trendline(w, lo_p, use_high=False)
        drop = (min(b["l"] for b in rev) / entry - 1) * 100
        results.append({
            "start": start,
            # Rank on how well the setup TELLS, not on how badly it lost.
            #
            # The first version of this scored `- sl_at * 0.15`, which quietly
            # ranked instant failure highest - and instant failure is the one
            # version of this story that teaches nothing. A trade that breaks
            # on the very next bar looks like a bad entry; a trade that works
            # for four bars and THEN breaks is the actual lesson, because the
            # viewer has time to agree with the character before he is wrong.
            #
            # So: reward a few bars of hope (mfe, capped - past ~1R it stops
            # being a loss story), reward the stop landing a few bars in rather
            # than immediately, and penalise risk so wide that the stop was
            # never really a stop.
            "score": round(
                s["score"]
                + (2 if tl else 0)
                + (1.5 if res else 0)
                + min(mfe, 1.0) * 3.0
                - abs(sl_at - 4) * 0.5
                - max(0.0, risk / entry * 100 - 4.0) * 0.8,
                3),
            "mfe": round(mfe, 2),
            "support": s, "resistances": res[:1], "trendline": tl,
            "trigger": {"bar": ti, "name": tname},
            "entry": entry, "stop": stop, "target": target,
            "risk": round(risk, 2), "slAt": sl_at, "tpAt": tp_at,
            "drop": round(drop, 1),
            "pivotsHigh": hi_p, "pivotsLow": lo_p,
            "from": w[0]["date"], "to": rev[-1]["date"],
            "bars": [{"d": b["date"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]}
                     for b in w + rev],
        })

    if not results:
        print("UNMATCHED - no real failed bullish setup in this series", file=sys.stderr)
        return 2

    results.sort(key=lambda r: -r["score"])
    best = results[0]
    print(f"{len(results)} real failed setups; best scores {best['score']:.2f}\n")
    print(f"  window      {best['from']} -> {best['to']}  ({SETUP_BARS}+{REVEAL_BARS} bars)")
    print(f"  support     {best['support']['price']}  touched {best['support']['touches']}x")
    if best["resistances"]:
        r = best["resistances"][0]
        print(f"  resistance  {r['price']}  touched {r['touches']}x")
    if best["trendline"]:
        t = best["trendline"]
        print(f"  trendline   {t['y0']} -> {t['y1']}  {t['touches']} touches")
    print(f"  trigger     {best['trigger']['name']} at setup bar {best['trigger']['bar']}")
    print(f"  entry {best['entry']}  stop {best['stop']}  risk {best['risk']} "
          f"({best['risk'] / best['entry'] * 100:.1f}%)  target(2R) {best['target']}")
    print(f"  best it ever got: +{best['mfe']}R  ({best['mfe'] * 50:.0f}% of the way to target)")
    tail = "  (target never reached)" if best["tpAt"] is None else f"  (target later at {best['tpAt']})"
    print(f"  STOPPED OUT at reveal bar {best['slAt']}{tail}")
    print(f"  worst drawdown from entry: {best['drop']}%")

    payload = {
        "symbol": src["symbol"], "interval": src["interval"],
        "retrieved_at": src["retrieved_at"], "source": "Interactive Brokers",
        "note": src.get("note"),
        "setupBars": SETUP_BARS, "revealBars": REVEAL_BARS,
        **{k: best[k] for k in
           ["from", "to", "support", "resistances", "trendline", "trigger",
            "entry", "stop", "target", "risk", "slAt", "tpAt", "drop", "mfe",
            "pivotsHigh", "pivotsLow", "bars"]},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(payload, open(OUT, "w"), indent=1)
    print(f"\n-> {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
