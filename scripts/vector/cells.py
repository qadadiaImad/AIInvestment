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


def white_bg_to_alpha(rgb: np.ndarray, thresh: int = 226) -> np.ndarray:
    """RGB -> RGBA keying out only BORDER-CONNECTED near-white pixels.

    `bg_to_alpha` samples the four corner patches for the background
    colour, which silently fails on tight bust closeups where the head
    fills the canvas and the corners are hair or skin -- those poses came
    out fully opaque and composited as a visible white rectangle over the
    scene. Here the test is absolute (near-white) and the flood is from
    the border, so an interior white shirt keeps its pixels while the
    margin around the figure is keyed regardless of what the corners
    happen to contain.
    """
    bright = (rgb >= thresh).all(axis=2)
    labels, _ = ndimage.label(bright)
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


# Small high-contrast features — a closed mouth line, the rim of an "oh"
# — are where the default speckle filter does damage: it is sized to drop
# anti-aliasing crumbs off a big flat shape, and at mouth scale it eats
# and re-joins the outline instead, which is where the stray black hook
# in rex_shock_v1's closed mouth came from. Tracing detail is raised and
# the input is posterised first, because vtracer wants genuinely flat
# colour and a diffusion model never returns quite that.
VTRACER_DETAIL = dict(
    filter_speckle=3,
    color_precision=8,
    corner_threshold=45,
    path_precision=4,
)


def flatten_palette(png_path, out_path, colors: int = 40) -> Path:
    """Posterise to a small palette, preserving alpha, so the tracer sees
    flat regions rather than the soft gradients the generator leaves.

    OFF by default, and it should stay off at these palette sizes: a
    median-cut quantise over a whole character shifts colours that
    matter. At 40 colours Sol's pink cheek blush came back olive and his
    bow tie lost its gold. The speckle filter, not the gradients, was
    what damaged the mouths — `detail=True` alone fixes them.
    """
    im = Image.open(png_path).convert("RGBA")
    alpha = im.getchannel("A")
    flat = im.convert("RGB").quantize(
        colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
    out = flat.convert("RGBA")
    out.putalpha(alpha)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return out_path


def vectorize(png_path, svg_path, detail: bool = False,
              flatten: bool = False, **overrides) -> Path:
    """Vectorize one RGBA PNG to SVG via vtracer."""
    import vtracer

    params = {**VTRACER_DEFAULTS}
    if detail:
        params.update(VTRACER_DETAIL)
    params.update(overrides)
    svg_path = Path(svg_path)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    src = png_path
    if flatten:
        src = flatten_palette(
            png_path, svg_path.parent / f"_flat_{Path(png_path).name}")
    vtracer.convert_image_to_svg_py(str(src), str(svg_path), **params)
    if flatten:
        Path(src).unlink(missing_ok=True)
    return svg_path
