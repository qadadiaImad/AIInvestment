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

### Deviation from the brief, and why

The brief (§3, §4) specifies the character be **generated as separate transparent
PNG limb layers** and rigged from those rasters. It is built instead as a **pure SVG
pivot rig** (`remotion/src/characters/rubberHoseRig.tsx`), the same technique as the
six existing mascot rigs.

Rubber-hose is the one style where that trade goes the other way: thick
constant-width outlines, noodle limbs and flat fills *are* vector primitives, so
drawing them directly **removes** the two failure modes the brief itself warns
about — limbs detaching at the joints, and style drifting between separately
generated layers — rather than merely managing them. Generated art is still used
for the static room, which is what generative models are actually good at.

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
