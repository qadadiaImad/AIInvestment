"""Render REAL trading-terminal screens for Maya's monitors.

The owner called the AI-painted monitor content artificial — correctly: an
image model's "charts" are fiction (house rule 10.1). These PNGs are drawn in
Python from real Yahoo daily bars, in the house green-terminal style (rule
10.2: bg #02070A, up #00E676, down #FF3B30, accent #22E07E), and get
perspective-warped onto the anchor still's dark screens by
composite_anchor.py. Every pull is stamped in screens_manifest.json.

    python scripts/why_cards/render_terminals.py
"""
import json
import os
import time
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "why")

BG = (2, 7, 10)
UP = (0, 230, 118)
DOWN = (255, 59, 48)
ACCENT = (34, 224, 126)
GRID = (18, 34, 40)
INK = (160, 185, 178)

W, H = 1000, 760  # matches the anchor monitors' projected aspect (~1.32)
SYMBOLS = ["NVDA", "SPY"]


def fetch(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=6mo"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    r = d["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    bars = [
        (o, h, l, c)
        for o, h, l, c in zip(q["open"], q["high"], q["low"], q["close"])
        if None not in (o, h, l, c)
    ]
    return bars[-90:], url


def draw_terminal(symbol, bars):
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    try:
        f_sm = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
        f_big = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 30)
    except OSError:
        f_sm = f_big = ImageFont.load_default()

    pad_l, pad_r, pad_t, pad_b = 24, 110, 70, 30
    lo = min(b[2] for b in bars)
    hi = max(b[1] for b in bars)
    span = hi - lo

    def y(p):
        return pad_t + (hi - p) / span * (H - pad_t - pad_b)

    for k in range(6):  # ruled grid + real price scale
        gy = pad_t + k * (H - pad_t - pad_b) / 5
        dr.line([(pad_l, gy), (W - pad_r, gy)], fill=GRID, width=1)
        price = hi - k * span / 5
        dr.text((W - pad_r + 12, gy - 9), f"{price:,.0f}", fill=INK, font=f_sm)

    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gdr = ImageDraw.Draw(glow)
    n = len(bars)
    step = (W - pad_l - pad_r) / n
    bw = max(3, int(step * 0.55))
    for i, (o, h, l, c) in enumerate(bars):
        x = pad_l + int(i * step + step / 2)
        col = UP if c >= o else DOWN
        for d_ in (dr, gdr):
            d_.line([(x, y(h)), (x, y(l))], fill=col, width=1)
            d_.rectangle([x - bw // 2, y(max(o, c)), x + bw // 2, y(min(o, c))], fill=col)
    img = Image.blend(img, Image.composite(glow.filter(ImageFilter.GaussianBlur(6)), img, Image.new("L", (W, H), 90)), 0.35)

    dr = ImageDraw.Draw(img)
    last = bars[-1][3]
    dr.text((pad_l, 18), symbol, fill=ACCENT, font=f_big)
    dr.text((pad_l + 130, 26), f"{last:,.2f}", fill=(232, 237, 242), font=f_sm)
    dr.text((pad_l + 240, 26), "1D", fill=INK, font=f_sm)
    dr.line([(0, 54), (W, 54)], fill=GRID, width=1)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    stamps = []
    for sym in SYMBOLS:
        bars, url = fetch(sym)
        img = draw_terminal(sym, bars)
        dest = os.path.join(OUT, f"screen_{sym}.png")
        img.save(dest)
        stamps.append({
            "symbol": sym, "bars": len(bars), "last_close": bars[-1][3],
            "source": url, "source_class": "api",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        print(f"{sym}: {len(bars)} bars, last {bars[-1][3]:,.2f} -> {dest}")
    json.dump(stamps, open(os.path.join(OUT, "screens_manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
