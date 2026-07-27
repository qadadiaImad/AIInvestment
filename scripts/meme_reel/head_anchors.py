"""Measure where the HEAD is in each pose drawing.

Character-anchored effects - sweat beads, an impact burst, a thought bubble -
have to sit at the head, and the head is not in the same place twice. Between
`idle` and `crouch` in this sheet it travels most of the body's height and a
third of its width. A single anchor derived from the standing figure puts the
sweat in empty wall the moment he bends, which is exactly what the first cut
did.

So it gets measured per drawing, the same way the ground contact already is
(pose_anchors.py):

  vertical    the top of the ink, plus a fixed fraction of head height. The
              topmost ink in every pose here IS the skull, except in the two
              poses where a raised hand is higher - which is why the band is
              taken from the WIDEST contiguous run of ink near the top rather
              than from the single highest pixel. A hand is narrow; a head is
              not.
  horizontal  the centroid of alpha inside that band. Using the whole
              drawing's centre would drag the anchor toward whichever side the
              arms are on.

Output is a fraction of the drawing's own box, so it survives any scaling, and
is consumed through PoseCut's `poseHead()` which also applies the mirror.

Usage:
    python scripts/meme_reel/head_anchors.py
"""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
POSES = os.path.join(REPO, "remotion", "public", "meme_reel", "poses")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "meme_reel", "head_anchors.json")

ALPHA = 40          # what counts as ink
BAND = 0.16         # fraction of ink height searched for the skull
HEAD_DROP = 0.55    # head CENTRE, as a fraction of the band below its top


def rows_with_ink(px, w, h):
    out = []
    for y in range(h):
        run = best = 0
        first = None
        for x in range(w):
            if px[x, y][3] > ALPHA:
                if first is None:
                    first = x
                run += 1
                best = max(best, run)
            else:
                run = 0
        out.append((y, best))
    return out


def main():
    result = {}
    for fn in sorted(os.listdir(POSES)):
        if not fn.endswith(".png"):
            continue
        name = fn[:-4]
        im = Image.open(os.path.join(POSES, fn)).convert("RGBA")
        w, h = im.size
        px = im.load()

        rows = rows_with_ink(px, w, h)
        inked = [y for y, run in rows if run > 0]
        if not inked:
            continue
        top, bot = min(inked), max(inked)
        ink_h = bot - top

        # The skull is the widest run in the top band - a raised hand is narrow
        # and would otherwise win on height alone.
        band_lo, band_hi = top, top + int(ink_h * BAND)
        widths = [(run, y) for y, run in rows if band_lo <= y <= band_hi]
        head_w, _ = max(widths) if widths else (0, top)
        # first row in the band that is at least 60% of the widest - the crown
        crown = next((y for y, run in rows if band_lo <= y <= band_hi and run >= head_w * 0.6), top)

        hy = crown + ink_h * BAND * HEAD_DROP

        # horizontal centroid of ink across the head band only
        lo, hi = int(crown), int(min(bot, crown + ink_h * BAND))
        tot = 0
        acc = 0.0
        for y in range(lo, hi + 1):
            for x in range(w):
                if px[x, y][3] > ALPHA:
                    acc += x
                    tot += 1
        hx = (acc / tot) if tot else w / 2

        result[name] = {
            "head": [round(hx / w, 5), round(hy / h, 5)],
            "head_w": round(head_w / w, 5),
        }
        print(f"  {name:10} head at ({hx / w:.3f}, {hy / h:.3f})  width {head_w / w:.3f}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w"), indent=1)
    print(f"\n-> {os.path.relpath(OUT, REPO)}  ({len(result)} poses)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
