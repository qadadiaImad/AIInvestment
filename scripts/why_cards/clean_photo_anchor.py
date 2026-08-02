"""Prepare the owner-supplied 'girly day trader' photo as the WhyReel anchor.

Crops the app-frame border, then erases the burned-in caption by rebuilding
the wall behind it: for each row of the text band, the fill color is the
median of the text-free side margins (captures the wall's vertical gradient),
plus matched sensor noise so the patch doesn't read as a sticker. The reel's
own gold serif question is overlaid at render time by the Question component.

    python scripts/why_cards/clean_photo_anchor.py <src.jpeg>
Writes content/probe/anchor_photo_clean.png (pre-upscale).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "content", "probe", "anchor_photo_clean.png")

CROP = (22, 30, 573, 1040)   # inner content inside the app frame
TEXT_BAND = (0, 178)          # rows of the caption, in cropped coords
MARGIN_L = (2, 22)            # text-free wall columns used as row samples
MARGIN_R = (506, 549)


def main():
    src = Image.open(sys.argv[1]).convert("RGB").crop(CROP)
    arr = np.asarray(src).astype(np.float64)
    rng = np.random.default_rng(7)

    y0, y1 = TEXT_BAND
    for y in range(y0, y1):
        row = np.concatenate([
            arr[y, MARGIN_L[0]:MARGIN_L[1]], arr[y, MARGIN_R[0]:MARGIN_R[1]]
        ])
        med = np.median(row, axis=0)
        # gentle horizontal gradient between the two margins keeps the wall's
        # left-dark / right-light falloff instead of a flat stripe
        med_l = np.median(arr[y, MARGIN_L[0]:MARGIN_L[1]], axis=0)
        med_r = np.median(arr[y, MARGIN_R[0]:MARGIN_R[1]], axis=0)
        w = np.linspace(0, 1, arr.shape[1])[:, None]
        arr[y] = med_l * (1 - w) + med_r * w + rng.normal(0, 2.4, (arr.shape[1], 3))
        del med

    # second pass: the caption's last line dips past the wall onto the TV's
    # top bezel/chrome. Row-context inpaint (blend of same-row medians left
    # and right of the box) heals across the wall->bezel->chrome transitions
    # without breaking the bezel's straight horizontal edge.
    bx0, bx1, by0, by1 = 138, 384, 154, 200
    for y in range(by0, by1):
        med_l = np.median(arr[y, 96:136], axis=0)
        med_r = np.median(arr[y, 388:432], axis=0)
        w = np.linspace(0, 1, bx1 - bx0)[:, None]
        arr[y, bx0:bx1] = med_l * (1 - w) + med_r * w + rng.normal(0, 2.2, (bx1 - bx0, 3))

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # soften the seams so the patches melt into the scene
    seam = img.crop((0, y1 - 6, img.width, y1 + 6)).filter(ImageFilter.GaussianBlur(2))
    img.paste(seam, (0, y1 - 6))
    box = img.crop((bx0 - 6, by0 - 6, bx1 + 6, by1 + 6)).filter(ImageFilter.GaussianBlur(1.2))
    img.paste(box, (bx0 - 6, by0 - 6))
    img.save(OUT)
    print(f"OK {OUT} {img.size}")


if __name__ == "__main__":
    main()
