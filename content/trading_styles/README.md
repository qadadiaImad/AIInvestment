# Find Your Trading Style — long-form explainer

**Deliverable:** `find_your_trading_style.mp4` — 1080×1920, 30fps, **2:20** (4200 frames), silent.
**Voiceover script:** [`voiceover_script.md`](voiceover_script.md) — 361 words, timed to the beat map, ready for Higgsfield.

Ten trading styles, twelve seconds each, every one with its own animated chart
simulation. Built in our own visual language (the MAYA LAB navy/grid board that
`TradingQuiz` uses) rather than reproducing the reference card's layout — the
*concepts* are common knowledge, the design is not.

---

## The premise, and why it constrains everything

No style is better than another. The right one depends on the viewer's time,
temperament and goals. That is not a disclaimer bolted on the end — it shapes
the whole piece:

- Per-style accents are **chapter colours**, never a verdict. Scalping is not
  red because it is dangerous.
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

## How it is built — three sources, deliberately separated

| Source | Owns | Why |
|---|---|---|
| `build_fixture.py` → `STYLES` | number, name, timeframe, hold | Facts. Overwrites any agent that "improves" a timeframe. |
| `generate_regimes.py` | **all OHLC, all trade marker positions** | Numbers. Seeded, deterministic, asserted. |
| The workflow → `content.json` | oneLiner, bullets, demands, VO | Prose. What models are actually good at. |

**Models never touch the numbers.** Every previous attempt at model-authored OHLC
in this repo produced geometry that looked right and was wrong. Each regime
asserts the claim its scene makes and *raises* rather than rendering:

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

### On chart scale

Every regime is normalised to fill the plot — otherwise scalping is a flat line
and unreadable for twelve seconds. That makes a 1.9-point microrange *look* as
violent as a 35-point trend. The terminal chrome therefore states the real span
(`52 bars · span 1.9 pts`): shape is comparable across scenes, scale is not, and
the viewer is told which is which.

## Reproduce

```bash
python scripts/trading_styles/generate_regimes.py      # OHLC + trades, asserted
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

---

*Charts are simulations built to demonstrate each style — not real market data.
Educational only, not financial advice.*
