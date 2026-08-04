"""Key, crop, vectorise and register a congress caricature as a pose.

Same treatment the cast drawings get, so a caricature can be staged,
reframed and moved by exactly the same machinery — which is the point:
she should act in the scene, not be pasted over it.

Usage:
  python -m vector.add_congress                       # the default pair
  python -m vector.add_congress congress2b:c5_scheme_0:congress2_scheme ...
"""
from __future__ import annotations

import json
import sys

import numpy as np
from PIL import Image

from vector.cells import (bg_to_alpha, compute_anchor, vectorize,
                          white_bg_to_alpha)
from vector.visemes_ep1 import VIS, PUB, FIX, RENDERS

# (source dir, generated file stem, pose name in pose_anchors.json)
ADD = [
    ("congress", "c3_scheme_0", "congress_scheme"),
    ("congress", "c3_smug_0", "congress_smug"),
]
if len(sys.argv) > 1:
    ADD = [tuple(a.split(":")) for a in sys.argv[1:]]


def key(rgb: np.ndarray) -> tuple[np.ndarray, str]:
    """Key the background, MEASURING the result instead of trusting it.

    bg_to_alpha takes the background colour from the four corner patches,
    which fails whenever the figure occupies two of them: on a
    shoulders-to-the-edge bust the median lands between the pale wall and
    the dark suit, matches neither, and nothing is keyed at all. That is
    not a visible failure downstream — the pose just composites as an
    opaque rectangle over the scene.

    So try each keyer and keep the first whose result actually looks
    keyed: mostly-transparent border, and not so aggressive that the
    figure itself is eaten.
    """
    attempts = [("corner", lambda: bg_to_alpha(rgb, tol=42)),
                ("corner+", lambda: bg_to_alpha(rgb, tol=64)),
                ("white", lambda: white_bg_to_alpha(rgb, thresh=226)),
                ("white-", lambda: white_bg_to_alpha(rgb, thresh=200))]
    best, best_name, best_ink = None, "none", 2.0
    for name, fn in attempts:
        a = fn()[..., 3]
        border = np.concatenate([a[0, :], a[-1, :], a[:, 0], a[:, -1]])
        ink = float((border > 0).mean())
        opaque = float((a > 0).mean())
        if ink < best_ink and opaque > 0.15:
            best, best_name, best_ink = fn(), name, ink
        if ink < 0.02 and opaque > 0.2:
            return fn(), name
    if best is None:
        raise SystemExit("every keying strategy failed")
    return best, best_name


def main() -> None:
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    for src_dir, stem, pose in ADD:
        rgb = np.asarray(Image.open(
            VIS.parent / src_dir / f"{stem}.png").convert("RGB"))
        rgba, how = key(rgb)
        ys, xs = np.nonzero(rgba[..., 3] > 0)
        pad = 8
        crop = rgba[max(0, ys.min() - pad):min(rgba.shape[0], ys.max() + pad),
                    max(0, xs.min() - pad):min(rgba.shape[1], xs.max() + pad)]
        out = RENDERS / f"_{pose}_rgba.png"
        Image.fromarray(crop).save(out)
        a = compute_anchor(crop)
        border = np.concatenate([crop[0, :, 3], crop[-1, :, 3],
                                 crop[:, 0, 3], crop[:, -1, 3]])
        print(f"{pose:18s} {a['w']}x{a['h']}  key={how:7s} opaque "
              f"{(crop[..., 3] > 0).mean():.2f}  border ink "
              f"{(border > 0).mean():.3f}")
        vectorize(out, PUB / f"{pose}.svg", detail=True)
        anchors[pose] = {**a, "src": f"characters/cast_ep1/{pose}.svg",
                         "scale": 1.0}
    (FIX / "pose_anchors.json").write_text(json.dumps(anchors, indent=1),
                                           "utf-8")
    print(f"registered {len(ADD)} caricature poses")


if __name__ == "__main__":
    main()
