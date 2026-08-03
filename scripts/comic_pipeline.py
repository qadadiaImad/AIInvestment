"""Comic panel pipeline — a reusable STRUCTURE for visually-narrating panels.

A panel is defined by explicit fields (who / what shot / what action / where /
which background props / what mood). `compose()` turns those into an optimized
prompt that FRONT-LOADS shot + action + environment (so the image narrates the
story, not just shows a character), and `render_panel()` runs it through the
local ComfyUI pipeline with the two-pass "scene → face-lock" method
(dynamic action + rich background in pass 1; IPAdapter locks the character's
identity in pass 2). This is the structure to reuse across all comics.

    from comic_pipeline import Panel, render_panels
    render_panels([Panel(char=GH, shot="FULL", action="...", setting="...", props=[...]), ...], "higgs/x/art")
"""
from __future__ import annotations

import sys
import pathlib
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy_gen  # noqa: E402

COMIC_LORA = "comic_eldritch.safetensors"

# Camera language — WIDE establishes the world; FULL shows dynamic full-body
# action; MEDIUM reads gesture + expression; CLOSEUP carries emotion.
SHOTS = {
    "WIDE": "wide establishing shot, the full environment fills the frame, small figures in a vast scene, deep perspective, epic scale",
    "FULL": "dynamic full-body action shot, the whole figure visible head to toe, exaggerated dynamic pose, motion lines, sense of movement",
    "MEDIUM": "medium shot, waist-up, clear readable gesture and facial expression",
    "CLOSEUP": "dramatic extreme close-up, intense emotional facial expression",
}

STYLE = ("comic book, bold black ink outlines, dynamic comic-book shading, dramatic cinematic composition, "
         "a rich, detailed, story-telling background full of environmental detail, depth and atmosphere")

NEG = comfy_gen.NEG_DEFAULT + ", empty background, plain background, blank backdrop, static boring pose, flat lighting"


@dataclass
class Panel:
    char: str | None = None          # focal character reference (IPAdapter) — None = scene / multi-char panel
    ip_weight: float = 0.8           # pass-2 identity strength (two-pass keeps the scene regardless)
    shot: str = "FULL"               # WIDE | FULL | MEDIUM | CLOSEUP
    action: str = ""                 # what is HAPPENING — strong verbs, dynamic; describe ALL characters present
    setting: str = ""                # place + season/time/weather
    props: list = field(default_factory=list)  # enriched background artifacts (story-relevant objects)
    mood: str = ""                   # lighting + emotion
    seed: int = 0
    pass2_denoise: float = 0.5       # lower keeps more of pass-1's scene/pose
    lora_weight: float = 0.85        # comic LoRA strength (lower for softer/cuter, less superhero)
    neg_extra: str = ""              # panel-specific negatives (e.g. anti-superhero for animal casts)
    style: str = STYLE               # override the style header if a panel needs a different look

    # For 2-character interaction panels, keep char=None and describe both animals
    # in `action` (IPAdapter can only lock one identity; generic animal designs
    # read fine from the prompt). Use `char` only when one figure dominates.


def compose(p: Panel) -> str:
    parts = [p.style, SHOTS.get(p.shot, SHOTS["FULL"]), p.action, p.setting]
    if p.props:
        parts.append("the background is filled with: " + ", ".join(p.props))
    if p.mood:
        parts.append(p.mood)
    return ", ".join(x for x in parts if x)


def render_panel(p: Panel, out: str):
    prompt = compose(p)
    negative = NEG + (", " + p.neg_extra if p.neg_extra else "")
    comfy_gen.generate(
        prompt, out, negative=negative, width=1024, height=1024, steps=28, seed=p.seed,
        lora=COMIC_LORA, lora_weight=p.lora_weight,
        ref=p.char, ip_weight=p.ip_weight,
        twopass=bool(p.char), pass2_denoise=p.pass2_denoise,
        quality=True,
    )


def render_panels(panels: dict[str, Panel], outdir: str):
    """panels: {name: Panel}. Renders each to <outdir>/<name>.png."""
    outp = pathlib.Path(outdir)
    outp.mkdir(parents=True, exist_ok=True)
    for name, p in panels.items():
        render_panel(p, str(outp / f"{name}.png"))
