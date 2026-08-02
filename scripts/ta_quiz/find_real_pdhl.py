"""Find a REAL failed break above the previous day's high and emit a fixture.

The previous-day-high/low strategy: mark yesterday's high and low before the
open — they are the day's two reference lines. A push above yesterday's high is
only a breakout if price ACCEPTS above the line (closes that hold it). The
other half of the rule — the half this detector hunts — is the failure: real
acceptance that then slips back inside the range and stays there. First breaks
without follow-through get sold, and that is a teachable SELL.

Same discipline as find_real_pattern.py: the detector either finds a window
that already satisfies the definition, or it reports nothing found. It never
nudges data to fit. The decision bar is chosen BY DEFINITION (the last close
above the line — the moment of maximum breakout belief), not by eyeing the
outcome.

Data: an intraday 1-minute IBKR pull (resampled to 5-minute) for the session,
and the daily file for yesterday's high/low. Both cached in data/prices/.

Usage:
    python scripts/ta_quiz/find_real_pdhl.py
"""
import datetime as dt
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PRICES = os.path.join(REPO, "data", "prices")
FIXDIR = os.path.join(REPO, "remotion", "src", "fixtures", "ta_quiz")

DURATION = 682          # must match TRADING_QUIZ_MIN_FRAMES (TradingQuiz.tsx)
LESSON_DURATION = 690   # must match STRATEGY_LESSON_FRAMES (StrategyLesson.tsx)
SETUP_MAX = 62          # most context bars the plot stays readable with
REVEAL = 12             # bars of "what happened next"
DEV_HARD = 0.15         # bars deviating more than this are not trusted


def resample(bars, n):
    """Aggregate 1-minute bars into n-minute OHLC. A trailing partial group is
    dropped — a bar that only traded two of its five minutes is not a bar."""
    out = []
    for i in range(0, len(bars) - n + 1, n):
        ch = bars[i:i + n]
        out.append({
            "date": ch[0]["date"],
            "o": ch[0]["o"],
            "h": max(b["h"] for b in ch),
            "l": min(b["l"] for b in ch),
            "c": ch[-1]["c"],
        })
    return out


def prev_day_levels(daily, session_date):
    """Yesterday's high/low for a session: the latest daily bar BEFORE it,
    provided the calendar gap is bridgeable (weekend/holiday, not a data hole)."""
    prior = [b for b in daily if b["date"] < session_date]
    if not prior:
        return None
    last = max(prior, key=lambda b: b["date"])
    gap = dt.date.fromisoformat(session_date) - dt.date.fromisoformat(last["date"])
    if gap.days > 4:
        return None
    return {"date": last["date"], "pdh": last["h"], "pdl": last["l"]}


def find_setup(bars, pdh, min_above=3, min_reveal=6):
    """The failed break, by definition.

    Price trades inside the range, then closes above the line at least
    `min_above` times (real acceptance, not one poke), then closes back inside
    and NEVER re-accepts for the rest of the tape. The decision bar is the last
    close above the line; it must leave at least `min_reveal` bars of tape to
    reveal. Returns indices, or None — this detector does not negotiate.
    """
    above = [i for i, b in enumerate(bars) if b["c"] > pdh]
    if len(above) < min_above:
        return None
    break_at, decision = above[0], above[-1]
    if break_at == 0 or not any(b["c"] < pdh for b in bars[:break_at]):
        return None                     # must approach from inside the range
    if len(bars) - 1 - decision < min_reveal:
        return None                     # break held to the end — not a failure
    return {"break_at": break_at, "decision": decision, "closes_above": len(above)}


def build_lesson(src_meta, session_date, setup, reveal, lv, hit, start):
    """The sequel reel's fixture: same tape, same lines, explainer beats.

    The beats are timed off the detector's indices (re-based to the trimmed
    window) — the composition never re-derives where the break or the last
    acceptance happened.
    """
    allbars = setup + reveal
    return {
        "kick": "THE LESSON",
        "indexLabel": "#83",
        "subject": f"{src_meta['symbol']} · 5-MIN · {session_date}",
        "levelPrice": lv["pdh"],
        "levelLabel": f"Y-DAY HIGH {lv['pdh']}",
        "level2Price": lv["pdl"],
        "level2Label": f"Y-DAY LOW {lv['pdl']}",
        "breakAt": hit["break_at"] - start,
        "decisionAt": hit["decision"] - start,
        "captions": [
            "Sellers defend yesterday's HIGH. Buyers defend yesterday's LOW.",
            "Price grinds toward the top line…",
            "It breaks above — but a break only counts if the closes HOLD the line.",
            "No acceptance — the closes slip back inside. The break has failed.",
        ],
        "ruleTitle": "LINE → BREAK → ACCEPTANCE",
        "ruleText": (
            "Reach the line, break the line, hold the line. Without the hold, "
            "the first break is usually sold — that is the fade."
        ),
        "footer": (f"{src_meta['symbol']} 5-min bars, IBKR, pulled {src_meta['retrieved_at'][:10]} · "
                   "Educational only — not financial advice · Historical example — DYOR"),
        "durationInFrames": LESSON_DURATION,
        "candles": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in allbars],
    }


