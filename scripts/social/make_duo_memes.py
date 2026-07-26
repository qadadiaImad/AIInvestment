"""Stacked two-panel "which investor are you" memes.

Top panel  = the confident selfie  -> label in house green  (#00E676)
Bottom panel = the defeated shot   -> label in house red    (#FF3B30)

Same template for every pair so the set reads as one series:
    small tracked kicker  +  heavy uppercase term  on a bottom scrim,
    a VS chip on the seam, and the compliance footer on every frame.

Two formats, one spec each; every size is derived from the panel height so
the feed cut is the story cut, not a squashed version of it:
    feed  1080x1350 (4:5)  -- the in-feed maximum, nothing gets cropped
    story 1080x1920 (9:16) -- Reels / Stories

Usage:  python scripts/social/make_duo_memes.py
Output: higgs/duo_memes/{feed,story}/*.png + *.jpg
"""

from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants

GREEN = (0, 230, 118)                 # house up-colour
RED = (255, 59, 48)                   # house down-colour
INK = (6, 9, 11)
WHITE = (255, 255, 255)
SEAM = 6                              # divider thickness

FONT_BLACK = r"C:\Windows\Fonts\ariblk.ttf"    # Arial Black - the big term
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"    # Arial Bold  - kicker / footer

SRC_TOP = r"C:\Users\imadq\Downloads\hf_20260726_192848_e3830f4f-3df1-4aab-b7eb-3e3192e11713.png"
SRC_BOT = r"C:\Users\imadq\Downloads\hf_20260726_193306_c2927f89-dd26-42ec-9ec4-02f8211c76fe.png"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "higgs", "duo_memes")

FOOTER = "EDUCATIONAL ONLY  \u00b7  NOT INVESTMENT ADVICE"

FORMATS = {
    "feed": dict(w=1080, h=1350, term_max=98, term_w=880, block_h=225,
                 kicker=32, tracking=6, scrim=290, chip_r=52, chip_font=42,
                 top_pad=74, bot_pad=94, footer=19, footer_pad=32),
    "story": dict(w=1080, h=1920, term_max=118, term_w=880, block_h=280,
                  kicker=38, tracking=7, scrim=400, chip_r=66, chip_font=52,
                  top_pad=96, bot_pad=122, footer=21, footer_pad=40),
}

# slug, kicker, top term, bottom term
PAIRS = [
    ("bull-vs-bear",         "PEOPLE WHO LIKE",      "BULL MARKETS", "BEAR MARKETS"),
    ("momentum-vs-rotation", "PEOPLE WHO TRADE",     "MOMENTUM",     "SECTOR ROTATION"),
    ("btc-vs-dollar",        "PEOPLE WHO HOLD",      "BITCOIN",      "US DOLLARS"),
    ("hype-vs-news",         "PEOPLE WHO TRADE THE", "HYPE",         "NEWS"),
    ("charts-vs-filings",    "PEOPLE WHO TRUST",     "CHARTS",       "FILINGS"),
    ("vol-vs-flat",          "PEOPLE WHO LIKE",      "VOLATILITY",   "SIDEWAYS TAPE"),
    ("earnings-vs-fed",      "PEOPLE WHO LIVE FOR",  "EARNINGS DAY", "FED DAY"),
    ("ai-vs-defensives",     "PEOPLE WHO BUY",       "AI STOCKS",    "DEFENSIVE STOCKS"),
]

# ---------------------------------------------------------------- helpers


def panel(src_path, anchor, w, panel_h):
    """Crop a square source to the panel aspect, biased to keep the face."""
    im = Image.open(src_path).convert("RGB")
    sw, sh = im.size
    crop_h = int(round(sw * panel_h / w))
    if anchor == "top":                            # arms-out selfie: keep sky + face
        y0 = 0
    else:                                          # lying down: face sits mid-frame
        y0 = (sh - crop_h) // 2
    return im.crop((0, y0, sw, y0 + crop_h)).resize((w, panel_h), Image.LANCZOS)


def scrim(w, height, strength=225):
    """Transparent -> dark vertical gradient, so text reads over grass or sky."""
    mask = Image.new("L", (1, height))
    px = mask.load()
    for y in range(height):
        px[0, y] = int(strength * ((y / (height - 1)) ** 1.6))
    layer = Image.new("RGBA", (w, height), INK + (0,))
    layer.putalpha(mask.resize((w, height), Image.BILINEAR))
    return layer


