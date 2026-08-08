"""Round-two exhibit prompts, written against what round one MEASURED.

Round one routed people to Illustrious-XL and objects to Z-Image. All eight
Illustrious cards came back unusable. Rerouting them to Z-Image and
rewriting them as prose fixed the mush but produced a new, sharper failure:
a visual gate on the actual pixels returned 5 fail / 2 borderline / 1 pass,
and FOUR of the five failures were the same defect - the figure had drifted
into a recognisable Jotaro Kujo (pompadour, popped gakuran collar, peaked
cap, star earring).

That is the finding this file is built on. "JoJo's Bizarre Adventure" is
load-bearing for the style and cannot be dropped - remove it and the style
collapses into colour noise, tested twice. But an UNNAMED "generic adult
man" leaves an identity vacuum, and the style tag fills it with the
franchise's most famous character. The fix is not a longer negative list.
The fix is to give every human figure a specific identity of its own:

  * a named real politician, drawn as an editorial-cartoon caricature; or
  * an ordinary person pinned down by concrete, un-JoJo specifics (short
    combed hair, a flat shirt collar); or
  * no face at all - a back-turned silhouette, with an OBJECT as the
    subject. Z-Image draws symbolic still life extremely well.

Four more rules, each of them paid for:

1. NAME FIRST, DESCRIBE BARELY. Probed at fixed seed: "Nancy Pelosi" plus
   "distinctive dark bob, angular face" returned a generic glamorous woman
   who is not her; "Nancy Pelosi, former Speaker of the House" with no
   physical description returned a clean likeness. A description that
   contradicts the real face overrides the name. Biden, Obama and Clinton
   all resolve name-only too. Only add a feature if it is actually true.

2. NEGATION DOES NOT WORK. zimage_t2i samples at cfg=1, so there is no
   classifier-free guidance and the negative prompt is inert - but worse,
   writing "no hat, no cap, no fedora" INSIDE the positive prose just feeds
   the model the concept. capitol_ticker said "no hat, cap, fedora or
   headband" and came back wearing a peaked cap. State the positive
   instead: "bare-headed, short hair swept back".

3. NEVER USE A DOMAIN TERM WITH A LITERAL HOMONYM. watching_chart asked for
   "an abstract candlestick chart rendered as glowing bars and wicks" and
   got a man standing among lit wax candles - no chart at all. Two candle
   words beat the finance sense. Describe the GEOMETRY: narrow vertical
   bars, each crossed by a thin line running above and below it.

4. WATCH FOR ICONOGRAPHY THAT DRAGS NUMERALS IN. leaderboard_suits said
   "no numbers" and still printed 1 / 2 / 3, because "three-tier winner's
   podium" summons the Olympic podium whole. Say "three plain rectangular
   pedestal blocks of different heights, front faces smooth and unmarked".

Casting note: the series' compliance rail is caricature + parody/public-
record footer + no on-screen name + no accusation. The owner asked for real
politicians rather than the older generic-archetype rule; the footer rail
stays either way, and the ranking exhibit is staged as "people track this",
never as a claim about who performed best.

  python scripts/vector/exhibit_prompts_v2.py          # patch the cards
  python scripts/vector/gen_jojo_exhibits.py <names>   # then generate
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CARDS = REPO / "remotion/public/characters/cast_ep1/exhibits/_cards.json"

# Style tail shared by every card. Names the franchise (load-bearing for the
# look) but immediately re-anchors to editorial cartooning so the style does
# not drag a character in with it. Surfaces are described as blank rather
# than "no text", because stating the positive is what actually holds.
STYLE = (
    "Drawn as a bold manga caricature in the hard-ink, angular cel-shaded, "
    "halftone-screentone style of JoJo's Bizarre Adventure by Hirohiko Araki "
    "- thick black contour outlines, sharp graphic drop shadows, heavy amber "
    "rim light - but posed and exaggerated like a newspaper editorial "
    "cartoon. Restrained palette held to deep navy, warm amber, burgundy and "
    "muted teal on a dark ground, evenly lit and never blown out to white. "
    "Every surface in the picture - paper, plaques, panels, screens - is "
    "smooth, blank and unmarked. The illustration fills the entire wide "
    "horizontal frame edge to edge, one continuous scene."
)

PROMPTS = {
    # OPENER. Object-forward on purpose: the only human is a back-turned
    # silhouette, so there is no face for the style tag to fill in.
    "capitol_ticker": (
        "A towering neoclassical government building crowned by a great "
        "domed rotunda stands at the centre of a wide night scene, its walls "
        "and dome built out of interlocking polished brass clockwork gears "
        "that turn slowly in place of stonework. A long ribbon of paper tape "
        "unspools from an opening at the base of the dome and coils forward "
        "through the foreground in a lazy S-curve, its blank surface printed "
        "only with plain solid rectangles of varying height and a few small "
        "upward-pointing arrows. One man in a dark suit stands small at the "
        "lower left, seen entirely from behind as a flat silhouette, head "
        "tilted up at the machine, giving it scale. Warm amber light glows "
        "out from deep inside the gearwork against a deep navy night sky. "
    ) + STYLE,

    # The owner's brief, literally: politics and corporate ambition joined
    # in one gesture. Trump resolves cleanly name-only (probed).
    "deal_handshake": (
        "A caricature of Donald Trump, the American president, in a dark "
        "navy suit and long red necktie, stands on the left of a wide frame "
        "and grips the hand of a corporate executive on the right in a firm, "
        "straining handshake. The two clasped hands are the exact centre of "
        "the picture and the largest thing in it, knuckles tight, held at "
        "chest height between the two men. The executive is a silver-haired "
        "man in a charcoal double-breasted suit and burgundy tie, carrying a "
        "slim leather briefcase in his free hand. Both men are shown from "
        "the waist up at a slight low angle, leaning fractionally toward one "
        "another, jaws set. Behind them a dark hall recedes into deep navy "
        "shadow with a faint amber glow along the horizon. "
    ) + STYLE,

    # "People track these disclosures like a leaderboard." Staged as being
    # WATCHED, never as a claim about whose returns are best.
    "leaderboard_suits": (
        "Three plain rectangular pedestal blocks of three different heights "
        "stand in a row on a dark floor, the tallest block in the centre and "
        "a shorter block to either side, their front faces completely "
        "smooth, blank and unmarked. A caricature of Nancy Pelosi, the "
        "former Speaker of the United States House of Representatives, "
        "stands on the tallest centre block in a burgundy skirt suit, chin "
        "lifted, one hand raised in a small confident wave. Two anonymous "
        "men in dark suits stand on the two lower blocks, drawn as flat "
        "featureless silhouettes with their shoulders slumped and heads "
        "bowed. A plain glowing amber rectangle and a simple teal laurel "
        "wreath float on the wall behind them, both entirely blank. A wide "
        "eye-level view holds all three blocks and all three figures. "
    ) + STYLE,

    # Not a politician - the retail investor copying filings. Pinned down
    # with un-JoJo specifics: short combed hair, an ordinary flat collar.
    "copy_homework": (
        "A young office worker in his twenties, with short neatly combed "
        "dark hair and an ordinary flat shirt collar, leans over a wooden "
        "desk at night under the warm pool of a brass desk lamp. He wears a "
        "plain pale blue dress shirt with the sleeves rolled to the elbow "
        "and a loosened burgundy tie hanging straight down. He is "
        "bare-headed and clean-cut. His right hand grips a pen and writes "
        "onto a fresh sheet, while his left hand holds open a thick stack of "
        "aged, yellowed paper files beside it, his eyes flicking sideways to "
        "the stack as he copies from it. Every sheet on the desk is blank "
        "apart from faint grey squiggles. The wall behind him is deep navy "
        "and bare. Shown from a slight low angle, waist up. "
    ) + STYLE,

    # Object-forward, to kill the giant-radiating-fists Stand composition
    # the gate caught. The lever is the subject; the man gives it scale.
    "options_leverage": (
        "An enormous industrial floor lever dominates the centre of a wide "
        "frame: a long steel bar ending in a heavy round handle, mounted in "
        "a slotted steel base bolted to a dark metal floor, hauled all the "
        "way down to its lowest notch. One man in a dark navy suit, drawn "
        "small against the size of the machine, grips the handle with both "
        "hands and leans his entire body weight backward into it, feet "
        "braced and heels dug in, seen from a low angle. His arms stay "
        "ordinary human proportions. A narrow controlled fan of warm amber "
        "sparks sprays upward from the slot where the bar meets the base, "
        "rising only a short distance before fading. The hall behind stays "
        "deep navy and unlit, and the picture never blows out to white. "
    ) + STYLE,

    # The word "candlestick" produced literal wax candles. Geometry only.
    "watching_chart": (
        "A man in a dark navy suit stands small at the lower right of a wide "
        "frame, his back three-quarters turned to the viewer, one hand in a "
        "pocket, looking up and to his left at an enormous glowing wall "
        "display that fills the left two-thirds of the picture. The display "
        "shows one long row of narrow upright rectangular bars of many "
        "different heights, standing shoulder to shoulder along a common "
        "baseline, each single bar crossed by one thin straight vertical "
        "line that extends a short way above its top edge and a short way "
        "below its bottom edge. The row of bars steps unevenly upward from "
        "left to right across the wall. The bars glow in muted warm amber "
        "and dusty teal against a dark flat panel, with no grid lines and no "
        "markings of any kind. The room around him is deep navy shadow. "
    ) + STYLE,
}


def main() -> None:
    cards = json.loads(CARDS.read_text("utf-8"))
    n = 0
    for c in cards:
        p = PROMPTS.get(c["name"])
        if not p:
            continue
        c.setdefault("prompt_v1_zimage", c["prompt"])
        c["prompt"] = p
        c["route"] = "zimage"
        c["revision"] = "v2 - identity-anchored after the Jotaro-drift gate"
        n += 1
    CARDS.write_text(json.dumps(cards, indent=1), "utf-8")
    print(f"patched {n} cards -> {CARDS}")
    print("next: python scripts/vector/gen_jojo_exhibits.py "
          + " ".join(PROMPTS))


if __name__ == "__main__":
    main()
