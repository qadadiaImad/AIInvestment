"""Find the history that justifies a level, and decide how much of it to PLAY.

The trading-quiz reel's second act zooms out to argue that a line matters:
"this rim has been tested ten times since 2021". This module produces that
argument from real bars, and - just as important - decides which part of it the
tape is allowed to play back.

Two rules do the editorial work:

  * A VISIT is a cluster of bars, not a bar. Price resting on a level for six
    sessions tested it once. Counting bars would let any sideways chop
    advertise itself as a heavily-defended line.

  * PLAYBACK is capped at PLAYBACK_MAX bars (6 months). Owner ruling,
    2026-08-12: history older than that is revealed by the camera moving, never
    played back bar by bar - "if a previous point 3y ago ... we zoom out to show
    that point but never display the curve progressing real time from 3y ago,
    it will be boring to watch."

Everything else here is refusal. Too few visits, too little history behind
them, or a dirty bar anywhere in an emitted window, and this reports UNMATCHED.
It never widens the tolerance until it finds what it was asked to find.

Usage:
    python scripts/ta_quiz/find_anchored_level.py            # SPY cup and handle
    python scripts/ta_quiz/find_anchored_level.py --list     # candidates
"""
import io
import json
import os
import sys
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# A level is "touched" when a bar's range straddles it within this fraction of
# price. 0.4% on SPY at 437 is ~1.75 - about one day's noise, which is what a
# trader eyeballing a line would accept.
TOL_PCT = 0.004
# Bars closer together than this belong to the same visit.
VISIT_GAP = 5
# 6 months of daily bars. The hard cap on how much tape may be played back.
PLAYBACK_MAX = 126
# Below this many prior visits the "tested N times" claim isn't worth making.
MIN_VISITS = 3
# The deep act needs a genuine deep past, not more of the playback window.
MIN_HISTORY = 126
# CLAUDE.md 10.1: a close this far outside the session range quarantines the bar.
DEV_HARD = 0.15
# Bars of breathing room left to the left of the oldest visit in the deep view.
DEEP_PAD = 12
# The opening tight window: how many bars are on screen while the tape prints.
TIGHT_BARS = 24


class Unmatched(Exception):
    """No honest window exists. Reported, never worked around."""


@dataclass(frozen=True)
class Visit:
    i: int
    end: int
    date: str


def touches_level(bar, level, tol):
    return bar["l"] - tol <= level <= bar["h"] + tol


def visits(bars, level, end, tol_pct=TOL_PCT, gap=VISIT_GAP):
    """Distinct visits to `level` among bars[:end], oldest first."""
    tol = level * tol_pct
    out = []
    for i in range(min(end, len(bars))):
        if not touches_level(bars[i], level, tol):
            continue
        if out and i - out[-1].end <= gap:
            out[-1] = Visit(out[-1].i, i, out[-1].date)
        else:
            out.append(Visit(i, i, bars[i]["date"]))
    return out


def dirty(bars, lo, hi):
    """Indices in [lo,hi] whose close sits outside the session range."""
    bad = []
    for i in range(max(0, lo), min(hi, len(bars) - 1) + 1):
        b = bars[i]
        dev = max(max(b["o"], b["c"]) - b["h"], b["l"] - min(b["o"], b["c"]), 0.0)
        if dev > DEV_HARD:
            bad.append(i)
    return bad


def first_break(bars, level, start, end):
    """First bar at or after `start` closing above the level - the breakout."""
    for i in range(start, min(end, len(bars) - 1) + 1):
        if bars[i]["c"] > level:
            return i
    return min(end, len(bars) - 1)


