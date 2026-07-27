"""Prove the character never overlaps any text or display object.

The owner's rule for the cam format: the character's space must never overlap
the panel, a caption, the timer, the chips, the lesson card, or the footer.
That is a geometry constraint over 1200 frames and ~25 poses, and eyeballing a
contact sheet misses it — the shipped v1 had his head over the panel's bottom
strip and nobody saw it until it was pointed out.

So it gets CHECKED. This script replicates the composition's placement maths
against the same staging file the composition imports
(remotion/src/fixtures/btc_reel/cam_staging.json), using the pose drawings'
REAL per-row ink profiles - not bounding boxes, which would flag a lean's empty
corner as a collision - and reports every frame where ink enters a UI lane.

Conservative on purpose:
  * drift is evaluated at its full travel including the action curve's 6%
    overshoot;
  * camDy is evaluated at both endpoints of its easing segment (every easing
    used is monotone, so the true value lies between them);
  * ink is inflated by the largest scale the snap/squash/breath stack can
    apply (+8% about the foot anchor) plus a 10px pad.

A clean run prints OK per lane. Any hit prints the frame, the pose, the lane
and the penetration in px. The loop rule: staging changes land in the JSON,
this runs, THEN the render happens.

Usage:
    python scripts/btc_reel/check_overlaps.py
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
STAGING = os.path.join(REPO, "remotion", "src", "fixtures", "btc_reel", "cam_staging.json")
ANCHORS = os.path.join(REPO, "remotion", "src", "fixtures", "meme_reel", "pose_anchors.json")
POSES = os.path.join(REPO, "remotion", "public", "meme_reel", "poses")

REF_INK = 686          # PoseCut's reference body height
ALPHA = 40             # what counts as ink
ROW_STEP = 3           # sample every 3rd row of the drawing
SCALE_INFLATE = 1.08   # snap 1.06 * breath * squash envelope
PAD = 10               # px, on top of everything else
OVERSHOOT = 1.06       # actionCurve's travel overshoot


def row_profiles(name):
    """Per-row [min_x, max_x] of ink, native resolution."""
    im = Image.open(os.path.join(POSES, f"{name}.png")).convert("RGBA")
    w, h = im.size
    px = im.load()
    rows = []
    for y in range(0, h, ROW_STEP):
        lo, hi = None, None
        for x in range(w):
            if px[x, y][3] > ALPHA:
                if lo is None:
                    lo = x
                hi = x
        rows.append((y, lo, hi))
    return {"w": w, "h": h, "rows": rows}


def cam_dy_range(frame, keys):
    """[min, max] possible camDy at this frame - easings are monotone, so the
    true value lies between the segment's endpoints."""
    if frame <= keys[0][0]:
        v = keys[0][1]
        return v, v
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if frame <= b[0]:
            return min(a[1], b[1]), max(a[1], b[1])
    v = keys[-1][1]
    return v, v


def main():
    st = json.load(open(STAGING))
    A = json.load(open(ANCHORS))
    cam = st["cam"]
    cuts = st["cuts"]
    lanes = st["lanes"]
    cap_windows = st["captionWindows"]

    profiles = {}
    for c in cuts:
        if c["pose"] not in profiles:
            profiles[c["pose"]] = row_profiles(c["pose"])

    def active(lane, frame):
        fr = lane["frames"]
        if fr == "captionWindows":
            return any(a <= frame < b for a, b in cap_windows)
        return fr[0] <= frame < fr[1]

    hits = {}
    for frame in range(0, 1200):
        # which cut
        cut = cuts[0]
        nxt_at = 1200
        for i, c in enumerate(cuts):
            if frame >= c["at"]:
                cut = c
                nxt_at = cuts[i + 1]["at"] if i + 1 < len(cuts) else 1200
        pose = cut["pose"]
        a = A[pose]
        prof = profiles[pose]
        dr = cut.get("drift", {})

        s = (cam["ink"] / REF_INK) * a["scale"] * SCALE_INFLATE
        w = prof["w"] * s
        h = prof["h"] * s

        # worst-case drift travel (with overshoot), applied fully
        dx = dr.get("dx", 0) * OVERSHOOT
        dy = dr.get("dy", 0) * OVERSHOOT

        dy_lo, dy_hi = cam_dy_range(frame, st["camDy"])

        for dy_cam in (dy_lo, dy_hi):
            foot_y = cam["footY"] + dy_cam + dy
            left = cam["footX"] + dx - a["anchor"][0] * w
            top = foot_y - a["anchor"][1] * h

            for lname, lane in lanes.items():
                if not active(lane, frame):
                    continue
                # rows of the drawing that intersect the lane's y band
                y0 = max(lane["y0"], top)
                y1 = min(lane["y1"], top + h, 1920)
                if y0 >= y1:
                    continue
                pen = 0.0
                for ry, lo, hi in prof["rows"]:
                    if lo is None:
                        continue
                    yy = top + ry * s
                    if yy < y0 or yy > y1:
                        continue
                    # facing='left' mirrors the drawing about its own box
                    m_lo = prof["w"] - hi
                    m_hi = prof["w"] - lo
                    ink_x0 = left + m_lo * s - PAD
                    ink_x1 = left + m_hi * s + PAD
                    if ink_x0 < lane["x1"] and ink_x1 > lane["x0"]:
                        pen = max(pen, min(lane["x1"], ink_x1) - max(lane["x0"], ink_x0))
                if pen > 0:
                    key = (lname, pose)
                    prev = hits.get(key)
                    if prev is None or pen > prev[2]:
                        hits[key] = (frame, pose, pen)

    if not hits:
        print("OK - no character/UI overlap anywhere in 1200 frames")
        return 0
    print(f"{len(hits)} lane/pose overlap classes:\n")
    for (lname, pose), (frame, _, pen) in sorted(hits.items(), key=lambda kv: -kv[1][2]):
        print(f"  {lname:8} x {pose:10} worst at frame {frame:4d}  penetration {pen:6.1f}px")
    return 1


if __name__ == "__main__":
    sys.exit(main())
