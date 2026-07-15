
# DCF Desk — Round 7 Design Spec (2-stage FCF DCF, client-side, pure)

## 0. Data-reality check (read before building)

Read `web/lib/data.ts`, `web/lib/macro.ts`, `web/lib/risk.ts`, `web/lib/archetypes.ts`, and confirmed against the live sandbox fixture (`web/public/data/site.json`, 535KB, `stocks: {}` / `screener: []` empty in this fixture — capital_web/edges only — so this design is schema-driven off the **TypeScript `Stock`/`Fundamentals`/`Valuation` interfaces**, not fixture values):

- `Stock.valuation: Valuation` → `price: number|null`, `pe: number|null`, plus fundamental-value fields. **No `market_cap`, no `shares_outstanding` anywhere on `Stock`.** Confirmed via `grep -n "market_cap\|shares" web/lib/data.ts` — zero hits in the `Stock`/`Fundamentals`/`Valuation`/`ScreenerRow` interfaces.
- `Stock.fundamentals: Fundamentals` → `gross_margin, operating_margin, net_margin, fcf_margin, roe, roa, roic, debt_to_equity, current_ratio, ps, pb, pfcf, rev_growth_yoy, eps_growth_yoy, sector, industry` — all `number|null`.
- `market_cap` **does** exist, but only on `RiskStock` in `web/lib/risk.ts` (a separate, `existsSync`-gated desk file, `risk.json`, not guaranteed present/joined). Per house rule (existsSync degradation) I do **not** make the DCF's core derivation depend on a second optional file — `risk.json` presence would silently change what "fair value" means depending on which JSON happened to exist that day. DCF stays `site.json`-only for its default derivation.
- `web/lib/macro.ts` → `getMacroSeries("DGS10")?.last` gives the 10Y Treasury yield **as a percent number** (e.g. `4.474` meaning 4.474%), confirmed against the fixture `macro.json`. `getMacroData()` returns `null` when `macro.json` is absent (existsSync-guarded, never throws) — mirrored by the DCF discount-rate fallback.
- `references/investing-brief.md` §6: *"Distinguish profitable from pre-revenue. DCF/GF Value/P/E are meaningful for [profitable names]…"* — reinforced by rule 1 here: base FCF must come from real fundamentals ratios, and the model must degrade to `null`/a labeled "not evaluable" state for names where those ratios don't exist, never fabricate.

### The key design decision: per-share is achievable WITHOUT shares outstanding

The task brief anticipated needing `market_cap / pfcf` (aggregate FCF) then dividing by shares — but `Stock` has neither field, so that path is a dead end. Instead:

`Fundamentals.pfcf` (Price/FCF) and `Fundamentals.ps` (Price/Sales) are **scale-invariant ratios** — `pfcf = market_cap / FCF_aggregate = price / FCF_per_share` (the share count cancels algebraically). So:

```
FCF_per_share = price / pfcf              (exact, no shares needed)
```

is a legitimate, non-fabricated per-share figure derived from two real fields (`valuation.price`, `fundamentals.pfcf`). Same logic gives a fallback via `ps` + `fcf_margin`:

```
revenue_per_share = price / ps
FCF_per_share_proxy = revenue_per_share × fcf_margin
```

**Resolution of the brief's conditional ("if site.json lacks shares/market_cap fields, output fair-value-vs-market-cap ratio instead of per-share")**: I checked the actual fields (§0 above) — `market_cap`/`shares` are genuinely absent, **but** a mathematically sound per-share path exists via ratio algebra above, using fields that *are* present. A "ratio-to-market-cap" fallback would itself need `market_cap`, which doesn't exist either — so it isn't buildable and wouldn't be more honest than the per-share path. I therefore emit **per-share fair value everywhere it's derivable**, and fall back to `null` (with a machine-readable reason string, never a fabricated ratio) only when even `price` is missing or both ratio pairs are unusable. This is directly comparable to `valuation.price`, which is what a sliders-and-upside% panel needs anyway.

---

## 1. Formulas (2-stage FCF DCF, explicit discounting sums)

