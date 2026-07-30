"""Select and prepare the 12 chart formations for the PatternGallery post.

The post is the animated version of the classic "trading chart patterns" cheat
sheet: each formation draws itself, breaks out, stamps its verdict, and the
completed cards assemble into the save-able poster the static sheets only
start as.

Every candle comes from references/ta-pattern-library.json - the validated
synthetic pattern library (see .claude/skills/ta-chart-quiz). These are
IDEALIZED ILLUSTRATIONS by design, like every cheat sheet's diagrams, and the
post's footer says so on every frame. Per CLAUDE.md §10.1 the geometry is
still not authored in the composition: this script computes every overlay
line, and the TSX only decides when and how things draw.

Overlays:
  * every pattern gets its LEVEL (neckline / breakout line) from the library;
  * "needs-overlay" formations (flags, triangles, wedges, megaphone) also get
    two trendlines, least-squares fit over the consolidation span's highs and
    lows - deterministic geometry from the candles, not taste. The
    consolidation span starts at the formation's own extreme (the pole tip for
    flags/pennants, the first bar for the rest) and ends at the breakout.

Usage:
    python scripts/patterns_post/build_fixture.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "references", "ta-pattern-library.json")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "patterns_post", "gallery.json")

# The cheat sheet's greatest hits, grouped the way the reference groups them.
CHAPTERS = [
    ("REVERSAL", "trend reverses", [42, 41, 43, 44]),
    ("CONTINUATION", "trend continues", [54, 52, 57, 58]),
    ("BILATERAL", "breakout decides", [63, 62, 60, 49]),
]


def fit_line(pts):
    """Least-squares y = m*x + c through (i, price) points."""
    n = len(pts)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    denom = n * sxx - sx * sx
    if denom == 0:
        return 0.0, sy / n
    m = (n * sxy - sx * sy) / denom
    c = (sy - m * sx) / n
    return m, c


def trendlines(candles, reveal, bias, family):
    """Upper and lower consolidation lines, or None for pure-level patterns."""
    # The consolidation starts at the formation's own extreme: the pole tip for
    # continuation patterns, the start of the window otherwise.
    if family == "continuation-chart":
        window = candles[:reveal]
        if bias == "bullish":
            start = max(range(len(window)), key=lambda i: window[i]["h"])
        else:
            start = min(range(len(window)), key=lambda i: window[i]["l"])
        start = min(start, reveal - 4)  # need a few bars to fit through
    else:
        start = 1
    span = list(range(start, reveal))
    if len(span) < 4:
        return None
    # Fit through SWING points, not every bar. On a converging pattern the two
    # give the same answer; on a BROADENING one (megaphone), an all-bars fit
    # produces two nearly-flat lines crossing mid-pattern - the exact opposite
    # of the shape. The swing highs/lows are what a human lays the ruler on,
    # and the fit through them diverges correctly.
    sw_hi = [i for i in span[1:-1] if candles[i]["h"] >= candles[i - 1]["h"] and candles[i]["h"] >= candles[i + 1]["h"]]
    sw_lo = [i for i in span[1:-1] if candles[i]["l"] <= candles[i - 1]["l"] and candles[i]["l"] <= candles[i + 1]["l"]]
    hi_pts = [(i, candles[i]["h"]) for i in (sw_hi if len(sw_hi) >= 2 else span)]
    lo_pts = [(i, candles[i]["l"]) for i in (sw_lo if len(sw_lo) >= 2 else span)]
    hi = fit_line(hi_pts)
    lo = fit_line(lo_pts)
    return {
        "from": start,
        "to": reveal,
        "hi": {"m": round(hi[0], 5), "c": round(hi[1], 4)},
        "lo": {"m": round(lo[0], 5), "c": round(lo[1], 4)},
    }


def main():
    lib = {p["id"]: p for p in json.load(open(SRC))["patterns"]}
    chapters = []
    for title, sub, ids in CHAPTERS:
        cards = []
        for pid in ids:
            p = lib[pid]
            reveal = p["revealFrom"]
            tl = trendlines(p["candles"], reveal, p["bias"], p["family"]) if p["renderable"] == "needs-overlay" else None
            cards.append({
                "id": pid,
                "name": p["name"],
                "bias": p["bias"],
                "answer": p["answer"],
                "answerLine": p["answerLine"],
                "context": p["context"],
                "levelPrice": p["levelPrice"],
                "levelLabel": p["levelLabel"],
                "revealFrom": reveal,
                "trend": tl,
                "candles": p["candles"],
            })
            print(f"  {pid:>3} {p['name']:32} {p['bias']:>8} -> {p['answer']:<4} overlay={'yes' if tl else 'level-only'}")
        chapters.append({"title": title, "sub": sub, "cards": cards})

    payload = {
        "source": "references/ta-pattern-library.json (validated synthetic library)",
        "note": "Idealized pattern illustrations - synthetic by design, labelled on every frame.",
        "chapters": chapters,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(payload, open(OUT, "w"), indent=1)
    print(f"\n-> {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
