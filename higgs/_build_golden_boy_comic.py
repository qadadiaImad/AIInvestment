"""'THE GOLDEN BOY' — a market tragedy, as a 6-page comic (each page a 2x2 grid
of 4 panels) + a title cover. Dramatic hype-then-fall arc opening on an
OVERVALUED darling (AMD, ~2x a fundamental-value model), the ignored cheap ones
(NVDA 1.9x under, Adobe 2.3x under) revealed at the payoff.

Comic art is generated on the local GPU (ComfyUI + Eldritch Comics SDXL LoRA)
in higgs/comic/art/ (cast) and higgs/comic/art2/ (scenes); THIS builder does the
panel layout, gutters, speech bubbles and captions (SDXL can't letter cleanly).
Renders 1080x1350 @2 pages to higgs/comic_gb/page_<n>.png + caption.txt.

Rails: a model's read, not a call · satire · educational — not financial advice.

    python higgs/_build_golden_boy_comic.py
"""
from __future__ import annotations
import base64, pathlib

HIGGS = pathlib.Path(__file__).resolve().parent
ART = HIGGS / "comic" / "art"
ART2 = HIGGS / "comic" / "art2"
OUT = HIGGS / "comic_gb"
W, H = 1080, 1350
M, G = 26, 16  # outer margin, gutter
PW = (W - 2 * M - G) // 2      # panel width
PH = (H - 2 * M - G) // 2      # panel height

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@700&family=JetBrains+Mono:wght@800&display=swap');"


