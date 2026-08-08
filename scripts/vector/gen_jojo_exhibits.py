"""Generate the wall exhibits from the workflow's gated prompt cards.

The cards come from the jojo-exhibit-cards workflow: twelve authored in
parallel, each then torn apart by an adversarial gate. Five needed
correction and the corrected text is what is used here.

The gate earned its keep on capitol_ticker, where it caught something no
negative-prompt token could have: the requested pose - low angle, fist
thrust at the viewer - IS the Stardust Crusaders cover composition. The
leak was structural, not lexical.

ROUTING is per card, decided by the authors: people go to Illustrious
(a character checkpoint - it draws figures well and objects badly, proven
here when six of eight object prompts came back unusable), objects go to
Z-Image. Jobs are ordered so the model family switches exactly once, since
switching families inside one ComfyUI process is a known VRAM-eviction
corruption risk in this repo.

  python scripts/vector/gen_jojo_exhibits.py
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

OUT = REPO / "remotion/public/characters/cast_ep1/exhibits"
CARDS = OUT / "_cards.json"
W, H = 976, 736


def main() -> None:
    cards = json.loads(CARDS.read_text("utf-8"))
    want = set(sys.argv[1:])
    if want:
        cards = [c for c in cards if c["name"] in want]
    # one family switch, not eleven
    cards.sort(key=lambda c: (c["route"] != "illustrious", c["name"]))

    ensure_server()
    client = ComfyClient()
    client._last_family = cards[0]["route"].replace("illustrious", "sdxl")

    rows = []
    for i, c in enumerate(cards):
        tmpl = ("sdxl_lora_t2i" if c["route"] == "illustrious"
                else "zimage_t2i")
        kw = dict(prompt=c["prompt"], negative=c["negative"],
                  width=W, height=H, seed=3100 + i * 37)
        if tmpl == "sdxl_lora_t2i":
            kw.update(lora_sm=0.0, lora_sc=0.0)   # never the cast LoRA
        t0 = time.monotonic()
        paths = client.generate(tmpl, OUT, timeout=600, **kw)
        dest = OUT / (c["name"] + ".png")
        if dest.exists():
            dest.unlink()
        paths[0].replace(dest)
        secs = time.monotonic() - t0
        rows.append({"name": c["name"], "file": c["name"] + ".png",
                     "route": c["route"], "template": tmpl,
                     "seed": 3100 + i * 37, "seconds": round(secs, 1),
                     "gate_clean": c["passed_clean"],
                     "gate_fixes": len(c["problems"]),
                     "source": "local ComfyUI " + tmpl,
                     "source_class": "local-gen",
                     "retrieved_at": datetime.now(timezone.utc)
                     .strftime("%Y-%m-%dT%H:%M:%SZ")})
        print("  %-18s %-11s %5.1fs" % (c["name"], c["route"], secs),
              flush=True)

    (OUT / "provenance.json").write_text(json.dumps(rows, indent=1), "utf-8")
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
