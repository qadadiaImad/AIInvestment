"""Synthetic breakout-retest fixture for the TradingQuiz engine (Act 3).

Candles are Python-authored and validated (house rule 10.1) — never
model-authored. Shape: range under a ceiling with two clean touches ->
breakout close -> drift -> pullback that RETESTS the level (setup freezes
here for the countdown) -> reveal: hold + rally through the 2R target.
Trade frame is all-four (entry/stop/target/rr, rule 10.5); footer keeps the
SYNTHETIC label.

    python scripts/strategy_reel/make_quiz_fixture.py
Writes remotion/src/fixtures/strategy_quiz_breakout_2026-08-02.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "src", "fixtures",
                   "strategy_quiz_breakout_2026-08-02.json")

LEVEL = 100.0
ENTRY = 100.0
STOP = 99.0        # below the retest low with buffer — set from setup logic
TARGET = 102.0     # entry + 2 * (entry - stop) = 2R exactly

# o, h, l, c — 19 setup bars (range, touch, touch, breakout, drift, retest),
# then 5 reveal bars (hold and rally through target).
CANDLES = [
    (96.2, 97.1, 95.4, 96.8), (96.8, 97.6, 96.1, 97.2), (97.2, 98.4, 96.9, 98.0),
    (98.0, 99.2, 97.6, 98.8), (98.8, 100.1, 98.3, 99.4),   # touch 1 (h ~ level)
    (99.4, 99.8, 98.2, 98.6), (98.6, 99.0, 97.3, 97.7), (97.7, 98.3, 96.8, 97.1),
    (97.1, 98.0, 96.6, 97.8), (97.8, 98.9, 97.4, 98.5),
    (98.5, 100.2, 98.1, 99.6),                              # touch 2
    (99.6, 99.9, 98.4, 98.9), (98.9, 99.4, 98.0, 99.1),
    (99.1, 99.7, 98.6, 99.5),
    (99.5, 101.6, 99.3, 101.3),                             # BREAKOUT close > level
    (101.3, 102.1, 100.9, 101.8), (101.8, 102.0, 101.0, 101.4),
    (101.4, 101.6, 100.3, 100.7),                           # pullback begins
    (100.7, 100.9, 99.6, 100.4),                            # RETEST: low kisses level
    # ---- revealFrom = 19: does the retest hold? ----
    (100.4, 101.2, 100.1, 101.0),                           # hold, buyers step in
    (101.0, 101.9, 100.8, 101.7),
    (101.7, 102.4, 101.5, 102.2),                           # TARGET 102 trades here
    (102.2, 102.6, 101.8, 102.4),
    (102.4, 102.8, 102.0, 102.6),
]
REVEAL_FROM = 19


def validate():
    for i, (o, h, l, c) in enumerate(CANDLES):
        assert h >= max(o, c) and l <= min(o, c), f"bar {i} wick geometry"
        assert h - l < 3.5, f"bar {i} implausible range"
    touches = [i for i, (_, h, _, _) in enumerate(CANDLES[:REVEAL_FROM])
               if abs(h - LEVEL) <= 0.25]
    assert len(touches) >= 2, "need two touches of the level in the setup"
    assert any(c > LEVEL for _, _, _, c in CANDLES[14:REVEAL_FROM]), "need a breakout close"
    rt = CANDLES[REVEAL_FROM - 1]
    assert rt[2] <= LEVEL * 1.005 and rt[3] >= LEVEL * 0.998, "last setup bar must retest"
    assert abs((TARGET - ENTRY) - 2 * (ENTRY - STOP)) < 1e-9, "2R by construction"
    assert max(h for _, h, _, _ in CANDLES[REVEAL_FROM:]) >= TARGET, "reveal must trade target"
    assert min(l for _, _, l, _ in CANDLES[REVEAL_FROM:]) > STOP, "reveal must not stop out"


def main():
    validate()
    fixture = {
        "kick": "STRATEGY QUIZ",
        "patternName": "BREAKOUT + RETEST",
        "levelPrice": LEVEL,
        "levelLabel": "RESISTANCE — TESTED 2×",
        "answer": "BUY",
        "answerLine": "The retest held. Old ceiling, new floor.",
        "ruleTitle": "The setup",
        "ruleText": "A level rejected twice, then broken with a close above. "
                    "The pullback that HOLDS the level is the trade: enter at "
                    "the level, stop below the retest low, target 2R.",
        "footer": "SYNTHETIC example — illustrative, not a real chart — "
                  "educational only, not financial advice",
        "revealFrom": REVEAL_FROM,
        "entry": ENTRY, "stop": STOP, "target": TARGET,
        "durationInFrames": 720,
        "candles": [{"o": o, "h": h, "l": l, "c": c} for o, h, l, c in CANDLES],
    }
    json.dump(fixture, open(OUT, "w"), indent=1)
    print(f"OK {OUT} ({len(CANDLES)} candles, reveal@{REVEAL_FROM})")


if __name__ == "__main__":
    main()
