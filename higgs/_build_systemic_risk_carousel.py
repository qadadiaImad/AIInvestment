"""Standalone IG carousel: "You don't own 20 AI stocks. You own 3." --
systemic risk / correlation shock-stat post, built from LIVE data in
web/public/data/risk.json (generated 2026-07-22) and the /resiliency page
(graph-structural risk), grounded per the confirmed brainstorming design
(see conversation; no separate spec doc for this content post).

Not tied to the daily-post/reels-kit pipeline -- a standalone 9-slide 4:5
(1080x1350) carousel, same brand system as _build_platform_carousel.py so it
reads as the same product family. Each "shock" slide leads with one huge,
simplified number; a small cropped screenshot of the real tool sits below as
proof. Screenshots pre-staged in higgs/_platform_src/ (captured live,
2026-07-23): risk_correlation_cluster.jpg, risk_correlation_msft.jpg,
resiliency_health.jpg, resiliency_cascade.jpg, resiliency_spof.jpg.

    python higgs/_build_systemic_risk_carousel.py

Writes 9 PNGs + caption.txt + manifest.json to higgs/systemic_risk_showcase_<date>/.
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
OUT = HIGGS / f"systemic_risk_showcase_{DATE}"

W, H = 1080, 1350

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700;9..144,900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"

BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:64px 64px;display:flex;flex-direction:column;z-index:2}}
.brand{{display:flex;align-items:baseline;gap:2px;font-family:'JetBrains Mono';font-weight:800;font-size:22px;letter-spacing:1px}}
.brand .ai{{color:#fff}} .brand .stack{{color:#34D399}} .brand .rest{{color:#fff}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:22px;letter-spacing:3px;color:#8893A4}}
.bigstat{{font-family:'JetBrains Mono';font-weight:800;line-height:0.92;letter-spacing:-2px;text-shadow:0 6px 40px rgba(0,0,0,.5)}}
.statlabel{{font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:2px;margin-top:14px}}
.head{{font-family:Fraunces;font-weight:700;line-height:1.08;letter-spacing:-1px;color:#fff}}
.sub{{font-family:Inter;font-size:24px;line-height:1.42;color:#B9C3D0}}
.foot{{font-family:'JetBrains Mono';font-size:15px;color:#8893A4;letter-spacing:.5px}}
.pill{{display:inline-flex;align-items:center;gap:12px;font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:16px 28px;border-radius:14px}}
.proof{{border-radius:14px;overflow:hidden;background:#12161d;border:1.5px solid rgba(255,255,255,.14);box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.chrome{{height:28px;background:#1a2029;display:flex;align-items:center;gap:7px;padding:0 14px}}
.dot{{width:9px;height:9px;border-radius:50%}}
"""

DISCLAIMER = "Educational research only — not financial advice"


def page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"


def brandbar():
    return "<div class='brand'><span class='ai'>AI</span><span class='stack'>STACK</span><span class='rest'>&nbsp;·&nbsp;TERMINAL</span></div>"


def proof_frame(img_b64, box_h, obj_pos="center top", fit="contain"):
    # object-fit:contain inside a letterboxed flex box (not the old
    # object-fit:cover) -- same technique as the value/congress carousels --
    # so screenshots are never cropped/squeezed, just shown in full at
    # whatever size fits the box.
    return f"""<div class='proof' style='width:100%;height:{box_h}px;display:flex;flex-direction:column'>
      <div class='chrome'><div class='dot' style='background:#e0605a'></div><div class='dot' style='background:#e0b23b'></div><div class='dot' style='background:#3bbf6b'></div></div>
      <div style='flex:1;background:#0d1017;display:flex;align-items:center;justify-content:center;overflow:hidden'>
        <img src='{img_b64}' style='width:100%;height:100%;object-fit:{fit};object-position:{obj_pos};display:block'>
      </div>
    </div>"""


# --------------------------------------------------------------------------- slides

