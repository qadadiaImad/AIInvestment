"""Give Rex ordinary eyes.

rex_eager is drawn with star/glint pupils — a permanent "excited" signal
baked into the artwork, so he wears it while asking a neutral question,
while listening, and while being corrected. Owner: normal eyes until an
emotion actually calls for more.

The glint sits inside the eye, so this is the viseme technique pointed at
a different region: mask the eyes, regenerate calm ones, composite back
so everything outside the mask stays pixel-identical. It is an easier ask
than the blinks that failed five rounds — those needed the model to CLOSE
an eye against a strong open-eye prior; this only restyles an open eye,
which the prior is happy to do.

Produces a parallel pose `rex_calm` (+ its visemes) so the glint version
is still available for the beats that have earned it.

Run from scripts/:  python -m vector.calm_eyes
"""
from __future__ import annotations

import json
import time

import numpy as np
from PIL import Image

from comfy.client import ComfyClient
from comfy.launch import ensure_server
from vector.visemes_ep1 import (VIS, REX_LOCK, SUFFIX, NEG, ellipse_mask,
                                pad8, unpad8, composite_rgb, flatten_white,
                                load_base, load_anchors, now_utc)

SRC_POSE = "rex_eager"
OUT_POSE = "rex_calm"
PHRASES = [
    "calm neutral expression, plain simple eyes, ordinary black pupils",
    "relaxed face, normal round eyes, plain dark pupils, no highlights",
]
NEG_EYE = (NEG + ", sparkle, sparkling eyes, star eyes, glint, glowing eyes, "
           "shiny eyes, starry eyes, excited, gradient, glossy" )
# The eye band from anchor_overrides is sized for BLINK masking (brows
# included). For a restyle the mask hugs the eyes themselves, so the
# brows — which carry the expression — survive untouched.
EYE_RX = 0.86
EYE_RY = 0.72


def eye_mask(anchors: dict) -> np.ndarray:
    a = anchors[SRC_POSE]
    W, H = a["canvas"]
    e = a["eyes"]
    return ellipse_mask(W, H, e["cx"], e["cy"],
                        EYE_RX * e["rx"], EYE_RY * e["ry"])


def main(denoise: float = 0.72) -> None:
    ensure_server()
    anchors = load_anchors()
    client = ComfyClient()
    client._last_family = "sdxl"
    picks = json.loads((VIS / "picks_final.json").read_text("utf-8"))
    out_dir = VIS / "calm"
    out_dir.mkdir(parents=True, exist_ok=True)
    stage = VIS / "staged"

    base_rgba = load_base(SRC_POSE)
    H, W = base_rgba.shape[:2]
    mask = eye_mask(anchors)
    mk, _ = pad8(mask)
    mask_name = f"calm_{SRC_POSE}_eyes.png"
    Image.fromarray(mk).convert("RGB").save(stage / mask_name)
    ComfyClient.stage_input(stage / mask_name)

    # base drawing plus every gated viseme of it
    sources = [("base", flatten_white(base_rgba))]
    for vis, cand in picks.get(SRC_POSE, {}).items():
        p = VIS / "comp" / f"{cand}.png"
        if p.exists():
            sources.append(
                (vis, np.asarray(Image.open(p).convert("RGB"))))

    manifest = []
    for vis, rgb in sources:
        for ci, phrase in enumerate(PHRASES):
            t0 = time.monotonic()
            padded, box = pad8(rgb)
            base_name = f"calm_{SRC_POSE}_{vis}_{ci}.png"
            Image.fromarray(padded).save(stage / base_name)
            ComfyClient.stage_input(stage / base_name)
            paths = client.generate(
                "sdxl_lora_inpaint", out_dir, timeout=300,
                image=base_name, mask=mask_name,
                prompt=f"{REX_LOCK}, {phrase}, {SUFFIX}",
                negative=NEG_EYE, seed=76000 + ci * 50 + len(manifest),
                denoise=denoise)
            gen = unpad8(np.asarray(Image.open(paths[0]).convert("RGB")), box)
            paths[0].unlink()
            comp = composite_rgb(rgb, gen, mask)
            name = f"{OUT_POSE}__{vis}__c{ci}"
            Image.fromarray(np.dstack([comp, base_rgba[..., 3]])).save(
                out_dir / f"{name}.png")
            manifest.append({"pose": OUT_POSE, "viseme": vis, "out": name,
                             "phrase": phrase, "denoise": denoise,
                             "seconds": round(time.monotonic() - t0, 1),
                             "source": "local ComfyUI sdxl_lora_inpaint "
                                       "Illustrious-XL-v0.1 + ana_cast_v1@0.9",
                             "source_class": "local-gen",
                             "retrieved_at": now_utc()})
            print(f"  {name}  {manifest[-1]['seconds']}s", flush=True)
    (out_dir / "provenance.json").write_text(json.dumps(manifest, indent=1),
                                             "utf-8")
    print(f"{len(manifest)} calm-eye candidates -> {out_dir}")


if __name__ == "__main__":
    main()