def plan(bars, level, window_start, window_end, tight_bars=TIGHT_BARS):
    """The viewport plan: what plays, what is merely revealed, and the touches.

    Raises Unmatched with a reason naming the rail that refused.
    """
    prior = visits(bars, level, end=window_start)
    if len(prior) < MIN_VISITS:
        raise Unmatched(
            f"only {len(prior)} prior visits to {level:.2f}; need {MIN_VISITS}"
        )

    brk = first_break(bars, level, window_start, window_end)
    oldest = prior[0].i
    if brk - oldest < MIN_HISTORY:
        raise Unmatched(
            f"only {brk - oldest} bars of history behind the oldest visit; "
            f"need {MIN_HISTORY}"
        )

    deep0 = max(0, oldest - DEEP_PAD)
    bad = dirty(bars, deep0, window_end)
    if bad:
        raise Unmatched(
            f"OHLC integrity: {len(bad)} bar(s) with a close outside the "
            f"session range by more than {DEV_HARD}, first at index {bad[0]}"
        )

    live0 = max(deep0, brk - PLAYBACK_MAX)
    tight0 = max(live0, brk - tight_bars)

    return {
        "level": level,
        "breakout": brk,
        "tight0": tight0,
        "live0": live0,
        "deep0": deep0,
        "window_start": window_start,
        "window_end": window_end,
        "touches": [
            {"i": v.i, "date": v.date, "inLive": v.i >= live0} for v in prior
        ],
    }


# ------------------------------------------------------------------ CLI

def _load_series(path):
    src = json.load(open(path))
    bars = []
    for b in src["bars"]:
        o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        # Normalise the cent-level "Last"-sourced overshoot by extending the
        # wick; anything bigger is left alone so `dirty` can quarantine it.
        bars.append({
            "date": b["date"], "o": o, "c": c,
            "h": max(h, o, c) if max(max(o, c) - h, 0) <= DEV_HARD else h,
            "l": min(l, o, c) if max(l - min(o, c), 0) <= DEV_HARD else l,
        })
    return src, bars


def _cards():
    p = os.path.join(REPO, "remotion", "src", "fixtures", "patterns_post", "gallery.json")
    g = json.load(open(p))
    return [c for ch in g["chapters"] for c in ch["cards"]]


_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _mon(date):
    y, m, _ = date.split("-")
    return f"{_MON[int(m) - 1]} {y}"


def _emit_fixture(src, bars, idx, want):
    """The full TradingQuiz props for the zoom reel, rebased to deep0.

    Every number here comes from the detected card or from `plan` - this
    function's whole job is re-indexing and wording, never inventing geometry.
    """
    card = next((c for c in _cards() if c["name"] == want), None)
    if card is None:
        print(f"no card named {want!r}", file=sys.stderr)
        return 1
    st, en = idx[card["from"]], idx[card["to"]]
    try:
        pl = plan(bars, card["levelPrice"], st, en)
    except Unmatched as e:
        print(f"UNMATCHED: {e}", file=sys.stderr)
        return 1

    d0, end = pl["deep0"], pl["window_end"]
    window = bars[d0:end + 1]
    # The quiz must end on the SIGNAL, not on the bar before it. The detected
    # card puts revealFrom ON the breakout, which hid the green close above the
    # rim and left the viewer guessing from the red bar underneath it - the
    # setup looked like a failure at the moment they were asked to call it.
    # +1 so the breakout candle is the last thing shown before the countdown.
    reveal_from = st + card["revealFrom"] - d0 + 1
    n_touch = len(pl["touches"])

    fixture = {
        "kick": "TRADING QUIZ",
        # Explicit empty, not omitted: Remotion merges --props OVER a
        # composition's defaultProps, so an absent key leaves the previous
        # fixture's footer on screen - and that footer says "not a real
        # chart", which is exactly backwards for this reel.
        "footer": "",
        "subject": "",
        "patternName": card["name"].upper(),
        "levelPrice": card["levelPrice"],
        "levelLabel": card["levelLabel"],
        "answer": card["answer"],
        "answerLine": card["answerLine"],
        "ruleTitle": "The setup",
        # No strike rate on screen. The one this card carries (1 of 6) counts
        # 3 trades that were still OPEN at the horizon as failures alongside 2
        # real stop-outs, so it reads as five losses when there were two - it
        # understated the setup rather than qualifying it. Owner call
        # 2026-08-12: cite no frequency claim. The reel instead makes no claim
        # about how often this works, and says the thing that is true of every
        # instance - the stop is decided before the entry.
        "ruleText": (
            "A rounded base that reclaims its rim, then a shallow handle that "
            "holds it. The rim is the trade because it is the level the whole "
            f"base was built against - here it had been tested {n_touch} times "
            f"since {_mon(pl['touches'][0]['date'])}. The stop is chosen before "
            "the entry, so the cost of being wrong is known before the trade "
            "is on."
        ),
        "revealFrom": reveal_from,
        "patternSpan": max(2, card["revealFrom"] // 3),
        "ticker": src["symbol"],
        # SPY is the instrument, the S&P 500 is what it tracks. Both are on
        # screen because the narration says "S and P five hundred" - a viewer
        # hearing the index and reading only the ETF ticker has to reconcile
        # them; showing both removes the question.
        "timeframe": "S&P 500 · DAILY",
        "dateRange": f"{_mon(window[0]['date'])} → {_mon(window[-1]['date'])}",
        "zoom": {
            "live0": pl["live0"] - d0,
            "breakout": pl["breakout"] - d0,
            "historyLabel": f"{pl['level']:.2f} · TESTED {n_touch}× SINCE {_mon(pl['touches'][0]['date'])}",
            "touches": [
                {"i": t["i"] - d0, "date": t["date"], "inLive": t["inLive"]}
                for t in pl["touches"]
            ],
        },
        "entry": card["entry"],
        "stop": card["stop"],
        "target": card["target"],
        "rrLabel": f"1:{card['rr']:g}",
        "candles": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in window],
        "durationInFrames": 1080,
        "_provenance": {
            "symbol": src["symbol"],
            "source": src.get("source"),
            "source_class": "api",
            "retrieved_at": src.get("retrieved_at"),
            "window": f"{window[0]['date']}..{window[-1]['date']}",
            "detector": "scripts/patterns_post/find_real_patterns.py",
            "anchoring": "scripts/ta_quiz/find_anchored_level.py",
        },
    }

    out = os.path.join(REPO, "remotion", "src", "fixtures",
                       "trading_quiz_spy_cup_zoom.json")
    # Explicit UTF-8 + ensure_ascii: the date range carries an arrow, and the
    # default console codepage on Windows is cp1252, which cannot encode it.
    with io.open(out, "w", encoding="utf-8") as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False)
    rel = os.path.relpath(out, REPO).replace("\\", "/")
    print(f"wrote {rel}")
    print(f"  {len(window)} bars {window[0]['date']}..{window[-1]['date']}")
    print(f"  revealFrom={reveal_from}  live0={fixture['zoom']['live0']}  "
          f"breakout={fixture['zoom']['breakout']}")
    print(f"  playback={pl['breakout'] - pl['live0']} bars (cap {PLAYBACK_MAX})")
    print(f"  touches={n_touch}  label={fixture['zoom']['historyLabel']}")
    return 0


