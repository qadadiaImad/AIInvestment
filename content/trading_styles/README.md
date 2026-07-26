# Find Your Trading Style — long-form explainer

**Deliverable:** `find_your_trading_style.mp4` — 1080×1920, 30fps, **2:20** (4200 frames), silent, CRF 19 master (31 MB).
**Preview:** `find_your_trading_style_preview.mp4` — same cut at CRF 27 (8 MB), for review and sharing.
**Voiceover script:** [`voiceover_script.md`](voiceover_script.md) — 361 words, timed to the beat map, ready for Higgsfield.

Ten trading styles, twelve seconds each, every one with its own animated chart —
built from **real SPY price data**, not simulations. Green trading-terminal
treatment on near-black: dotted world map, ruled grid, glowing candles, boxed
SUPPORT/RESISTANCE tags, moving average, true-range histogram.

---

## The premise, and why it constrains everything

No style is better than another. The right one depends on the viewer's time,
temperament and goals. That is not a disclaimer bolted on the end — it shapes
the whole piece:

- Accents are one green family, not ten hues. A rainbow would read as ranking
  the styles, and the terminal look is monochrome by design.
- Every scene carries a **"WHAT IT ASKS OF YOU"** block. If a style is genuinely
  unsuitable for most retail traders without infrastructure, that block says so.
- The voiceover is directed to hold **one energy across all ten** — no brightening
  for scalping, no flattening for portfolio work. Tonal consistency is what makes
  "no style is better" believable.
- The close is `There is no best style.`

## Beat map

| Frames | Time | Segment |
|---|---|---|
| 0–299 | 0:00–0:10 | Intro — premise + all ten names |
| 300–3899 | 0:10–2:10 | Ten scenes, 360 frames each |
| 3900–4199 | 2:10–2:20 | Close |

Inside a 12-second scene: card at 0, terminal at 26, bars print 40→~172,
levels 120, trade markers 158, bullets 196, demands 244, fade 344.

## The charts are real

Every window below is actual SPY price data pulled from Interactive Brokers.
`find_real_windows.py` scans the series and keeps only windows that already pass
the structural test for their regime — it does not construct anything.

**Snapshot: 2026-07-26 17:41 UTC.** Daily bars `period=TWO_YEARS, step=ONE_DAY`;
minute bars `period=ONE_DAY, step=ONE_MIN`; both `outside_rth=false`.

| Regime | Symbol | Interval | Window | Bars |
|---|---|---|---|---|
| `intraday-session` | SPY | 8m (rolled up from 1m) | 2026-07-24 13:30Z → 2026-07-24 19:30Z | 46 |
| `microrange` | SPY | 1m | 2026-07-24 13:52Z → 2026-07-24 14:43Z | 52 |
| `swing-leg` | SPY | 1d | 2026-04-01 → 2026-06-03 | 44 |
| `multimonth-trend` | SPY | 1d | 2026-03-09 → 2026-06-02 | 60 |
| `sustained-trend` | SPY | 1d | 2025-04-21 → 2025-07-03 | 52 |
| `consolidation-break` | SPY | 1d | 2024-09-25 → 2024-12-04 | 50 |
| `range-bound` | SPY | 1d | 2025-12-17 → 2026-03-06 | 54 |
| `event-gap` | SPY | 1d | 2025-12-02 → 2026-02-04 | 44 |
| `systematic` | SPY | 1d | 2024-12-04 → 2025-02-26 | 56 |
| `rotation` | SPY | 1d | 2025-04-22 → 2025-06-30 | 48 |

Day trading is the one exception to window-scanning: it has to be a *whole*
session, so the full real 390-minute day is rolled up into 46 genuine 8-minute
OHLC bars rather than a mid-session fragment being cropped out.

**Data integrity.** IBKR "Last"-sourced daily bars occasionally close a cent or
two outside the session's aggregated high/low. Those are normalised by extending
the wick to contain the body. Two bars deviated by more than 15 cents; those are
quarantined, and any window containing one is rejected outright rather than
quietly patched.

