# The Setup That Failed — IBIT 40s reel

Two formats, same real trade, same fixture:

| file | format |
|---|---|
| `ibit_fail_cam.mp4` (+`_preview`) | **CAM — the current one.** Full-frame trading terminal (prod-reel green look, timer), character as an upper-body corner cam bottom-right. `TradeFailCam.tsx` |
| `ibit_setup_that_failed.mp4` (+`_preview`) | ROOM — v2. Illustrated room, chart perspective-mapped onto a monitor, camera cuts. `TradeFailReel.tsx` |

All masters 1080×1920 · 30fps · 1200 frames · 40.06s · CRF 18; previews CRF 27.

## The cam format (v3)

Owner's spec: single screen with the trading window open, timer like the prod
reels, character upper body bottom-right — smaller, but he is big. One sweat
drop, gliding slowly, looping — not the three-bead gag.

With no room and no camera, motion comes from three places: the chart (pen
heads on the drawing lines, the three-view y-axis, a terminal ALARM — red wash
+ pulsing stop line + STOP FILLED — when the stop fires), the character (the
full toon grammar plus a vertical channel: he pops up to open, sinks with
dread through the wait, shoots up on the break, slumps into the facepalm —
the bottom edge crops him, so height IS emotion), and one single frame punch +
impact kick on the break.

A 3-agent adversarial review (craft / mobile legibility / compliance) ran on
the first full render and caught five real defects, all fixed and re-verified
in pixels: unclipped candle wicks punching through the chrome once the axis
narrows; the live price tag truncating ENTRY/SUP/STOP labels (now right-aligned
inside the plot + labels dim while the tag passes); STOP FILLED stacking on the
STOP label at the climax (now below the line); the "Four bars" caption
appearing while the counter said 1 BAR; and the live tag reading red through
the countdown (now neutral slate for exactly the quiz window — the tick colour
is data, but a red pill held through the ask reads as a lean).

A character reads a textbook bullish setup on a real chart, takes it, is asked to
call it, and is wrong. Silent apart from SFX — scored with trending music at post.

## What is real

Everything on the screen. 250 real IBKR daily IBIT bars
(`data/prices/IBIT_1d_2026-07-27.json`) were scanned by
`scripts/btc_reel/find_failed_setup.py`, which **finds** a window already
satisfying the definition rather than composing one. The window it returned:

| | |
|---|---|
| Window | 2025-10-13 → 2026-02-11, 70 setup + 14 reveal bars |
| Support | 50.30, two pivot lows (bars 38, 60) |
| Resistance | 53.57, three pivot highs (bars 36, 40, 57) |
| Trendline | 46.68 → 49.32, 3 touches, **no closes through it** |
| Trigger | HAMMER AT SUPPORT, 2026-01-21 — sweeps to 49.40, closes back at 51.11 |
| Entry | 50.67 (close of 2026-01-22) |
| Stop | 49.15, under the hammer's low |
| Target | 53.71 = 2R, which lands on the 53.57 resistance |
| Best it got | **+0.68R** — it worked for four bars |
| Outcome | stopped 2026-01-29, then −28.8% by 2026-02-05 |

Verified against the raw bars: 0 OHLC violations, 0 closes through the trendline.

**IBIT, not BTC.** Spot Bitcoin is not on the brokerage feed and the egress
policy blocks every crypto API, so the instrument is a spot Bitcoin ETF and the
footer says so on every frame. It is never presented as BTC/USD.

## Why this window and not one of the other five

Six real failed setups exist in the series. The first version of the scanner
ranked them with `- sl_at * 0.15`, which quietly put **instant failure** at the
top — and a trade that breaks on the very next bar teaches nothing, it just
looks like a bad entry. The ranking now rewards a few bars where the viewer
agrees with the character before he turns out to be wrong. The chosen window
went +0.68R and chopped for four bars before it broke.

## The beats — 1200 frames