def tracked_width(draw, text, font, tracking):
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def draw_tracked(draw, xy, text, font, fill, tracking, stroke=0):
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=font, fill=fill, anchor="ls",
                  stroke_width=stroke, stroke_fill=INK)
        x += draw.textlength(c, font=font) + tracking


def fit_term(draw, term, max_w, max_size, max_block_h):
    """Largest Arial Black size across the 1- and 2-line layouts of the term."""
    words = term.split()
    layouts = [[term]]
    # only break into two lines when neither line would be a stub ("AI", "DAY")
    if len(words) == 2 and all(len(w) >= 4 for w in words):
        layouts.append(words)
    best = None
    for lines in layouts:
        for size in range(max_size, 39, -2):
            font = ImageFont.truetype(FONT_BLACK, size)
            line_h = int(size * 1.06)
            if (max(draw.textlength(l, font=font) for l in lines) <= max_w
                    and line_h * len(lines) <= max_block_h):
                if best is None or size > best[0]:
                    best = (size, lines, font, line_h)
                break
    return best


def caption(draw, spec, kicker, term, colour, bottom_y):
    """Bottom-anchored caption block: tracked kicker above a heavy term."""
    size, lines, font, line_h = fit_term(draw, term, spec["term_w"],
                                         spec["term_max"], spec["block_h"])
    stroke = max(5, size // 13)
    w = spec["w"]

    y = bottom_y
    for line in reversed(lines):
        lw = draw.textlength(line, font=font)
        draw.text(((w - lw) / 2, y), line, font=font, fill=colour, anchor="ls",
                  stroke_width=stroke, stroke_fill=INK)
        y -= line_h

    k_font = ImageFont.truetype(FONT_BOLD, spec["kicker"])
    kw = tracked_width(draw, kicker, k_font, spec["tracking"])
    draw_tracked(draw, ((w - kw) / 2, y - spec["kicker"] * 0.36), kicker, k_font,
                 WHITE, spec["tracking"], stroke=max(4, spec["kicker"] // 8))


def vs_chip(draw, spec, panel_h):
    cx, cy, r = spec["w"] // 2, panel_h, spec["chip_r"]
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK, outline=WHITE,
                 width=max(4, r // 13))
    draw.text((cx, cy + 2), "VS", font=ImageFont.truetype(FONT_BLACK, spec["chip_font"]),
              fill=WHITE, anchor="mm")


def build(spec, out_dir, slug, kicker, top_term, bot_term, top_img, bot_img):
    w, h = spec["w"], spec["h"]
    panel_h = h // 2

    canvas = Image.new("RGB", (w, h), INK)
    canvas.paste(top_img, (0, 0))
    canvas.paste(bot_img, (0, panel_h))

    sc = scrim(w, spec["scrim"])
    canvas.paste(sc, (0, panel_h - spec["scrim"]), sc)
    canvas.paste(sc, (0, h - spec["scrim"]), sc)

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, panel_h - SEAM // 2, w, panel_h + SEAM // 2), fill=INK)

    caption(draw, spec, kicker, top_term, GREEN, panel_h - spec["top_pad"])
    caption(draw, spec, kicker, bot_term, RED, h - spec["bot_pad"])
    vs_chip(draw, spec, panel_h)

    f_font = ImageFont.truetype(FONT_BOLD, spec["footer"])
    fw = tracked_width(draw, FOOTER, f_font, 3)
    draw_tracked(draw, ((w - fw) / 2, h - spec["footer_pad"]), FOOTER, f_font,
                 WHITE, 3, stroke=4)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{slug}.png")
    canvas.save(path, "PNG", optimize=True)
    # JPEG twin: ~10x smaller, what actually gets uploaded to IG
    canvas.save(os.path.join(out_dir, f"{slug}.jpg"), "JPEG", quality=92,
                subsampling=0, optimize=True)
    return path


def main():
    for name, spec in FORMATS.items():
        out_dir = os.path.join(OUT_DIR, name)
        panel_h = spec["h"] // 2
        top_img = panel(SRC_TOP, "top", spec["w"], panel_h)
        bot_img = panel(SRC_BOT, "bottom", spec["w"], panel_h)
        for slug, kicker, t, b in PAIRS:
            print(build(spec, out_dir, slug, kicker, t, b, top_img, bot_img))


if __name__ == "__main__":
    main()
