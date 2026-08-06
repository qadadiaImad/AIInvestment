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


def _base_flat(pose: str):
    import numpy as np
    from PIL import Image

    p = (REPO / "content/vector_char/cast/ep_fairmarket/renders"
         / ("_%s_rgba.png" % pose))
    if not p.exists():
        return None, None
    b = np.asarray(Image.open(p).convert("RGBA")).astype(float)
    a = b[..., 3:4] / 255.0
    rgb = (b[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    return rgb, (b[..., 3] > 128)


def _palette(rgb, ink, k: int = 24):
    """The base drawing's own colours, most-used first.

    Flat cel art has a small true palette; everything else is antialiasing.
    Bucket at 16 levels per channel, take the top-k bucket means.
    """
    import numpy as np

    px = rgb[ink].astype(int)
    keys = (px[:, 0] >> 4) * 256 + (px[:, 1] >> 4) * 16 + (px[:, 2] >> 4)
    uniq, inv, cnt = np.unique(keys, return_inverse=True, return_counts=True)
    order = np.argsort(-cnt)[:k]
    return np.stack([px[inv == o].mean(axis=0) for o in order])


def _publish_processed(src: Path, dst: Path, base_rgb, pal,
                       erase_above: float | None) -> None:
    """Colour-lock a generated drawing to the base palette, and optionally
    erase its (base-identical) head so the head system stays the sole owner
    of that region.

    WHY. Each variant is an independent diffusion sample: outside the mask it
    is bit-exact, but INSIDE it the cardigan comes back a slightly different
    burgundy with different shading every time, so stepping between variants
    made the wardrobe pulse - the owner's "changes colors". Snapping every
    generated pixel to the nearest of the base's own 24 colours kills the
    hue drift outright (fold placement still varies, which reads as line
    boil - normal for drawn animation).

    The head erase exists because the torso draw is now UNCLIPPED at the top
    (the horizontal clip line was slicing raised hands off - "characters are
    cut"). Unclipped, the variant's embedded copy of the base head would sit
    static behind the rotating head part and show as a double image; erasing
    every unchanged pixel above the line removes the head while keeping any
    raised-hand ink, which is exactly the set of pixels that must survive.
    """
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    arr = np.asarray(Image.open(src).convert("RGBA")).copy()
    H = arr.shape[0]
    rgb = arr[..., :3].astype(int)
    diff = np.abs(rgb - base_rgb.astype(int)).max(axis=2)
    changed = ndimage.binary_dilation(diff > 26, iterations=3)

    if changed.any():
        px = rgb[changed].astype(float)
        d2 = ((px[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        arr[..., :3][changed] = pal[d2.argmin(axis=1)].astype(np.uint8)

    if erase_above is not None:
        y = int(erase_above * H)
        keep = changed[:y]
        arr[:y, :, 3] = np.where(keep, arr[:y, :, 3], 0)

    Image.fromarray(arr).save(dst)


def order_by_arm(d: Path, pose: str, names: list) -> list:
    """Order variants along the smoothest possible path between drawings.

    First attempt sorted by the mean height of the changed region, and it
    was a weak proxy: hiphand changes ink at the hip AND the shoulder, so
    its centroid lands mid-ladder while the hand reads low, and the sweep
    jumped. What actually needs minimising is the VISUAL step between
    consecutive drawings — so order them as the shortest Hamiltonian path
    over pairwise pixel distance, anchored at the variant nearest the base.
    Eight nodes is 5040 permutations: solved exactly, no heuristic.
    """
    import itertools

    import numpy as np
    from PIL import Image

    base_p = (REPO / "content/vector_char/cast/ep_fairmarket/renders"
              / ("_%s_rgba.png" % pose))
    if not base_p.exists() or len(names) > 9:
        return names
    b = np.asarray(Image.open(base_p).convert("RGBA")).astype(float)
    a = b[..., 3:4] / 255.0
    base = (b[..., :3] * a + 255 * (1 - a))[::4, ::4]
    imgs = [np.asarray(Image.open(d / (n + ".png")).convert("RGB")
                       ).astype(float)[::4, ::4] for n in names]
    n = len(imgs)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = np.abs(imgs[i] - imgs[j]).mean()
    start = int(np.argmin([np.abs(im - base).mean() for im in imgs]))
    rest = [i for i in range(n) if i != start]
    best, best_cost = None, 1e18
    for perm in itertools.permutations(rest):
        path = (start,) + perm
        cost = sum(D[path[k], path[k + 1]] for k in range(n - 1))
        if cost < best_cost:
            best, best_cost = path, cost
    return [names[i] for i in best]


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
        base_rgb, base_ink = _base_flat(pose)
        pal = _palette(base_rgb, base_ink) if base_rgb is not None else None
        # same underlap as the neck bands: the erased edge sits 14% above the
        # neck so the static body always fills the wedge a rotating head opens
        erase = max(0.0, rig.get("neck", 0.48) - 0.14)
        # A GESTURE ARC REPLACES THE VOCABULARY. The arc is one hand shape at
        # several positions; the vocabulary is eight different gestures.
        # Mixing them would reintroduce the hand-shape morphing the arc
        # exists to remove, so where an arc is APPROVED it IS the ladder.
        #
        # Approval is a whitelist, not a heuristic, because both heuristics
        # failed on inspection: rex_skeptic's arcs are same-seed clones (low
        # travel), and rex_eager's have HIGH travel precisely because the
        # inpaint deleted the tablet he holds in the base - an object that
        # would pop out of existence the moment the ladder starts. Only the
        # Sol point arcs hold one hand shape, real travel, and continuity.
        arc_d = d.parent.parent / "arcs" / pose
        if pose in ("sol_point", "sol_point_v1") and arc_d.exists()                 and list(arc_d.glob("arc*.png")):
            d = arc_d
        variants = []
        for png in sorted(d.glob("*.png")):
            if png.stem in ("contact_sheet",):
                continue
            dst = PUB / ("%s__%s.png" % (pose, png.stem))
            if pal is not None:
                _publish_processed(png, dst, base_rgb, pal, erase)
            else:
                shutil.copyfile(png, dst)
            rig["parts"]["body__" + png.stem] = (
                "characters/cast_ep1/poses/%s__%s.png" % (pose, png.stem))
            variants.append(png.stem)
            total += 1
        # ORDER THEM BY ARM HEIGHT, which is the difference between a move and
        # a shake. The renderer plays three drawings per action at offsets
        # -1/+1/0 in this list; alphabetical order (armscross, armsdown,
        # bothout, chinrub...) has nothing to do with where the arm IS, so
        # consecutive drawings were unrelated poses and the hand teleported
        # between them. Sorted by the centroid of what actually changed,
        # neighbours are neighbouring arm positions and the same three
        # offsets read as one continuous gesture.
        variants = order_by_arm(d, pose, variants)
        rig["variants"] = variants
        print("  %-16s %d variants  %s" % (pose, len(variants),
                                           " -> ".join(variants[:4]) + " ..."))

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
        base_rgb, base_ink = _base_flat(pose)
        pal = _palette(base_rgb, base_ink) if base_rgb is not None else None
        names = []
        for png in sorted(d.glob("*.png")):
            if png.stem == "contact_sheet":
                continue
            dst = PUB / ("%s__ex_%s.png" % (pose, png.stem))
            if pal is not None:
                # colour-locked like the body variants; no head erase — the
                # overlay is clipped to eyeBox, so it owns nothing else
                _publish_processed(png, dst, base_rgb, pal, None)
            else:
                shutil.copyfile(png, dst)
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
