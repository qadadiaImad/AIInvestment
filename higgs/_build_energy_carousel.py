"""Standalone IG carousel: "AI doesn't run on chips. It runs on electricity."
-- an ENERGY / AI-power-crunch reframe post, built from LIVE data in
web/public/data/site.json (generated 2026-07-22T09:47:01Z) -- the `layers`
counts, `stocks[*].performance.perf_1y`, and `capital_web.edges` gigawatt
compute-commitment records -- plus live captures (2026-07-23) of the
/screener and /map pages.

Same brand system + browser-frame screenshot pattern as
_build_value_carousel.py (the most-polished entry in the showcase family --
reused verbatim here: BASE css, foot_full(), proof_frame(), slide_shock,
slide_text, slide_tool, slide_cta) so this reads as the same product series.
Not tied to the daily-post/reels-kit pipeline -- a standalone 9-slide 4:5
(2160x2700 @ device_scale_factor=2) carousel.

THE IDEA (owner's angle): everyone buys Nvidia; almost nobody asks who
powers the datacenters. AI compute is now measured in GIGAWATTS -- the same
unit as power plants -- and the "energy" layer of the AI stack (34 tracked
names) is bigger than the chip layer (30). Several of 2026's best-performing
AI-adjacent stocks aren't chip names at all -- they're power/grid/nuclear
names most people have never heard of.

HARD RAILS (non-negotiable, see CLAUDE.md task):
  - Gigawatt commitments are company-reported or SEC-filed figures -- never
    asserted as verified/audited fact beyond that; certainty is labeled
    "reported" or "filed" per-figure, matching capital_web.edges[].certainty.
  - 1-year returns are backward-looking, factual, past performance --
    labeled "past-year return, not a prediction" -- never framed as a
    forecast or a buy signal.
  - No buy/sell language, no price targets, no recommendation to trade any
    security. A read, not a call.
  - No news outlet named anywhere.
  - Every slide footer carries the rails line + the educational/NFA line.

Data verified directly from web/public/data/site.json (generated
2026-07-22T09:47:01Z) at build time:
  layers: L0-energy=34, L1-chips=30, L2-infra=23, L3-models=0, L4-application=21
  stocks[*].performance.perf_1y: VRT=135.7 NVT=111.3 GEV=87.2 (price 1078.81)
    TRGP=64.6 PWR=58.3 PH=32.5 UUUU=30.7 WMB=24.4 AEP=21.2 BWXT=20.5 D=20.1
    UEC=18.5
  capital_web.edges (gigawatt compute commitments):
    openai -> NVDA   10 GW   "at least 10 GW of NVIDIA systems" (reported,
                      news-html, investor.nvidia.com)
    anthropic -> AMZN 5 GW   $100.0B  ~decade            (reported, curated)
    anthropic -> GOOGL 1 GW  $200.0B  1,000,000 TPUs     (reported, curated)
    anthropic -> AVGO 3.5 GW next-gen TPU compute from 2027 (FILED, SEC 8-K
                      d87999d8k.htm)
    anthropic -> spacex 300 MW  $1.3B/mo  220,000 GPUs until 2029-05 (reported)

Screenshots captured LIVE (2026-07-23) via Chromium/Playwright automation of
https://highreturnethicalscreen.vercel.app/ (home), /screener, and /map,
staged in higgs/_platform_src/:
  energy_layers_banner.jpg     -- home page header strip: "AI STACK: ENERGY
                                   34 . CHIPS 30 . INFRA 23 . MODELS 0 .
                                   APPS 21" -- confirms the 34-name claim
                                   directly from the live tool.
  energy_screener.jpg          -- /screener, SECTOR=AI, sorted by LAYER asc
                                   (groups all 34 ENERGY-badged rows first);
                                   header + ~17 rows incl. GEV, TRGP, VRT,
                                   BWXT, PH, WMB, PWR, NVT, AEP with PRICE /
                                   1Y / 1Y% columns legible.
  energy_map_gw.jpg            -- /map, "DRILL INTO NODE" = Anthropic,
                                   cropped to the outbound-relationship cards
                                   for GOOGL (1 GW / $200.0B), AMZN (5 GW /
                                   $100.0B), SpaceX (300 MW) -- header, GW
                                   figure, and REPORTED tag all legible.
  energy_capital_web_full.jpg  -- full /map global graph (unfiltered), used
                                   blurred/dimmed as the cover hero -- same
                                   "screenshot as atmospheric hero" technique
                                   as the value/systemic-risk carousels.
Live page values (e.g. the /screener "1Y" and "1Y%" columns) drift slightly
from the 2026-07-22 site.json snapshot used for slide copy -- expected, same
caveat as _build_value_carousel.py: screenshots are proof-of-tool, not the
numeric source of truth for the copy.

    python higgs/_build_energy_carousel.py

Writes 9 PNGs + caption.txt + manifest.json to higgs/energy_showcase_<date>/.
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
OUT = HIGGS / f"energy_showcase_{DATE}"

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
.sub{{font-family:Inter;font-size:25px;line-height:1.44;color:#B9C3D0}}
.foot{{font-family:'JetBrains Mono';font-size:14px;color:#8893A4;letter-spacing:.3px;line-height:1.5}}
.pill{{display:inline-flex;align-items:center;gap:12px;font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:16px 28px;border-radius:14px}}
.proof{{border-radius:14px;overflow:hidden;background:#0d1017;border:1.5px solid rgba(255,255,255,.14);box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.chrome{{height:28px;background:#1a2029;display:flex;align-items:center;gap:7px;padding:0 14px;flex:none}}
.dot{{width:9px;height:9px;border-radius:50%}}
.chip{{font-family:'JetBrains Mono';font-weight:800;color:#fff;background:#161c26;border:1.5px solid rgba(255,255,255,.16);border-radius:12px;padding:14px 22px;display:flex;align-items:baseline;gap:10px}}
.row{{display:flex;align-items:center;justify-content:space-between;background:#12161d;border:1.5px solid rgba(255,255,255,.12);border-radius:12px;padding:16px 22px}}
"""

