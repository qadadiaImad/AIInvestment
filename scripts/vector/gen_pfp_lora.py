"""Generate the profile-picture portrait with the cast LoRA.

The first PFP was a composite of existing render pixels - safe, but the
owner asked for a real portrait generated from the LoRA instead. That means
the two characters have to appear in ONE frame, which is the hard case for
a character LoRA: two trigger words in one prompt blend into a single
chimera with Sol's moustache on Rex's hair.

So two routes are generated and judged side by side:

  regional  sdxl_lora_regional2 - separate prompts bound to the left and
            right halves of the canvas, which is what that workflow exists
            for. Correct in principle; regional masks can still bleed.
  solo      each character generated alone at portrait crop, then paired.
            No blending risk at all, at the cost of two separate lightings.

Square 1024, because a PFP is square and generating wide then cropping
throws away the composition the sampler chose.

The LoRA triggers are `solquant` and `rexquant` - not optional, they are
what selects the trained identity. Lifted verbatim from pose_variants.LOCK
so the faces match the show rather than being a fourth interpretation.

  python scripts/vector/gen_pfp_lora.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

OUT = REPO / "content/brand/lora"

# verbatim from pose_variants.LOCK - the trained identity, not a description
SOL = ("solquant, 1boy, old man, gray hair, thick mustache, burgundy "
       "cardigan, white shirt, yellow bow tie, plump")
REX = ("rexquant, 1boy, young man, orange hair, glasses, gray vest, "
       "white shirt")

STYLE = ("upper body portrait, facing viewer, warm friendly expression, "
         "cel shading, thick clean black outlines, flat color, "
         "dark navy studio background, soft rim light, "
         "centered composition, masterpiece, best quality")
NEG = ("worst quality, low quality, blurry, deformed, extra limbs, "
       "extra arms, mutated hands, bad hands, extra fingers, text, "
       "watermark, letters, signature, logo, full body, tiny head, "
       "cluttered background, multiple views, cropped head")

# (name, kind, payload)
JOBS = [
    ("duo_regional", "regional", {
        "prompt_base": ("2boys, sitting together at a news desk, upper body "
                        "portrait, " + STYLE),
        "prompt_left": REX + ", looking at viewer, eager smile",
        "prompt_right": SOL + ", looking at viewer, wry knowing smile",
    }),
    ("duo_regional_b", "regional", {
        "prompt_base": ("2boys, close together, upper body portrait, "
                        "shoulder to shoulder, " + STYLE),
        "prompt_left": REX + ", slight smile, looking at viewer",
        "prompt_right": SOL + ", warm smile, looking at viewer",
    }),
    ("sol_portrait", "solo", {"prompt": SOL + ", solo, " + STYLE}),
    ("sol_portrait_b", "solo", {
        "prompt": SOL + ", solo, arms crossed, confident, " + STYLE}),
    ("rex_portrait", "solo", {"prompt": REX + ", solo, " + STYLE}),
    ("rex_portrait_b", "solo", {
        "prompt": REX + ", solo, holding a tablet, eager, " + STYLE}),
]


def main() -> None:
    want = set(sys.argv[1:])
    jobs = [j for j in JOBS if not want or j[0] in want]
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"

    rows = []
    for i, (name, kind, payload) in enumerate(jobs):
        t0 = time.monotonic()
        if kind == "regional":
            # regional2 has no width/height/lora knobs exposed; it ships at
            # its own canvas with the cast LoRA already loaded
            paths = client.generate("sdxl_lora_regional2", OUT, timeout=600,
                                    negative=NEG, seed=2600 + i * 41,
                                    **payload)
        else:
            paths = client.generate("sdxl_lora_t2i", OUT, timeout=600,
                                    negative=NEG, seed=2600 + i * 41,
                                    width=1024, height=1024, **payload)
        dest = OUT / (name + ".png")
        if dest.exists():
            dest.unlink()
        paths[0].replace(dest)
        secs = time.monotonic() - t0
        rows.append({"name": name, "file": name + ".png", "kind": kind,
                     "seed": 2600 + i * 41, "seconds": round(secs, 1),
                     "source": "local ComfyUI Illustrious-XL-v0.1 + "
                               "ana_cast_v1 (cast LoRA ON)",
                     "source_class": "local-gen",
                     "retrieved_at": datetime.now(timezone.utc)
                     .strftime("%Y-%m-%dT%H:%M:%SZ")})
        print("  %-16s %-9s %5.1fs" % (name, kind, secs), flush=True)

    (OUT / "provenance.json").write_text(json.dumps(rows, indent=1), "utf-8")
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
