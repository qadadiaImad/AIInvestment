"""Tests for scripts/vector/cells.py — sheet splitting + vectorization."""
import numpy as np
from PIL import Image

from vector import cells


def _sheet(tmp_path):
    """Synthetic sheet: white bg, two solid blobs + one sub-threshold speck."""
    a = np.full((300, 400, 3), 255, np.uint8)
    a[40:140, 30:130] = (200, 40, 40)      # blob 1 (top-left)
    a[160:280, 250:380] = (40, 40, 200)    # blob 2 (bottom-right)
    a[10:13, 390:393] = (0, 0, 0)          # speck (filtered by min_area)
    p = tmp_path / "sheet.png"
    Image.fromarray(a).save(p)
    return p


def test_white_to_alpha_clears_background():
    a = np.full((10, 10, 3), 255, np.uint8)
    a[2:5, 2:5] = (10, 10, 10)
    rgba = cells.white_to_alpha(a)
    assert rgba.shape == (10, 10, 4)
    assert rgba[0, 0, 3] == 0          # white -> transparent
    assert rgba[3, 3, 3] == 255        # ink kept


def test_find_cells_filters_specks_and_orders_reading_order(tmp_path):
    p = _sheet(tmp_path)
    rgba = cells.load_rgba(p)
    boxes = cells.find_cells(rgba, min_area=400)
    assert len(boxes) == 2
    (x0, y0, _, _), (x1, y1, _, _) = boxes
    assert y0 < y1 and x0 < x1        # reading order: top-left blob first


def test_compute_anchor_finds_feet_and_ink_height():
    """A 'figure': head blob high, feet blob at bottom-left of the ink."""
    a = np.zeros((200, 100, 4), np.uint8)
    a[20:60, 40:60, 3] = 255      # head ink
    a[60:180, 45:55, 3] = 255     # body/legs ink, bottom at y=180
    anc = cells.compute_anchor(a)
    assert anc["ink_h"] == 159                    # rows 20..179 inclusive
    assert abs(anc["anchor"][1] - 0.895) < 0.02   # feet at 179/200
    assert abs(anc["anchor"][0] - 0.50) < 0.05    # feet centered at x=50/100


def test_extract_and_vectorize_roundtrip(tmp_path):
    p = _sheet(tmp_path)
    out = tmp_path / "parts"
    pngs = cells.extract_cells(p, out, prefix="t", min_area=400, pad=6)
    assert len(pngs) == 2
    svgs = [cells.vectorize(png, png.with_suffix(".svg")) for png in pngs]
    for svg in svgs:
        text = svg.read_text("utf-8")
        assert text.lstrip().startswith("<?xml") or "<svg" in text[:200]
        assert "path" in text
