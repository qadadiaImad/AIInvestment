"""Halal-verdict carousel generator — v4 idiom, story-picker driven.

Renders 3-slide posts (hook / data / takeaway) per story from the verdict engine.
Reads web/public/data/halal.json and calls aiinvest.halal_stories.pick_stories.

    python higgs/_build_v4_halal.py --ticker WKEY
    python higgs/_build_v4_halal.py --top 3

Output filenames: v4_halal_{ticker_lower}_{1|2|3}_{hook|data|takeaway}.png  (1080x1350)

Copy rails (Global Constraints):
  - No first person; attribute to "analysts"/"screens", never direct advisor voice.
  - Verdict language stays methodology-framed — never "haram" as an accusation head.
  - Educational disclaimer required on every takeaway slide.
  - Social narrative: hook → tension → reveal → so-what.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

HIGGS = pathlib.Path(__file__).resolve().parent
ROOT = HIGGS.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from aiinvest.halal_stories import pick_stories  # noqa: E402

W, H = 1080, 1350

# --------------------------------------------------------------------------- CSS base (v4 idiom)

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"
BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:78px 74px;display:flex;flex-direction:column;z-index:2}}
.hdr{{display:flex;align-items:center;gap:22px}}
.tkr{{font-family:'JetBrains Mono';font-weight:800;font-size:72px;line-height:.9;letter-spacing:-1px;color:#fff}}
.ex{{font-family:'JetBrains Mono';font-weight:600;font-size:20px;letter-spacing:3px;color:#34D399;margin-top:6px}}
.foot{{font-family:'JetBrains Mono';font-size:17px;color:#8893A4;letter-spacing:.5px}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:23px;letter-spacing:4px;color:#34D399}}
.head{{font-family:Fraunces;font-weight:600;line-height:1.03;letter-spacing:-2px;text-shadow:0 4px 30px rgba(0,0,0,.6)}}
"""


def _page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"


def _topbar(sym, verdict):
    """Ticker header strip — no logo chip needed (solid bg approach per plan §Interfaces)."""
    tone_color = {"halal": "#10B981", "not_halal": "#EF4444", "questionable": "#F59E0B"}.get(verdict, "#8893A4")
    badge_label = {"halal": "HALAL", "not_halal": "NOT HALAL", "questionable": "QUESTIONABLE"}.get(verdict, verdict.upper())
    return f"""<div class='hdr'>
      <div><div class='tkr'>{sym}</div><div class='ex'>HALAL SCREEN · AAOIFI BASIS</div></div>
      <div style="margin-left:auto;font-family:'JetBrains Mono';font-weight:700;font-size:22px;
           color:{tone_color};border:2px solid {tone_color};border-radius:10px;padding:10px 20px;white-space:nowrap">
           {badge_label}</div></div>"""


# --------------------------------------------------------------------------- slide builders (v4 idiom)

def slide_hook(sym, verdict, kick, head, sub,
               foot="Educational · not financial advice   ·   swipe →"):
    """Hook slide — solid dark bg (no hero image required for v1.2)."""
    scrim = "linear-gradient(180deg,rgba(10,13,18,.74) 0%,rgba(10,13,18,.28) 36%,rgba(10,13,18,.45) 60%,rgba(10,13,18,.93) 100%)"
    bar = _topbar(sym, verdict)
    return _page(f"""
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{bar}
      <div style='margin-top:28px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:auto;font-size:76px">{head}</div>
      <div style="font-size:31px;line-height:1.4;color:#D7DEE8;margin-top:24px;max-width:850px;text-shadow:0 2px 16px rgba(0,0,0,.75)">{sub}</div>
      <div class='foot' style='margin-top:32px'>{foot}</div></div>""")


