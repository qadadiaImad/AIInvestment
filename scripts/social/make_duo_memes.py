"""Stacked two-panel "which investor are you" memes (9:16, Instagram-native).

Top panel  = the confident selfie  -> label in house green  (#00E676)
Bottom panel = the defeated shot   -> label in house red    (#FF3B30)

Same template for every pair so the set reads as one series:
    small tracked kicker  +  heavy uppercase term  on a bottom scrim,
    a VS chip on the seam, and the compliance footer on every frame.

Usage:  python scripts/social/make_duo_memes.py
Output: higgs/duo_memes/*.png  (1080x1920)
"""

from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants

W, H = 1080, 1920
PANEL_H = H // 2                      # 960 each
SEAM = 6                              # divider thickness

GREEN = (0, 230, 118)                 # house up-colour
RED = (255, 59, 48)                   # house down-colour
INK = (6, 9, 11)
WHITE = (255, 255, 255)

FONT_BLACK = r"C:\Windows\Fonts\ariblk.ttf"    # Arial Black - the big term
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"    # Arial Bold  - kicker / footer

SRC_TOP = r"C:\Users\imadq\Downloads\hf_20260726_192848_e3830f4f-3df1-4aab-b7eb-3e3192e11713.png"
SRC_BOT = r"C:\Users\imadq\Downloads\hf_20260726_193306_c2927f89-dd26-42ec-9ec4-02f8211c76fe.png"

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "higgs", "duo_memes")

FOOTER = "EDUCATIONAL ONLY  \u00b7  NOT INVESTMENT ADVICE"

# kicker, top term, bottom term
PAIRS = [
    ("bull-vs-bear",        "PEOPLE WHO LIKE",     "BULL MARKETS",  "BEAR MARKETS"),
    ("momentum-vs-rotation", "PEOPLE WHO TRADE",   "MOMENTUM",      "SECTOR ROTATION"),
    ("btc-vs-dollar",       "PEOPLE WHO HOLD",     "BITCOIN",       "US DOLLARS"),
    ("hype-vs-news",        "PEOPLE WHO TRADE THE", "HYPE",         "NEWS"),
    ("charts-vs-filings",   "PEOPLE WHO TRUST",    "CHARTS",        "FILINGS"),
    ("vol-vs-flat",         "PEOPLE WHO LIKE",     "VOLATILITY",    "SIDEWAYS TAPE"),
    ("earnings-vs-fed",     "PEOPLE WHO LIVE FOR", "EARNINGS DAY",  "FED DAY"),
    ("ai-vs-defensives",    "PEOPLE WHO BUY",      "AI STOCKS",     "DEFENSIVE STOCKS"),
]

# ---------------------------------------------------------------- helpers


def panel(src_path: str, anchor: str) -> Image.Image:
    """Center-crop a square source to the panel aspect, biased to keep the face."""
    im = Image.open(src_path).convert("RGB")
    sw, sh = im.size
    crop_h = int(round(sw * PANEL_H / W))          # 1.125:1 band out of the square
    if anchor == "top":                            # arms-out selfie: keep sky + face
        y0 = 0
    else:                                          # lying down: face sits mid-frame
        y0 = (sh - crop_h) // 2
    im = im.crop((0, y0, sw, y0 + crop_h))
    return im.resize((W, PANEL_H), Image.LANCZOS)


def scrim(height: int, strength: int = 210) -> Image.Image:
    """Transparent -> dark vertical gradient, so text reads over grass or sky."""
    mask = Image.new("L", (1, height))
    px = mask.load()
    for y in range(height):
        t = y / (height - 1)
        px[0, y] = int(strength * (t ** 1.6))
    mask = mask.resize((W, height), Image.BILINEAR)
    layer = Image.new("RGBA", (W, height), INK + (0,))
    layer.putalpha(mask)
    return layer