def slide_cover(bg_b64):
    return page(f"""<div class='hero' style="background-image:url('{bg_b64}');filter:blur(2px) brightness(.55)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,rgba(10,13,18,.75) 0%,rgba(10,13,18,.5) 32%,rgba(10,13,18,.78) 62%,rgba(10,13,18,.97) 100%)"></div>
    <div class='pad'>{brandbar()}
      <div style='margin-top:34px;max-width:920px' class='kick'>WE RAN THE MATH ON YOUR "DIVERSIFIED" AI PORTFOLIO</div>
      <div class='head' style="margin-top:24px;font-size:92px;color:#fff">You don't own<br>20 AI stocks.<br><span style="color:#E0A23B">You own 3.</span></div>
      <div class='sub' style="margin-top:26px;max-width:880px;font-size:40px;text-shadow:0 2px 16px rgba(0,0,0,.75)">424 companies tracked. The correlation math says most of them move as one.</div>
      <div style='margin-top:auto;display:flex;align-items:center;justify-content:space-between'>
        <div class='pill'>SWIPE TO SEE WHY →</div>
        <div class='foot'>{DISCLAIMER}</div></div></div>""")


def slide_shock(kick, big_stat, stat_label, headline, sub, stat_size=210, accent="#E0A23B",
                 proof_img=None, proof_pos="left top", proof_h=440, proof_fit="contain",
                 head_size=56, sub_size=None, fill=True):
    # head_size bumped from the original fixed 48px (~+17%) -- kept gentle
    # since every slide in this carousel carries a proof screenshot below it
    # (siblings' "screenshot slides get a gentler bump" rule applies here
    # across the board). sub_size defaults to ~0.62x head_size: a big jump
    # from the old fixed 24px body text while staying conservative enough
    # not to push the giant bigstat + proof screenshot combo into overflow.
    # fill=True wraps the whole content block in margin-top:auto so it
    # centers between the brandbar and footer (the footer's own
    # margin-top:auto supplies the matching bottom gap) -- same
    # single-auto-edge-per-gap technique as the value/congress carousels.
    if sub_size is None:
        sub_size = round(head_size * 0.62)
    proof_html = f"<div style='margin-top:26px'>{proof_frame(proof_img, proof_h, proof_pos, proof_fit)}</div>" if proof_img else ""
    content = f"""<div class='kick'>{kick}</div>
      <div class='bigstat' style="margin-top:18px;font-size:{stat_size}px;color:{accent}">{big_stat}</div>
      <div class='statlabel' style="color:{accent}">{stat_label}</div>
      <div class='head' style="margin-top:24px;font-size:{head_size}px">{headline}</div>
      <div class='sub' style="margin-top:14px;max-width:940px;font-size:{sub_size}px">{sub}</div>
      {proof_html}"""
    body = (f"<div style='margin-top:auto;display:flex;flex-direction:column'>{content}</div>" if fill
            else f"<div style='margin-top:28px;display:flex;flex-direction:column'>{content}</div>")
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      <div class='foot' style='margin-top:auto;padding-top:18px'>{DISCLAIMER}</div></div>""")


def slide_names(kick, headline, names, sub, proof_img=None, proof_h=420, proof_fit="contain",
                 head_size=60, sub_size=None, fill=True):
    # Same head_size/sub_size/fill conventions as slide_shock above.
    if sub_size is None:
        sub_size = round(head_size * 0.62)
    chips = "".join(
        f"<div style='font-family:JetBrains Mono;font-weight:800;font-size:34px;color:#fff;background:#161c26;border:1.5px solid rgba(255,255,255,.16);border-radius:12px;padding:14px 22px'>{n}</div>"
        for n in names)
    proof_html = f"<div style='margin-top:24px'>{proof_frame(proof_img, proof_h, 'left top', proof_fit)}</div>" if proof_img else ""
    content = f"""<div class='kick'>{kick}</div>
      <div class='head' style="margin-top:16px;font-size:{head_size}px">{headline}</div>
      <div style='display:flex;flex-wrap:wrap;gap:14px;margin-top:26px'>{chips}</div>
      <div class='sub' style="margin-top:22px;max-width:940px;font-size:{sub_size}px">{sub}</div>
      {proof_html}"""
    body = (f"<div style='margin-top:auto;display:flex;flex-direction:column'>{content}</div>" if fill
            else f"<div style='margin-top:28px;display:flex;flex-direction:column'>{content}</div>")
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      <div class='foot' style='margin-top:auto;padding-top:18px'>{DISCLAIMER}</div></div>""")


