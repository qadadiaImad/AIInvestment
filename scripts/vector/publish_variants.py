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
    MANIFEST.write_text(json.dumps(m, indent=1), "utf-8")
    print("\n%d variant drawings published -> %s" % (total, PUB))


if __name__ == "__main__":
    main()
