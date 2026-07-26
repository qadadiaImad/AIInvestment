# Index-Dispersion Reel ("The Gap") — Design Spec

> Educational/research only — **not financial advice**. The dispersion trade shown is an
> advanced, institutional cash strategy presented to *explain how it works*, not as a
> recommendation. The gap itself is an **illustrated mechanic**, not live price data.

**Date:** 2026-07-26
**Branch:** feat/multi-sector-research-platform (no push until owner says)
**Consumer:** @valuewithvalues IG — a "chart lesson" explainer reel, sibling to the shipped
Correlation reel it visually extends.

---

## 1. Goal

A ~45–50s vertical (1080×1920) Remotion explainer that teaches the **cash index-dispersion
/ index-arbitrage** trade: *an index equals the sum of its stocks; when the two prices drift
apart, you buy the cheap side and sell the rich side, and profit when the gap closes —
regardless of market direction.* Plus a short **mini cut** (hook → payoff beat → CTA), both
text-on-screen with synced royalty-free music. Matches how the Correlation reel shipped.

### What we teach (the cash trade, stated correctly)
- An index (e.g. an AI-stack ETF) is *by definition* the weighted basket of its constituents.
  Price(index) should equal Value(basket) — the law of one price.
- In real markets they **disperse**: a visible **gap** opens between the two prices.
- **The trade:** index rich → *sell index, buy basket*; index cheap → *buy index, sell basket*.
  Long one leg, short the other ⇒ **market-neutral**.
- **Positive PnL when the gap closes** — direction-agnostic; you collect the spread.
- **The catch:** the gap can widen before it converges; thin margins get eaten by
  borrow/fees; in a panic the creation/redemption plumbing can jam. Advanced/institutional.

> Explicitly NOT the volatility-dispersion (options/short-correlation) version — owner chose
> the simpler cash version. No options, no greeks.

---

## 2. Architecture — reuse the Correlation reel's spine

`halal-reels/` is a Remotion 4 project (30fps, 1080×1920). We reuse, unchanged:

- **`theme.ts`** — `C` palette (`bg #0A0D12`, `mint #7FE9C2`, `amber #E0A23B`, `emerald
  #34D399`, `muted`, `panel`, `line`), `FONT` (Fraunces/Inter/JetBrainsMono).
- **`ui.tsx`** — `Bg` (tint, driftSpeed), `Foot`, `Kicker`, `Slam`, `clamp`,
  `easeInOutCubic`, `easeOut`, `inOut`, `pop`.
- **`charts.tsx`** — `buildPoints`, `buildSmoothPath` (Catmull-Rom→bezier), `idleWobble`
  (module-private; the new chart lives in the same module to reuse them).
- **Audio bed pattern** — `quiz/music.mp3` at low volume with per-cue ducking; `quiz/reveal.mp3`
  whoosh at each phase arrival (both already in `public/quiz/`, Mixkit Free License).
- **`mini?: boolean` prop pattern** — one component, full vs mini via offset beat constants.
- **`Root.tsx`** registration + the render-to-`higgs/` convention.

### New units (all pure/presentational, deterministic — no `Math.random`/`Date`)

**A. `charts.tsx` additions**

1. **`GapChart`** — the centerpiece. Draws the **INDEX** line (amber) and **BASKET** line
   (mint) as smooth curves (reusing `buildPoints`/`buildSmoothPath`/`idleWobble`), plus a
   **filled gap region** between them (mint→amber vertical gradient) whose area *is* the
   dispersion. Lead dots + floating `INDEX`/`BASKET` tags. Optional gap-size caption anchor.
   ```
   GapChart({ indexData: number[], basketData: number[], reveal: number,
              liveFrame?: number, gapEmphasis?: number /*0..1 fill opacity*/,
              width, height })
   ```
   Contract: `indexData`/`basketData` are normalized 0..1, equal length; the fill polygon
   is exactly `[index path] + [reversed basket path]` so it always hugs the drawn lines.

2. **`PnLMeter`** — horizontal bar, center-anchored. `value ∈ [-1, 1]` fills right in
   **emerald** for profit, left in **amber** for drawdown (NO red — owner rule). Numeric
   readout is an abstract PnL index ("+PROFIT" / "−DRAWDOWN", or a unit-free number), never a
   fabricated dollar figure. `liveFrame` drives a gentle glow pulse.
   ```
   PnLMeter({ value: number /*-1..1*/, width?, liveFrame?, label? })
   ```

