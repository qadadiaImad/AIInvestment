"""Assembly view of the FairMarketEp1 cut — the editor's artifact.

One representative frame per beat, laid out in cut order and annotated
with the pose used, how tall the figure stands on screen (the shot-size
proxy the composition actually controls) and how long the beat holds.
Reading the strip left to right shows the rhythm: repeated shot sizes,
repeated drawings and dead holds are visible here without rendering
forensics on the finished file.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from vector.visemes_ep1 import EP, FIX, _font
from vector.continuity_probe import FF
import json

FRAME_H = 1920

# One row per SHOT, not per beat — a reframe of the same drawing is a
# new shot. (start frame, poses, kind, staged h, k, label)
CUT = [
    (0,    ["sol_smug_v1"],              "bust",    760,  1.00, "SOL intro"),
    (56,   ["sol_smug_v1"],              "bust",    760,  1.50, "  push"),
    (110,  ["rex_eager"],                "full",    1090, 1.00, "REX fundamentals"),
    (170,  ["rex_eager"],                "full",    1090, 1.30, "  push"),
    (195,  ["sol_laugh"],                "full",    1270, 1.00, "SOL HA!"),
    (255,  ["sol_finger", "rex_listen"], "full",    1000, 1.00, "SOL politics 2-shot"),
    (281,  ["sol_finger"],               "full",    1000, 1.50, "  SOL isolated"),
    (327,  ["sol_finger", "rex_listen"], "full",    1000, 1.00, "  back to 2-shot"),
    (345,  ["rex_shock"],                "closeup", 1920, 1.00, "REX WHAT?!"),
    (400,  ["sol_point"],                "full",    800,  1.00, "SOL exhibit + card"),
    (458,  ["sol_point"],                "full",    800,  3.00, "  CU, card out"),
    (523,  ["sol_point"],                "full",    800,  1.00, "  back to card"),
    (590,  ["sol_point"],                "full",    800,  2.20, "  kicker CU"),
    (640,  ["rex_shock_v1"],             "panel",   620,  1.00, "REX an INDEX?!"),
    (687,  ["rex_shock_v1"],             "panel",   620,  1.45, "  push"),
    (740,  ["sol_smug_v1"],              "bust",    1250, 1.00, "SOL all legal"),
    (804,  ["sol_smug_v1"],              "bust",    1250, 1.35, "  push"),
    (859,  ["sol_smug_v1"],              "bust",    1250, 1.00, "  out"),
    (895,  ["rex_eager"],                "full",    1000, 1.35, "REX filings"),
    (955,  ["sol_wink"],                 "panel",   560,  1.90, "SOL reverse"),
    (1015, [],                           "full",    0,    1.00, "outro"),
]


def figure_height(pose: str, kind: str, h: int, anchors: dict) -> float:
    """On-screen ink height in px for this beat's staging."""
    d = anchors[pose]
    if kind == "full":
        return h
    if kind == "closeup":
        s = 1.04 * max(1080 / d["w"], FRAME_H / d["h"])
        return d["ink_h"] * s
    return h * (d["ink_h"] / d["h"])       # bust / panel scale by canvas


def main(video: Path, out: Path) -> None:
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    tmp = EP / "cut_frames"
    tmp.mkdir(parents=True, exist_ok=True)
    tiles = []
    for i, (at, poses, kind, h, k, label) in enumerate(CUT[:-1]):
        nxt = CUT[i + 1][0]
        mid = at + (nxt - at) // 2
        p = tmp / f"cut_{mid:04d}.png"
        if not p.exists():
            subprocess.run([str(FF), "-v", "error", "-i", str(video),
                            "-ss", f"{(mid + 0.5) / 30:.4f}", "-frames:v", "1",
                            str(p), "-y"], check=True)
        fh = figure_height(poses[0], kind, h, anchors) * k
        pct = 100 * fh / FRAME_H
        secs = (nxt - at) / 30
        im = Image.open(p).convert("RGB")
        s = 620 / im.height
        im = im.resize((int(im.width * s), 620))
        tile = Image.new("RGB", (im.width + 8, 620 + 92), "white")
        tile.paste(im, (4, 84))
        d = ImageDraw.Draw(tile)
        d.text((6, 4), f"{i + 1}. {label}", fill="black", font=_font(21))
        d.text((6, 28), f"{'+'.join(poses)}  [{kind}]", fill=(150, 30, 30),
               font=_font(17))
        d.text((6, 50), f"figure {pct:.0f}% of frame   hold {secs:.1f}s",
               fill=(20, 90, 190), font=_font(18))
        tiles.append((tile, pct, secs, poses[0], kind))
    w = sum(t[0].width for t in tiles)
    sheet = Image.new("RGB", (w, tiles[0][0].height), "white")
    x = 0
    for t, *_ in tiles:
        sheet.paste(t, (x, 0))
        x += t.width
    sheet.save(out)
    print(f"wrote {out}\n")
    total = CUT[-1][0] / 30
    print(f"{len(tiles)} shots in {total:.1f}s = one cut every "
          f"{total / len(tiles):.1f}s\n")
    print(f"{'#':>2} {'shot':24s} {'pose':16s} {'shot%':>6s} {'hold':>6s}")
    for i, (_, pct, secs, pose, kind) in enumerate(tiles, 1):
        flag = "  <-- LONG" if secs >= 4 else ""
        print(f"{i:>2} {CUT[i-1][5]:24s} {pose:16s} {pct:6.0f} "
              f"{secs:6.1f}{flag}")
    # A small size change only reads as a jump cut when the SUBJECT is
    # unchanged; cutting to the other character is a new subject and needs
    # no size contrast at all.
    print("\nshot-size deltas between consecutive cuts:")
    for i in range(1, len(tiles)):
        d_pct = abs(tiles[i][1] - tiles[i - 1][1])
        same = tiles[i][3] == tiles[i - 1][3]
        flag = "  <-- JUMP CUT (same drawing, <12% size change)" \
            if same and d_pct < 12 else ("" if same else "   (new subject)")
        print(f"  cut {i}->{i+1}: {tiles[i-1][1]:5.0f}% -> "
              f"{tiles[i][1]:5.0f}%   delta {d_pct:4.0f}{flag}")
    seen = {}
    print("\ndrawings reused across shots (fine when the framing differs):")
    for i, (_, _, _, pose, _) in enumerate(tiles, 1):
        seen.setdefault(pose, []).append(i)
    for pose, at in seen.items():
        if len(at) > 1:
            print(f"  {pose}: shots {at}")

    vis = json.loads((FIX / "visemes.json").read_text("utf-8"))
    print("\nmouth/blink coverage of the drawings in the cut:")
    for pose in sorted(seen):
        v = vis.get(pose, {})
        mouths = [k for k in ("closed", "half", "open", "oh") if k in v]
        note = ",".join(mouths) if mouths else "NONE - mouth is frozen"
        print(f"  {pose:16s} {note:30s} blink: "
              f"{'yes' if 'blink' in v else 'NO'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), EP / f"cut_sheet_{sys.argv[2]}.png")
