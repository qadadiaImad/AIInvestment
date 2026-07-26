"""Measure the monitor's screen quad in a generated room plate.

The chart is perspective-mapped onto the monitor by ScreenInsert, and that
mapping is only correct if the destination quad matches where the screen
ACTUALLY is in the plate. The generator does not place the monitor at the
coordinates the prompt asked for -- it places it somewhere close -- so the quad
is measured from the accepted plate rather than assumed from the brief. Pick one
direction and lock it; this is that direction.

Method: the screen is by construction the largest connected region of near-black
pixels in an otherwise warm, mid-tone illustration. Flood-fill the dark mask,
take the largest component, and report its bounding box both in plate pixels and
normalised to the 1080x1920 composition.

The bezel is a slightly lighter charcoal than the screen, so the threshold has
to separate the two. The script reports the component's fill ratio (area /
bbox area); anything below ~0.97 means the mask leaked into the bezel or the
stand and the threshold needs lowering -- it does not silently accept it.

Usage:
    python scripts/meme_reel/measure_screen_quad.py higgs/meme_reel/room_plate_C.png
"""
import json
import os
import sys
from collections import deque

from PIL import Image

# Luminance below this counts as "screen". The bezel in the generated plates
# sits around 55-75; the screen sits under 30.
DARK_MAX = 42
# The composition the quad is consumed in.
COMP_W, COMP_H = 1080, 1920


def largest_dark_component(img, dark_max=DARK_MAX):
    g = img.convert("L")
    w, h = g.size
    px = g.load()
    seen = bytearray(w * h)
    best = None

    for sy in range(0, h, 2):  # stride the seeds; components are large
        for sx in range(0, w, 2):
            if seen[sy * w + sx] or px[sx, sy] > dark_max:
                continue
            q = deque([(sx, sy)])
            seen[sy * w + sx] = 1
            x0 = x1 = sx
            y0 = y1 = sy
            area = 0
            while q:
                x, y = q.popleft()
                area += 1
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny] <= dark_max:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            if best is None or area > best["area"]:
                best = {"area": area, "bbox": (x0, y0, x1, y1)}
    return best


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    img = Image.open(path)
    w, h = img.size
    comp = largest_dark_component(img)
    if comp is None:
        print("No dark region found -- is this the right plate?")
        return 1

    x0, y0, x1, y1 = comp["bbox"]
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    fill = comp["area"] / float(bw * bh)

    # The plate is rendered at the composition's aspect; scale the measurement
    # into 1080x1920 space, which is what the TSX consumes.
    sx, sy = COMP_W / float(w), COMP_H / float(h)
    q = [
        (x0 * sx, y0 * sy),
        (x1 * sx, y0 * sy),
        (x1 * sx, y1 * sy),
        (x0 * sx, y1 * sy),
    ]

    print(f"plate            : {os.path.basename(path)}  ({w}x{h})")
    print(f"dark component   : area={comp['area']}  bbox={comp['bbox']}  {bw}x{bh}")
    print(f"fill ratio       : {fill:.4f}  {'OK (clean rectangle)' if fill > 0.97 else 'LEAKED -- lower DARK_MAX'}")
    print(f"aspect           : {bw / float(bh):.3f}")
    print(f"screen in plate %: x {x0 / w:.3f}..{x1 / w:.3f}   y {y0 / h:.3f}..{y1 / h:.3f}")
    print()
    print(f"quad in {COMP_W}x{COMP_H} (TL, TR, BR, BL):")
    print(
        "  ["
        + ", ".join(f"{{x: {px:.0f}, y: {py:.0f}}}" for px, py in q)
        + "]"
    )
    print()
    print(json.dumps({"plate": os.path.basename(path), "plate_size": [w, h],
                      "bbox_plate": [x0, y0, x1, y1], "fill_ratio": round(fill, 4),
                      "quad_1080x1920": [[round(px), round(py)] for px, py in q]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