**Stage 1 — 5 explicit forecast years, growth fading linearly from `g1` to terminal growth `gT`:**

```
g_t = g1 - (g1 - gT) · (t-1)/4,   t = 1..5        // g_1 = g1, g_5 = gT exactly

FCF_t = FCF_0 · Π_{k=1}^{t} (1 + g_k),   t = 1..5   // FCF_0 = base FCF/share

PV_t = FCF_t / (1 + r)^t
```

**Stage 2 — Gordon-growth terminal value at the end of year 5** (FCF_5 already growing at `gT`, so the year-6 cash flow continues cleanly at the terminal rate):

```
TV_5 = FCF_5 · (1 + gT) / (r - gT)          // requires r > gT, else model is INVALID
PV(TV) = TV_5 / (1 + r)^5
```

**Fair value per share — full expanded sum:**

```
FairValue = Σ_{t=1}^{5} [ FCF_0 · Π_{k=1}^{t}(1+g_k) ] / (1+r)^t
          + [ FCF_0 · Π_{k=1}^{5}(1+g_k) · (1+gT) ] / [ (r - gT) · (1+r)^5 ]
```

**Upside/(discount) vs current price:**

```
UpsidePct = (FairValue - Price) / Price × 100
```

**Invalidity guard:** if `r ≤ gT`, the Gordon-growth denominator is zero/negative → `TV_5` blows up or goes negative. The model must return `{ valid: false, error: "discount rate must exceed terminal growth" }` and render nothing numeric — never a huge/garbage fair value. UI must clamp the discount-rate slider's minimum to `gT + 0.5pp` to make this practically unreachable, but the pure function still must guard it directly (defense in depth — sliders aren't the only caller, capture-card defaults are too).

---

## 2. Default-input derivation table

