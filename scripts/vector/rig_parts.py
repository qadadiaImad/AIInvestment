"""Split a pose SVG into articulable body parts.

THE INSIGHT (owner's): a video is a series of images, so smooth motion is
an IMAGE-SUPPLY problem. The mistake was assuming the extra images have to
be generated. A vtracer pose is already 162 independent paths - the
drawings do not need to be re-drawn, they need to be ARTICULATED.

Group those paths by where they sit and you have cut-out animation: the
head bobs and tilts while the torso breathes and the arm gestures, every
in-between computed at render time. That yields INFINITE frames instead
of the 8 or 16 a generator gives, at zero cost, with identity guaranteed
because they are literally the same paths moved.

Why not OpenPose: it is trained on realistic proportions and this cast is
chibi - roughly three heads tall. Skeleton-driven generation pulls toward
realistic proportions, i.e. it fights the exact style the project spent a
session locking down. Generation keeps the job it is actually good at -
things that change SHAPE (mouths, expressions, hand poses) - which the
viseme system already covers.

Clustering is by ink position, using the pose's own head_focus anchor as
the reference point, so it adapts per drawing rather than assuming a
layout.

  python scripts/vector/rig_parts.py sol_point
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PUB = REPO / "remotion" / "public" / "characters" / "cast_ep1"
FIX = REPO / "remotion" / "src" / "fixtures" / "cast_ep1"
OUT = FIX / "rig_parts.json"

PATH_RE = re.compile(r'<path[^>]*?d="([^"]+)"[^>]*?/?>', re.S)
FILL_RE = re.compile(r'fill="(#[0-9A-Fa-f]{6})"')


def path_bbox(tag: str):
    """Bounding box in CANVAS space.

    Every vtracer path starts at "M0 0" and is placed by its own
    transform="translate(x,y)". Reading the d= numbers alone therefore
    puts every path at the origin - which is exactly what happened on
    the first run: 161 of 162 paths clustered into "head" because they
    all appeared to sit at the top-left. The translate has to be added
    back before anything can be grouped by position.
    """
    dm = re.search(r'd="([^"]+)"', tag)
    if not dm:
        return None
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", dm.group(1))]
    if len(nums) < 4:
        return None
    xs, ys = nums[0::2], nums[1::2]
    tx = ty = 0.0
    tm = re.search(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", tag)
    if tm:
        tx, ty = float(tm.group(1)), float(tm.group(2))
    return min(xs) + tx, min(ys) + ty, max(xs) + tx, max(ys) + ty


def main() -> None:
    pose = sys.argv[1] if len(sys.argv) > 1 else "sol_point"
    svg = (PUB / (pose + ".svg")).read_text("utf-8", errors="ignore")
    w = int(re.search(r'width="(\d+)"', svg).group(1))
    h = int(re.search(r'height="(\d+)"', svg).group(1))
    hf = json.loads((FIX / "head_focus.json").read_text("utf-8")).get(
        pose, {"fx": 0.5, "fy": 0.32})

    # every path with its bbox
    items = []
    for m in re.finditer(r"<path[^>]*>", svg):
        tag = m.group(0)
        bb = path_bbox(tag)
        if not bb:
            continue
        items.append({"tag": tag, "bbox": bb})

    # THE HEAD LINE. The head focus point marks the face centre; a chibi
    # head runs roughly from the crown to a little below that point, so
    # the neck sits near fy * 1.55. Derived from the pose's own anchor
    # rather than hard-coded, so it travels across drawings.
    neck = h * min(0.62, hf["fy"] * 1.62)
    midx = w * hf["fx"]
    hip_guess = h * 0.72

    # WHERE THE FEET START, measured off the pose's own alpha rather than
    # assumed. Scanning down the silhouette, the first row that resolves into
    # two separated runs is the crotch. On this cast that lands very low - Sol
    # is 0.938 of the way down, because his cardigan hangs to the shoe tops -
    # which is exactly why a leg-swing walk was never going to read on him and
    # a waddle is the honest cycle.
    crotch, foot_mid, feet_split = 0.93, 0.5, False
    rgba = REPO / ("content/vector_char/cast/ep_fairmarket/renders/_%s_rgba.png"
                   % pose)
    if rgba.exists():
        import numpy as np
        from PIL import Image
        a = np.array(Image.open(rgba).convert("RGBA"))[:, :, 3]
        H, W = a.shape

        def segments(y):
            idx = np.where(a[y] > 90)[0]
            if len(idx) == 0:
                return []
            cuts = np.where(np.diff(idx) > W * 0.02)[0]
            out, s = [], idx[0]
            for c in cuts:
                out.append((s, idx[c])); s = idx[c + 1]
            out.append((s, idx[-1]))
            return out

        # Constrained, because an unconstrained scan lies. Reading the first
        # row with two runs anywhere below mid-height found the gap between an
        # arm and the ribs and called it a crotch, at y=0.500. A leg split is
        # LOW, has exactly two runs, both of them substantial, and the gap
        # between them is narrow and roughly centred on the body.
        found = None
        for y in range(int(H * 0.80), int(H * 0.97)):
            seg = [s for s in segments(y) if s[1] - s[0] > W * 0.06]
            if len(seg) != 2:
                continue
            gap = seg[1][0] - seg[0][1]
            mid = (seg[0][1] + seg[1][0]) / 2 / W
            body = (seg[1][1] - seg[0][0]) / W
            if gap < W * 0.22 and abs(mid - 0.5) < 0.12 and body > 0.18:
                found = (y / H, mid)
                break
        if found:
            crotch, foot_mid, feet_split = found[0], found[1], True
            print("  crotch %.3f  foot split x %.3f  (measured)" % found)
        else:
            # No visible gap between the feet. Splitting a single connected
            # blob down the middle and moving the halves apart would TEAR it
            # on screen, so this pose waddles as one block instead.
            print("  feet not separable — waddle only (cut %.3f)" % crotch)

    # LEGS CANNOT BE CLUSTERED OUT, and pretending otherwise produced a walk
    # that did not walk. vtracer merges contiguous same-coloured regions, so
    # this cast's whole body silhouette is ONE path: for sol_point the largest
    # single path covers 97% of the frame and spans y 0.01-0.99. Sorting paths
    # by position can never split it, so legL/legR came out as fragments (1%
    # and 8%) and the "walk" was really just the bob and the arm swing.
    #
    # So the body ships as one `body` group and is CLIPPED into torso/legL/
    # legR at render time - three draws of the same artwork, each transformed
    # independently. See CharRig.
    groups = {"head": [], "body": [], "armL": [], "armR": []}
    for it in items:
        x0, y0, x1, y1 = it["bbox"]
        cy = (y0 + y1) / 2
        cx = (x0 + x1) / 2
        if cy < neck:
            groups["head"].append(it)
        elif cy < hip_guess and cx < midx - w * 0.17:
            groups["armL"].append(it)
        elif cy < hip_guess and cx > midx + w * 0.17:
            groups["armR"].append(it)
        else:
            groups["body"].append(it)

    # PIVOTS ARE MEASURED, NOT GUESSED. The first version used constants off
    # the head anchor, and an arm rotating about a made-up point does not
    # rotate about a shoulder: a -62 degree raise swung the pointing hand
    # clean past vertical and folded it into the hip.
    #
    # A joint sits at the edge of its part where that part meets the body:
    #   arm  -> top edge, INNER side (toward the spine)
    #   leg  -> top edge, centre
    #   head -> bottom edge, centre (the neck)
    #   torso-> bottom edge, centre (the hips, so a lean comes off the feet)
    def bounds(lst):
        xs0 = min(i["bbox"][0] for i in lst); ys0 = min(i["bbox"][1] for i in lst)
        xs1 = max(i["bbox"][2] for i in lst); ys1 = max(i["bbox"][3] for i in lst)
        return xs0, ys0, xs1, ys1

    def joint(name, lst):
        x0, y0, x1, y1 = bounds(lst)
        if name == "armL":                       # inner edge is its RIGHT
            return [x1 / w, y0 / h]
        if name == "armR":                       # inner edge is its LEFT
            return [x0 / w, y0 / h]
        if name == "head":
            return [(x0 + x1) / 2 / w, y1 / h]   # the neck
        return [(x0 + x1) / 2 / w, y1 / h]

    pivots = {n: joint(n, l) for n, l in groups.items() if l}
    # The cut is placed ABOVE the crotch and the torso is drawn over it, so
    # the straight edge is never on screen; a foot therefore swings about a
    # pivot the viewer cannot see, which is the whole trick.
    leg_cut = max(0.0, crotch - 0.045)
    pivots["torso"] = [midx / w, 0.995]           # lean comes off the floor
    pivots["legL"] = [foot_mid - 0.13, leg_cut]
    pivots["legR"] = [foot_mid + 0.13, leg_cut]

    header = svg[:svg.index(">", svg.index("<svg")) + 1]
    partdir = PUB / "parts"
    partdir.mkdir(exist_ok=True)
    manifest = {"w": w, "h": h, "pivots": pivots, "parts": {},
                "crotch": crotch, "legCut": leg_cut, "footMid": foot_mid,
                "feetSplit": feet_split}
    print("%s  %dx%d  neck y=%.0f  legCut=%.3f  %d paths"
          % (pose, w, h, neck, leg_cut, len(items)))
    for name, lst in groups.items():
        if not lst:
            print("  %-6s EMPTY" % name)
            continue
        body = "\n".join(i["tag"] for i in lst)
        p = partdir / ("%s__%s.svg" % (pose, name))
        p.write_text(header + "\n" + body + "\n</svg>", "utf-8")
        manifest["parts"][name] = "characters/cast_ep1/parts/%s__%s.svg" % (pose, name)
        print("  %-6s %3d paths -> %s" % (name, len(lst), p.name))

    all_m = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    all_m[pose] = manifest
    OUT.write_text(json.dumps(all_m, indent=1), "utf-8")
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
