"""Generate the art for the arcade-fighter comparison cut.

The owner asked to see the arcade direction built out alongside the current
one before choosing. The whole point of the genre here is that the
INTERFACE is code: health bars, round timer, combo counter, VS plate and
every numeral are drawn by Remotion in `motion/ArcadeHUD.tsx`, sharp and
correct, over flat generated art. So these prompts deliberately produce
STAGES AND FIGHTERS ONLY, with the top and bottom strips of every frame
left quiet for the HUD to sit in, and every surface blank.

Same measured Z-Image rules as the wall exhibits: prose not tags, no
negation (cfg=1 makes the negative inert and "no X" in the positive just
injects X), no domain term with a literal homonym, and any prop that must
stay clean is described as completely blank rather than blank-ish.

  python scripts/vector/arcade_assets.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

OUT = REPO / "remotion/public/characters/cast_ep1/arcade"

STYLE = (
    "Drawn in the style of a 1990s Japanese arcade fighting game: bold "
    "hand-inked art with thick black contour outlines, flat cel-shaded "
    "colour blocks, hard specular highlights and a strong warm rim light, "
    "high contrast. Deep navy and near-black stage, warm amber key light, "
    "burgundy and muted teal accents. Every surface is smooth, blank and "
    "unmarked. The artwork fills the entire wide horizontal frame edge to "
    "edge, and the top strip and the bottom strip of the frame are left "
    "visually quiet and uncluttered."
)

JOBS = [
    ("stage_floor",
     "An empty arcade fighting game stage seen from a straight-on "
     "side-scrolling camera at eye level: a broad raised platform of dark "
     "polished stone runs the full width of the frame, lit by one warm "
     "amber spotlight pool at its centre. Behind and above it, tiers of "
     "featureless silhouetted spectators recede into deep navy haze, their "
     "shapes simplified to flat dark blocks. Two tall unlit banner poles "
     "stand at the far left and far right edges, their banners plain, "
     "smooth and completely blank. No fighters or people stand on the "
     "platform itself, which is bare and empty. "),

    ("fighter_pelosi",
     "A single arcade fighting game character, full body, standing in a "
     "composed balanced fighting stance at the centre of a plain dark "
     "stage, seen from a straight-on side-scrolling camera at eye level: a "
     "caricature of Nancy Pelosi, the former Speaker of the United States "
     "House of Representatives, in a burgundy skirt suit, weight settled on "
     "her back foot, one hand raised flat and open in front of her in a "
     "measured guard, chin level. The background is a flat deep navy void "
     "with a single soft amber spotlight pool around her feet. "),

    ("fighter_retail",
     "A single arcade fighting game character, full body, standing in an "
     "eager forward-leaning fighting stance at the centre of a plain dark "
     "stage, seen from a straight-on side-scrolling camera at eye level: a "
     "young retail investor in his twenties with short neatly combed dark "
     "hair, a plain pale blue dress shirt with the sleeves rolled to the "
     "elbow and a loosened burgundy tie, both fists raised in an untrained "
     "guard, knees bent, looking determined and slightly out of his depth. "
     "The background is a flat deep navy void with a single soft amber "
     "spotlight pool around his feet. "),
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
                                width=976, height=736, seed=7500 + i)
        dest = OUT / (name + ".png")
        if dest.exists():
            dest.unlink()
        paths[0].replace(dest)
        print("  %-16s %5.1fs" % (name, time.monotonic() - t0), flush=True)
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
