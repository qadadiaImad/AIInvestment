"""Key, crop, vectorise and register a congress caricature as a pose.

Same treatment the cast drawings get, so a caricature can be staged,
reframed and moved by exactly the same machinery — which is the point:
she should act in the scene, not be pasted over it.
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from vector.cells import bg_to_alpha, compute_anchor, vectorize
from vector.visemes_ep1 import VIS, PUB, FIX, RENDERS

# (generated file stem, pose name registered in pose_anchors.json)
ADD = [
    ("c3_scheme_0", "congress_scheme"),
    ("c3_smug_0", "congress_smug"),
]


def main() -> None:
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    for stem, pose in ADD:
        rgb = np.asarray(Image.open(
            VIS.parent / "congress" / f"{stem}.png").convert("RGB"))
        rgba = bg_to_alpha(rgb, tol=42)
        ys, xs = np.nonzero(rgba[..., 3] > 0)
        pad = 8
        crop = rgba[max(0, ys.min() - pad):min(rgba.shape[0], ys.max() + pad),
                    max(0, xs.min() - pad):min(rgba.shape[1], xs.max() + pad)]
        out = RENDERS / f"_{pose}_rgba.png"
        Image.fromarray(crop).save(out)
        a = compute_anchor(crop)
        border = np.concatenate([crop[0, :, 3], crop[-1, :, 3],
                                 crop[:, 0, 3], crop[:, -1, 3]])
        print(f"{pose:18s} {a['w']}x{a['h']}  opaque "
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
