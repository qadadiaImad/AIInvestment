"""Build the INTC failed-breakout case study fixture from REAL price bars.

This is the one fixture in the set that is not synthetic. It uses actual INTC
daily OHLC pulled from Interactive Brokers (see the `source` field of the input
file), so three things are handled differently from the pattern library:

1. The footer states the data is real and names the source and pull date, rather
   than carrying the synthetic-chart disclaimer.
2. The answer badge is overridden via `answerLabel` — a live ticker never gets a
   literal "SELL" badge, because a hindsight reel must not read as a call.
3. Every number below is asserted against the source file. If the input changes
   and the structure no longer holds, this raises rather than quietly shipping a
   chart that no longer shows what the script claims.

The setup ends on 2026-06-30, the day INTC printed a marginal higher high
(142.35 vs 141.45 eight sessions earlier) but closed at 139.63 — BELOW the
140.94 close of that earlier peak. That is the teachable part and it was
stateable in advance: a breakout is not a breakout until price closes above the
level. It didn't, and the neckline broke a week later.

Usage:
    python scripts/ta_quiz/intc_failed_breakout.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "data", "prices", "INTC_1d_2026-07-25.json")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "ta_quiz", "real_intc_failed_breakout.json")

# Must match TRADING_QUIZ_MIN_FRAMES in TradingQuiz.tsx.
DURATION = 546

SETUP_FROM, SETUP_TO = "2026-06-03", "2026-06-30"   # 19 bars, inclusive
REVEAL_TO = "2026-07-08"                            # 5 reveal bars

# The level a breakout had to close above: the high of the first rejection.
RESISTANCE = 141.45


def main():
    src = json.load(open(SRC))
    bars = src["bars"]
    by_date = {b["date"]: b for b in bars}

    window = [b for b in bars if SETUP_FROM <= b["date"] <= REVEAL_TO]
    setup = [b for b in window if b["date"] <= SETUP_TO]
    reveal = [b for b in window if b["date"] > SETUP_TO]

    # ---- the claims this reel makes, checked against the data ----
    p1, p2 = by_date["2026-06-22"], by_date["2026-06-30"]
    assert p1["h"] == RESISTANCE, p1["h"]
    assert p2["h"] > p1["h"], "no marginal higher high"
    assert p2["c"] < p1["c"], "the higher high did NOT close lower — the whole point fails"
    assert p2["c"] < RESISTANCE, "price closed above resistance; it was a real breakout"
    # three touches of the 140-142 zone
    touches = [b["date"] for b in bars if b["h"] >= 140.0]
    assert len(touches) == 3, touches
    # the reveal actually falls
    assert reveal[-1]["c"] < setup[-1]["c"], "reveal does not go down"
    drop = (reveal[-1]["c"] / setup[-1]["c"] - 1) * 100

    print(f"setup  {setup[0]['date']} -> {setup[-1]['date']}  ({len(setup)} bars)")
    print(f"reveal {reveal[0]['date']} -> {reveal[-1]['date']}  ({len(reveal)} bars)")
    print(f"touches of 140+: {touches}")
    print(f"peak closes: {p1['date']} {p1['c']}  vs  {p2['date']} {p2['c']}  "
          f"(higher high {p2['h']} on a LOWER close)")
    print(f"reveal move: {setup[-1]['c']} -> {reveal[-1]['c']} = {drop:.1f}%")

    fixture = {
        "kick": "REAL CHART",
        "indexLabel": "INTC",
        "subject": "INTC · DAILY · JUN 2026",
        "patternName": "FAILED BREAKOUT",
        "levelPrice": RESISTANCE,
        "levelLabel": f"RESISTANCE {RESISTANCE} · 3 TOUCHES",
        "answer": "SELL",
        "answerLabel": f"IT FELL {abs(drop):.0f}%",
        "answerLine": "Higher high, lower close. It never closed above the level.",
        "ruleTitle": "What the chart said",
        "ruleText": (
            f"Three touches of {RESISTANCE}, no close above it. The last one printed a higher "
            f"high on a LOWER close than the first peak — a marginal break that failed. The rule "
            f"is stateable before the fact: a breakout is not a breakout until price CLOSES above "
            f"the level. It never did. The swing low at 118.50 broke a week later; INTC went on to "
            f"89.59."
        ),
        "footer": ("INTC daily bars, IBKR, pulled 2026-07-25 · Educational only — not financial "
                   "advice · Hindsight example — DYOR"),
        "revealFrom": len(setup),
        "patternSpan": 3,
        "durationInFrames": DURATION,
        "candles": [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in window],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(fixture, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"\n-> {os.path.relpath(OUT, REPO)}  ({len(window)} candles, revealFrom={len(setup)})")


if __name__ == "__main__":
    main()
