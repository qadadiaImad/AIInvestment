"""Build the Instagram profile picture from the approved cast art.

WHY NOT GENERATE ONE. The faces are already canon and already vectorised.
A fresh generation would be a fourth Sol, subtly off from the three the
audience just watched for three minutes, and identity drift is the exact
failure this project has fought all the way through. So the PFP is a
COMPOSITE of the existing RGBA renders - the same pixels as the show.

DESIGNED FOR 110px, NOT 1024. Instagram shows a profile picture at roughly
110px in feed and 320px on the profile, always circular. That governs every
decision here:

  * heads are huge and cropped tight - a full body would be four grey
    pixels of cardigan;
  * everything meaningful sits inside the INSCRIBED CIRCLE, because the
    corners are always thrown away;
  * no text - a show title is illegible at 110px and just adds mush;
  * one bright rim light behind the heads to separate them from the dark
    ground, since at small size silhouette is all that survives.

Head geometry is read from rig_parts.json (headBox / neck), the same
measured anchors the rig uses, rather than eyeballed crops.

  python scripts/vector/make_pfp.py
Writes content/brand/pfp_*.png plus a legibility strip at real sizes.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
FIX = REPO / "remotion/src/fixtures/cast_ep1/rig_parts.json"
OUT = REPO / "content/brand"

S = 1024                      # master size
NAVY = (10, 16, 28)
INK = (6, 10, 18)
MINT = (124, 224, 162)
AMBER = (232, 176, 84)


def head_crop(pose: str, pad_x: float = 0.10, drop: float = 1.45):
    """Head + shoulders, from the measured headBox / neck anchors."""
    rig = json.loads(FIX.read_text("utf-8"))[pose]
    im = Image.open(RENDERS / f"_{pose}_rgba.png").convert("RGBA")
    w, h = im.size
    x0, x1 = rig["headBox"]
    neck = rig["neck"]
    px = (x1 - x0) * pad_x
    L = max(0, int((x0 - px) * w))
    R = min(w, int((x1 + px) * w))
    B = min(h, int(neck * drop * h))
    box = im.crop((L, 0, R, B))
    # trim fully transparent margins so scaling is about the ink, not the canvas
    a = np.asarray(box)[..., 3]
    ys, xs = np.nonzero(a > 8)
    if len(ys):
        box = box.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return box


def fit(im: Image.Image, target_h: int) -> Image.Image:
    r = target_h / im.height
    return im.resize((max(1, int(im.width * r)), target_h), Image.LANCZOS)


def ground() -> Image.Image:
    """Dark radial ground with the studio's teal cast, plus a desk arc."""
    g = Image.new("RGB", (S, S), NAVY)
    d = ImageDraw.Draw(g)
    cx, cy = S / 2, S * 0.46
    for i in range(28, 0, -1):
        t = i / 28
        r = int(S * 0.62 * t)
        v = tuple(int(NAVY[k] + (30, 58, 74)[k] * (1 - t) ** 2) for k in range(3))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    g = g.filter(ImageFilter.GaussianBlur(38))
    d = ImageDraw.Draw(g)
    # the desk, as a single arc - the show's one recognisable furniture line
    d.ellipse([-S * 0.30, S * 0.80, S * 1.30, S * 1.62], fill=(38, 26, 24))
    d.arc([-S * 0.30, S * 0.80, S * 1.30, S * 1.62], 180, 360,
          fill=AMBER, width=6)
    return g


def rim(im: Image.Image, colour, grow: int = 13) -> Image.Image:
    """A glow behind a cut-out, so the silhouette survives at 110px."""
    a = im.split()[3].filter(ImageFilter.GaussianBlur(grow))
    lay = Image.new("RGBA", im.size, colour + (0,))
    lay.putalpha(a.point(lambda v: int(v * 0.85)))
    return lay


def circle_mask(size: int) -> Image.Image:
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4, size * 4], fill=255)
    return m.resize((size, size), Image.LANCZOS)


VARIANTS = {
    # name: (sol pose, rex pose, sol height, rex height, sol cx, rex cx, sol cy, rex cy)
    "duo": ("sol_smug_v1", "rex_eager", 0.60, 0.50, 0.62, 0.30, 0.50, 0.56),
    "duo_tight": ("sol_smug_v1", "rex_skeptic", 0.68, 0.54, 0.64, 0.29, 0.47, 0.55),
    "sol_lead": ("sol_smug_v1", "rex_eager", 0.74, 0.38, 0.54, 0.20, 0.46, 0.63),
}


def build(name: str, spec) -> Image.Image:
    sp, rp, sh, rh, scx, rcx, scy, rcy = spec
    g = ground().convert("RGBA")
    sol = fit(head_crop(sp), int(S * sh))
    rex = fit(head_crop(rp), int(S * rh))
    # Rex behind and left, Sol front and right - the show's own seating
    for im, cx, cy, col in ((rex, rcx, rcy, (70, 140, 200)),
                            (sol, scx, scy, MINT)):
        x = int(S * cx - im.width / 2)
        y = int(S * cy - im.height / 2)
        g.alpha_composite(rim(im, col), (x, y))
        g.alpha_composite(im, (x, y))
    return g.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, spec in VARIANTS.items():
        img = build(name, spec)
        img.save(OUT / f"pfp_{name}.png")
        # the circular version, which is what anyone actually sees
        c = img.convert("RGBA")
        c.putalpha(circle_mask(S))
        c.save(OUT / f"pfp_{name}_circle.png")
        made.append((name, img))
        print(f"  pfp_{name}.png")

    # LEGIBILITY STRIP. Every variant at the three sizes Instagram uses,
    # circular, on a neutral field. If it fails here it fails, whatever it
    # looks like at 1024.
    sizes = [320, 150, 110]
    pad = 22
    w = sum(sizes) + pad * (len(sizes) + 1)
    h = (320 + pad * 2 + 26) * len(made)
    strip = Image.new("RGB", (w, h), (238, 240, 244))
    d = ImageDraw.Draw(strip)
    for r, (name, img) in enumerate(made):
        y0 = r * (320 + pad * 2 + 26)
        d.text((pad, y0 + 6), name, fill=(20, 24, 34))
        x = pad
        for s in sizes:
            c = img.resize((s, s), Image.LANCZOS).convert("RGBA")
            c.putalpha(circle_mask(s))
            strip.paste(c, (x, y0 + 26 + (320 - s) // 2), c)
            d.text((x, y0 + 26 + 320 + 2), f"{s}px", fill=(90, 96, 110))
            x += s + pad
    strip.save(OUT / "pfp_legibility.png")
    print("-> " + str(OUT / "pfp_legibility.png"))


if __name__ == "__main__":
    main()
