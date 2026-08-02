# Science Reel — design (2026-08-02, owner-approved "build it")

"They call it gambling" reel on the habits-reel engine: part 1 (~28%) the
accusations people throw at finance/trading, part 2 (~72%) the actual
sciences behind it, each science on an adequate backdrop. Owner picks an
Instagram phonk sound → silent render, beat-ready 1.7s grid (3 beats @
~106 BPM), 18 units = 918 frames = 30.6s.

**Aesthetic:** cinematic dark-phonk — night scenes, deep blacks, LED accent
lighting (cool blue/purple/red), 35mm grain, shallow DOF. Deliberately
breaks the habits reel's no-neon rule at the owner's request for this
piece. No readable text/numbers/logos in AI frames (rule 10.1), faces
never visible.

**Type color story:** accusations cold white with RED underline glow;
pivot onward flips to house GREEN glow. Two 2-frame white flashes: at the
pivot and at the closer. Hard cuts + 4-frame black dips everywhere else.

## Shot list (units of 1.7s)

| # | u | kind | text (color) | backdrop |
|---|---|------|------|----------|
| 0 | 2 | vid | "TRADING ISN'T A REAL SCIENCE" (red) | night crowd crossing, headlights |
| 1 | 1 | img | "IT'S JUST GAMBLING" (red) | casino table in near-dark, chips |
| 2 | 1 | img | "IT'S PURE LUCK" (red) | spinning coin macro, black void |
| 3 | 1 | img | "IT'S UNETHICAL" (red) | dark glass tower, smoke drift |
| 4 | 1 | img | HERE'S THE ACTUAL SCIENCE (green, +flash) | LED-lit dark study desk |
| 5 | 1 | img | PROBABILITY | Galton-board light trails, bell curve |
| 6 | 1 | img | STATISTICS | luminous distribution traces |
| 7 | 1 | img | STOCHASTIC CALCULUS | chalkboard, unreadable equations |
| 8 | 2 | vid | RANDOM WALKS | drifting particle light trails |
| 9 | 1 | img | COMPUTER SCIENCE | server-rack LED aisle |
| 10 | 1 | img | ALGORITHMS | blurred code glow, RGB keyboard |
| 11 | 1 | img | GAME THEORY | chess mid-game, low key |
| 12 | 1 | img | MACHINE LEARNING | GPU rig / neural light web |
| 13 | 1 | img | BEHAVIORAL SCIENCE | blurred crowd, one still figure |
| 14 | 1 | vid | IT'S NOT LUCK. IT'S MATH. (+flash) | LED night trading desk |
| 15 | 1 | vid | STUDY THE SCIENCE. | night street as in hook — loop |

Stills 12, videos 4 (6s gens for the 2-unit shots, 3s for 1-unit).
Accusations are quoted discourse; sciences are facts; no income claims
(rule 10.6). Engine: `ScienceReel.tsx` with cutStarts/totalFrames props
for later track re-timing, `scripts/science_reel/gen_assets.py` serial
grok batch with stamped resumable manifest.
