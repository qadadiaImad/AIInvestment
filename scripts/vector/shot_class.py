"""Classify each pose drawing by how much of its ink touches the canvas
edge. A full-bleed drawing (head cropped by the canvas on several sides)
cannot float over the scene background -- the canvas boundary reads as a
hard straight cut across the character. Those poses must either be scaled
past the visible area (a true closeup) or not used."""
from __future__ import annotations

import numpy as np
from PIL import Image

from vector.visemes_ep1 import RENDERS


def border_ink(pose: str) -> float:
    a = np.asarray(Image.open(
        RENDERS / f"_{pose}_rgba.png").convert("RGBA"))[..., 3] > 0
    return float(np.concatenate(
        [a[0, :], a[-1, :], a[:, 0], a[:, -1]]).mean())


def verdict(f: float) -> str:
    if f > 0.5:
        return "FULL-BLEED (clips)"
    if f > 0.15:
        return "partial clip"
    return "clean silhouette"


def main() -> None:
    rows = [(p.stem[1:-5], border_ink(p.stem[1:-5]))
            for p in sorted(RENDERS.glob("_*_rgba.png"))]
    print(f"{'pose':24s} {'border_ink':>10s}  verdict")
    for n, f in sorted(rows, key=lambda r: -r[1]):
        print(f"{n:24s} {f:10.3f}  {verdict(f)}")


if __name__ == "__main__":
    main()
