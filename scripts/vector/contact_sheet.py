"""Tile named PNGs into one labelled contact sheet.

Exists because the exhibit gate has to be VISUAL. The first exhibit pass
was reviewed as PROMPTS, passed, and then produced eight unusable images -
blob subjects, a collapsed palette, garbled fake-Japanese lettering baked
into two frames. Reading the prompt cannot catch any of that. So every art
pass now ends here, with agents looking at the actual pixels.

  python scripts/vector/contact_sheet.py OUT.png DIR name1 name2 ...
  python scripts/vector/contact_sheet.py OUT.png DIR          # all *.png
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

CELL_W = 340
BAND = 26
BG = (10, 14, 22)
INK = (124, 224, 162)


def build(out: Path, src: Path, names: list[str], cols: int = 4) -> Path:
    if not names:
        names = sorted(p.stem for p in src.glob("*.png")
                       if not p.stem.startswith("_"))
    imgs = []
    for n in names:
        p = src / (n + ".png")
        if not p.exists():
            print(f"  missing: {p}")
            continue
        im = Image.open(p).convert("RGB")
        h = max(1, round(CELL_W * im.height / im.width))
        imgs.append((n, im.resize((CELL_W, h), Image.LANCZOS)))
    if not imgs:
        raise SystemExit("no images")

    cell_h = max(im.height for _, im in imgs) + BAND
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * CELL_W, rows * cell_h), BG)
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(imgs):
        x, y = (i % cols) * CELL_W, (i // cols) * cell_h
        d.text((x + 8, y + 7), n, fill=INK)
        sheet.paste(im, (x, y + BAND))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"-> {out}  ({len(imgs)} cells, {sheet.width}x{sheet.height})")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:])