def slide_data(sym, verdict, tests, caption,
               foot=""):
    """Data slide — bar chart of AAOIFI ratio vs threshold.

    Each test: dict with keys label, ratio, threshold, status.
    Bar length = min(ratio/threshold, 4) on a 0-4 scale; threshold at 25% of bar width.
    Green = pass, Red = fail, Grey = unknown.
    A vertical dashed line marks the threshold position (25% along bar area).
    """
    bar = _topbar(sym, verdict)
    kick = "WORKED MATH · AAOIFI SS 21"

    def _status_color(st):
        return {"pass": "#10B981", "fail": "#EF4444"}.get(st, "#6B7787")

    def _fmt_ratio(r):
        if r is None:
            return "—"
        return f"{r * 100:.1f}%" if r < 2 else f"{r:.2f}x"

    # threshold marker sits at 25% of bar width
    THRESHOLD_PCT = 25.0

    bars_html = ""
    for t in tests:
        ratio = t.get("ratio")
        threshold = t.get("threshold") or 0.3
        status = t.get("status", "unknown")
        label = t.get("label", "")

        if ratio is None or status == "unknown":
            val_text = "—"
            bar_w = 0
            color = "#6B7787"
        else:
            # Normalise: ratio=threshold => bar at THRESHOLD_PCT; cap at 4x threshold
            capped = min(ratio / threshold, 4.0)
            # scale so capped==1 lands at THRESHOLD_PCT, capped==4 lands at ~90%
            bar_w = THRESHOLD_PCT * capped
            bar_w = min(bar_w, 96.0)
            val_text = _fmt_ratio(ratio)
            color = _status_color(status)

        threshold_text = _fmt_ratio(threshold)

        bars_html += f"""<div style='display:flex;align-items:center;margin:18px 0'>
          <div style="width:260px;font-family:'JetBrains Mono';font-weight:600;font-size:22px;color:#E8EDF2;padding-right:12px">{label}</div>
          <div style='flex:1;position:relative;height:38px'>
            <div style='position:absolute;left:0;top:4px;height:30px;width:{bar_w:.1f}%;background:{color};border-radius:6px;opacity:.85'></div>
            <div style='position:absolute;left:{THRESHOLD_PCT:.1f}%;top:-6px;bottom:-6px;border-left:2px dashed rgba(255,255,255,.5)'></div>
            <div style="position:absolute;left:{THRESHOLD_PCT:.1f}%;top:-26px;font-family:'JetBrains Mono';font-size:15px;color:#8893A4;padding-left:4px">limit {threshold_text}</div>
            <div style="position:absolute;left:calc({bar_w:.1f}% + 10px);top:4px;font-family:'JetBrains Mono';font-weight:700;font-size:24px;color:#E8EDF2">{val_text}</div>
          </div></div>"""

    return _page(f"""
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 28%,rgba(10,13,18,.5) 100%)"></div>
    <div class='pad'>{bar}
      <div style='margin-top:24px' class='kick'>{kick}</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:50px;line-height:1.04;letter-spacing:-1px;margin-top:10px">Ratio vs Threshold</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style='position:relative;margin-top:20px'>{bars_html}</div>
        <div style="color:#34D399;font-weight:600;font-size:26px;margin-top:30px">{caption}</div>
      </div>
      <div class='foot'>{foot}</div></div>""")


def slide_takeaway(sym, verdict, big_str, label, body,
                   foot="Computed methodology results — not a fatwa, not financial advice. Educational only."):
    """Takeaway slide — big decisive number + verdict badge + disclaimer."""
    bar = _topbar(sym, verdict)
    kick = "SCREEN RESULT"
    tone_color = {"halal": "#10B981", "not_halal": "#EF4444", "questionable": "#F59E0B"}.get(verdict, "#8893A4")
    scrim = "linear-gradient(180deg,rgba(10,13,18,.80) 0%,rgba(10,13,18,.42) 45%,rgba(10,13,18,.93) 100%)"

    return _page(f"""
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{bar}
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div class='kick'>{kick}</div>
        <div style="font-family:Fraunces;font-weight:700;font-size:180px;line-height:.86;letter-spacing:-6px;margin-top:16px;
             background:linear-gradient(180deg,#fff,{tone_color});-webkit-background-clip:text;-webkit-text-fill-color:transparent">{big_str}</div>
        <div style="font-family:'JetBrains Mono';font-size:24px;letter-spacing:2px;color:#CFE8DD;margin-top:14px">{label}</div>
        <div style="font-size:30px;line-height:1.42;color:#D7DEE8;margin-top:38px;max-width:860px">{body}</div>
      </div>
      <div class='foot'>{foot}</div></div>""")


# --------------------------------------------------------------------------- story -> slides

def _fmt_ratio(r):
    """Format ratio for display — matches halal_stories._fmt_ratio."""
    if r is None:
        return "—"
    return f"{r * 100:.1f}%" if r < 2 else f"{r:.2f}x"


def _hook_head_for_kind(kind, sym, numbers):
    """Build the hook headline text per the slide-content contract in the plan."""
    if kind == "flip":
        was = next((n["value"] for n in numbers if n["label"] == "was"), "?")
        now = next((n["value"] for n in numbers if n["label"] == "now"), "?")
        return f"{sym} just changed status: {was} → {now}"
    elif kind == "extreme_ratio":
        value = next((n["value"] for n in numbers if n["label"] not in ("limit",)), "?")
        limit = next((n["value"] for n in numbers if n["label"] == "limit"), "?")
        return f"{sym} holds {value} against a {limit} cap"
    elif kind == "business_override":
        return f"Every ratio passes. {sym} still fails."
    elif kind == "margin_squeeze":
        value = next((n["value"] for n in numbers if n["label"] not in ("limit",)), "?")
        limit = next((n["value"] for n in numbers if n["label"] == "limit"), "?")
        return f"{sym} misses by a whisker: {value} vs {limit}"
    return numbers[0]["value"] if numbers else sym


def _hook_sub_for_kind(kind):
    """One-line methodology framing for the sub-head."""
    if kind == "flip":
        return "Status changed on the latest data pull. Computed under AAOIFI SS 21 — worked math on the next slide."
    elif kind == "extreme_ratio":
        return "Computed under AAOIFI SS 21 — worked math inside."
    elif kind == "business_override":
        return "Business activity classification takes precedence — AAOIFI SS 21 prohibits the sector regardless of ratios."
    elif kind == "margin_squeeze":
        return "Screens cut off at the published threshold. Computed under AAOIFI SS 21 — worked math inside."
    return "Computed under AAOIFI SS 21 — worked math inside."


