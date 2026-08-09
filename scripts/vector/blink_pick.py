"""Eye-crop every blink candidate for a pose so it can be judged.

The blink pipeline generated candidates for sol_point, sol_point_v1 and
rex_listen across four rounds and then nobody selected one, so the assets
never reached visemes.json and those poses have been unable to blink ever
since - sol_point alone is a quarter of each episode's actor slots.

Judging a blink from the full 771x1159 drawing is hopeless; the eyes are a
few dozen pixels. This crops each candidate to its eye ellipse from
anchors_ep1.json and tiles them with the BASE drawing first, so "both eyes
closed" versus "a wink" versus "unchanged" is obvious at a glance.

  python scripts/vector/blink_pick.py sol_point
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
VIS = REPO / "content/vector_char/cast/ep_fairmarket/visemes"
ANCH = json.loads((VIS / "anchors_ep1.json").read_text("utf-8"))
PAD = 1.35        # show a little around the ellipse for context
SCALE = 3


def crop(img: Image.Image, pose: str) -> Image.Image:
    e = ANCH[pose]["eyes"]
    x0 = max(0, int(e["cx"] - e["rx"] * PAD))
    x1 = min(img.width, int(e["cx"] + e["rx"] * PAD))
    y0 = max(0, int(e["cy"] - e["ry"] * PAD * 1.6))
    y1 = min(img.height, int(e["cy"] + e["ry"] * PAD * 1.6))
    c = img.crop((x0, y0, x1, y1))
    return c.resize((c.width * SCALE // 2, c.height * SCALE // 2),
                    Image.LANCZOS)


def main() -> None:
    pose = sys.argv[1] if len(sys.argv) > 1 else "sol_point"
    base = VIS.parent / "poses" / (pose + ".png")
    if not base.exists():
        base = next(VIS.parent.rglob(pose + ".png"), None)
    items = []
    if base and base.exists():
        items.append(("BASE", Image.open(base).convert("RGB")))
    for p in sorted((VIS / "comp").glob(pose + "__blink__*.png")):
        if "eyecrop" in p.name:
            continue
        items.append((p.stem.split("__")[-1], Image.open(p).convert("RGB")))
    if not items:
        raise SystemExit("no candidates for " + pose)

    crops = [(lbl, crop(im, pose)) for lbl, im in items]
    cw = max(c.width for _, c in crops)
    ch = max(c.height for _, c in crops)
    cols = min(5, len(crops))
    rows = (len(crops) + cols - 1) // cols
    band = 22
    sheet = Image.new("RGB", (cols * cw, rows * (ch + band)), (12, 16, 26))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (lbl, c) in enumerate(crops):
        x, y = (i % cols) * cw, (i // cols) * (ch + band)
        d.text((x + 6, y + 5), lbl, fill=(124, 224, 162))
        sheet.paste(c, (x, y + band))
    out = VIS / ("_pick_" + pose + ".png")
    sheet.save(out)
    print("%d candidates -> %s" % (len(crops), out))


if __name__ == "__main__":
    main()
