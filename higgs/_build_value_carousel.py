"""Standalone IG carousel: "This stock costs $548. A model says it's worth
$86." -- a PRICE vs FUNDAMENTAL VALUE teaching post, built from LIVE data in
web/public/data/site.json's `screener` array (generated 2026-07-22T09:47:01Z)
plus a live /screener page capture (2026-07-23) showing the real
price / fundamental-value / discount columns.

Same brand system + browser-frame screenshot pattern as
_build_systemic_risk_carousel.py / _build_congress_carousel.py (giant-stat-slide
family), reused here for consistency across the showcase series. Not tied to
the daily-post/reels-kit pipeline -- a standalone 9-slide 4:5 (2160x2700 @
device_scale_factor=2) carousel.

THE IDEA: a stock's PRICE is only an indicator of what it's worth -- set by
supply & demand -- not what it's actually worth. Fundamental value is what a
model estimates the business is worth. Famous investors (Buffett, Graham)
built their whole approach on that gap. We show it shocking both ways: stocks
priced WAY above a fundamental-value model's estimate (critically
"overvalued" per the model), then the flip -- stocks priced WAY below (deeply
"undervalued" per the model).

HARD RAILS (non-negotiable, see CLAUDE.md task):
  - NEVER name the data vendor anywhere (slides, caption, code). The
    fundamental value is always "a fundamental-value model" 's estimate.
  - Fundamental value is a MODEL ESTIMATE, not ground truth. Every
    over/undervalued claim is framed as "a fundamental-value model
    estimates/pegs/says" + "a read, not a call" -- the model can be wrong.
    No recommendations, no promised price targets, no buy/sell language.
  - Every slide footer carries: "A fundamental-value model's estimate -- a
    read, not a call" + the educational/NFA disclaimer.
  - Buffett / Graham quotes are attributed correctly; both are famous public
    quotes reproduced verbatim (short, attributed -- not a copyright issue).

Screenshots captured LIVE (2026-07-23) via Chrome automation of
https://highreturnethicalscreen.vercel.app/screener, staged in
higgs/_platform_src/:
  value_overvalued.jpg  -- table sorted by "vs Price %" ascending (most
                           negative / most overvalued first): WDC, STX, CIEN,
                           INTC, COHR all visible with SYMBOL / PRICE /
                           FUND. VAL / VS PRICE % columns, header included.
  value_undervalued.jpg -- table sorted by "vs Price %" descending, scrolled
                           to the real (non-null) cluster: TEAM, DUOL, SMCI,
                           INTU, ADBE all visible with the same 4 columns.
  value_tool_wide.jpg   -- full-column default view (Symbol/Layer/Price/PE/
                           Net margin/ROE/Rev YoY/1Y/1Y%/5Y%/Fund. val/
                           vs Price%/Next catalyst/Sector/Halal) -- "the whole
                           tool" wide shot, header included, still legible.
Live page values drift slightly from the 2026-07-22 site.json snapshot used
for slide copy (market moves daily) -- expected, both are dated and the
screenshots are proof-of-tool, not the numeric source of truth for the copy.

    python higgs/_build_value_carousel.py

Writes 9 PNGs + caption.txt + manifest.json to higgs/value_showcase_<date>/.
"""
from __future__ import annotations

import base64
import json
import pathlib
from datetime import datetime, timezone

HIGGS = pathlib.Path(__file__).resolve().parent
ROOT = HIGGS.parent
SRC = HIGGS / "_platform_src"
DATE = "2026-07-23"
OUT = HIGGS / f"value_showcase_{DATE}"

W, H = 1080, 1350  # CSS px canvas; device_scale_factor=2 -> 2160x2700 output

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;0,9..144,900;1,9..144,500;1,9..144,600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"

BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:64px 64px;display:flex;flex-direction:column;z-index:2}}
.brand{{display:flex;align-items:baseline;gap:2px;font-family:'JetBrains Mono';font-weight:800;font-size:22px;letter-spacing:1px}}
.brand .ai{{color:#fff}} .brand .stack{{color:#34D399}} .brand .rest{{color:#fff}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:22px;letter-spacing:3px;color:#8893A4}}
.bigstat{{font-family:'JetBrains Mono';font-weight:800;line-height:0.92;letter-spacing:-2px;text-shadow:0 6px 40px rgba(0,0,0,.5)}}
.statlabel{{font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:1.5px;margin-top:14px}}
.head{{font-family:Fraunces;font-weight:700;line-height:1.1;letter-spacing:-1px;color:#fff}}
.quote{{font-family:Fraunces;font-style:italic;font-weight:600;line-height:1.22;letter-spacing:-.5px;color:#fff}}
.attr{{font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#7FE9C2}}
.sub{{font-family:Inter;font-size:25px;line-height:1.44;color:#B9C3D0}}
.foot{{font-family:'JetBrains Mono';font-size:14px;color:#8893A4;letter-spacing:.3px;line-height:1.5}}
.pill{{display:inline-flex;align-items:center;gap:12px;font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:16px 28px;border-radius:14px}}
.proof{{border-radius:14px;overflow:hidden;background:#0d1017;border:1.5px solid rgba(255,255,255,.14);box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.chrome{{height:28px;background:#1a2029;display:flex;align-items:center;gap:7px;padding:0 14px;flex:none}}
.dot{{width:9px;height:9px;border-radius:50%}}
.chip{{font-family:'JetBrains Mono';font-weight:800;color:#fff;background:#161c26;border:1.5px solid rgba(255,255,255,.16);border-radius:12px;padding:14px 22px;display:flex;align-items:baseline;gap:10px}}
.row{{display:flex;align-items:center;justify-content:space-between;background:#12161d;border:1.5px solid rgba(255,255,255,.12);border-radius:12px;padding:16px 22px}}
.qmark{{font-family:Fraunces;font-weight:900;font-size:120px;line-height:0.6;color:#7FE9C2;opacity:.55}}
"""

RAILS = "A fundamental-value model's estimate — a read, not a call."
DISCLAIMER = "Educational research only — not financial advice."


def page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"


def brandbar():
    return "<div class='brand'><span class='ai'>AI</span><span class='stack'>STACK</span><span class='rest'>&nbsp;·&nbsp;TERMINAL</span></div>"


def foot_full():
    # Every slide carries BOTH the model-estimate/"read not a call" rail and
    # the educational/NFA disclaimer -- non-negotiable per the task's hard
    # rails, so this is the only footer helper used across all 9 slides.
    return f"<div class='foot' style='margin-top:auto;padding-top:16px'>{RAILS}<br>{DISCLAIMER}</div>"


def proof_frame(img_b64, box_h, obj_pos="center top", fit="contain"):
    return f"""<div class='proof' style='width:100%;height:{box_h}px;display:flex;flex-direction:column'>
      <div class='chrome'><div class='dot' style='background:#e0605a'></div><div class='dot' style='background:#e0b23b'></div><div class='dot' style='background:#3bbf6b'></div></div>
      <div style='flex:1;background:#0d1017;display:flex;align-items:center;justify-content:center;overflow:hidden'>
        <img src='{img_b64}' style='width:100%;height:100%;object-fit:{fit};object-position:{obj_pos};display:block'>
      </div>
    </div>"""


# --------------------------------------------------------------------------- slides

def slide_cover(bg_b64):
    return page(f"""<div class='hero' style="background-image:url('{bg_b64}');filter:blur(3px) brightness(.4)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,rgba(10,13,18,.74) 0%,rgba(10,13,18,.5) 30%,rgba(10,13,18,.82) 62%,rgba(10,13,18,.97) 100%)"></div>
    <div class='pad'>{brandbar()}
      <div style='margin-top:34px;max-width:920px' class='kick'>PRICE ISN'T VALUE</div>
      <div class='head' style="margin-top:24px;font-size:92px;color:#fff">This stock costs<br><span style="color:#E0A23B">$548</span>.</div>
      <div class='head' style="margin-top:10px;font-size:64px;color:#B9C3D0">A model says it's worth <span style="color:#7FE9C2">$86</span>.</div>
      <div class='sub' style="margin-top:28px;max-width:880px;font-size:40px;text-shadow:0 2px 16px rgba(0,0,0,.75)">Price is what the market charges. Value is what a fundamental-value model thinks the business is actually worth. They are not the same number.</div>
      <div style='margin-top:auto;display:flex;align-items:center;justify-content:space-between'>
        <div class='pill'>SWIPE TO SEE WHY →</div></div>
      {foot_full()}</div>""")


def slide_quote(kick, quote, attribution, head, sub):
    # Vertically centers the whole quote block (kick..sub) in the space
    # between the brandbar and the footer via flex auto-margins on the
    # wrapper -- fills the frame instead of clustering everything at the
    # top with dead air above the footer.
    # NOTE: wrapper gets only margin-top:auto (not margin-bottom too) --
    # foot_full()'s own margin-top:auto supplies the gap below. With both
    # the wrapper's top AND bottom margins auto plus foot's top margin
    # auto, flexbox splits free space 1:2 (top gap : bottom gap) since the
    # middle gap is fed by two auto-margin edges -- true centering needs
    # exactly one auto edge per gap.
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:auto;display:flex;flex-direction:column'>
        <div class='kick'>{kick}</div>
        <div class='qmark' style="margin-top:24px;font-size:140px">&ldquo;</div>
        <div class='quote' style="margin-top:-10px;font-size:68px">{quote}</div>
        <div class='attr' style="margin-top:30px">— {attribution}</div>
        <div class='head' style="margin-top:46px;font-size:52px">{head}</div>
        <div class='sub' style="margin-top:20px;max-width:960px;font-size:38px">{sub}</div>
      </div>
      {foot_full()}</div>""")


def slide_text(kick, head, sub, rows=None, head_size=58, sub_size=None, fill=False):
    # head_size default bumped from the original 46px (+~26%). `fill=True`
    # (used for the sparse transition slide) centers kick+head+sub as one
    # block in the space between brandbar and footer, same trick as
    # slide_quote, so the composition fills the canvas instead of floating
    # in the top third.
    rows_html = ""
    if rows:
        items = "".join(
            f"<div class='row' style='margin-top:14px'>"
            f"<div style=\"font-family:'JetBrains Mono';font-weight:800;font-size:22px;color:{r[2]}\">{r[0]}</div>"
            f"<div class='sub' style='font-size:20px;max-width:640px;text-align:right'>{r[1]}</div></div>"
            for r in rows)
        rows_html = f"<div style='margin-top:26px'>{items}</div>"
    sub_style = f"margin-top:{'20px' if fill else '16px'};max-width:960px" + (f";font-size:{sub_size}px" if sub_size else "")
    if fill:
        # Same single-auto-edge-per-gap fix as slide_quote: margin-top:auto
        # only, so the top gap and the (foot's) bottom gap split evenly.
        body = f"""<div style='margin-top:auto;display:flex;flex-direction:column'>
          <div class='kick'>{kick}</div>
          <div class='head' style="margin-top:28px;font-size:{head_size}px">{head}</div>
          <div class='sub' style="{sub_style}">{sub}</div>
        </div>"""
    else:
        body = f"""<div style='margin-top:28px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:20px;font-size:{head_size}px">{head}</div>
      <div class='sub' style="{sub_style}">{sub}</div>
      {rows_html}"""
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      {foot_full()}</div>""")


def slide_shock(kick, big_stat, stat_label, headline, sub, stat_size=190, accent="#E0A23B",
                 proof_img=None, proof_pos="center top", proof_h=380, proof_fit="contain",
                 chips=None, note=None, sub_size=30):
    proof_html = f"<div style='margin-top:20px'>{proof_frame(proof_img, proof_h, proof_pos, proof_fit)}</div>" if proof_img else ""
    chips_html = ""
    if chips:
        c = "".join(
            f"<div class='chip'><span>{n}</span><span style='color:{accent};font-size:22px'>{v}</span></div>"
            for n, v in chips)
        chips_html = f"<div style='display:flex;flex-wrap:wrap;gap:12px;margin-top:18px'>{c}</div>"
    note_html = f"<div class='sub' style='margin-top:10px;font-size:19px;font-style:italic;color:#8893A4'>{note}</div>" if note else ""
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:26px' class='kick'>{kick}</div>
      <div class='bigstat' style="margin-top:16px;font-size:{stat_size}px;color:{accent}">{big_stat}</div>
      <div class='statlabel' style="color:{accent}">{stat_label}</div>
      <div class='head' style="margin-top:20px;font-size:40px">{headline}</div>
      <div class='sub' style="margin-top:12px;max-width:960px;font-size:{sub_size}px">{sub}</div>
      {chips_html}
      {note_html}
      {proof_html}
      {foot_full()}</div>""")


def slide_tool(kick, head, sub, proof_img, proof_h=420, proof_fit="contain", sub_size=32):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:28px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:16px;font-size:48px">{head}</div>
      <div class='sub' style="margin-top:14px;max-width:960px;font-size:{sub_size}px">{sub}</div>
      <div style='margin-top:22px'>{proof_frame(proof_img, proof_h, 'left top', proof_fit)}</div>
      <div class='sub' style="margin-top:12px;font-size:18px;color:#8893A4">SYMBOL · PRICE · MODEL'S FUND. VALUE · GAP VS PRICE — live columns from the tool.</div>
      {foot_full()}</div>""")


def slide_cta(img_b64):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:30px' class='kick'>PRICE VS VALUE, EVERY AI-STACK NAME</div>
      <div class='head' style="margin-top:12px;font-size:50px">Check the gap yourself.</div>
      <div class='sub' style="margin-top:12px;max-width:960px;font-size:38px">We compute price vs. a fundamental-value model's estimate for every name we track — the gap, sized and dated. Free, sourced, no login.</div>
      <div style='margin-top:20px'>{proof_frame(img_b64, 300, 'left top', 'contain')}</div>
      <div style='margin-top:auto;display:flex;flex-direction:column;gap:12px;padding-top:20px'>
        <div class='pill' style='font-size:28px;padding:20px 32px;width:fit-content'>\U0001f4ac COMMENT "VALUE"</div>
        <div style="font-family:'JetBrains Mono';font-weight:600;font-size:19px;letter-spacing:.5px;color:#B9C3D0">↳ and I'll DM you the link</div>
        {foot_full()}</div></div>""")


def _b64(path, ext="jpeg"):
    p = pathlib.Path(path)
    data = p.read_bytes()
    return f"data:image/{ext};base64," + base64.b64encode(data).decode()


def build():
    names = ["value_overvalued", "value_undervalued", "value_tool_wide"]
    imgs = {name: _b64(SRC / f"{name}.jpg") for name in names}

    slides = {}

    # 0 -------------------------------------------------------------- cover
    slides["0_cover.png"] = slide_cover(imgs["value_overvalued"])

    # 1 ---------------------------------------------------------- Buffett
    slides["1_priceisntvalue.png"] = slide_quote(
        "01 · THE CORE IDEA",
        "&ldquo;<span style='color:#E0A23B'>Price</span> is what you <span style='color:#E0A23B'>pay</span>.<br><span style='color:#34D399'>Value</span> is what you <span style='color:#34D399'>get</span>.&rdquo;",
        "WARREN BUFFETT",
        "<span style='color:#E0A23B'>Price</span> is what the market charges you today.",
        "It's set by supply and demand — everyone buying and selling right now, for any reason at all. Value is what a fundamental-value model estimates the business is actually worth: its cash flows, its assets, its earning power. The two numbers are rarely the same.")

    # 2 --------------------------------------------------------- Graham
    slides["2_votingmachine.png"] = slide_quote(
        "02 · WHY THEY DIVERGE",
        "&ldquo;In the short run, the market is a <span style='color:#E0A23B'>voting machine</span>;<br>in the long run, it is a <span style='color:#34D399'>weighing machine</span>.&rdquo;",
        "BENJAMIN GRAHAM",
        "Short-run <span style='color:#E0A23B'>price</span> is a popularity contest.",
        "Day to day, price just tracks demand — hype, fear, momentum, whatever's trending. Over the long run, Graham argued, it settles toward what the business truly weighs: its real, underlying value.")

    # 3 --------------------------------------------------- margin of safety
    slides["3_marginofsafety.png"] = slide_text(
        "03 · HOW THE GREATS USE IT",
        "Estimate the value. Compare it to the price. The gap below value is your margin of safety.",
        "Buffett and Graham built fortunes on exactly this gap — favoring businesses priced well under what a fundamental-value model estimates they're worth, and letting the market's short-run &ldquo;vote&rdquo; catch up to the long-run &ldquo;weight.&rdquo;",
        rows=[
            ("PRICE", "What you pay today — set by supply &amp; demand.", "#E0A23B"),
            ("VALUE", "What a fundamental-value model estimates the business is worth.", "#7FE9C2"),
        ],
        sub_size=42)

    # 4 --------------------------------------------------------- overvalued
    slides["4_overvalued.png"] = slide_shock(
        "04 · SHOCK #1 · THE <span style='color:#E0A23B'>OVERVALUED</span>",
        "6.4×", "WDC · PRICE VS. THE MODEL'S ESTIMATE",
        "You'd pay <span style='color:#E0A23B'>$548.39</span> for a stock a fundamental-value model pegs at <span style='color:#34D399'>$86.32</span>.",
        "Same story across the chip/infra layer — price running as a multiple of what the model thinks the business is worth. Priced on demand and hype, not necessarily fundamentals. A read, not a call — the model can be wrong.",
        stat_size=210, accent="#E0A23B",
        chips=[("STX", "5.7×"), ("CIEN", "4.2×"), ("COHR", "3.8×"), ("INTC", "3.7×"), ("WULF", "3.3×")],
        proof_img=imgs["value_overvalued"], proof_h=330)

    # 5 ---------------------------------------------------------- the flip
    slides["5_undervalued.png"] = slide_shock(
        "05 · THE FLIP · THE <span style='color:#34D399'>UNDERVALUED</span>",
        "3.4×", "SMCI · THE MODEL'S ESTIMATE VS. PRICE",
        "SMCI trades at <span style='color:#E0A23B'>$25.50</span>. A fundamental-value model estimates it's worth <span style='color:#34D399'>$87.03</span>.",
        "Maybe the market's overlooking it. Maybe the model's wrong. That's the debate — not a recommendation, not a price target.",
        stat_size=210, accent="#34D399",
        chips=[("DUOL", "3.1×"), ("TEAM", "3.1×"), ("INTU", "2.8×"), ("CRWD", "2.6×"), ("ADBE", "2.6×")],
        proof_img=imgs["value_undervalued"], proof_h=340)

    # 6 --------------------------------------------------------- the gap
    slides["6_thegap.png"] = slide_text(
        "06 · WHY IT MATTERS",
        "That gap is the whole game.",
        "<span style='color:#E0A23B'>Price</span> is a vote. <span style='color:#34D399'>Value</span> is a weight. The gap between them is where opportunity — and risk — live. A big gap can mean a mispriced business, or a red flag the market sees that the model doesn't. This is a read, not a call.",
        head_size=62, sub_size=46, fill=True)

    # 7 -------------------------------------------------------------- tool
    slides["7_tool.png"] = slide_tool(
        "07 · THE TOOL",
        "We compute <span style='color:#E0A23B'>price</span> vs. a fundamental-value model for every AI-stack name.",
        "The gap, sized and dated, for every name we track — sortable by symbol, price, the model's fundamental value, and the gap between them.",
        imgs["value_tool_wide"], proof_h=340, sub_size=36)

    # 8 -------------------------------------------------------------------- CTA
    slides["8_cta.png"] = slide_cta(imgs["value_overvalued"])

    OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for name, html in slides.items():
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered", name)
        b.close()

    caption = """This stock costs $548. A fundamental-value model says it's worth $86. \U0001f440\U0001f4c9

Here's a fact that trips people up: a stock's PRICE isn't the same thing as its VALUE. Price is just what the market is charging RIGHT NOW — set by supply and demand, by everyone buying and selling today. Value is what the business is actually worth underneath all that noise.

Warren Buffett put it simply: "Price is what you pay. Value is what you get." Benjamin Graham explained WHY they diverge: "In the short run, the market is a voting machine; in the long run, it is a weighing machine." Short-term, price is a popularity contest. Long-term, it tends to reflect what the business really weighs.

Buffett and Graham built their whole approach on that gap — estimate the value, compare it to the price, and the room between them is your "margin of safety."

So we ran a fundamental-value model against every AI-stack stock we track. Here's the gap it found:

\U0001f6a8 OVERVALUED (per the model): WDC trades at $548.39 — the model pegs it at just $86.32. That's 6.4× the estimate. STX (5.7×), CIEN (4.2×), COHR (3.8×), INTC (3.7×), and WULF (3.3×) show the same pattern.

\U0001f504 THE FLIP — UNDERVALUED (per the model): SMCI trades at only $25.50, while the model estimates it's worth $87.03 — 3.4× the price. DUOL, TEAM, INTU, CRWD, and ADBE all show similar gaps in the other direction.

Is the market wrong? Is the model wrong? That's exactly the debate serious investors have — not a tip, not a prediction.

We compute this gap — price vs. a fundamental-value model's estimate — for every AI-stack name, dated and sourced, free.

Comment "VALUE" and I'll DM you the link \U0001f4f2

⚠️ Fundamental value here comes from a third-party fundamental-value model's estimate, not a guarantee — it can be wrong, and a large gap is a read, not a call. Nothing here is a recommendation to buy or sell any security, and none of these figures are price targets or predictions. Educational research only — not financial advice.

#valueinvesting #warrenbuffett #stockmarket #investing #fundamentalanalysis #AIstocks #stocktok #fintok #financetok #investing101 #benjamingraham #marginofsafety #wallstreet #stockanalysis #dueDiligence #undervalued #overvalued
"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")

    manifest = {
        "kind": "value_showcase_carousel",
        "product": "AI Stack Terminal",
        "source_url": "https://highreturnethicalscreen.vercel.app/screener",
        "date": DATE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_source": "web/public/data/site.json 'screener' array (generated 2026-07-22T09:47:01Z) + live /screener page capture (2026-07-23)",
        "aspect": "4:5 (2160x2700) — Instagram carousel",
        "slides": list(slides.keys()),
        "standalone": True,
        "hard_rails": [
            "Fundamental value is a third-party model's ESTIMATE, not ground truth — never asserted as fact.",
            "No vendor/provider name appears anywhere in slides, caption, or this file.",
            "Every over/undervalued claim is framed 'a fundamental-value model estimates/pegs' + 'a read, not a call.'",
            "No recommendation to buy or sell any security; no price targets presented as promises.",
        ],
        "figures_used": {
            "overvalued": {
                "WDC": {"price": 548.39, "fundamental_value": 86.32, "multiple": "6.4x"},
                "STX": {"price": 891.83, "fundamental_value": 157.65, "multiple": "5.7x"},
                "CIEN": {"price": 408.73, "fundamental_value": 96.47, "multiple": "4.2x"},
                "COHR": {"price": 317.22, "fundamental_value": 83.36, "multiple": "3.8x"},
                "INTC": {"price": 105.45, "fundamental_value": 28.22, "multiple": "3.7x"},
                "WULF": {"price": 19.87, "fundamental_value": 5.99, "multiple": "3.3x"},
            },
            "undervalued": {
                "SMCI": {"price": 25.50, "fundamental_value": 87.03, "multiple": "3.4x"},
                "DUOL": {"price": 124.71, "fundamental_value": 391.84, "multiple": "3.1x"},
                "TEAM": {"price": 90.60, "fundamental_value": 279.31, "multiple": "3.1x"},
                "INTU": {"price": 289.92, "fundamental_value": 810.47, "multiple": "2.8x"},
                "CRWD": {"price": 191.15, "fundamental_value": 506.36, "multiple": "2.6x"},
                "ADBE": {"price": 227.16, "fundamental_value": 595.80, "multiple": "2.6x"},
            },
        },
        "quotes": {
            "Warren Buffett": "Price is what you pay. Value is what you get.",
            "Benjamin Graham": "In the short run, the market is a voting machine; in the long run, it is a weighing machine.",
        },
        "screenshot_source": "live captures of highreturnethicalscreen.vercel.app/screener via browser automation, 2026-07-23 (sorted asc/desc by 'vs Price %' column; live values drift slightly from the 2026-07-22 site.json snapshot used for slide copy)",
        "posting_instructions": "Post as an Instagram carousel (not a reel). CTA slide asks viewers to comment \"VALUE\" for a DM'd link (not link-in-bio).",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"DONE slides={len(slides)} -> {OUT}")


if __name__ == "__main__":
    build()
