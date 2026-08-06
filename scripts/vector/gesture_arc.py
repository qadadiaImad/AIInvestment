"""Generate a single gesture ARC: one motion, sampled at N positions.

THE LAST MONTAGE SMELL. After palette lock and shortest-path ordering, the
sweep is smooth in position but the HAND still morphs along it - point,
open palm, two fingers - because the variant vocabulary is eight DIFFERENT
gestures. Real animation draws one gesture at several positions. So this
generates exactly that: the same open-palm presenting motion at five
heights, arm-at-side to arm-raised.

Two things hold the shape together across samples:
  · every prompt names the SAME hand ("palm open"), varying only position;
  · every step uses the SAME seed - same seed + near-same prompt keeps the
    model's layout choices, so the sleeve folds and hand construction stay
    siblings instead of strangers.

Published, an arc REPLACES the pose's ladder (mixing it with the old
vocabulary would reintroduce the shape morphing it exists to remove).

  python scripts/vector/gesture_arc.py sol_point rex_skeptic
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402
from vector.pose_variants import (             # noqa: E402
    LOCK, NEG, SUFFIX, body_mask, flatten_white, pad8, composite)
from vector.cells import white_bg_to_alpha     # noqa: E402

RENDERS = REPO / "content/vector_char/cast/ep_fairmarket/renders"
OUT = REPO / "content/vector_char/cast/ep_fairmarket/arcs"
FIX = REPO / "remotion/src/fixtures/cast_ep1"

# One gesture, five positions, low to high. The hand is "palm open" in
# every line; only the arm's position moves.
# Weighted position terms, because the first run proved the seed wins a
# fair fight: with one seed and plain prompts, arcs 1-4 came back as near
# clones of the base with the finger at the same height. Position gets
# weight 1.4, the hand shape is named identically in every step, and the
# base pose's own gesture ("pointing, index finger") is negated so the
# model cannot just keep it.
ARC = [
    ("arc0", "(pointing his index finger downward:1.3), arm lowered"),
    ("arc1", "(arm low, pointing index finger forward at waist height:1.3)"),
    ("arc2", "(pointing index finger at the viewer, arm at chest "
             "height:1.3)"),
    ("arc3", "(arm extended, pointing index finger forward at shoulder "
             "height:1.3)"),
    ("arc4", "(arm raised, pointing index finger up high:1.3)"),
]
# No anti-point negative: v2 negated "pointing, index finger" and the model
# answered with truncated forearms and missing hands - that hand shape is
# what the LoRA knows best. The arc now keeps the point in every step and
# moves only the arm, which is also simply Sol's signature gesture.
ARC_NEG = ""
SEED = 7777


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(pose: str, client, denoise: float) -> int:
    who = "sol" if pose.startswith("sol") else "rex"
    src = RENDERS / ("_" + pose + "_rgba.png")
    if not src.exists():
        print("  %-16s no render - skipped" % pose)
        return 0
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
    Image.fromarray(bp).save(stage / ("ga_%s_base.png" % pose))
    Image.fromarray(mp).convert("RGB").save(stage / ("ga_%s_mask.png" % pose))
    ComfyClient.stage_input(stage / ("ga_%s_base.png" % pose))
    ComfyClient.stage_input(stage / ("ga_%s_mask.png" % pose))

    man = []
    for i, (name, desc) in enumerate(ARC):
        t0 = time.monotonic()
        paths = client.generate(
            "sdxl_lora_inpaint", out, timeout=600,
            image="ga_%s_base.png" % pose, mask="ga_%s_mask.png" % pose,
            prompt=LOCK[who] + ", " + desc + ", " + SUFFIX,
            negative=NEG + ARC_NEG, seed=SEED + i * 31, denoise=denoise)
        gen = np.asarray(Image.open(paths[0]).convert("RGB"))[:H, :W]
        Image.fromarray(white_bg_to_alpha(composite(base, gen, mk))).save(
            out / (name + ".png"))
        paths[0].unlink()
        man.append({"pose": pose, "step": name, "prompt": desc,
                    "seed": SEED, "denoise": denoise,
                    "seconds": round(time.monotonic() - t0, 1),
                    "source": "local ComfyUI sdxl_lora_inpaint "
                              "Illustrious-XL-v0.1 + ana_cast_v1",
                    "source_class": "local-gen", "retrieved_at": now_utc()})
        print("  %s %-5s %5.1fs" % (pose, name, time.monotonic() - t0),
              flush=True)
    (out / "manifest.json").write_text(json.dumps(man, indent=1), "utf-8")

    tiles = [("BASE", Image.fromarray(base))] + [
        (n, Image.open(out / (n + ".png")).convert("RGB")) for n, _ in ARC]
    ht = 400
    wt = int(tiles[0][1].width * ht / tiles[0][1].height)
    sheet = Image.new("RGB", (wt * len(tiles), ht + 24), "white")
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(tiles):
        sheet.paste(im.resize((wt, ht)), (i * wt, 24))
        d.text((i * wt + 6, 6), n, fill=(0, 0, 0))
    sheet.save(out / "contact_sheet.png")
    return len(ARC)


def main() -> None:
    denoise = float(sys.argv[sys.argv.index("--denoise") + 1]
                    if "--denoise" in sys.argv else 0.88)
    poses = [a for a in sys.argv[1:] if not a.startswith("--")] or [
        "sol_point", "sol_point_v1", "rex_skeptic", "rex_eager"]
    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    total = sum(run(p, client, denoise) for p in poses)
    print("\n%d arc drawings -> %s" % (total, OUT))


if __name__ == "__main__":
    main()
