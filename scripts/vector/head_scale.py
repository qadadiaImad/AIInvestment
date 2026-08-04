"""Report how big each character's HEAD lands on screen for a given staging.

Matching two characters by ink height does not match how big they read:
these drawings have different head-to-body ratios, so a crouching figure
staged at 75% of another's height can still have a head half the size,
and the taller one reads as "zoomed in more". This measures the actual
head box per pose and scales it by the staging, which is the number to
equalise.

Usage:  python -m vector.head_scale
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from vector.visemes_ep1 import RENDERS, FIX, detect_face

# (pose, staged h, kind) as the composition stages them
STAGED = [
    ("sol_laugh", 770, "full"),         # b195, paired with rex_skeptic
    ("rex_skeptic", 1040, "full"),
    ("rex_listen", 1120, "full"),       # b255, paired with sol_finger
    ("sol_finger", 1000, "full"),
    ("rex_eager", 1000, "full"),        # b110, paired with sol_point_v1
    ("sol_point_v1", 780, "full"),
    ("sol_smug_v1", 700, "bust"),       # b895 pop-in
    ("sol_point", 800, "full"),
]


def main() -> None:
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    print(f"{'pose':15s} {'staged':>7s} {'headpx':>8s} {'scale':>7s} "
          f"{'ON-SCREEN HEAD':>15s}")
    for pose, h, kind in STAGED:
        rgba = np.asarray(Image.open(
            RENDERS / f"_{pose}_rgba.png").convert("RGBA"))
        d = anchors[pose]
        try:
            x0, y0, x1, y1 = detect_face(rgba)
        except Exception as exc:            # noqa: BLE001
            print(f"{pose:15s} head detect failed: {exc}")
            continue
        hw, hh = x1 - x0, y1 - y0
        scale = h / (d["ink_h"] if kind == "full" else d["h"])
        print(f"{pose:15s} {h:7d} {hw:4d}x{hh:<3d} {scale:7.3f} "
              f"{hw * scale:7.0f}x{hh * scale:<7.0f}")


if __name__ == "__main__":
    main()
