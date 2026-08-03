"""Generate 'The Ant & the Grasshopper' panels via the comic_pipeline schema.
Cute ANIMAL cast (not superheroes): solo beats use IPAdapter two-pass on the
animal ref for consistency; the interaction beats (5,6) show BOTH characters
in frame (no IPAdapter — it can only lock one identity; both cute animals are
described in `action`). Writes higgs/fable/art/<key>.png.

    python higgs/_gen_fable_panels.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from comic_pipeline import Panel, render_panels  # noqa: E402

ART = pathlib.Path(__file__).resolve().parent / "fable" / "art"
GH = str(ART / "grasshopper_ref.png")
AN = str(ART / "ant_ref.png")

NEG_ANIMAL = "muscular, buff, superhero, bodybuilder, six-pack abs, human body, human man, spandex suit, tough guy, biceps"
CUTE = "cute soft storybook cartoon animal style"
GH_DESC = "a cute cartoon green grasshopper with a little straw hat, real grasshopper anatomy, wings and antennae"
AN_DESC = "a cute cartoon red ant, real ant anatomy, six legs, round segmented body and antennae"

PANELS = {
    # --- solo beats: IPAdapter two-pass for a consistent animal ---
    "p1_gh_summer": Panel(
        char=GH, ip_weight=0.55, lora_weight=0.5, neg_extra=NEG_ANIMAL, shot="FULL", seed=611,
        action=f"{GH_DESC} lounging back happily on a big curved leaf, one leg crossed, playing a tiny fiddle with eyes closed and a blissful grin, tapping a foot, musical notes drifting up",
        setting="a lush sun-drenched summer meadow at golden hour",
        props=["towering wildflowers", "buzzing bees", "a big warm sun", "a pile of ripe berries", "dandelion fluff drifting"],
        mood=f"warm carefree golden light, {CUTE}"),
    "p2_ant_haul": Panel(
        char=AN, ip_weight=0.55, lora_weight=0.5, neg_extra=NEG_ANIMAL, shot="FULL", seed=612,
        action=f"{AN_DESC} straining and puffing as he carries a big round grain seed on his back up a dirt trail toward an anthill, little legs working hard",
        setting="the same summer meadow, a worn trail climbing to an anthill entrance",
        props=["a long line of tiny worker ants carrying grain", "the mounded anthill entrance", "sacks of stored grain in the burrow"],
        mood=f"hard-working, hot sunny day, {CUTE}"),
    "p3_gh_dance": Panel(
        char=GH, ip_weight=0.55, lora_weight=0.5, neg_extra=NEG_ANIMAL, shot="FULL", seed=613,
        action=f"{GH_DESC} hopping and dancing happily in mid-air, twirling his fiddle overhead, head thrown back laughing, pointing playfully at a tiny working ant",
        setting="the sunny summer meadow",
        props=["swirling glowing musical notes", "the tiny toiling ant far in the background", "wildflowers and grass"],
        mood=f"carefree joyful, {CUTE}"),
    # --- pure scene ---
    "p4_winter": Panel(
        char=None, lora_weight=0.6, shot="WIDE", seed=614,
        action="a fierce howling winter blizzard tearing across a frozen meadow at night",
        setting="the meadow now buried under deep snow, the dead of winter, midnight",
        props=["bare skeletal frozen trees", "long jagged icicles", "one distant cozy cottage window glowing warm gold", "a little fiddle half-buried in a snowdrift", "swirling snow"],
        mood="bleak, freezing, cold blue moonlight, ominous"),
    # --- interaction beats: BOTH characters in frame ---
    "p5_gh_beg": Panel(
        char=None, lora_weight=0.5, neg_extra=NEG_ANIMAL, shot="FULL", seed=615,
        action=(f"{GH_DESC}, thin frostbitten and shivering, kneeling in the snow with his hands clasped together begging pitifully and looking up, "
                f"while {AN_DESC} stands sternly in a warm glowing doorway above him with arms crossed, coldly refusing"),
        setting="the ant's cozy cottage doorway during a raging blizzard at night",
        props=["warm golden light spilling from the doorway", "snow piling on the grasshopper", "frost on his little coat", "sacks of stored grain glimpsed inside the warm house", "icicles hanging above the door"],
        mood=f"desperate begging against cold refusal, warm door glow versus cold blue snow, {CUTE}"),
    "p6_ant_evil": Panel(
        char=None, lora_weight=0.5, neg_extra=NEG_ANIMAL, shot="FULL", seed=616,
        action=(f"{AN_DESC} standing in a warm doorway with a wicked evil grin, one leg flung out pointing into the raging blizzard, "
                f"while a tiny {GH_DESC} cowers miserably down in the snow below, casting a long menacing shadow"),
        setting="the ant's cottage doorway, blizzard howling outside, night",
        props=["a roaring orange fireplace glow behind the ant", "stacked sacks of stockpiled grain inside", "the little grasshopper cowering in the snow", "the ant's long sinister shadow"],
        mood=f"cruel villain refusal, cozy warm interior against the cold storm, {CUTE} but dark"),
}

if __name__ == "__main__":
    render_panels(PANELS, str(ART))
    print("DONE")
