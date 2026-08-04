"""Emit per-pose grid overlays so anchor coordinates can be read off
visually (5% grid, labels every 10%) -- used to hand-place the ep1 viseme
mask anchors after auto-detection proved unreliable on busts/Rex poses."""
from __future__ import annotations

from PIL import Image, ImageDraw

from vector.visemes_ep1 import (SOL_POSES, REX_POSES, VIS, load_base,
                                flatten_white, _font)


def main() -> None:
    out = VIS / "grids"
    out.mkdir(parents=True, exist_ok=True)
    for pose in SOL_POSES + REX_POSES:
        rgb = flatten_white(load_base(pose))
        im = Image.fromarray(rgb)
        s = 900 / im.height
        im = im.resize((int(im.width * s), 900))
        d = ImageDraw.Draw(im)
        w, h = im.size
        for i in range(1, 20):
            f = i / 20
            major = i % 2 == 0
            col = (255, 60, 60) if major else (120, 180, 255)
            d.line([f * w, 0, f * w, h], fill=col, width=2 if major else 1)
            d.line([0, f * h, w, f * h], fill=col, width=2 if major else 1)
            if major:
                d.text((f * w + 3, 2), f"{f:.1f}", fill=(200, 0, 0),
                       font=_font(20))
                d.text((3, f * h + 2), f"{f:.1f}", fill=(200, 0, 0),
                       font=_font(20))
        im.save(out / f"{pose}.png")
        print(pose, im.size)


if __name__ == "__main__":
    main()
