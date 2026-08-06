"""Generate BROW/EYE expression variants by masked inpainting.

WHY THIS IS THE NEXT GAP, by beat count rather than by taste.

Arm variants fixed the wide shots. They do almost nothing for the busts,
and the busts are most of the episode: sol_smug_v1 is 12 of 39 beats and
shows barely any body at all. On a bust the only thing that can act is the
face, and the only part of the face the viseme system is not already
driving is the brows and the eyes.

So the mask is the hand-placed EYES ellipse from anchors_ep1.json - the
same geometry the blink pass uses, already verified on the debug sheet -
and nothing else. The mouth stays outside it and stays viseme-driven, so
expressions and speech compose instead of fighting: an expression changes
the brows while the mouth keeps forming words.

Everything outside the ellipse is pasted back from the base, so identity
is exact and an expression cannot drift the character.

  python scripts/vector/expression_variants.py            # all rigged poses
  python scripts/vector/expression_variants.py sol_smug_v1
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
from vector.cells import white_bg_to_alpha     # noqa: E402

RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
ANCHORS = REPO / "content/vector_char/cast/ep_fairmarket/visemes/anchors_ep1.json"
OUT = REPO / "content/vector_char/cast/ep_fairmarket/expressions"
FIX = REPO / "remotion/src/fixtures/cast_ep1"

LOCK = {
    "sol": "solquant, 1boy, solo, old man, gray hair, thick mustache, "
           "bushy gray eyebrows",
    "rex": "rexquant, 1boy, solo, young man, orange hair, glasses",
}
SUFFIX = ("flat color, thick clean black outlines, cel shading, "
          "white background, masterpiece, best quality")
NEG = ("worst quality, low quality, blurry, deformed, different character, "
       "changing hairstyle, closed eyes, text, watermark, multiple views")

# Brows and eyes only. Each is a readable acting state a presenter uses;
# none of them touch the mouth, which the visemes own.
EXPRESSIONS = [
    ("brow_raise", "eyebrows raised high, eyes wide, interested"),
    ("brow_furrow", "eyebrows furrowed down, stern serious glare"),
    ("squint",     "eyes narrowed, squinting, skeptical"),
    ("side_eye",   "eyes looking to the side, glancing sideways"),
    ("wide",       "eyes very wide open, surprised, alarmed"),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pad8(a: np.ndarray):
    h, w = a.shape[:2]
    ph, pw = (-h) % 8, (-w) % 8
    if not ph and not pw:
        return a, (h, w)
    return np.pad(a, [(0, ph), (0, pw)] + [(0, 0)] * (a.ndim - 2),
                  mode="edge"), (h, w)


def flatten_white(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3:4].astype(float) / 255.0
    return (rgba[..., :3] * a + 255 * (1 - a)).astype(np.uint8)


def eye_mask(w: int, h: int, e: dict) -> np.ndarray:
    """The verified eyes ellipse, grown a little upward to take in the brows.

    Brows sit ABOVE the eye band and they carry most of an expression - a
    mask tight to the eyes alone changes the pupils and leaves the face
    reading exactly the same.
    """
    im = Image.new("L", (w, h), 0)
    ry = e["ry"] * 1.55
    cy = e["cy"] - e["ry"] * 0.35
    ImageDraw.Draw(im).ellipse(
        [e["cx"] - e["rx"] * 1.08, cy - ry,
         e["cx"] + e["rx"] * 1.08, cy + ry], fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(7)))


def composite(base, gen, mask):
    m = (mask.astype(float) / 255.0)[..., None]
    return (gen * m + base * (1 - m)).astype(np.uint8)


def run(pose: str, client, anchors: dict, denoise: float) -> int:
    who = "sol" if pose.startswith("sol") else "rex"
    src = RENDERS / ("_" + pose + "_rgba.png")
    if not src.exists() or pose not in anchors:
        print("  %-16s no render/anchor - skipped" % pose)
        return 0
    rgba = np.asarray(Image.open(src).convert("RGBA"))
    base = flatten_white(rgba)
    H, W = base.shape[:2]
    mk = eye_mask(W, H, anchors[pose]["eyes"])

    out = OUT / pose
    out.mkdir(parents=True, exist_ok=True)
    stage = out / "_stage"
    stage.mkdir(exist_ok=True)
    bp, _ = pad8(base)
    mp, _ = pad8(mk)
    Image.fromarray(bp).save(stage / ("ex_%s_base.png" % pose))
    Image.fromarray(mp).convert("RGB").save(stage / ("ex_%s_mask.png" % pose))
    ComfyClient.stage_input(stage / ("ex_%s_base.png" % pose))
    ComfyClient.stage_input(stage / ("ex_%s_mask.png" % pose))

    man = []
    for i, (name, desc) in enumerate(EXPRESSIONS):
        t0 = time.monotonic()
        paths = client.generate(
            "sdxl_lora_inpaint", out, timeout=600,
            image="ex_%s_base.png" % pose, mask="ex_%s_mask.png" % pose,
            prompt=LOCK[who] + ", " + desc + ", " + SUFFIX,
            negative=NEG, seed=6200 + i * 17, denoise=denoise)
        gen = np.asarray(Image.open(paths[0]).convert("RGB"))[:H, :W]
        Image.fromarray(white_bg_to_alpha(composite(base, gen, mk))).save(
            out / (name + ".png"))
        paths[0].unlink()
        man.append({"pose": pose, "expression": name, "prompt": desc,
                    "denoise": denoise, "seed": 6200 + i * 17,
                    "seconds": round(time.monotonic() - t0, 1),
                    "source": "local ComfyUI sdxl_lora_inpaint "
                              "Illustrious-XL-v0.1 + ana_cast_v1",
                    "source_class": "local-gen", "retrieved_at": now_utc()})
    (out / "manifest.json").write_text(json.dumps(man, indent=1), "utf-8")

    tiles = [("BASE", Image.fromarray(base))] + [
        (n, Image.open(out / (n + ".png")).convert("RGB"))
        for n, _ in EXPRESSIONS]
    ht = 360
    wt = int(tiles[0][1].width * ht / tiles[0][1].height)
    sheet = Image.new("RGB", (wt * len(tiles), ht + 24), "white")
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(tiles):
        sheet.paste(im.resize((wt, ht)), (i * wt, 24))
        d.text((i * wt + 6, 6), n, fill=(0, 0, 0))
    sheet.save(out / "contact_sheet.png")
    print("  %-16s %d expressions" % (pose, len(EXPRESSIONS)))
    return len(EXPRESSIONS)


def main() -> None:
    anchors = json.loads(ANCHORS.read_text("utf-8"))
    rig = json.loads((FIX / "rig_parts.json").read_text("utf-8"))
    denoise = float(sys.argv[sys.argv.index("--denoise") + 1]
                    if "--denoise" in sys.argv else 0.80)
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    poses = only or [p for p in anchors if p in rig]
    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    total = sum(run(p, client, anchors, denoise) for p in poses)
    print("\n%d expression drawings -> %s" % (total, OUT))


if __name__ == "__main__":
    main()
