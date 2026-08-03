"""Generate 'The Ant & the Grasshopper' panels via the comic_pipeline schema.

RECIPE (validated 2026-08-03 after debugging a consistency regression): use the
TRAINED character LoRA at ~0.9 with the comic-style LoRA at only ~0.2. A higher
style-LoRA weight HIJACKS the character's face (different eyes/mouth per scene =
inconsistency); 0.2 keeps the comic ink+color while letting the trained identity
dominate. Every panel reuses ONE canonical descriptor + a fixed seed, keeps the
character UPRIGHT/bipedal (the trained pose), and bans clothing cues (a winter
"coat" turned the bug into a person-in-a-hoodie). See memory:
lora-pose-distribution-consistency. Writes higgs/fable/art/<key>.png.

    python higgs/_gen_fable_panels.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from comic_pipeline import Panel, render_panels  # noqa: E402

ART = pathlib.Path(__file__).resolve().parent / "fable" / "art"

# --- the proven recipe: trained char LoRA 0.9 + light comic style 0.2 ---
GH_LORAS = [("fablegh.safetensors", 0.9), ("comic_eldritch.safetensors", 0.2)]
AN_LORAS = [("fableant.safetensors", 0.9), ("comic_eldritch.safetensors", 0.2)]

# ONE canonical descriptor per character, reused verbatim in every panel so the
# identity is pinned (eyes/wings/stance) regardless of the beat.
GH = "fablegh, a cute cartoon green grasshopper character, standing upright on two legs, big amber eyes, translucent dragonfly wings, friendly rounded face"
AN = "fableant, a cute cartoon red ant character, standing upright on two legs, big expressive teal eyes, two antennae, three round body segments, friendly face"

# Ban the two failure modes: base-model realistic-insect prior, and clothing.
NEG = ("realistic insect, photorealistic bug, side-view insect, many legs, six legs sprawled, "
       "quadruped, crawling on all legs, prone lying flat, human, person, clothing, hoodie, coat, "
       "jacket, spandex suit, muscular, buff, superhero, bodybuilder")
VIB = "vibrant saturated comic colors"

PANELS = {
    "p1_gh_summer": Panel(
        loras=GH_LORAS, neg_extra=NEG, shot="FULL", seed=611,
        action=f"{GH} leaning back relaxed, playing a tiny fiddle with a blissful grin, one foot tapping, glowing musical notes drifting up",
        setting="a lush sun-drenched summer meadow at golden hour",
        props=["towering wildflowers", "buzzing bees", "a big warm sun", "a pile of ripe berries", "dandelion fluff drifting"],
        mood=f"warm carefree golden light, {VIB}"),
    "p2_ant_haul": Panel(
        loras=AN_LORAS, neg_extra=NEG, shot="FULL", seed=612,
        action=f"{AN} hauling a big round golden grain over his shoulder with both arms, straining and determined, marching upright up a dirt trail toward a mounded anthill",
        setting="the same summer meadow, a worn trail climbing to an anthill entrance",
        props=["a long line of tiny worker ants carrying grain", "the mounded anthill entrance", "sacks of stored grain"],
        mood=f"hard-working, hot sunny day, {VIB}"),
    "p3_gh_dance": Panel(
        loras=GH_LORAS, neg_extra=NEG, shot="FULL", seed=613,
        action=f"{GH} dancing and hopping joyfully, arms raised, twirling his fiddle overhead, head thrown back laughing",
        setting="the sunny summer meadow",
        props=["swirling glowing musical notes", "a tiny toiling ant far in the background", "wildflowers and grass"],
        mood=f"carefree joyful, {VIB}"),
    # pure scene — no character, so a touch more comic style is fine
    "p4_winter": Panel(
        loras=[("comic_eldritch.safetensors", 0.4)], shot="WIDE", seed=614,
        action="a fierce howling winter blizzard tearing across a frozen meadow at night",
        setting="the meadow now buried under deep snow, the dead of winter, midnight",
        props=["bare skeletal frozen trees", "long jagged icicles", "one distant cozy cottage window glowing warm gold", "a little fiddle half-buried in a snowdrift", "swirling snow"],
        mood="bleak, freezing, cold blue moonlight, ominous"),
    # interaction beats — each character solo (split-panel composites them in the builder)
    "p5a_gh_beg": Panel(
        loras=GH_LORAS, neg_extra=NEG, shot="FULL", seed=615,
        action=f"{GH} standing hunched and shivering, thin and frostbitten, both hands clasped together begging pitifully, looking up desperate",
        setting="deep snow at night just outside a cottage, a blizzard blowing",
        props=["snow falling all around", "a warm glowing cottage window behind", "icicles", "frost on the ground"],
        mood=f"desperate begging, cold blue winter night against a warm window glow, {VIB}"),
    "p5b_ant_door": Panel(
        loras=AN_LORAS, neg_extra=NEG, shot="FULL", seed=617,
        action=f"{AN} standing sternly in a warm glowing doorway, arms crossed, chin up, coldly refusing and looking down",
        setting="the ant's cozy cottage doorway during a raging blizzard at night",
        props=["warm golden light spilling from the doorway", "sacks of stored grain glimpsed inside the warm house", "icicles hanging above the door", "snow piling on the threshold"],
        mood=f"cold stern refusal, warm interior versus cold blue snow, {VIB}"),
    "p6_ant_evil": Panel(
        loras=AN_LORAS, neg_extra=NEG, shot="FULL", seed=616,
        action=f"{AN} with a wicked evil grin, one arm flung out pointing into a raging blizzard, standing in a warm doorway",
        setting="the ant's cottage doorway, blizzard howling outside, night",
        props=["a roaring orange fireplace glow behind the ant", "stacked sacks of stockpiled grain inside", "the ant's long sinister shadow"],
        mood=f"cruel villain refusal, cozy warm interior against the cold storm, {VIB} but dark"),
}

if __name__ == "__main__":
    render_panels(PANELS, str(ART))
    print("DONE")
