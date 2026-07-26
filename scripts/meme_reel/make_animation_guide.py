"""Render the stage guide the character animator works against.

The character is animated OUTSIDE this repo (Cartoon Animator / Character
Animator / Moho / After Effects) and delivered as a transparent 1080x1920 video.
For that performance to land in the room, the animator needs to know exactly
where the room's furniture is in the same coordinate space — the floor line he
stands on, the desk he can lean on, the monitor he must not cover, and the
bottom strip the caption and disclaimer occupy.

This writes that guide: the room plate, dimmed, with those marks drawn on top,
at exactly 1080x1920. Import it as a background reference layer, animate the
character over it, then hide it before exporting.

Usage:
    python scripts/meme_reel/make_animation_guide.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PLATE = os.path.join(REPO, "remotion", "public", "meme_reel", "room_plate.png")
FIXTURE = os.path.join(REPO, "remotion", "src", "fixtures", "meme_reel", "intc_failed_breakout.json")
OUT = os.path.join(REPO, "content", "meme_reel", "ANIMATION_GUIDE.png")

W, H = 1080, 1920
# Measured from the plate by measure_screen_quad.py / the floor scan.
FLOOR_Y = 1506      # wall-to-floor junction
DESK_TOP_Y = 1000   # desk surface
FOOTER_Y = 1812     # top of the disclaimer strip
CAPTION_TOP = 1560  # captions occupy roughly here down to the footer


def label(d, xy, text, fill, font):
    x, y = xy
    # a dark halo so the text survives on both the wall and the floor
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0, 200), font=font)
    d.text((x, y), text, fill=fill, font=font)


def main():
    fx = json.load(open(FIXTURE, encoding="utf-8"))
    quad = fx["quad"]
    qx0, qy0 = quad[0]["x"], quad[0]["y"]
    qx1, qy1 = quad[2]["x"], quad[2]["y"]

    plate = Image.open(PLATE).convert("RGB").resize((W, H), Image.LANCZOS)
    # Dim it so the animator's character reads clearly on top of the guide.
    plate = Image.blend(plate, Image.new("RGB", (W, H), (255, 255, 255)), 0.45)
    img = plate.convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    try:
        font = ImageFont.truetype("consola.ttf", 26)
        small = ImageFont.truetype("consola.ttf", 21)
    except OSError:
        font = ImageFont.load_default()
        small = font

    # --- the monitor: do not cover it -------------------------------------
    d.rectangle([qx0, qy0, qx1, qy1], outline=(230, 60, 60, 255), width=5)
    label(d, (qx0, qy0 - 34), "MONITOR - KEEP CLEAR", (255, 120, 120, 255), small)

    # --- the desk ----------------------------------------------------------
    d.line([(0, DESK_TOP_Y), (700, DESK_TOP_Y)], fill=(240, 170, 60, 255), width=4)
    label(d, (12, DESK_TOP_Y + 8), f"DESK TOP  y={DESK_TOP_Y}", (250, 200, 110, 255), small)

    # --- the floor he stands on -------------------------------------------
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(90, 200, 130, 255), width=4)
    label(d, (12, FLOOR_Y - 34), f"WALL/FLOOR JUNCTION  y={FLOOR_Y}", (130, 240, 170, 255), small)

    # --- type safe area ----------------------------------------------------
    d.rectangle([0, CAPTION_TOP, W, H], fill=(0, 0, 0, 70))
    d.line([(0, CAPTION_TOP), (W, CAPTION_TOP)], fill=(120, 170, 255, 255), width=3)
    label(d, (12, CAPTION_TOP - 32), "CAPTIONS + DISCLAIMER over this strip - keep the FACE and HANDS above it",
          (170, 205, 255, 255), small)
    d.line([(0, FOOTER_Y), (W, FOOTER_Y)], fill=(120, 170, 255, 200), width=2)

    # Where the feet should land, and the stage box he should stay inside.
    feet_y = fx["charFeetY"]
    d.line([(430, feet_y), (W - 20, feet_y)], fill=(90, 200, 130, 255), width=6)
    label(d, (440, feet_y + 10), f"FEET LAND HERE  y={feet_y}", (150, 255, 190, 255), font)

    d.rectangle([430, 300, W - 20, feet_y], outline=(90, 200, 130, 160), width=3)
    label(d, (440, 306), "CHARACTER STAGE BOX", (150, 255, 190, 255), small)

    # --- canvas spec -------------------------------------------------------
    label(d, (12, 14), "1080 x 1920  ·  30 fps  ·  510 frames  ·  17.00 s", (255, 255, 255, 255), font)
    label(d, (12, 48), "animate the CHARACTER ONLY on transparent - no camera move", (255, 235, 170, 255), small)
    label(d, (12, 76), "the reel's camera is applied in Remotion, to room + character together", (255, 235, 170, 255), small)

    img.alpha_composite(ov)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.convert("RGB").save(OUT)
    print(f"wrote {OUT}  ({W}x{H})")
    print(f"  monitor quad   : ({qx0},{qy0}) -> ({qx1},{qy1})")
    print(f"  desk top       : y={DESK_TOP_Y}")
    print(f"  floor junction : y={FLOOR_Y}")
    print(f"  feet land      : y={feet_y}")
    print(f"  type safe area : y>{CAPTION_TOP}")


if __name__ == "__main__":
    main()
