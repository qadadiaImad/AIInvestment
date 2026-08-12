# TradingQuiz — time-axis zoom, real underlying, ticker chrome

**Date:** 2026-08-12
**Owner decision session:** this document records decisions made by the project owner
on 2026-08-12; where a decision overrides a standing house rule it says so explicitly.

## Problem

The shipped `TradingQuiz` reel (Instagram post #43, "MAYA LAB — HEAD AND SHOULDERS")
presents the whole bar window from frame 0. `slot = (CHART.x1 - CHART.x0) / candles.length`
(`remotion/src/compositions/TradingQuiz.tsx:258`) is fixed for the entire reel, so only the
*price* axis can move, and it only moves once, at the reveal (line 226).

That means the viewer never experiences the thing that makes a level persuasive: seeing
price arrive at a line, then discovering the line was drawn from history that was off-screen.

`fluidCamera` does not solve this. It is a CSS `transform: scale()` about a focus point
(lines 276–302). It magnifies strokes and text; it cannot reveal additional bars.

## Goals

1. Open zoomed **in** on recent bars, printing live, like a terminal being watched.
2. Zoom **out** through time to expose the formation and then the multi-year level history
   that justifies the line.
3. Zoom back in to the decision zone for the countdown and answer.
4. Replace the `MAYA LAB` chrome label with the real ticker + logo.
5. Total runtime 30s.

## Non-goals

- Playing back years of tape bar by bar. Owner ruling: *"if a previous point 3y ago … we
  zoom out to show that point but never display the curve progressing real time from 3y
  ago, it will be boring to watch."*
- Changing the countdown / answer / reveal / risk-reward acts. Those ship as-is.

## Owner decisions that override standing rules

| Rule | Standing text | 2026-08-12 decision |
|---|---|---|
| CLAUDE.md §10.6, `ta-chart-quiz` rails | No literal BUY/SELL badge on a real ticker; use `answerLabel` | **BUY/SELL badge with the ticker visible.** Rationale given: the window is historical, not a live call. |
| CLAUDE.md §10.6, `ta-chart-quiz` rails | "Keep the disclaimer footer on every frame" | **Footer deleted.** In the shipped post it is already half-occluded by Instagram's comment row, so it was costing screen and delivering nothing. |

Both documents are updated in the same commit as the code, so the rules and the
implementation do not contradict each other.

## The data (verified 2026-08-12 against `data/prices/SPY_1d_5y_2026-07-30.json`)

Underlying: **SPY daily**, real Interactive Brokers bars, 1254 bars, 2021-08-02 → 2026-07-30.

Formation: **Cup and Handle**, already detected by
`scripts/patterns_post/find_real_patterns.py` and stored in
`remotion/src/fixtures/patterns_post/gallery.json`.

| | |
|---|---|
| Window | 2023-10-09 → 2023-12-01, series idx 550–588 (39 bars) |
| Level | RIM **437.34** |
| Breakout | idx 574 = 2023-11-10, close 440.61 |
| Trade frame | entry 440.61 · stop 432.53 · target 456.76 · 1:2 · target reached 12 sessions later · +3.7% |
| Honest sample | 1 win / 6 detections of this formation in the series |

Prior distinct visits to 437.34 (±0.4%, visits separated by >5 bars), all verified:

| Date | idx | Bars before breakout | Inside 6M window? |
|---|---|---|---|
| 2021-08-02 | 0 | 574 | no |
| 2021-08-18 | 12 | 562 | no |
| 2021-09-20 | 34 | 540 | no |
| 2022-01-21 | 120 | 454 | no |
| 2022-02-11 | 135 | 439 | no |
| 2022-03-16 | 157 | 417 | no |
| 2022-04-12 | 176 | 398 | no |
| 2023-06-13 | 469 | 105 | **yes** |
| 2023-08-17 | 514 | 60 | **yes** |
| 2023-09-20 | 537 | 37 | **yes** |

Ten touches total: three are watched live inside the playback window, seven are revealed
as static history. The level is inside the price frame at every zoom level (deep viewport
spans 348.11–479.98), so the line never leaves the screen during the pull-back.

## Design

### 1. Viewport model

Replace the fixed slot with an animated bar-index window `[v0, v1]`, recomputed per frame
(the component body already re-evaluates every frame, so this is a derivation change, not
a refactor):

```
slot   = (CHART.x1 - CHART.x0) / (v1 - v0)
cx(i)  = CHART.x0 + (i - v0 + 0.5) * slot
```

Bars outside `[v0 - 1, v1 + 1]` are not rendered.

**Silhouette morph.** At the deep stop the window is 575 bars, i.e. **1.2 px/bar**. Candles
are unreadable there. Below ~3.5 px/bar they cross-fade into a close-line silhouette — the
same substitution `remotion/src/components/PatternCard.tsx` already makes for its mini
cells. This is required for legibility, not decoration.

**Anti-leak rule preserved.** CLAUDE.md §10.3: the y-frame must not telegraph the answer.
Price extents are fitted to the *visible* window, but padded symmetrically about the setup
midpoint until `REVEAL_START`, exactly as the current code does.

### 2. Playback vs reveal

The distinction that keeps the reel watchable:

- **Playback window** — bars print one at a time, tape-style. Hard capped at **126 bars
  (6 months)**. Enforced in the scanner, not trusted to the fixture.
- **Reveal window** — bars outside the playback window are already settled when they come
  into frame. They never print. The camera does the work.

### 3. Timeline — 900 frames @ 30fps = 30.0s

| Frames | Act | Viewport | Tape |
|---|---|---|---|
| 0–40 | boot, hook | tight | — |
| 40–190 | **Live tape** | 24 bars into the rim | ~6.3 f/bar, real time |
| 190–265 | **Zoom out, still ≤6M** | → 126 bars | ~100 bars back-fill fast (the speed-up) |
| 265–340 | **Deep reveal** | → 575 bars | nothing prints; settled silhouette slides in, RIM extends left |
| 340–405 | **Justify** | hold wide | 7 older touches strobe on with real dates |
| 405–450 | **Zoom back** | → decision zone | |
| 450–600 | Countdown | decision zone | 5s, existing tick/tock |
| 600–628 | Answer | | |
| 628–712 | Reveal | eases to full range | existing |
| 720–812 | Risk/reward | | existing |
| 812–900 | Rule card | | existing |

15s of setup, 15s of payoff.

### 4. Chrome

New optional props: `ticker`, `timeframe`, `dateRange`. The chrome renders
`[mark] SPY · DAILY · AUG 2021 → DEC 2023` in place of `MAYA LAB — {subject}`.

The mark resolves from `remotion/public/logos/<TICKER>.svg` via `staticFile`, falling back
to a typographic mono tile when no SVG exists. SPY has no SVG and gets the tile; INTC, AMD,
SMCI, QBTS, DUOL and INTU already have marks and get them for free.

### 5. Scanner

`scripts/ta_quiz/find_anchored_level.py`, written test-first in the idiom of
`scripts/patterns_post/find_real_patterns.py`.

Input: a series file and a formation window. Output: playback window bounds, deep viewport
bounds, and the touch list with real dates.

Refusal conditions — reports UNMATCHED rather than adjusting anything:

- fewer than 3 distinct prior visits to the level
- less than 6 months of history behind the oldest visit
- a requested playback window longer than 126 bars
- any bar in any emitted window failing the CLAUDE.md §10.1 integrity check
  (close outside the session range by more than 15c)

### 6. Backwards compatibility

`trading_quiz_engulfing_2026-07-25`, `strategy_quiz_breakout_2026-08-02`,
`strategy_quiz_ihs_2026-08-02` and `quiz_with_host_2026-07-25` are pinned at 682 frames.
The two-act timeline activates **only** when a fixture carries the `zoom` prop. Without it
the existing 682-frame timeline runs unchanged. `footer` becomes optional; existing
fixtures that set it keep rendering it.

### 7. Sound

Existing tick/tock, candle up/down and coin are unchanged. Added, synthesised in
`scripts/audio/make_tick.py` (Remotion's bundled ffmpeg is a minimal build with no
highpass/lowpass, so these cannot be filtered at mux time):

- a rising whoosh on each of the two zoom-outs
- a soft click per level touch as it lights during the justify act

Per-bar tones stay confined to the reveal. The back-fill and the deep reveal are silent
except for the whoosh — 100+ bars cannot each take a hit.

## Risks

| Risk | Mitigation |
|---|---|
| The silhouette morph reads as a rendering fault rather than a zoom | Frame-check both crossover points specifically (≈f265 and ≈f405) before shipping |
| Deep reveal feels static / dead | Level extends left and touches strobe *during* it, so something is always resolving |
| 900 frames at CRF 18 exceeds the 30MB chat cap | Render a CRF-27 preview alongside the master, per CLAUDE.md §10.9 |
| Existing fixtures silently break | `zoom` prop gates the whole new path; verify one legacy fixture still renders |

## Verification before completion

Per CLAUDE.md §10.7 — assertions do not count:

1. Extract frames at the act boundaries (40, 190, 265, 340, 405, 450, 600, 700, 850) and look at them.
2. Bucket the audio RMS to confirm the countdown ticks land inside the countdown window.
3. Confirm the level line is on screen at every zoom stop.
4. Re-render one legacy 682-frame fixture and confirm it is unchanged.