RAILS = "GW figures are company-reported/SEC-filed · 1-year returns are past performance, not a prediction."
DISCLAIMER = "Educational research only — not financial advice."


def page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"


def brandbar():
    return "<div class='brand'><span class='ai'>AI</span><span class='stack'>STACK</span><span class='rest'>&nbsp;·&nbsp;TERMINAL</span></div>"


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

def slide_cover(bg_b64):
    return page(f"""<div class='hero' style="background-image:url('{bg_b64}');filter:blur(3px) brightness(.38)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,rgba(10,13,18,.74) 0%,rgba(10,13,18,.5) 30%,rgba(10,13,18,.82) 62%,rgba(10,13,18,.97) 100%)"></div>
    <div class='pad'>{brandbar()}
      <div style='margin-top:34px;max-width:920px' class='kick'>THE PART EVERYONE IGNORES</div>
      <div class='head' style="margin-top:24px;font-size:88px;color:#fff">AI doesn't run<br>on chips.</div>
      <div class='head' style="margin-top:10px;font-size:88px;color:#E0A23B">It runs on<br>electricity.</div>
      <div class='sub' style="margin-top:28px;max-width:880px;font-size:40px;text-shadow:0 2px 16px rgba(0,0,0,.75)">Everyone buys Nvidia. Almost nobody asks who powers the datacenter it sits in.</div>
      <div style='margin-top:auto;display:flex;align-items:center;justify-content:space-between'>
        <div class='pill'>SWIPE TO SEE WHY →</div></div>
      {foot_full()}</div>""")


def slide_text(kick, head, sub, rows=None, head_size=58, sub_size=None, fill=False):
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
                 chips=None, note=None, sub_size=30, fill=False, head_size=40):
    proof_html = f"<div style='margin-top:20px'>{proof_frame(proof_img, proof_h, proof_pos, proof_fit)}</div>" if proof_img else ""
    chips_html = ""
    if chips:
        c = "".join(
            f"<div class='chip'><span>{n}</span><span style='color:{accent};font-size:22px'>{v}</span></div>"
            for n, v in chips)
        chips_html = f"<div style='display:flex;flex-wrap:wrap;gap:12px;margin-top:18px'>{c}</div>"
    note_html = f"<div class='sub' style='margin-top:10px;font-size:19px;font-style:italic;color:#8893A4'>{note}</div>" if note else ""
    content = f"""<div class='kick'>{kick}</div>
      <div class='bigstat' style="margin-top:16px;font-size:{stat_size}px;color:{accent}">{big_stat}</div>
      <div class='statlabel' style="color:{accent}">{stat_label}</div>
      <div class='head' style="margin-top:20px;font-size:{head_size}px">{headline}</div>
      <div class='sub' style="margin-top:12px;max-width:960px;font-size:{sub_size}px">{sub}</div>
      {chips_html}
      {note_html}
      {proof_html}"""
    body = (f"<div style='margin-top:auto;display:flex;flex-direction:column'>{content}</div>" if fill
            else f"<div style='margin-top:26px;display:flex;flex-direction:column'>{content}</div>")
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      {foot_full()}</div>""")


def slide_names(kick, headline, names, sub, head_size=56, sub_size=42, fill=True, accent="#7FE9C2"):
    chips = "".join(
        f"<div class='chip'><span>{n}</span><span style='color:{accent};font-size:28px'>{v}</span></div>"
        for n, v in names)
    content = f"""<div class='kick'>{kick}</div>
      <div class='head' style="margin-top:20px;font-size:{head_size}px">{headline}</div>
      <div style='display:flex;flex-wrap:wrap;gap:14px;margin-top:28px'>{chips}</div>
      <div class='sub' style="margin-top:24px;max-width:960px;font-size:{sub_size}px">{sub}</div>"""
    body = (f"<div style='margin-top:auto;display:flex;flex-direction:column'>{content}</div>" if fill
            else f"<div style='margin-top:28px;display:flex;flex-direction:column'>{content}</div>")
    return page(f"""<div class='pad'>{brandbar()}
      {body}
      {foot_full()}</div>""")


def slide_tool(kick, head, sub, proof_img, proof_h=420, proof_fit="contain", sub_size=32, note=None):
    note_html = f"<div class='sub' style=\"margin-top:12px;font-size:18px;color:#8893A4\">{note}</div>" if note else ""
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:28px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:16px;font-size:48px">{head}</div>
      <div class='sub' style="margin-top:14px;max-width:960px;font-size:{sub_size}px">{sub}</div>
      <div style='margin-top:22px'>{proof_frame(proof_img, proof_h, 'left top', proof_fit)}</div>
      {note_html}
      {foot_full()}</div>""")


