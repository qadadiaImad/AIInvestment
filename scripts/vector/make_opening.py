"""Build the episode opening card. One set image, text swapped per episode.

THE OWNER'S RULE, which this file exists to enforce:

  * ONE opening image per VERTICAL (subject area). Every episode inside that
    vertical reuses the same background and the same cast art; only the
    text changes.
  * If the VERTICAL changes - finance to history, say - then everything
    changes: a new background, and the cast get new clothes.

So the card has two zones and they must not be confused:

  FIXED   the brand band at the top (SOL & REX / NEWS) and the set and cast
          below. Identical on every episode of a vertical. This is what
          makes six reels look like one show.
  SWAP    y 470-900 only. Episode number and title. Nothing else may move,
          because a title card whose furniture shifts between episodes
          reads as six different channels.

The background is generated once with grok-cli (Grok Imagine handles a
rich lit studio far better than the local models) and committed as a
finished asset. The CAST IS NEVER GENERATED HERE - grok has no idea who
Sol and Rex are and would invent two strangers, which is the identity
drift this project has fought the whole way. Canon RGBA renders only.

  python scripts/vector/make_opening.py                 # all episodes
  python scripts/vector/make_opening.py 3               # just ep.3
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = Path(__file__).resolve().parents[2]
BRAND = REPO / "content/brand/opening"
RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
ROCK = r"C:\Windows\Fonts\ROCKB.TTF"

W, H = 1080, 1920
CREAM = (244, 238, 224)
AMBER = (232, 176, 84)
TEAL = (124, 224, 162)

# ── THE VERTICAL ───────────────────────────────────────────────────────
# Change these three together, never one alone. A new vertical means a new
# set AND new clothes; keeping the finance wardrobe over a history set is
# the failure this block exists to prevent.
VERTICAL = {
    "name": "finance",
    "set": "set_a.jpg",
    "sol": "sol_smug_v1",     # burgundy cardigan, yellow bow tie
    "rex": "rex_skeptic",     # grey vest, white shirt
}

# ── THE SWAP ZONE ──────────────────────────────────────────────────────
# Two lines max. Rockwell at 120px fits about 11 characters per line at
# this width; longer titles silently overflow the plate.
EPISODES = {
    "1": ("EPISODE 1", ["THE 'FAIR'", "MARKET"]),
    "2": ("EPISODE 2", ["SIXTEEN", "MINUTES"]),
    "3": ("EPISODE 3", ["THEY", "BANNED IT"]),
    "4": ("EPISODE 4", ["NINETY-FIVE", "TO NOTHING"]),
    "5": ("EPISODE 5", ["NO", "TOMORROW"]),
}


def word(txt: str, size: int, fill, track: int = 0) -> Image.Image:
    f = ImageFont.truetype(ROCK, size)
    w = sum(f.getbbox(c)[2] - f.getbbox(c)[0] + track for c in txt) + 60
    im = Image.new("RGBA", (int(w), int(size * 1.9)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 30
    for c in txt:
        d.text((x, size * 0.2), c, font=f, fill=fill)
        x += f.getbbox(c)[2] - f.getbbox(c)[0] + track
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > 4)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def fit(im: Image.Image, h: int) -> Image.Image:
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


def cast(name: str, h: int) -> Image.Image:
    im = Image.open(RENDERS / f"_{name}_rgba.png").convert("RGBA")
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > 8)
    return fit(im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)), h)


def rim(im: Image.Image, col, g: int = 18) -> Image.Image:
    a = im.split()[3].filter(ImageFilter.GaussianBlur(g))
    lay = Image.new("RGBA", im.size, col + (0,))
    lay.putalpha(a.point(lambda v: int(v * 0.7)))
    return lay


def base() -> Image.Image:
    """Everything that does NOT change between episodes."""
    bg = Image.open(BRAND / VERTICAL["set"]).convert("RGB").resize(
        (W, H), Image.LANCZOS)
    bg = Image.eval(bg, lambda v: int(v * 0.78)).convert("RGBA")
    for who, cx, by, h, col in (("rex", 0.31, 1520, 690, (70, 140, 200)),
                                ("sol", 0.68, 1540, 760, TEAL)):
        im = cast(VERTICAL[who], h)
        x = int(W * cx - im.width / 2)
        y = by - im.height
        bg.alpha_composite(rim(im, col), (x, y))
        bg.alpha_composite(im, (x, y))
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 150, W, 168], fill=AMBER)
    wm = fit(word("SOL & REX", 150, CREAM, 8), 96)
    bg.alpha_composite(wm, ((W - wm.width) // 2, 210))
    sb = fit(word("NEWS", 120, AMBER, 22), 42)
    bg.alpha_composite(sb, ((W - sb.width) // 2, 330))
    d.rectangle([0, 400, W, 406], fill=TEAL)
    return bg


def main() -> None:
    want = set(sys.argv[1:]) or set(EPISODES)
    BRAND.mkdir(parents=True, exist_ok=True)
    shared = base()
    for ep in sorted(want):
        if ep not in EPISODES:
            print(f"  ep{ep}: no title registered")
            continue
        num, lines = EPISODES[ep]
        img = shared.copy()
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        do = ImageDraw.Draw(ov)
        do.rectangle([70, 470, W - 70, 900], fill=(6, 10, 18, 190))
        do.rectangle([70, 470, W - 70, 478], fill=AMBER + (255,))
        img.alpha_composite(ov)
        e = fit(word(num, 90, AMBER, 16), 40)
        img.alpha_composite(e, (110, 520))
        for i, ln in enumerate(lines[:2]):
            t = fit(word(ln, 150, CREAM, 4), 120)
            if t.width > W - 220:
                print(f"  ep{ep}: WARNING '{ln}' overflows the plate")
            img.alpha_composite(t, (110, 600 + i * 140))
        out = BRAND / f"opening_ep{ep}.png"
        img.convert("RGB").save(out)
        print(f"  {out.name}  [{VERTICAL['name']}]")


if __name__ == "__main__":
    main()
