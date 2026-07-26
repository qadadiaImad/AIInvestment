"""Standalone IG carousel: "Congress traded up to $1 BILLION in stock. Guess
what they bought." -- built from LIVE data in web/public/data/congress.json
(generated 2026-07-11T13:54:18Z, source = House Clerk STOCK Act disclosure
PDFs) plus a live /congress page capture and the hot_topics.py 30-day scan.

Same brand system + browser-frame screenshot pattern as
_build_systemic_risk_carousel.py (giant-stat-slide family), reused here for
consistency across the showcase series. Not tied to the daily-post/reels-kit
pipeline -- a standalone 9-slide 4:5 (2160x2700 @ device_scale_factor=2)
carousel.

HARD RAILS (see CLAUDE.md task + congress.json's own disclaimer):
  - These are SELF-REPORTED STOCK Act disclosures: public record, dated, up
    to 45-day filing lag, dollar amounts are reported RANGES.
  - Every slide frames this as disclosure/optics/questions -- NEVER an
    accusation of illegality, insider trading, or wrongdoing by any
    individual.
  - "Committee overlap" is an approximate, curated committee->sector
    heuristic -- a "flag", not a legal jurisdiction claim.
  - Every slide footer carries the rails line; cover + CTA also carry the
    educational/NFA line.

Screenshots pre-staged in higgs/_platform_src/ (captured live, 2026-07-23,
from https://highreturnethicalscreen.vercel.app/congress):
  congress_stats.jpg          -- trades/members/est.volume/date-range cards
  congress_overlap_pill.jpg   -- site's own disclaimer + "854 of 9,735 flagged"
  congress_msft.jpg           -- live table filtered/searched to MSFT rows
  congress_shreve_profile.jpg -- Jefferson Shreve member profile card
  congress_whitesides.jpg     -- George Whitesides row, MSFT trade, OVERLAP tag
  _congress_top.jpg           -- full header (nav+stats+disclaimer+pills)

    python higgs/_build_congress_carousel.py

Writes 9 PNGs + caption.txt + manifest.json to higgs/congress_showcase_<date>/.
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
OUT = HIGGS / f"congress_showcase_{DATE}"

W, H = 1080, 1350  # CSS px canvas; device_scale_factor=2 -> 2160x2700 output

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700;9..144,900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"

BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:-40px;background-size:cover;background-position:center;background-repeat:no-repeat}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:64px 64px;display:flex;flex-direction:column;z-index:2}}
.brand{{display:flex;align-items:baseline;gap:2px;font-family:'JetBrains Mono';font-weight:800;font-size:22px;letter-spacing:1px;text-shadow:0 2px 12px rgba(0,0,0,.7)}}
.brand .ai{{color:#fff}} .brand .stack{{color:#34D399}} .brand .rest{{color:#fff}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:22px;letter-spacing:3px;color:#8893A4;text-shadow:0 2px 14px rgba(0,0,0,.7)}}
.bigstat{{font-family:'JetBrains Mono';font-weight:800;line-height:0.92;letter-spacing:-2px;text-shadow:0 6px 40px rgba(0,0,0,.6)}}
.statlabel{{font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:1.5px;margin-top:14px;text-shadow:0 2px 14px rgba(0,0,0,.65)}}
.head{{font-family:Fraunces;font-weight:700;line-height:1.1;letter-spacing:-1px;color:#fff;text-shadow:0 3px 22px rgba(0,0,0,.65)}}
.sub{{font-family:Inter;font-size:34px;line-height:1.4;color:#B9C3D0;text-shadow:0 2px 16px rgba(0,0,0,.6)}}
.foot{{font-family:'JetBrains Mono';font-size:14px;color:#8893A4;letter-spacing:.3px;line-height:1.5;text-shadow:0 1px 10px rgba(0,0,0,.75)}}
.pill{{display:inline-flex;align-items:center;gap:12px;font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:16px 28px;border-radius:14px}}
.proof{{border-radius:14px;overflow:hidden;background:#0d1017;border:1.5px solid rgba(255,255,255,.14);box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.chrome{{height:28px;background:#1a2029;display:flex;align-items:center;gap:7px;padding:0 14px;flex:none}}
.dot{{width:9px;height:9px;border-radius:50%}}
.chip{{font-family:'JetBrains Mono';font-weight:800;color:#fff;background:#161c26;border:1.5px solid rgba(255,255,255,.16);border-radius:12px;padding:14px 22px;display:flex;align-items:baseline;gap:10px}}
.row{{display:flex;align-items:center;justify-content:space-between;background:#12161d;border:1.5px solid rgba(255,255,255,.12);border-radius:12px;padding:16px 22px}}
"""

