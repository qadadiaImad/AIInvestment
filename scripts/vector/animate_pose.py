"""Generate in-between frames for an existing pose with AnimateDiff.

THE IDEA, and why it is not "AnimateDiff instead of the rig".

The composition animates by holding a flat SVG drawing and moving it in
code - breathing, weight shift, camera creep. What it cannot do is draw
the character actually moving, because there is only ever one drawing per
pose. Per-beat pose CYCLING was tried and banned: swapping between
independent LoRA generations changed Sol's haircut and head direction
mid-sentence, and the owner rejected it.

A motion module fixes exactly that gap. Frames from AnimateDiff are
temporally coherent with each other by construction - they come from one
sampling pass with a motion prior, not from N unrelated generations. So
the plan is:

    approved drawing
      -> VAEEncode -> RepeatLatentBatch(16) -> AnimateDiff KSampler
      -> 16 coherent frames
      -> the EXISTING pipeline: background key, vectorise, anchor, gate
      -> 16 registered poses that play as a cycle

Everything downstream survives, which was the whole objection to using
video here: visemes still swap per frame off the VO amplitude, the
staging audit still measures real ink bounds, and any frame that drifts
is rejected by the same identity gate that threw out 5 of 9 caricatures.

denoise is deliberately LOW (~0.45). High denoise gives more motion and
less of the drawing you approved; this is an in-betweener, not a
re-imaginer.

  python scripts/vector/animate_pose.py sol_point [--frames 16] [--denoise 0.45]
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
OUT = REPO / "content/vector_char/cast/ep_fairmarket/anim"
COMFY_INPUT = Path.home() / "Documents" / "ComfyUI" / "input"

LOCK = {
    "sol": ("solquant, 1boy, solo, old man, gray hair, thick mustache, "
            "burgundy cardigan, yellow bow tie, plump"),
    "rex": ("rexquant, 1boy, solo, orange hair, spiky hair, glasses, "
            "gray vest, white shirt"),
}
MOTION = ("subtle idle motion, breathing, slight weight shift, "
          "small natural head movement, standing still")
SUFFIX = ("flat color, thick clean black outlines, cel shading, "
          "simple background, white background, masterpiece, best quality")
NEG = ("worst quality, low quality, blurry, deformed, extra limbs, "
       "changing hairstyle, changing clothes, morphing face, "
       "different character, multiple views, text, watermark, "
       "large movement, walking, turning around")


def flatten_to_white(rgba_path: Path, dst: Path) -> tuple[int, int]:
    """The pipeline stores poses as RGBA cut-outs; img2img needs pixels.
    Compose onto white - the same background the pose was generated on,
    so the model sees what it originally produced."""
    im = Image.open(rgba_path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    # SDXL wants dimensions on a multiple of 8
    w, h = (im.width // 8) * 8, (im.height // 8) * 8
    bg.convert("RGB").resize((w, h)).save(dst)
    return w, h


def main() -> None:
    pose = sys.argv[1] if len(sys.argv) > 1 else "sol_point"
    frames = int(sys.argv[sys.argv.index("--frames") + 1]
                 if "--frames" in sys.argv else 16)
    denoise = float(sys.argv[sys.argv.index("--denoise") + 1]
                    if "--denoise" in sys.argv else 0.45)
    motion = float(sys.argv[sys.argv.index("--motion") + 1]
                   if "--motion" in sys.argv else 1.0)
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
    who = "sol" if pose.startswith("sol") else "rex"

    src = RENDERS / ("_" + pose + "_rgba.png")
    if not src.exists():
        sys.exit("no such pose render: " + str(src))
    COMFY_INPUT.mkdir(parents=True, exist_ok=True)
    stem = "anim_src_" + pose + ".png"
    w, h = flatten_to_white(src, COMFY_INPUT / stem)
    print("anchor: %s  %dx%d  frames=%d  denoise=%.2f  motion=%.2f"
          % (pose, w, h, frames, denoise, motion))

    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    out_dir = OUT / (pose + tag)
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()
    paths = client.generate(
        "sdxl_lora_animate", out_dir, timeout=1800,
        prompt=LOCK[who] + ", " + MOTION + ", " + SUFFIX,
        negative=NEG, seed=4242, denoise=denoise, steps=20,
        image=stem, frames=frames, ctx_len=min(16, frames), closed=True,
        motion=motion, lora_sm=0.75, lora_sc=0.75)
    print("%d frames in %.1fs" % (len(paths), time.monotonic() - t0))
    for i, p in enumerate(sorted(paths)):
        p.rename(out_dir / ("f%02d.png" % i))
    print("-> " + str(out_dir))


if __name__ == "__main__":
    main()
