"""Composite the REAL terminal renders onto the anchor still's dark screens.

anchor_base.png (720x1280, screens OFF) + screen_SPY/screen_NVDA.png (real
Yahoo bars, house terminal style) -> anchor_final.png. Perspective-warp each
terminal onto its measured screen quad, then re-occlude Maya's head with a
feathered silhouette polygon — her hair overlaps the join between the two
monitors, and a chart drawn OVER hair is the tell that kills the shot.

A faint warm sheen goes over the glass so the inserts sit in the sunset
light instead of floating. Quads/polygon were measured by eye on the still
and iterated against rendered output.

    python scripts/why_cards/composite_anchor.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
WHY = os.path.join(REPO, "remotion", "public", "why")

# screen quads on the 720x1280 base, clockwise from top-left (measured on a
# gridded 3x crop; the left monitor's top edge rises slightly to the right)
QUAD_LEFT = [(10, 490), (284, 486), (285, 701), (10, 688)]
QUAD_RIGHT = [(288, 490), (558, 487), (561, 701), (288, 700)]

# generous corridor around Maya's head/shoulders — the REAL occlusion mask is
# colorimetric (warm hair vs neutral-dark off-screen) and only applies inside
# this corridor. A hand-drawn polygon alone shipped ~30px wide of the hair
# and restored a band of blank screen next to it — the chart cut to black
# before the hair started, which read as a broken display.
CORRIDOR = [
    (100, 720), (120, 590), (150, 520), (185, 488), (250, 480),
    (295, 505), (320, 560), (340, 650), (350, 720),
]


def find_coeffs(dst, src):
    """PIL PERSPECTIVE coeffs. PIL maps each OUTPUT pixel (x,y) to an INPUT
    location (u,v) = ((ax+by+c)/(gx+hy+1), (dx+ey+f)/(gx+hy+1)) — so the
    linear system is built on dst coords with src as the right-hand side.
    (Solving the reverse direction smears a source corner across the quad.)"""
    a = []
    b = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    return np.linalg.solve(np.array(a, dtype=np.float64), np.array(b, dtype=np.float64))


def warp_onto(base, screen_png, quad):
    scr = Image.open(screen_png).convert("RGBA")
    w, h = base.size
    src = [(0, 0), (scr.width, 0), (scr.width, scr.height), (0, 0 + scr.height)]
    coeffs = find_coeffs(quad, src)
    warped = scr.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(quad, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    base.paste(warped, (0, 0), mask)
    return base


def main():
    base = Image.open(os.path.join(WHY, "anchor_base.png")).convert("RGBA")
    keep = base.copy()  # pre-composite pixels, used to restore the occluder

    base = warp_onto(base, os.path.join(WHY, "screen_SPY.png"), QUAD_LEFT)
    base = warp_onto(base, os.path.join(WHY, "screen_NVDA.png"), QUAD_RIGHT)

    # warm glass sheen so the inserts share the sunset light
    sheen = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdr = ImageDraw.Draw(sheen)
    for quad in (QUAD_LEFT, QUAD_RIGHT):
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]
        for i in range(24):
            a = int(16 * (1 - i / 24))
            sdr.polygon(
                [(min(xs) + i * 6, min(ys)), (min(xs) + i * 6 + 5, min(ys)),
                 (min(xs) + i * 6 + 5 + 40, max(ys)), (min(xs) + i * 6 + 40, max(ys))],
                fill=(255, 214, 160, a),
            )
    scr_mask = Image.new("L", base.size, 0)
    for quad in (QUAD_LEFT, QUAD_RIGHT):
        ImageDraw.Draw(scr_mask).polygon(quad, fill=255)
    base = Image.composite(Image.alpha_composite(base, sheen), base, scr_mask)

    # restore Maya over the screens: colorimetric hair mask inside the
    # corridor. Off screens are neutral/cool dark (R<=B-ish); hair is warm
    # (R-B high) with bright rim light — segment on that, close small gaps,
    # feather the edge.
    arr = np.asarray(keep.convert("RGB")).astype(np.int16)
    warm = ((arr[:, :, 0] - arr[:, :, 2] >= 7) & (arr[:, :, 0] >= 18)) | (
        arr.mean(axis=2) > 85
    )
    hair = Image.fromarray((warm * 255).astype(np.uint8), "L")
    corridor = Image.new("L", base.size, 0)
    ImageDraw.Draw(corridor).polygon(CORRIDOR, fill=255)
    hair = Image.composite(hair, Image.new("L", base.size, 0), corridor)
    # close strand gaps hard — the darkest crown pixels fail the warm test and
    # left candle fragments printed across her head on the first pass
    hair = hair.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(5))
    core = Image.new("L", base.size, 0)  # center of head/neck is always hers
    ImageDraw.Draw(core).polygon(
        [(180, 540), (192, 505), (215, 494), (248, 494), (272, 514),
         (287, 545), (292, 605), (287, 665), (277, 720), (188, 720), (178, 620)],
        fill=255,
    )
    hair = Image.fromarray(np.maximum(np.asarray(hair), np.asarray(core)))
    hair = hair.filter(ImageFilter.GaussianBlur(2.5))
    base.paste(keep, (0, 0), hair)

    out = os.path.join(WHY, "anchor_final.png")
    base.convert("RGB").save(out)
    print(f"OK {out}")


if __name__ == "__main__":
    main()
