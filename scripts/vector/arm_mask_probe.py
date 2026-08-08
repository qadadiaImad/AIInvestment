"""Does a NARROW mask isolate one arm? The owner's proposal, tested.

THE QUESTION. Today a part is found by GUESSING: vtracer hands back the
whole figure as one path (97% of the frame for sol_point), so rig_parts.py
infers "this cluster is an arm" from bounding boxes - and every inference
bug this project hit came from there (legs unsplittable, the black-body
pose, the ghost hand beside the face).

The owner's proposal removes the guess: let the GENERATOR define the part.
Masked inpainting already guarantees that pixels OUTSIDE the mask are
untouched - not similar, identical, because composite pastes the base back.
So if the mask is drawn tightly around one arm and only the arm changes,
then the mask IS that arm's boundary, exactly, with no tracing at all.

pose_variants.py cannot answer this: its mask is "everything below the
neck", so the whole body is redrawn every time and the difference between
base and variant tells you nothing about where the arm is.

WHAT THIS MEASURES. Per generated variant:
  · leak   - share of changed pixels that fall OUTSIDE the mask. Should be
             ~0. Anything real means the guarantee does not hold.
  · fill   - share of the mask that actually changed. If this is tiny the
             model ignored the instruction and just redrew the same arm,
             which is a different failure and equally fatal.
  · a side-by-side and a change-map, because a number can pass while the
             picture is nonsense.

  python scripts/vector/arm_mask_probe.py sol_point
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient           # noqa: E402
from comfy.launch import ensure_server          # noqa: E402

RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
OUT = REPO / "content/vector_char/cast/ep_fairmarket/arm_probe"

LOCK = {
    "sol": ("solquant, 1boy, solo, old man, gray hair, thick mustache, "
            "burgundy cardigan, white shirt, yellow bow tie, plump, "
            "dark trousers"),
    "rex": ("rexquant, 1boy, solo, young man, orange hair, glasses, "
            "gray vest, white shirt, dark trousers"),
}
SUFFIX = ("flat color, thick clean black outlines, cel shading, "
          "white background, masterpiece, best quality")
NEG = ("worst quality, low quality, blurry, deformed, extra limbs, "
       "extra arms, missing arm, mutated hands, bad hands, "
       "different character, changing hairstyle, changing clothes, "
       "text, watermark, multiple views")

# Read off the base drawing: sol_point's pointing arm occupies the left
# third, from just under the chin to the hem. The box is deliberately
# LARGER than the arm's current pixels - an arm that may only be redrawn
# where it already is cannot move.
ARM_BOX = (0.00, 0.40, 0.45, 0.88)

TRIES = [
    ("down",   "his raised arm lowered straight down at his side, hand open"),
    ("outward", "his raised arm extended out to the side, palm open"),
    ("chin",   "his raised hand moved to his chin, thinking, elbow bent"),
]


def flatten_white(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3:4].astype(float) / 255.0
    return (rgba[..., :3] * a + 255 * (1 - a)).astype(np.uint8)


def pad8(a: np.ndarray):
    h, w = a.shape[:2]
    ph, pw = (-h) % 8, (-w) % 8
    if not ph and not pw:
        return a
    pad = [(0, ph), (0, pw)] + [(0, 0)] * (a.ndim - 2)
    return np.pad(a, pad, mode="edge")


def arm_mask(w: int, h: int, box) -> np.ndarray:
    x0, y0, x1, y1 = box
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).rectangle(
        [int(w * x0), int(h * y0), int(w * x1), int(h * y1)], fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(9)))


def composite(base, gen, mask):
    m = (mask.astype(float) / 255.0)[..., None]
    return (gen * m + base * (1 - m)).astype(np.uint8)


def main() -> None:
    pose = sys.argv[1] if len(sys.argv) > 1 else "sol_point"
    who = "sol" if pose.startswith("sol") else "rex"
    src = RENDERS / ("_" + pose + "_rgba.png")
    if not src.exists():
        sys.exit("no render for " + pose)

    base = flatten_white(np.asarray(Image.open(src).convert("RGBA")))
    H, W = base.shape[:2]
    mk = arm_mask(W, H, ARM_BOX)
    hard = mk > 127

    OUT.mkdir(parents=True, exist_ok=True)
    stage = OUT / "_stage"
    stage.mkdir(exist_ok=True)
    Image.fromarray(pad8(base)).save(stage / "ap_base.png")
    Image.fromarray(pad8(mk)).convert("RGB").save(stage / "ap_mask.png")
    ComfyClient.stage_input(stage / "ap_base.png")
    ComfyClient.stage_input(stage / "ap_mask.png")

    # the mask, drawn on the base, so a bad box is caught before the GPU runs
    ov = base.copy()
    ov[hard] = (ov[hard] * 0.55 + np.array([255, 90, 90]) * 0.45).astype(np.uint8)
    Image.fromarray(ov).save(OUT / "_mask_overlay.png")

    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    print(f"{pose} {W}x{H}  mask box {ARM_BOX}  "
          f"({100 * hard.mean():.1f}% of frame)")

    rows, results = [], []
    for i, (name, desc) in enumerate(TRIES):
        t0 = time.monotonic()
        paths = client.generate(
            "sdxl_lora_inpaint", OUT, timeout=600,
            image="ap_base.png", mask="ap_mask.png",
            prompt=LOCK[who] + ", " + desc + ", " + SUFFIX,
            negative=NEG, seed=8800 + i * 17, denoise=0.88)
        gen = np.asarray(Image.open(paths[0]).convert("RGB"))[:H, :W]
        paths[0].unlink()

        # RAW generator output vs base - NOT the composite. Compositing
        # pastes the base back outside the mask, so measuring leak on the
        # composite would prove only that the paste works, which is not in
        # question. What is in question is whether the MODEL stayed put.
        d = np.abs(gen.astype(int) - base.astype(int)).sum(axis=2) > 60
        leak = d[~hard].mean() if (~hard).any() else 0.0
        fill = d[hard].mean() if hard.any() else 0.0
        out = composite(base, gen, mk)
        Image.fromarray(out).save(OUT / (name + ".png"))
        Image.fromarray((d * 255).astype(np.uint8)).save(OUT / (name + "_diff.png"))
        results.append((name, out))
        rows.append({"variant": name, "leak_outside_mask": round(float(leak), 4),
                     "fill_inside_mask": round(float(fill), 4),
                     "seconds": round(time.monotonic() - t0, 1)})
        print(f"  {name:9s} leak {100 * leak:5.2f}%   fill {100 * fill:5.1f}%   "
              f"{time.monotonic() - t0:5.1f}s", flush=True)

    (OUT / "probe.json").write_text(json.dumps(rows, indent=1), "utf-8")

    tiles = [("BASE", Image.fromarray(base))] + [
        (n, Image.fromarray(im)) for n, im in results]
    ht = 460
    wt = int(W * ht / H)
    sheet = Image.new("RGB", (wt * len(tiles), ht + 26), "white")
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(tiles):
        sheet.paste(im.resize((wt, ht)), (i * wt, 26))
        d.text((i * wt + 6, 7), n, fill=(0, 0, 0))
    sheet.save(OUT / "contact_sheet.png")
    print("-> " + str(OUT / "contact_sheet.png"))


if __name__ == "__main__":
    main()
