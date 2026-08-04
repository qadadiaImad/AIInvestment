"""Contact sheets of every Sol / Rex drawing used by FairMarketEp1, for
the identity-continuity gate (which drawings are on-model for hair
silhouette, head direction and proportion)."""
from __future__ import annotations

from PIL import Image, ImageDraw

from vector.visemes_ep1 import VIS, RENDERS, flatten_white, _font
import numpy as np

SOL = ["sol_smug_v1", "sol_smug_v2", "sol_smug", "sol_wink", "sol_wink_v1",
       "sol_point", "sol_point_v1", "sol_finger", "sol_armswide",
       "sol_laugh", "sol_laugh_v1", "sol_shrug", "sol_shrug_v1",
       "sol_whisper", "sol_whisper_v1"]
REX = ["rex_eager", "rex_eager_v1", "rex_shock", "rex_shock_v1",
       "rex_determined", "rex_determined_v1", "rex_listen", "rex_skeptic"]


def sheet(names: list[str], out: str, cols: int = 5, h: int = 460) -> None:
    tiles = []
    for n in names:
        p = RENDERS / f"_{n}_rgba.png"
        rgba = np.asarray(Image.open(p).convert("RGBA"))
        im = Image.fromarray(flatten_white(rgba))
        s = h / im.height
        im = im.resize((int(im.width * s), h))
        t = Image.new("RGB", (im.width + 8, h + 34), "white")
        t.paste(im, (4, 34))
        ImageDraw.Draw(t).text((6, 6), n, fill="black", font=_font(22))
        tiles.append(t)
    cw = max(t.width for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    sh = Image.new("RGB", (cw * cols, (h + 34) * rows), "white")
    for i, t in enumerate(tiles):
        sh.paste(t, ((i % cols) * cw, (i // cols) * (h + 34)))
    p = VIS / "sheets" / out
    sh.save(p)
    print(f"wrote {p} ({sh.size[0]}x{sh.size[1]})")


if __name__ == "__main__":
    sheet(SOL, "CAST_sol_all.png")
    sheet(REX, "CAST_rex_all.png", cols=4)
