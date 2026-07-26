"""Assemble the TradingStyles fixture from three independent sources.

  1. STYLES below — the spec. Number, name, timeframe and hold period. These are
     the factual fields from the reference card and are NOT model-authored; a
     content agent that "improves" a timeframe is overwritten here.
  2. content.json — the model-written copy (oneLiner, bullets, demands, markers),
     produced by the trading-styles-explainer workflow.
  3. regimes.json — the chart simulations, generated and asserted in
     generate_regimes.py.

The split matters: models write prose, Python owns the numbers, and the spec
owns the facts. Copy is validated against its length budget here rather than
trusted, because overlong strings don't fail loudly — they just wrap badly and
push the layout apart.

Usage:
    python scripts/trading_styles/build_fixture.py [content.json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FIXDIR = os.path.join(REPO, "remotion", "src", "fixtures", "trading_styles")
REGIMES = os.path.join(FIXDIR, "regimes.json")
OUT = os.path.join(FIXDIR, "trading_styles.json")

# 30fps: 300 intro + 10 * 360 + 300 outro. Must match TRADING_STYLES_FRAMES.
DURATION = 4200

STYLES = [
    (1,  "SCALPING",           "1m → 15m",           "Seconds – Minutes",        "microrange"),
    (2,  "DAY TRADING",        "5m–15m → 1H–4H",     "Minutes – Hours",          "intraday-session"),
    (3,  "SWING TRADING",      "4H → 1W",            "Days – Weeks",             "swing-leg"),
    (4,  "POSITION TRADING",   "1D → 1M",            "Weeks – Months",           "multimonth-trend"),
    (5,  "TREND TRADING",      "4H–1D → 1W–1M",      "While the trend lasts",    "sustained-trend"),
    (6,  "BREAKOUT TRADING",   "5m–1H → 4H–1D",      "Until the breakout fails", "consolidation-break"),
    (7,  "RANGE TRADING",      "15m–1H → 4H",        "Inside support–resistance","range-bound"),
    (8,  "NEWS TRADING",       "1m–5m → 15m",        "Around the event",         "event-gap"),
    (9,  "ALGORITHMIC",        "Auto entries → auto analysis", "Depends on the system", "systematic"),
    (10, "PORTFOLIO / SIZING", "1D–1W → 1M",         "Long-term rotations",      "rotation"),
]

LIMITS = {"oneLiner": 52, "bullets": 44, "demands": 60}

FOOTER = ("Simulated charts, not real market data · Educational only — not financial advice · DYOR")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(FIXDIR, "content.json")
    content = {c["n"]: c for c in json.load(open(src))}
    regimes = json.load(open(REGIMES))

    over = []
    styles = []
    for n, name, tf, hold, regime in STYLES:
        c = content.get(n)
        if c is None:
            raise SystemExit(f"no content for style {n} ({name})")
        if regime not in regimes:
            raise SystemExit(f"style {n} wants regime '{regime}' which the generator did not emit")

        for f, lim in LIMITS.items():
            vals = c[f] if isinstance(c[f], list) else [c[f]]
            for v in vals:
                if len(v) > lim:
                    over.append(f"  #{n} {f}: {len(v)}/{lim} — {v!r}")

        # The model's `markers` are DISCARDED. They were positioned as guessed
        # fractions by an agent that never saw the generated series, and the
        # first render put a "Buy" marker at the top of the range. Trades now
        # come from generate_regimes.py, which places them on the actual bars
        # and asserts they sit where the label claims.
        trades = regimes[regime].get("trades", [])
        if not trades:
            raise SystemExit(f"regime '{regime}' emitted no trades")
        for t in trades:
            if not 0 <= t["bar"] < len(regimes[regime]["bars"]):
                raise SystemExit(f"{regime} trade '{t['label']}' at bar {t['bar']} is out of range")

        styles.append({
            "n": n, "name": name, "timeframe": tf, "hold": hold, "regime": regime,
            "oneLiner": c["oneLiner"], "bullets": c["bullets"], "demands": c["demands"],
            "markers": trades,
        })

    if over:
        print("copy over its length budget (will wrap and break the layout):")
        print("\n".join(over))
        raise SystemExit(1)

    fixture = {
        "title": "Find Your Trading Style",
        "subtitle": "Ten ways to trade the same chart. The right one depends on your time, "
                    "temperament and goals — not on which looks cleverest.",
        "outroTitle": "There is no best style.",
        "outroLine": "There is only the one you can run for years without burning out. "
                     "Pick for your life, not for the chart.",
        "footer": FOOTER,
        "styles": styles,
        "regimes": regimes,
        "durationInFrames": DURATION,
    }

    json.dump(fixture, open(OUT, "w"), indent=1, ensure_ascii=False)
    total = sum(len(r["bars"]) for r in regimes.values())
    print(f"10 styles, {total} simulated bars -> {os.path.relpath(OUT, REPO)}")
    print(f"duration {DURATION} frames = {DURATION/30:.0f}s = {DURATION//30//60}:{DURATION//30%60:02d}")


if __name__ == "__main__":
    main()
