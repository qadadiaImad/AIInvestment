"""Put two renders side by side at matched timestamps.

The fluidity work is judged by comparison, not by description — and a
still cannot show motion, so this samples PAIRS of adjacent frames around
each sample point and stacks them, which at least reveals whether
anything is moving during a hold (identical pair = parked drawing).

Usage:
  python -m vector.compare_renders <before.mp4> <after.mp4> <out.png> [t ...]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from vector.visemes_ep1 import EP, _font
from vector.continuity_probe import FF

FPS = 30
# seconds to sample: one inside each act, biased to held shots
DEFAULT_TS = [1.6, 5.4, 13.6, 17.8, 26.0, 31.5, 40.0, 48.5]


def grab(video: Path, t: float, out: Path) -> Path:
    subprocess.run([str(FF), "-v", "error", "-i", str(video),
                    "-ss", f"{t:.4f}", "-frames:v", "1", str(out), "-y"],
                   check=True)
    return out


def main(before: str, after: str, out_path: str, ts: list[float]) -> None:
    tmp = EP / "compare_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    cols = []
    for t in ts:
        col = []
        for tag, vid in (("v16 before", before), ("v17 after", after)):
            # two frames 4 apart: if a hold is alive they differ
            a = grab(Path(vid), t, tmp / f"{tag[:3]}_{t}_a.png")
            b = grab(Path(vid), t + 4 / FPS, tmp / f"{tag[:3]}_{t}_b.png")
            ims = [Image.open(p).convert("RGB") for p in (a, b)]
            s = 300 / ims[0].height
            ims = [im.resize((int(im.width * s), 300)) for im in ims]
            pair = Image.new("RGB", (ims[0].width * 2 + 4, 300), "white")
            pair.paste(ims[0], (0, 0))
            pair.paste(ims[1], (ims[0].width + 4, 0))
            tile = Image.new("RGB", (pair.width, 300 + 26), "white")
            tile.paste(pair, (0, 26))
            ImageDraw.Draw(tile).text((3, 4), f"{tag}  t={t}s",
                                      fill="black", font=_font(15))
            col.append(tile)
        stack = Image.new("RGB", (col[0].width, sum(c.height for c in col) + 8),
                          "white")
        y = 0
        for c in col:
            stack.paste(c, (0, y))
            y += c.height + 8
        cols.append(stack)

    w = sum(c.width + 8 for c in cols)
    sheet = Image.new("RGB", (w, cols[0].height), "white")
    x = 0
    for c in cols:
        sheet.paste(c, (x, 0))
        x += c.width + 8
    sheet.save(out_path)
    print(f"wrote {out_path}")
    print("each cell is two frames 4 apart — identical pair means the "
          "drawing is parked, different means the hold is alive")


if __name__ == "__main__":
    args = sys.argv[1:]
    times = [float(a) for a in args[3:]] or DEFAULT_TS
    main(args[0], args[1], args[2], times)
