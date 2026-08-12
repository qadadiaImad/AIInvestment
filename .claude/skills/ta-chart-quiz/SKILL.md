---
name: ta-chart-quiz
description: Build an animated candlestick "guess the next move" quiz reel from the numbered TA pattern library. Use when asked to create a carousel/reel/video for a TA pattern by number or name — e.g. "create a carousel of TA pattern number 5 with trading chart animation", "make the bearish engulfing quiz", "render TA pattern 42". Also use to list or search the pattern library.
---

# TA Chart Quiz — pattern library → animated reel

A numbered library of standard technical-analysis patterns, each carrying its
own validated OHLC data, wired to the `TradingQuiz` Remotion composition. Pattern
number in, rendered vertical reel out.

## The invocation

> "create a carousel of pattern TA number 5 with trading chart animation skills × remotion"

means: take library entry **id 5**, build its fixture, render it. Three commands.

## Run

```bash
# what's in the library
python scripts/ta_quiz/make_fixture.py --list
python scripts/ta_quiz/make_fixture.py --list --family two-candle

# id -> fixture (validates first; refuses to emit a broken pattern)
python scripts/ta_quiz/make_fixture.py 5

# then render with the command it prints
cd remotion && npx remotion render src/index.ts TradingQuiz \
  ../content/ta_quiz_<slug>.mp4 --props=../<fixture> \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec h264 --crf 17
```

Always **extract frames and look at them** before calling it done — the engine
has bitten twice on layout (labels clipping off-frame, annotations landing on
top of candles). Frames around the countdown, the answer, and the lesson card:

```bash
FF=video/node_modules/@remotion/compositor-linux-x64-gnu/ffmpeg
for t in 2 8 12 14 17; do $FF -v error -ss $t -i out.mp4 -frames:v 1 /tmp/f_$t.png -y; done
```

## The library

`references/ta-pattern-library.json` — each entry:

| Field | Meaning |
|---|---|
| `id` | stable number; this is what the invocation refers to |
| `slug` / `name` | `bearish-engulfing` / "Bearish Engulfing" |
| `family` | single-candle, two-candle, three-candle, reversal-chart, continuation-chart, gap-window, structure-level, volume-indicator |
| `complexity` | 1 (single obvious candle) → 5 (needs measurement/ratios) |
| `occurrence` | very-common / common / uncommon / rare — how often it actually appears, not how famous it is |
| `bias` / `type` | bullish/bearish/neutral · reversal/continuation/indecision |
| `answer` | BUY or SELL — drives arrow colours, glow, reveal badge |
| `candles`, `revealFrom` | the OHLC sequence; everything from `revealFrom` on is the reveal |
| `levelPrice`, `levelLabel` | the support/resistance the pattern fires at |
| `ruleText` | the teachable rule shown on the closing card |
| `renderable` | `candles-only` or `needs-overlay` |

**`renderable` matters.** The engine draws candles plus one horizontal level —
or two: optional `level2Price`/`level2Label` add a second line (built for the
previous-day-high/low strategy), and when present the y-frame goes symmetric
about the setup midpoint and static so the extra room can't leak the answer.
Anything else tagged `needs-overlay` (trendlines, channels, volume bars, moving
averages, indicator panes) will not read correctly as-is — `make_fixture.py`
warns, and the honest options are to pick a different pattern or extend the
composition first.

**Camera.** Optional `fluidCamera: true` swaps the flat push-in for a
focus-tracking move: glide into the decision zone for the countdown, release
wide when the answer lands. The HUD (hook, countdown ring, badge, rule card)
stays unscaled, and the ring relocates onto the chart's empty lower band. The
focus constants in `TradingQuiz.tsx` are collision-checked against this layout
— re-verify frames if you move them.

## Correctness is the whole point

The format only works if the chart genuinely shows the pattern. A reel with a
mislabelled setup teaches something false, which is worse than no reel.

`scripts/ta_quiz/validate.py` re-derives the checks in plain Python rather than
trusting the generating model — OHLC integrity (`h ≥ max(o,c)`, `l ≤ min(o,c)`),
the level actually being touched, the reveal moving the direction the answer
claims, plus per-family geometry (engulfing body containment, hammer wick
ratios, harami containment, doji body fraction, three-soldiers progression).

`make_fixture.py` runs it and **refuses to emit** a failing pattern unless
`--force`. Don't reach for `--force` to make something render — fix the data.

```bash
python scripts/ta_quiz/validate.py                # report
python scripts/ta_quiz/validate.py --write-clean  # emit the passing subset
```

## Sound

Three sound layers, all synthesised by `scripts/audio/make_tick.py`:

| Sound | When |
|---|---|
| `tick` / `tock` | one per countdown second, alternating |
| `candle_up` / `candle_down` | one per **reveal** candle, pitched by direction |
| `coin` | when a reveal bar reaches the target |

Reveal candles only — the setup prints 60+ bars in under four seconds, and a hit
per bar there is seventeen a second, which is noise rather than information.
`REVEAL_SPAN` is what keeps the reveal slow enough to score.

The countdown **ticks** — five escapement
sounds, one per second, alternating `tick.wav`/`tock.wav` from
`remotion/public/audio/`. They are placed off the same `COUNT_START`/`COUNT_PER`
constants the digits use, so the sound cannot drift from the number on screen.

The assets are synthesised by `scripts/audio/make_tick.py` rather than shipped as
a download — Remotion's bundled ffmpeg is a minimal build with no highpass or
lowpass filter, and a tick without filtering is a beep or a hiss. Regenerate with
`python scripts/audio/make_tick.py` if they go missing.

Verify placement after rendering — the sound is worth checking numerically
because a missing `<Audio>` still produces a valid file:

```bash
ffmpeg -i out.mp4 -vn -ac 1 -ar 8000 /tmp/a.wav -y   # then bucket the RMS
```

Five loud buckets one second apart inside the countdown window, silence
elsewhere.

## Real data instead of the library

`scripts/ta_quiz/find_real_pattern.py` scans actual IBKR bars in `data/prices/`
for a genuine occurrence of a pattern and emits a fixture from it. Prefer this
over the synthetic library where a detector exists — the library candles read as
what they are: too few bars, too clean a trend, not enough of the noise a real
tape carries.

```bash
python scripts/ta_quiz/find_real_pattern.py --list
python scripts/ta_quiz/find_real_pattern.py breakout-retest

# previous-day high/low strategy: failed break above yesterday's high, from a
# cached intraday 1-minute session (resampled 5-min) + the daily file's levels
python scripts/ta_quiz/find_real_pdhl.py
```

It reports "no real occurrence found" rather than nudging data to fit. The
composition scales frames-per-candle, form time, body width and wick weight off
the bar count, so a 24-bar library fixture and a 74-bar real window both work.

## The trade frame (optional)

Set `entry`, `stop`, `target` and `rrLabel` together and the reel adds a
risk/reward act after the reveal: risk band, reward band, three labelled lines,
and — if a reveal bar actually reaches the target — coins pouring out of that
bar with a chime.

**All four fields or none.** A target with no stop shows the upside and hides
what being wrong cost. And `tpBar` is derived in the composition from the price
data, never stated in the fixture, so the payoff cannot fire on a trade that
never got there. If no bar reaches the target, no coins.

Stop placement decides whether 2R is reached, so it is a real editorial choice,
not a detail — on the SPY breakout-retest, a stop under the retest low reaches
2.61R while a stop under the level tops out at 1.72R. Pick it before you look at
the outcome.

## Timing

`TradingQuiz.tsx` holds the beat constants; everything after the countdown is
derived from it, so changing the answer window can't desync the reveal.
Currently a **5-second answer countdown** (5 digits × 30 frames), total 682
frames / 22.7s at 30fps. Fixtures must carry `durationInFrames: 682` — that's
`TRADING_QUIZ_MIN_FRAMES`, exported from the composition (the risk/reward act
extended it; older docs saying 546 are stale).

**Zoom fixtures run 900 frames / 30s** (`TRADING_QUIZ_ZOOM_FRAMES`). A fixture
carrying a `zoom` prop gets a 218-frame prologue in front of the classic
timeline, and every act from the level draw onward shifts by that one constant —
so the back half keeps its relative spacing and cannot desync. Inside the
component the shifted clock is `tl`; the real clock is `frame`. **Anything
timed off a post-countdown constant must read `tl`.** Three sites reading
`frame` shipped once and put the risk/reward act seven seconds early, while its
audio — placed off `SH + RR_ZONES_IN` — stayed correct, so the coins poured
before the chime.

## Time-axis zoom

`scripts/ta_quiz/find_anchored_level.py` finds a level's prior tests across a
long series and decides how much of that history may be **played** versus merely
**revealed**:

- playback is hard-capped at **126 bars / 6 months** — older tape is exposed by
  the camera widening, never printed bar by bar, because watching three years
  print is dead screen time;
- the tape runs **forward** out of the past, so the window may only ever widen
  to expose older bars. Printing a recent bar and then revealing an older one is
  a tape running backwards;
- below 3 distinct prior visits, or under 6 months of history behind the oldest,
  it reports **UNMATCHED**. On the SPY five-year series it refuses 8 of the 11
  detected formations, which is the rail working, not a bug.

Below ~3.5px per bar the candles cross-fade to a close-line silhouette. At the
deep stop this reel runs 1.2px/bar, so that substitution is required for
legibility, not decoration.

```bash
python scripts/ta_quiz/find_anchored_level.py --list      # which formations qualify
python scripts/ta_quiz/find_anchored_level.py --fixture   # emit the zoom fixture
```

## Adding a host (Maya)

`QuizWithHost` composites a rendered quiz with a generated talking-head clip as
a screen-share. Grok generates only Maya (see
`higgs/maya-grok-conventions.md` for the required prompt format); Remotion does
the compositing, so the chart is embedded pixel-exact rather than risking a
generative model regenerating and silently breaking the pattern.

```bash
cp <maya-clip>.mp4 remotion/public/host/maya_<slug>.mp4
# point hostSrc at it in remotion/src/fixtures/quiz_with_host_*.json, then:
cd remotion && npx remotion render src/index.ts QuizWithHost ...
```

## Rails

There are now **two kinds of fixture**, and the rails differ:

**Synthetic-library fixtures** (`make_fixture.py`)
- The OHLC is built to demonstrate the pattern. Say so on screen, never present
  it as a real chart of a real asset, and never attach a ticker or timeframe.
- Keep the disclaimer footer. On a synthetic reel it is the only thing telling
  the viewer the candles were drawn rather than traded.

**Real-bar fixtures** (`find_real_pattern.py`, `find_anchored_level.py`)
- The ticker, timeframe and date range go in the **chrome bar**, which is what
  makes the window self-evidently historical.
- A literal BUY/SELL badge is permitted (owner ruling 2026-08-12) because the
  window is closed and dated. `answerLabel` remains correct for recent windows.
- The footer is optional. Pass `""` — and note that Remotion merges `--props`
  *over* `defaultProps`, so **omitting** the key leaves the previous fixture's
  footer on screen rather than removing it.

Both kinds:
- Frame patterns as education, not calls. `ruleText` describes the setup and its
  confirmation condition, and carries the honest hit rate when one is known —
  the drawn instance is a winner by construction, so without it the reel reads
  as a 100% strike rate.