RAILS = "Public record · self-reported STOCK Act filings · not an accusation of wrongdoing."
DISCLAIMER = "Educational research only — not financial advice."

# --------------------------------------------------------------- hero photo
# higgs/hero_congress_2026-06-21.png: 1792x2304 portrait, U.S. Capitol dome
# on near-black w/ green-teal smoke wisps + bokeh. Top ~third near-black
# (good for headlines), dome center/lower, green wisps sweep lower-right.
# One config per slide index (0-8) so the same photo reads as a DIFFERENT
# framing on every slide: background-position moves which part of the photo
# shows through `background-size:cover`, `scale` is a subtle extra zoom
# (1.0-1.2) applied via transform, `flip` mirrors horizontally on about half
# the slides (scaleX negative), and `scrim` is a per-slide linear-gradient
# scrim -- darker/denser on the text-heavy and screenshot slides (3, 5, 7)
# so the busy dome/wisp area never fights the browser-frame screenshots or
# body copy sitting on top of it.
_HERO_CFG = {
    0: dict(pos="50% 25%", scale=1.08, flip=False,
            scrim="linear-gradient(180deg, rgba(10,13,18,.52) 0%, rgba(10,13,18,.34) 26%, rgba(10,13,18,.72) 58%, rgba(10,13,18,.96) 100%)"),
    1: dict(pos="78% 55%", scale=1.15, flip=False,
            scrim="linear-gradient(165deg, rgba(9,12,16,.8) 0%, rgba(9,12,16,.66) 42%, rgba(9,12,16,.92) 100%)"),
    2: dict(pos="18% 65%", scale=1.2, flip=True,
            scrim="linear-gradient(200deg, rgba(9,14,13,.82) 0%, rgba(9,14,13,.68) 38%, rgba(9,14,13,.93) 100%)"),
    3: dict(pos="50% 12%", scale=1.25, flip=False,
            scrim="linear-gradient(180deg, rgba(8,10,14,.88) 0%, rgba(8,10,14,.8) 28%, rgba(8,10,14,.9) 55%, rgba(8,10,14,.97) 100%)"),
    4: dict(pos="65% 45%", scale=1.05, flip=True,
            scrim="linear-gradient(175deg, rgba(10,13,18,.76) 0%, rgba(10,13,18,.6) 40%, rgba(10,13,18,.93) 100%)"),
    5: dict(pos="35% 20%", scale=1.15, flip=False,
            scrim="linear-gradient(180deg, rgba(8,11,15,.87) 0%, rgba(8,11,15,.74) 32%, rgba(8,11,15,.96) 100%)"),
    6: dict(pos="75% 78%", scale=1.1, flip=True,
            scrim="linear-gradient(200deg, rgba(9,14,13,.7) 0%, rgba(9,14,13,.53) 34%, rgba(9,14,13,.9) 100%)"),
    7: dict(pos="50% 10%", scale=1.2, flip=True,
            scrim="linear-gradient(180deg, rgba(8,10,14,.88) 0%, rgba(8,10,14,.77) 28%, rgba(8,10,14,.63) 52%, rgba(8,10,14,.95) 100%)"),
    8: dict(pos="45% 55%", scale=1.08, flip=False,
            scrim="linear-gradient(175deg, rgba(10,13,18,.72) 0%, rgba(10,13,18,.52) 28%, rgba(10,13,18,.91) 100%)"),
}


def hero_layer(idx, hero_b64):
    c = _HERO_CFG[idx]
    sx = -c["scale"] if c["flip"] else c["scale"]
    return (f"<div class='hero' style=\"background-image:url('{hero_b64}');"
            f"background-position:{c['pos']};transform:scale({sx},{c['scale']});"
            f"transform-origin:center\"></div>"
            f"<div class='scrim' style=\"background:{c['scrim']}\"></div>")


