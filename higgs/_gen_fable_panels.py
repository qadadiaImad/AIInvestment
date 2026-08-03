"""Generate 'The Ant & the Grasshopper' panels via the comic_pipeline schema —
dynamic action + enriched, story-telling backgrounds, two-pass (scene → face-
lock) so the characters stay consistent AND the images narrate the story.
Writes into higgs/fable/art/<key>.png (the keys _build_fable_comic.py expects).

    python higgs/_gen_fable_panels.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from comic_pipeline import Panel, render_panels  # noqa: E402

ART = pathlib.Path(__file__).resolve().parent / "fable" / "art"
GH = str(ART / "grasshopper_ref.png")
AN = str(ART / "ant_ref.png")

PANELS = {
    "p1_gh_summer": Panel(
        char=GH, ip_weight=0.8, shot="FULL", seed=611,
        action="a green grasshopper musician lounging back blissfully on a big curved leaf, one leg lazily crossed, sawing away on a fiddle with eyes closed and a wide grin, musical notes drifting from the strings",
        setting="a lush sun-drenched summer meadow at golden hour",
        props=["towering wildflowers", "buzzing bees", "a big warm glowing sun", "a pile of ripe berries", "dandelion fluff drifting on the breeze"],
        mood="warm, carefree, golden summer light"),
    "p2_ant_haul": Panel(
        char=AN, ip_weight=0.8, shot="FULL", seed=612,
        action="a red ant bent double, straining and sweating hard as he pushes an ENORMOUS grain seed twice his size up a steep dirt trail toward an anthill, muscles bulging with effort",
        setting="the same summer meadow, a well-worn trail climbing to an anthill entrance",
        props=["a long line of tiny worker ants carrying grain", "the mounded anthill entrance", "flying sweat droplets", "sacks of stored grain glimpsed in the burrow"],
        mood="hard-working, effortful, hot midday sun"),
    "p3_gh_dance": Panel(
        char=GH, ip_weight=0.75, shot="FULL", seed=613,
        action="a green grasshopper leaping high and dancing mid-air, twirling his fiddle overhead, head thrown back laughing, one arm pointing mockingly downward",
        setting="the sunny summer meadow",
        props=["swirling glowing musical notes", "kicked-up golden pollen", "the tiny toiling ant far in the background still hauling grain"],
        mood="carefree, mocking, joyful"),
    "p4_winter": Panel(
        char=None, shot="WIDE", seed=614,
        action="a fierce howling winter blizzard tearing across a frozen meadow at night, snow whipping sideways",
        setting="the meadow now buried under deep snow, the dead of winter, midnight",
        props=["bare skeletal frozen trees", "long jagged icicles", "one distant cottage window glowing warm gold", "a half-buried abandoned fiddle sticking out of a snowdrift", "swirling snow and wind"],
        mood="bleak, freezing, cold blue moonlight, ominous and unforgiving"),
    "p5_gh_beg": Panel(
        char=GH, ip_weight=0.8, shot="MEDIUM", seed=615, pass2_denoise=0.45,
        action="a gaunt, frostbitten green grasshopper collapsed and violently shivering on a snowy doorstep, one thin trembling arm weakly reaching up to knock on a huge wooden door, snow caked on his shoulders",
        setting="the ant's cottage doorstep during a raging blizzard at night",
        props=["warm golden light spilling through the door crack", "snow piling on his shoulders", "frost crusting his tattered coat", "his cracked fiddle clutched to his chest", "icicles hanging above the door"],
        mood="desperate, pitiful, freezing cold blue with a sliver of warm door glow"),
    "p6_ant_evil": Panel(
        char=AN, ip_weight=0.8, shot="FULL", seed=616, pass2_denoise=0.5,
        action="a red ant villain filling a doorway, looming and backlit, one arm flung out pointing into the raging blizzard, a wicked evil grin on his face, casting a long menacing shadow over a tiny cowering grasshopper down in the snow",
        setting="the ant's warm cottage doorway, blizzard howling outside, night",
        props=["a roaring orange fireplace glow behind him", "stacked sacks of stockpiled grain inside", "the tiny grasshopper cowering small in the snow below", "the ant's long sinister shadow stretching out"],
        mood="dramatic low-angle villain reveal, warm cozy interior against the cold storm, sinister and cruel"),
}

if __name__ == "__main__":
    render_panels(PANELS, str(ART))
    print("DONE")
