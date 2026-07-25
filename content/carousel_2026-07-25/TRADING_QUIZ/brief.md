# Trading Quiz reel — bearish engulfing at resistance — 2026-07-25

A "guess the next move" candlestick quiz, benchmarked against the format that
does numbers on IG (the @forextradingclub.en reel: hook → chart → BUY/SELL fork
→ countdown → reveal). Silent by design — no audio in either version.

**Two versions of the same setup**, so they can be compared head to head:
- `trading_quiz_engulfing.mp4` — rendered here in Remotion (composition
  `TradingQuiz`, fixture `remotion/src/fixtures/trading_quiz_engulfing_2026-07-25.json`)
- `grok_prompt.md` — the prompt to generate the same reel with Grok

## The strategy shown

Not a vibe call — a nameable, textbook setup, so the reveal teaches something:

**Bearish engulfing at a thrice-tested resistance.**
1. Price trends up, then stalls into a level at 100 and gets rejected — **three
   separate touches** (candles 7, 12, 18 all wick into ~100 and close below).
2. On the third test, a green candle pushes into the level and closes near its
   high (o 97 → c 99.8) — looks like the breakout is finally coming.
3. The next candle **opens above that green candle's close (100.5 > 99.8) and
   closes below its open (96 < 97)** — a true bearish engulfing. The red body
   fully contains the green body. Buyers tried, sellers took the entire candle.
4. **Confirmation** is the next candle printing a lower high *and* a lower low
   (h 97 < 101, l 91 < 95) — which is exactly what the reveal shows, followed
   by two more down candles breaking the range.

Answer: **SELL.**

### Why this is a real setup, not invented

Bearish engulfing is standard candlestick literature (Nison), and
support/resistance is the most basic structural concept in TA. The combination
— a pattern that only counts when it fires *at a level that's already held
multiple times* — is the honest version of the strategy, because the level is
what gives the candle its meaning. A bearish engulfing in the middle of nowhere
is noise.

**What the reel deliberately doesn't claim:** that this is a guaranteed signal.
It fails on strong-trend breakouts, in thin markets, and on news spikes. Real
application adds a volume check and higher-timeframe trend alignment. The reel
teaches the pattern; it doesn't promise an outcome, and the on-screen text is
framed as "the setup," not "the trade."

## Data honesty

The OHLC sequence is **synthetic** — hand-built to demonstrate the pattern
cleanly. It is **not** a real chart of a real asset, and the reel says so on
every frame ("Illustrative example, not a real chart"). This matters: the
benchmark reel captions its chart as a real Bitcoin 1-hour chart. Ours doesn't
claim that, because it isn't, and passing a constructed chart off as live market
data would be exactly the kind of thing this repo's rails exist to prevent.

## The engine

`TradingQuiz` is built as a **reusable quiz engine**, not a one-off. Everything
that defines the quiz lives in the fixture:

| Field | Purpose |
|---|---|
| `candles` | full OHLC sequence (setup + reveal) |
| `revealFrom` | index where the setup ends and the reveal begins |
| `levelPrice` / `levelLabel` | the support/resistance line and its caption |
| `patternName` | label on the highlight box |
| `answer` | `BUY` or `SELL` — drives arrow colors, glow, and the reveal badge |
| `answerLine` | one-line explanation under the answer |
| `ruleTitle` / `ruleText` | the closing lesson card |
| `footer` | the persistent disclaimer |

Swap the fixture → different pattern, different answer, same reel. A bullish
version (hammer/pin bar at support, `answer: "BUY"`) needs no code changes.

Beat timing (30fps, 480 frames / 16s), all named constants at the top of the
composition:

| Beat | Frames | Seconds |
|---|---|---|
| Hook | 0–36 | 0.0–1.2 |
| Chart prints (19 setup candles) | 36–150 | 1.2–5.0 |
| Resistance level draws | 118–140 | 3.9–4.7 |
| Pattern box + label | 158+ | 5.3+ |
| BUY/SELL arrows | 196+ | 6.5+ |
| Countdown 3-2-1 | 232–316 | 7.7–10.5 |
| Answer badge | 316+ | 10.5+ |
| Reveal candles | 344–377 | 11.5–12.6 |
| Lesson card | 392+ | 13.1+ |

## Render

```
cd remotion && npx remotion render src/index.ts TradingQuiz out.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec h264 --crf 17
```

## QA notes (fixed during this build)

Two layout bugs caught by extracting frames and inspecting them, both fixed:
1. **BUY/SELL labels clipped off the right edge** — arrows were 196px long with
   the label another 46px beyond the head, which overran 1080px. Shortened to
   132px and reduced the label to 46px type.
2. **Pattern label sat on top of the reveal candles** — it was anchored directly
   under the highlight box, which is exactly where the next candles print. Moved
   to a fixed clear band below the candle field (`PATTERN_LABEL_Y`) with a dashed
   leader line back up to the box.

## Compliance

- Disclaimer on-screen for the full duration (silent reel — no spoken rail
  possible, so the persistent footer carries it).
- Chart explicitly labeled illustrative/synthetic — no implied real asset,
  no ticker, no timeframe claim.
- Frames the pattern as education ("THE SETUP"), never as a call — no entry,
  no target, no "this will drop."
