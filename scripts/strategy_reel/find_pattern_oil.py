"""Find the MOST RECENT complex bullish pattern on oil — real bars only.

Patterns (definitions fixed ex-ante, scanner never nudges data):

INVERSE HEAD & SHOULDERS
  swing lows L1 (left shoulder), H (head), L2 (right shoulder), w=3;
  head >= 1.5% deeper than both shoulders (daily; 0.7% hourly);
  shoulders within 2% of each other; neckline = max of the two swing highs
  between them, the two within 1.5% (near-horizontal); breakout = close >
  neckline*1.002 within 15 bars of L2; entry = neckline; stop = below L2;
  target = neckline + (neckline - head)  [measured move]; require
  RR >= 1.3 and risk >= 0.8% (daily) / 0.4% (hourly); success = target
  trades before stop within 40 bars.

DOUBLE BOTTOM
  swing lows B1, B2 within 1.2% of each other, 5-40 bars apart, head-free
  in between; neckline = highest high between them; breakout, entry, stop
  (below B2), target = neckline + (neckline - bottoms avg), same gates.

Candidates are sorted by breakout recency; the newest qualifying window
wins. UNMATCHED is reported honestly.

    python scripts/strategy_reel/find_pattern_oil.py
Writes content/probe/strategy_real_window2.json
"""
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "content", "probe", "strategy_real_window2.json")


