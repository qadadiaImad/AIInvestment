# Index-Dispersion Reel ("The Gap") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A ~45–50s vertical Remotion explainer (+ a mini cut) that teaches the cash index-dispersion / index-arbitrage trade — index vs its basket, a gap that opens, the buy-cheap/sell-rich legs, PnL when the gap closes, and the catch — reusing the shipped Correlation reel's spine.

**Architecture:** New `dispersionData.ts` holds all deterministic data + math (a scalar `gap` knob and derived `pnl`, exactly like `correlationData.ts`'s `r`-knob). Two new presentational primitives (`GapChart`, `PnLMeter`) go in `charts.tsx` beside `DualLineChart`, reusing its private `buildPoints`/`buildSmoothPath`/`idleWobble`. `DispersionReel.tsx` mirrors `CorrelationReel.tsx` beat-for-beat (TITLE→DEFINE→DEMO→CLOSE + `mini` hook variant + audio bed). `Root.tsx` registers two compositions. `halal-reels/`'s other reels are untouched.

**Tech Stack:** Remotion 4.0.496, React 19, TypeScript 5.9, `@remotion/google-fonts`; Vitest (added here) for the pure-math unit tests. Rendering via `npx remotion render`.

## Global Constraints

- **Spec:** `docs/superpowers/specs/2026-07-26-dispersion-reel-design.md`.
- **Palette (from `theme.ts` `C`):** INDEX line = amber `#E0A23B`, BASKET line = mint `#7FE9C2`, gap fill = mint→amber gradient, PnL profit = emerald `#34D399`, PnL drawdown = amber `#E0A23B`. **NO red as emphasis** (owner rule) — never use `C.red`/`C.redHot` in this reel.
- **Determinism:** no `Math.random` / `Date.now` / argless `new Date()` anywhere in reel code — all motion is `useCurrentFrame()`- or index-driven sine (matches `correlationData.ts`).
- **Rails (persistent `Foot`):** `"Cash index-arbitrage is an advanced institutional strategy, shown for education — not a recommendation. Illustrative mechanic, not live prices. Educational — not financial advice."`
- **Honesty:** persistent `ILLUSTRATIVE` badge on the demo; `BASKET_TICKERS` are real names used as texture only; never render a fabricated dollar/gap figure.
- **CTA keyword:** `GAP`.
- **Format:** 30fps, 1080×1920. Full reel + a `mini` cut via one component + a boolean prop (mirror `CorrelationReel`'s `mini`).
- **Verify commands:** `cd halal-reels && npx tsc --noEmit` (clean) and `npx vitest run` (green) after every task that touches TS logic.
- **Model policy:** every subagent / workflow `agent()` runs `model:'sonnet'`. Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Branch `feat/multi-sector-research-platform`; no push until owner says.
- **Media:** `.mp4` outputs are gitignored; `.ts`/`.tsx` sources are committed.

---

### Task 1: Test tooling + dispersion base series (`COMMON_LEVEL`, `indexAt`, `basketAt`)

**Files:**
- Modify: `halal-reels/package.json` (add `vitest` devDep + `"test"` script)
- Create: `halal-reels/src/dispersionData.ts`
- Test: `halal-reels/src/dispersionData.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `COMMON_LEVEL: number[]` — length-60 shared "market" wander, every element in `[0,1]`.
  - `indexAt(gap: number): number[]` — `COMMON_LEVEL[i] + gap/2`, clamped to `[0,1]`.
  - `basketAt(gap: number): number[]` — `COMMON_LEVEL[i] - gap/2`, clamped to `[0,1]`.
  - `DISP_LEN = 60` (exported const).

- [ ] **Step 1: Add Vitest tooling**

In `halal-reels/package.json`, add to `devDependencies`: `"vitest": "^3.0.0"`, and to `scripts`: `"test": "vitest run"`. Then run `cd halal-reels && npm install`.

- [ ] **Step 2: Write the failing test**

Create `halal-reels/src/dispersionData.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { COMMON_LEVEL, indexAt, basketAt, DISP_LEN } from "./dispersionData";

describe("dispersion base series", () => {
  it("COMMON_LEVEL is length DISP_LEN and bounded 0..1", () => {
    expect(COMMON_LEVEL).toHaveLength(DISP_LEN);
    for (const v of COMMON_LEVEL) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
  });

  it("index sits above basket by exactly `gap` before clamping", () => {
    const g = 0.4;
    const idx = indexAt(g);
    const bkt = basketAt(g);
    // middle sample well away from the 0/1 rails -> no clamping
    const i = 20;
    expect(idx[i] - bkt[i]).toBeCloseTo(g, 6);
  });

  it("gap = 0 makes the two lines identical", () => {
    expect(indexAt(0)).toEqual(basketAt(0));
  });

  it("stays in [0,1] even at the widest gap used (0.59)", () => {
    for (const v of [...indexAt(0.59), ...basketAt(0.59)]) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd halal-reels && npx vitest run src/dispersionData.test.ts`
Expected: FAIL — cannot find module `./dispersionData`.

- [ ] **Step 4: Write minimal implementation**

Create `halal-reels/src/dispersionData.ts`:

```ts
// Deterministic data + math for the cash index-dispersion reel ("The Gap").
// Pure functions of index / a scalar `gap` knob only -- no Math.random /
// Date.now -- so every render is bit-identical (mirrors correlationData.ts).
// The gap is an ILLUSTRATED teaching mechanic, NOT live ETF-vs-NAV data.

export const DISP_DATE = "2026-07-26";
export const DISP_LEN = 60;

const clamp01 = (x: number): number => Math.max(0, Math.min(1, x));

// Shared "market" wander: index and basket ride this SAME curve, offset only
// by the vertical `gap`. That is what lets the reel show "market up or down
// doesn't matter -- only the gap matters." Mean ~0.5, gentle amplitude so
// level +/- gap/2 stays within [0,1] for every gap the demo visits.
const genLevel = (n: number): number[] =>
  Array.from(
    { length: n },
    (_, i) =>
      0.5 +
      0.1 * Math.sin(i * 0.18) +
      0.05 * Math.sin(i * 0.37 + 1.1) +
      0.03 * Math.sin(i * 0.09 + 0.5),
  );

export const COMMON_LEVEL: number[] = genLevel(DISP_LEN);

/** Index line at a given scalar gap: rides COMMON_LEVEL, lifted by gap/2. */
export const indexAt = (gap: number): number[] => COMMON_LEVEL.map((v) => clamp01(v + gap / 2));

/** Basket line at a given scalar gap: rides COMMON_LEVEL, dropped by gap/2. */
export const basketAt = (gap: number): number[] => COMMON_LEVEL.map((v) => clamp01(v - gap / 2));
```

- [ ] **Step 5: Run tests + typecheck**

Run: `cd halal-reels && npx vitest run src/dispersionData.test.ts && npx tsc --noEmit`
Expected: PASS (4 tests) and no TS errors.

- [ ] **Step 6: Commit**

```bash
git add halal-reels/package.json halal-reels/package-lock.json halal-reels/src/dispersionData.ts halal-reels/src/dispersionData.test.ts
git commit -m "feat(dispersion): vitest + base index/basket series

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Demo schedule — `gapAtDemoFrame`, `pnlAtDemoFrame`, phase constants, tickers

**Files:**
- Modify: `halal-reels/src/dispersionData.ts`
- Test: `halal-reels/src/dispersionData.test.ts` (append)

**Interfaces:**
- Consumes: `COMMON_LEVEL` (Task 1).
- Produces:
  - `GAP_MAX = 0.42`, `GAP_WIDE = 0.588` (the "catch" over-shoot).
  - Demo phase constants (all frame offsets, demo-local): `OPEN_LEN`, `TRADE_LEN`, `CONVERGE_LEN`, `CATCH_LEN`, and `DISP_DEMO_LEN` (their sum).
  - `gapAtDemoFrame(f: number): number` — scalar gap over demo-local frames, in `[0, GAP_WIDE]`.
  - `pnlAtDemoFrame(f: number): number` — PnL in `[-0.5, 1]`; `0` until the trade is placed (end of TRADE), positive as the gap closes, negative when the gap widens past entry during CATCH.
  - `DISP_WHOOSH_OFFSETS: number[]` — demo-local frames where each phase begins (for audio cues).
  - `BASKET_TICKERS: string[]` — 12 real AI-cluster names (texture only).

- [ ] **Step 1: Write the failing tests** (append to `dispersionData.test.ts`)

```ts
import {
  GAP_MAX,
  GAP_WIDE,
  gapAtDemoFrame,
  pnlAtDemoFrame,
  OPEN_LEN,
  TRADE_LEN,
  CONVERGE_LEN,
  DISP_DEMO_LEN,
  BASKET_TICKERS,
} from "./dispersionData";

describe("dispersion demo schedule", () => {
  it("opens from ~0 to GAP_MAX across the OPEN phase", () => {
    expect(gapAtDemoFrame(0)).toBeCloseTo(0, 2);
    expect(gapAtDemoFrame(OPEN_LEN)).toBeCloseTo(GAP_MAX, 2);
  });

  it("holds at GAP_MAX through the TRADE phase", () => {
    expect(gapAtDemoFrame(OPEN_LEN + Math.floor(TRADE_LEN / 2))).toBeCloseTo(GAP_MAX, 2);
  });

  it("closes toward ~0 by the end of the CONVERGE phase", () => {
    const endConverge = OPEN_LEN + TRADE_LEN + CONVERGE_LEN;
    expect(gapAtDemoFrame(endConverge)).toBeLessThan(0.08);
  });

  it("gap never exceeds GAP_WIDE and never goes negative", () => {
    for (let f = 0; f <= DISP_DEMO_LEN; f += 3) {
      const g = gapAtDemoFrame(f);
      expect(g).toBeGreaterThanOrEqual(0);
      expect(g).toBeLessThanOrEqual(GAP_WIDE + 1e-9);
    }
  });

  it("pnl is 0 before the trade, positive (~1) when the gap has closed", () => {
    expect(pnlAtDemoFrame(Math.floor(OPEN_LEN / 2))).toBe(0); // before trade placed
    const endConverge = OPEN_LEN + TRADE_LEN + CONVERGE_LEN;
    expect(pnlAtDemoFrame(endConverge)).toBeGreaterThan(0.85);
  });

  it("pnl goes negative during the CATCH widen, bounded at -0.5", () => {
    let sawNegative = false;
    let min = 1;
    for (let f = OPEN_LEN + TRADE_LEN + CONVERGE_LEN; f <= DISP_DEMO_LEN; f += 2) {
      const p = pnlAtDemoFrame(f);
      if (p < 0) sawNegative = true;
      min = Math.min(min, p);
    }
    expect(sawNegative).toBe(true);
    expect(min).toBeGreaterThanOrEqual(-0.5);
  });

  it("exposes 12 real ticker labels", () => {
    expect(BASKET_TICKERS).toHaveLength(12);
    expect(BASKET_TICKERS).toContain("NVDA");
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd halal-reels && npx vitest run src/dispersionData.test.ts`
Expected: FAIL — exports not defined.

- [ ] **Step 3: Implement** (append to `dispersionData.ts`)

```ts
// --- Demo schedule -----------------------------------------------------------
// Mirrors correlationData/CorrelationReel's HOLD/SWEEP model but expressed as
// four named phases. The gap is a scalar knob; pnl is derived from it relative
// to the entry gap (GAP_MAX). All demo-LOCAL frames (0 = first demo frame).

export const GAP_MAX = 0.42; // "normal" dispersion the trade is put on at
export const GAP_WIDE = 0.588; // 1.4x -- the CATCH over-shoot (drawdown)

export const OPEN_LEN = 150; // gap sweeps 0 -> GAP_MAX
export const TRADE_LEN = 150; // hold at GAP_MAX; BUY/SELL legs appear
export const CONVERGE_LEN = 170; // gap sweeps GAP_MAX -> ~0; PnL fills green
export const CATCH_LEN = 190; // fresh entry -> widen to GAP_WIDE -> back to ~0
export const DISP_DEMO_LEN = OPEN_LEN + TRADE_LEN + CONVERGE_LEN + CATCH_LEN; // 660

const OPEN_START = 0;
const TRADE_START = OPEN_LEN; // 150
const CONVERGE_START = OPEN_LEN + TRADE_LEN; // 300
const CATCH_START = CONVERGE_START + CONVERGE_LEN; // 470

export const DISP_WHOOSH_OFFSETS: number[] = [OPEN_START, TRADE_START, CONVERGE_START, CATCH_START];

// smootherstep(0..1) -- eased both ends, matches the reel's easeInOutCubic feel
// while staying a pure numeric function testable without Remotion's Easing.
const ease = (t: number): number => {
  const x = Math.max(0, Math.min(1, t));
  return x * x * x * (x * (x * 6 - 15) + 10);
};

/** Scalar gap over demo-local frame f. */
export const gapAtDemoFrame = (f: number): number => {
  if (f <= OPEN_START) return 0;
  if (f < TRADE_START) return GAP_MAX * ease((f - OPEN_START) / OPEN_LEN);
  if (f < CONVERGE_START) return GAP_MAX;
  if (f < CATCH_START) return GAP_MAX * (1 - ease((f - CONVERGE_START) / CONVERGE_LEN));
  // CATCH: 0 -> GAP_WIDE (first 45%), GAP_WIDE -> ~0 (rest).
  const t = (f - CATCH_START) / CATCH_LEN;
  if (t < 0.45) return GAP_WIDE * ease(t / 0.45);
  return GAP_WIDE * (1 - ease((t - 0.45) / 0.55));
};

/** PnL in [-0.5, 1]. Zero until the trade is placed (end of TRADE); then
 * (entry - gap)/entry, so it rises to +1 as the gap closes and dips negative
 * (amber) when the gap widens past entry during the CATCH. */
export const pnlAtDemoFrame = (f: number): number => {
  if (f < CONVERGE_START) return 0; // trade not on yet
  const entry = GAP_MAX;
  const raw = (entry - gapAtDemoFrame(f)) / entry;
  return Math.max(-0.5, Math.min(1, raw));
};

// Real AI-cluster constituents -- texture/labels only, NOT the gap source.
export const BASKET_TICKERS: string[] = [
  "ASML", "AMAT", "LRCX", "KLAC", "TSM", "MU",
  "NVDA", "AMD", "AVGO", "MRVL", "ARM", "CDNS",
];
```

- [ ] **Step 4: Run tests + typecheck**

Run: `cd halal-reels && npx vitest run src/dispersionData.test.ts && npx tsc --noEmit`
Expected: PASS (all tests) and no TS errors.

- [ ] **Step 5: Commit**

```bash
git add halal-reels/src/dispersionData.ts halal-reels/src/dispersionData.test.ts
git commit -m "feat(dispersion): gap/pnl demo schedule + basket tickers

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `GapChart` + `PnLMeter` primitives in `charts.tsx`

**Files:**
- Modify: `halal-reels/src/charts.tsx` (append two exports; reuse existing private `buildPoints`, `buildSmoothPath`, `idleWobble`)

**Interfaces:**
- Consumes: `buildPoints`, `buildSmoothPath` (already private in `charts.tsx`); `C`, `FONT`, `clamp`.
- Produces:
  - `GapChart({ indexData, basketData, reveal, liveFrame?, gapEmphasis?, width, height })` — draws INDEX (amber) + BASKET (mint) smooth lines and a mint→amber filled polygon between them (`[index path] + reversed [basket path]`), with `INDEX`/`BASKET` tip tags.
  - `PnLMeter({ value, width?, liveFrame?, label? })` — center-anchored horizontal bar; fills right emerald for `value>0`, left amber for `value<0`; mono readout `+PROFIT` / `−DRAWDOWN` / `FLAT`.

- [ ] **Step 1: Implement `GapChart`** (append to `charts.tsx`, after `DualLineChart`)

```tsx
/**
 * GapChart — two normalized lines (index above, basket below) with the area
 * between them filled (mint->amber gradient). The fill polygon is exactly the
 * index path followed by the reversed basket path, so it always hugs the drawn
 * curves. Reuses buildPoints/buildSmoothPath so the fill matches the lines.
 */
export const GapChart: React.FC<{
  indexData: number[];
  basketData: number[];
  reveal: number;
  width: number;
  height: number;
  gapEmphasis?: number; // 0..1 fill opacity
  liveFrame?: number;
}> = ({ indexData, basketData, reveal, width, height, gapEmphasis = 1, liveFrame }) => {
  const idxPts = buildPoints(indexData, width, height, reveal, liveFrame);
  const bktPts = buildPoints(basketData, width, height, reveal, liveFrame);
  if (idxPts.length < 2 || bktPts.length < 2) return null;

  const idxPath = buildSmoothPath(idxPts);
  const bktPath = buildSmoothPath(bktPts);
  // Fill polygon: index curve forward, basket curve back to start.
  const fillD =
    `${idxPath} L ${bktPts[bktPts.length - 1][0]},${bktPts[bktPts.length - 1][1]} ` +
    `${buildSmoothPath([...bktPts].reverse()).replace(/^M [^ ]+ /, "")} Z`;

  const [ilx, ily] = idxPts[idxPts.length - 1];
  const [blx, bly] = bktPts[bktPts.length - 1];

  const INDEX_COLOR = C.amber;
  const BASKET_COLOR = C.mint;

  return (
    <div style={{ position: "relative", width, height }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id="gap-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={INDEX_COLOR} stopOpacity={0.28 * gapEmphasis} />
            <stop offset="100%" stopColor={BASKET_COLOR} stopOpacity={0.28 * gapEmphasis} />
          </linearGradient>
          <filter id="gap-glow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation={8} result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1={0} x2={width} y1={height * f} y2={height * f} stroke={C.line} strokeWidth={1} />
        ))}

        <path d={fillD} fill="url(#gap-fill)" stroke="none" opacity={gapEmphasis} />
        <path d={bktPath} fill="none" stroke={BASKET_COLOR} strokeWidth={7} strokeLinecap="round" filter="url(#gap-glow)" />
        <path d={idxPath} fill="none" stroke={INDEX_COLOR} strokeWidth={7} strokeLinecap="round" filter="url(#gap-glow)" />
        <circle cx={ilx} cy={ily} r={10} fill={INDEX_COLOR} filter="url(#gap-glow)" />
        <circle cx={blx} cy={bly} r={10} fill={BASKET_COLOR} filter="url(#gap-glow)" />
      </svg>

      {[
        { x: ilx, y: ily, t: "INDEX", c: INDEX_COLOR, dy: -30 },
        { x: blx, y: bly, t: "BASKET", c: BASKET_COLOR, dy: 30 },
      ].map((tag) => (
        <div
          key={tag.t}
          style={{
            position: "absolute",
            left: Math.min(width - 10, tag.x + 16),
            top: Math.max(0, tag.y - 14 + tag.dy),
            fontFamily: FONT.mono,
            fontWeight: 800,
            fontSize: 26,
            letterSpacing: 1,
            color: tag.c,
            textShadow: "0 2px 10px rgba(0,0,0,.85)",
            whiteSpace: "nowrap",
          }}
        >
          {tag.t}
        </div>
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Implement `PnLMeter`** (append to `charts.tsx`)

```tsx
/**
 * PnLMeter — center-anchored horizontal bar. value in [-1,1]: fills RIGHT in
 * emerald for profit, LEFT in amber for drawdown (no red -- owner rule).
 * Abstract readout only; never a fabricated dollar figure.
 */
export const PnLMeter: React.FC<{
  value: number; // -1..1
  width?: number;
  liveFrame?: number;
  label?: string;
}> = ({ value, width = 760, liveFrame, label = "TRADE PnL" }) => {
  const v = Math.max(-1, Math.min(1, value));
  const h = 40;
  const half = width / 2;
  const pulse = liveFrame !== undefined ? 1 + 0.06 * Math.sin(liveFrame * 0.08) : 1;
  const pos = v >= 0;
  const fillColor = pos ? C.emerald : C.amber;
  const readout = v > 0.02 ? "+PROFIT" : v < -0.02 ? "−DRAWDOWN" : "FLAT";

  return (
    <div style={{ width, fontFamily: FONT.mono }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
        <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: 2, color: C.muted }}>{label}</span>
        <span style={{ fontSize: 26, fontWeight: 800, color: fillColor }}>{readout}</span>
      </div>
      <div style={{ position: "relative", height: h, background: C.panel, borderRadius: 10, border: `1.5px solid ${C.line}` }}>
        {/* center zero line */}
        <div style={{ position: "absolute", left: half - 1, top: -6, bottom: -6, width: 2, background: C.muted, opacity: 0.6 }} />
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: pos ? half : half - Math.abs(v) * half,
            width: Math.abs(v) * half,
            background: fillColor,
            borderRadius: 8,
            opacity: 0.9 * pulse,
            boxShadow: `0 0 ${18 * pulse}px ${fillColor}`,
          }}
        />
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Typecheck**

Run: `cd halal-reels && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Visual smoke — render one still of each primitive**

Create a throwaway composition is unnecessary; instead verify in Task 4's render. For now confirm the fill-path helper produces valid SVG by a node assertion:

Run: `cd halal-reels && node -e "const s='M 0,0 C 1,1 2,2 3,3'; console.log(s.replace(/^M [^ ]+ /,''))"`
Expected: prints `C 1,1 2,2 3,3` (confirms the reversed-path concat trims the leading M correctly).

- [ ] **Step 5: Commit**

```bash
git add halal-reels/src/charts.tsx
git commit -m "feat(dispersion): GapChart + PnLMeter chart primitives

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `DispersionReel.tsx` composition

**Files:**
- Create: `halal-reels/src/DispersionReel.tsx`

**Interfaces:**
- Consumes: `GapChart`, `PnLMeter` (Task 3); `gapAtDemoFrame`, `pnlAtDemoFrame`, `indexAt`, `basketAt`, `DISP_DEMO_LEN`, `DISP_WHOOSH_OFFSETS`, `OPEN_LEN`, `TRADE_LEN`, `CONVERGE_LEN`, `GAP_MAX`, `DISP_DATE` (Tasks 1–2); `Bg`, `Foot`, `Kicker`, `Slam`, `clamp`, `easeOut`, `pop` (`ui.tsx`); `C`, `FONT` (`theme.ts`).
- Produces: `DispersionReel: React.FC<{ mini?: boolean }>`, `DISPERSION_BEATS` (`{title,define,demo,close,total}`), `DISPERSION_MINI_TOTAL: number`.

**Pattern to mirror:** `CorrelationReel.tsx` — copy its beat-offset scaffolding, audio bed (`quiz/music.mp3` + per-cue `quiz/reveal.mp3` ducking), `RailFoot`, `MiniIllustrativeBadge`, and `mini` hook structure verbatim, swapping the synced-demo body for the gap demo below. Reuse these constants from it: `TITLE_LEN=90`, `DEFINE_LEN=150`, `CLOSE_LEN=210`, `MINI_HOOK_LEN=80`.

- [ ] **Step 1: Create the composition**

Create `halal-reels/src/DispersionReel.tsx`:

```tsx
import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, FONT } from "./theme";
import { Bg, Foot, Kicker, Slam, clamp, easeOut, pop } from "./ui";
import { GapChart, PnLMeter } from "./charts";
import {
  DISP_DATE,
  DISP_DEMO_LEN,
  DISP_WHOOSH_OFFSETS,
  OPEN_LEN,
  TRADE_LEN,
  CONVERGE_LEN,
  GAP_MAX,
  gapAtDemoFrame,
  pnlAtDemoFrame,
  indexAt,
  basketAt,
} from "./dispersionData";

const TITLE_LEN = 90;
const DEFINE_LEN = 150;
const DEMO_LEN = DISP_DEMO_LEN; // 660
const CLOSE_LEN = 210;
const MINI_HOOK_LEN = 80;
const PAD = 84;

export const DISPERSION_BEATS = {
  title: TITLE_LEN,
  define: DEFINE_LEN,
  demo: DEMO_LEN,
  close: CLOSE_LEN,
  total: TITLE_LEN + DEFINE_LEN + DEMO_LEN + CLOSE_LEN,
};
export const DISPERSION_MINI_TOTAL = MINI_HOOK_LEN + DEMO_LEN + CLOSE_LEN;

const TITLE_START = 0;
const DEFINE_START = TITLE_START + TITLE_LEN;
const DEMO_START = DEFINE_START + DEFINE_LEN;
const CLOSE_START = DEMO_START + DEMO_LEN;

const DISP_RAIL =
  "Cash index-arbitrage is an advanced institutional strategy, shown for education — not a recommendation. Illustrative mechanic, not live prices. Educational — not financial advice.";

// Phase boundaries (demo-local) for captions + leg badges.
const TRADE_START_L = OPEN_LEN;
const CONVERGE_START_L = OPEN_LEN + TRADE_LEN;
const CATCH_START_L = CONVERGE_START_L + CONVERGE_LEN;

const CAPTION_FADE = 14;
const fadeInOut = (local: number, len: number) =>
  interpolate(local, [0, CAPTION_FADE, len - CAPTION_FADE, len], [0, 1, 1, 0], clamp);

const captionAt = (f: number): { text: string; opacity: number } => {
  if (f < TRADE_START_L) return { text: "In real markets, the two prices drift apart.", opacity: fadeInOut(f, OPEN_LEN) };
  if (f < CONVERGE_START_L) return { text: "Buy the cheap side. Sell the rich side.", opacity: fadeInOut(f - TRADE_START_L, TRADE_LEN) };
  if (f < CATCH_START_L) return { text: "Market up or down — you only need the gap to close.", opacity: fadeInOut(f - CONVERGE_START_L, CONVERGE_LEN) };
  return { text: "It can widen before it closes. That's the risk.", opacity: fadeInOut(f - CATCH_START_L, DEMO_LEN - CATCH_START_L) };
};

// --- audio bed (mirror CorrelationReel) --------------------------------------
const MUSIC_VOL = 0.3, MUSIC_DUCK_VOL = 0.1, MUSIC_DUCK_LEN = 26;
const duckAt = (frame: number, center: number): number | null => {
  const rel = frame - center;
  if (rel >= 0 && rel < MUSIC_DUCK_LEN)
    return interpolate(rel, [0, 5, MUSIC_DUCK_LEN - 5, MUSIC_DUCK_LEN], [MUSIC_VOL, MUSIC_DUCK_VOL, MUSIC_DUCK_VOL, MUSIC_VOL], clamp);
  return null;
};
const musicVolumeFor = (whooshFrames: number[]) => (frame: number) => {
  for (const c of whooshFrames) { const v = duckAt(frame, c); if (v !== null) return v; }
  return MUSIC_VOL;
};

const RailFoot: React.FC = () => (
  <div style={{ position: "absolute", bottom: 40, left: PAD, right: PAD, textAlign: "center" }}>
    <Foot text={DISP_RAIL} />
  </div>
);

const IllustrativeBadge: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: easeOut });
  return (
    <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 18, letterSpacing: 2, color: C.inkSoft, background: C.panel, border: `1px dashed ${C.muted}`, padding: "6px 12px", borderRadius: 8, opacity: p, whiteSpace: "nowrap" }}>
      ILLUSTRATIVE
    </div>
  );
};

const LegBadges: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div style={{ display: "flex", gap: 16, opacity }}>
    <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 26, color: C.mint, background: C.panel, border: `1.5px solid ${C.mint}55`, padding: "12px 20px", borderRadius: 12 }}>▲ BUY the cheap side</div>
    <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 26, color: C.amber, background: C.panel, border: `1.5px solid ${C.amber}55`, padding: "12px 20px", borderRadius: 12 }}>▼ SELL the rich side</div>
  </div>
);

