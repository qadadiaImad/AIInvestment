"""Turn a TA pattern library entry into a Remotion TradingQuiz fixture.

This is what backs the "create a carousel of TA pattern number N" invocation:
one command from library id -> render-ready fixture + the render command.

Usage:
    python scripts/ta_quiz/make_fixture.py 5
    python scripts/ta_quiz/make_fixture.py 5 --out remotion/src/fixtures/my_quiz.json
    python scripts/ta_quiz/make_fixture.py --list
    python scripts/ta_quiz/make_fixture.py --list --family two-candle
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIB = os.path.join(REPO, "references", "ta-pattern-library.json")
FIXTURE_DIR = os.path.join(REPO, "remotion", "src", "fixtures", "ta_quiz")

# Must match TRADING_QUIZ_MIN_FRAMES in TradingQuiz.tsx (5s answer countdown).
DURATION = 546
FOOTER = "Illustrative example, not a real chart — educational only, not financial advice · DYOR"

sys.path.insert(0, HERE)
from validate import validate  # noqa: E402


def load():
    lib = json.load(open(LIB))
    return lib["patterns"] if isinstance(lib, dict) else lib


# How many bars the highlight box should enclose. Boxing two candles around a
# single-candle pattern (a doji, a hammer) visually mislabels it. For multi-bar
# chart formations the box marks the completion bars, not the whole shape —
# outlining a 15-bar head-and-shoulders would swallow the chart.
SPAN_BY_FAMILY = {
    "single-candle": 1,
    "two-candle": 2,
    "three-candle": 3,
    "reversal-chart": 3,
    "continuation-chart": 3,
    "gap-window": 2,
    "structure-level": 3,
    "volume-indicator": 2,
}


def to_fixture(p):
    return {
        "kick": "TRADING QUIZ",
        "patternName": p["name"].upper(),
        "levelPrice": p["levelPrice"],
        "levelLabel": p["levelLabel"],
        "answer": p["answer"],
        "answerLine": p["answerLine"],
        "ruleTitle": p.get("ruleTitle") or "The setup",
        "ruleText": p["ruleText"],
        "footer": FOOTER,
        "revealFrom": p["revealFrom"],
        "patternSpan": SPAN_BY_FAMILY.get(p.get("family"), 2),
        "durationInFrames": DURATION,
        "candles": p["candles"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id", nargs="?", type=int, help="library pattern id")
    ap.add_argument("--out", help="output fixture path")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--family")
    ap.add_argument("--force", action="store_true", help="emit even if validation fails")
    args = ap.parse_args()

    patterns = load()

    if args.list:
        rows = [p for p in patterns if not args.family or p.get("family") == args.family]
        for p in rows:
            flag = "" if p.get("renderable") == "candles-only" else "  [needs-overlay]"
            print(f"{p['id']:>3}  {p['name']:<34} {p.get('family',''):<20} "
                  f"cx{p.get('complexity','?')} {p.get('occurrence',''):<12} {p.get('answer','')}{flag}")
        print(f"\n{len(rows)} patterns")
        return 0

    if args.id is None:
        ap.error("give a pattern id, or --list")

    match = [p for p in patterns if p.get("id") == args.id]
    if not match:
        print(f"no pattern with id {args.id}. Try --list.", file=sys.stderr)
        return 1
    p = match[0]

    errs = validate(p)
    if errs and not args.force:
        print(f"#{p['id']} {p['slug']} FAILS validation — refusing to build a fixture "
              f"that would teach a wrong pattern:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        print("\n(use --force to override)", file=sys.stderr)
        return 2
    if errs:
        print(f"WARNING: emitting despite {len(errs)} validation failure(s)", file=sys.stderr)

    if p.get("renderable") != "candles-only":
        print(f"NOTE: '{p['name']}' is tagged needs-overlay — the current engine draws candles "
              f"plus one horizontal level only, so this may not read correctly.", file=sys.stderr)

    out = args.out or os.path.join(FIXTURE_DIR, f"{p['id']:03d}_{p['slug'].replace('-', '_')}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(to_fixture(p), open(out, "w"), indent=2, ensure_ascii=False)

    rel = os.path.relpath(out, REPO)
    print(f"#{p['id']} {p['name']} ({p.get('family')}, complexity {p.get('complexity')}, "
          f"{p.get('occurrence')}) -> {rel}")
    print("\nRender:")
    print(f"  cd remotion && npx remotion render src/index.ts TradingQuiz \\\n"
          f"    ../content/ta_quiz_{p['slug']}.mp4 \\\n"
          f"    --props=../{rel} \\\n"
          f"    --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \\\n"
          f"    --codec h264 --crf 17")
    return 0


if __name__ == "__main__":
    sys.exit(main())
