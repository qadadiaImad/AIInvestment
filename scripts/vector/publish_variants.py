"""Publish generated pose variants into the Remotion public tree + manifest.

The variants are full-body PNGs pixel-aligned to their base pose, so they
drop straight into the rig's existing clip bands: the torso/feet bands read
from the VARIANT while the head band and the viseme still read from the
base. No re-vectorisation, no re-anchoring, and the head cannot drift
because it was never regenerated.

Arms are deliberately NOT drawn as separate parts in variant mode - the
variant already contains its own arms, and drawing the base pose's arm
clusters on top of them would give the character four.

  python scripts/vector/publish_variants.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
POSES = REPO / "content/vector_char/cast/ep_fairmarket/poses"
EXPR = REPO / "content/vector_char/cast/ep_fairmarket/expressions"
ANCHORS = REPO / ("content/vector_char/cast/ep_fairmarket/visemes/"
                  "anchors_ep1.json")
PUB = REPO / "remotion/public/characters/cast_ep1/poses"
MANIFEST = REPO / "remotion/src/fixtures/cast_ep1/rig_parts.json"


def main() -> None:
    m = json.loads(MANIFEST.read_text("utf-8"))
    PUB.mkdir(parents=True, exist_ok=True)
    total = 0
    for d in sorted(POSES.iterdir()):
        if not d.is_dir():
            continue
        pose = d.name
        rig = m.get(pose)
        if not rig:
            print("  %-16s no rig - skipped" % pose)
            continue
        variants = []
        for png in sorted(d.glob("*.png")):
            if png.stem in ("contact_sheet",):
                continue
            dst = PUB / ("%s__%s.png" % (pose, png.stem))
            shutil.copyfile(png, dst)
            rig["parts"]["body__" + png.stem] = (
                "characters/cast_ep1/poses/%s__%s.png" % (pose, png.stem))
            variants.append(png.stem)
            total += 1
        rig["variants"] = variants
        print("  %-16s %d variants" % (pose, len(variants)))

    # EXPRESSIONS. Published with the eye box they were generated inside, so
    # the renderer can clip the overlay to exactly the region that changed.
    # Outside that ellipse the drawing IS the base, so a rectangular clip
    # around it is safe and leaves no seam.
    anchors = json.loads(ANCHORS.read_text("utf-8")) if ANCHORS.exists() else {}
    ex = 0
    for d in sorted(EXPR.iterdir()) if EXPR.exists() else []:
        if not d.is_dir():
            continue
        pose, rig = d.name, m.get(d.name)
        if not rig or pose not in anchors:
            continue
        e = anchors[pose]["eyes"]
        W, H = anchors[pose]["canvas"]
        ry = e["ry"] * 1.55
        cy = e["cy"] - e["ry"] * 0.35
        rig["eyeBox"] = [max(0.0, (e["cx"] - e["rx"] * 1.15) / W),
                         max(0.0, (cy - ry * 1.1) / H),
                         min(1.0, (e["cx"] + e["rx"] * 1.15) / W),
                         min(1.0, (cy + ry * 1.1) / H)]
        names = []
        for png in sorted(d.glob("*.png")):
            if png.stem == "contact_sheet":
                continue
            shutil.copyfile(png, PUB / ("%s__ex_%s.png" % (pose, png.stem)))
            rig["parts"]["expr__" + png.stem] = (
                "characters/cast_ep1/poses/%s__ex_%s.png" % (pose, png.stem))
            names.append(png.stem)
            ex += 1
        rig["expressions"] = names
        print("  %-16s %d expressions" % (pose, len(names)))

    MANIFEST.write_text(json.dumps(m, indent=1), "utf-8")
    print("\n%d variant + %d expression drawings published -> %s"
          % (total, ex, PUB))


if __name__ == "__main__":
    main()