const TitleScene: React.FC = () => (
  <AbsoluteFill style={{ padding: PAD, justifyContent: "center", alignItems: "center", gap: 24, textAlign: "center" }}>
    <Kicker text="TODAY'S CHART LESSON" color={C.amber} />
    <Slam size={124} delay={8}>DISPERSION</Slam>
  </AbsoluteFill>
);

const DefineScene: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [10, 60], [0, 1], { ...clamp, easing: easeOut });
  return (
    <AbsoluteFill style={{ padding: PAD, justifyContent: "center", alignItems: "center", gap: 30, textAlign: "center" }}>
      <Kicker text="ONE THING, TWO PRICES" color={C.amber} />
      <Slam size={60} delay={6}>An index is just its stocks, added up.</Slam>
      <div style={{ display: "flex", justifyContent: "center", marginTop: 8 }}>
        <GapChart indexData={indexAt(0.02)} basketData={basketAt(0.02)} reveal={reveal} width={860} height={360} gapEmphasis={0.4} liveFrame={frame} />
      </div>
    </AbsoluteFill>
  );
};

const MiniHookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const inP = interpolate(frame, [0, 12], [0, 1], { ...clamp, easing: pop });
  return (
    <AbsoluteFill style={{ padding: PAD, justifyContent: "center", alignItems: "center", textAlign: "center" }}>
      <div style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 96, lineHeight: 1.05, letterSpacing: -3, color: C.ink, opacity: inP, scale: String(0.8 + 0.2 * inP), textShadow: "0 8px 44px rgba(0,0,0,.6)" }}>
        Two prices.<br />One basket.<br /><span style={{ color: C.amber }}>Wall Street's oldest trade.</span>
      </div>
    </AbsoluteFill>
  );
};