| Input | Primary source (site.json field) | Fallback | Final fallback | Never-fake rule |
|---|---|---|---|---|
| **Base FCF/share** (`FCF_0`) | `valuation.price / fundamentals.pfcf`, requires `price != null`, `pfcf != null`, `pfcf > 0` | `(valuation.price / fundamentals.ps) × fundamentals.fcf_margin`, requires `price != null`, `ps != null`, `ps > 0`, `fcf_margin != null` (may be negative — real loss-making FCF is meaningful, not rejected) | `null`, `basis: "none"`, `reason` set (e.g. `"no price"`, `"pfcf and ps both unusable"`) | Reject `pfcf ≤ 0` / `ps ≤ 0` (nonsensical ratio) rather than dividing through it |
| **Growth Y1** (`g1`) | `fundamentals.rev_growth_yoy`, clamped to `[GROWTH_FLOOR = -0.15, GROWTH_CAP = 0.35]` | `GROWTH_DEFAULT = 0.08` (8%) when `rev_growth_yoy == null` — a documented **methodology parameter**, not a claim about the company; `growthSource: "default"` is surfaced in the UI so it's never silently mistaken for real data | — | Clamp, don't discard — extreme reported growth (e.g. +90% YoY off a tiny base) is real data, just not extrapolable 5 years; cap communicates that without hiding the number (raw value still shown alongside) |
| **Terminal growth** (`gT`) | Fixed constant `TERMINAL_GROWTH_DEFAULT = 0.025` (2.5%, ≈ long-run nominal GDP proxy) | — | — | User-adjustable via slider; UI enforces `gT < r` |
| **Discount rate** (`r`) | `getMacroSeries("DGS10")?.last / 100 + EQUITY_RISK_PREMIUM (0.045)` when `macro.json` present and `DGS10` resolvable | — | `FLAT_DISCOUNT_FALLBACK = 0.095` (9.5%) when `macro.json` absent/unparseable or `DGS10` missing — mirrors `getMacroData()`'s own `existsSync`/try-catch/never-throws contract | `discountSource: "macro_dgs10" \| "flat_fallback"` surfaced in output so the UI can label which one was used |
| **Per-share vs. ratio output** | Per-share whenever `FCF_0` is derivable (see row 1) | — | `null` fair value, `basis: "none"` (no market-cap-ratio mode — see §0, that field doesn't exist to fall back to) | Documented explicitly as the resolved design decision, not left implicit |
| **Horizon** | Fixed `years = 5` | — | — | Not user-adjustable (keeps the sensitivity grid and capture card layout stable) |

Worked numeric example of the discount-rate default using the fixture `macro.json` (`DGS10.last = 4.474`): `r_default = 4.474/100 + 0.045 = 0.08974` → **8.974% ≈ 8.97%**.

---

## 3. `web/lib/dcf.ts` — pure functions and types

```ts
// web/lib/dcf.ts
// Pure, client-safe 2-stage FCF DCF. No I/O. Every function here is a plain
// function of its arguments — safe to call on every slider tick in a "use
// client" component, and reusable server-side for the capture card's fixed
// defaults. TOY MODEL: educational, not a price target. See CLAUDE.md rule 1
// (stamp everything) — callers stamp retrieved_at/as_of from the Stock they
// pulled these inputs from; this module does no stamping itself (pure math).

import type { Stock } from "@/lib/data";
import type { MacroData } from "@/lib/macro";

// ---- Constants (methodology parameters, not fabricated facts) ----
export const GROWTH_FLOOR = -0.15;
export const GROWTH_CAP = 0.35;
export const GROWTH_DEFAULT = 0.08;
export const TERMINAL_GROWTH_DEFAULT = 0.025;
export const EQUITY_RISK_PREMIUM = 0.045;
export const FLAT_DISCOUNT_FALLBACK = 0.095;
export const DCF_YEARS = 5;

export type DcfBasis = "pfcf" | "ps_margin" | "none";
export type GrowthSource = "actual" | "default";
export type DiscountSource = "macro_dgs10" | "flat_fallback";

export interface DcfBaseFcf {
  value: number | null;   // FCF per share, same unit as valuation.price; null = never faked
  basis: DcfBasis;
  reason: string | null;  // set iff value === null
}

// price/pfcf primary, price/ps*fcf_margin fallback, null (never-fake) last resort.
export function deriveBaseFcfPerShare(
  stock: Pick<Stock, "valuation" | "fundamentals">
): DcfBaseFcf;

export function deriveDefaultGrowth(
  stock: Pick<Stock, "fundamentals">
): { rate: number; raw: number | null; source: GrowthSource };

// macro=null (getMacroData() absent) OR DGS10 unresolvable -> flat fallback.
export function deriveDefaultDiscountRate(
  macro: MacroData | null
): { rate: number; source: DiscountSource; dgs10: number | null };

export interface DcfDefaultInputs {
  baseFcf: DcfBaseFcf;
  growth: { rate: number; raw: number | null; source: GrowthSource };
  terminalGrowth: number;                 // TERMINAL_GROWTH_DEFAULT
  discount: { rate: number; source: DiscountSource; dgs10: number | null };
  years: number;                          // DCF_YEARS
  currentPrice: number | null;
}

// Composes the three derive* functions above into one default bundle —
// what DcfPanel seeds its sliders with, and what the capture card renders
// verbatim (no sliders on the card).
export function buildDefaultDcfInputs(
  stock: Pick<Stock, "valuation" | "fundamentals">,
  macro: MacroData | null
): DcfDefaultInputs;

export interface DcfYearRow {
  year: number;            // 1..5
  growth: number;          // g_t, decimal
  fcf: number;              // FCF_t, absolute per-share
  discountFactor: number;   // 1/(1+r)^t
  pv: number;                // PV_t
}

export interface DcfRunParams {
  baseFcfPerShare: number;
  growthY1: number;
  terminalGrowth: number;
  discountRate: number;
  years?: number;           // default DCF_YEARS; exposed for testing, not UI
}

export interface DcfResult {
  inputs: Required<DcfRunParams>;
  rows: DcfYearRow[];
  sumPvStage1: number;
  terminalValue: number;      // undiscounted TV at year 5
  pvTerminalValue: number;
  fairValuePerShare: number | null;   // null iff !valid
  valid: boolean;               // false iff discountRate <= terminalGrowth
  error: string | null;         // "discount rate must exceed terminal growth" when !valid
}

// The core pure DCF engine — formulas in §1. Guards r<=gT internally
// (defense in depth even though the UI also clamps sliders).
export function runDcf(params: DcfRunParams): DcfResult;

// Adds price-comparison fields on top of runDcf() — the shape DcfPanel
// actually renders.
export interface DcfResultWithUpside extends DcfResult {
  currentPrice: number | null;
  upsidePct: number | null;   // (fair - price)/price * 100, null if no price or !valid
}

export function runDcfWithUpside(
  params: DcfRunParams,
  currentPrice: number | null
): DcfResultWithUpside;

export interface SensitivityCell {
  discountDelta: number;   // -0.01 | 0 | 0.01
  growthDelta: number;     // -0.02 | 0 | 0.02
  discountRate: number;
  growthY1: number;
  fairValuePerShare: number | null;
  valid: boolean;
}

// 3x3 grid: discount ±1pt (rows) x growth ±2pt (columns), base case center.
// Pure — recomputes runDcf() 9x, cheap enough for every slider tick.
export function sensitivityGrid(
  params: DcfRunParams,
  discountDeltas?: number[],   // default [-0.01, 0, 0.01]
  growthDeltas?: number[]      // default [-0.02, 0, 0.02]
): SensitivityCell[][];        // outer = discountDeltas, inner = growthDeltas
```

---

## 4. Component / file inventory

| File | Kind | Purpose |
|---|---|---|
| `web/lib/dcf.ts` | pure lib | All math above; zero I/O, zero React import |
| `web/lib/dcf.test.ts` | vitest | Fixtures below, `toBeCloseTo` tolerances (float arithmetic) |
| `web/components/terminal/DcfPanel.tsx` | `"use client"` | Sliders for `g1`, `r`, `gT` seeded from `buildDefaultDcfInputs()`; live-recomputes `runDcfWithUpside()` + `sensitivityGrid()` on every change (mirrors `StressControls.tsx`'s controlled-value pattern — `useState<DcfRunParams>` initialized once from server-computed defaults passed as props, `<input type="range">` for each knob, a "Reset to defaults" button). Renders: 5-year cash-flow table, fair value vs. price, 3×3 sensitivity grid, basis/source disclosure line (which fallback fired), and the **"TOY MODEL — educational, not a price target"** banner (always visible, not gated behind interaction). Rendered on `/stocks/[symbol]/page.tsx` next to `ArchetypePanel`, with its own "Capture card →" link to `/terminal/card/dcf/[symbol]`. |
| `web/components/terminal/DcfCaptureCard.tsx` | server component | 1080×1350 capture-card slide, same construction discipline as `ArchetypeCaptureCard.tsx` (`#capture-canvas`, `data-capture-ready="true"`, all-px sizing, no client JS). Renders `runDcfWithUpside(buildDefaultDcfInputs(stock, macro), price)` **at pure defaults only — no sliders, no user state** (task constraint). Shows: symbol, fair value/share, current price, upside/discount %, basis used, discount-rate source, `generated_at`/`as_of` stamp, and the mandatory NFA footer line (same footer pattern as `ArchetypeCaptureCard.tsx`'s "Educational research only — not financial advice. NFA."). |
| `web/app/terminal/card/dcf/[symbol]/page.tsx` | route | Mirrors `app/terminal/card/archetype/[symbol]/page.tsx` exactly: `export const dynamic = "force-dynamic"`, `normalizeSymbol()`, `notFound()` when the stock (or its `baseFcf`) can't be resolved, `?capture=1` → bare `DcfCaptureCard` + `CaptureChromeStrip`; otherwise → `CardScaleShell`-wrapped preview. Gated automatically via `web/proxy.ts`'s existing `/terminal/*` `TERMINAL_KEY` cookie check — no new gating code needed. |
| `web/app/stocks/[symbol]/page.tsx` | edit | Import `getMacroData` (already exported by `lib/macro.ts`), compute `buildDefaultDcfInputs(s, getMacroData())` server-side, pass as props into `<DcfPanel defaults={...} symbol={s.symbol} price={v.price} />` near the existing `<ArchetypePanel record={archetype} />` render. |

No new Python pipeline step, no new gitignored bundle — `dcf.ts` computes entirely from `site.json` (already loaded server-side by `getSiteData()`) + `macro.json` (already loaded by `getMacroData()`), both existing artifacts.

---

## 5. Vitest case list (`web/lib/dcf.test.ts`) — hand-computed expected values

Arithmetic verified with a short Python script implementing the exact §1 formulas (linear fade `g_t = g1-(g1-gT)(t-1)/4`, `PV_t=FCF_t/(1+r)^t`, Gordon `TV=FCF_5(1+gT)/(r-gT)`); shown to 4-6dp, test with `toBeCloseTo(expected, 3)` or looser given compounding.

1. **`deriveBaseFcfPerShare` — pfcf basis (primary)**
   `{ valuation: { price: 100 }, fundamentals: { pfcf: 20, ps: null, fcf_margin: null } }` → `{ value: 5, basis: "pfcf", reason: null }` (100/20 = 5 exact)

2. **`deriveBaseFcfPerShare` — pfcf rejected (≤0), falls to ps/fcf_margin**
   `{ valuation: { price: 50 }, fundamentals: { pfcf: -3, ps: 5, fcf_margin: 0.15 } }` → `{ value: 1.5, basis: "ps_margin", reason: null }` ((50/5)×0.15 = 1.5 exact)

3. **`deriveBaseFcfPerShare` — everything unusable → null, never faked**
   `{ valuation: { price: null }, fundamentals: { pfcf: 20, ps: 5, fcf_margin: 0.15 } }` → `{ value: null, basis: "none", reason: "no price" }` (price missing invalidates both paths)

4. **`deriveDefaultGrowth` — actual, within cap**
   `{ fundamentals: { rev_growth_yoy: 0.20 } }` → `{ rate: 0.20, raw: 0.20, source: "actual" }`

5. **`deriveDefaultGrowth` — actual, clamped at cap**
   `{ fundamentals: { rev_growth_yoy: 0.90 } }` → `{ rate: 0.35, raw: 0.90, source: "actual" }` (clamped to `GROWTH_CAP`, raw preserved for display)

6. **`deriveDefaultGrowth` — null → default**
   `{ fundamentals: { rev_growth_yoy: null } }` → `{ rate: 0.08, raw: null, source: "default" }`

7. **`deriveDefaultDiscountRate` — macro present, DGS10 resolvable**
   `macro.series = [{ series_id: "DGS10", symbol: "10Y", last: 4.474, ... }]` → `{ rate: 0.08974, source: "macro_dgs10", dgs10: 4.474 }` (4.474/100+0.045 = 0.08974)

8. **`deriveDefaultDiscountRate` — macro null → flat fallback**
   `macro = null` → `{ rate: 0.095, source: "flat_fallback", dgs10: null }`

9. **`runDcf` — Fixture A, full engine, r=0.10 (round number for hand-verification), FCF0=5, g1=0.20, gT=0.025**
   - `gs = [0.2, 0.15625, 0.1125, 0.06875, 0.025]`
   - `fcfs = [6.0, 6.9375, 7.717969, 8.248579, 8.454794]`
   - `pvs = [5.454545, 5.733471, 5.798624, 5.633891, 5.249762]`
   - `sumPvStage1 ≈ 27.870293`
   - `terminalValue ≈ 115.548846` (`8.454794×1.025/(0.10-0.025)`)
   - `pvTerminalValue ≈ 71.746742`
   - `fairValuePerShare ≈ 99.617035`, `valid: true`, `error: null`

10. **`runDcf` — Fixture B, ps/fcf_margin-derived base, r=0.0897 (≈ default-derived rate), FCF0=1.5, g1=0.10, gT=0.025**
    - `fcfs = [1.65, 1.784063, 1.895566, 1.978497, 2.02796]`
    - `sumPvStage1 ≈ 7.204561`, `terminalValue ≈ 32.127649`, `pvTerminalValue ≈ 20.909526`
    - `fairValuePerShare ≈ 28.114087`

11. **`runDcf` — invalidity guard, r ≤ gT**
    `{ baseFcfPerShare: 5, growthY1: 0.2, terminalGrowth: 0.025, discountRate: 0.02 }` → `{ valid: false, error: "discount rate must exceed terminal growth", fairValuePerShare: null }` (no NaN/Infinity ever surfaces)

12. **`runDcf` — zero-growth flat case (sanity/regression anchor)**
    `{ baseFcfPerShare: 10, growthY1: 0.025, terminalGrowth: 0.025, discountRate: 0.075 }` (g1==gT ⇒ every `g_t=0.025`, flat perpetuity check) → `FCF_t = 10×1.025^t` for all t; `terminalValue = FCF_5×1.025/(0.075-0.025) = FCF_5×20.5`; assert `fairValuePerShare ≈ sum of a straightforward growing-perpetuity closed form` computed independently as a cross-check (`FCF_0×(1+g)/(r-g) ≈ 205.0` since stage-1/stage-2 boundary is seamless when g1=gT) — this case exists specifically to prove the fade formula collapses correctly to a plain Gordon-growth perpetuity when there's no fade.

13. **`runDcfWithUpside` — price comparison**
    Using Fixture A (`fairValuePerShare ≈ 99.617`) with `currentPrice = 110` → `upsidePct ≈ (99.617-110)/110×100 ≈ -9.44` (overvalued vs. model)

14. **`runDcfWithUpside` — null price → null upside, no throw**
    `currentPrice = null` → `{ ...result, currentPrice: null, upsidePct: null }`

15. **`sensitivityGrid` — 3×3 grid off Fixture A base case (FCF0=5, g1=0.20, gT=0.025, r=0.10)**
    Center cell `[dr=0][dg=0] ≈ 99.617` (matches case 9). Full grid (rows = discountDelta −0.01/0/+0.01, cols = growthDelta −0.02/0/+0.02):
    ```
                    g-2%      g+0        g+2%
    r-1%          110.6245   115.2945   120.1027
    r+0%           95.6122    99.6170   103.7395
    r+1%           84.1385    87.6357    91.2349
    ```
    Assert monotonicity as a structural check too: fair value strictly decreases left→right→down is wrong (increases with growth, decreases with discount) — i.e. `grid[0][*] > grid[1][*] > grid[2][*]` (lower discount ⇒ higher value) and each row increasing left-to-right (higher growth ⇒ higher value).

16. **`buildDefaultDcfInputs` — integration of all four derive* functions**
    Full `Stock` fixture (`price:100, pfcf:20, rev_growth_yoy:0.20`) + macro fixture (`DGS10.last:4.474`) → bundles cases 1+4+7 into one object; assert every sub-field matches its standalone case's expected value (no drift between the composed function and its parts).

---

## 6. Docs-writer brief (pipeline additions, Rounds 1–6, verified against `scripts/refresh_daily.py`'s current step list)

Ran `build_plan()` in `scripts/refresh_daily.py` (lines 50–105) directly against its own source to get the **authoritative, current** ordered step list (not memory):

```
1. pull AI-stack fundamentals         pull_ai_stack.py
2. pull 5y prices                     pull_prices.py
3. merge ai-extracted edges           merge_enriched.py
4. build capital web                  build_capital_web.py
5. graph analysis (metrics/health/macro/fed/vuln)   run_graph_analysis.py
6. build chokepoint layer -> chokepoints.json       build_chokepoints.py     [conditional: os.path.exists guard]
7. (optional, --with-backtest) backtest (heavy)     run_backtest.py
8. export site.json                   export_site.py
9. compute risk analytics -> risk.json               build_risk.py           [conditional: os.path.exists guard]
10. compute investor-archetype scorecards -> archetypes.json   build_archetypes.py   [conditional: os.path.exists guard]
11. compute portfolio -> web/data/portfolio.json     build_portfolio.py       [conditional: os.path.exists guard]
12. pull macro dashboard -> macro.json               pull_macro.py           [conditional: os.path.exists guard]
13. (optional, quantum CLIs present) pull quantum fundamentals   pull_quantum.py
14. (optional) export quantum.json                   export_quantum.py
15. build screener                     build_screener.py
16. (optional, pull_news.py present) pull news + graph linkage   pull_news.py
17. (optional, --deploy) deploy to Vercel (prod)     vercel --prod --yes
```

**For the docs writer — per-round pipeline additions, mapped onto the list above:**

- **Round 2 (TA desk):** `pull_ta.py` (referenced in the task prompt) does **not appear in `build_plan()`'s current step list** — confirm with the TA-round author whether `ta_desk.json` (present in `public/data/`, 74KB) is produced by a step wired elsewhere (e.g. a separate cron/CLI not part of `refresh_daily.py`) or whether the `refresh_daily.py` wiring was never added. Flag this as a doc gap, don't assume — the file exists (`web/public/data/ta_desk.json`) but its producing script is not in this orchestrator's plan.
- **Round 3 (Risk desk):** step 9, `build_risk.py` → `risk.json`. Conditionally added (`os.path.exists` guard — degrades gracefully if the script isn't present in a given checkout).
- **Round 4 (Macro desk):** step 12, `pull_macro.py` → `macro.json`. Conditionally added, same guard pattern. Note it runs **after** `export_site.py`/`build_screener.py` in the current ordering, and even after the quantum steps — sequencing detail worth calling out since macro.json is independent of the AI/quantum stock universe.
- **Round 5 (Archetypes):** step 10, `build_archetypes.py` → `archetypes.json`. Conditionally added; explicitly documented in its own file header as "a pure, zero-network 'computed' step over site.json" (see `web/lib/archetypes.ts` header comment) — i.e. it depends on `export_site.py` having already run (step 8), consistent with its position after it in the plan.
- **Round 5/6 (Portfolio):** step 11, `build_portfolio.py` → `web/data/portfolio.json` (note: **not** `web/public/data/` — different output root than every other step; worth flagging to the docs writer as a likely-intentional but easy-to-miss distinction, e.g. a private/local-only file not meant for the public bundle).
- **Round 6 (Chokepoints):** step 6, `build_chokepoints.py` → `chokepoints.json`. Conditionally added, positioned **before** `export_site.py` (step 8) — i.e. it runs against `build_capital_web.py`/`run_graph_analysis.py` output directly, not against the exported site bundle, unlike archetypes/risk which run after export.
- **This round (DCF):** confirms **zero pipeline additions** — `dcf.ts` is pure client/server math over already-loaded `site.json` + `macro.json`; `refresh_daily.py`'s step list is unchanged by this round, and the docs writer should note DCF explicitly as the "no new Python step" counter-example to Rounds 3/4/5/6 above.

**Cross-cutting notes for the docs writer:**
- Every desk file (`risk.json`, `archetypes.json`, `macro.json`, `portfolio.json`, `chokepoints.json`) is produced by a **conditionally-added** step (`if os.path.exists(.../build_X.py)`) — the pipeline degrades to skipping the step entirely if the script is missing, and every corresponding `web/lib/*.ts` loader independently degrades via `existsSync`/try-catch/never-throws if the *output* JSON is missing. Two independent degradation layers — document both.
- `ta_desk.json` is the one output file in `public/data/` whose producing script does not currently appear in `build_plan()` — needs verification/doc-flag as noted above, not silently assumed to be `pull_ta.py` run out-of-band.
- `pull_quantum.py`/`export_quantum.py` and `pull_news.py` are also conditional/optional steps from earlier work not explicitly named in this round's Rounds-1-6 list but present in the current plan — worth a one-line mention so the docs writer's step inventory matches `refresh_daily.py` exactly rather than only the six named rounds.