**B. `dispersionData.ts`** (new; models `correlationData.ts`'s deterministic style)

- `COMMON_LEVEL: number[]` — a shared "market" wander (deterministic sine mix, mean ≈0.5,
  bounded so ±gap/2 stays in [0,1]). This is what makes both lines rise/fall *together* so
  the reel can show "direction doesn't matter."
- `indexAt(gap)`, `basketAt(gap)` — `COMMON_LEVEL ± gap/2` (index above, basket below).
  Pure functions of the scalar `gap`.
- `gapAtDemoFrame(f)` — the single knob driving the demo (mirrors `rAtDemoFrame`): the
  scalar gap over demo-time, using the same HOLD/SWEEP scheduling as Correlation.
- `pnlAtDemoFrame(f)` — derived PnL in [-1,1] from the gap relative to the entry gap
  (trade put on when gap is wide; PnL rises as gap closes; goes amber-negative when the gap
  widens past entry during the "catch" phase, then recovers).
- `BASKET_TICKERS: string[]` — the real ~12–15 AI-cluster names for texture only
  (ASML, AMAT, LRCX, TSM, MU, NVDA, AMD, KLAC, …). Labels/flavor, not the gap source.
- `DISP_DATE = "2026-07-26"`.

**C. `DispersionReel.tsx`** (new; mirrors `CorrelationReel.tsx`)

**D. `Root.tsx`** — register `DispersionReel` (full) + `DispersionReelMini` (`mini:true`).

`halal-reels/`'s other reels and the correlation reel are **untouched**.

---

## 3. Beat structure (30fps)

Full reel — TITLE → DEFINE → DEMO → CLOSE (mirrors Correlation; target ~45–50s):

| Beat | ~Len | Content |
|---|---|---|
| **TITLE** | 90f / 3s | `Kicker "TODAY'S CHART LESSON"` + `Slam "DISPERSION"`. |
| **DEFINE** | 150f / 5s | "An index is just its stocks, added up." INDEX & BASKET lines shown **locked together** (gap≈0) — same number, two names. |
| **DEMO** | ~760f / ~25s | The continuous synced GapChart + PnLMeter. Four phases (holds + sweeps), see below. |
| **CLOSE** | 210f / 7s | Tie-back + CTA `Comment "GAP"` + full rail + `data as of 2026-07-26`. |

**DEMO phases** (each a HOLD ≈150–160f with a short SWEEP between, exactly like the
Correlation `HOLD_LEN`/`SWEEP_LEN` model; a `reveal.mp3` whoosh at each phase arrival):

1. **THE GAP OPENS** — `gap` sweeps 0→MAX; the fill grows; gap label appears.
   Caption: *"In real markets, the two prices drift apart."*
2. **THE TRADE** — `gap` holds at MAX; two leg badges snap in: **▲ BUY the cheap side**
   (mint) / **▼ SELL the rich side** (amber). Caption: *"Buy the cheap side. Sell the rich side."*
3. **THE GAP CLOSES → PnL** — `gap` sweeps MAX→~0 while `COMMON_LEVEL` visibly wanders up
   *and* back down (both lines together) and the **PnLMeter fills emerald**.
   Caption: *"Market up or down — you only need the gap to close."*
4. **THE CATCH** — a fresh entry at MAX, `gap` widens to ~1.4×MAX (PnLMeter dips **amber**),
   then converges (recovers emerald). Caption: *"It can widen before it closes. That's the risk."*

**Mini cut** — `MINI_HOOK` (~80f punchy retention hook, e.g. *"Two prices. One basket.
Wall Street's oldest trade."*) → DEMO → CLOSE. Same offset-constants technique as
`CorrelationReel` so audio stays in lockstep; default (full) unchanged.

---

## 4. Palette, rails, honesty

- **Colors:** INDEX = amber `#E0A23B`, BASKET = mint `#7FE9C2`, gap fill = mint→amber
  gradient, PnL profit = emerald `#34D399`, PnL drawdown = amber. **No red as emphasis**
  (owner rule) even though `C.red` exists.
- **`ILLUSTRATIVE` badge** (reuse the Correlation one) persistent on the demo — the gap is a
  taught mechanic, not a live ETF-vs-NAV reading. We never show a fabricated "today's gap = X".
- **Rail (persistent `Foot`)**: `"Cash index-arbitrage is an advanced institutional strategy,
  shown for education — not a recommendation. Illustrative mechanic, not live prices.
  Educational — not financial advice."`
- **Real vs illustrative:** `BASKET_TICKERS` are real names we track (texture); the gap/PnL
  motion is illustrative and labeled as such. No laundering illustration into fact.

---

## 5. Backgrounds (Grok, already being generated)

The three portrait heroes already prompted fit without regeneration:
- **SCATTER** → TITLE/DEFINE ambient (the dispersed basket).
- **LOCKSTEP** (points converging to one column) → reframed as the **gap snapping shut /
  convergence payoff** behind DEMO phase 3–4.
- **TERMINAL** → CLOSE/CTA.
Used as `Bg`-style dimmed backdrops behind the chart (dark scrim, chart stays legible), same
treatment as the daily-screen heroes. Drop files in `higgs/`; wiring is a build step.

---

## 6. Deliverables

- `halal-reels/src/dispersionData.ts`, `DispersionReel.tsx`; `charts.tsx` +`GapChart`/`PnLMeter`;
  `Root.tsx` two compositions.
- Renders: `higgs/dispersion_reel.mp4` (full) + `higgs/dispersion_reel_mini.mp4` (mini).
- IG caption (rails-compliant) + keyword `GAP`.
- `.mp4` outputs are gitignored (regenerable media); `.tsx`/`.ts` sources are tracked.

## 7. Testing / verification

- **Pure math is deterministic** → unit-test `gapAtDemoFrame`, `pnlAtDemoFrame`, `indexAt`/
  `basketAt` (monotonic gap→PnL, bounds in [0,1], phase boundaries) with whatever runner
  `halal-reels/package.json` provides (Vitest if present; else a scratch node assertion —
  the plan inspects and picks). Model on how `correlationData` math is reasoned about.
- `cd halal-reels && npx tsc --noEmit` clean.
- Render both compositions; **visually verify stills** (verification-before-completion):
  gap opens/closes, legs read, PnL fills green then amber-then-green on the catch, rails +
  ILLUSTRATIVE present, no red, heroes legible. Show extracted frames, not an assertion.

## 8. Model / process (owner rules)

- All subagents / workflow `agent()` calls on **`model:'sonnet'`**; orchestrator alone on the
  top model. Commit trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- TDD the pure data/math (superpowers:test-driven-development); the visual composition is
  built against tsc + render + visual review.

## 9. Self-review notes

- Scope is one reel + one mini, one new data module, two new chart primitives — single plan.
- Types consistent: `number[]` normalized series into `GapChart`; scalar `gap`/`pnl` knobs;
  `mini` boolean like Correlation. No placeholders/TBDs.
- YAGNI: no options/greeks, no live-gap fetch (illustrative), no VO (music only), reuse
  existing audio + Bg + primitives.