**The histogram is TRUE RANGE, not volume**, and is labelled that way on screen.
Volume was not transcribed with these bars, and drawing an invented volume series
under real prices would have been the one dishonest element in the piece.

## How it is built — three sources, deliberately separated

| Source | Owns | Why |
|---|---|---|
| `build_fixture.py` → `STYLES` | number, name, timeframe, hold | Facts. Overwrites any agent that "improves" a timeframe. |
| `find_real_windows.py` | **which real window, and where the markers go** | Numbers. Scanned from real bars, never authored. |
| The workflow → `content.json` | oneLiner, bullets, demands, VO | Prose. What models are actually good at. |

**Models never touch the numbers.** Each regime's test is applied to real bars,
and a window is only kept if it already satisfies it:

```
microrange           drift < 45% of span, or it isn't a scalping tape
intraday-session     an actual opening drive exists
swing-leg            the leg travels, and is held > 15 bars
multimonth-trend     ≥2 real drawdowns, and the trade spans both
sustained-trend      higher highs AND higher lows (verified, not asserted by prose)
consolidation-break  box respected before the break; a CLOSE beyond it after
range-bound          both boundaries tested ≥2×; no close outside
event-gap            the event bar OPENS above the prior high; range expands >2.5×
systematic           the rule fires ≥5 times
```

**Trade markers are derived from the series too.** The first render put a "Buy"
marker at the *top* of the range, because the fractions came from an agent that
had never seen the generated bars. Markers are now absolute indices computed from
local extrema, and the range regime asserts that every "Buy" sits in the bottom
third and every "Sell" in the top third of its own range.

`generate_regimes.py` (the earlier synthetic path) is kept for reference — it is
where these tests were first written — but it no longer feeds the video.

### On chart scale

Every window is normalised to fill the plot — otherwise the scalping chart is a
flat line and unreadable for twelve seconds. That makes a $2 microrange *look* as
violent as a $90 trend. The terminal chrome therefore names the instrument, the
timeframe, the exact date range and the real span (`52 bars · span $2.11`): shape
is comparable across scenes, scale is not, and the viewer is told which is which.

## Reproduce

```bash
python scripts/trading_styles/find_real_windows.py     # scan real IBKR bars
python scripts/trading_styles/build_fixture.py         # merge + length-check copy
cd remotion && npx remotion render src/index.ts TradingStyles out.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec h264 --crf 18
```

A single render exceeds the shell timeout here; this one was rendered as
`--frames=0-1399`, `1400-2799`, `2800-4199` and concatenated with
`ffmpeg -f concat -c copy`.

## Review trail

The content went through an adversarial pass ([`review_issues.json`](review_issues.json)).
Five issues were found and all five applied. Two were substantive:

- **A fabricated regulatory term.** The copy said "the pattern day trader *capital
  rule*", which is not a thing — it's the Pattern Day Trader rule, which *has* an
  equity requirement.
- **A wrong definition of a trend:** "higher highs **or** higher lows". Higher highs
  with lower lows is an expanding range, not a trend. Corrected to *and* — and the
  `sustained-trend` generator now verifies both conditions on the actual series.

The rest were a character-limit overrun, two colliding markers, and a chartNote
that asked for more pullbacks than the marker data supplied.

## Audio

The script is written for a separate voiceover pass in Higgsfield. It is timed at
roughly 150–160 wpm, deliberately under the per-segment budget — undershooting a
12-second slot reads better than compressing it. Delivery notes, pause positions
and per-segment emphasis are in the script document.

**To actually record and mux it, see
[`references/higgsfield-audio-workflow.md`](../../references/higgsfield-audio-workflow.md)** —
setup, the offset table, the ffmpeg assembly recipe, and a paste-ready prompt.
It is a laptop task: `higgsfield auth login` is interactive and cannot complete
in a remote container.

---

*Charts are real SPY price data via Interactive Brokers, snapshot 2026-07-26
17:41 UTC. Historical examples chosen to illustrate each style. Educational only,
not financial advice.*
