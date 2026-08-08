"""Second polish pass on ep.2, from the visual gate's borderline calls.

The gate marked four exhibits borderline and they were shipped anyway. On
review only two are worth the risk of a fresh sample:

  * ep2_what_to_watch - five plain wooden cubes are scattered around the
    telescope for no reason. They are not a metaphor for anything; they are
    clutter, and this is the CLOSING image of the episode. Rebuilt as a
    telescope on a tripod actually aimed at something.
  * ep2_empty_docket - the cage rendered pink/magenta, which the series
    palette rule explicitly excludes, and the "single falling feather" came
    back as a scatter of shapes that read as birds. Rebuilt in brass and
    amber on navy with exactly one feather.

Two are deliberately LEFT ALONE, because a regeneration is a fresh roll of
the dice and neither is actually broken:

  * ep2_once_twice - flagged for the pips on the domino being countable
    marks. Pips are what makes a domino a domino; strip them and it reads
    as a blank block, not a tile. The no-numerals rule is about text and
    figures, not spots, and the gate passed the image.
  * ep2_running_total - flagged as a static arrangement rather than an act
    of totalling. True, but it still reads as weight accumulating on a
    beam, and the line over it is only a two-second question.

  python scripts/vector/fix_ep2_polish.py && \
    python scripts/vector/gen_jojo_exhibits.py ep2_what_to_watch ep2_empty_docket
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CARDS = REPO / "remotion/public/characters/cast_ep1/exhibits/_cards.json"

STYLE = (
    "Drawn as a bold manga illustration in the hard-ink, angular cel-shaded, "
    "halftone-screentone style of JoJo's Bizarre Adventure by Hirohiko Araki "
    "- thick black contour outlines, sharp graphic drop shadows, heavy amber "
    "rim light. The colour is held strictly to deep navy, warm amber, brass "
    "gold and muted teal on a dark ground, with warm candle-amber as the only "
    "bright note. Every surface in the picture is smooth, blank and unmarked. "
    "The illustration fills the entire wide horizontal frame edge to edge as "
    "one continuous scene."
)

PROMPTS = {
    # The closing image. A tool AIMED at something, not lying beside clutter.
    "ep2_what_to_watch": (
        "A symbolic still life with no people anywhere in it: a tall brass "
        "refracting telescope stands on a slender wooden tripod on a bare "
        "stone balcony, seen from behind and slightly to one side at eye "
        "level, tilted up and out toward a wide open night sky. The balcony "
        "floor is completely bare and smooth, with nothing else resting on "
        "it. Beyond the low stone parapet the land falls away into a deep "
        "navy night, and along the far horizon a thin band of warm amber "
        "dawn light is just beginning to separate the sky from the ground. "
        "The telescope's brass barrel and its tripod catch that amber light "
        "in hard-edged highlights along their upper edges, and the great "
        "front lens glints once. Everything else sits in deep navy shadow. "
        "The mood is calm, patient and forward-looking rather than tense. "
    ) + STYLE,

    # Brass and amber, not pink; exactly one feather, not a flock.
    # Third roll. The second fixed the palette but left the door ambiguous
    # and dropped a scribbled fake signature onto the ground - small, but a
    # lettering violation all the same, and the cheapest possible fix.
    "ep2_empty_docket": (
        "A symbolic still life with no people anywhere in it: one large "
        "ornate birdcage of polished brass hangs on a chain slightly left of "
        "centre in a wide frame against a flat deep navy void, lit from "
        "within by a soft warm amber glow. Its little wire door has swung "
        "fully outward on its hinge and hangs wide open in the air well "
        "clear of the cage body, so the opening in the bars is unmistakable "
        "and a clear gap of empty dark space shows straight through it. The "
        "cage is completely empty: the perch is bare, the cage floor is bare "
        "and smooth, and nothing rests on either. Exactly one small pale "
        "feather drifts in the air just outside the open door, the only "
        "loose object in the picture. Beneath the cage the ground is a "
        "plain, unbroken, perfectly smooth expanse of dark stone, empty from "
        "edge to edge apart from one soft pool of amber light. The brass is "
        "warm gold and deep bronze throughout, the surrounding void stays "
        "deep navy fading to black, and the mood is quiet, hollow and still. "
    ) + STYLE,
}


def main() -> None:
    cards = json.loads(CARDS.read_text("utf-8"))
    n = 0
    for c in cards:
        p = PROMPTS.get(c["name"])
        if not p:
            continue
        c.setdefault("prompt_polish_prev", c["prompt"])
        c["prompt"] = p
        c["revision"] = "v3 - polish pass on the gate's borderline calls"
        n += 1
    CARDS.write_text(json.dumps(cards, indent=1), "utf-8")
    print("patched %d cards" % n)


if __name__ == "__main__":
    main()
