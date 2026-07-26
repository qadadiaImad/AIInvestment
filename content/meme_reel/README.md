# Meme reel — rubber-hose character reacting to a real chart

**Output:** `content/meme_reel/intc_failed_breakout.mp4` — 1080×1920, 30fps, 510 frames (17.05s), silent.

Built to the brief in [`references/meme-reel-pipeline.md`](../../references/meme-reel-pipeline.md).

---

## What it is

A rubber-hose cartoon character stands beside a desk and reacts to a chart playing
on the monitor in front of him. The chart is **real INTC daily bars rendered by our
own engine** and perspective-mapped into the monitor — not a drawn chart, not a
generated one.

The story is the INTC failed breakout of June–July 2026:

| beat | frames | what happens |
|---|---|---|
| idle | 0–70 | he stands at the desk, the tape prints history |
| notices | 70–130 | double-take; the 141.45 level draws in |
| leans in | 130–230 | he leans toward the screen as the fourth test sets up |
| **cutaway** | 214–296 | camera pushes to the monitor; the story bar prints over 46 frames |
| the pattern fails | 230–300 | it trades to 142.35, closes 139.63 — **below** the level |
| facepalm | 300–390 | the glove drags down over his eyes as the aftermath prints |
| shrug | 390–510 | palms up to camera: the level held |

## The rail

The reference reel this format comes from hooks on *"I turned −19,168 into
+123,716."* That is a returns claim and we did not ship it — framing it as a meme
does not make it less of one.

**The character reacts to a pattern, not a payout.** There is no P&L, no return, no
position size and no money counter anywhere in the composition or in any component
it mounts. The only on-screen number is **price**, and the chart says so in its own
footer (`PRICE — NOT P&L`). The disclaimer renders unconditionally on every frame.

## Architecture

```
Higgsfield (once)                  Remotion (every render)
──────────────────                 ────────────────────────────────────
room plate .png  ──────────────►   background; the camera moves over it
                                   ScreenInsert ← matrix3d homography
                                     └── TapeChart (real IBKR bars)
                                   RubberHoseRig  (pure SVG pivot rig)
                                   camera, captions, Grain + Vignette
```

### The character: generated art on a cutout rig

The brief (§3, §4) specifies the character be **generated as separate transparent
PNG limb layers** and rigged from those rasters. A first pass overrode that with a
hand-authored SVG rig — and the SVG rig was not good enough. Its limbs are
`<path stroke strokeWidth={14}>`, a mathematically constant width, and the target
look needs a **tapered brush outline** with visible volume (thick at the hip,
hairline at the ankle). No amount of effort fixes that; it is the wrong primitive.

So the brief was right. The shipping character is `toonRig.tsx`: generated art,
cut into per-limb PNGs, driven by the rig.

**What was kept from the vector attempt:** all of the animation. `toonRig` imports
`computeRubberHosePose` and the `armIK` contact solver unchanged — the beat timing,
anticipation/follow-through, and the facepalm/desk-plant IK are the same reviewed,
tested code. Only what gets *drawn* inside each joint's `rotate()` group changed.
`rubberHoseRig.tsx` is retained because it still owns the pose engine, and
`RigCheck` can render either rig for an art-only A/B.

**Proportions come from the art**, not from a skeleton guess: bone lengths are
derived from each part PNG's own pixel height, so the figure is shaped like the
drawing.

**Expressions** are four interchangeable heads (`neutral`, `curious`, `shock`,
`weary`) generated as ONE sheet so they share framing, size and neck position
exactly — a head from a separate generation jumps on the cut. `expressionAt(frame)`
swaps them per beat. The reference reel gets most of its read from the FACE; a
shocked take with a neutral face is just a man waving.

**Two bugs worth remembering**, both found by looking at renders:
* the far arm/leg were dimmed with `opacity`, which makes opaque art
  *see-through* where it crosses the body. Depth needs a tint
  (`filter: brightness()`), not transparency.