def fetch(symbol, interval, rng):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?interval={interval}&range={rng}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    r = d["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    bars = []
    for t, o, h, l, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None in (o, h, l, c) or c > h + 0.02 or c < l - 0.02:
            bars.append(None)
            continue
        fmt = "%Y-%m-%d" if interval == "1d" else "%Y-%m-%d %H:%M"
        bars.append({"t": time.strftime(fmt, time.gmtime(t)),
                     "o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)})
    return bars, url


def swings(bars, key, w=3):
    out = []
    for i in range(w, len(bars) - w):
        if bars[i] is None:
            continue
        seg = [bars[j] for j in range(i - w, i + w + 1)]
        if any(s is None for s in seg):
            continue
        vals = [s[key] for s in seg]
        if key == "l" and bars[i]["l"] == min(vals):
            out.append(i)
        if key == "h" and bars[i]["h"] == max(vals):
            out.append(i)
    return out


def resolve(bars, start, entry, stop, target, max_bars=40):
    for i in range(start, min(start + max_bars, len(bars))):
        if bars[i] is None:
            return None
        if bars[i]["l"] <= stop:
            return ("stop", i)
        if bars[i]["h"] >= target:
            return ("target", i)
    return None


def scan_ihs(bars, min_depth, min_risk):
    lows = swings(bars, "l")
    highs = swings(bars, "h")
    found = []
    for a_i, l1 in enumerate(lows):
        for h_i in [x for x in lows if l1 < x <= l1 + 45]:
            for l2 in [x for x in lows if h_i < x <= h_i + 45]:
                L1, H, L2 = bars[l1]["l"], bars[h_i]["l"], bars[l2]["l"]
                if not (H < L1 * (1 - min_depth) and H < L2 * (1 - min_depth)):
                    continue
                if abs(L1 - L2) / L2 > 0.02:
                    continue
                n1c = [x for x in highs if l1 < x < h_i]
                n2c = [x for x in highs if h_i < x < l2]
                if not n1c or not n2c:
                    continue
                n1, n2 = max(bars[x]["h"] for x in n1c), max(bars[x]["h"] for x in n2c)
                if abs(n1 - n2) / n2 > 0.015:
                    continue
                neck = max(n1, n2)
                brk = None
                for i in range(l2 + 1, min(l2 + 16, len(bars))):
                    if bars[i] is None:
                        break
                    if bars[i]["c"] > neck * 1.002:
                        brk = i
                        break
                if brk is None:
                    continue
                entry, stop = neck, L2 * 0.9975
                target = round(neck + (neck - H), 2)
                risk = (entry - stop) / entry
                if risk < min_risk:
                    continue
                rr = (target - entry) / (entry - stop)
                if rr < 1.3:
                    continue
                res = resolve(bars, brk + 1, entry, stop, target)
                if res and res[0] == "target":
                    found.append({"pattern": "INVERSE HEAD & SHOULDERS",
                                  "l1": l1, "head": h_i, "l2": l2, "neck": neck,
                                  "breakout": brk, "resolve": res[1],
                                  "entry": round(entry, 2), "stop": round(stop, 2),
                                  "target": target, "rr": round(rr, 2)})
    return found


def scan_db(bars, min_risk):
    lows = swings(bars, "l")
    found = []
    for b1 in lows:
        for b2 in [x for x in lows if b1 + 5 <= x <= b1 + 40]:
            B1, B2 = bars[b1]["l"], bars[b2]["l"]
            if abs(B1 - B2) / B2 > 0.012:
                continue
            mid = [bars[i] for i in range(b1, b2 + 1) if bars[i]]
            if min(m["l"] for m in mid) < min(B1, B2) * 0.997:
                continue
            neck = max(m["h"] for m in mid)
            if neck / max(B1, B2) < 1.012:
                continue
            brk = None
            for i in range(b2 + 1, min(b2 + 16, len(bars))):
                if bars[i] is None:
                    break
                if bars[i]["c"] > neck * 1.002:
                    brk = i
                    break
            if brk is None:
                continue
            entry, stop = neck, B2 * 0.9975
            target = round(neck + (neck - (B1 + B2) / 2), 2)
            risk = (entry - stop) / entry
            if risk < min_risk:
                continue
            rr = (target - entry) / (entry - stop)
            if rr < 1.3:
                continue
            res = resolve(bars, brk + 1, entry, stop, target)
            if res and res[0] == "target":
                found.append({"pattern": "DOUBLE BOTTOM", "b1": b1, "b2": b2,
                              "neck": neck, "breakout": brk, "resolve": res[1],
                              "entry": round(entry, 2), "stop": round(stop, 2),
                              "target": target, "rr": round(rr, 2)})
    return found


def main():
    trials = [("BZ=F", "1d", "2y", 0.015, 0.008), ("CL=F", "1d", "2y", 0.015, 0.008),
              ("BZ=F", "1h", "1y", 0.007, 0.004), ("CL=F", "1h", "1y", 0.007, 0.004)]
    all_c = []
    for symbol, interval, rng, depth, risk in trials:
        bars, url = fetch(symbol, interval, rng)
        cands = scan_ihs(bars, depth, risk) + scan_db(bars, risk)
        for c in cands:
            all_c.append({"stamp": bars[c["breakout"]]["t"], "symbol": symbol,
                          "interval": interval, "cand": c, "bars": bars, "url": url})
        print(f"{symbol} {interval} {rng}: {len(cands)} qualifying "
              f"({', '.join(sorted(set(x['pattern'] for x in cands))) or 'none'})")
    if not all_c:
        print("UNMATCHED: no qualifying complex pattern on oil in the scanned ranges.")
        raise SystemExit(2)
    window = None
    for best in sorted(all_c, key=lambda x: x["stamp"], reverse=True):
        c, bars = best["cand"], best["bars"]
        first_idx = c.get("l1", c.get("b1"))
        w0 = max(0, first_idx - 6)
        w1 = min(len(bars), c["resolve"] + 4)
        cand_window = bars[w0:w1]
        if any(b is None for b in cand_window):
            print(f"  skip {c['pattern']} @ {best['stamp']} (quarantined bar in window)")
            continue
        window = cand_window
        break
    if window is None:
        print("UNMATCHED: every qualifying window contains a quarantined bar.")
        raise SystemExit(2)
    shift = {k: v - w0 for k, v in c.items() if isinstance(v, int)}
    out = {"symbol": best["symbol"], "interval": best["interval"],
           "pattern": c["pattern"], "bars": window, "indices": shift,
           "neck": c["neck"], "entry": c["entry"], "stop": c["stop"],
           "target": c["target"], "rr": c["rr"],
           "source": best["url"], "source_class": "api",
           "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"BEST: {c['pattern']} on {best['symbol']} {best['interval']}, breakout "
          f"{best['stamp']}, entry {c['entry']} stop {c['stop']} target {c['target']} "
          f"rr {c['rr']} ({len(window)} bars) -> {OUT}")


if __name__ == "__main__":
    main()
