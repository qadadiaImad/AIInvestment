"""Generate ARM/BODY pose variants by masked inpainting - real new drawings.

WHY THIS, AFTER THE RIG.

The owner's read is right: a cut-out rig is not animation. It moves a
picture around. The drawing never changes, so there is no elbow bend, no
change of shape, no follow-through, no new expression - and no amount of
tuning fixes that. Pushed as hard as it goes the rig measured 1.75x the
per-frame motion of a still, and it still reads as a moving photograph.

The original diagnosis was the correct one: a video is a series of images,
so this is an IMAGE-SUPPLY problem. What went wrong was the conclusion I
drew when generation failed:

  · plain img2img would not turn the character at ANY denoise, because
    nothing forces the pose to change - the anchor latent always wins;
  · AnimateDiff gave boil, not motion.

But masked inpainting is a different mechanism and it is already proven in
this repo: it produced 66 viseme variants whose identity outside the mask
is EXACT, because SetLatentNoiseMask forces change inside the mask and
composite_rgb pastes the untouched base back outside it.

Per-beat pose cycling was banned once before, and for a good reason:
independent LoRA generations changed Sol's haircut and head direction
mid-sentence. Inpainting cannot do that. The mask stops below the neck, so
the head is not merely similar - it is the same pixels.

  python scripts/vector/pose_variants.py sol_point
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402
from vector.cells import white_bg_to_alpha      # noqa: E402

RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
OUT = REPO / "content/vector_char/cast/ep_fairmarket/poses"
FIX = REPO / "remotion/src/fixtures/cast_ep1"

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

# The vocabulary. Each entry is a DIFFERENT ARM POSITION on the same body -
# the shapes a presenter actually makes. These are what the rig can never
# produce, because an elbow has to bend and a flat cut-out has no elbow.
VARIANTS = [
    ("armsdown",  "both arms relaxed down at his sides, hands open"),
    ("presentL",  "one arm extended out to the side, palm open, presenting"),
    ("bothout",   "both arms spread wide open, palms up, explaining"),
    ("hiphand",   "one hand resting on his hip, the other arm relaxed"),
    ("countup",   "one hand raised holding up two fingers, counting"),
    ("chinrub",   "one hand raised to his chin, thinking, elbow bent"),
    ("reachout",  "one arm reaching forward toward the viewer, palm open"),
    ("armscross", "both arms folded across his chest"),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pad8(a: np.ndarray):
    h, w = a.shape[:2]
    ph, pw = (-h) % 8, (-w) % 8
    if not ph and not pw:
        return a, (h, w)
    pad = [(0, ph), (0, pw)] + [(0, 0)] * (a.ndim - 2)
    return np.pad(a, pad, mode="edge"), (h, w)


def flatten_white(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3:4].astype(float) / 255.0
    return (rgba[..., :3] * a + 255 * (1 - a)).astype(np.uint8)


def body_mask(w: int, h: int, neck: float) -> np.ndarray:
    """Everything below the neck and above the feet.

    The head is deliberately OUTSIDE it. That is the whole guarantee: the
    face, hair and expression are not regenerated and not approximately
    preserved - they are the same pixels, pasted back by composite.

    Feathered, because a hard mask edge leaves a visible seam right across
    the collar where the generated region meets the base.
    """
    im = Image.new("L", (w, h), 0)
    top = int(h * (neck + 0.015))
    ImageDraw.Draw(im).rectangle([0, top, w, int(h * 0.86)], fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(9)))


def composite(base: np.ndarray, gen: np.ndarray, mask: np.ndarray):
    """Feathered paste. Identity outside the mask is exact by construction."""
    m = (mask.astype(float) / 255.0)[..., None]
    return (gen * m + base * (1 - m)).astype(np.uint8)


def main() -> None:
    pose = sys.argv[1] if len(sys.argv) > 1 else "sol_point"
    denoise = float(sys.argv[sys.argv.index("--denoise") + 1]
                    if "--denoise" in sys.argv else 0.88)
    who = "sol" if pose.startswith("sol") else "rex"
    src = RENDERS / ("_" + pose + "_rgba.png")
    if not src.exists():
        sys.exit("no render for " + pose)

    rig = json.loads((FIX / "rig_parts.json").read_text("utf-8")).get(pose, {})
    neck = rig.get("neck", 0.48)
    rgba = np.asarray(Image.open(src).convert("RGBA"))
    base = flatten_white(rgba)
    H, W = base.shape[:2]
    mk = body_mask(W, H, neck)

    out = OUT / pose
    out.mkdir(parents=True, exist_ok=True)
    stage = out / "_stage"
    stage.mkdir(exist_ok=True)
    bp, _ = pad8(base)
    mp, _ = pad8(mk)
    Image.fromarray(bp).save(stage / ("pv_%s_base.png" % pose))
    Image.fromarray(mp).convert("RGB").save(stage / ("pv_%s_mask.png" % pose))
    ComfyClient.stage_input(stage / ("pv_%s_base.png" % pose))
    ComfyClient.stage_input(stage / ("pv_%s_mask.png" % pose))

    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    print("%s  %dx%d  neck %.3f  denoise %.2f  %d variants"
          % (pose, W, H, neck, denoise, len(VARIANTS)))

    manifest = []
    for i, (name, desc) in enumerate(VARIANTS):
        t0 = time.monotonic()
        paths = client.generate(
            "sdxl_lora_inpaint", out, timeout=600,
            image="pv_%s_base.png" % pose, mask="pv_%s_mask.png" % pose,
            prompt=LOCK[who] + ", " + desc + ", " + SUFFIX,
            negative=NEG, seed=5100 + i * 13, denoise=denoise)
        gen = np.asarray(Image.open(paths[0]).convert("RGB"))[:H, :W]
        # KEY THE BACKGROUND OUT. The variants are generated on white, and
        # shipping them opaque put a white rectangle behind the character in
        # the studio — which is the failure white_bg_to_alpha's own docstring
        # warns about. Border-connected near-white only, so the white shirt
        # keeps its pixels.
        rgb = composite(base, gen, mk)
        Image.fromarray(white_bg_to_alpha(rgb)).save(out / (name + ".png"))
        paths[0].unlink()
        manifest.append({
            "pose": pose, "variant": name, "prompt": desc,
            "denoise": denoise, "seed": 5100 + i * 13,
            "seconds": round(time.monotonic() - t0, 1),
            "source": "local ComfyUI sdxl_lora_inpaint "
                      "Illustrious-XL-v0.1 + ana_cast_v1",
            "source_class": "local-gen", "retrieved_at": now_utc()})
        print("  %-10s %5.1fs" % (name, time.monotonic() - t0), flush=True)

    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), "utf-8")

    # contact sheet: base first, so drift is judged against the original
    tiles = [("BASE", Image.fromarray(base))] + [
        (n, Image.open(out / (n + ".png")).convert("RGB")) for n, _ in VARIANTS]
    ht = 420
    wt = int(tiles[0][1].width * ht / tiles[0][1].height)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (wt * cols, (ht + 26) * rows), "white")
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(tiles):
        x, y = (i % cols) * wt, (i // cols) * (ht + 26)
        sheet.paste(im.resize((wt, ht)), (x, y + 26))
        d.text((x + 6, y + 7), n, fill=(0, 0, 0))
    sheet.save(out / "contact_sheet.png")
    print("-> " + str(out / "contact_sheet.png"))


if __name__ == "__main__":
    main()
