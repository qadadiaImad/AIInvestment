"""Split generated character sheets into part cells and vectorize them.

Pipeline stage between the local ComfyUI renders (flat-style character
sheets on white) and the Remotion rigs: near-white background becomes
alpha, connected components become individual part crops (reading
order), and vtracer turns each crop into a real SVG.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

WHITE_THRESH = 238   # >= on all RGB channels counts as background
DEFAULT_MIN_AREA = 2500
DEFAULT_PAD = 12

# vtracer settings tuned for flat-color art: spline mode keeps edges
# smooth; filter_speckle drops anti-aliasing crumbs around outlines.
VTRACER_DEFAULTS = dict(
    colormode="color",
    mode="spline",
    filter_speckle=8,
    color_precision=7,
    corner_threshold=60,
    path_precision=3,
)


def load_rgba(path) -> np.ndarray:
    return white_to_alpha(np.asarray(Image.open(path).convert("RGB")))


def white_to_alpha(rgb: np.ndarray, thresh: int = WHITE_THRESH) -> np.ndarray:
    """RGB (H,W,3) -> RGBA with near-white pixels fully transparent."""
    bg = (rgb >= thresh).all(axis=2)
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    return np.dstack([rgb, alpha])


def bg_to_alpha(rgb: np.ndarray, tol: int = 24) -> np.ndarray:
    """RGB -> RGBA keying out the FLAT background color sampled from the
    image corners (median of the four 8x8 corner patches). Handles LoRA
    renders that come back on solid gray/tinted backgrounds instead of
    white; falls back to plain distance keying, no flood fill needed
    because the backgrounds are flat by prompt construction."""
    h, w = rgb.shape[:2]
    corners = np.concatenate([
        rgb[:8, :8].reshape(-1, 3), rgb[:8, w-8:].reshape(-1, 3),
        rgb[h-8:, :8].reshape(-1, 3), rgb[h-8:, w-8:].reshape(-1, 3)])
    bg_color = np.median(corners, axis=0)
    dist = np.abs(rgb.astype(int) - bg_color).max(axis=2)
    candidate = dist <= tol
    # Key ONLY background-CONNECTED candidate regions (flood from borders):
    # interior pixels that merely resemble the bg color (shading inside
    # clothes) must stay opaque, or the figure gets pinholes.
    labels, _ = ndimage.label(candidate)
    border = np.unique(np.concatenate([
        labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]]))
    bg_mask = np.isin(labels, border[border != 0])
    alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
    return np.dstack([rgb, alpha])


def find_cells(rgba: np.ndarray, min_area: int = DEFAULT_MIN_AREA) -> list[tuple]:
    """Connected components of the alpha mask -> [(x0,y0,x1,y1)] in reading
    order (row bands top-to-bottom, then left-to-right within a band)."""
    mask = rgba[..., 3] > 0
    # close small gaps so one drawing doesn't split into fragments
    mask = ndimage.binary_dilation(mask, iterations=3)
    labels, n = ndimage.label(mask)
    boxes = []
    for sl in ndimage.find_objects(labels):
        if sl is None:
            continue
        y, x = sl
        if (y.stop - y.start) * (x.stop - x.start) >= min_area:
            boxes.append((x.start, y.start, x.stop, y.stop))
    if not boxes:
        return []
    med_h = np.median([b[3] - b[1] for b in boxes])
    boxes.sort(key=lambda b: (int((b[1] + b[3]) / 2 // max(med_h, 1)), b[0]))
    return boxes


def extract_cells(sheet_path, out_dir, prefix: str,
                  min_area: int = DEFAULT_MIN_AREA,
                  pad: int = DEFAULT_PAD) -> list[Path]:
    """Split a sheet PNG into per-cell RGBA crops. Returns saved paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rgba = load_rgba(sheet_path)
    h, w = rgba.shape[:2]
    saved = []
    for i, (x0, y0, x1, y1) in enumerate(find_cells(rgba, min_area), 1):
        x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
        x1, y1 = min(w, x1 + pad), min(h, y1 + pad)
        crop = rgba[y0:y1, x0:x1]
        p = out_dir / f"{prefix}_{i:02d}.png"
        Image.fromarray(crop).save(p)
        saved.append(p)
    return saved


def compute_anchor(rgba: np.ndarray, foot_band: float = 0.08) -> dict:
    """Ground-contact anchor for a figure drawing, poseCut-style: the bottom
    of the ink, and the x-centre of only the ink NEAR that bottom (the feet),
    both normalised to the canvas. `ink_h` supports cross-pose scale
    normalisation so a cut can't grow or shrink the character."""
    h, w = rgba.shape[:2]
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    if len(ys) == 0:
        raise ValueError("empty drawing")
    y_top, y_bot = int(ys.min()), int(ys.max())
    band = max(2, int((y_bot - y_top) * foot_band))
    feet_xs = xs[ys >= y_bot - band]
    return {
        "w": w, "h": h,
        "ink_h": int(y_bot - y_top),
        "anchor": [round(float(feet_xs.mean()) / w, 4), round(y_bot / h, 4)],
    }


def vectorize(png_path, svg_path, **overrides) -> Path:
    """Vectorize one RGBA PNG to SVG via vtracer."""
    import vtracer

    params = {**VTRACER_DEFAULTS, **overrides}
    svg_path = Path(svg_path)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    vtracer.convert_image_to_svg_py(str(png_path), str(svg_path), **params)
    return svg_path