def slide_cta(img_b64):
    return page(f"""<div class='pad'>{brandbar()}
      <div style='margin-top:30px' class='kick'>EVERY ENERGY NAME IN THE AI STACK</div>
      <div class='head' style="margin-top:12px;font-size:52px">Check who actually powers the boom.</div>
      <div class='sub' style="margin-top:12px;max-width:960px;font-size:38px">34 energy names, every gigawatt commitment we track, mapped against price and 1-year performance — free, dated, sourced. No login.</div>
      <div style='margin-top:20px'>{proof_frame(img_b64, 190, 'left top', 'contain')}</div>
      <div style='margin-top:auto;display:flex;flex-direction:column;gap:12px;padding-top:20px'>
        <div class='pill' style='font-size:28px;padding:20px 32px;width:fit-content'>\U0001f4ac COMMENT "POWER"</div>
        <div style="font-family:'JetBrains Mono';font-weight:600;font-size:19px;letter-spacing:.5px;color:#B9C3D0">↳ and I'll DM you the link</div>
        {foot_full()}</div></div>""")


def _b64(path, ext="jpeg"):
    p = pathlib.Path(path)
    data = p.read_bytes()
    return f"data:image/{ext};base64," + base64.b64encode(data).decode()


def build():
    names = ["energy_capital_web_full", "energy_layers_banner", "energy_screener", "energy_map_gw"]
    imgs = {name: _b64(SRC / f"{name}.jpg") for name in names}

    slides = {}

    # 0 -------------------------------------------------------------- cover
    slides["0_cover.png"] = slide_cover(imgs["energy_capital_web_full"])

    # 1 --------------------------------------------------------- the reframe
    slides["1_gigawatts.png"] = slide_shock(
        "01 · THE NEW UNIT OF AI COMPUTE",
        "10 GW", "OPENAI &harr; NVIDIA · AT LEAST · REPORTED",
        "AI compute is now measured in <span style='color:#E0A23B'>gigawatts</span> — the same unit as power plants.",
        "OpenAI and NVIDIA's strategic partnership targets deploying at least 10 GW of NVIDIA systems; NVIDIA intends to invest up to $100B in OpenAI as each gigawatt is deployed. And that's just one deal.",
        stat_size=200, accent="#E0A23B",
        chips=[
            ("ANTHROPIC → AMAZON", "5 GW · reported"),
            ("ANTHROPIC → GOOGLE", "1 GW · reported"),
            ("ANTHROPIC → BROADCOM", "3.5 GW · filed"),
            ("ANTHROPIC → SPACEX", "300 MW · reported"),
        ])

    # 2 --------------------------------------------------------- visceral scale
    slides["2_reactor.png"] = slide_shock(
        "02 · MAKE IT VISCERAL",
        "≈10", "NUCLEAR REACTORS' WORTH OF POWER",
        "1 gigawatt ≈ one full-size nuclear reactor ≈ power for roughly 800,000 U.S. homes.",
        "10 GW — OpenAI's commitment alone — is roughly ten reactors' worth of continuous electricity. For one company's AI buildout. Not the whole industry. One company.",
        stat_size=230, accent="#E0A23B", fill=True, sub_size=34)

    # 3 --------------------------------------------------- the overlooked layer
    slides["3_biggestlayer.png"] = slide_shock(
        "03 · THE LAYER EVERYONE SKIPS",
        "34", "NAMES IN THE ENERGY LAYER — MORE THAN ANY OTHER",
        "Energy is the single <span style='color:#34D399'>biggest layer</span> in the AI stack. Bigger than chips.",
        "34 energy names we track vs. 30 in chips, 23 in infra, 21 in application. Everyone talks Nvidia. Almost nobody talks about who powers it.",
        stat_size=210, accent="#34D399",
        proof_img=imgs["energy_layers_banner"], proof_h=140, proof_pos="left top")

    # 4 --------------------------------------------------- shock: power winners
    slides["4_vertiv.png"] = slide_shock(
        "04 · SHOCK · THE YEAR'S BIGGEST AI WINNERS AREN'T CHIPS",
        "+136%", "VRT (VERTIV) · PAST-YEAR RETURN, NOT A PREDICTION",
        "Vertiv — datacenter power &amp; cooling — is up <span style='color:#E0A23B'>136%</span> over the past year.",
        "Power-layer names are quietly among 2026's best-performing AI stocks. Past-year return — factual, backward-looking, not a forecast.",
        stat_size=190, accent="#E0A23B",
        chips=[("NVT", "+111%"), ("GEV", "+87% ($1,078)"), ("TRGP", "+65%"), ("PWR", "+58%"), ("PH", "+33%")],
        proof_img=imgs["energy_screener"], proof_h=330)

    # 5 --------------------------------------------------------- nuclear comeback
    slides["5_nuclear.png"] = slide_names(
        "05 · THE NUCLEAR COMEBACK",
        "Datacenters are reviving <span style='color:#7FE9C2'>nuclear power</span> — and uranium with it.",
        [("UUUU", "+31%"), ("BWXT", "+20%"), ("UEC", "+18%"), ("D", "+20%"), ("PWR", "+58%"), ("GEV", "+87%")],
        "Uranium (UUUU, UEC), nuclear-services (BWXT), utilities (D), and the grid buildout behind them (PWR, GEV) — all past-year returns, none a prediction.",
        head_size=54, sub_size=32)

    # 6 --------------------------------------------------------- who powers whom
    slides["6_whopowerswhom.png"] = slide_shock(
        "06 · WHO POWERS WHOM",
        "5+1+3.5", "GW · ANTHROPIC'S OWN COMMITMENTS — AMAZON, GOOGLE, BROADCOM",
        "One AI lab. Three separate multi-gigawatt power deals.",
        "Anthropic alone: 5 GW with Amazon ($100B, reported), 1 GW with Google ($200B, reported), 3.5 GW of next-gen TPU compute through Broadcom (SEC-filed) — plus 300 MW with SpaceX. Mapped below.",
        stat_size=110, accent="#E0A23B", head_size=44,
        proof_img=imgs["energy_map_gw"], proof_h=380, proof_pos="left top")

    # 7 -------------------------------------------------------------- the tool
    slides["7_tool.png"] = slide_tool(
        "07 · THE TOOL",
        "We map the whole <span style='color:#34D399'>power layer</span> of the AI stack.",
        "Every energy name, its price and past-year performance, and every gigawatt commitment we can source — who supplies the power, who's exposed if it doesn't show up.",
        imgs["energy_screener"], proof_h=340, sub_size=36,
        note="SYMBOL · LAYER · PRICE · 1Y RETURN — live columns from the tool, energy layer grouped.")

    # 8 -------------------------------------------------------------------- CTA
    slides["8_cta.png"] = slide_cta(imgs["energy_layers_banner"])

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

    caption = """AI doesn't run on chips. It runs on electricity. ⚡\U0001f440

Everyone's buying Nvidia. Almost nobody's asking who powers the datacenter it sits in.

Here's the reframe: AI compute is now measured in GIGAWATTS — the same unit you'd use for a power plant. OpenAI and NVIDIA's partnership targets deploying AT LEAST 10 GW of NVIDIA systems (reported), with NVIDIA investing up to $100B as each gigawatt goes live. Anthropic alone has separately committed to 5 GW with Amazon ($100B, reported), 1 GW with Google ($200B, reported), 3.5 GW of next-gen TPU compute through Broadcom (SEC-filed), and 300 MW with SpaceX.

Let's make that visceral: 1 gigawatt is roughly one full-size nuclear reactor — enough continuous power for roughly 800,000 U.S. homes. 10 GW, one company's AI buildout, is roughly TEN reactors' worth of electricity.

So who actually supplies all that power? We track the whole AI stack by layer, and here's the part that surprised us: ENERGY is the single biggest layer — 34 companies, more than chips (30), infra (23), or application (21).

And several of them are quietly among 2026's best-performing AI-adjacent stocks:
\U0001f50c Vertiv (datacenter power/cooling): +136% past year
⚡ nVent (electrical infrastructure): +111%
\U0001f50b GE Vernova (power equipment): +87%, now a $1,078 stock
\U0001f6e2️ Targa Resources (pipelines): +65%
\U0001f527 Quanta Services (grid buildout): +58%

Datacenters are even reviving nuclear power: Centrus (UUUU) +31%, BWX Technologies +20%, Uranium Energy Corp +18% — all past-year returns, none of this a prediction.

We map every gigawatt commitment we can source, every energy name, priced and dated — free.

⚠️ Gigawatt figures are company-reported or SEC-filed, not independently audited — labeled reported/filed throughout, and none of this is a promise those commitments will be fulfilled on schedule. 1-year returns are historical and backward-looking; past performance does not predict future results. Nothing here is a recommendation to buy or sell any security. Educational research only — not financial advice.

Comment "POWER" and I'll DM you the link \U0001f4f2

#AIstocks #energy #nuclear #datacenters #powergrid #stockmarket #investing #Vertiv #GEVernova #uranium #stocktok #fintok #financetok #investing101 #electricgrid #uraniumstocks #wallstreet #dueDiligence
"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")

    manifest = {
        "kind": "energy_showcase_carousel",
        "product": "AI Stack Terminal",
        "source_url": "https://highreturnethicalscreen.vercel.app/ (home + /screener + /map)",
        "date": DATE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_source": "web/public/data/site.json 'layers', 'stocks[*].performance.perf_1y', and 'capital_web.edges' (generated 2026-07-22T09:47:01Z) + live /screener and /map page captures (2026-07-23)",
        "aspect": "4:5 (2160x2700) — Instagram carousel",
        "slides": list(slides.keys()),
        "standalone": True,
        "hard_rails": [
            "Gigawatt commitments are company-reported or SEC-filed figures, labeled 'reported'/'filed' per capital_web.edges[].certainty -- never asserted as independently audited fact.",
            "1-year returns (performance.perf_1y) are backward-looking, factual, past performance -- labeled 'past-year return, not a prediction' -- never a forecast or buy signal.",
            "No recommendation to buy or sell any security; no price targets.",
            "No news outlet named anywhere in slides, caption, or this file.",
        ],
        "figures_used": {
            "layer_counts": {"L0-energy": 34, "L1-chips": 30, "L2-infra": 23, "L3-models": 0, "L4-application": 21},
            "gigawatt_commitments": {
                "openai->NVDA": {"power_gw": 10, "certainty": "reported", "note": "at least 10 GW of NVIDIA systems; NVIDIA to invest up to $100B as each GW deploys"},
                "anthropic->AMZN": {"power_gw": 5, "usd": 100000000000, "duration": "~decade", "certainty": "reported"},
                "anthropic->GOOGL": {"power_gw": 1, "usd": 200000000000, "tpus": 1000000, "certainty": "reported"},
                "anthropic->AVGO": {"power_gw": 3.5, "online_year": 2027, "certainty": "filed", "source": "SEC 8-K d87999d8k.htm"},
                "anthropic->spacex": {"power_mw": 300, "usd_per_month": 1250000000, "until": "2029-05", "certainty": "reported"},
            },
            "perf_1y": {
                "VRT": 135.7, "NVT": 111.3, "GEV": 87.2, "TRGP": 64.6, "PWR": 58.3, "PH": 32.5,
                "UUUU": 30.7, "WMB": 24.4, "AEP": 21.2, "BWXT": 20.5, "D": 20.1, "UEC": 18.5,
            },
            "gev_price": 1078.81,
        },
        "screenshot_source": "live captures of highreturnethicalscreen.vercel.app (home, /screener, /map) via Playwright/Chromium automation, 2026-07-23; live 1Y/1Y% figures drift slightly from the 2026-07-22 site.json snapshot used for slide copy (same caveat as _build_value_carousel.py) -- screenshots are proof-of-tool, not the numeric source of truth for the copy.",
        "posting_instructions": "Post as an Instagram carousel (not a reel). CTA slide asks viewers to comment \"POWER\" for a DM'd link (not link-in-bio).",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"DONE slides={len(slides)} -> {OUT}")


if __name__ == "__main__":
    build()
