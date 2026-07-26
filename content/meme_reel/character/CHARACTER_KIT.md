# Character kit — rigging spec

Everything needed to build the puppet and animate the reel. Pair this with
[`../ANIMATION_BRIEF.md`](../ANIMATION_BRIEF.md), which has the frame-accurate
beat sheet, and [`../ANIMATION_GUIDE.png`](../ANIMATION_GUIDE.png), which is the
stage he performs on.

**He is an original character.** The recording that inspired the *style* is not
in this repo and its character design is not to be copied.

---

## The sheets

| File | What it is | Use |
|---|---|---|
| `../CHARACTER_SHEET.png` | Turnaround — front, ¾, side | Design reference. Proportions and colour truth. |
| `PARTS.png` | **The puppet source.** Separated body parts | Cut these into layers and rig them. |
| `HANDS.png` | 6 hand poses, labelled | **Swap set** — cutout hands are swapped, never deformed. |
| `EXPRESSIONS.png` | 6 heads, labelled | **Swap set** — one head per emotional beat. |
| `KEY_POSES.png` | The 6 story beats as finished poses | The targets. Animate *to* these. |

> **Note on facing:** the parts and heads are drawn facing **RIGHT**. In the reel
> he faces **LEFT** toward the monitor. Rig him facing right, then mirror the
> whole puppet horizontally. Nothing in the design is asymmetric (no text, no
> parting, no logo), so mirroring is lossless.

> **Note on the labels:** `HANDS.png` and `EXPRESSIONS.png` came back with text
> labels under each piece. That is useful for you and harmless for rigging —
> just crop the text off when you cut the pieces.

## Rig hierarchy

Parent → child. Every child rotates about the joint it is named for.

```
ROOT (ground contact, between the feet)
└── PELVIS
    ├── TORSO ......................... pivot: hip, at the belt line
    │   ├── NECK → HEAD .............. pivot: neck stub, bottom-centre of the head
    │   ├── SHOULDER_far → UPPER_ARM   pivot: shoulder, inside the sleeve
    │   │   └── ELBOW → FOREARM ...... pivot: elbow
    │   │       └── WRIST → HAND ..... pivot: wrist stub, top-centre
    │   └── SHOULDER_near → UPPER_ARM  (same chain, drawn IN FRONT of the torso)
    │       └── ELBOW → FOREARM
    │           └── WRIST → HAND
    ├── HIP_far → THIGH .............. pivot: hip
    │   └── KNEE → SHIN .............. pivot: knee
    │       └── ANKLE → SHOE ......... pivot: ankle, at the top of the shoe opening
    └── HIP_near → THIGH             (same chain, drawn IN FRONT)
```

**Draw order, back to front:** far leg → far arm → torso → head → near leg → near arm.

## Pivot placement — the rule that makes or breaks it

**Put every pivot slightly INSIDE the ink of the child, not on its edge.** Roughly
5% down from the top of a limb piece. The child's rounded cap then overlaps the
parent's end at every rotation and there is no gap to see. A pivot placed on the
edge produces a visible seam the moment the joint bends — the single most common
cutout-rig failure.

| part | pivot |
|---|---|
| head | neck stub, bottom-centre — the head hangs **up** from it |
| torso | belt line, bottom-centre — the torso also runs **up** from its pivot |
| upper arm | top-centre, inside the sleeve |
| forearm | top-centre |
| hand | wrist stub, top-centre |
| thigh | top-centre, inside the hip mass |
| shin | top-centre |
| shoe | top of the ankle opening — **not** centre of the shoe |

## Joint limits — please enforce these

The code rig had none, and the result was elbows bending backwards through the
joint. Whatever tool you rig in, set limits. **Hinges must sit entirely on one
side of zero** so they can never invert:

| joint | range |
|---|---|
| shoulder | −175° … 40° |
| **elbow** | **0° … 135° — one side of zero only** |
| wrist | −32° … 32° (small; overdriven wrists read as broken faster than anything) |
| hip | −55° … 70° |
| **knee** | **−95° … 0° — one side of zero only** |
| spine lean | −25° … 45° |
| head | −38° … 38° |

## Swap sets

Wire these as switchable states, not as deformations.

**Hands** — `relaxed` (rest) · `flat palm down` (hand on desk, the lean-in beat) ·
`pointing` · `splayed shock` (the recoil) · `palm up open` (the shrug) · `loose fist`

**Heads** — `neutral` (idle) · `curious` (notices, leans in) · `shocked` (the
pattern fails) · `weary` (facepalm, shrug) · `wince` · `blink`

Blink is a straight swap off the neutral head — run it every 3–4 seconds and
**suppress it during the double-take and the recoil**. Nobody blinks mid-flinch.

If your tool supports a separate pupil layer, split the eyes out of the head so
gaze can move without swapping the whole face. That one addition buys more life
than any other single thing.

## Beat → swap map

| frames | head | near hand |
|---|---|---|
| 0–76 | neutral | relaxed |
| 76–232 | curious | relaxed → **flat palm down** from ~206 (planted on the desk) |
| 232–302 | **shocked** | **splayed shock** |
| 302–392 | weary | relaxed (it is covering his eyes) |
| 392–510 | weary | **palm up open** |

## Deliverable

One transparent video — see `../ANIMATION_BRIEF.md` §1 for the full spec:

```
1080 × 1920 · 30 fps · exactly 510 frames · VP9 + alpha (yuva420p)
→ remotion/public/meme_reel/character.webm
```

Then set `characterSrc: "meme_reel/character.webm"` in
`remotion/src/fixtures/meme_reel/intc_failed_breakout.json` and re-render.

---

*Educational content only — not financial advice.*
