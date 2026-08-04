"""Re-key the pose drawings whose background was never removed.

Eight ep1 poses composited as a visible white rectangle over the scene:
`bg_to_alpha` samples the four corner patches for the background colour,
which fails on tight bust closeups where hair/skin reaches the corners.
`white_bg_to_alpha` keys border-connected near-white instead.

Alpha only -- the canvas is NOT re-cropped, so every viseme SVG already
generated for these poses stays pixel-aligned. Downstream this refreshes
each affected pose's base SVG, its viseme composites + SVGs, and its
pose_anchors entry (ink_h/anchor were measuring the white box, so
sol_shrug was also being scaled and placed wrong).
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from vector.cells import white_bg_to_alpha, compute_anchor, vectorize
from vector.visemes_ep1 import RENDERS, VIS, PUB, FIX


def affected() -> list[str]:
    out = []
    for p in sorted(RENDERS.glob("_*_rgba.png")):
        a = np.asarray(Image.open(p).convert("RGBA"))[..., 3]
        if a[0, 0] or a[0, -1] or a[-1, 0] or a[-1, -1]:
            out.append(p.stem[1:-5])
    return out


def main() -> None:
    poses = affected()
    print(f"re-keying {len(poses)}: {poses}")
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    visemes = json.loads((FIX / "visemes.json").read_text("utf-8"))
    picks = json.loads((VIS / "picks_final.json").read_text("utf-8"))
    for pose in poses:
        src = RENDERS / f"_{pose}_rgba.png"
        old = np.asarray(Image.open(src).convert("RGBA"))
        rgba = white_bg_to_alpha(old[..., :3])
        assert rgba.shape == old.shape, "canvas must not change"
        Image.fromarray(rgba).save(src)
        frac = (rgba[..., 3] > 0).mean()
        # base SVG
        if pose in anchors:
            vectorize(src, PUB / f"{pose}.svg")
            a = compute_anchor(rgba)
            anchors[pose].update(w=a["w"], h=a["h"], ink_h=a["ink_h"],
                                 anchor=a["anchor"])
        # viseme composites + SVGs (RGB already correct; alpha changed)
        n_vis = 0
        for vis, cand in picks.get(pose, {}).items():
            comp = VIS / "comp" / f"{cand}.png"
            rgb = np.asarray(Image.open(comp).convert("RGB"))
            out = np.dstack([rgb, rgba[..., 3]])
            Image.fromarray(out).save(comp)
            if pose in visemes and vis in visemes[pose]:
                vectorize(comp, PUB / "visemes" / f"{pose}__{vis}.svg")
                n_vis += 1
        print(f"  {pose}: opaque {frac:.3f}, {n_vis} visemes re-traced")
    (FIX / "pose_anchors.json").write_text(json.dumps(anchors, indent=1),
                                           "utf-8")
    print(f"updated {FIX / 'pose_anchors.json'}")


if __name__ == "__main__":
    main()
