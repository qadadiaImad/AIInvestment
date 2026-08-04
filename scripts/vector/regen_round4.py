"""Round 4: close the last two coverage gaps in the ep1 cut.

sol_laugh carries a 2s beat with a frozen mouth (its base drawing is a
wide open laugh, so it needs closed/half/oh to pulse), and sol_point,
rex_shock_v1 and sol_wink hold screen time with no blink.

Rounds 1-2 taught the failure modes: an open-eye prior survives denoise
0.85 and returns the base eyes untouched (or a wink), and a wide-open
mouth prior reproduces itself unless pushed to 0.9 with explicit
anti-negatives. Both are answered here with denoise 0.95 and negatives
naming the thing to avoid.
"""
from __future__ import annotations

import json

from vector.visemes_ep1 import VIS, SOL_LOCK, REX_LOCK, SUFFIX, NEG

FLAT = ", gradient, glossy, 3d, realistic shading"
BLINK_NEG = (NEG + ", wink, one eye open, open eye, pupil, eyeball, "
             "iris, sclera" + FLAT)
BLINK_PHRASES = [
    "sleeping face, both eyes closed, smooth curved closed eyelids",
    "eyes shut tight, closed eyelid lines, no pupils",
    "peaceful sleeping expression, both eyes closed",
]

JOBS: list[dict] = []


def add(pose, viseme, phrases, negative, denoise):
    lock = SOL_LOCK if pose.startswith("sol") else REX_LOCK
    for i, ph in enumerate(phrases):
        JOBS.append({
            "pose": pose, "viseme": viseme,
            "mask": "eyes" if viseme == "blink" else "mouth",
            "phrase": ph,
            "prompt": f"{lock}, {ph}, {SUFFIX}",
            "negative": negative,
            "seed": 97000 + len(JOBS),
            "denoise": denoise,
            "out": f"{pose}__{viseme}__r4c{i}",
        })


# sol_laugh: base drawing IS the open viseme, so the set it lacks is the
# closed end of the range. The laugh prior is as stubborn as rex_shock's
# scream was -- same denoise 0.9 + explicit anti-laugh negatives.
add("sol_laugh", "closed",
    ["mouth closed, lips together, warm smile, cheeks raised",
     "closed mouth smile, no teeth showing",
     "mouth shut, gentle grin"],
    NEG + ", open mouth, teeth, tongue, laughing, shouting" + FLAT, 0.9)
add("sol_laugh", "half",
    ["small slightly open mouth, chuckling",
     "half open mouth, mid laugh, small opening"],
    NEG + ", wide open mouth, huge mouth, screaming" + FLAT, 0.9)
add("sol_laugh", "oh",
    ["round o shaped open mouth, small circular mouth",
     "small round o mouth, surprised"],
    NEG + ", wide rectangular mouth, teeth" + FLAT, 0.9)

for pose in ["sol_laugh", "sol_point", "rex_shock_v1", "sol_wink"]:
    add(pose, "blink", BLINK_PHRASES, BLINK_NEG, 0.95)

if __name__ == "__main__":
    p = VIS / "regen_round4_jobs.json"
    p.write_text(json.dumps(JOBS, indent=1), "utf-8")
    print(f"{len(JOBS)} round-4 jobs -> {p}")
    for j in JOBS:
        print(f"  {j['out']:34s} denoise {j['denoise']}")
