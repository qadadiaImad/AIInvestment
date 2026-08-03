"""'MR. MARKET'S KINGDOM' — an 8-panel satirical market comic carousel.

Comic-book character art is generated on the local GPU (ComfyUI + Eldritch
Comics SDXL LoRA) into higgs/comic/art/<NAME>.png; THIS builder lays out each
panel with clean speech bubbles + narration boxes (SDXL can't render legible
text, so all lettering is composed here). Renders 1080x1350 @2 IG carousel
panels to higgs/comic/panel_<n>.png + caption.txt.

Satire ties to our real value-quiz data (price vs a fundamental-value model):
NVDA 1.9x UNDER · INTC ~3x OVER · AMD ~2x OVER · ADBE 2.3x UNDER. Rails:
a model's read, not a call · satire · educational — not financial advice.

    python higgs/_build_market_comic.py
"""
from __future__ import annotations
import base64, pathlib

HIGGS = pathlib.Path(__file__).resolve().parent
ART = HIGGS / "comic" / "art"
OUT = HIGGS / "comic"
W, H = 1080, 1350

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@700&family=JetBrains+Mono:wght@700;800&display=swap');"


def b64(name):
    return "data:image/png;base64," + base64.b64encode((ART / f"{name}.png").read_bytes()).decode()


BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:'Comic Neue'}}
.frame{{position:absolute;inset:26px;border:10px solid #0A0D12;border-radius:6px;overflow:hidden;box-shadow:0 0 0 6px #F4D03F}}
.art{{position:absolute;inset:-20px;background-size:cover;background-position:center 30%}}
.tone{{position:absolute;inset:0;background:radial-gradient(circle, transparent 60%, rgba(10,13,18,.35) 100%)}}
.narr{{position:absolute;left:44px;right:44px;top:44px;background:#F4D03F;border:5px solid #0A0D12;border-radius:8px;
  padding:20px 26px;font-family:'Comic Neue';font-weight:700;font-size:40px;line-height:1.15;color:#0A0D12;box-shadow:6px 6px 0 rgba(0,0,0,.5)}}
.bubble{{position:absolute;background:#fff;border:5px solid #0A0D12;border-radius:34px;padding:22px 30px;max-width:640px;
  font-family:'Comic Neue';font-weight:700;font-size:42px;line-height:1.12;color:#0A0D12;box-shadow:6px 6px 0 rgba(0,0,0,.45)}}
.bubble:after{{content:'';position:absolute;bottom:-34px;left:60px;border-width:34px 26px 0 0;border-style:solid;border-color:#0A0D12 transparent transparent transparent}}
.bubble b{{color:#C0392B}}
.sfx{{position:absolute;font-family:'Bangers';letter-spacing:2px;color:#F4D03F;-webkit-text-stroke:6px #0A0D12;
  paint-order:stroke fill;font-size:130px;line-height:.9;transform:rotate(-8deg);text-shadow:8px 8px 0 rgba(0,0,0,.35)}}
.title{{font-family:'Bangers';color:#F4D03F;-webkit-text-stroke:8px #0A0D12;paint-order:stroke fill;
  font-size:150px;line-height:.92;letter-spacing:2px;text-shadow:10px 10px 0 rgba(0,0,0,.4)}}
.kick{{font-family:'JetBrains Mono';font-weight:800;font-size:26px;letter-spacing:4px;color:#F4D03F;text-shadow:0 2px 10px #000}}
.moral{{font-family:'Bangers';color:#fff;-webkit-text-stroke:3px #0A0D12;paint-order:stroke fill;font-size:96px;line-height:1.0;letter-spacing:1px}}
.moral .g{{color:#F4D03F}} .moral .r{{color:#E0524D}}
.pill{{font-family:'JetBrains Mono';font-weight:800;font-size:34px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:16px 30px;border-radius:14px;display:inline-block}}
.rail{{position:absolute;left:44px;right:44px;bottom:34px;font-family:'JetBrains Mono';font-size:18px;color:#cbd3dd;text-align:center;text-shadow:0 2px 8px #000}}
.swipe{{position:absolute;right:60px;bottom:52px;font-family:'Bangers';font-size:60px;color:#7FE9C2;-webkit-text-stroke:3px #0A0D12;paint-order:stroke fill}}
"""


def page(inner):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{inner}</div></body></html>"


def art_frame(name, focus="center 30%"):
    return f"<div class='frame'><div class='art' style=\"background-image:url('{b64(name)}');background-position:{focus}\"></div><div class='tone'></div></div>"


def narr(t):
    return f"<div class='narr'>{t}</div>"


def bubble(t, left, top, w=640):
    return f"<div class='bubble' style='left:{left}px;top:{top}px;max-width:{w}px'>{t}</div>"


def sfx(t, left, top, color="#F4D03F"):
    return f"<div class='sfx' style='left:{left}px;top:{top}px;color:{color}'>{t}</div>"


# --------------------------------------------------------------- the 8 panels
def build_panels():
    P = {}
    # 1 — cover
    P[1] = page(art_frame("THRONE", "center 40%") +
        "<div style='position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.55),rgba(10,13,18,.2) 40%,rgba(10,13,18,.85))'></div>"
        "<div style='position:absolute;left:60px;top:120px;right:60px'>"
        "<div class='kick'>AI&nbsp;STACK · TERMINAL PRESENTS</div>"
        "<div class='title' style='margin-top:16px'>MR. MARKET'S<br>KINGDOM</div>"
        "<div style=\"font-family:'Comic Neue';font-weight:700;font-size:44px;color:#fff;margin-top:24px;text-shadow:0 3px 12px #000\">a market fable · in 8 panels</div>"
        "</div><div class='swipe'>SWIPE →</div>")
    # 2 — coronation
    P[2] = page(art_frame("NVDA", "center 22%") +
        narr("Each year, Mr. Market crowns the most VALUABLE in the land…") +
        bubble("ALL HAIL <b>NVIDIA</b> — KING OF A.I.!", 90, 470, 560) +
        sfx("AI BUBBLE!!", 470, 980, "#7FE9C2"))
    # 3 — the twist
    P[3] = page(art_frame("NVDA", "center 26%") +
        narr("But the ledger whispered a secret the crowd never heard…") +
        bubble("Priced $200… a model says <b>$372</b>. The 'bubble' is <b>1.9× CHEAP.</b>", 100, 840, 700))
    # 4 — fallen king
    P[4] = page(art_frame("INTC", "center 24%") +
        narr("Intel strutted in gold that wasn't there…") +
        bubble("I'm STILL worth a FORTUNE!", 110, 470, 520) +
        bubble("The model says you're priced at <b>3× your worth</b>, old friend.", 300, 900, 660))
    # 5 — challenger
    P[5] = page(art_frame("AMD", "center 26%") +
        narr("AMD sprinted for the throne — and ran ahead of himself…") +
        bubble("I'll CATCH the King!", 110, 480, 460) +
        sfx("~2× OVER!", 520, 980, "#E0524D"))
    # 6 — ignored gem
    P[6] = page(art_frame("ADBE", "center 24%") +
        narr("In the corner, nobody watched the artist…") +
        bubble("…quietly worth <b>2.3× his price.</b>", 300, 900, 560))
    # 7 — mr market
    P[7] = page(art_frame("MRMARKET", "center 28%") +
        narr("And who set every price? A showman ruled by mood.") +
        bubble("PRICES?! I make 'em up by FEELING!", 120, 470, 620) +
        sfx("🎲", 780, 940))
    # 8 — moral + CTA
    P[8] = page(art_frame("THRONE", "center 45%") +
        "<div style='position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.5),rgba(10,13,18,.35) 40%,rgba(10,13,18,.92))'></div>"
        "<div style='position:absolute;left:56px;right:56px;top:150px'>"
        "<div class='moral'>The crowd prices the <span class='r'>STORY.</span><br>Value prices the <span class='g'>BUSINESS.</span></div>"
        "<div style='margin-top:60px'><span class='pill'>💬 COMMENT \"VALUE\"</span></div>"
        "<div style=\"font-family:'Comic Neue';font-weight:700;font-size:34px;color:#7FE9C2;margin-top:20px\">↳ and I'll DM the full over/under list</div>"
        "</div>"
        "<div class='rail'>A model's read, not a call · satire · figures vs a fundamental-value model · educational — not financial advice.</div>")
    return P


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    panels = build_panels()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for n, html in panels.items():
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / f"panel_{n}.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered panel", n)
        b.close()

    caption = """MR. MARKET'S KINGDOM 👑 a market fable in 8 panels 🧵

Every cycle, the crowd crowns a king and boos a "bubble" — but the ledger tells a funnier story:
🟢 The "A.I. bubble" everyone screams about? A fundamental-value model says it's ~1.9× CHEAP.
👑 The fallen giant strutting in gold? Priced near 3× the model's worth.
🏃 The challenger sprinting for the throne? ~2× ahead of himself.
🎨 The artist nobody watches? Quietly worth ~2.3× his price.

The moral: the crowd prices the STORY. Value prices the BUSINESS.

Comment "VALUE" and I'll DM the full over/under list 📲

⚠️ Satire. Figures are a fundamental-value model's estimates — a read, not a call. Not price targets, not predictions, not financial advice.

#valueinvesting #stockmarket #aistocks #satire #comic #fundamentalanalysis #investingtips #nvidia #intel #fintok"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    print("DONE ->", OUT)


if __name__ == "__main__":
    build()