def slide_cta(img_b64):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:32px' class='kick'>STOP ASSUMING YOU'RE DIVERSIFIED</div>
      <div class='head' style="margin-top:14px;font-size:66px">Check your own AI stocks.</div>
      <div class='sub' style="margin-top:14px;max-width:940px;font-size:38px">Correlation matrix, VaR, volatility, resiliency stress-tests — free, dated, sourced. No login.</div>
      <div style='margin-top:24px'>{proof_frame(img_b64, 650, "left top", "contain")}</div>
      <div style='margin-top:auto;display:flex;flex-direction:column;gap:12px;padding-top:22px'>
        <div class='pill' style='font-size:30px;padding:22px 34px;width:fit-content'>💬 COMMENT "RISK"</div>
        <div style="font-family:'JetBrains Mono';font-weight:600;font-size:20px;letter-spacing:.5px;color:#B9C3D0">↳ and I'll DM you the link</div>
        <div class='foot' style='margin-top:8px'>{DISCLAIMER} · not a recommendation to buy or sell any security · historical measures do not predict future losses</div></div></div>""")


def _b64(path):
    p = pathlib.Path(path)
    data = p.read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


def build():
    names = ["risk_correlation_cluster", "risk_correlation_msft", "resiliency_health",
             "resiliency_cascade", "resiliency_spof"]
    imgs = {name: _b64(SRC / f"{name}.jpg") for name in names}

    slides = {}
    slides["0_cover.png"] = slide_cover(imgs["risk_correlation_cluster"])

    slides["1_correlation_bomb.png"] = slide_shock(
        "01 · THE CORRELATION BOMB",
        "89%", "AMAT &amp; LRCX MOVE TOGETHER",
        "Two different chip-equipment stocks. Practically the same trade.",
        "When one moves, the other moves with it 9 times out of 10. That's not diversification — that's doubling down without knowing it.",
        stat_size=220, accent="#E0A23B",
        proof_img=imgs["risk_correlation_cluster"], proof_pos="right top", proof_h=440)

    slides["2_cluster.png"] = slide_shock(
        "02 · THE CLUSTER",
        "5 STOCKS", "PRACTICALLY 1 TRADE",
        "ASML, AMAT, LRCX, TSM, MU — five tickers, one bet.",
        "Every pair in this group moves together 60–89% of the time. Buy all five thinking you've spread your risk, and you've mostly just resized one position.",
        stat_size=140, accent="#E0A23B",
        proof_img=imgs["risk_correlation_cluster"], proof_pos="right top", proof_h=440)

    slides["3_exception.png"] = slide_shock(
        "03 · THE EXCEPTION",
        "≈0", "MSFT vs. THE CHIP-EQUIPMENT CLUSTER",
        "Except this one. It barely moves with the rest at all.",
        "Microsoft's correlation with that same chip-equipment cluster sits between −0.12 and 0.04 — almost zero. Proof real diversification exists, if you know where to look.",
        stat_size=210, accent="#7FE9C2",
        proof_img=imgs["risk_correlation_msft"], proof_pos="left top", proof_h=440)

    slides["4_score.png"] = slide_shock(
        "04 · THE SCORE",
        "73/100", "OFFICIALLY &ldquo;RESILIENT&rdquo;",
        "The system rates the whole AI market healthy.",
        "Our resiliency model scores the entire 117-company tracked network 73.2 out of 100 — “resilient.” Sounds reassuring. Keep swiping.",
        stat_size=160, accent="#34D399",
        proof_img=imgs["resiliency_health"], proof_pos="left top", proof_h=380)

    slides["5_twist.png"] = slide_shock(
        "05 · THE TWIST",
        "5X", "WORSE THAN RANDOM BAD LUCK",
        "But knock out ONE company on purpose, and the damage is five times worse.",
        "Targeted removal of the network's top hub is 4.85× more damaging than a random failure — the fingerprint of a single point of failure.",
        stat_size=240, accent="#E0A23B",
        proof_img=imgs["resiliency_health"], proof_pos="right top", proof_h=380)

    slides["6_domino.png"] = slide_shock(
        "06 · THE DOMINO EFFECT",
        "66 OF 117", "TRACKED COMPANIES GET HIT",
        "If Big Tech cuts AI spending, the shock reaches HALF the market.",
        "A simulated hyperscaler capex pullback propagates to 66 of 117 tracked companies — 49% of the entire network, not just the obvious names.",
        stat_size=110, accent="#E0A23B",
        proof_img=imgs["resiliency_cascade"], proof_pos="left top", proof_h=280)

    slides["7_fewnames.png"] = slide_names(
        "07 · THE FEW NAMES HOLDING IT UP",
        "Take out any ONE of these 6, and dozens of others shake.",
        ["NVDA", "MSFT", "AMZN", "GOOGL", "GEV", "META"],
        "Ranked by how structurally load-bearing they are to the network — not by size.",
        proof_img=imgs["resiliency_spof"], proof_h=420)

    slides["8_cta.png"] = slide_cta(imgs["risk_correlation_msft"])

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

    caption = """Everyone's picking their own "diversified" basket of AI stocks. We ran the correlation math. 📉🔥

