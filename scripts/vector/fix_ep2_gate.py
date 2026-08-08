"""Repair the four ep.2 exhibits the visual gate rejected.

The gate did the job it exists for. Two of these are editorial hazards that
a prompt review could not have caught, because the prompt text was innocent
and only the rendered pixels were not:

  * ep2_caught_one - the small "figure for scale" came back KNEELING in a
    spotlight in front of a wall studded with arrows. It reads as an
    execution. This episode is about trades with no charges filed; an image
    that reads as a killing is unusable at any quality. Fix: delete the
    human entirely and let the objects carry it.
  * ep2_inverted_bet - the pool under the barrel rendered as dark red and
    reads as a blood spill, on the one episode where that association is
    least acceptable. Fix: the spill becomes a black-and-teal oil sheen.
  * ep2_late_useless - the room glimpsed through the door came back warm
    and occupied, which inverts the point (nobody is left to use it).
  * ep2_tell_me_coincidence - only one row of dominoes is actually
    toppling, so the "impossible synchrony" the line needs is absent.

  python scripts/vector/fix_ep2_gate.py && \
    python scripts/vector/gen_jojo_exhibits.py <the four names>
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
    "rim light. Restrained palette held to deep navy, warm amber, burgundy "
    "and muted teal on a dark ground, evenly lit and never blown out to "
    "white. Every surface in the picture is smooth, blank and unmarked. The "
    "illustration fills the entire wide horizontal frame edge to edge as one "
    "continuous scene."
)

PROMPTS = {
    # No human at all. The gate read a kneeling silhouette as an execution.
    "ep2_caught_one": (
        "A symbolic still life with no people anywhere in it: a broad, weathered "
        "stone wall fills the frame, seen straight on at eye level. Dozens of "
        "plain wooden arrows lie broken and scattered in a heap along the base "
        "of the wall, spent and fallen, their shafts dull and unmarked. Exactly "
        "one arrow stands buried deep in the stone at the centre of the wall, "
        "still quivering, its burgundy fletching catching a single hard-edged "
        "shaft of warm amber light that falls from high above and pools around "
        "the point of impact. Fine cracks radiate through the stone outward from "
        "that one arrow. The rest of the wall recedes into deep navy shadow, and "
        "the far edges of the frame fade to near black. "
    ) + STYLE,

    # The spill was reading as blood. Make it unmistakably oil.
    "ep2_inverted_bet": (
        "A symbolic still life with no people anywhere in it: one monumental "
        "brass balance stands bolted to a smooth unmarked stone pedestal at the "
        "centre of a wide frame, shot from a low angle looking up. A long "
        "double-armed crossbar swivels on a single bare brass ball-pivot. The "
        "left arm plunges steeply downward, carrying a black iron oil drum that "
        "has tipped and spilled a glossy black slick across the pedestal, the "
        "slick catching muted teal and cold blue-green highlights along its "
        "rainbow-sheened surface exactly the way spilled crude oil does. The "
        "right arm sweeps steeply upward, lifting a tall polished spire into a "
        "warm amber glow at the top of the frame. Heavy rim lighting traces both "
        "arms against a flat deep navy void fading to black at the edges. "
    ) + STYLE,

    # The room beyond must read cold, bare and abandoned.
    "ep2_late_useless": (
        "A symbolic still life with no people anywhere in it: the camera faces "
        "straight on at chest height toward a tall dark weathered wooden door "
        "standing ajar against a flat deep navy void. One plain white envelope "
        "with a completely blank smooth surface hangs frozen in mid-air just "
        "below a brass mail slot, halfway through its fall to the floor. Through "
        "the open gap the room beyond is cold, bare and long abandoned: no lamp "
        "is lit and no furniture remains, only bare floorboards under a thin "
        "wash of pale blue-grey moonlight from an unseen window, a drift of dust "
        "across them, and one clean pale rectangle of unweathered wood marking "
        "where something large once stood and was carried away. Cobwebs hang in "
        "the upper corners of the empty doorway. Warm amber light exists only on "
        "the near face of the door itself, making the emptiness beyond colder by "
        "contrast. "
    ) + STYLE,

    # BOTH rows have to be mid-topple, in the same wave, at the same angle.
    "ep2_tell_me_coincidence": (
        "A symbolic still life with no people anywhere in it: a long dark "
        "polished wooden table runs the full width of a wide frame, seen from a "
        "low side-on angle at table height. Two entirely separate rows of "
        "smooth, unmarked ivory dominoes stand on the table, one row on the left "
        "half and one row on the right half, with a broad stretch of completely "
        "bare, empty tabletop between them. BOTH rows are caught in mid-collapse "
        "at the very same instant: in each row three tiles have already gone "
        "down flat, the next tile in each is frozen leaning at an identical "
        "steep angle, and the tiles beyond it in each still stand upright. The "
        "two toppling waves mirror each other exactly, tile for tile, angle for "
        "angle, with nothing at all crossing the empty gap between them. One "
        "hard-edged shaft of warm amber light falls straight down onto that bare "
        "gap, making the empty stretch of wood the brightest thing in frame, "
        "while both rows sit in deep navy shadow. "
    ) + STYLE,
}


def main() -> None:
    cards = json.loads(CARDS.read_text("utf-8"))
    n = 0
    for c in cards:
        p = PROMPTS.get(c["name"])
        if not p:
            continue
        c.setdefault("prompt_gate_rejected", c["prompt"])
        c["prompt"] = p
        c["revision"] = "v2 - repaired after the ep.2 visual gate"
        n += 1
    CARDS.write_text(json.dumps(cards, indent=1), "utf-8")
    print("patched %d cards" % n)
    print("next: python scripts/vector/gen_jojo_exhibits.py " + " ".join(PROMPTS))


if __name__ == "__main__":
    main()