* `boneLen()` was signed, and the torso is the one part whose bone runs *upward*
  from its joint. The first assembly put the head and both arms below the hip.

Generated art still does the static room, which is what generative models are
good at.

### Regenerating the character

```bash
# 1. generate a parts sheet (8 parts, 2 rows of 4, separated, on white)
#    and a 4-head expression sheet in the same style
# 2. cut them
python scripts/meme_reel/extract_limbs.py higgs/meme_reel/parts_sheet_A.png        remotion/public/meme_reel/char
python scripts/meme_reel/extract_limbs.py higgs/meme_reel/heads4.png        remotion/public/meme_reel/char --parts 4 --neck-pivot        --names head_neutral,head_curious,head_shock,head_weary
```

`extract_limbs.py` removes the background by **flood-filling from the image
border**, not by thresholding brightness — the body fill is ~#D9D9D9, only 15%
off white, so a threshold would eat the body and punch holes through the eye
whites. Parts are then found by connected component rather than on a hardcoded
grid, because the generator does not place them on the grid it was asked for.

## Files

| what | where |
|---|---|
| composition | `remotion/src/compositions/MemeReel.tsx` |
| character rig | `remotion/src/characters/rubberHoseRig.tsx` |
| arm IK (contact poses) | `remotion/src/characters/armIK.ts` |
| chart on the screen | `remotion/src/components/TapeChart.tsx` |
| perspective insert | `remotion/src/components/ScreenInsert.tsx` + `screenMath.ts` |
| rig contact sheet | `remotion/src/compositions/RigCheck.tsx` (a check, not a deliverable) |
| fixture | `remotion/src/fixtures/meme_reel/intc_failed_breakout.json` |
| room plate | `remotion/public/meme_reel/room_plate.png` (source in `higgs/meme_reel/`) |

## Data provenance

The 24 candles are **not authored**. They are copied programmatically from
`remotion/src/fixtures/ta_quiz/real_intc_failed_breakout.json`, which was verified
this session against `data/prices/INTC_1d_2026-07-25.json`:

```
match offset: 26   date range: 2026-06-03 -> 2026-07-08   bars: 24
source: Interactive Brokers via brokerage MCP get_price_history
        (period=THREE_MONTHS, step=ONE_DAY, outside_rth=false)
retrieved_at: 2026-07-25T22:30:00Z
```

The story bar is `2026-06-30`: `o 131.99 · h 142.35 · l 131.52 · c 139.63`. Its high
is above the 141.45 level and its close is below it — the failed breakout is in the
data, not in the edit.

## Checks

Two components have failure modes that typecheck and render without error, so both
are asserted numerically under plain node:

```bash
cd remotion
node scripts/check_screen_math.mjs   # the matrix3d homography
node scripts/check_arm_ik.mjs        # the arm IK contact poses
```

`check_screen_math.mjs` round-trips all four corners through the **packed** 16-value
array (catching a column-major transposition, which is silent) and agrees with an
independently derived vector to 5.6e-17. It also refuses degenerate and bowtie
quads. `check_arm_ik.mjs` round-trips every IK solution back through forward
kinematics — "the glove lands on his eyes" is a numeric claim and is checked as one.

The screen quad is **measured from the accepted plate**, never guessed:

```bash
python scripts/meme_reel/measure_screen_quad.py higgs/meme_reel/room_plate_C.png
# -> quad TL(85,722) TR(502,722) BR(502,974) BL(85,974), fill ratio 0.996
```

## Rendering

```bash
cd remotion
npx remotion still RigCheck ../higgs/meme_reel/rig_sheet.png --frame=0   # pose check
npx remotion render MemeReel ../content/meme_reel/intc_failed_breakout.mp4
```

One pass — the three-chunk `--frames=` split in `content/trading_styles/README.md`
was a sandbox shell timeout, not a Remotion limitation. Do **not** pass
`--browser-executable`; that path only exists in the remote container.

To re-render with a different ticker, swap the fixture — it is a data change, not a
new generation.

---

*Educational content only — not financial advice. Hindsight example.*
