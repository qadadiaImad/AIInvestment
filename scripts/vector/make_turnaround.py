"""Generate turnaround views so a 2D character can turn in depth.

WHY GENERATION IS THE RIGHT TOOL *HERE*, having been the wrong one twice.

A cut-out rig moves parts in the picture plane. That covers walking,
gesturing, leaning, looking up - anything that is translation or rotation
on screen. It cannot turn a character 45 degrees, because a flat drawing
has no depth to rotate through: rotate it and you get a squashed front
view, not a three-quarter view.

Traditional 2D animation has always solved this with a TURNAROUND - a
separate drawing per angle, cut between as the character turns. The turn
is a new drawing, not a transform. That is precisely the "lack of image
resources" the owner identified.

And the anchored img2img rig is the tool for it, proven: 16 generations
off one approved drawing held hair, wardrobe and proportions with zero
drift. Same anchor, same LoRA, same seed - only the angle prompt changes.

Denoise is HIGHER here than for in-betweening (~0.62) because the pose
genuinely has to change; the anchor is steering identity, not geometry.

  python scripts/vector/make_turnaround.py sol_point
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
OUT = REPO / "content/vector_char/cast/ep_fairmarket/turnaround"
COMFY_INPUT = Path.home() / "Documents" / "ComfyUI" / "input"

LOCK = {
    "sol": ("solquant, 1boy, solo, old man, gray hair, thick mustache, "
            "burgundy cardigan, yellow bow tie, plump, full body, standing"),
    "rex": ("rexquant, 1boy, solo, orange hair, spiky hair, glasses, "
            "gray vest, white shirt, full body, standing"),
}
SUFFIX = ("flat color, thick clean black outlines, cel shading, "
          "simple background, white background, masterpiece, best quality")
NEG = ("worst quality, low quality, blurry, deformed, extra limbs, "
       "different character, changing hairstyle, changing clothes, "
       "multiple views, character sheet, text, watermark")

# The turnaround. "Giving the viewer the shoulder" is the three-quarter
# BACK view - the one that sells a character talking to someone beside
# them rather than at camera.
ANGLES = [
    ("q34l",  "three quarter view, turned 45 degrees to the left, "
              "shoulder toward viewer"),
    ("q34r",  "three quarter view, turned 45 degrees to the right, "
              "shoulder toward viewer"),
    ("prof",  "profile view, side view, facing right"),
    ("back34", "three quarter back view, seen from behind and the side, "
               "shoulder and back toward viewer, head turned in profile"),
    ("up",    "looking up, chin raised, head tilted upward"),
]


def flatten(rgba_path: Path, dst: Path):
    im = Image.open(rgba_path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    w, h = (im.width // 8) * 8, (im.height // 8) * 8
    bg.convert("RGB").resize((w, h)).save(dst)
    return w, h


def main() -> None:
    pose = sys.argv[1] if len(sys.argv) > 1 else "sol_point"
    denoise = float(sys.argv[sys.argv.index("--denoise") + 1]
                    if "--denoise" in sys.argv else 0.62)
    who = "sol" if pose.startswith("sol") else "rex"
    src = RENDERS / ("_" + pose + "_rgba.png")
    if not src.exists():
        sys.exit("no such pose: " + str(src))

    COMFY_INPUT.mkdir(parents=True, exist_ok=True)
    stem = "turn_src_" + pose + ".png"
    w, h = flatten(src, COMFY_INPUT / stem)
    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    out = OUT / pose
    out.mkdir(parents=True, exist_ok=True)
    print("%s  %dx%d  denoise=%.2f  %d angles" % (pose, w, h, denoise, len(ANGLES)))

    for i, (name, angle) in enumerate(ANGLES):
        t0 = time.monotonic()
        paths = client.generate(
            "sdxl_lora_img2img", out, timeout=900,
            prompt=LOCK[who] + ", " + angle + ", " + SUFFIX,
            negative=NEG, seed=7000 + i, denoise=denoise, steps=22,
            image=stem, lora_sm=0.8, lora_sc=0.8)
        for p in paths:
            p.replace(out / (name + ".png"))   # replace, not rename: re-runs overwrite
        print("  %-7s %5.1fs" % (name, time.monotonic() - t0), flush=True)
    print("-> " + str(out))


if __name__ == "__main__":
    main()