def main(argv):
    series_path = os.path.join(REPO, "data", "prices", "SPY_1d_5y_2026-07-30.json")
    src, bars = _load_series(series_path)
    idx = {b["date"]: i for i, b in enumerate(bars)}
    want = "Cup and Handle"

    if "--list" in argv:
        print(f"{'formation':<26} {'level':>8}  {'result'}")
        for c in _cards():
            st, en = idx.get(c["from"]), idx.get(c["to"])
            if st is None or en is None:
                print(f"{c['name']:<26} {c['levelPrice']:>8.2f}  UNMATCHED (window not in series)")
                continue
            try:
                pl = plan(bars, c["levelPrice"], st, en)
                print(f"{c['name']:<26} {c['levelPrice']:>8.2f}  "
                      f"{len(pl['touches'])} visits since {pl['touches'][0]['date']}, "
                      f"playback {pl['breakout'] - pl['live0']} bars, deep {pl['breakout'] - pl['deep0']} bars")
            except Unmatched as e:
                print(f"{c['name']:<26} {c['levelPrice']:>8.2f}  UNMATCHED ({e})")
        return 0

    if "--fixture" in argv:
        return _emit_fixture(src, bars, idx, want)

    card = next((c for c in _cards() if c["name"] == want), None)
    if card is None:
        print(f"no card named {want!r}", file=sys.stderr)
        return 1
    st, en = idx[card["from"]], idx[card["to"]]
    try:
        pl = plan(bars, card["levelPrice"], st, en)
    except Unmatched as e:
        print(f"UNMATCHED: {e}", file=sys.stderr)
        return 1

    pl["symbol"] = src["symbol"]
    pl["source"] = src.get("source")
    pl["retrieved_at"] = src.get("retrieved_at")
    print(json.dumps(pl, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
