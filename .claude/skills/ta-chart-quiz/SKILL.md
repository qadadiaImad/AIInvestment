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

**`renderable` matters.** The engine draws candles plus one horizontal level.
Anything tagged `needs-overlay` (trendlines, channels, volume bars, moving
averages, indicator panes) will not read correctly as-is — `make_fixture.py`
warns, and the honest options are to pick a different pattern or extend the
composition first.

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

The reel is otherwise silent, but the countdown **ticks** — five escapement
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

## Timing

`TradingQuiz.tsx` holds the beat constants; everything after the countdown is
derived from it, so changing the answer window can't desync the reveal.
Currently a **5-second answer countdown** (5 digits × 30 frames), total 546
frames / 18.2s at 30fps. Fixtures must carry `durationInFrames: 546` — that's
`TRADING_QUIZ_MIN_FRAMES`, exported from the composition.

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

- The OHLC is **synthetic** — built to demonstrate the pattern. The footer says
  so on every frame. Never present it as a real chart of a real asset, and never
  attach a ticker or timeframe to it.
- Frame patterns as education, not calls: no entry, no target, no "this will
  drop". `ruleText` describes the setup and its confirmation condition.
- Keep the disclaimer footer. It's the compliance rail on a silent reel.
