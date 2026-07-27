"""Measure the room's floor plane and desk geometry from the plate.

The character has to look like he is standing IN the room, not pasted on top of
a picture of one. That is decided entirely at the placement stage: feet on the
real floor, height consistent with a real desk, eye-line consistent with the
room's camera. All three come from numbers that are in the plate already, so
they get measured rather than nudged until it "looks about right".

What is measured, and how:

  wall/floor junction  The skirting board is the lightest horizontal band in the
                       lower half of a wall-only column. Scanning a column clear
                       of the desk, it is the row where luminance jumps up (wall
                       -> white skirting) then drops hard (skirting -> wood).
  desk top surface     In a column through the desk, the first strong downward
                       luminance step below the monitor.
  desk foot contact    In the same column, the lowest row still belonging to the
                       desk's dark wood before the lighter floor resumes.

From those three the character's scale follows from one real-world ratio: a desk
is about 75cm and an adult about 175cm, so

    character_px = (desk_foot_y - desk_top_y) * (175 / 75)

which is a measurement, not a taste call. Standing depth is the desk's own foot
line, because that is the one depth in the plate whose floor position is known.

Usage:
    python scripts/meme_reel/measure_floor_plane.py remotion/public/meme_reel/room_plate.png
"""
import json
import os
import sys

from PIL import Image

COMP_W, COMP_H = 1080, 1920

DESK_H_CM = 75.0
ADULT_H_CM = 175.0


def column(px, x, y0, y1):
    return [sum(px[x, y][:3]) / 3.0 for y in range(y0, y1)]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "remotion/public/meme_reel/room_plate.png"
    img = Image.open(path).convert("RGB")
    W, H = img.size
    px = img.load()
    sx, sy = W / COMP_W, H / COMP_H

    # --- wall/floor junction, from a column on the clear right-hand wall ------
    xr = int(W * 0.80)
    lum = column(px, xr, int(H * 0.45), H - 1)
    y0 = int(H * 0.45)
    # The skirting is a bright band; find the strongest bright->dark step after it.
    best, best_d = None, 0.0
    for i in range(6, len(lum) - 6):
        before = sum(lum[i - 6:i]) / 6
        after = sum(lum[i:i + 6]) / 6
        d = before - after
        if d > best_d:
            best_d, best = d, y0 + i
    wall_floor_y = best

    # --- desk: top surface and foot contact, from a column through the desk ---
    xd = int(W * 0.12)
    lumd = column(px, xd, int(H * 0.45), H - 1)
    # desk top: strongest bright(wall)->dark(wood) step in the upper part
    top, top_d = None, 0.0
    for i in range(6, len(lumd) // 2):
        d = sum(lumd[i - 6:i]) / 6 - sum(lumd[i:i + 6]) / 6
        if d > top_d:
            top_d, top = d, y0 + i
    desk_top_y = top
    # foot contact: last row noticeably darker than the floor below it
    floor_lum = sum(lumd[-40:]) / 40
    foot = None
    for i in range(len(lumd) - 8, len(lumd) // 3, -1):
        if lumd[i] < floor_lum - 18:
            foot = y0 + i
            break
    desk_foot_y = foot

    desk_px = desk_foot_y - desk_top_y
    char_px = desk_px * (ADULT_H_CM / DESK_H_CM)

    out = {
        "plate": os.path.relpath(path),
        "plate_size": [W, H],
        "measured_plate_px": {
            "wall_floor_junction_y": wall_floor_y,
            "desk_top_y": desk_top_y,
            "desk_foot_y": desk_foot_y,
        },
        "composition_1080x1920": {
            "wall_floor_junction_y": round(wall_floor_y / sy, 1),
            "desk_top_y": round(desk_top_y / sy, 1),
            "desk_foot_y": round(desk_foot_y / sy, 1),
            "desk_height_px": round(desk_px / sy, 1),
            # The number the rig is scaled to. Feet land on desk_foot_y because
            # that is the only depth in the plate whose floor position is known.
            "character_height_px": round(char_px / sy, 1),
            "character_feet_y": round(desk_foot_y / sy, 1),
            "character_head_y": round((desk_foot_y - char_px) / sy, 1),
            # Camera horizon: with a level camera the horizon sits at eye height
            # of the viewer, and everything at that height has no vertical
            # foreshortening. The wall/floor junction is the far floor edge, so
            # the horizon is above it by the wall's visible run.
            "horizon_y_est": round(wall_floor_y / sy, 1),
        },
        "notes": [
            "Character height derives from the desk, not from taste: 75cm desk, 175cm adult.",
            "Feet sit on the desk's own foot line - the one known floor depth.",
            "If the character reads too large, the desk in the plate is drawn small, not the maths wrong.",
        ],
    }
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
