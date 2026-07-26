"""Find the ground-contact anchor of each drawn key pose.

Pose-to-pose animation cuts between whole DRAWINGS rather than rotating rigid
parts. That removes every cutout-rig artefact at a stroke — no pivots, no joint
limits, no sliding feet, no detached hands — because each pose is a complete,
correctly-deformed drawing.

The one thing it introduces is a registration problem: if the drawings are not
aligned to a common point, the character JUMPS on every cut. Aligning on the
bounding box is wrong, because a pose that throws its arms up has a taller box
and would sink; a pose that reaches sideways has a wider box and would slide.

The correct anchor is the GROUND CONTACT: the bottom of the ink, and the
horizontal centre of only the ink NEAR that bottom — i.e. the feet, not the
whole silhouette. Everything else about the drawing is then free to change.

Usage:
    python scripts/meme_reel/pose_anchors.py <posedir>
"""
import json
import os
import sys

import numpy as np
from PIL import Image

# Fraction of the ink's height, measured from the bottom, that counts as "the
# feet" for the purpose of finding the horizontal anchor.
FOOT_BAND = 0.07


def anchor(path: str):
    im = Image.open(path).convert("RGBA")
    a = np.array(im)[:, :, 3]
    ink = a > 40
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    if len(rows) == 0:
        return None
    y0, y1 = int(rows[0]), int(rows[-1])
    x0, x1 = int(cols[0]), int(cols[-1])
    h = y1 - y0 + 1

    band_top = max(y0, y1 - int(h * FOOT_BAND))
    band = ink[band_top : y1 + 1, :]
    bcols = np.where(band.any(axis=0))[0]
    # Centre of the FEET, not of the whole silhouette.
    ax = float(bcols.mean()) if len(bcols) else (x0 + x1) / 2.0

    return {
        "w": im.width,
        "h": im.height,
        "ink": [x0, y0, x1, y1],
        # normalised into the image, which is what the composition consumes
        "anchor": [round(ax / im.width, 5), round((y1 + 1) / im.height, 5)],
        "ink_h": h,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    d = sys.argv[1]
    names = [f[:-4] for f in sorted(os.listdir(d)) if f.endswith(".png")]

    out = {}
    print(f"\nground anchors in {d}\n")
    heights = {}
    for n in names:
        a = anchor(os.path.join(d, n + ".png"))
        if not a:
            continue
        out[n] = a
        heights[n] = a["ink_h"]
        print(f"  {n:<10} {a['w']:>4}x{a['h']:<4}  anchor=({a['anchor'][0]:.3f}, {a['anchor'][1]:.3f})  ink height {a['ink_h']}")

    # Every pose must be scaled so the CHARACTER is the same size in each,
    # otherwise he grows and shrinks on every cut. Use the median standing
    # height as the reference and report the correction each pose needs.
    body = {k: v for k, v in heights.items() if k != "hero"}
    ref = float(np.median(list(body.values())))
    print(f"\n  reference ink height (median of the poses): {ref:.0f}px")
    print("  per-pose scale correction so he never changes size on a cut:\n")
    # A correction has to distinguish two very different things:
    #   * the drawing was rendered at a different RESOLUTION (a hero figure
    #     drawn twice as large) — that must be corrected in full;
    #   * the POSE is genuinely lower than standing (a crouch, a deep bend) —
    #     that must NOT be corrected, because scaling a crouch up to standing
    #     height is exactly undoing the pose.
    # Anything within +-40% is treated as pose variation and only lightly
    # trimmed; a gross outlier is treated as a resolution difference.
    for n in sorted(body):
        raw = ref / heights[n]
        if raw < 0.7 or raw > 1.4:
            s = raw                      # resolution difference — correct fully
            note = "  <-- resolution"
        else:
            s = max(0.95, min(1.05, raw))  # pose difference — barely touch it
            note = "  (pose, clamped)" if abs(raw - s) > 1e-6 else ""
        out[n]["scale"] = round(s, 5)
        print(f"    {n:<10} x{s:.3f}   raw {raw:.3f}{note}")
    if "hero" in out:
        out["hero"]["scale"] = round(ref / heights["hero"], 5)

    with open(os.path.join(d, "anchors.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  wrote {os.path.join(d, 'anchors.json')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
