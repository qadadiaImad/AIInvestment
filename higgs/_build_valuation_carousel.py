"""Standalone IG carousel: "OVER or UNDER? — Wall Street's valuation illusions"
Built from FRESH web/public/data (fair values retrieved 2026-08-03) + hero art
generated on the LOCAL GPU (ComfyUI, higgs/post_0803/heroA|B.png) — the new
local pipeline, no Grok. 5 slides, 1080x1350 @2 -> 2160x2700.

Rails: a fundamental-value model's read, not a call · not the vendor by name ·
past performance not a prediction · educational, not financial advice.

    python higgs/_build_valuation_carousel.py
"""
from __future__ import annotations
import base64, pathlib
HIGGS = pathlib.Path(__file__).resolve().parent
POST = HIGGS / "post_0803"
OUT = HIGGS / "valuation_carousel_2026-08-03"
W, H = 1080, 1350
FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,900&family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@700;800&display=swap');"
GREEN, GOLD, MINT = "#34D399", "#E0A23B", "#7FE9C2"
RAIL = "A fundamental-value model's read, not a call · figures as of 2026-08-03 · educational — not financial advice."


def b64(p):
    return "data:image/png;base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()


BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.s{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:-30px;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:70px 68px;display:flex;flex-direction:column;z-index:2}}
.brand{{font-family:'JetBrains Mono';font-weight:800;font-size:24px;letter-spacing:1px;text-shadow:0 2px 12px #000}}
.brand .g{{color:{GREEN}}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:3px;color:#8893A4;text-shadow:0 2px 12px #000}}
.big{{font-family:'JetBrains Mono';font-weight:800;line-height:.9;letter-spacing:-2px;text-shadow:0 6px 40px rgba(0,0,0,.7)}}
.h{{font-family:Fraunces;font-weight:700;line-height:1.08;color:#fff;text-shadow:0 3px 20px rgba(0,0,0,.7)}}
.sub{{font-family:Inter;font-size:37px;line-height:1.4;color:#C4CDD9;text-shadow:0 2px 14px rgba(0,0,0,.8)}}
.rail{{font-family:'JetBrains Mono';font-size:16px;color:#96A0AF;letter-spacing:.3px;line-height:1.5;margin-top:auto;padding-top:16px;text-shadow:0 1px 10px #000}}
.pill{{font-family:'JetBrains Mono';font-weight:700;font-size:24px;letter-spacing:2px;color:#0A0D12;background:{MINT};padding:16px 28px;border-radius:14px;display:inline-block}}
.tag{{font-family:'JetBrains Mono';font-weight:800;font-size:26px;letter-spacing:2px;padding:10px 20px;border-radius:12px;display:inline-block}}
"""


def page(inner, hero=None, scrim="linear-gradient(180deg,rgba(10,13,18,.5) 0%,rgba(10,13,18,.35) 35%,rgba(10,13,18,.82) 72%,rgba(10,13,18,.97) 100%)"):
    bg = f"<div class='hero' style=\"background-image:url('{b64(hero)}')\"></div><div class='scrim' style='background:{scrim}'></div>" if hero else ""
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='s'>{bg}<div class='pad'>{inner}</div></div></body></html>"


def brand():
    return "<div class='brand'>AI<span class='g'>STACK</span> · TERMINAL</div>"


def stat_slide(kick, ticker, name, mult, verdict, price, model, hook):
    color = GREEN if verdict == "UNDER" else GOLD
    return page(
        brand() +
        f"<div class='kick' style='margin-top:40px'>{kick}</div>"
        f"<div class='big' style='margin-top:14px;font-size:250px;color:{color}'>{mult}</div>"
        f"<div class='tag' style='color:#0A0D12;background:{color};margin-top:6px'>{verdict}VALUED</div>"
        f"<div class='h' style='margin-top:28px;font-size:52px'>{name}</div>"
        f"<div class='sub' style='margin-top:14px;max-width:940px'>{hook} <span style='color:{color};font-weight:700'>${price}</span> vs a model's <span style='color:{color};font-weight:700'>${model}</span>.</div>"
        f"<div class='rail'>{RAIL}</div>")


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    slides = {}
    # 0 cover
    slides["0_cover.png"] = page(
        brand() +
        "<div class='kick' style='margin-top:40px'>TODAY'S VALUE SCREEN · 2026-08-03</div>"
        f"<div class='h' style='margin-top:22px;font-size:96px'>Over or <span style='color:{GOLD}'>under</span>valued?</div>"
        f"<div class='sub' style='margin-top:22px;max-width:900px;font-size:44px'>I ran every AI-stack price against a fundamental-value model. Some answers flip what everyone \"knows.\" \U0001f440</div>"
        "<div style='margin-top:auto'><div class='pill'>SWIPE →</div></div>"
        f"<div class='rail'>{RAIL}</div>", hero=str(POST / "heroA.png"))
    # 1 NVDA under
    slides["1_nvda.png"] = stat_slide("01 · THE 'BUBBLE'", "NVDA", "Nvidia", "1.8x", "UNDER", "207", "374",
        "Everyone screams 'AI bubble' — a model says the business is worth nearly 2× the price:")
    # 2 INTC over
    slides["2_intc.png"] = stat_slide("02 · THE COMEBACK", "INTC", "Intel", "2.9x", "OVER", "90", "31",
        "The turnaround everyone's buying back — still priced near 3× a model's value:")
    # 3 ADBE under
    slides["3_adbe.png"] = stat_slide("03 · 'AI WILL KILL IT'", "ADBE", "Adobe", "2.3x", "UNDER", "254", "587",
        "The stock the market left for dead — a model says worth ~2.3× the price:")
    # 4 CTA
    slides["4_cta.png"] = page(
        brand() +
        "<div class='kick' style='margin-top:40px'>THE FULL OVER/UNDER LIST</div>"
        f"<div class='h' style='margin-top:16px;font-size:64px'>Which of your AI names<br>is secretly cheap?</div>"
        f"<div class='sub' style='margin-top:18px;max-width:940px;font-size:42px'>NVDA, Adobe, Duolingo, ServiceNow, Meta all screen <span style='color:{GREEN};font-weight:700'>undervalued</span> today — while Intel, AMD, Google screen <span style='color:{GOLD};font-weight:700'>rich</span>.</div>"
        "<div style='margin-top:34px'><div class='pill'>\U0001f4ac COMMENT \"VALUE\"</div></div>"
        f"<div style='font-family:JetBrains Mono;font-weight:600;font-size:19px;color:{MINT};margin-top:16px'>→ and I'll DM you the full list</div>"
        f"<div class='rail'>{RAIL}</div>", hero=str(POST / "heroB.png"))

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for name, html in slides.items():
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered", name)
        b.close()

    caption = """Over or undervalued? I ran the AI-stack against a fundamental-value model. \U0001f440\U0001f4c8

The market's most-hated names keep screening CHEAP, and its darlings keep screening rich:
\U0001f7e2 Nvidia — the 'AI bubble' everyone fears is ~1.8× UNDER a model's value
\U0001f7e2 Adobe — 'AI will kill it' … model says worth ~2.3× the price
\U0001f7e2 Duolingo, ServiceNow, Meta — all screening undervalued today
\U0001f7e1 Intel — the comeback everyone's buying is still ~3× a model's worth
\U0001f7e1 AMD, Google — screening rich

The crowd prices the story. Value prices the business.

Comment "VALUE" and I'll DM you the full over/under list \U0001f4f2

⚠️ A fundamental-value model's estimates — a read, not a call. Not price targets, not predictions, not financial advice. Figures as of 2026-08-03.

#valueinvesting #stockmarket #aistocks #nvidia #intel #fundamentalanalysis #investing #fintok"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    print("DONE ->", OUT)


if __name__ == "__main__":
    build()