| Beat | Frames | Shot |
|---|---|---|
| 0 Hook | 0–90 | wide |
| 1 Chart build | 90–360 | **close** on the monitor (structure draws) |
| 2 Pattern | 360–510 | **close** on the hammer → hard cut wide on the take |
| 3 Entry | 510–660 | **close** while entry/stop/target draw → cut wide on the commit |
| 4 Quiz | 660–780 | wide, 4.0s, he is in shot the whole timer |
| 5 Wait | 780–960 | wide, with one **close** on the bars going nowhere |
| 6 Fail | 960–1080 | **close** on the break → hard cut wide on the shock |
| 7 Lesson | 1080–1200 | wide, the rule held to the last frame |

The trade frame lands at 516 — **before** the quiz, never after. A viewer asked
to call a trade without seeing what being wrong costs is guessing, and the loss
then reads as bad luck instead of as a bounded bet that lost.

## The animation layer

The first cut of this held each drawing ~60 frames and hard-cut to the next.
That is limited animation on paper and a slideshow on screen. What was missing
is not more drawings — it is everything that happens around one:

| | where |
|---|---|
| Anticipation, squash/stretch, smear, three-beat holds, boil | `remotion/src/motion/toon.ts` |
| Impact lines, shock ring, sweat, dust, flash, speed lines | `remotion/src/motion/ToonFX.tsx` |
| Measured per-pose head position | `scripts/meme_reel/head_anchors.py` |

Three things are worth stating because they are what separate this from an
effects preset:

1. **The smear is derived, not decorated.** Its strength comes from how much
   the silhouette and the drift actually change across that cut, so 30 of the
   32 cuts smear and the shock take (0.78) smears four times as hard as a
   weight shift (0.19). A constant smear is the giveaway that one was bolted
   on afterwards.
2. **The take is one event.** Drawing, smear, flash, impact burst, camera kick
   and sound all key off a single frame number (`SHOCK_AT`). Nothing can drift
   apart later.
3. **Character-anchored effects use a measured head.** The head runs from
   x=0.29 of the drawing box in `stagger` to x=0.78 in `leans_a`, and most of
   the body's height between `idle` and `crouch`. The first version anchored
   sweat to one standing position and it hung in empty wall the moment he bent.

Cut density went from 20 to 33 — roughly one per second, tightest through the
reaction (four drawings in 70 frames; a take that holds is not a take).

## Two things that only show up if you look

Both shipped in an intermediate cut here and were caught in stills, not in code:

1. **The character has to be CUT, not faded.** Any fade at all leaves him
   semi-present over a moving camera, so his pointing arm hangs across the chart
   as a ghost. Fading a character out is not the same as cutting away from him.
2. **Every camera move is one frame.** A six-frame ease means the camera flies
   through an empty room, because he is already cut. Ten transitions of that is
   two seconds of the reel spent looking at nobody.

Both are invisible in a typecheck and obvious in a contact sheet.

## Staging

Solved, not chosen — see the note in `scripts/btc_reel/build_fixture.py`. The
twelve drawings in the cut sheet are up to 883px wide and roughly centred on the
feet, so at the previously-approved 1020px / x=800 every pose clips the frame.
900px at x=760 keeps every *gesture* inside the frame; `shrug` is dropped
outright as the widest drawing in the set.

## Sound

Four countdown ticks (22–25s) and one blip per **reveal** candle (26s onward).
One impact on the take (33.8s) — a swept-down sine for the body, a
band-limited noise crack for the leading edge, a short mid ring so it reads
cartoon rather than as a gunshot. There is deliberately **no coin**: the coin
is the target-hit sound and this trade never reached its target. All verified
by RMS bucketing, because a missing `<Audio>` still produces a valid file.

## Rebuild

```bash
python scripts/btc_reel/find_failed_setup.py     # scan -> setup.json
python scripts/btc_reel/build_fixture.py         # stage -> trade_fail_reel.json
cd remotion && npx remotion render src/index.ts TradeFailReel out.mp4 --crf=18
```

Drop `--browser-executable=...` on a laptop; it only exists in the sandbox.

---
*Educational content only — not financial advice. Hindsight example.*
