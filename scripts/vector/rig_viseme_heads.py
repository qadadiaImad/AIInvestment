"""Extract a head part from every viseme variant so a rigged character can
still talk.

THE COLLISION. The rig articulates a pose by splitting it into parts and
transforming each one. The mouth system articulates it by swapping the WHOLE
drawing for an inpainted variant with a different mouth. Do both naively and
they fight: swapping the whole drawing throws away the rig, and rigging off
the base pose throws away the mouth.

They compose once you notice the variants differ ONLY inside the mouth mask -
the viseme pipeline composited the generated region back onto the base, so
every pixel outside it is bit-identical, and all 66 files carry their base
pose's exact canvas dimensions (verified). So the body and arms can come from
the base pose while the HEAD comes from whichever variant the current frame
wants, and the two register perfectly because they are the same artwork.

Only the head is extracted; taking the whole variant would double-draw the
body and the static copy would show the moment an arm moved.

  python scripts/vector/rig_viseme_heads.py            # all poses
  python scripts/vector/rig_viseme_heads.py sol_point  # one
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PUB = REPO / "remotion" / "public" / "characters" / "cast_ep1"
FIX = REPO / "remotion" / "src" / "fixtures" / "cast_ep1"
MANIFEST = FIX / "rig_parts.json"


def path_bbox(tag: str):
    dm = re.search(r'd="([^"]+)"', tag)
    if not dm:
        return None
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", dm.group(1))]
    if len(nums) < 4:
        return None
    xs, ys = nums[0::2], nums[1::2]
    tm = re.search(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", tag)
    tx, ty = (float(tm.group(1)), float(tm.group(2))) if tm else (0.0, 0.0)
    return min(xs) + tx, min(ys) + ty, max(xs) + tx, max(ys) + ty


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    visemes = json.loads((FIX / "visemes.json").read_text("utf-8"))
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    hf_all = json.loads((FIX / "head_focus.json").read_text("utf-8"))
    partdir = PUB / "parts"
    partdir.mkdir(exist_ok=True)

    done = miss = 0
    for pose, variants in sorted(visemes.items()):
        if only and pose != only:
            continue
        rig = manifest.get(pose)
        if not rig:
            print("  %-18s no rig — skipped" % pose)
            miss += 1
            continue
        hf = hf_all.get(pose, {"fx": 0.5, "fy": 0.32})
        h = rig["h"]
        # the SAME neck line the base pose was split on, so the variant head
        # and the base body meet exactly where they did before
        neck = h * min(0.62, hf["fy"] * 1.62)
        kept = []
        for key, rel in sorted(variants.items()):
            if not rel:
                continue
            f = REPO / "remotion" / "public" / rel
            if not f.exists():
                continue
            svg = f.read_text("utf-8", errors="ignore")
            header = svg[: svg.index(">", svg.index("<svg")) + 1]
            head = []
            for m in re.finditer(r"<path[^>]*>", svg):
                bb = path_bbox(m.group(0))
                if not bb:
                    continue
                # same size rule as rig_parts: a path spanning the figure is
                # line art, not a head, and drawing it in the head layer
                # would paint over the whole body every talking frame
                if (bb[3] - bb[1]) > h * 0.55:
                    continue
                if (bb[2] - bb[0]) * (bb[3] - bb[1]) > rig["w"] * h * 0.30:
                    continue
                if (bb[1] + bb[3]) / 2 < neck:
                    head.append(m.group(0))
            if not head:
                continue
            name = "%s__v_%s" % (pose, key)
            (partdir / (name + ".svg")).write_text(
                header + "\n" + "\n".join(head) + "\n</svg>", "utf-8")
            rig["parts"]["head__" + key] = (
                "characters/cast_ep1/parts/%s.svg" % name)
            kept.append("%s:%d" % (key, len(head)))
        if kept:
            done += 1
            print("  %-18s %s" % (pose, "  ".join(kept)))

    MANIFEST.write_text(json.dumps(manifest, indent=1), "utf-8")
    print("\n%d poses given viseme heads, %d skipped -> %s"
          % (done, miss, MANIFEST))


if __name__ == "__main__":
    main()
