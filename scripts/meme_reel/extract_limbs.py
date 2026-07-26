"""Cut a generated character parts-sheet into individual rigged limb PNGs.

The reel's character is drawn art rigged as a cutout puppet: a generated sheet
of separated body parts, sliced into one transparent PNG per part, driven by the
FK/IK rig in remotion/src/characters/. This script is the slicing step.

Two things here are easy to get wrong and are done deliberately:

1. BACKGROUND REMOVAL IS A FLOOD FILL FROM THE BORDER, not a white threshold.
   The character's body fill is light grey (~#D9D9D9), which is only ~15% away
   from the white background. Thresholding on brightness would eat the body and
   punch holes through the eye whites. Flooding inward from the image border
   over near-white pixels marks only the background that is actually connected
   to the outside, so interior whites (eyes, highlights) survive.

2. PARTS ARE FOUND BY CONNECTED COMPONENT, not by a hardcoded grid. The
   generator does not place pieces on the grid it was asked for. Labelling the
   foreground and taking the N largest blobs finds them wherever they landed;
   they are then ordered by row (clustered on centroid y) and by x within a row,
   which is the order the prompt lays them out in.

Each part is written with its PIVOT recorded: the joint that its parent rotates
it about. For a limb drawn hanging vertically the pivot is the top-centre of the
ink, which is what the rig's FK assumes (a limb at angle 0 points straight down
from its pivot).

Usage:
    python scripts/meme_reel/extract_limbs.py <sheet.png> <outdir> [--parts 8]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# A pixel this bright is a background candidate. The body fill is ~217; the
# gap has to be wide enough to catch JPEG-ish ringing around the linework
# without reaching the fill.
WHITE_MIN = 238
# Blobs smaller than this fraction of the largest blob are speckle, not a part.
MIN_AREA_FRAC = 0.02

# The order the sheet prompt lays parts out in: two rows of four, left to right.
PART_NAMES = ["head", "torso", "upper_arm", "forearm", "hand", "thigh", "shin", "foot"]


def background_mask(rgb: np.ndarray) -> np.ndarray:
    """True where the pixel is background — near-white AND reachable from the
    image border. Interior whites (eye whites) are deliberately excluded."""
    lum = rgb.astype(np.float32).mean(axis=2)
    nearly_white = lum >= WHITE_MIN

    # Label the near-white regions and keep only those touching the border.
    lab, n = ndimage.label(nearly_white)
    if n == 0:
        return np.zeros(lum.shape, bool)
    border = np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])
    outside = set(int(v) for v in np.unique(border) if v != 0)
    return np.isin(lab, list(outside))


def find_parts(fg: np.ndarray, want: int):
    """Connected components of the foreground, largest `want` kept, ordered
    row-major the way the sheet lays them out."""
    # 8-connectivity: a tapered brush line can pinch to a diagonal hairline, and
    # 4-connectivity would split a single part in two there.
    lab, n = ndimage.label(fg, structure=np.ones((3, 3), int))
    if n == 0:
        return []
    areas = ndimage.sum(fg, lab, range(1, n + 1))
    order = np.argsort(areas)[::-1]
    biggest = areas[order[0]]
    keep = [int(order[i]) + 1 for i in range(len(order)) if areas[order[i]] >= biggest * MIN_AREA_FRAC]
    keep = keep[:want]

    objs = ndimage.find_objects(lab)
    parts = []
    for lbl in keep:
        sy, sx = objs[lbl - 1]
        parts.append({
            "label": lbl,
            "x0": int(sx.start), "x1": int(sx.stop),
            "y0": int(sy.start), "y1": int(sy.stop),
            "cy": (sy.start + sy.stop) / 2.0,
            "cx": (sx.start + sx.stop) / 2.0,
            "area": int(areas[lbl - 1]),
        })

    # Cluster into rows on centroid y: sort by y, start a new row wherever the
    # gap exceeds half a typical part height.
    parts.sort(key=lambda p: p["cy"])
    heights = [p["y1"] - p["y0"] for p in parts]
    gap = float(np.median(heights)) * 0.6
    rows, cur = [], [parts[0]]
    for p in parts[1:]:
        if p["cy"] - cur[-1]["cy"] > gap:
            rows.append(cur)
            cur = [p]
        else:
            cur.append(p)
    rows.append(cur)

    ordered = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda p: p["cx"]))
    return ordered


def cut(rgb: np.ndarray, fg: np.ndarray, lab: np.ndarray, part: dict, pad: int):
    """Crop one part to its bbox, alpha'd to its OWN component so a neighbour
    that happens to fall inside the padded box does not come along with it."""
    h, w = fg.shape
    x0 = max(0, part["x0"] - pad)
    x1 = min(w, part["x1"] + pad)
    y0 = max(0, part["y0"] - pad)
    y1 = min(h, part["y1"] + pad)

    sub_rgb = rgb[y0:y1, x0:x1]
    mine = (lab[y0:y1, x0:x1] == part["label"])

    alpha = (mine * 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([sub_rgb, alpha]), "RGBA")
    # One-pixel feather: the flood fill produces a hard binary edge, which reads
    # as aliased stair-stepping once the part is rotated by the rig.
    a = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8))
    img.putalpha(a)
    return img, (x0, y0, x1, y1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("outdir")
    ap.add_argument("--parts", type=int, default=8)
    ap.add_argument("--pad", type=int, default=6)
    ap.add_argument("--names", default="", help="comma-separated part names, overriding the default body order")
    ap.add_argument("--neck-pivot", action="store_true",
                    help="pivot at the bottom neck stub instead of the top — for head/expression sheets")
    args = ap.parse_args()

    img = Image.open(args.sheet).convert("RGB")
    rgb = np.array(img)
    bg = background_mask(rgb)
    fg = ~bg
    lab, _ = ndimage.label(fg, structure=np.ones((3, 3), int))

    names = [n.strip() for n in args.names.split(",") if n.strip()] or PART_NAMES
    parts = find_parts(fg, args.parts)
    os.makedirs(args.outdir, exist_ok=True)

    print(f"sheet   : {os.path.basename(args.sheet)}  ({img.width}x{img.height})")
    print(f"parts   : found {len(parts)} (asked for {args.parts})")
    print()

    manifest = []
    for i, p in enumerate(parts):
        name = names[i] if i < len(names) else f"part_{i}"
        out, (x0, y0, x1, y1) = cut(rgb, fg, lab, p, args.pad)
        path = os.path.join(args.outdir, f"{name}.png")
        out.save(path)
        if args.neck_pivot:
            # A head hangs UP from its neck, so it pivots about the neck stub at
            # the BOTTOM — and on the stub's own centre, not the head's, because
            # the skull overhangs the neck on a three-quarter view.
            band = lab[max(0, p["y1"] - 24):p["y1"], x0:x1] == p["label"]
            cols = np.where(band.any(axis=0))[0]
            piv_x = float(cols.mean()) / out.width if len(cols) else 0.5
            piv_y = (p["y1"] - y0) / out.height - 0.02
        else:
            # A limb drawn hanging vertically pivots about the TOP-CENTRE of its
            # ink, which is what the rig's "angle 0 points down" convention needs.
            piv_x = (p["cx"] - x0) / out.width
            piv_y = (p["y0"] - y0) / out.height
        manifest.append({
            "name": name,
            "file": f"{name}.png",
            "w": out.width, "h": out.height,
            "pivot": [round(piv_x, 4), round(piv_y, 4)],
            "area": p["area"],
        })
        print(f"  {name:<10} {out.width:>4}x{out.height:<4}  pivot=({piv_x:.3f}, {piv_y:.3f})  area={p['area']}")

    stem = os.path.splitext(os.path.basename(args.sheet))[0]
    with open(os.path.join(args.outdir, f"manifest_{stem}.json"), "w", encoding="utf-8") as f:
        json.dump({"source": os.path.basename(args.sheet), "parts": manifest}, f, indent=2)
    print(f"\nwrote {len(manifest)} parts + manifest.json to {args.outdir}")


if __name__ == "__main__":
    main()
