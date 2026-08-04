"""Merge gate rounds into picks_final.json and render gated contact
matrices (one per character): rows = poses, cols = BASE + visemes, using
the picked survivor for each cell; missing viseme = grayed X cell."""
from __future__ import annotations

import json

import numpy as np
from PIL import Image, ImageDraw

from vector.visemes_ep1 import (VIS, SOL_POSES, REX_POSES, load_anchors,
                                load_base, flatten_white, _font)

ORDER = ["closed", "half", "open", "oh", "blink"]


ROUNDS = ("round1", "round2", "round3", "round4", "twopass")


def merge_picks() -> dict:
    """Later rounds win: each was generated to fix what the previous one
    failed the gate on."""
    picks: dict[str, dict[str, str]] = {}
    for tag in ROUNDS:
        p = VIS / f"picks_{tag}.json"
        if not p.exists():
            continue
        for pose, vis in json.loads(p.read_text("utf-8")).items():
            for v, cand in vis.items():
                picks.setdefault(pose, {})[v] = cand
    (VIS / "picks_final.json").write_text(json.dumps(picks, indent=1),
                                          "utf-8")
    return picks


def face_crop(rgb: np.ndarray, a: dict, out_h=190) -> Image.Image:
    m, e = a["mouth"], a["eyes"]
    im = Image.fromarray(rgb)
    x0 = int(min(m["cx"] - m["rx"], e["cx"] - e["rx"]))
    x1 = int(max(m["cx"] + m["rx"], e["cx"] + e["rx"]))
    y0 = int(min(m["cy"] - m["ry"], e["cy"] - e["ry"]))
    y1 = int(max(m["cy"] + m["ry"], e["cy"] + e["ry"]))
    pad = int((x1 - x0) * 0.12)
    crop = im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))
    s = out_h / crop.height
    return crop.resize((int(crop.width * s), out_h))


def matrix(poses: list[str], picks: dict, anchors: dict,
           out_name: str) -> None:
    cell_h, label_h, cw = 190, 26, 260
    rows = []
    for pose in poses:
        a = anchors[pose]
        cells = [face_crop(flatten_white(load_base(pose)), a)]
        for v in ORDER:
            cand = picks.get(pose, {}).get(v)
            if cand:
                rgba = np.asarray(Image.open(
                    VIS / "comp" / f"{cand}.png").convert("RGBA"))
                cells.append(face_crop(flatten_white(rgba), a))
            else:
                cells.append(None)
        rows.append((pose, cells))
    W = cw * (len(ORDER) + 1) + 150
    H = (cell_h + 8) * len(rows) + label_h
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    for c, name in enumerate(["BASE"] + ORDER):
        d.text((150 + c * cw + 8, 4), name.upper(), fill="black",
               font=_font(20))
    for r, (pose, cells) in enumerate(rows):
        y = label_h + r * (cell_h + 8)
        d.text((4, y + cell_h // 2 - 10), pose, fill="black", font=_font(17))
        for c, cell in enumerate(cells):
            x = 150 + c * cw
            if cell is None:
                d.rectangle([x + 4, y + 4, x + cw - 8, y + cell_h - 4],
                            fill=(240, 240, 240), outline=(200, 200, 200))
                d.text((x + cw // 2 - 8, y + cell_h // 2 - 12), "X",
                       fill=(170, 170, 170), font=_font(26))
            else:
                sheet.paste(cell, (x + (cw - cell.width) // 2, y))
    out = VIS / "sheets" / out_name
    sheet.save(out)
    print(f"wrote {out} ({sheet.size[0]}x{sheet.size[1]})")


if __name__ == "__main__":
    picks = merge_picks()
    total = sum(len(v) for v in picks.values())
    print(f"picks_final.json: {total} gated visemes across "
          f"{len(picks)} poses")
    anchors = load_anchors()
    matrix(SOL_POSES, picks, anchors, "GATED_matrix_sol.png")
    matrix(REX_POSES, picks, anchors, "GATED_matrix_rex.png")