def page(body, bg=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{bg}{body}</div></body></html>"


def brandbar():
    return "<div class='brand'><span class='ai'>AI</span><span class='stack'>STACK</span><span class='rest'>&nbsp;·&nbsp;TERMINAL</span></div>"


def foot_rails_only():
    return f"<div class='foot' style='margin-top:auto;padding-top:16px'>{RAILS}</div>"


def foot_full():
    return f"<div class='foot' style='margin-top:auto;padding-top:16px'>{RAILS}<br>{DISCLAIMER}</div>"


def proof_frame(img_b64, box_h, obj_pos="center top", fit="contain"):
    return f"""<div class='proof' style='width:100%;height:{box_h}px;display:flex;flex-direction:column'>
      <div class='chrome'><div class='dot' style='background:#e0605a'></div><div class='dot' style='background:#e0b23b'></div><div class='dot' style='background:#3bbf6b'></div></div>
      <div style='flex:1;background:#0d1017;display:flex;align-items:center;justify-content:center;overflow:hidden'>
        <img src='{img_b64}' style='width:100%;height:100%;object-fit:{fit};object-position:{obj_pos};display:block'>
      </div>
    </div>"""


# --------------------------------------------------------------------------- slides

def slide_cover(hero_b64):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:34px;max-width:920px' class='kick'>PUBLIC RECORD · STOCK ACT DISCLOSURES</div>
      <div class='head' style="margin-top:22px;font-size:102px;color:#fff">Congress traded<br>up to <span style="color:#E0A23B">$1 BILLION</span><br>in stock.</div>
      <div class='head' style="margin-top:8px;font-size:64px;color:#B9C3D0;font-style:italic">Guess what they bought.</div>
      <div class='sub' style="margin-top:26px;max-width:880px;font-size:46px"><span style="color:#E0A23B;font-weight:700">9,735</span> disclosed trades. 118 members of Congress. Since 2015. All public record.</div>
      <div style='margin-top:auto;display:flex;align-items:center;justify-content:space-between'>
        <div class='pill'>SWIPE TO SEE WHAT →</div></div>
      <div class='foot' style='padding-top:18px'>{RAILS}<br>{DISCLAIMER}</div></div>""", bg=hero_layer(0, hero_b64))


def slide_shock(kick, big_stat, stat_label, headline, sub, hero_idx, hero_b64, stat_size=170, accent="#E0A23B",
                 proof_img=None, proof_pos="center top", proof_h=380, proof_fit="contain",
                 extra_rows=None, full_footer=False, head_size=38, fill=False, sub_size=None):
    # `fill=True` wraps the whole content block (kick..proof) in a
    # margin-top:auto column so it centers in the space between the
    # brandbar and the footer -- same single-auto-edge-per-gap trick as
    # _build_value_carousel.py's slide_quote/slide_text(fill=True): the
    # footer's own margin-top:auto supplies the matching bottom gap, so
    # free space splits evenly instead of the block floating at the top.
    # Used for sparse/text-only slides (e.g. the 854 overlap explainer)
    # so they fill the frame instead of leaving dead air above the footer.
    # sub_size: body copy is sized relative to this slide's own headline so it
    # reads as "nearly as big as the headline, a little smaller" on a phone
    # screen (owner feedback 2026-07-23) -- default ~0.75x of head_size unless
    # the caller dials it back for a screenshot slide (3/5/7) to protect the
    # proof frame from being squeezed.
    if sub_size is None:
        sub_size = round(head_size * 0.75)
    proof_html = f"<div style='margin-top:22px'>{proof_frame(proof_img, proof_h, proof_pos, proof_fit)}</div>" if proof_img else ""
    rows_html = ""
    if extra_rows:
        items = "".join(
            f"<div class='row' style='margin-top:12px'><div style=\"font-family:'JetBrains Mono';font-weight:700;font-size:21px;color:#fff\">{r[0]}</div><div style=\"font-family:'JetBrains Mono';font-weight:800;font-size:21px;color:{accent}\">{r[1]}</div></div>"
            for r in extra_rows)
        rows_html = f"<div style='margin-top:6px'>{items}</div>"
    foot = foot_full() if full_footer else foot_rails_only()
    content = f"""<div class='kick'>{kick}</div>
      <div class='bigstat' style="margin-top:16px;font-size:{stat_size}px;color:{accent}">{big_stat}</div>
      <div class='statlabel' style="color:{accent}">{stat_label}</div>
      <div class='head' style="margin-top:20px;font-size:{head_size}px">{headline}</div>
      <div class='sub' style="margin-top:12px;max-width:960px;font-size:{sub_size}px">{sub}</div>
      {rows_html}
      {proof_html}"""
    if fill:
        body = f"<div style='margin-top:auto;display:flex;flex-direction:column'>{content}</div>"
    else:
        body = f"<div style='margin-top:26px;display:flex;flex-direction:column'>{content}</div>"
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      {foot}</div>""", bg=hero_layer(hero_idx, hero_b64))


