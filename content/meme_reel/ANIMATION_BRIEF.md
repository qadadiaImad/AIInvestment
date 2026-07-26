# Meme reel — character animation brief

**You animate the character. Remotion does everything else.**

This is the frame-accurate spec for the character performance in
`content/meme_reel/intc_failed_breakout.mp4`. Animate against it in Cartoon
Animator / Character Animator / Moho / After Effects, export one transparent
video, drop it in, done.

---

## 1. Deliverable

| | |
|---|---|
| **File** | `remotion/public/meme_reel/character.webm` |
| **Canvas** | **1080 × 1920** |
| **Frame rate** | **30 fps** — exactly |
| **Length** | **510 frames = 17.00 s** |
| **Codec** | VP9 (or VP8) with **alpha**, pixel format `yuva420p` |
| **Alternative** | Apple **ProRes 4444** `.mov`, pixel format `yuva444p10le` |

Then set `characterSrc: "meme_reel/character.webm"` in
`remotion/src/fixtures/meme_reel/intc_failed_breakout.json` and re-render. If
that field is absent the built-in rig is used instead, so the reel always
renders either way.

> **ffmpeg check before you send it** — a file with no alpha still plays fine
> and silently composites as a black box:
> ```bash
> ffprobe -v error -show_entries stream=pix_fmt -of csv=p=0 character.webm
> # must print yuva420p (or yuva444p10le for ProRes)
> ```

## 2. The three rules that will break it if ignored

1. **NO CAMERA MOVE.** Animate on a static 1080×1920 canvas. The reel pushes in
   to the monitor and back out again, and Remotion applies that camera to the
   room plate and to your video **together** — a push baked into your export
   would double up and slide off the room.
2. **CHARACTER ONLY.** No background, no room, no shadow plate, no chart. Pure
   alpha. A contact shadow under his feet is welcome; a background is not.
3. **WORLD SPACE.** He must sit in the same coordinate space as the room. Use
   `ANIMATION_GUIDE.png` as a locked background reference layer while you work,
   then hide it before export.

## 3. The stage — `ANIMATION_GUIDE.png`

Import it at 1080×1920, lock it, animate over it.

| mark | y | meaning |
|---|---|---|
| desk top | **1000** | the surface he can lean a hand on |
| wall/floor junction | **1506** | the back of the floor |
| **feet land** | **1665** | his contact point when standing |
| type-safe top | **1560** | captions and the disclaimer sit over this strip |
| monitor quad | x 85–502, y 722–974 | **never cover this** — the live chart plays here |

**He stands to the RIGHT of the desk, facing LEFT toward the monitor.** Stage box
is roughly x 430–1060.

> ⚠️ **Known conflict:** his feet at y=1665 sit *inside* the caption strip
> (y>1560). Captions render **over** him. Keep the storytelling in his head,
> torso and hands — everything below the knee will be behind type for much of
> the reel. If that bothers you, raise `charFeetY` in the fixture and re-run the
> guide script.

## 4. The beat sheet

510 frames @ 30fps. The chart column is what the viewer sees on the monitor at
that moment — his reaction has to be motivated by it.

| frames | time | CHARACTER | chart on the monitor | caption on screen | camera |
|---|---|---|---|---|---|
| **0–70** | 0.0–2.3 | **Idle.** Standing relaxed by the desk, weight settled, breathing. Not yet looking at the screen. | history printing, bar every 7f | *(none until f40)* → "INTC, daily. One level: 141.45." | wide, static |
| **70–130** | 2.3–4.3 | **Notices.** Double-take — head flicks AWAY first (~6f), then snaps to the monitor. Eyes widen. Torso follows the head. | the 141.45 level line draws in at **f96** | — | slow creep in |
| **130–230** | 4.3–7.7 | **Leans in.** Rocks back ~5f first, then leans toward the screen, plants a hand on the desk (desk top y=1000). Peering. | price approaching the level | "Twice price stalled there. No close above it." (f130–202) | pushing in |
| **206–252** | 6.9–8.4 | ⚠️ **THE STORY BAR PRINTS.** It takes 46 frames. He should be watching it, still, tense. | one bar trading up through 141.45 — its high **clears the level at f240** | "Third test." (f214–236) → "Higher high…" (f238) | **monitor close-up** |
| *206–290* | | ⚠️ **He is FADED OUT f216–276** — this is a cutaway to the screen. Animate through it anyway; the fade is applied in Remotion. | | | |
| **230–300** | 7.7–10.0 | **The pattern fails.** Load ~3f forward, then a hard full-body recoil away from the screen. Hands fly up. Eyes maximum. Mouth open. This is the biggest pose in the reel. | the bar settles at **139.63 — below the level** | "…lower close." (f264–300) | pulls back out |
| **300–390** | 10.0–13.0 | **Facepalm / slump.** Hand lifts up-and-back ~4f first, then drags down over the eyes. Spine collapses, shoulders drop. Keep sinking ~20f after the hand lands. | the aftermath prints — five red bars, price falls away | "The close-based rule: no close above the level, no breakout." (f312–388) | wide-ish |
| **390–510** | 13.0–17.0 | **Shrug at camera.** Dip lower ~4f first, then half-straighten, turn to camera, shoulders up, palms out. Then a **second smaller beat around f460–500** — a re-shrug or head tilt — so the ending is not a freeze. | settled, level visible and unbroken | "It never closed above. The level held." (f398–508) | back to wide |

### Timing craft the reel already assumes

- **Every action gets anticipation** — a counter-move first. He rocks back before
  leaning in, loads forward before recoiling, drops lower before shrugging.
- **Every action overshoots then settles.** Nothing arrives and stops dead.
- **Hands lag the shoulders.** They keep travelling after the arm stops.
- **Nothing ever fully freezes** — breathing and a small hand waggle run under
  every held pose, including the final 2 seconds.

## 5. Character design

Full kit in **[`character/CHARACTER_KIT.md`](character/CHARACTER_KIT.md)** — rig
hierarchy, pivot placement, joint limits, swap sets, and a beat→swap map.

| sheet | what |
|---|---|
| `CHARACTER_SHEET.png` | turnaround — the design truth |
| `character/PARTS.png` | the puppet source, separated body parts |
| `character/HANDS.png` | 6 hand poses (swap set) |
| `character/EXPRESSIONS.png` | 6 heads (swap set) |
| `character/KEY_POSES.png` | the 6 story beats as finished poses — animate to these |

Chunky and bouncy, ~4.5 heads tall, thick sturdy limbs with volume, big rounded
hands and shoes. Teal short-sleeved shirt, grey trousers, dark shoes. Bold
tapered black outline, flat fills, muted palette to sit in a warm beige room.

**He is an original character.** The reference recording that inspired the *style*
is not in this repo and is not to be copied as a design.

## 6. What Remotion still owns

You don't need to touch any of this — it is data-driven and re-renders on demand:

- the room plate and the camera move
- the **live chart** (real IBKR bars, perspective-mapped into the monitor)
- captions, the disclaimer footer, grain and vignette
- the character fade during the monitor cutaway

Swapping the reel to a different ticker is a fixture change, not a re-animation —
**as long as the beat frames above stay the same.** If a new ticker needs a
different rhythm, the beat sheet changes and the character has to be re-animated
to it. Keep the beats fixed if you want the character performance to be reusable.

---

*Educational content only — not financial advice.*
