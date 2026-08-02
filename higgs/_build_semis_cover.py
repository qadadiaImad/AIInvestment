"""Reel cover for the semis "out of buyers" reel. 1080x1920 (@2 -> 2160x3840),
grid-legible: one bold Fraunces hook + two stat pills over the panic-floor
scene, AI STACK brand system (dark #0A0D12, gold #E0A23B, mint #7FE9C2).
Figures relayed AS REPORTED (rail). Writes higgs/semis_cover.png.

    python higgs/_build_semis_cover.py
"""
from __future__ import annotations
import base64, pathlib

HIGGS = pathlib.Path(__file__).resolve().parent
BG = HIGGS / "_semis_cover_bg.jpg"
OUT = HIGGS / "semis_cover.png"
W, H = 1080, 1920

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,900&family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@700;800&display=swap');"

bg_b64 = "data:image/jpeg;base64," + base64.b64encode(BG.read_bytes()).decode()

HTML = f"""<!doctype html><html><head><meta charset='utf-8'><style>
*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:-30px;background-image:url('{bg_b64}');background-size:cover;background-position:center 40%}}
.scrim{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.5) 0%,rgba(10,13,18,.32) 30%,rgba(10,13,18,.6) 60%,rgba(10,13,18,.97) 100%)}}
.pad{{position:absolute;inset:0;padding:96px 84px 88px;display:flex;flex-direction:column;z-index:2}}
.brand{{display:flex;align-items:baseline;gap:2px;font-family:'JetBrains Mono';font-weight:800;font-size:28px;letter-spacing:1px;text-shadow:0 2px 12px rgba(0,0,0,.8)}}
.brand .g{{color:#34D399}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:30px;letter-spacing:5px;color:#8893A4;margin-top:54px;text-shadow:0 2px 14px rgba(0,0,0,.8)}}
.hook{{font-family:Fraunces;font-weight:900;font-size:150px;line-height:.96;letter-spacing:-3px;color:#fff;margin-top:26px;text-shadow:0 4px 30px rgba(0,0,0,.7)}}
.hook .gold{{color:#E0A23B}}
.pills{{margin-top:auto;display:flex;flex-direction:column;gap:20px;align-items:flex-start}}
.pill{{font-family:'JetBrains Mono';font-weight:800;font-size:36px;letter-spacing:1px;padding:18px 30px;border-radius:16px;backdrop-filter:blur(3px)}}
.red{{color:#fff;background:rgba(224,82,77,.22);border:2px solid #E0524D}}
.red b{{color:#E0524D}}
.goldpill{{color:#fff;background:rgba(224,162,59,.16);border:2px solid #E0A23B}}
.goldb{{color:#E0A23B}}
.cue{{font-family:'JetBrains Mono';font-weight:800;font-size:40px;letter-spacing:1px;color:#7FE9C2;margin-top:34px;text-shadow:0 2px 16px rgba(0,0,0,.8)}}
.rail{{font-family:'JetBrains Mono';font-size:19px;letter-spacing:.4px;color:#8893A4;margin-top:22px;line-height:1.5;text-shadow:0 1px 10px rgba(0,0,0,.85)}}
</style></head><body><div class='slide'>
  <div class='hero'></div><div class='scrim'></div>
  <div class='pad'>
    <div class='brand'><span>AI</span><span class='g'>STACK</span><span>&nbsp;·&nbsp;TERMINAL</span></div>
    <div class='kick'>TODAY'S MARKET STORY</div>
    <div class='hook'>Semis are<br>running out<br>of <span class='gold'>buyers.</span></div>
    <div class='pills'>
      <div class='pill red'>SanDisk <b>&#8722;14.1%</b> today</div>
      <div class='pill goldpill'>retail leverage at a <span class='goldb'>record $39B</span></div>
      <div class='cue'>&#9654;&nbsp; the chain reaction, explained</div>
      <div class='rail'>Relaying reported market data · educational only — not financial advice.</div>
    </div>
  </div>
</div></body></html>"""


def build():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.set_content(HTML, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT), clip={"x": 0, "y": 0, "width": W, "height": H})
        b.close()
    print("wrote", OUT)


if __name__ == "__main__":
    build()
