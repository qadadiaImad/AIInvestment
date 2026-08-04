"""Generate the CONGRESS caricature the exhibit beats currently lack.

The episode talks about a filing, a Speaker's household and an ETF that
copies lawmakers, and shows only a text card while it does. A stylised
lawmaker on screen carries that far better than a paragraph.

Rails, because this one has them: the figure is a generic senior-lawmaker
ARCHETYPE — silver bob, dark suit, gavel — drawn as flat caricature, not
a likeness of any named individual, and no on-screen text ever names a
person. The episode's own footer already carries "parody · public record
· educational, not advice · not an accusation", and the exhibit card
states only what the public filing states.

Run from scripts/:  python -m vector.gen_congress
"""
from __future__ import annotations

import json
import time

from comfy.client import ComfyClient
from comfy.launch import ensure_server
from vector.visemes_ep1 import VIS, now_utc

OUT = VIS.parent / "congress"


def main() -> None:
    ensure_server()
    client = ComfyClient()
    client._last_family = "sdxl"
    jobs = json.loads((VIS / "congress_jobs.json").read_text("utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for n, j in enumerate(jobs, 1):
        t0 = time.monotonic()
        paths = client.generate(
            "sdxl_lora_t2i", OUT, timeout=300,
            prompt=j["prompt"], negative=j["negative"], seed=j["seed"],
            width=j["width"], height=j["height"],
            # the cast LoRA is three specific characters; at full strength
            # it drags a new figure toward them, so it is held low and
            # used only for the flat-line house style.
            lora_sm=0.55, lora_sc=0.55)
        paths[0].rename(OUT / f"{j['name']}.png")
        manifest.append({**j, "seconds": round(time.monotonic() - t0, 1),
                         "source": "local ComfyUI sdxl_lora_t2i "
                                   "Illustrious-XL-v0.1 + ana_cast_v1@0.3",
                         "source_class": "local-gen",
                         "retrieved_at": now_utc()})
        print(f"[{n}/{len(jobs)}] {j['name']} "
              f"{manifest[-1]['seconds']}s", flush=True)
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=1),
                                         "utf-8")
    print(f"{len(manifest)} caricatures -> {OUT}")


if __name__ == "__main__":
    main()
