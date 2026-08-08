"""Probe an ARCADE-FIGHTER art direction for the wall, as an alternative to JoJo.

The owner looked at the politician caricature probes and said they read like
arcade games rather than JoJo, and asked whether that could be used
deliberately - miming arcade-game movement to land jokes and opinions.

Worth taking seriously, because the genre solves three problems this repo
keeps paying for:

  * NUMBERS. House rule: code owns every number, a generated image may never
    carry a figure. An arcade HUD - health bar, timer, score, combo counter,
    VS plate - is a code layer BY NATURE. The art becomes the stage and the
    fighters; Remotion draws the whole interface on top, sharp and correct.
  * IP LEAK. Naming "JoJo" is load-bearing for that look and keeps dragging
    Jotaro into frame - four of five gate failures were exactly that. "1990s
    arcade fighting game" is a GENRE, not one rights-holder's character, so
    the style anchor does not come with a person attached.
  * MOTION. The house animation rules already are sprite rules: anticipation,
    volume-preserving squash and stretch, 2-frame smears, three-beat holds,
    ~1 cut/second. Arcade sprites are built from a handful of extreme poses
    held hard and cut between - cheap to produce and exactly the grammar in
    motion/toon.ts.

Three probes, one per staging idea:
  select   - character-select portrait, the format for introducing a figure
  versus   - two fighters squared off on a stage, the format for a conflict
  stance   - a single full-body fighting stance, the format for a sprite rig

All three deliberately leave the top and bottom of the frame quiet, because
that is where a code-drawn HUD would sit.

  python scripts/vector/arcade_probe.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

OUT = REPO / "remotion/public/characters/cast_ep1/exhibits/_probe"

# Genre, not franchise. Pixel-adjacent but still clean vector-traceable
# flats, because the downstream path is Z-Image -> vtracer -> SVG rig.
STYLE = (
    "Drawn in the style of a 1990s Japanese arcade fighting game: bold "
    "hand-inked character art with thick black outlines, flat cel-shaded "
    "colour blocks, hard specular highlights and a strong rim light, high "
    "contrast and highly saturated within a controlled range. Deep navy and "
    "near-black stage, warm amber key light, burgundy and muted teal "
    "accents. Every surface is smooth, blank and unmarked, with no letters, "
    "numerals, signage or logos anywhere. The artwork fills the entire wide "
    "horizontal frame edge to edge, leaving the top and the bottom strips of "
    "the frame visually quiet and uncluttered."
)

JOBS = [
    ("arc_select",
     "An arcade fighting game character-select portrait: a caricature of "
     "Donald Trump, the American president, in a dark navy suit and long red "
     "necktie, shown from the chest up, turned three-quarters to the viewer, "
     "chin lifted, fists raised into a boxing guard, glaring straight out of "
     "the frame. He is lit from below by a hard amber spotlight against a "
     "flat dark navy backdrop, framed by a simple glowing rectangular panel "
     "of plain colour behind his shoulders. "),

    ("arc_versus",
     "Two arcade fighting game characters squared off against each other on "
     "a stage, seen from a low ringside angle: on the left a caricature of "
     "Donald Trump, the American president, in a dark navy suit and long red "
     "necktie, leaning forward with fists clenched; on the right a "
     "caricature of Nancy Pelosi, the former Speaker of the United States "
     "House of Representatives, in a burgundy skirt suit, standing balanced "
     "and composed with one hand raised flat. A wide dark gap of empty stage "
     "separates them at the centre of the frame. Behind them rises a dim "
     "amber-lit crowd of featureless silhouetted spectators. "),

    ("arc_stance",
     "A single arcade fighting game character sprite, full body, standing in "
     "a wide braced fighting stance at the centre of a dark stage, seen from "
     "a straight-on side-scrolling camera at eye level: a caricature of "
     "Donald Trump, the American president, in a dark navy suit and long red "
     "necktie, knees bent, weight low, both fists up in guard, coat tails "
     "flaring outward. The stage floor is a plain dark platform and the "
     "background is a deep navy void with a single amber spotlight pool "
     "around his feet. "),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_server()
    client = ComfyClient()
    client._last_family = "zimage"
    for i, (name, body) in enumerate(JOBS):
        t0 = time.monotonic()
        paths = client.generate("zimage_t2i", OUT, timeout=600,
                                prompt=body + STYLE, negative="",
                                width=976, height=736, seed=7300 + i)
        dest = OUT / (name + ".png")
        if dest.exists():
            dest.unlink()
        paths[0].replace(dest)
        print(f"  {name:12s} {time.monotonic() - t0:5.1f}s", flush=True)
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