# ------------------------------------------------------------------ pipeline

def _load_intraday():
    cands = sorted(glob.glob(os.path.join(PRICES, "*_1m_*.json")))
    if not cands:
        return None
    src = json.load(open(cands[-1]))
    bars, bad = [], set()
    for i, b in enumerate(src["bars"]):
        o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        if max(max(o, c) - h, l - min(o, c), 0.0) > DEV_HARD:
            bad.add(i)
        bars.append({**b, "h": max(h, o, c), "l": min(l, o, c)})
    return src, bars, bad


def main():
    loaded = _load_intraday()
    if not loaded:
        print(f"no 1-minute file in {PRICES}", file=sys.stderr)
        return 2
    src, ones, bad = loaded
    if bad:
        print(f"quarantined 1m bars {sorted(bad)} — refusing the session", file=sys.stderr)
        return 2
    session_date = ones[0]["date"][:10]

    dailies = sorted(glob.glob(os.path.join(PRICES, f"{src['symbol']}_1d_*.json")),
                     key=os.path.getsize, reverse=True)
    if not dailies:
        print(f"no daily file for {src['symbol']} in {PRICES}", file=sys.stderr)
        return 2
    dsrc = json.load(open(dailies[0]))
    lv = prev_day_levels(dsrc["bars"], session_date)
    if not lv:
        print(f"no bridgeable prior day for {session_date}", file=sys.stderr)
        return 2
    pdh, pdl = lv["pdh"], lv["pdl"]

    fives = resample(ones, 5)
    hit = find_setup(fives, pdh)
    if not hit:
        print(f"no failed break above {pdh} in {src['symbol']} {session_date} — UNMATCHED",
              file=sys.stderr)
        return 2

    dec = hit["decision"]
    start = max(0, dec + 1 - SETUP_MAX)
    setup = fives[start:dec + 1]
    reveal = fives[dec + 1:dec + 1 + REVEAL]
    move = (reveal[-1]["c"] / setup[-1]["c"] - 1) * 100
    if reveal[-1]["c"] >= setup[-1]["c"]:
        print("reveal does not fall — no SELL reel in this tape", file=sys.stderr)
        return 2
    touched_pdl = min(b["l"] for b in fives) <= pdl

    print(f"{src['symbol']} {session_date} 5-min · prev day {lv['date']} "
          f"H {pdh} / L {pdl}{'  (PDL TOUCHED — story muddied)' if touched_pdl else ''}")
    print(f"  first close above at bar {hit['break_at']} ({fives[hit['break_at']]['date'][-6:]}), "
          f"{hit['closes_above']} closes above, last at bar {dec} ({fives[dec]['date'][-6:]})")
    print(f"  session high {max(b['h'] for b in fives)} — "
          f"{max(b['h'] for b in fives) - pdh:+.2f} above the line")
    print(f"  reveal: {setup[-1]['c']} -> {reveal[-1]['c']} = {move:+.2f}% "
          f"({reveal[-1]['c'] - setup[-1]['c']:+.2f} pts)")

    allbars = setup + reveal
    fixture = {
        "kick": "REAL CHART",
        "indexLabel": "#83",
        "subject": f"{src['symbol']} · 5-MIN · {session_date}",
        "patternName": "BREAK ABOVE Y-HIGH",
        "levelPrice": pdh,
        "levelLabel": f"Y-DAY HIGH {pdh}",
        "level2Price": pdl,
        "level2Label": f"Y-DAY LOW {pdl}",
        "answer": "SELL",
        "answerLabel": f"BACK INSIDE {move:+.1f}%",
        "answerLine": "The first break above yesterday's high found no acceptance — and got sold straight back into the range.",
        "ruleTitle": "A break needs acceptance",
        "ruleText": (
            "Mark yesterday's high and low before the open — they are the day's two "
            "reference lines. A push above yesterday's high is only a breakout if price "
            "ACCEPTS: closes that keep holding above the line. When the closes slip back "
            "inside, the break has failed — and failed breaks travel. "
            "Line, break, acceptance — in that order."
        ),
        "footer": (f"{src['symbol']} 5-min bars, IBKR, pulled {src['retrieved_at'][:10]} · "
                   "Educational only — not financial advice · Historical example — DYOR"),
        "revealFrom": len(setup),
        "patternSpan": dec - hit["break_at"] + 1,
        "fluidCamera": True,
        "durationInFrames": DURATION,
        "candles": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in allbars],
    }
    os.makedirs(FIXDIR, exist_ok=True)
    out = os.path.join(FIXDIR, "real_pdh_fade.json")
    # utf-8 explicitly: Windows' locale default (cp1252) writes '·' and '—' as
    # single bytes that the UTF-8 bundler then renders as replacement chars.
    json.dump(fixture, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n{len(allbars)} candles -> {os.path.relpath(out, REPO)}")

    lesson = build_lesson(src, session_date, setup, reveal, lv, hit, start)
    out2 = os.path.join(FIXDIR, "real_pdh_fade_lesson.json")
    json.dump(lesson, open(out2, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"lesson fixture -> {os.path.relpath(out2, REPO)} "
          f"(breakAt {lesson['breakAt']}, decisionAt {lesson['decisionAt']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
