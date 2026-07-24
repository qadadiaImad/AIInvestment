"""One-off IG carousel builder: "AI Stack Terminal" platform feature showcase.

Not tied to the daily-post/reels-kit pipeline (no ticker, no VO) -- a standalone
9-slide 4:5 (1080x1350) carousel introducing the platform itself, built from real
screenshots of the live site (highreturnethicalscreen.vercel.app, same deploy as
this repo's web/). Reuses the exact brand system (fonts/colors/CSS tokens) from
higgs/_build_v4.py so it reads as the same product family as the daily posts.

    python higgs/_build_platform_carousel.py

Reads screenshots from higgs/_platform_src/*.jpg (staged separately -- not part
of this script). Writes 9 PNGs + caption.txt + manifest.json to
higgs/platform_showcase_<date>/.
"""
from __future__ import annotations

import base64
import json
import pathlib
import sys
from datetime import datetime, timezone

HIGGS = pathlib.Path(__file__).resolve().parent
ROOT = HIGGS.parent
SRC = HIGGS / "_platform_src"
DATE = "2026-07-23"
OUT = HIGGS / f"platform_showcase_{DATE}"

W, H = 1080, 1350

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"

# Same tokens as _build_v4.py's BASE, extended with a browser-chrome mockup frame
# so real UI screenshots read as "our product" rather than a random crop.
BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:70px 64px;display:flex;flex-direction:column;z-index:2}}
.brand{{display:flex;align-items:baseline;gap:2px;font-family:'JetBrains Mono';font-weight:800;font-size:22px;letter-spacing:1px}}
.brand .ai{{color:#fff}} .brand .stack{{color:#34D399}} .brand .rest{{color:#fff}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:4px;color:#34D399}}
.kick-lg{{font-family:'JetBrains Mono';font-weight:700;font-size:36px;letter-spacing:3px;color:#34D399;line-height:1.15}}
.head{{font-family:Fraunces;font-weight:600;line-height:1.05;letter-spacing:-1.5px;text-shadow:0 4px 30px rgba(0,0,0,.6)}}
.foot{{font-family:'JetBrains Mono';font-size:16px;color:#8893A4;letter-spacing:.5px}}
.pill{{display:inline-flex;align-items:center;gap:12px;font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:16px 28px;border-radius:14px}}
.browser{{border-radius:16px;overflow:hidden;background:#12161d;border:1.5px solid rgba(255,255,255,.14);box-shadow:0 24px 70px rgba(0,0,0,.55)}}
.chrome{{height:34px;background:#1a2029;display:flex;align-items:center;gap:8px;padding:0 16px}}
.dot{{width:11px;height:11px;border-radius:50%}}
.stat{{font-family:'JetBrains Mono'}}
.statbig{{font-weight:800;font-size:38px;color:#fff;line-height:1}}
.statlbl{{font-weight:600;font-size:15px;color:#8893A4;letter-spacing:1px;margin-top:6px}}
"""


def page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"


def brandbar():
    return "<div class='brand'><span class='ai'>AI</span><span class='stack'>STACK</span><span class='rest'>&nbsp;·&nbsp;TERMINAL</span></div>"


def browser_frame(img_b64, box_h, obj_pos="center top", obj_fit="cover"):
    # obj_fit="contain" + a background matching the browser-chrome panel
    # keeps the whole captured screenshot uncropped (no letterboxing seam)
    # when the capture's aspect ratio doesn't exactly match the frame.
    return f"""<div class='browser' style='width:100%;height:{box_h}px'>
      <div class='chrome'><div class='dot' style='background:#e0605a'></div><div class='dot' style='background:#e0b23b'></div><div class='dot' style='background:#3bbf6b'></div></div>
      <img src='{img_b64}' style='width:100%;height:{box_h-34}px;object-fit:{obj_fit};object-position:{obj_pos};background:#12161d;display:block'>
    </div>"""


def stat(big, lbl, color="#fff"):
    return f"<div class='stat'><div class='statbig' style='color:{color}'>{big}</div><div class='statlbl'>{lbl}</div></div>"


DISCLAIMER = "Educational research only — not financial or religious advice"


# --------------------------------------------------------------------------- slides

def slide_cover(bg_b64):
    return page(f"""<div class='hero' style="background-image:url('{bg_b64}');filter:blur(1px)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,rgba(10,13,18,.86) 0%,rgba(10,13,18,.55) 30%,rgba(10,13,18,.72) 62%,rgba(10,13,18,.96) 100%)"></div>
    <div class='pad'>{brandbar()}
      <div style='margin-top:36px;max-width:900px' class='kick-lg'>WHILE EVERYONE TRADES THE SAME 5 STOCKS</div>
      <div class='head' style="margin-top:22px;font-size:92px;color:#fff">We mapped the<br>entire AI stack.</div>
      <div style="font-size:32px;line-height:1.42;color:#D7DEE8;margin-top:26px;max-width:900px;text-shadow:0 2px 16px rgba(0,0,0,.75)">
        424 companies. Energy to apps, chips to Congress. Every layer top-tier investors actually watch — in one tool.</div>
      <div style='margin-top:auto;display:flex;align-items:center;justify-content:space-between'>
        <div class='pill'>SWIPE FOR THE TOUR →</div>
        <div class='foot'>{DISCLAIMER}</div></div></div>""")


def slide_feature(img_b64, kick, head, sub, stats, obj_pos="center top", box_h=760, obj_fit="contain"):
    stat_row = "<div style='display:flex;gap:56px;margin-top:34px'>" + "".join(stats) + "</div>"
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:30px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:12px;font-size:56px;color:#fff">{head}</div>
      <div style="font-size:25px;line-height:1.4;color:#B9C3D0;margin-top:16px;max-width:920px">{sub}</div>
      <div style='margin-top:26px'>{browser_frame(img_b64, box_h, obj_pos, obj_fit)}</div>
      {stat_row}
      <div class='foot' style='margin-top:auto;padding-top:20px'>{DISCLAIMER}</div></div>""")


def slide_strategies(img_b64):
    stats = [stat("+1,400.6%", "MOMENTUM (12-1) TOTAL RETURN", "#34D399"),
             stat("+1,111.3%", "AI-SYNTHESIS TOTAL RETURN", "#7FE9C2"),
             stat("1.72", "BEST SHARPE RATIO", "#E0A23B")]
    stat_row = "<div style='display:flex;gap:44px;margin-top:30px'>" + "".join(stats) + "</div>"
    disc = ("<div style='margin-top:20px;border:1.5px solid rgba(224,162,59,.5);background:rgba(224,162,59,.08);"
            "border-radius:12px;padding:16px 20px;font-family:JetBrains Mono;font-size:16px;color:#E0A23B;line-height:1.5'>"
            "⚠ Illustrative backtest, run on today's roster (survivorship-biased) · monthly rebalance, 0.1% fees, "
            "45-day fundamental lag · not investment advice, does not predict future results.</div>")
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:30px' class='kick'>STRATEGIES — BACKTESTED, NOT VIBES</div>
      <div class='head' style="margin-top:12px;font-size:54px;color:#fff">Playbooks, receipts included.</div>
      <div style="font-size:25px;line-height:1.4;color:#B9C3D0;margin-top:16px;max-width:920px">Three model strategies across 113 AI-stack names, backtested since 2022 against an equal-weight benchmark (+365.1%).</div>
      <div style='margin-top:22px'>{browser_frame(img_b64, 620, "center top", "contain")}</div>
      {stat_row}{disc}
      <div class='foot' style='margin-top:auto;padding-top:16px'>{DISCLAIMER}</div></div>""")


def slide_cta(img_b64):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:34px' class='kick'>STOP TRADING THE OBVIOUS FIVE</div>
      <div class='head' style="margin-top:14px;font-size:66px;color:#fff">Screen the whole stack.</div>
      <div style="font-size:24px;line-height:1.4;color:#B9C3D0;margin-top:14px;max-width:920px">
        Capital web · chokepoints · resiliency · screener · Congress trades · backtests · halal screen — free, dated, sourced.</div>
      <div style='margin-top:24px'>{browser_frame(img_b64, 700, "center top")}</div>
      <div style='margin-top:auto;display:flex;flex-direction:column;gap:12px;padding-top:24px'>
        <div class='pill' style='font-size:30px;padding:22px 34px;width:fit-content'>💬 COMMENT "AI STACK"</div>
        <div style="font-family:'JetBrains Mono';font-weight:600;font-size:20px;letter-spacing:.5px;color:#B9C3D0">↳ and I'll DM you the link</div>
        <div class='foot' style='margin-top:8px'>{DISCLAIMER} · not a recommendation to buy or sell any security</div></div></div>""")


def _b64(path):
    p = pathlib.Path(path)
    data = p.read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


def build():
    imgs = {name: _b64(SRC / f"{name}.jpg") for name in
            ["home", "map", "map_zoom", "chokepoints", "resiliency", "screener", "congress", "strategies", "halal"]}

    slides = {}
    slides["0_cover.png"] = slide_cover(imgs["map"])

    slides["1_map.png"] = slide_feature(
        imgs["map_zoom"],
        "01 · CAPITAL WEB MAP",
        "See who actually funds, builds, and buys.",
        "An interactive graph of the whole AI value chain — not five household names. Drag nodes, drill into any company, see who's exposed to whom.",
        [stat("424", "COMPANIES TRACKED"), stat("190", "GRAPH NODES"), stat("416", "FUNDING/BUSINESS EDGES")],
        obj_pos="center", box_h=760, obj_fit="contain")

    slides["2_chokepoints.png"] = slide_feature(
        imgs["chokepoints"],
        "02 · SUPPLY-CHAIN CHOKEPOINTS",
        "One island. One company. Your whole portfolio.",
        "“Sub-7nm logic — the silicon under every AI accelerator — runs through one company, on one island.” We track every single point of failure like it, fact vs. reported vs. rumored.",
        [stat("13", "CHOKEPOINTS TRACKED"), stat("3", "RATED CRITICAL (≥75)"), stat("90%+", "TSMC SUB-7NM SHARE")],
        obj_pos="center", box_h=630, obj_fit="contain")

    slides["3_resiliency.png"] = slide_feature(
        imgs["resiliency"],
        "03 · GRAPH RESILIENCY",
        "We stress-test the network before it breaks.",
        "Betweenness centrality, fragility ratios, cascade modeling. Targeted removal of the top hub is 4.85× more damaging than random failure — we show you exactly which nodes those are.",
        [stat("73.2", "NETWORK HEALTH SCORE", "#34D399"), stat("4.85×", "TARGETED-HUB FRAGILITY"), stat("11", "ARTICULATION POINTS")],
        obj_pos="center", box_h=750, obj_fit="contain")

    slides["4_screener.png"] = slide_feature(
        imgs["screener"],
        "04 · THE SCREENER",
        "424 names. Every layer. One screen.",
        "Price, P/E, margins, ROE, revenue growth, 1Y/5Y returns, fundamental value vs. price — plus a next-catalyst date most screeners don't bother tracking.",
        [stat("424", "NAMES SCREENED"), stat("5", "STACK LAYERS"), stat("4", "DATA SOURCES", "#7FE9C2")],
        obj_pos="center", box_h=650, obj_fit="contain")

    slides["5_congress.png"] = slide_feature(
        imgs["congress"],
        "05 · CONGRESS TRACKER",
        "9,735 trades. We flag the committee overlap.",
        "Every disclosed House stock trade since 2015, mapped to the AI stack — and tagged the moment a member trades a sector their own committee oversees.",
        [stat("9,735", "DISCLOSED TRADES"), stat("118", "HOUSE MEMBERS"), stat("854", "FLAGGED: COMMITTEE OVERLAP", "#E0A23B")],
        obj_pos="center", box_h=650, obj_fit="contain")

    slides["6_strategies.png"] = slide_strategies(imgs["strategies"])

    slides["7_halal.png"] = slide_feature(
        imgs["halal"],
        "06 · HALAL SCREEN",
        "Ethical screening, five standards, side by side.",
        "AAOIFI, FTSE Yasaar, MSCI Islamic, S&P Shariah, DJIM — the same company can pass one and fail another. We show the worked math for every one, not just a verdict.",
        [stat("128", "NAMES SCREENED"), stat("77", "HALAL", "#34D399"), stat("43", "NOT HALAL", "#C25E5E")],
        obj_pos="center", box_h=630, obj_fit="contain")

    slides["8_cta.png"] = slide_cta(imgs["home"])

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

    caption = """We mapped the entire AI stack — while everyone else trades the same 5 stocks. \U0001F4E1\U0001F52C

424 companies. Energy → chips → infra → models → apps. One capital web graph, 13 supply-chain chokepoints, a resiliency stress-test, a 424-name screener, 9,735 tracked Congress trades, backtested strategies, and a 5-standard halal screen — all dated, sourced, free.

Swipe through every feature →

Illustrative strategy backtests are survivorship-biased and educational only — not investment advice, not predictive of future results.

Educational research only — not financial or religious advice — not a recommendation to buy or sell any security.

Comment "AI STACK" and I'll DM you the private link \U0001F4F2

#AIstocks #semiconductors #stockscreener #investingtips #stockmarket #AIinvesting #fintech #dueDiligence #chipstocks #halalinvesting #islamicfinance #congresstrading #stocktok #investing101 #techstocks #dataviz #quant
"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")

    manifest = {
        "kind": "platform_showcase_carousel",
        "product": "AI Stack Terminal",
        "source_url": "https://highreturnethicalscreen.vercel.app/",
        "date": DATE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aspect": "4:5 (1080x1350) — Instagram carousel",
        "slides": list(slides.keys()),
        "screenshot_source": "live captures of highreturnethicalscreen.vercel.app via browser automation, same day",
        "posting_instructions": "Post as an Instagram carousel (not a reel), text-only slides, no voiceover. CTA slide asks viewers to comment \"AI STACK\" for a DM'd link (not link-in-bio).",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"DONE slides={len(slides)} -> {OUT}")


if __name__ == "__main__":
    build()
