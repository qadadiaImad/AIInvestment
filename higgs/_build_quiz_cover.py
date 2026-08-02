"""Reel cover for the "5-Second Value Test" quiz reel. 1080x1920 (@2). Big hook
+ the 6 ticker chips + a teaser, over the NVDA circuit hero. Brand system
(dark #0A0D12, gold #E0A23B, mint #7FE9C2). Writes higgs/value_quiz_cover.png.

    python higgs/_build_quiz_cover.py
"""
from __future__ import annotations
import base64, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HIGGS = ROOT / "higgs"
BG = ROOT / "halal-reels" / "public" / "quiz" / "nvidia.jpg"
OUT = HIGGS / "value_quiz_cover.png"
W, H = 1080, 1920

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,900&family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@700;800&display=swap');"
bg_b64 = "data:image/jpeg;base64," + base64.b64encode(BG.read_bytes()).decode()

TICKERS = ["NVDA", "META", "GOOGL", "AMD", "ADBE", "INTC"]
chips = "".join(f"<div class='chip'>{t}</div>" for t in TICKERS)

HTML = f"""<!doctype html><html><head><meta charset='utf-8'><style>
*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:-30px;background-image:url('{bg_b64}');background-size:cover;background-position:center 55%}}
.scrim{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,13,18,.72) 0%,rgba(10,13,18,.5) 34%,rgba(10,13,18,.66) 62%,rgba(10,13,18,.97) 100%)}}
.pad{{position:absolute;inset:0;padding:100px 84px 92px;display:flex;flex-direction:column;z-index:2}}
.brand{{display:flex;align-items:baseline;gap:2px;font-family:'JetBrains Mono';font-weight:800;font-size:28px;letter-spacing:1px;text-shadow:0 2px 12px rgba(0,0,0,.8)}}
.brand .g{{color:#34D399}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:30px;letter-spacing:5px;color:#7FE9C2;margin-top:52px;text-shadow:0 2px 14px rgba(0,0,0,.8)}}
.hook{{font-family:Fraunces;font-weight:900;font-size:132px;line-height:.98;letter-spacing:-3px;color:#fff;margin-top:26px;text-shadow:0 4px 30px rgba(0,0,0,.75)}}
.hook .gold{{color:#E0A23B}}
.timer{{font-family:'JetBrains Mono';font-weight:800;font-size:40px;letter-spacing:2px;color:#fff;margin-top:30px}}
.timer b{{color:#7FE9C2}}
.chips{{display:flex;flex-wrap:wrap;gap:16px;margin-top:38px}}
.chip{{font-family:'JetBrains Mono';font-weight:800;font-size:38px;letter-spacing:1px;color:#fff;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.22);border-radius:16px;padding:16px 26px;backdrop-filter:blur(3px)}}
.tease{{margin-top:auto;font-family:Inter;font-weight:700;font-size:44px;line-height:1.32;color:#D7DEE8;text-shadow:0 2px 16px rgba(0,0,0,.8)}}
.tease .gold{{color:#E0A23B}}
.rail{{font-family:'JetBrains Mono';font-size:19px;letter-spacing:.4px;color:#8893A4;margin-top:26px;text-shadow:0 1px 10px rgba(0,0,0,.85)}}
</style></head><body><div class='slide'>
  <div class='hero'></div><div class='scrim'></div>
  <div class='pad'>
    <div class='brand'><span>AI</span><span class='g'>STACK</span><span>&nbsp;·&nbsp;TERMINAL</span></div>
    <div class='kick'>THE 5-SECOND VALUE TEST</div>
    <div class='hook'>Can you spot the <span class='gold'>overvalued</span> stock?</div>
    <div class='timer'>6 famous names · <b>5 seconds each</b> · call it before the timer</div>
    <div class='chips'>{chips}</div>
    <div class='tease'>One is priced near <span class='gold'>3&#215; fair value</span>.<br>One "bubble" is actually cheap. Most people miss both.</div>
    <div class='rail'>A model's read, not a call · educational — not financial advice.</div>
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