def tracked_width(draw, text, font, tracking):
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def draw_tracked(draw, xy, text, font, fill, tracking, stroke=0, stroke_fill=INK):
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=font, fill=fill, anchor="ls",
                  stroke_width=stroke, stroke_fill=stroke_fill)
        x += draw.textlength(c, font=font) + tracking


def fit_term(draw, term: str, max_w: int, max_size: int, max_block_h: int):
    """Pick the largest Arial Black size for 1- or 2-line layouts of the term."""
    words = term.split()
    layouts = [[term]]
    # only break into two lines when neither line would be a stub ("AI", "DAY")
    if len(words) == 2 and all(len(w) >= 4 for w in words):
        layouts.append(words)
    best = None
    for lines in layouts:
        for size in range(max_size, 47, -2):
            font = ImageFont.truetype(FONT_BLACK, size)
            widths = [draw.textlength(l, font=font) for l in lines]
            line_h = int(size * 1.06)
            block_h = line_h * len(lines)
            if max(widths) <= max_w and block_h <= max_block_h:
                if best is None or size > best[0]:
                    best = (size, lines, font, line_h)
                break
    return best


def caption(canvas, draw, kicker, term, colour, bottom_y):
    """Bottom-anchored caption block: tracked kicker above a heavy term."""
    fit = fit_term(draw, term, max_w=880, max_size=118, max_block_h=280)
    size, lines, font, line_h = fit
    stroke = max(6, size // 13)

    # term lines, stacked upward from bottom_y
    y = bottom_y
    for line in reversed(lines):
        w = draw.textlength(line, font=font)
        draw.text(((W - w) / 2, y), line, font=font, fill=colour, anchor="ls",
                  stroke_width=stroke, stroke_fill=INK)
        y -= line_h

    # kicker sits above the term block
    k_size = 38
    k_font = ImageFont.truetype(FONT_BOLD, k_size)
    tracking = 7
    kw = tracked_width(draw, kicker, k_font, tracking)
    draw_tracked(draw, ((W - kw) / 2, y - 14), kicker, k_font, (255, 255, 255),
                 tracking, stroke=5)


def vs_chip(canvas, draw):
    cx, cy, r = W // 2, PANEL_H, 66
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK, outline=WHITE, width=5)
    f = ImageFont.truetype(FONT_BLACK, 52)
    draw.text((cx, cy + 2), "VS", font=f, fill=WHITE, anchor="mm")


def build(slug, kicker, top_term, bot_term, top_img, bot_img):
    canvas = Image.new("RGB", (W, H), INK)
    canvas.paste(top_img, (0, 0))
    canvas.paste(bot_img, (0, PANEL_H))

    sc = scrim(400, strength=225)
    canvas.paste(sc, (0, PANEL_H - 400), sc)
    canvas.paste(sc, (0, H - 400), sc)

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, PANEL_H - SEAM // 2, W, PANEL_H + SEAM // 2), fill=INK)

    caption(canvas, draw, kicker, top_term, GREEN, bottom_y=PANEL_H - 96)
    caption(canvas, draw, kicker, bot_term, RED, bottom_y=H - 122)
    vs_chip(canvas, draw)

    f_font = ImageFont.truetype(FONT_BOLD, 21)
    fw = tracked_width(draw, FOOTER, f_font, 3)
    draw_tracked(draw, ((W - fw) / 2, H - 40), FOOTER, f_font,
                 (255, 255, 255, 255), 3, stroke=4)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{slug}.png")
    canvas.save(path, "PNG", optimize=True)
    # JPEG twin: ~10x smaller, what actually gets uploaded to IG
    canvas.save(os.path.join(OUT_DIR, f"{slug}.jpg"), "JPEG", quality=92,
                subsampling=0, optimize=True)
    return path


def main():
    top_img = panel(SRC_TOP, "top")
    bot_img = panel(SRC_BOT, "bottom")
    for slug, kicker, t, b in PAIRS:
        print(build(slug, kicker, t, b, top_img, bot_img))


if __name__ == "__main__":
    main()