def slide_names(kick, headline, names, sub, hero_idx, hero_b64, proof_img=None, proof_h=380, proof_fit="contain",
                 head_size=44, fill=False, sub_size=None):
    # Same fill=True centering trick as slide_shock -- for the sparse,
    # no-screenshot transition slide (e.g. "trending tie-in") that would
    # otherwise float in the top third with dead air above the footer.
    # sub_size: see slide_shock's comment -- defaults to ~0.75x head_size,
    # dialed back explicitly on screenshot slides to protect the proof frame.
    if sub_size is None:
        sub_size = round(head_size * 0.75)
    chips = "".join(
        f"<div class='chip'><span>{n[0]}</span><span style='color:#7FE9C2;font-size:22px'>{n[1]}</span></div>"
        for n in names)
    proof_html = f"<div style='margin-top:20px'>{proof_frame(proof_img, proof_h, 'center top', proof_fit)}</div>" if proof_img else ""
    content = f"""<div class='kick'>{kick}</div>
      <div class='head' style="margin-top:14px;font-size:{head_size}px">{headline}</div>
      <div style='display:flex;flex-wrap:wrap;gap:12px;margin-top:22px'>{chips}</div>
      <div class='sub' style="margin-top:18px;max-width:960px;font-size:{sub_size}px">{sub}</div>
      {proof_html}"""
    if fill:
        body = f"<div style='margin-top:auto;display:flex;flex-direction:column'>{content}</div>"
    else:
        body = f"<div style='margin-top:26px;display:flex;flex-direction:column'>{content}</div>"
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      {foot_rails_only()}</div>""", bg=hero_layer(hero_idx, hero_b64))


def slide_cta(img_b64, hero_idx, hero_b64):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:30px' class='kick'>EVERY DISCLOSED TRADE, IN ONE PLACE</div>
      <div class='head' style="margin-top:14px;font-size:64px">Check what your rep is trading.</div>
      <div class='sub' style="margin-top:14px;max-width:960px;font-size:44px">Search by politician, ticker, sector, or committee-overlap flag — <span style="color:#E0A23B;font-weight:700">9,735</span> disclosed trades, free, sourced straight from the House Clerk.</div>
      <div style='margin-top:22px'>{proof_frame(img_b64, 150, 'center top', 'contain')}</div>
      <div style='margin-top:auto;display:flex;flex-direction:column;gap:12px;padding-top:20px'>
        <div class='pill' style='font-size:28px;padding:20px 32px;width:fit-content'>\U0001f4ac COMMENT "CONGRESS"</div>
        <div style="font-family:'JetBrains Mono';font-weight:600;font-size:19px;letter-spacing:.5px;color:#B9C3D0;text-shadow:0 2px 12px rgba(0,0,0,.7)">↳ and I'll DM you the link</div>
        <div class='foot' style='margin-top:6px'>{RAILS}<br>{DISCLAIMER}</div></div></div>""", bg=hero_layer(hero_idx, hero_b64))


def _b64(path, ext="jpeg"):
    p = pathlib.Path(path)
    data = p.read_bytes()
    return f"data:image/{ext};base64," + base64.b64encode(data).decode()