AMAT and LRCX — two different chip-equipment companies — move together 89% of the time. Zoom out and the whole equipment cluster (ASML, AMAT, LRCX, TSM, MU) trades as basically one position. Meanwhile Microsoft barely moves with any of them — proof real diversification exists, if you know where to look.

Then the structural side: the network scores 73/100, "resilient" — but knock out one hub on purpose and the damage is 5x worse than random bad luck. A simulated Big Tech spending pullback reaches 66 of 117 tracked companies. Half the market, hit by one shock.

Six companies are structurally holding up the whole AI stack: Nvidia, Microsoft, Amazon, Google, GE Vernova, Meta.

We track correlation, VaR, volatility, and network resiliency for the whole AI stack — free, dated, sourced.

Historical risk measures (correlation, VaR, volatility, resiliency scores) are backward-looking and do not predict future losses. Educational research only — not financial advice, not a recommendation to buy or sell any security.

Comment "RISK" and I'll DM you the link 📲

#AIstocks #stockmarket #investing #riskmanagement #correlation #portfoliomanagement #wallstreet #Nasdaq #stockanalysis #semiconductors #diversification #investing101 #stocktok #fintok #financetok #dueDiligence #techstocks #quant
"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")

    manifest = {
        "kind": "systemic_risk_showcase_carousel",
        "product": "AI Stack Terminal",
        "source_url": "https://highreturnethicalscreen.vercel.app/terminal/risk and /resiliency",
        "date": DATE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_source": "web/public/data/risk.json (generated 2026-07-22T09:47:01Z) + live /resiliency page",
        "aspect": "4:5 (1080x1350) — Instagram carousel",
        "slides": list(slides.keys()),
        "standalone": True,
        "posting_instructions": "Post as an Instagram carousel (not a reel). CTA slide asks viewers to comment \"RISK\" for a DM'd link (not link-in-bio).",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"DONE slides={len(slides)} -> {OUT}")


if __name__ == "__main__":
    build()