const DemoScene: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [0, 20], [0, 1], { ...clamp, easing: easeOut });
  const gap = gapAtDemoFrame(frame);
  const pnl = pnlAtDemoFrame(frame);
  const caption = captionAt(frame);
  const legOpacity = interpolate(frame, [TRADE_START_L, TRADE_START_L + 16], [0, 1], clamp);
  const parallaxY = 5 * Math.sin(frame * 0.019 + 1.2);

  return (
    <AbsoluteFill style={{ padding: `${PAD}px ${PAD}px 172px`, display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <Kicker text="THE GAP" color={C.amber} />
        <IllustrativeBadge />
      </div>
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", transform: `translateY(${parallaxY}px)` }}>
        <GapChart indexData={indexAt(gap)} basketData={basketAt(gap)} reveal={reveal} width={900} height={420} gapEmphasis={interpolate(gap, [0, GAP_MAX], [0.2, 1], clamp)} liveFrame={frame} />
      </div>
      <div style={{ display: "flex", justifyContent: "center", minHeight: 68 }}><LegBadges opacity={legOpacity} /></div>
      <div style={{ display: "flex", justifyContent: "center" }}><PnLMeter value={pnl} width={820} liveFrame={frame} /></div>
      <div style={{ minHeight: 72, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ fontFamily: FONT.body, fontWeight: 500, fontSize: 42, lineHeight: 1.3, color: C.inkSoft, opacity: caption.opacity, textAlign: "center", textShadow: "0 2px 18px rgba(0,0,0,.8)" }}>{caption.text}</div>
      </div>
    </AbsoluteFill>
  );
};

const CloseScene: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 18], [0, 1], { ...clamp, easing: easeOut });
  const ctaP = interpolate(frame, [110, 130], [0, 1], { ...clamp, easing: pop });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 30, padding: 90 }}>
      <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 32, letterSpacing: 3, color: C.bg, background: C.amber, padding: "16px 30px", borderRadius: 16, opacity: p, scale: String(0.8 + 0.2 * p) }}>MIND THE GAP</div>
      <div style={{ textAlign: "center", maxWidth: 900, opacity: p }}>
        <Slam size={54} color={C.amber} delay={10}>Buy the cheap side, sell the rich side —</Slam>
        <Slam size={54} color={C.amber} delay={22}>you profit when the gap closes.</Slam>
      </div>
      <div style={{ fontFamily: FONT.body, fontWeight: 600, fontSize: 32, color: C.amber, opacity: ctaP, textAlign: "center", maxWidth: 820, translate: `0px ${(1 - ctaP) * 16}px` }}>
        Comment GAP and I&apos;ll DM you how the pros track it 📲
      </div>
      <div style={{ fontFamily: FONT.mono, fontSize: 22, color: C.muted, opacity: p }}>illustrative example · {DISP_DATE}</div>
      <div style={{ position: "absolute", bottom: 60, left: 90, right: 90, textAlign: "center" }}><Foot text={DISP_RAIL} /></div>
    </AbsoluteFill>
  );
};