def build():
    names = ["congress_stats", "congress_overlap_pill", "congress_msft",
              "congress_shreve_profile", "congress_whitesides", "_congress_top"]
    imgs = {name: _b64(SRC / f"{name}.jpg") for name in names}
    hero_b64 = _b64(HIGGS / "hero_congress_2026-06-21.png", ext="png")

    slides = {}

    # 0 -------------------------------------------------------------- cover
    # Hero photo (Capitol dome + green wisps) replaces the old blurred
    # disclosure-table/screenshot motif as the cover background.
    slides["0_cover.png"] = slide_cover(hero_b64)

    # 1 --------------------------------------------------------- the number
    slides["1_billion.png"] = slide_shock(
        "01 · THE NUMBER",
        "$1.1B", "DISCLOSED TRADING VOLUME · UP TO",
        "<span style='color:#E0A23B'>9,735</span> disclosed trades. 118 members. One public record.",
        "Every member of Congress must disclose stock trades within 45 days under the STOCK Act. Add up every disclosed trade since 2015 and the reported dollar ranges top out at an estimated <span style='color:#E0A23B;font-weight:700'>$300.2M–$1.1B</span> — self-reported, unverified, and fully public.",
        1, hero_b64,
        stat_size=200, accent="#E0A23B", head_size=48,
        proof_img=imgs["congress_stats"], proof_h=150)

    # 2 ------------------------------------------------------- the overlap
    # Sparse explainer slide -- bigger headline + fill=True to center the
    # block between the brandbar and footer (same technique as the value
    # carousel's fill=True text slides), so it fills the frame instead of
    # floating at the top.
    slides["2_overlap.png"] = slide_shock(
        "02 · THE OVERLAP FLAG",
        "854", "DISCLOSED TRADES FLAGGED",
        "<span style='color:#E0A23B'>854</span> times, a member traded a sector their own committee has a hand in.",
        "Our tracker <span style='color:#E0A23B;font-weight:700'>flags</span> any disclosed trade in a sector that lines up with the member's committee assignments — committees that help write the rules for that industry. It's a correlational <span style='color:#E0A23B;font-weight:700'>overlap</span>, not a legal or ethics finding: <span style='color:#E0A23B'>854</span> of <span style='color:#E0A23B'>9,735</span> trades carry the flag.",
        2, hero_b64,
        stat_size=230, accent="#E0A23B", head_size=50, fill=True,
        proof_img=imgs["congress_overlap_pill"], proof_h=165)

    # 3 --------------------------------------------------- the AI portfolio
    # Screenshot slide (AI-portfolio table) -- smaller headline bump so the
    # table screenshot isn't squeezed/cropped.
    slides["3_portfolio.png"] = slide_names(
        "03 · THE PORTFOLIO",
        "Congress's most-traded stocks are your <span style='color:#7FE9C2'>AI portfolio</span>.",
        [("MSFT", "132"), ("NVDA", "127"), ("AMZN", "96"),
         ("AVGO", "67"), ("META", "66"), ("GOOGL", "57")],
        "Ranked by number of disclosed trades since 2015 — not dollar value. Six names, and they're the same six carrying most AI-stock portfolios.",
        3, hero_b64,
        head_size=48, sub_size=32,
        proof_img=imgs["congress_msft"], proof_h=360)

    # 4 -------------------------------------------------------- the whales
    slides["4_whales.png"] = slide_shock(
        "04 · THE WHALES",
        "$390M", "JEFFERSON SHREVE (R-IN) · UP TO · 633 TRADES",
        "A handful of members account for hundreds of millions in disclosed volume.",
        "All disclosed under the STOCK Act. A public official's filing is public record — not proof of anything improper.",
        4, hero_b64,
        stat_size=180, accent="#E0A23B", head_size=48,
        extra_rows=[
            ("GILBERT CISNEROS (D-CA)", "1,461 TRADES · UP TO $53M"),
            ("NANCY PELOSI (D-CA)", "31 TRADES · UP TO $130M"),
        ],
        proof_img=imgs["congress_shreve_profile"], proof_h=270)

    # 5 ------------------------------------------------- concrete overlap
    # Screenshot slide (Whitesides example) -- smaller headline bump so
    # the row screenshot stays legible; only color emphasis added.
    slides["5_example.png"] = slide_shock(
        "05 · ONE CONCRETE EXAMPLE",
        "$250K–$500K", "DISCLOSED SALE OF MICROSOFT STOCK",
        "Rep. George Whitesides sits on the House Science, Space, and Technology Committee.",
        "That committee's jurisdiction, per our sector map, covers Technology Services — Microsoft's sector. In March 2025 he disclosed selling MSFT stock valued <span style='color:#E0A23B;font-weight:700'>$250,001–$500,000</span>. <span style='color:#E0A23B;font-weight:700'>Flagged</span> by our tracker as a committee-sector <span style='color:#E0A23B;font-weight:700'>overlap</span> — an approximate, correlational tag. Disclosed, on the public record. Not an accusation of insider trading or any rule violation.",
        5, hero_b64,
        stat_size=110, accent="#E0A23B", head_size=42, sub_size=27,
        proof_img=imgs["congress_whitesides"], proof_h=260)

    # 6 -------------------------------------------------------- trending tie-in
    # No-screenshot transition slide -- bigger headline + fill=True to
    # center between brandbar and footer.
    slides["6_trending.png"] = slide_names(
        "06 · AND RIGHT NOW…",
        "The sectors Congress keeps trading are the same ones ripping in 2026.",
        [("MU", "+755%"), ("STX", "+497%"), ("INTC", "+351%"),
         ("AMD", "+245%"), ("ASML", "+146%")],
        "1-year price performance on our chips/AI momentum scan — the same Electronic Technology / Technology Services sectors Congress trades most. Past performance doesn't predict future returns.",
        6, hero_b64,
        head_size=56, fill=True,
        proof_img=None)

    # 7 -------------------------------------------------------------- the tool
    # Screenshot slide (the tool) -- smaller headline bump to protect the
    # screenshot; overlap-flag language colored for emphasis.
    slides["7_tool.png"] = slide_shock(
        "07 · THE TOOL",
        "9,735", "TRADES · SEARCHABLE, FREE",
        "Every trade is public. We put it in one place.",
        "Filter by politician, ticker, sector, party, ideology, or <span style='color:#E0A23B;font-weight:700'>committee-overlap flag</span>. Every row links back to the original House Clerk PDF filing.",
        7, hero_b64,
        stat_size=150, accent="#7FE9C2", head_size=42, sub_size=30,
        proof_img=imgs["_congress_top"], proof_h=310)

    # 8 -------------------------------------------------------------------- CTA
    slides["8_cta.png"] = slide_cta(imgs["congress_stats"], 8, hero_b64)

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

    caption = """Congress disclosed trading up to $1.1 BILLION in stock. We checked what they bought. \U0001f440\U0001f4c8

Every member of Congress has to report their stock trades within 45 days — that's the STOCK Act. We pulled all 9,735 of those disclosures, filed by 118 members since 2015, straight from the House Clerk. Here's what showed up:

\U0001f4b0 Disclosed trading volume: up to $1.1 billion (reported as ranges — that's how the law requires it, not our estimate)
\U0001f6a9 854 times, a member disclosed a trade in a sector their own committee has a hand in regulating — flagged by our tracker, not an accusation
\U0001f4ca Their most-traded stocks? Microsoft, Nvidia, Amazon, Broadcom, Meta, Google — basically the AI stock market
\U0001f40b A few names show up again and again: Jefferson Shreve (633 trades, up to $390M), Gilbert Cisneros (1,461 trades), Nancy Pelosi (up to $130M)
\U0001f50d One concrete example: a member of the House Science, Space, and Technology Committee disclosed selling $250K–$500K of Microsoft stock — in a sector that committee's own jurisdiction covers
\U0001f525 And 2026's hottest stocks? The same chip sector — AMD, Micron, Intel, ASML, and Seagate are all up huge over the past year

We put every disclosed trade in one searchable place — free, sourced, dated.

⚠️ Everything above comes from self-reported, unverified STOCK Act disclosures filed with the U.S. House Clerk. Dollar amounts are reported as ranges, filings can lag up to 45 days, and none of this is an accusation of wrongdoing by any individual. Educational research only — not financial advice, not a recommendation to buy or sell any security.

Comment "CONGRESS" and I'll DM you the link \U0001f4f2

#congresstrading #pelositracker #stockmarket #politics #AIstocks #investing #capitolhill #politicalfinance #stocktok #fintok #financetok #wallstreet #dueDiligence #investing101 #stockmarketnews #transparency
"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")

    manifest = {
        "kind": "congress_showcase_carousel",
        "product": "AI Stack Terminal",
        "source_url": "https://highreturnethicalscreen.vercel.app/congress",
        "date": DATE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_source": "web/public/data/congress.json (generated 2026-07-11T13:54:18Z, source = House Clerk STOCK Act disclosure PDFs) + live /congress page + scripts/hot_topics.py --days 30",
        "aspect": "4:5 (2160x2700) — Instagram carousel",
        "slides": list(slides.keys()),
        "standalone": True,
        "hard_rails": [
            "Self-reported STOCK Act disclosures; public record; amounts are reported ranges; up to 45-day filing lag.",
            "Committee overlap is an approximate, correlational committee->sector heuristic, not a legal jurisdiction or ethics claim.",
            "No slide asserts illegality, insider trading, or wrongdoing by any individual.",
        ],
        "concrete_overlap_example": {
            "politician": "George Whitesides",
            "party_state": "D-CA27",
            "committee": "House Committee on Science, Space, and Technology",
            "ticker": "MSFT",
            "sector": "Technology Services",
            "txn_type": "SELL",
            "txn_date": "03/24/2025",
            "amount_range": "$250,001–$500,000",
            "source": "https://disclosures-clerk.house.gov (2026-07-11 pull, web/public/data/congress.json trades[].conflict_signal)",
        },
        "posting_instructions": "Post as an Instagram carousel (not a reel). CTA slide asks viewers to comment \"CONGRESS\" for a DM'd link (not link-in-bio).",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"DONE slides={len(slides)} -> {OUT}")


if __name__ == "__main__":
    build()
