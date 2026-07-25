"""Independently validate the TA pattern library's OHLC data.

Deliberately does NOT trust the generating model's own audit: this re-derives
every check arithmetically in plain Python. A pattern whose candles don't
actually form the named pattern would have the reel teaching something false,
so it gets quarantined rather than shipped.

Usage:
    python scripts/ta_quiz/validate.py                 # validate the library
    python scripts/ta_quiz/validate.py --write-clean   # also emit the passing subset
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIB = os.path.join(REPO, "references", "ta-pattern-library.json")
CLEAN = os.path.join(REPO, "references", "ta-pattern-library.validated.json")


def body(k):
    return abs(k["c"] - k["o"])


def upper_wick(k):
    return k["h"] - max(k["o"], k["c"])


def lower_wick(k):
    return min(k["o"], k["c"]) - k["l"]


def is_up(k):
    return k["c"] >= k["o"]


# ----------------------------------------------------------------- universal
def check_ohlc_integrity(p):
    """h must contain the body from above, l from below. Non-negotiable."""
    errs = []
    for i, k in enumerate(p["candles"]):
        if k["h"] < max(k["o"], k["c"]) - 1e-9:
            errs.append(f"candle {i}: high {k['h']} below body top {max(k['o'], k['c'])}")
        if k["l"] > min(k["o"], k["c"]) + 1e-9:
            errs.append(f"candle {i}: low {k['l']} above body bottom {min(k['o'], k['c'])}")
        if k["h"] < k["l"]:
            errs.append(f"candle {i}: high {k['h']} below low {k['l']}")
    return errs


def check_structure(p):
    errs = []
    n = len(p["candles"])
    if n < 8:
        errs.append(f"only {n} candles; need at least 8 for readable context")
    rf = p.get("revealFrom")
    if not isinstance(rf, int) or rf < 3 or rf > n - 2:
        errs.append(f"revealFrom {rf} out of range for {n} candles (need 3..{n - 2})")
    if p.get("answer") not in ("BUY", "SELL"):
        errs.append(f"answer must be BUY or SELL, got {p.get('answer')!r}")
    return errs


def check_level_touched(p):
    """The stated level has to be a price the chart actually interacts with,
    otherwise the 'tested N times' label is decoration."""
    lvl = p.get("levelPrice")
    if lvl is None:
        return ["no levelPrice"]
    lo = min(k["l"] for k in p["candles"])
    hi = max(k["h"] for k in p["candles"])
    if not (lo <= lvl <= hi):
        return [f"levelPrice {lvl} outside the chart range {lo}-{hi}"]
    span = hi - lo
    touches = sum(1 for k in p["candles"] if k["l"] - span * 0.02 <= lvl <= k["h"] + span * 0.02)
    if touches < 2:
        return [f"levelPrice {lvl} only touched by {touches} candle(s); not a tested level"]
    return []


def check_reveal_direction(p):
    """A SELL answer whose reveal candles rally is a broken lesson."""
    rf = p["revealFrom"]
    reveal = p["candles"][rf:]
    if len(reveal) < 2:
        return ["fewer than 2 reveal candles"]
    start = p["candles"][rf - 1]["c"]
    end = reveal[-1]["c"]
    span = max(k["h"] for k in p["candles"]) - min(k["l"] for k in p["candles"])
    move = end - start
    if abs(move) < span * 0.02:
        return [f"reveal barely moves ({move:+.2f}); the answer isn't demonstrated"]
    if p["answer"] == "SELL" and move > 0:
        return [f"answer SELL but reveal closes {move:+.2f} higher"]
    if p["answer"] == "BUY" and move < 0:
        return [f"answer BUY but reveal closes {move:+.2f} lower"]
    return []


# ---------------------------------------------------- pattern-specific checks
def check_engulfing(p):
    rf = p["revealFrom"]
    a, b = p["candles"][rf - 2], p["candles"][rf - 1]
    bear = "bearish" in p["slug"]
    if bear:
        if not (is_up(a) and not is_up(b)):
            return ["bearish engulfing needs an up candle then a down candle"]
        if not (b["o"] > a["c"] and b["c"] < a["o"]):
            return [f"body doesn't engulf: open {b['o']} vs prior close {a['c']}, close {b['c']} vs prior open {a['o']}"]
    else:
        if not (not is_up(a) and is_up(b)):
            return ["bullish engulfing needs a down candle then an up candle"]
        if not (b["o"] < a["c"] and b["c"] > a["o"]):
            return [f"body doesn't engulf: open {b['o']} vs prior close {a['c']}, close {b['c']} vs prior open {a['o']}"]
    return []


def check_hammer_like(p):
    """hammer / hanging man: long lower wick, small body, minimal upper wick."""
    k = p["candles"][p["revealFrom"] - 1]
    bd = body(k) or 1e-9
    if lower_wick(k) < 2 * bd:
        return [f"lower wick {lower_wick(k):.2f} is not >= 2x body {bd:.2f}"]
    if upper_wick(k) > bd:
        return [f"upper wick {upper_wick(k):.2f} too large vs body {bd:.2f}"]
    return []


def check_star_like(p):
    """shooting star / inverted hammer: long upper wick, small body."""
    k = p["candles"][p["revealFrom"] - 1]
    bd = body(k) or 1e-9
    if upper_wick(k) < 2 * bd:
        return [f"upper wick {upper_wick(k):.2f} is not >= 2x body {bd:.2f}"]
    if lower_wick(k) > bd:
        return [f"lower wick {lower_wick(k):.2f} too large vs body {bd:.2f}"]
    return []


def check_doji(p):
    k = p["candles"][p["revealFrom"] - 1]
    rng = k["h"] - k["l"] or 1e-9
    if body(k) / rng > 0.1:
        return [f"body is {body(k) / rng:.0%} of range; a doji needs <=10%"]
    return []


def check_harami(p):
    rf = p["revealFrom"]
    a, b = p["candles"][rf - 2], p["candles"][rf - 1]
    if not (max(b["o"], b["c"]) < max(a["o"], a["c"]) and min(b["o"], b["c"]) > min(a["o"], a["c"])):
        return ["second body is not contained inside the first"]
    return []


def check_three_soldiers_crows(p):
    rf = p["revealFrom"]
    trio = p["candles"][rf - 3:rf]
    if len(trio) < 3:
        return ["needs 3 candles"]
    up = "soldier" in p["slug"]
    for i, k in enumerate(trio):
        if is_up(k) != up:
            return [f"candle {i} of the trio is the wrong colour"]
    for i in range(1, 3):
        if up and trio[i]["c"] <= trio[i - 1]["c"]:
            return ["closes are not progressively higher"]
        if not up and trio[i]["c"] >= trio[i - 1]["c"]:
            return ["closes are not progressively lower"]
    return []



def check_star(p):
    """morning/evening star: long body, small-bodied middle, then a close back
    beyond the midpoint of the first body."""
    rf = p["revealFrom"]
    if rf < 3:
        return ["needs 3 setup candles"]
    a, b, c = p["candles"][rf - 3], p["candles"][rf - 2], p["candles"][rf - 1]
    bull = "morning" in p["slug"]
    if is_up(a) == bull:
        return [f"first candle should oppose the reversal (expected {'down' if bull else 'up'})"]
    if body(b) > body(a) * 0.5:
        return [f"middle body {body(b):.2f} is not small vs first body {body(a):.2f}"]
    if is_up(c) != bull:
        return [f"third candle should be {'bullish' if bull else 'bearish'}"]
    mid = (a["o"] + a["c"]) / 2
    if bull and c["c"] <= mid:
        return [f"third close {c['c']} does not clear the first body midpoint {mid:.2f}"]
    if not bull and c["c"] >= mid:
        return [f"third close {c['c']} does not clear below the first body midpoint {mid:.2f}"]
    return []


def check_piercing_darkcloud(p):
    rf = p["revealFrom"]
    a, b = p["candles"][rf - 2], p["candles"][rf - 1]
    bull = "piercing" in p["slug"]
    if is_up(a) == bull:
        return ["first candle should oppose the reversal"]
    if is_up(b) != bull:
        return ["second candle is the wrong direction"]
    mid = (a["o"] + a["c"]) / 2
    if bull and not (b["o"] < a["l"] or b["o"] < a["c"]):
        return ["second candle should open below the prior close/low"]
    if bull and b["c"] <= mid:
        return [f"close {b['c']} does not pierce past the midpoint {mid:.2f}"]
    if not bull and b["c"] >= mid:
        return [f"close {b['c']} does not cut below the midpoint {mid:.2f}"]
    return []


def check_tweezer(p):
    rf = p["revealFrom"]
    a, b = p["candles"][rf - 2], p["candles"][rf - 1]
    top = "top" in p["slug"]
    span = max(k["h"] for k in p["candles"]) - min(k["l"] for k in p["candles"])
    tol = span * 0.01
    if top and abs(a["h"] - b["h"]) > tol:
        return [f"highs {a['h']} and {b['h']} are not matched"]
    if not top and abs(a["l"] - b["l"]) > tol:
        return [f"lows {a['l']} and {b['l']} are not matched"]
    return []


def check_marubozu(p):
    k = p["candles"][p["revealFrom"] - 1]
    rng = k["h"] - k["l"] or 1e-9
    if (upper_wick(k) + lower_wick(k)) / rng > 0.06:
        return [f"wicks are {(upper_wick(k) + lower_wick(k)) / rng:.0%} of range; a marubozu has almost none"]
    if ("bullish" in p["slug"]) != is_up(k):
        return ["candle direction does not match the name"]
    return []


SPECIFIC = [
    ("morning-star", check_star),
    ("evening-star", check_star),
    ("morning-doji-star", check_star),
    ("evening-doji-star", check_star),
    ("piercing-line", check_piercing_darkcloud),
    ("dark-cloud-cover", check_piercing_darkcloud),
    ("tweezer", check_tweezer),
    ("marubozu", check_marubozu),
    ("engulfing", check_engulfing),
    ("harami", check_harami),
    ("hammer", check_hammer_like),
    ("hanging-man", check_hammer_like),
    ("shooting-star", check_star_like),
    ("inverted-hammer", check_star_like),
    ("doji", check_doji),
    ("three-white-soldiers", check_three_soldiers_crows),
    ("three-black-crows", check_three_soldiers_crows),
]


def validate(p):
    errs = []
    errs += check_ohlc_integrity(p)
    errs += check_structure(p)
    if errs:  # later checks index into the data; don't run them on broken shapes
        return errs
    errs += check_level_touched(p)
    errs += check_reveal_direction(p)
    slug = p.get("slug", "")
    for key, fn in SPECIFIC:
        if key in slug:
            try:
                errs += fn(p)
            except Exception as e:  # noqa: BLE001 - a crash here is itself a failure
                errs.append(f"{key} check crashed: {e}")
            break
    return errs


def suspect_trigger_displacement(p):
    """Heuristic for the off-by-one bug class the generator kept producing: the
    pattern's decisive bar (the engulfing candle, the sweep wick, the star's
    third candle) ends up at index `revealFrom` — inside the reveal window —
    instead of being the last setup bar. The viewer is then quizzed on a chart
    that doesn't contain the pattern, and the answer is given away.

    Signature: the first reveal candle dwarfs the last setup candle. Returns a
    bool, not an error — it only ever triggers an attempted repair, and the
    repair is kept solely if the shifted version still validates.
    """
    rf = p.get("revealFrom")
    ks = p.get("candles") or []
    if not isinstance(rf, int) or rf < 1 or rf >= len(ks):
        return False
    rng = lambda k: k["h"] - k["l"]  # noqa: E731
    last_setup, first_reveal = rng(ks[rf - 1]), rng(ks[rf])
    med = sorted(rng(k) for k in ks)[len(ks) // 2]
    if last_setup <= 0 or med <= 0:
        return False
    return first_reveal > last_setup * 2 and first_reveal > med * 1.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-clean", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(LIB):
        print(f"library not found: {LIB}", file=sys.stderr)
        return 1

    lib = json.load(open(LIB))
    patterns = lib["patterns"] if isinstance(lib, dict) else lib

    passed, failed = [], []
    for p in patterns:
        errs = validate(p)
        (passed if not errs else failed).append((p, errs))

    print(f"{len(passed)}/{len(patterns)} patterns pass independent validation\n")
    if failed:
        print("QUARANTINED:")
        for p, errs in failed:
            print(f"  #{p.get('id', '?'):>3} {p.get('slug', '?')}")
            for e in errs[:3]:
                print(f"        - {e}")
    # Coverage by how renderable each one is on the current engine.
    only = sum(1 for p, _ in passed if p.get("renderable") == "candles-only")
    print(f"\nof the {len(passed)} passing: {only} render on the current candles-only engine, "
          f"{len(passed) - only} need overlays (trendlines/indicators/volume)")

    if args.write_clean:
        out = [p for p, _ in passed]
        json.dump({"patterns": out}, open(CLEAN, "w"), indent=2)
        print(f"\nwrote {len(out)} validated patterns -> {os.path.relpath(CLEAN, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