def _decisive_number(story, verdict_data):
    """Pick the single most important number for the takeaway big-digit."""
    numbers = story.get("numbers", [])
    if not numbers:
        return "—", "ratio"
    # First number that isn't "limit" is the decisive value
    for n in numbers:
        if n.get("label", "").lower() not in ("limit", "was"):
            return n["value"], n.get("label", "ratio")
    return numbers[0]["value"], numbers[0].get("label", "ratio")


def build_slides(story, verdict_data):
    """Build the 3 slides for one story. Returns [(filename, html), ...]."""
    sym = story["symbol"]
    kind = story["kind"]
    verdict = story.get("verdict", "unknown")
    numbers = story.get("numbers", [])
    headline_fact = story.get("headline_fact", "")

    # --- hook slide ---
    kick = "HALAL SCREEN · AAOIFI BASIS"
    head = _hook_head_for_kind(kind, sym, numbers)
    sub = _hook_sub_for_kind(kind)
    html_hook = slide_hook(sym, verdict, kick, head, sub)

    # --- data slide ---
    # Pull AAOIFI tests from the verdict if available, else synthesise from story numbers
    tests = []
    if verdict_data:
        aaoifi = verdict_data.get("standards", {}).get("AAOIFI", {})
        tests = aaoifi.get("tests", [])
    if not tests and numbers:
        # Fallback: reconstruct from the story numbers (for flip kind or missing verdict)
        for n in numbers:
            if n.get("label") != "limit":
                tests.append({"label": n.get("label", "ratio"), "ratio": None, "threshold": 0.3, "status": "unknown"})

    inputs_asof = (verdict_data or {}).get("inputs_asof", "")
    caption_date = inputs_asof[:10] if inputs_asof else "latest"
    caption = f"Source: TradingView-sourced, stamped {caption_date}. AAOIFI SS 21 thresholds."
    html_data = slide_data(sym, verdict, tests, caption)

    # --- takeaway slide ---
    big_str, big_label = _decisive_number(story, verdict_data)
    body = (f"Analysts screen {sym} under AAOIFI SS 21 methodology. {headline_fact}. "
            "Ratios use spot market cap as denominator per AAOIFI clause 3/4/5.")
    html_takeaway = slide_takeaway(sym, verdict, big_str, big_label, body)

    tkl = sym.lower()
    return [
        (f"v4_halal_{tkl}_1_hook.png", html_hook),
        (f"v4_halal_{tkl}_2_data.png", html_data),
        (f"v4_halal_{tkl}_3_takeaway.png", html_takeaway),
    ]


# --------------------------------------------------------------------------- I/O

def load_verdicts():
    """Load halal.json from web/public/data/."""
    path = ROOT / "web" / "public" / "data" / "halal.json"
    if not path.exists():
        raise FileNotFoundError(f"halal.json not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render halal-verdict carousel slides (v4 idiom).")
    ap.add_argument("--ticker", help="Single ticker to render (e.g. WKEY).")
    ap.add_argument("--top", type=int, default=3, help="Number of top stories to render (default 3).")
    args = ap.parse_args(argv)

    bundle = load_verdicts()
    verdicts = bundle.get("verdicts", {})

    if args.ticker:
        ticker = args.ticker.upper()
        if ticker not in verdicts:
            print(f"WARN: {ticker} not in halal.json — attempting story-picker with synthetic bundle.")
            single_bundle = {"verdicts": {ticker: verdicts.get(ticker, {})}} if ticker in verdicts else {"verdicts": {}}
        else:
            single_bundle = {"verdicts": {ticker: verdicts[ticker]}}
        stories = pick_stories(single_bundle, top=1)
        if not stories:
            print(f"No story generated for {ticker} — it may be a passing name with no notable signal.")
            print("Generating a generic data slide for it regardless.")
            # Build a minimal synthetic story so the CLI still emits PNGs
            v = verdicts.get(ticker, {})
            stories = [{
                "symbol": ticker,
                "kind": "extreme_ratio",
                "score": 0.0,
                "headline_fact": f"{ticker} halal screen result",
                "numbers": [],
                "verdict": v.get("overall", "unknown"),
            }]
    else:
        stories = pick_stories(bundle, top=args.top)

    if not stories:
        print("No stories to render — halal.json may be empty or all names pass without signal.")
        return 1

    # Collect all slides
    all_slides = []
    for story in stories:
        sym = story["symbol"]
        vdata = verdicts.get(sym)
        all_slides.extend(build_slides(story, vdata))

    print(f"Rendering {len(all_slides)} slides for {len(stories)} stories...")

    # Playwright render loop — verbatim from _build_v4.py:260-269
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H})
        for name, html in all_slides:
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(HIGGS / name), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered", name)
        b.close()

    print(f"DONE  stories={len(stories)}  slides={len(all_slides)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
