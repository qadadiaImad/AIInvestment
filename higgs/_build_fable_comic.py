"""'THE ANT & THE GRASSHOPPER' (villain-ant cut) — a 7-slide comic carousel
(title cover + 6 one-panel slides). Public-domain Aesop fable, retold in
original wording; bold comic-book art generated locally (ComfyUI + Eldritch
Comics LoRA + IPAdapter for consistent characters) in higgs/fable/art/. This
builder does the panel framing, speech bubbles and captions.

Not tied to the finance theme — a standalone creative piece. Renders
1080x1350 @2 to higgs/fable/slide_<n>.png + caption.txt.

    python higgs/_build_fable_comic.py
"""
from __future__ import annotations
import base64, pathlib

HIGGS = pathlib.Path(__file__).resolve().parent
ART = HIGGS / "fable" / "art"
OUT = HIGGS / "fable"
W, H = 1080, 1350

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@700&family=JetBrains+Mono:wght@800&display=swap');"


def b64(name):
    return "data:image/png;base64," + base64.b64encode((ART / f"{name}.png").read_bytes()).decode()


BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:'Comic Neue'}}
.frame{{position:absolute;inset:26px;border:9px solid #0A0D12;border-radius:6px;overflow:hidden;box-shadow:0 0 0 6px #F4D03F}}
.art{{position:absolute;inset:-30px;background-size:cover;background-position:center 32%}}
.grad{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.15),transparent 30%,transparent 60%,rgba(10,13,18,.4))}}
.narr{{position:absolute;left:46px;right:46px;top:46px;background:#F4D03F;border:5px solid #0A0D12;border-radius:8px;
  padding:20px 26px;font-family:'Comic Neue';font-weight:700;font-size:40px;line-height:1.14;color:#0A0D12;box-shadow:6px 6px 0 rgba(0,0,0,.5)}}
.bub{{position:absolute;background:#fff;border:5px solid #0A0D12;border-radius:34px;padding:22px 30px;max-width:70%;
  font-family:'Comic Neue';font-weight:700;font-size:44px;line-height:1.08;color:#0A0D12;box-shadow:6px 6px 0 rgba(0,0,0,.45)}}
.bub b{{color:#C0392B}}
.bub:after{{content:'';position:absolute;bottom:-32px;left:52px;border-width:32px 24px 0 0;border-style:solid;border-color:#0A0D12 transparent transparent transparent}}
.sfx{{position:absolute;font-family:'Bangers';letter-spacing:2px;color:#F4D03F;-webkit-text-stroke:6px #0A0D12;paint-order:stroke fill;
  font-size:120px;line-height:.9;transform:rotate(-8deg);text-shadow:8px 8px 0 rgba(0,0,0,.35)}}
.title{{font-family:'Bangers';color:#F4D03F;-webkit-text-stroke:8px #0A0D12;paint-order:stroke fill;font-size:118px;line-height:.95;letter-spacing:2px;text-shadow:9px 9px 0 rgba(0,0,0,.4)}}
.kick{{font-family:'JetBrains Mono';font-weight:800;font-size:26px;letter-spacing:4px;color:#F4D03F;text-shadow:0 2px 10px #000}}
.moral{{position:absolute;left:46px;right:46px;bottom:46px;background:#0A0D12;border:5px solid #F4D03F;border-radius:10px;
  padding:20px 26px;font-family:'Comic Neue';font-weight:700;font-size:38px;line-height:1.15;color:#fff;text-align:center}}
.swipe{{position:absolute;right:56px;bottom:52px;font-family:'Bangers';font-size:58px;color:#7FE9C2;-webkit-text-stroke:3px #0A0D12;paint-order:stroke fill}}
"""


def page(inner):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{inner}</div></body></html>"


def frame(name, focus="center 32%"):
    return f"<div class='frame'><div class='art' style=\"background-image:url('{b64(name)}');background-position:{focus}\"></div><div class='grad'></div>"


def slides():
    S = []
    # 0 cover
    S.append(page(frame("p1_gh_summer", "center 30%") +
        "<div style='position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.5),rgba(10,13,18,.15) 40%,rgba(10,13,18,.8))'></div>"
        "<div style='position:absolute;left:56px;top:110px;right:56px'>"
        "<div class='kick'>AN AESOP FABLE · RETOLD</div>"
        "<div class='title' style='margin-top:16px'>THE ANT &<br>THE<br>GRASSHOPPER</div></div>"
        "<div class='swipe'>SWIPE →</div></div>"))
    # 1
    S.append(page(frame("p1_gh_summer") +
        "<div class='narr'>One golden summer, the Grasshopper played…</div>"
        "<div class='bub' style='left:120px;top:820px'>Ahh — <b>summer forever!</b></div></div>"))
    # 2
    S.append(page(frame("p2_ant_haul", "center 30%") +
        "<div class='narr'>…while the Ant worked without rest.</div>"
        "<div class='bub' style='left:120px;top:840px'>Winter's coming. <b>Store now.</b></div></div>"))
    # 3
    S.append(page(frame("p3_gh_dance") +
        "<div class='narr'>The Grasshopper only laughed.</div>"
        "<div class='bub' style='left:110px;top:470px'>Work, work, work! Come <b>DANCE!</b></div></div>"))
    # 4
    S.append(page(frame("p4_winter", "center 45%") +
        "<div class='narr'>Then winter came. And it did not forgive.</div>"
        "<div class='sfx' style='left:120px;top:520px'>HOWWWL…</div></div>"))
    # 5
    S.append(page(frame("p5_gh_beg", "center 34%") +
        "<div class='narr'>Starving, the Grasshopper crawled to the Ant's door.</div>"
        "<div class='bub' style='left:120px;top:840px'>P-please… just a <b>crumb?</b></div></div>"))
    # 6 — villain reveal + moral
    S.append(page(frame("p6_ant_evil", "center 30%") +
        "<div class='bub' style='left:90px;top:250px;max-width:78%'>You laughed while I slaved, fiddler. Now <b>DANCE IN THE FROST!</b></div>"
        "<div class='sfx' style='left:520px;top:640px;color:#E0524D;-webkit-text-stroke-color:#0A0D12'>SLAM!</div>"
        "<div class='moral'>Cross the wrong ant… and <span style='color:#F4D03F'>winter never ends.</span></div></div>"))
    return S


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for n, html in enumerate(slides()):
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / f"slide_{n}.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered slide", n)
        b.close()

    caption = """THE ANT & THE GRASSHOPPER 🐜🎻❄️ (the villain-ant cut)

All summer the grasshopper fiddled and danced while the ant hauled grain and warned: winter's coming.
The grasshopper laughed.
Then the snow fell… and when he came begging at the ant's door, he learned the ant remembers EVERYTHING. 😈

Moral: cross the wrong ant, and winter never ends.

An Aesop fable, retold. Made 100% on a local GPU — comic art via ComfyUI + IPAdapter for consistent characters.

#comic #aesopfables #webcomic #comicart #aiart #comfyui #storytime #fable #shortcomic"""
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    print("DONE ->", OUT)


if __name__ == "__main__":
    build()
