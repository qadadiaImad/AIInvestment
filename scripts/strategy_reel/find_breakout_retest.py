"""Find a REAL breakout-and-retest occurrence in Brent daily bars.

The scanner FINDS a window that already satisfies the definition — it never
nudges data (house rule 10.1). Yahoo REST is the live source this session
(IBKR MCP unauthenticated); every pull is stamped. Bars whose close sits
outside [low, high] by more than 2 ticks are quarantined; a window containing
one is rejected outright.

Definition (chosen BEFORE looking at outcomes):
  resistance  = a swing-high price level touched >= 2 times (highs within
                0.35% of each other), touches >= 3 bars apart
  breakout    = first bar AFTER touch 2 whose CLOSE exceeds level * 1.002
  retest      = a later bar (within 15 bars) whose LOW comes back within
                0.5% of the level, closing above it
  entry       = level (the retest holds), stop = retest bar low - 0.25%,
                target = entry + 2.0 * (entry - stop)   [2R by construction]
  success     = target trades (some later high >= target) within 20 bars
                WITHOUT stop trading first

    python scripts/strategy_reel/find_breakout_retest.py [SYMBOL]

Emits content/probe/strategy_real_window.json (bars, indices, prices,
dates, provenance) or reports UNMATCHED honestly.
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "content", "probe", "strategy_real_window.json")

TOL_TOUCH = 0.0035
BREAK_MARGIN = 1.002
TOL_RETEST = 0.005
MAX_RETEST_BARS = 15
MAX_PLAY_BARS = 20
RR = 2.0
MIN_RISK_PCT = 0.008  # entry-to-stop must be a real daily-scale retest, not noise


def fetch(symbol, rng="2y"):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?interval=1d&range={rng}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    r = d["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    bars, quarantined = [], 0
    for t, o, h, l, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None in (o, h, l, c):
            continue
        if c > h + 0.02 or c < l - 0.02:  # dirty bar -> quarantine
            quarantined += 1
            bars.append(None)
            continue
        bars.append({"t": time.strftime("%Y-%m-%d", time.gmtime(t)),
                     "o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)})
    return bars, url, quarantined


def swing_high(bars, i, w=2):
    if bars[i] is None:
        return False
    for j in range(max(0, i - w), min(len(bars), i + w + 1)):
        if j != i and bars[j] is not None and bars[j]["h"] > bars[i]["h"]:
            return False
    return True


def scan(bars):
    n = len(bars)
    swings = [i for i in range(n - 25) if swing_high(bars, i)]
    for a_pos, a in enumerate(swings):
        for b in swings[a_pos + 1:]:
            if b - a < 3 or b - a > 40:
                continue
            level = max(bars[a]["h"], bars[b]["h"])
            if abs(bars[a]["h"] - bars[b]["h"]) / level > TOL_TOUCH:
                continue
            # no close above level between the two touches
            seg = [x for x in bars[a:b + 1] if x]
            if any(x["c"] > level * BREAK_MARGIN for x in seg):
                continue
            # breakout after touch 2
            brk = None
            for i in range(b + 1, min(b + 12, n)):
                if bars[i] is None:
                    brk = None
                    break
                if bars[i]["c"] > level * BREAK_MARGIN:
                    brk = i
                    break
                if bars[i]["c"] < level * 0.96:
                    break
            if brk is None:
                continue
            # retest
            rt = None
            for i in range(brk + 1, min(brk + MAX_RETEST_BARS, n)):
                if bars[i] is None:
                    rt = None
                    break
                if bars[i]["l"] <= level * (1 + TOL_RETEST) and bars[i]["c"] >= level * 0.998:
                    rt = i
                    break
                if bars[i]["c"] < level * 0.985:
                    break
            if rt is None:
                continue
            entry = level
            stop = bars[rt]["l"] * 0.9975
            if entry - stop <= 0 or (entry - stop) / entry < MIN_RISK_PCT:
                continue
            target = round(entry + RR * (entry - stop), 2)
            hit = None
            for i in range(rt + 1, min(rt + MAX_PLAY_BARS, n)):
                if bars[i] is None:
                    hit = None
                    break
                if bars[i]["l"] <= stop:
                    hit = ("stop", i)
                    break
                if bars[i]["h"] >= target:
                    hit = ("target", i)
                    break
            if hit and hit[0] == "target":
                return {"touch1": a, "touch2": b, "breakout": brk, "retest": rt,
                        "resolve": hit[1], "level": round(level, 2),
                        "entry": round(entry, 2), "stop": round(stop, 2),
                        "target": target}
    return None


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BZ=F"
    rng = sys.argv[2] if len(sys.argv) > 2 else "2y"
    bars, url, quarantined = fetch(symbol, rng)
    found = scan(bars)
    if not found:
        print(f"UNMATCHED: no qualifying breakout-retest in {symbol} 2y daily "
              f"({quarantined} bars quarantined). Try CL=F or GC=F.")
        sys.exit(2)
    # window: some context before touch1, through a few bars past resolution
    w0 = max(0, found["touch1"] - 4)
    w1 = min(len(bars), found["resolve"] + 4)
    window = bars[w0:w1]
    if any(b is None for b in window):
        print("UNMATCHED: qualifying window contains a quarantined bar — rejected.")
        sys.exit(2)
    rel = {k: found[k] - w0 for k in ("touch1", "touch2", "breakout", "retest", "resolve")}
    out = {
        "symbol": symbol, "interval": "1d",
        "bars": window, "indices": rel,
        "level": found["level"], "entry": found["entry"],
        "stop": found["stop"], "target": found["target"],
        "rr": RR,
        "dates": {"touch1": window[rel["touch1"]]["t"],
                  "touch2": window[rel["touch2"]]["t"],
                  "breakout": window[rel["breakout"]]["t"],
                  "retest": window[rel["retest"]]["t"],
                  "resolve": window[rel["resolve"]]["t"]},
        "source": url, "source_class": "api",
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "quarantined_bars_in_series": quarantined,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"FOUND {symbol}: level {found['level']} touches "
          f"{out['dates']['touch1']} & {out['dates']['touch2']}, breakout "
          f"{out['dates']['breakout']}, retest {out['dates']['retest']}, "
          f"2R target {found['target']} hit {out['dates']['resolve']} "
          f"({len(window)} bars) -> {OUT}")


if __name__ == "__main__":
    main()