export const DispersionReel: React.FC<{ mini?: boolean }> = ({ mini = false }) => {
  const demoStart = mini ? MINI_HOOK_LEN : DEMO_START;
  const closeStart = mini ? MINI_HOOK_LEN + DEMO_LEN : CLOSE_START;
  const whooshFrames = DISP_WHOOSH_OFFSETS.map((o) => demoStart + o);
  const musicVolume = musicVolumeFor(whooshFrames);

  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      <Audio src={staticFile("quiz/music.mp3")} volume={musicVolume} />
      {whooshFrames.map((f, i) => (
        <Sequence key={f} from={f} durationInFrames={40} name={`Whoosh${i}`}>
          <Audio src={staticFile("quiz/reveal.mp3")} volume={0.5} />
        </Sequence>
      ))}

      {!mini && (
        <Sequence from={TITLE_START} durationInFrames={TITLE_LEN} name="Title">
          <Bg tint={C.amber} /><TitleScene /><RailFoot />
        </Sequence>
      )}
      {!mini && (
        <Sequence from={DEFINE_START} durationInFrames={DEFINE_LEN} name="Define">
          <Bg tint={C.amber} /><DefineScene /><RailFoot />
        </Sequence>
      )}
      {mini && (
        <Sequence from={0} durationInFrames={MINI_HOOK_LEN} name="MiniHook">
          <Bg tint={C.amber} /><MiniHookScene /><RailFoot />
        </Sequence>
      )}

      <Sequence from={demoStart} durationInFrames={DEMO_LEN} name="Demo">
        <Bg tint={C.amber} driftSpeed={1.7} /><DemoScene /><RailFoot />
      </Sequence>
      <Sequence from={closeStart} durationInFrames={CLOSE_LEN} name="Close">
        <Bg tint={C.amber} /><CloseScene />
      </Sequence>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Typecheck**

Run: `cd halal-reels && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add halal-reels/src/DispersionReel.tsx
git commit -m "feat(dispersion): DispersionReel composition (full + mini)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Register compositions, render, visually verify, caption

**Files:**
- Modify: `halal-reels/src/Root.tsx`
- Create: `higgs/dispersion_caption.txt`

**Interfaces:**
- Consumes: `DispersionReel`, `DISPERSION_BEATS`, `DISPERSION_MINI_TOTAL` (Task 4).

- [ ] **Step 1: Register two compositions** in `halal-reels/src/Root.tsx`

Add the import after the CorrelationReel import:
```tsx
import { DispersionReel, DISPERSION_BEATS, DISPERSION_MINI_TOTAL } from "./DispersionReel";
```
Add inside the fragment, after the `CorrelationReelMini` composition:
```tsx
      <Composition id="DispersionReel" component={DispersionReel} durationInFrames={DISPERSION_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="DispersionReelMini" component={DispersionReel} durationInFrames={DISPERSION_MINI_TOTAL} fps={FPS} width={W} height={H} defaultProps={{ mini: true }} />
```

- [ ] **Step 2: Confirm compositions register + typecheck**

Run: `cd halal-reels && npx tsc --noEmit && npx remotion compositions`
Expected: no TS errors; list includes `DispersionReel` and `DispersionReelMini`.

- [ ] **Step 3: Render still frames spanning the 4 demo phases (visual verification)**

The full-reel demo starts at frame 240. Phase mid-points ≈ TITLE/DEFINE(120), open(315), trade(390), converge(560), catch(730), close(1080). Render them:
```bash
cd halal-reels
for f in 45 120 315 390 560 730 1080; do npx remotion still DispersionReel "out/disp_$f.png" --frame=$f; done
```
Expected: 7 PNGs. **Read each** and confirm (verification-before-completion — show the frames, don't assert):
- 315: gap open, INDEX(amber) above BASKET(mint), fill visible, PnL flat.
- 390: gap held wide, both leg badges visible, PnL flat.
- 560: gap nearly closed, PnLMeter filled emerald (+PROFIT).
- 730: gap widened again, PnLMeter amber (−DRAWDOWN).
- All: `ILLUSTRATIVE` badge + rail present; NO red anywhere; text legible.

- [ ] **Step 4: Render both MP4s**

```bash
cd halal-reels
npx remotion render DispersionReel ../higgs/dispersion_reel.mp4
npx remotion render DispersionReelMini ../higgs/dispersion_reel_mini.mp4
```
Expected: two MP4s in `higgs/`. (Gitignored — do not `git add` them.)

- [ ] **Step 5: Write the IG caption**

Create `higgs/dispersion_caption.txt` (rails-compliant, keyword GAP):
```
Wall Street's oldest trade, explained in 45 seconds. 📉📈

An index is just its stocks added up — so the index and its basket "should" be worth the exact same thing. In real markets they drift apart, and a gap opens.

The trade: buy the cheap side, sell the rich side. You're long one, short the other — so it doesn't matter if the market goes up or down. You profit when the gap closes.

The catch: the gap can widen before it converges, borrow and fees eat thin margins, and in a panic it can stay open. That's why it's an advanced, institutional strategy — not a retail button.

This is an illustrated explainer of how cash index-arbitrage works — not a recommendation, not live prices, and nothing here is a signal to buy or sell. Educational research only — not financial advice.

Comment "GAP" and I'll DM you how the pros track it 📲

#investing #stockmarket #indexfunds #arbitrage #quant #fintok #financetok #tradingstrategies #ETF #marketstructure
```

- [ ] **Step 6: Commit (sources + caption only; MP4s stay gitignored)**

```bash
git add halal-reels/src/Root.tsx higgs/dispersion_caption.txt
git commit -m "feat(dispersion): register compositions + IG caption; render reel + mini

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

1. **Spec coverage:** cash trade taught → Tasks 1–2 (gap/pnl) + Task 4 (legs/captions/close); GapChart+PnLMeter → Task 3; reel spine reuse + mini + audio → Task 4; register+render+verify+caption → Task 5; rails/ILLUSTRATIVE/no-red/no-fabricated-figure → Global Constraints + enforced in Tasks 3–5; Grok backgrounds → deferred wiring (non-blocking; `Bg` fallback), noted below.
2. **Placeholder scan:** none — full code in every code step; render/verify commands exact.
3. **Type consistency:** `gapAtDemoFrame`/`pnlAtDemoFrame` signatures identical across Tasks 2/4; `GapChart`/`PnLMeter` prop names identical Tasks 3/4; `indexAt`/`basketAt` return `number[]` consumed as `indexData`/`basketData`; `DISP_DEMO_LEN`=`DEMO_LEN` used consistently.
4. **Scope:** one reel + mini, one data module, two primitives, one registration — single plan.

## Deferred (non-blocking): hero backgrounds

When the 3 Grok images land in `higgs/` (`disp_scatter`, `disp_converge`, `disp_terminal`), a follow-up wires them behind TITLE/DEFINE, DEMO(converge), and CLOSE respectively as dimmed full-bleed backdrops (same treatment as the daily-screen heroes: `<Img>` under a dark scrim, chart stays legible). Until then the reel renders on the `Bg` gradient — fully functional, just less cinematic.
