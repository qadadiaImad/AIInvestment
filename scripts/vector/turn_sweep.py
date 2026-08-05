"""Find the denoise where a turn actually happens.

img2img at 0.62 held identity perfectly and turned nothing: the anchor
latent carries the composition, and "three quarter view" in the prompt
cannot fight it. Too high and the LoRA is the only identity left. This
sweeps the band and prints a sheet so the trade-off is visible rather
than guessed at.
"""
from __future__ import annotations
import sys, time
from pathlib import Path
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

OUT = REPO / "content/vector_char/cast/ep_fairmarket/turnaround/sweep"
CI = Path.home() / "Documents" / "ComfyUI" / "input"
LOCK = ("solquant, 1boy, solo, old man, gray hair, thick mustache, "
        "burgundy cardigan, yellow bow tie, plump, full body, standing")
ANGLE = ("three quarter view, body turned 45 degrees away from viewer, "
         "head turned to the side, shoulder toward the camera")
SUF = ("flat color, thick clean black outlines, cel shading, "
       "simple background, white background, masterpiece, best quality")
NEG = ("worst quality, low quality, blurry, deformed, extra limbs, "
       "front view, facing viewer, multiple views, text, watermark")

ensure_server(); c = ComfyClient(); c._last_family = "sdxl"
OUT.mkdir(parents=True, exist_ok=True)
tiles = [("anchor", Image.open(CI / "turn_src_sol_point.png").convert("RGB"))]
for dn in (0.72, 0.82, 0.92):
    t0 = time.monotonic()
    p = c.generate("sdxl_lora_img2img", OUT, timeout=900,
                   prompt=LOCK + ", " + ANGLE + ", " + SUF, negative=NEG,
                   seed=7101, denoise=dn, steps=24,
                   image="turn_src_sol_point.png", lora_sm=0.85, lora_sc=0.85)
    dst = OUT / ("i2i_%.2f.png" % dn); p[0].replace(dst)
    tiles.append(("i2i %.2f" % dn, Image.open(dst).convert("RGB")))
    print("  i2i %.2f  %.1fs" % (dn, time.monotonic() - t0), flush=True)
# pure text2img: LoRA alone carries identity, nothing constrains the pose
for sm in (0.85, 1.0):
    t0 = time.monotonic()
    p = c.generate("sdxl_lora_t2i", OUT, timeout=900,
                   prompt=LOCK + ", " + ANGLE + ", " + SUF, negative=NEG,
                   seed=7101, width=768, height=1152,
                   lora_sm=sm, lora_sc=sm)
    dst = OUT / ("t2i_%.2f.png" % sm); p[0].replace(dst)
    tiles.append(("t2i lora %.2f" % sm, Image.open(dst).convert("RGB")))
    print("  t2i %.2f  %.1fs" % (sm, time.monotonic() - t0), flush=True)

H = 500
sheet = Image.new("RGB", (sum(int(i.width*H/i.height) for _, i in tiles), H+26), "white")
dr = ImageDraw.Draw(sheet); x = 0
for n, i in tiles:
    w = int(i.width*H/i.height); sheet.paste(i.resize((w, H)), (x, 26))
    dr.text((x+6, 7), n, fill=(0, 0, 0)); x += w
sheet.save(OUT / "sweep.png"); print("->", OUT / "sweep.png")
