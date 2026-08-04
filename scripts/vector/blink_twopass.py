"""Blink by inpainting ONE EYE AT A TIME.

Three rounds of whole-eye-band inpainting (denoise 0.85 -> 0.95, a dozen
phrasings, explicit anti-wink negatives) failed the same way every time:
the model closes exactly one eye and leaves the other open. It is not
ignoring the instruction, it is drawing a wink -- a strong prior in this
style.

So remove the choice. Mask a single eye, and a wink is unreachable: the
only eye in the region either closes or it doesn't. Pass 2 then repeats
on the other eye, using pass 1's composite as its base, so both closures
accumulate into one drawing.

Run from scripts/:  python -m vector.blink_twopass
"""
from __future__ import annotations

import json
import time

import numpy as np
from PIL import Image

from comfy.client import ComfyClient
from comfy.launch import ensure_server
from vector.visemes_ep1 import (VIS, SOL_LOCK, REX_LOCK, SUFFIX, NEG,
                                ellipse_mask, pad8, unpad8, composite_rgb,
                                flatten_white, load_base, load_anchors,
                                now_utc)

POSES = ["sol_point", "rex_shock_v1", "sol_laugh", "sol_wink"]
PHRASES = ["sleeping face, eye closed, curved closed eyelid",
           "eye shut, closed eyelid line, no pupil"]
NEG_EYE = (NEG + ", open eye, pupil, iris, sclera, eyeball"
           ", gradient, glossy, 3d, realistic shading")
# Each eye gets its own ellipse: half the band's width, centred on the
# left/right half of it.
EYE_SPLIT = 0.52      # centre offset as a fraction of the band's rx
EYE_RX = 0.46         # per-eye rx as a fraction of the band's rx


def eye_mask(pose: str, side: str, anchors: dict) -> np.ndarray:
    a = anchors[pose]
    W, H = a["canvas"]
    e = a["eyes"]
    dx = -EYE_SPLIT * e["rx"] if side == "l" else EYE_SPLIT * e["rx"]
    return ellipse_mask(W, H, e["cx"] + dx, e["cy"],
                        EYE_RX * e["rx"], e["ry"])


def main(denoise: float = 0.95) -> None:
    ensure_server()
    anchors = load_anchors()
    client = ComfyClient()
    client._last_family = "sdxl"
    out_dir = VIS / "raw"
    stage = VIS / "staged"
    stage.mkdir(parents=True, exist_ok=True)
    manifest = []
    for pose in POSES:
        rgba = load_base(pose)
        H, W = rgba.shape[:2]
        lock = SOL_LOCK if pose.startswith("sol") else REX_LOCK
        for ci, phrase in enumerate(PHRASES):
            cur = flatten_white(rgba)          # RGB we keep folding into
            t0 = time.monotonic()
            for si, side in enumerate(("l", "r")):
                base_name = f"tp_{pose}_{ci}_{si}_base.png"
                mask_name = f"tp_{pose}_{side}.png"
                padded, box = pad8(cur)
                Image.fromarray(padded).save(stage / base_name)
                ComfyClient.stage_input(stage / base_name)
                mk, _ = pad8(eye_mask(pose, side, anchors))
                Image.fromarray(mk).convert("RGB").save(stage / mask_name)
                ComfyClient.stage_input(stage / mask_name)
                paths = client.generate(
                    "sdxl_lora_inpaint", out_dir, timeout=300,
                    image=base_name, mask=mask_name,
                    prompt=f"{lock}, {phrase}, {SUFFIX}",
                    negative=NEG_EYE, seed=99000 + ci * 10 + si,
                    denoise=denoise)
                gen = unpad8(np.asarray(Image.open(paths[0]).convert("RGB")),
                             box)
                paths[0].unlink()
                cur = composite_rgb(cur, gen, eye_mask(pose, side, anchors))
            name = f"{pose}__blink__tp{ci}"
            Image.fromarray(cur).save(out_dir / f"{name}.png")
            Image.fromarray(np.dstack([cur, rgba[..., 3]])).save(
                VIS / "comp" / f"{name}.png")
            manifest.append({
                "pose": pose, "viseme": "blink", "out": name,
                "method": "two-pass single-eye inpaint",
                "denoise": denoise, "phrase": phrase,
                "seconds": round(time.monotonic() - t0, 1),
                "source": "local ComfyUI sdxl_lora_inpaint "
                          "Illustrious-XL-v0.1 + ana_cast_v1@0.9",
                "source_class": "local-gen", "retrieved_at": now_utc()})
            print(f"  {name}  {manifest[-1]['seconds']}s", flush=True)
    p = VIS / "blink_twopass_manifest.json"
    p.write_text(json.dumps(manifest, indent=1), "utf-8")
    print(f"{len(manifest)} two-pass blinks -> {p}")


if __name__ == "__main__":
    main()
