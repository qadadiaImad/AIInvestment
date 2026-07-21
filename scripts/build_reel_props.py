"""Live-data props builder for the unified `SlideStoryReel` composition.

Pure `build_props(ticker, halal_bundle, story=None) -> dict` matching
`remotion/src/slides/slideProps.ts`'s `slideStoryPropsSchema` field-for-field
(see docs/superpowers/plans/2026-07-21-reel-factory-unification.md Task 2's
interface block), plus a CLI that reads the live `web/public/data/halal.json`
bundle and writes a props JSON `remotion/src/fixtures/*.json` render can consume:

    python build_reel_props.py WULF --out ../remotion/src/fixtures/generated_wulf.json
    python build_reel_props.py --auto --out ../remotion/src/fixtures/generated.json

`--auto` ranks the next reel via `aiinvest.halal_stories.pick_stories` and
seeds the hook beat's headline from the picked story's `headline_fact`.

Copy rails (spec §5, halal_lint.py's rails): methodology framing only — the
word "haram" never appears in generated copy (no verdict-claim head is
possible if the word is simply never emitted); disclaimer footer always on,
verbatim match to the WULF reel's footer text.

Aborts (exit 2, named reason) rather than emit a half-empty props file when
the verdict has no decisive ratio test AND no business revenue split to
visualize — mirrors the halal-reels/spec "never render a half-empty canvas"
rule, ported to the props-builder boundary.

Educational/research only — not financial advice, not a religious ruling.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from aiinvest import halal_stories

DISCLAIMER = "Computed methodology result — not a fatwa · not financial advice"

_STANDARD_ORDER = ("AAOIFI", "FTSE", "MSCI")

_BAR_STATUSES = {"pass", "fail", "unknown"}

_VERDICT_ENUM = {"halal", "not_halal", "questionable", "insufficient_data"}

_VERDICT_LABEL = {
    "halal": "PASS",
    "not_halal": "FAIL",
    "questionable": "REVIEW",
    "insufficient_data": "INSUFFICIENT DATA",
}

_BADGE_TEXT = {
    "halal": "AAOIFI SCREEN: PASS",
    "not_halal": "AAOIFI SCREEN: FAIL",
    "questionable": "AAOIFI SCREEN: REVIEW",
    "insufficient_data": "AAOIFI SCREEN: INSUFFICIENT DATA",
}

# Beat-kind durations (frames @ 30fps) — mirror the WULF reel's own section
# lengths (halal-reels/src/WulfReel.tsx) so parity mode (Task 2/6) and the
# live builder produce reels of a comparable pace.
_DUR_HOOK = 120
_DUR_BARS = 150
_DUR_DONUT = 130
_DUR_STAMP = 130
_DUR_ENDCARD = 110

_HOOK_SUB = (
    "Muslim investors run a halal screen — a math test for stocks. Watch it work."
)


class InsufficientDataError(Exception):
    """Raised by `build_props` when the verdict lacks decisive data for a story."""


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _pct(x):
    return round(x * 100, 1)


def _binding_test(std):
    """Tightest-margin test with a numeric ratio, or None.

    Ports halal-reels/src/data.ts's `binding()` helper: the binding test is
    the one with the smallest (most-failing) margin among tests that report
    a numeric margin at all.
    """
    tests = [t for t in (std or {}).get("tests", []) if _is_number(t.get("margin"))]
    if not tests:
        return None
    return min(tests, key=lambda t: t["margin"])


def _build_bars(standards):
    bars = []
    for key in _STANDARD_ORDER:
        b = _binding_test(standards.get(key))
        if b is None:
            continue
        status = b.get("status")
        if status not in _BAR_STATUSES:
            status = "unknown"
        bars.append({
            "label": key,
            "ratio": _pct(b["ratio"]) if _is_number(b.get("ratio")) else None,
            "threshold": _pct(b["threshold"]) if _is_number(b.get("threshold")) else 0.0,
            "status": status,
        })
    return bars


def _worst_bar(bars):
    numeric = [b for b in bars if _is_number(b.get("ratio"))]
    if not numeric:
        return None
    return max(numeric, key=lambda b: (b["ratio"] or 0) - (b["threshold"] or 0))


def build_props(ticker, halal_bundle, story=None):
    """Assemble SlideStoryReel props for `ticker` from a halal.json-shaped bundle.

    Pure — no I/O. Raises `InsufficientDataError` (named reason in the message)
    when there is nothing decisive to visualize, rather than emit a half-empty
    props file.
    """
    verdicts = (halal_bundle or {}).get("verdicts", {}) or {}
    v = verdicts.get(ticker)
    if v is None:
        raise InsufficientDataError(f"{ticker}: not present in halal bundle verdicts")

    standards = v.get("standards", {}) or {}
    bars = _build_bars(standards)

    business = v.get("business") or {}
    impermissible = business.get("impermissible_revenue_pct") or {}
    donut_pct = impermissible.get("value")
    donut_pct = donut_pct if _is_number(donut_pct) else None

    if not bars and donut_pct is None:
        raise InsufficientDataError(
            f"{ticker}: no binding ratio test and no business revenue split — "
            "nothing decisive to visualize")

    overall = v.get("overall")
    if overall not in _VERDICT_ENUM:
        overall = "insufficient_data"

    date = (v.get("inputs_asof") or "")[:10] or "unknown date"
    layer = v.get("layer")
    ticker_sub = f"{layer} · SCREEN AS OF {date}" if layer else f"HALAL SCREEN · AS OF {date}"
    badge = _BADGE_TEXT[overall]

    worst = _worst_bar(bars)

    purification = v.get("purification") or {}
    per_share = purification.get("per_share")
    purify_cents = round(per_share * 100) if _is_number(per_share) else None

    beats = []
    vo = []

    # --- hook ---
    if story and story.get("headline_fact"):
        hook_headline = str(story["headline_fact"])
    elif donut_pct is not None:
        hook_headline = f"{ticker} still earns money the halal screen flags."
    elif worst is not None:
        hook_headline = f"{ticker} carries more debt than the halal screen allows."
    else:
        hook_headline = f"{ticker}: does it clear the halal screen?"
    beats.append({
        "kind": "hook", "headline": hook_headline, "sub": _HOOK_SUB,
        "durationInFrames": _DUR_HOOK,
    })
    vo.append(f"{ticker}: let's run the halal screen.")

    # --- bars ---
    if bars:
        labels = ", ".join(b["label"] for b in bars)
        beats.append({
            "kind": "bars", "title": "THE RULEBOOKS AGREE" if len(bars) > 1 else "THE DEBT TEST",
            "caption": f"Checked against {labels}.", "bars": bars,
            "durationInFrames": _DUR_BARS,
        })
        if worst is not None:
            vo.append(
                f"The {worst['label']} debt ratio comes in at {worst['ratio']}%, "
                f"against a {worst['threshold']}% limit.")
        else:
            vo.append(f"Here's what {labels} say about the debt test.")

    # --- donut ---
    if donut_pct is not None:
        tone = "fail" if overall == "not_halal" else ("pass" if overall == "halal" else "warn")
        beats.append({
            "kind": "donut", "title": "THE BUSINESS TEST", "pct": donut_pct,
            "centerLabel": "FLAGGED REVENUE",
            "caption": f"{donut_pct}% of revenue comes from a flagged activity.",
            "tone": tone, "durationInFrames": _DUR_DONUT,
        })
        vo.append(f"{donut_pct} percent of revenue is still tied to a flagged activity.")

    # --- stamp ---
    basis_parts = []
    if worst is not None:
        basis_parts.append(f"{worst['label']} debt {worst['ratio']}% vs a {worst['threshold']}% cap")
    if donut_pct is not None:
        basis_parts.append(f"flagged business {donut_pct}% of revenue")
    basis = " · ".join(basis_parts) or (v.get("overall_basis") or "")
    if purify_cents is not None:
        stamp_line = (
            f"Purification: about {purify_cents} cents a share would go to charity — "
            "the flagged slice doesn't belong in your pocket.")
        vo.append(
            f"Verdict: {_VERDICT_LABEL[overall].lower()}. Purification would send about "
            f"{purify_cents} cents a share to charity.")
    else:
        stamp_line = f"Verdict: {_VERDICT_LABEL[overall].lower()} on the halal screen."
        vo.append(f"Verdict: {_VERDICT_LABEL[overall].lower()} on the halal screen.")
    beats.append({
        "kind": "stamp", "verdict": overall, "basis": basis, "line": stamp_line,
        "durationInFrames": _DUR_STAMP,
    })

    # --- endcard ---
    beats.append({
        "kind": "endcard", "headline": f"{ticker}: the verdict.",
        "sub": f"{_VERDICT_LABEL[overall]} · THE HALAL SCREEN · data as of {date}",
        "durationInFrames": _DUR_ENDCARD,
    })
    vo.append(f"{ticker}: {_VERDICT_LABEL[overall].lower()} on the halal screen, as of {date}.")

    return {
        "ticker": ticker, "tickerSub": ticker_sub, "badge": badge,
        "beats": beats, "vo": vo, "bubbleClips": [], "captions": [],
        "disclaimer": DISCLAIMER,
    }


def _default_bundle_path():
    return pathlib.Path(__file__).resolve().parent.parent / "web" / "public" / "data" / "halal.json"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Build SlideStoryReel props JSON from the live halal.json bundle.")
    ap.add_argument("ticker", nargs="?", help="Ticker symbol (omit when passing --auto).")
    ap.add_argument("--auto", action="store_true",
                    help="Pick the ticker via aiinvest.halal_stories.pick_stories "
                         "(alerts-first ranking) instead of a positional ticker.")
    ap.add_argument("--bundle", default=str(_default_bundle_path()),
                    help="Path to a halal.json-shaped bundle (default: web/public/data/halal.json).")
    ap.add_argument("--out", required=True, help="Output props JSON path.")
    args = ap.parse_args(argv)

    bundle_path = pathlib.Path(args.bundle)
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except OSError as e:
        print(f"error: cannot read bundle {bundle_path}: {e}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"error: {bundle_path} is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(2)

    story = None
    ticker = args.ticker
    if args.auto:
        picked = halal_stories.pick_stories(bundle, top=1)
        if not picked:
            print("error: --auto found no story-worthy ticker in the bundle", file=sys.stderr)
            raise SystemExit(2)
        story = picked[0]
        ticker = story["symbol"]
    if not ticker:
        print("error: a ticker is required unless --auto is passed", file=sys.stderr)
        raise SystemExit(2)

    try:
        props = build_props(ticker, bundle, story=story)
    except InsufficientDataError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(2)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(props, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(props['beats'])} beats, ticker={ticker})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
