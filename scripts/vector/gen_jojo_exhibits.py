"""Generate the wall exhibits from the workflow's gated prompt cards.

The cards come from the jojo-exhibit-cards workflow: twelve authored in
parallel, each then torn apart by an adversarial gate. Five needed
correction and the corrected text is what is used here.

The gate earned its keep on capitol_ticker, where it caught something no
negative-prompt token could have: the requested pose - low angle, fist
thrust at the viewer - IS the Stardust Crusaders cover composition. The
leak was structural, not lexical.

ROUTING: everything goes to Z-Image. The first pass split people to
Illustrious-XL and objects to Z-Image on the theory that a character
checkpoint draws figures better. All eight Illustrious cards came back
unusable - blob subjects, the palette collapsed to sepia, and two carried
garbled fake-Japanese lettering baked across the frame despite a negative
prompt forbidding text. All four Z-Image cards came back clean first try.

The deeper reason the reroute alone was not enough: the two models want
different PROMPT GRAMMAR. Illustrious is SDXL and eats danbooru tag soup
("1man, solo, dark navy suit, ..."); Z-Image Turbo is driven by a
Qwen-3-4B text encoder and wants flowing prose. The cards were rewritten
accordingly (see prompt_illustrious_orig on each card for what failed).

Note also that zimage_t2i samples at cfg=1, so there is no
classifier-free guidance and the negative prompt has NO effect. Every
constraint - no text, restrained palette, full bleed - has to be stated
positively inside the prose.

Jobs are still ordered so the model family switches at most once, since
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

    # MERGE, never overwrite: a partial run (the usual case - regenerating
    # the few that failed) must not delete the provenance of the exhibits
    # it did not touch.
    prov = OUT / "provenance.json"
    old = json.loads(prov.read_text("utf-8")) if prov.exists() else []
    merged = {r["name"]: r for r in old}
    merged.update({r["name"]: r for r in rows})
    prov.write_text(json.dumps(sorted(merged.values(),
                                      key=lambda r: r["name"]), indent=1),
                    "utf-8")
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
