"""Round-2 regen jobs for the gate failures, phrased per failure mode.

Round-1 gate findings (gate_round1.json): blinks come back as WINKS or
no-ops; rex_shock/_v1's scream prior reproduces itself for closed/half/oh
and adds gloss gradients to open interiors; sol_armswide's opens read
half-sized. Fixes: explicit both-eyes phrasing + anti-wink negatives,
anti-gloss negatives, and denoise 0.9 where the base mouth structure must
be overpowered.
"""
from __future__ import annotations

import json

from vector.visemes_ep1 import (VIS, SOL_LOCK, REX_LOCK, SUFFIX, NEG)

FLAT_NEG = ", gradient, glossy, 3d, realistic shading"

BLINK_PHRASES = [
    "sleeping face, both eyes completely closed, curved closed eyelids",
    "both eyes shut, closed eyelids, no pupils visible",
    "eyes closed tight, anime sleeping expression",
]
BLINK_NEG = NEG + ", wink, one eye open, open eye, pupil" + FLAT_NEG

TARGETS: list[dict] = []


def add(pose, viseme, phrases, negative, denoise):
    lock = SOL_LOCK if pose.startswith("sol") else REX_LOCK
    for i, phrase in enumerate(phrases):
        TARGETS.append({
            "pose": pose, "viseme": viseme,
            "mask": "eyes" if viseme == "blink" else "mouth",
            "phrase": phrase,
            "prompt": f"{lock}, {phrase}, {SUFFIX}",
            "negative": negative,
            "seed": 91000 + len(TARGETS),
            "denoise": denoise,
            "out": f"{pose}__{viseme}__r2c{i}",
        })


for pose in ["sol_point", "sol_point_v1", "sol_smug_v1", "sol_smug_v2",
             "sol_wink", "sol_wink_v1", "sol_armswide", "rex_shock_v1"]:
    add(pose, "blink", BLINK_PHRASES, BLINK_NEG, 0.85)

for pose in ["rex_shock", "rex_shock_v1"]:
    add(pose, "closed",
        ["mouth completely closed, lips pressed into a thin line, "
         "worried frown",
         "closed mouth, thin frown line, no teeth",
         "small closed frowning mouth, calm"],
        NEG + ", open mouth, teeth, tongue, screaming, shouting" + FLAT_NEG,
        0.9)
    add(pose, "half",
        ["small slightly open mouth, talking",
         "small parted lips, mid-sentence",
         "small open mouth, speaking quietly"],
        NEG + ", wide open mouth, screaming, huge mouth" + FLAT_NEG,
        0.9)

add("rex_shock_v1", "open",
    ["wide open mouth, flat solid dark mouth interior, shouting",
     "wide open mouth, yelling, flat color",
     "huge open mouth, flat dark interior"],
    NEG + FLAT_NEG, 0.8)
add("rex_shock_v1", "oh",
    ["small round o shaped mouth, whistling",
     "round o mouth, surprised, flat color interior",
     "small circular open mouth"],
    NEG + ", wide rectangular mouth, screaming, teeth" + FLAT_NEG, 0.9)
add("sol_armswide", "open",
    ["huge wide open mouth, jaw dropped, laughing loudly",
     "very wide open mouth, shouting, big dark opening",
     "jaw dropped wide open mouth"],
    NEG + ", small mouth, slightly parted lips, closed mouth" + FLAT_NEG,
    0.85)

if __name__ == "__main__":
    p = VIS / "regen_round2_jobs.json"
    p.write_text(json.dumps(TARGETS, indent=1), "utf-8")
    print(f"{len(TARGETS)} round-2 jobs -> {p}")