def src(key):
    p = ART2 / f"{key}.png"
    if not p.exists():
        p = ART / f"{key}.png"
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.page{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:'Comic Neue'}}
.panel{{position:absolute;width:{PW}px;height:{PH}px;overflow:hidden;border:6px solid #0A0D12;border-radius:4px;box-shadow:0 0 0 4px #F4D03F}}
.art{{position:absolute;inset:-6%;background-size:cover}}
.grad{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.15),transparent 30%,transparent 62%,rgba(10,13,18,.35))}}
.narr{{position:absolute;left:14px;right:14px;top:12px;background:#F4D03F;border:4px solid #0A0D12;border-radius:6px;
  padding:11px 14px;font-family:'Comic Neue';font-weight:700;font-size:26px;line-height:1.08;color:#0A0D12;box-shadow:4px 4px 0 rgba(0,0,0,.5)}}
.bub{{position:absolute;background:#fff;border:4px solid #0A0D12;border-radius:22px;padding:12px 16px;max-width:74%;
  font-family:'Comic Neue';font-weight:700;font-size:27px;line-height:1.05;color:#0A0D12;box-shadow:4px 4px 0 rgba(0,0,0,.4)}}
.bub b{{color:#C0392B}}
.bub:after{{content:'';position:absolute;bottom:-22px;left:30px;border-width:22px 16px 0 0;border-style:solid;border-color:#0A0D12 transparent transparent transparent}}
.sfx{{position:absolute;font-family:'Bangers';letter-spacing:1px;color:#F4D03F;-webkit-text-stroke:4px #0A0D12;paint-order:stroke fill;
  font-size:74px;line-height:.9;transform:rotate(-8deg);text-shadow:5px 5px 0 rgba(0,0,0,.35)}}
.big{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:20px;
  font-family:'Bangers';color:#fff;-webkit-text-stroke:3px #0A0D12;paint-order:stroke fill;font-size:66px;line-height:1.02;letter-spacing:1px}}
.big .g{{color:#F4D03F}} .big .r{{color:#E0524D}} .big .m{{color:#7FE9C2}}
.moralw{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:30px}}
.moral{{font-family:'Comic Neue';font-weight:700;font-size:48px;line-height:1.25;color:#fff}}
.moral .r{{color:#E0524D}} .moral .m{{color:#7FE9C2}}
.cover-t{{font-family:'Bangers';color:#F4D03F;-webkit-text-stroke:7px #0A0D12;paint-order:stroke fill;font-size:150px;line-height:.92;letter-spacing:2px;text-shadow:9px 9px 0 rgba(0,0,0,.4)}}
.kick{{font-family:'JetBrains Mono';font-weight:800;font-size:26px;letter-spacing:4px;color:#F4D03F;text-shadow:0 2px 10px #000}}
.pill{{font-family:'JetBrains Mono';font-weight:800;font-size:30px;letter-spacing:2px;color:#0A0D12;background:#7FE9C2;padding:14px 24px;border-radius:12px;display:inline-block}}
.rail{{font-family:'JetBrains Mono';font-size:16px;color:#cbd3dd;text-align:center;line-height:1.4}}
.swipe{{position:absolute;right:54px;bottom:48px;font-family:'Bangers';font-size:56px;color:#7FE9C2;-webkit-text-stroke:3px #0A0D12;paint-order:stroke fill}}
"""

# quadrant offsets
Q = [(M, M), (M + PW + G, M), (M, M + PH + G), (M + PW + G, M + PH + G)]


def panel(cfg):
    """cfg: dict(art, focus?, narr?, bubbles?[ (text,left%,top%) ], sfx?( text,left%,top% ), big?)"""
    inner = ""
    if cfg.get("art"):
        foc = cfg.get("focus", "center 28%")
        inner += f"<div class='art' style=\"background-image:url('{src(cfg['art'])}');background-position:{foc}\"></div><div class='grad'></div>"
    if cfg.get("big"):
        inner += f"<div class='big'>{cfg['big']}</div>"
    if cfg.get("moral"):
        inner += f"<div class='moralw'><div class='moral'>{cfg['moral']}</div></div>"
    if cfg.get("narr"):
        inner += f"<div class='narr'>{cfg['narr']}</div>"
    for b in cfg.get("bubbles", []):
        t, lx, ty = b
        inner += f"<div class='bub' style='left:{lx}%;top:{ty}%'>{t}</div>"
    if cfg.get("sfx"):
        t, lx, ty = cfg["sfx"]
        inner += f"<div class='sfx' style='left:{lx}%;top:{ty}%'>{t}</div>"
    return inner


def page2x2(panels):
    body = ""
    for i, cfg in enumerate(panels):
        x, y = Q[i]
        body += f"<div class='panel' style='left:{x}px;top:{y}px'>{panel(cfg)}</div>"
    return f"<div class='page'>{body}</div>"


def raw(inner):
    return f"<div class='page'>{inner}</div>"


def html(inner):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body>{inner}</body></html>"


# --------------------------------------------------------------------- script
def pages():
    P = []
    # 0 — COVER
    P.append(raw(
        f"<div class='panel' style='left:{M}px;top:{M}px;width:{W-2*M}px;height:{H-2*M}px'>"
        f"<div class='art' style=\"background-image:url('{src('crown_pedestal')}');background-position:center 40%\"></div>"
        "<div class='grad'></div>"
        "<div style='position:absolute;left:50px;top:80px;right:50px'>"
        "<div class='kick'>AI STACK · TERMINAL PRESENTS</div>"
        "<div class='cover-t' style='margin-top:14px'>THE<br>GOLDEN<br>BOY</div>"
        "<div style=\"font-family:'Comic Neue';font-weight:700;font-size:40px;color:#fff;margin-top:20px;text-shadow:0 3px 12px #000\">a market tragedy · in 6 acts</div>"
        "</div><div class='swipe'>SWIPE →</div></div>"))
    # 1 — CORONATION (hype the overvalued)
    P.append(page2x2([
        dict(art="mrmarket_bell", narr="9:30 AM. Mr. Market rings the bell…", bubbles=[("Behold — the FUTURE of chips!", 20, 55)]),
        dict(art="amd_pedestal", narr="…and crowns his Golden Boy.", sfx=("ALL HAIL AMD!", 6, 66)),
        dict(art="crowd_cheer", bubbles=[("BUY! BUY! BUY!", 22, 20)], narr="The crowd went wild."),
        dict(art="rocket_sage", focus="center 40%", sfx=("TO THE MOON!", 6, 6), narr="…while an old sage quietly opened his ledger."),
    ]))
    # 2 — HUBRIS
    P.append(page2x2([
        dict(art="amd_hero", focus="center 22%", bubbles=[("I'm UNSTOPPABLE!", 16, 20)]),
        dict(art="mrmarket_hubris", focus="center 24%", narr="Mr. Market pumped him higher…", bubbles=[("HIGHER! HIGHER!", 20, 60)]),
        dict(art="crowd_cheer", narr="Nobody asked what he was WORTH."),
        dict(art="amd_pedestal", focus="center 20%", sfx=("$476!!", 30, 12), narr="The price just… soared."),
    ]))
    # 3 — THE LEDGER (turn)
    P.append(page2x2([
        dict(art="oracle_ledger", narr="Then the sage cleared his throat.", bubbles=[("Before you cheer… check the BOOKS.", 16, 60)]),
        dict(art="oracle_ledger", focus="center 45%", narr="Price paid: $476. A model's value: $246."),
        dict(big="= <span class='r'>2×</span><br>OVER-<br>VALUED"),
        dict(art="crowd_cheer", bubbles=[("Wait… <b>WHAT?!</b>", 20, 24)], narr="The cheering stopped."),
    ]))
    # 4 — THE FALL (climax)
    P.append(page2x2([
        dict(art="amd_crack", bubbles=[("N-no… I'm the KING!", 12, 18)]),
        dict(art="rocket_red", focus="center 55%", sfx=("SP-SPUTTER…", 6, 40)),
        dict(art="amd_fall", sfx=("CRASH!", 26, 20)),
        dict(art="crowd_panic", bubbles=[("SELL!! SELL!!", 22, 20)]),
    ]))
    # 5 — THE OVERLOOKED (payoff)
    P.append(page2x2([
        dict(art="nvda_shadow", narr="Meanwhile, in the shadows…", bubbles=[("The 'bubble' they mocked…", 12, 60)]),
        dict(art="NVDA", focus="center 18%", sfx=("1.9× CHEAP", 8, 12), narr="…was 1.9× UNDER."),
        dict(art="ADBE", focus="center 20%", narr="And the artist nobody watched? 2.3× under."),
        dict(art="oracle_ledger", focus="center 30%", bubbles=[("Value was here all along.", 14, 22)]),
    ]))
    # 6 — MORAL + CTA
    P.append(page2x2([
        dict(art="mrmarket_shrug", bubbles=[("Eh — I'll crown a NEW king tomorrow!", 12, 18)]),
        dict(art="crown_pedestal", focus="center 45%", narr="The crown never stays."),
        dict(moral="The crowd crowns<br>the <span class='r'>STORY.</span><br><br>Value crowns<br>the <span class='m'>BUSINESS.</span>"),
        dict(big="<div style='font-family:Comic Neue;font-weight:700;-webkit-text-stroke:0;color:#fff;font-size:34px;line-height:1.3'>"
                 "<span class='pill'>💬 COMMENT \"VALUE\"</span><br><br>"
                 "<span style='color:#7FE9C2;font-size:30px'>↳ for the full over/under list</span><br><br>"
                 "<span class='rail'>A model's read, not a call · satire · educational — not financial advice.</span></div>"),
    ]))
    return P


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for n, inner in enumerate(pages()):
            pg.set_content(html(inner), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / f"page_{n}.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered page", n)
        b.close()

    caption = """THE GOLDEN BOY 👑💥 a market tragedy in 6 acts 🧵

Act I — the market crowns its darling and the crowd screams BUY.
Act II — hubris: nobody asks what he's worth.
Act III — the sage opens the ledger: paid $476… a model says $246. That's ~2× OVERVALUED.
Act IV — the fall.
Act V — the twist: the "bubble" everyone mocked was ~1.9× CHEAP, and the artist nobody watched ~2.3× under.
Act VI — the moral: the crowd crowns the STORY; value crowns the BUSINESS.

Comment "VALUE" for the full over/under list on the AI-stack names 📲

⚠️ Satire. Figures are a fundamental-value model's estimates — a read, not a call. Not price targets, not predictions, not financial advice.

#valueinvesting #stockmarket #aistocks #satire #comic #amd #nvidia #fundamentalanalysis #fintok #investingtips"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    print("DONE ->", OUT)


if __name__ == "__main__":
    build()
