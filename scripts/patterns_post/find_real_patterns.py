"""Find REAL occurrences of the 12 classic chart formations in real bars.

The pattern post's first cut drew the synthetic library. The owner's rule -
the same one that rebuilt the trading-styles reel - is that bars must be real:
detect each formation in actual market history, or report it UNMATCHED. Never
draw one.

So each detector below FINDS its formation in real daily bars (SPY five-year
pull by default, more tickers addable), picks the cleanest instance whose
textbook resolution actually followed, and emits the window with:

  * the real candles and their real dates,
  * the level (neckline / rim / flag boundary) from the ACTUAL pivots,
  * trendlines fit through the ACTUAL swing points (for the line formations),
  * the breakout bar index, and
  * a factLine computed from what really happened after.

Bilateral formations (symmetrical triangle, megaphone) take their verdict from
the direction the real breakout took - that is what bilateral means.

Data integrity per CLAUDE.md §10.1: bars whose close sits a cent or two
outside the session range are normalised by extending the wick; anything
deviating more than 15c is quarantined and no window containing one is
eligible.

Eye-friendly proportions are enforced here, not in the renderer: every window
is trimmed to 24-44 bars (48 for the cup) with a little run-in before the
formation and a few bars of aftermath after the break, so every card's
box-to-candle ratio sits in the same comfortable band.

Usage:
    python scripts/patterns_post/find_real_patterns.py
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "patterns_post", "gallery.json")

SOURCES = [os.path.join(REPO, "data", "prices", "SPY_1d_5y_2026-07-30.json")]

PIVOT_N = 2
DEV_HARD = 0.15


# ------------------------------------------------------------------ loading

def load(path):
    src = json.load(open(path))
    bars, bad = [], set()
    for i, b in enumerate(src["bars"]):
        o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        if max(max(o, c) - h, l - min(o, c), 0.0) > DEV_HARD:
            bad.add(i)
        bars.append({"date": b["date"], "o": o, "h": max(h, o, c), "l": min(l, o, c), "c": c})
    return src["symbol"], bars, bad, src["retrieved_at"]


def pivots(bars, n=PIVOT_N):
    hi, lo = [], []
    for i in range(n, len(bars) - n):
        w = bars[i - n:i + n + 1]
        if bars[i]["h"] >= max(b["h"] for b in w):
            hi.append(i)
        if bars[i]["l"] <= min(b["l"] for b in w):
            lo.append(i)
    return hi, lo


def fit(pts):
    n = len(pts)
    sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts); sxy = sum(p[0] * p[1] for p in pts)
    den = n * sxx - sx * sx
    if den == 0:
        return 0.0, sy / n
    m = (n * sxy - sx * sy) / den
    return m, (sy - m * sx) / n


# Each detector returns a list of instances:
# {start, end (exclusive of aftermath), reveal (abs idx of breakout bar),
#  level, levelLabel, trendPts: ([(i,price)..],[(i,price)..]) or None,
#  answer, bias, score, name}
# Window assembly (run-in + aftermath + trimming) happens once, in finish().


def d_double(bars, hi, lo, top=True):
    out = []
    P = hi if top else lo
    key = (lambda i: bars[i]["h"]) if top else (lambda i: bars[i]["l"])
    for a in range(len(P)):
        for b in range(a + 1, len(P)):
            i, j = P[a], P[b]
            if not 5 <= j - i <= 30:
                continue
            if abs(key(i) - key(j)) / key(i) > 0.014:
                continue
            between = range(i + 1, j)
            if not between:
                continue
            if top:
                m = min(between, key=lambda x: bars[x]["l"])
                depth = (min(key(i), key(j)) - bars[m]["l"]) / key(i)
            else:
                m = max(between, key=lambda x: bars[x]["h"])
                depth = (bars[m]["h"] - max(key(i), key(j))) / key(i)
            if depth < 0.02:
                continue
            neck = bars[m]["l"] if top else bars[m]["h"]
            # the two extremes must be THE two extremes of their neighbourhood,
            # or the card reads as "downtrend with a bounce", not a double top
            hood = bars[max(0, i - 3):min(len(bars), j + 4)]
            if top and max(b_["h"] for b_ in hood) > max(key(i), key(j)) * 1.004:
                continue
            if not top and min(b_["l"] for b_ in hood) < min(key(i), key(j)) * 0.996:
                continue
            reveal = None
            for k in range(j + 1, min(j + 16, len(bars))):
                if (top and bars[k]["c"] < neck) or (not top and bars[k]["c"] > neck):
                    reveal = k
                    break
            if reveal is None:
                continue
            after = bars[reveal + 1:reveal + 7]
            if not after:
                continue
            move = (min(b_["l"] for b_ in after) / neck - 1) if top else (max(b_["h"] for b_ in after) / neck - 1)
            if (top and move > -0.012) or (not top and move < 0.012):
                continue
            out.append({
                "start": i, "end": j, "reveal": reveal, "level": neck,
                "levelLabel": "NECKLINE", "trendPts": None,
                "answer": "SELL" if top else "BUY", "bias": "bearish" if top else "bullish",
                "score": depth * 100 + min(abs(move), 0.06) * 100 - abs(key(i) - key(j)) / key(i) * 100,
                "name": "Double Top" if top else "Double Bottom",
                "marks": [(i, "1", "above" if top else "below"), (j, "2", "above" if top else "below")],
            })
    return out


def d_hs(bars, hi, lo, top=True):
    out = []
    P = hi if top else lo
    key = (lambda i: bars[i]["h"]) if top else (lambda i: bars[i]["l"])
    opp = (lambda i: bars[i]["l"]) if top else (lambda i: bars[i]["h"])
    sgn = 1 if top else -1
    for x in range(len(P) - 2):
        i, j, k = P[x], P[x + 1], P[x + 2]
        if not (4 <= j - i <= 22 and 4 <= k - j <= 22):
            continue
        head_over = (key(j) - key(i)) / key(i) * sgn, (key(j) - key(k)) / key(k) * sgn
        if min(head_over) < 0.01:
            continue
        if abs(key(i) - key(k)) / key(i) > 0.035:
            continue
        b1 = range(i + 1, j)
        b2 = range(j + 1, k)
        if not b1 or not b2:
            continue
        t1 = (min if top else max)(b1, key=lambda z: bars[z]["l"] if top else -bars[z]["h"])
        t2 = (min if top else max)(b2, key=lambda z: bars[z]["l"] if top else -bars[z]["h"])
        # a neckline drawn horizontal has to BE horizontal-honest: if the two
        # troughs disagree by more than 1.5% the sloped fit dominates the box
        # and reads as a mistake, so the instance is rejected instead
        if abs(opp(t1) - opp(t2)) / opp(t1) > 0.015:
            continue
        m, c = fit([(t1, opp(t1)), (t2, opp(t2))])
        reveal = None
        for z in range(k + 1, min(k + 14, len(bars))):
            neck_z = m * z + c
            if (top and bars[z]["c"] < neck_z) or (not top and bars[z]["c"] > neck_z):
                reveal = z
                break
        if reveal is None:
            continue
        neck_r = m * reveal + c
        after = bars[reveal + 1:reveal + 7]
        if not after:
            continue
        move = (min(b_["l"] for b_ in after) / neck_r - 1) if top else (max(b_["h"] for b_ in after) / neck_r - 1)
        if (top and move > -0.016) or (not top and move < 0.016):
            continue
        out.append({
            "start": i, "end": k, "reveal": reveal, "level": round((m * reveal + c), 2),
            "levelLabel": "NECKLINE", "trendPts": None,
            "answer": "SELL" if top else "BUY", "bias": "bearish" if top else "bullish",
            "score": min(head_over) * 200 + min(abs(move), 0.06) * 100,
            "name": "Head and Shoulders" if top else "Inverse Head and Shoulders",
            "marks": [(i, "S", "above" if top else "below"), (j, "H", "above" if top else "below"), (k, "S", "above" if top else "below")],
        })
    return out


def d_flag(bars, hi, lo, bull=True):
    out = []
    n = len(bars)
    for p0 in range(2, n - 20):
        # the pole
        for plen in range(4, 11):
            p1 = p0 + plen
            if p1 >= n - 12:
                break
            chg = (bars[p1]["c"] - bars[p0]["c"]) / bars[p0]["c"]
            if bull and chg < 0.055:
                continue
            if not bull and chg > -0.055:
                continue
            pole_h = abs(bars[p1]["c"] - bars[p0]["c"])
            # the flag
            for flen in range(4, 11):
                f1 = p1 + flen
                if f1 >= n - 6:
                    break
                flag = bars[p1 + 1:f1 + 1]
                if not flag:
                    continue
                fh = max(b["h"] for b in flag)
                fl = min(b["l"] for b in flag)
                if (fh - fl) > pole_h * 0.62:
                    continue
                drift = (flag[-1]["c"] - flag[0]["c"]) / flag[0]["c"]
                if bull and not -0.045 < drift <= 0.004:
                    continue
                if not bull and not -0.004 <= drift < 0.045:
                    continue
                if bull and fh > bars[p1]["h"] * 1.004:
                    continue
                if not bull and fl < bars[p1]["l"] * 0.996:
                    continue
                lvl = fh if bull else fl
                reveal = None
                for z in range(f1 + 1, min(f1 + 5, n)):
                    if (bull and bars[z]["c"] > lvl) or (not bull and bars[z]["c"] < lvl):
                        reveal = z
                        break
                if reveal is None:
                    continue
                after = bars[reveal + 1:reveal + 6]
                if not after:
                    continue
                move = (max(b["h"] for b in after) / lvl - 1) if bull else (min(b["l"] for b in after) / lvl - 1)
                if (bull and move < 0.012) or (not bull and move > -0.012):
                    continue
                # a flag is a parallel channel: one slope from the closes,
                # offset to hug the highs and the lows. Independent hi/lo fits
                # on 5 bars routinely CROSS, which no flag does.
                span = list(range(p1 + 1, f1 + 1))
                mm, _ = fit([(z, bars[z]["c"]) for z in span])
                c_hi = max(bars[z]["h"] - mm * z for z in span)
                c_lo = min(bars[z]["l"] - mm * z for z in span)
                hi_pts = [(span[0], mm * span[0] + c_hi), (span[-1], mm * span[-1] + c_hi)]
                lo_pts = [(span[0], mm * span[0] + c_lo), (span[-1], mm * span[-1] + c_lo)]
                out.append({
                    "start": p0, "end": f1, "reveal": reveal, "level": lvl,
                    "levelLabel": "FLAG EDGE", "trendPts": (hi_pts, lo_pts),
                    "answer": "BUY" if bull else "SELL", "bias": "bullish" if bull else "bearish",
                    "score": abs(chg) * 100 + min(abs(move), 0.06) * 100 - flen * 0.2,
                    "name": "Bull Flag" if bull else "Bear Flag",
                })
    return out


def d_triangle_asc(bars, hi, lo):
    out = []
    n = len(bars)
    for s in range(2, n - 24):
        for e in range(s + 14, min(s + 30, n - 6)):
            H = [i for i in hi if s <= i <= e]
            L = [i for i in lo if s <= i <= e]
            if len(H) < 2 or len(L) < 2:
                continue
            top_prices = [bars[i]["h"] for i in H]
            band = max(top_prices) * 0.008
            if max(top_prices) - min(top_prices) > band:
                continue
            mlo, clo = fit([(i, bars[i]["l"]) for i in L])
            if mlo <= 0 or (bars[L[-1]]["l"] - bars[L[0]]["l"]) / bars[L[0]]["l"] < 0.012:
                continue
            lvl = sum(top_prices) / len(top_prices)
            reveal = None
            for z in range(e, min(e + 8, n)):
                if bars[z]["c"] > lvl * 1.002:
                    reveal = z
                    break
            if reveal is None:
                continue
            after = bars[reveal + 1:reveal + 6]
            if not after or max(b["h"] for b in after) / lvl - 1 < 0.012:
                continue
            out.append({
                "start": s, "end": e, "reveal": reveal, "level": round(lvl, 2),
                "levelLabel": f"RESISTANCE · {len(H)} TOUCHES",
                "trendPts": ([(i, bars[i]["h"]) for i in H], [(i, bars[i]["l"]) for i in L]),
                "answer": "BUY", "bias": "bullish",
                "score": len(H) * 2 + mlo * 500 + (max(b["h"] for b in after) / lvl - 1) * 100,
                "name": "Ascending Triangle",
            })
    return out


def _wedge_like(bars, hi, lo, kind):
    """kind: 'sym' converging both ways; 'rise'/'fall' wedges; 'mega' diverging."""
    out = []
    n = len(bars)
    for s in range(2, n - 24):
        for e in range(s + 14, min(s + 32, n - 6)):
            H = [i for i in hi if s <= i <= e]
            L = [i for i in lo if s <= i <= e]
            if len(H) < 2 or len(L) < 2:
                continue
            mh, ch = fit([(i, bars[i]["h"]) for i in H])
            ml, cl = fit([(i, bars[i]["l"]) for i in L])
            px = bars[e]["c"]
            rh, rl = mh / px * 100, ml / px * 100  # %/bar slopes
            ok = False
            if kind == "sym":
                ok = rh < -0.06 and rl > 0.06
            elif kind == "rise":
                ok = rh > 0.05 and rl > 0.05 and rl > rh * 1.25
            elif kind == "fall":
                ok = rh < -0.05 and rl < -0.05 and rh < rl * 1.25
            elif kind == "mega":
                ok = rh > 0.05 and rl < -0.05
            if not ok:
                continue
            reveal, direction = None, None
            for z in range(e, min(e + 8, n)):
                up_line = mh * z + ch
                dn_line = ml * z + cl
                if bars[z]["c"] > up_line * 1.002:
                    reveal, direction = z, "up"
                    break
                if bars[z]["c"] < dn_line * 0.998:
                    reveal, direction = z, "down"
                    break
            if reveal is None:
                continue
            # wedges have a textbook direction; bilateral takes the real one
            if kind == "rise" and direction != "down":
                continue
            if kind == "fall" and direction != "up":
                continue
            lvl = (ml * reveal + cl) if direction == "down" else (mh * reveal + ch)
            after = bars[reveal + 1:reveal + 6]
            if not after:
                continue
            move = (min(b["l"] for b in after) / lvl - 1) if direction == "down" else (max(b["h"] for b in after) / lvl - 1)
            if (direction == "down" and move > -0.012) or (direction == "up" and move < 0.012):
                continue
            name = {
                "sym": "Symmetrical Triangle",
                "rise": "Rising Wedge",
                "fall": "Falling Wedge",
                "mega": "Megaphone",
            }[kind]
            out.append({
                "start": s, "end": e, "reveal": reveal, "level": round(lvl, 2),
                "levelLabel": "BREAK LINE",
                "trendPts": ([(i, bars[i]["h"]) for i in H], [(i, bars[i]["l"]) for i in L]),
                "answer": "BUY" if direction == "up" else "SELL",
                "bias": "bullish" if direction == "up" else "bearish",
                "score": (abs(rh) + abs(rl)) * 8 + min(abs(move), 0.06) * 100 + len(H) + len(L),
                "name": name,
            })
    return out


def d_cup(bars, hi, lo):
    out = []
    n = len(bars)
    for r in hi:  # left rim
        R = bars[r]["h"]
        for blen in range(8, 30):
            b = r + blen
            if b >= n - 16:
                break
            bot = min(range(r + 1, b + 1), key=lambda z: bars[z]["l"])
            depth = (R - bars[bot]["l"]) / R
            if depth < 0.06:
                continue
            # recovery to near the rim
            rec = None
            for z in range(bot + 6, min(bot + 34, n - 8)):
                if bars[z]["h"] >= R * 0.985:
                    rec = z
                    break
            if rec is None:
                continue
            # U-shape: bottom roughly central
            span = rec - r
            if not 0.25 < (bot - r) / span < 0.75 or span < 16:
                continue
            # handle: a few bars holding the upper part
            for hlen in range(3, 9):
                hz = rec + hlen
                if hz >= n - 6:
                    break
                handle = bars[rec + 1:hz + 1]
                if not handle:
                    continue
                if min(x["l"] for x in handle) < bars[bot]["l"] + (R - bars[bot]["l"]) * 0.55:
                    continue
                if max(x["h"] for x in handle) > R * 1.004:
                    continue
                reveal = None
                for z in range(hz, min(hz + 5, n)):
                    if bars[z]["c"] > R * 1.002:
                        reveal = z
                        break
                if reveal is None:
                    continue
                after = bars[reveal + 1:reveal + 6]
                if not after or max(x["h"] for x in after) / R - 1 < 0.012:
                    continue
                out.append({
                    "start": r, "end": hz, "reveal": reveal, "level": round(R, 2),
                    "levelLabel": "RIM", "trendPts": None,
                    "answer": "BUY", "bias": "bullish",
                    "score": depth * 60 + (max(x["h"] for x in after) / R - 1) * 100 - span * 0.05,
                    "name": "Cup and Handle",
                })
    return out


# ------------------------------------------------------------------ assembly

def finish(bars, bad, inst, max_n=44):
    """Trim to an eye-friendly window and convert to card geometry."""
    pre = 3
    post = 5
    s = max(0, inst["start"] - pre)
    e = min(len(bars) - 1, inst["reveal"] + post)
    # proportion floor: a 20-bar box among 36-bar boxes reads wrong. Pad the
    # run-in (honest context) until the window reaches 24 bars.
    while e - s + 1 < 24 and s > 0:
        s -= 1
    if e - s + 1 > max_n:
        s = e - max_n + 1
    # The trim must NEVER cut a defining pivot out of the window — losing the
    # first top of a double top deletes the pattern's own evidence. Marks win
    # over the size cap: pull s back to keep them, trim aftermath instead,
    # and accept up to 50 bars before giving up on the instance.
    first_mark = min((mi for mi, _, _ in inst.get("marks", [])), default=None)
    if first_mark is not None and s > first_mark - 2:
        s = max(0, first_mark - 2)
        while e - s + 1 > max_n and e > inst["reveal"] + 2:
            e -= 1
        if e - s + 1 > 50:
            return None
    if any(i in bad for i in range(s, e + 1)):
        return None
    w = bars[s:e + 1]
    reveal_local = inst["reveal"] - s
    trend = None
    if inst["trendPts"]:
        hp, lp = inst["trendPts"]
        def loc(pts):
            pts = [(i - s, v) for i, v in pts if s <= i <= e]
            return fit(pts) if len(pts) >= 2 else None
        fh = loc(hp) if hp else None
        fl = loc(lp) if lp else None
        if fh and fl:
            trend = {
                "from": max(0, inst["start"] - s), "to": reveal_local,
                "hi": {"m": round(fh[0], 5), "c": round(fh[1], 4)},
                "lo": {"m": round(fl[0], 5), "c": round(fl[1], 4)},
            }
        elif fh:  # neckline-as-line (H&S): store as level line via hi, mirror lo
            trend = {
                "from": max(0, inst["start"] - s), "to": reveal_local,
                "hi": {"m": round(fh[0], 5), "c": round(fh[1], 4)},
                "lo": {"m": round(fh[0], 5), "c": round(fh[1], 4)},
            }
    # What actually happened, for the factLine. Measured from the BREAKOUT
    # BAR'S REAL CLOSE, never from a fitted line's value: an extrapolated
    # neckline can sit far from where price actually trades, and dividing by
    # it produced -19% five-session SPY moves that never happened. The level
    # must also BE near the breakout close, or the instance's geometry is a
    # degenerate fit and the whole card is rejected.
    after = w[reveal_local:]
    close_r = w[reveal_local]["c"]
    lvl = inst["level"]
    if abs(lvl / close_r - 1) > 0.025:
        return None
    if inst["bias"] == "bearish":
        ext = min(b["l"] for b in after)
    else:
        ext = max(b["h"] for b in after)
    chg = (ext / close_r - 1) * 100
    days = len(after) - 1
    fact = f"Real break — {chg:+.1f}% in {days} sessions."
    marks = [
        {"i": mi - s, "label": lab, "side": side}
        for mi, lab, side in inst.get("marks", [])
        if s <= mi <= e
    ]
    return {
        "window": w, "revealFrom": reveal_local, "trend": trend,
        "factLine": fact, "chg": round(chg, 1), "marks": marks,
    }


def main():
    symbol, bars, bad, retrieved = load(SOURCES[0])
    hi, lo = pivots(bars)

    detectors = [
        ("Double Top", lambda: d_double(bars, hi, lo, top=True)),
        ("Double Bottom", lambda: d_double(bars, hi, lo, top=False)),
        ("Head and Shoulders", lambda: d_hs(bars, hi, lo, top=True)),
        ("Inverse Head and Shoulders", lambda: d_hs(bars, hi, lo, top=False)),
        ("Bull Flag", lambda: d_flag(bars, hi, lo, bull=True)),
        ("Bear Flag", lambda: d_flag(bars, hi, lo, bull=False)),
        ("Ascending Triangle", lambda: d_triangle_asc(bars, hi, lo)),
        ("Cup and Handle", lambda: d_cup(bars, hi, lo)),
        ("Symmetrical Triangle", lambda: _wedge_like(bars, hi, lo, "sym")),
        ("Rising Wedge", lambda: _wedge_like(bars, hi, lo, "rise")),
        ("Falling Wedge", lambda: _wedge_like(bars, hi, lo, "fall")),
        ("Megaphone", lambda: _wedge_like(bars, hi, lo, "mega")),
    ]

    CHAPTERS = [
        ("REVERSAL", "trend reverses", ["Double Top", "Double Bottom", "Head and Shoulders", "Inverse Head and Shoulders"]),
        ("CONTINUATION", "trend continues", ["Bull Flag", "Bear Flag", "Ascending Triangle", "Cup and Handle"]),
        ("BILATERAL", "breakout decides", ["Symmetrical Triangle", "Rising Wedge", "Falling Wedge", "Megaphone"]),
    ]

    found = {}
    taken = []  # (start, end) of chosen windows

    def overlaps(a0, a1):
        for b0, b1 in taken:
            inter = max(0, min(a1, b1) - max(a0, b0))
            if inter > 0.6 * (a1 - a0):
                return True
        return False

    for name, det in detectors:
        insts = det()
        insts.sort(key=lambda x: -x["score"])
        pick = None
        for inst in insts:
            # Distinct windows: the August-2022 rollover IS both a double top
            # and a head-and-shoulders, but showing the same six weeks twice
            # makes the reel read as one example wearing two hats.
            if overlaps(inst["start"], inst["reveal"] + 5):
                continue
            fin = finish(bars, bad, inst, max_n=48 if name == "Cup and Handle" else 44)
            if fin:
                pick = (inst, fin)
                taken.append((inst["start"], inst["reveal"] + 5))
                break
        if pick:
            inst, fin = pick
            w = fin["window"]
            found[name] = {
                "id": len(found) + 1,
                "name": name,
                "ticker": symbol,
                "from": w[0]["date"], "to": w[-1]["date"],
                "bias": inst["bias"], "answer": inst["answer"],
                "answerLine": fin["factLine"],
                "context": "",
                "levelPrice": round(inst["level"], 2),
                "levelLabel": inst["levelLabel"],
                "revealFrom": fin["revealFrom"],
                "trend": fin["trend"],
                "marks": fin["marks"],
                "candles": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in w],
            }
            print(f"  FOUND {name:28} {w[0]['date']} -> {w[-1]['date']}  n={len(w)}  {inst['answer']}  {fin['factLine']}")
        else:
            print(f"  UNMATCHED {name}")

    missing = [n for n, _ in detectors if n not in found]
    if missing:
        print(f"\nUNMATCHED in {symbol}: {missing}", file=sys.stderr)

    chapters = []
    for title, sub, names in CHAPTERS:
        chapters.append({"title": title, "sub": sub, "cards": [found[n] for n in names if n in found]})

    payload = {
        "source": f"Real {symbol} daily bars · Interactive Brokers · retrieved {retrieved}",
        "note": "Every formation DETECTED in real history, never drawn. Windows trimmed to 24-48 bars.",
        "chapters": chapters,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(payload, open(OUT, "w"), indent=1)
    print(f"\n-> {os.path.relpath(OUT, REPO)}  ({len(found)}/12 formations)")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
