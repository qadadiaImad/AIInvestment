# AI STACK TERMINAL — `/terminal` TA/Day-Trading Desk — Merged v1 Spec

Status: merged from three parallel designs (A = TA data, B = UI/UX, C = gate/ops) by the
lead architect. This is the binding v1 spec. Where the three designs disagreed, this
document states the resolution and why — **simplicity and one-round shippability won**
every tie unless noted.

Educational/research only — not financial advice. `/terminal` is access-gated and
strictly personal.

---

## 0. What shipped vs. what got cut for v1

Cut from the source designs, to keep this a one-round build:

- **Weekly pivots.** Design A fully specced `weekly_pivots_basis`/ISO-week aggregation.
  None of the three UI mockups actually surfaced a second pivot table. Daily pivots only
  in v1; weekly is a clean fast-follow (the `ta.py` function list still reserves the
  name).
- **Per-leaf envelope objects** (`{value,raw,unit,dirty,retrieved_at,source,source_url,
  source_class}` on every single number). Design A wrapped every pivot/ATR/SMA/RSI value
  individually. Design B's own contract sketch (§1.1 of Design B) already flattened this
  to plain numbers with one provenance stamp per instrument. **Resolution: flatten.**
  `ta_desk.json` carries one `retrieved_at` + two `source_url_*` fields per instrument
  (all its numbers come from the same two Yahoo fetches at the same moment — one stamp is
  honest, not a shortcut). This directly resolves Design A's own flagged open question
  ("does `source_class` need a new `computed` enum value?") — **no**, because the
  cross-repo `data-schema.md` envelope is no longer used leaf-by-leaf for this feed, so
  no sign-off is needed on that enum change. This is a deliberate, documented deviation
  from the root CLAUDE.md's literal "every datum gets an envelope" phrasing, justified by:
  all values for an instrument share one retrieval event, and per-leaf envelopes would
  roughly 8x the JSON size and the builder/consumer code for zero information gain here.
  Missing/uncomputable values become explicit `null` plus a human-readable entry in a
  per-instrument `warnings: string[]` array — this satisfies "flag dirty explicitly,
  never silently decide" without reintroducing the envelope.
- **TradingView scanner endpoints for indicators** (Design C §2.2 speculated `pull_ta.py`
  might use TV's `/forex/scan`/`/cfd/scan`). **Resolution: no.** Design A's pure-Yahoo,
  locally-computed pipeline is fully specified (formulas + Wilder smoothing + edge cases +
  pytest fixtures) and needs zero extra provider. TradingView is used **only** for the
  `tv_symbol` embed prop in the interactive chart — never as a data source. Single
  dependency (Yahoo keyless chart API), matches CLAUDE.md §3's REST-first doctrine
  trivially (this is "no Playwright anywhere in the pipeline," Mode A/B don't even apply).
- **Route-group restructure of the entire app** (Design C's Option A for chrome-stripping,
  which would move every existing top-level route folder under `(site)/`). Also rejected
  Design B's client-side `ChromeGate` (real correctness risk: a `"use client"` component
  can render `<Header/>`/`<Footer/>` for one frame before hydration resolves, which is
  fatal for a script that screenshots the page — a screenshot taken a few ms too early
  bakes the chrome in). **Resolution: Design C's Option B**, done server-side with zero
  flash risk and a small diff — see §6.
- **Instrument universe**: Design A's 11-instrument table is authoritative (Design B and C
  both left the universe as an open question / assumption). See §1.
- **Session key names / windows**: unify on Design A's 9-hour windows (`00:00–09:00 /
  08:00–17:00 / 13:00–22:00` UTC) since that's the version with actual bar-partitioning
  logic and tests behind it; use Design B/C's friendlier key `tokyo` (not `asia`) for the
  first window since both UI designs independently chose it.
- **DXY's UI group**: none of the three designs' FX/METALS/ENERGY taxonomy has a home for
  DXY (an index, not FX/metal/energy). **Resolution: add a fourth group, `INDEX`.**

Everything else below is additive merge — most content across the three designs did not
conflict and is carried through unchanged (gate mechanics, refresh runner shape, capture
Playwright sequence, mobile-first rules, TradingView embed reuse).

---

## 1. Instrument universe (11 instruments — from Design A, authoritative)

| symbol | display_name | asset_class | group | yahoo_symbol | tv_symbol |
|---|---|---|---|---|---|
| EURUSD | EUR/USD | fx | FX | `EURUSD=X` | `OANDA:EURUSD` |
| GBPUSD | GBP/USD | fx | FX | `GBPUSD=X` | `OANDA:GBPUSD` |
| USDJPY | USD/JPY | fx | FX | `USDJPY=X` | `OANDA:USDJPY` |
| USDCHF | USD/CHF | fx | FX | `USDCHF=X` | `OANDA:USDCHF` |
| AUDUSD | AUD/USD | fx | FX | `AUDUSD=X` | `OANDA:AUDUSD` |
| USDCAD | USD/CAD | fx | FX | `USDCAD=X` | `OANDA:USDCAD` |
| GOLD | Gold | commodity | METALS | `GC=F` | `OANDA:XAUUSD` |
| SILVER | Silver | commodity | METALS | `SI=F` | `OANDA:XAGUSD` |
| WTI | WTI Crude Oil | commodity | ENERGY | `CL=F` | `NYMEX:CL1!` |
| NATGAS | Natural Gas | commodity | ENERGY | `NG=F` | `NYMEX:NG1!` |
| DXY | US Dollar Index | index | INDEX | `DX-Y.NYB` | `TVC:DXY` |

`group` is a derived UI-grouping field (not re-fetched, computed once in `ta.py`'s
`UNIVERSE` table): `fx→FX`, `GOLD/SILVER→METALS`, `WTI/NATGAS→ENERGY`, `DXY→INDEX`.
`groups` array in the JSON is `["FX","METALS","ENERGY","INDEX"]`, always in that order.

Big-Six FX majors (no NZDUSD — matches the investing brief). Metals use OANDA spot
aliases for the TV embed (free-tier friendly, tracks `GC=F`/`SI=F` closely); WTI/NatGas
use TV's continuous-futures symbols since there's no equally standard free spot alias.
`tv_symbol` is embed-only — never used for data retrieval.

---

## 2. Data pipeline (Python side) — REST-only, no Playwright

Two Yahoo chart-API pulls per instrument:
- **Daily**: `range=1y&interval=1d` (~252 bars, full OHLC).
- **Intraday**: `range=1mo&interval=60m` (Yahoo has no literal "30d" range enum; `1mo` is
  the closest valid bucket and satisfies "≈30d of hourly bars").

All indicators/levels are computed locally in pure Python from these two series — see
brief for exact formulas (classic pivots, Wilder ATR14/RSI14, SMA20/50/200, 52-week
range, session H/L partitioning, nearest-level lookup, ATR bands, RSI state).

"Today" boundary = UTC calendar date of `generated_at`. `prev_bar` = most recent **daily**
bar with `date < today` — never assume the newest daily bar is complete. Documented
caveats carried through unchanged from Design A: UTC-midnight day boundary (not NY 17:00
close) and DST-naive fixed-UTC session windows — both acceptable for v1, flagged as
revisit-if-the-owner-notices items, not silently resolved.

---

## 3. `ta_desk.json` — the binding contract

See the `contract` field of this task's structured output for the exact annotated JSON
(one FX + one commodity instrument). Summary of shape:

```
{ generated_at, schema_version, source, source_class, disclaimer, groups[],
  instruments: [ {
      symbol, display_name, asset_class, group, yahoo_symbol, tv_symbol,
      retrieved_at, source_url_daily, source_url_intraday,
      price: { last, previous_close, day_change_pct, day_change_abs },
      trend: { state, sma20, sma50, sma200, price_above_sma20/50/200, sma50_above_sma200 },
      rsi14: { value, state },
      atr14: { value, upper_1x, lower_1x, upper_2x, lower_2x },
      levels: { daily_pivots{basis_date,pp,r1-3,s1-3}, previous_day_ohlc{date,o,h,l,c,change_pct},
                fifty_two_week{high,low,position_pct} },
      nearest_level: { label, value, distance_pct },
      sessions: { date, tokyo{window_utc,high,low,bar_count,complete}, london{...}, new_york{...} },
      sparkline: [ {t, c}, ... ],   // ~48 most recent intraday closes, ascending, free slice of the intraday fetch
      warnings: [ "..." ]
  } ] }
```

Storage: `web/public/data/ta_desk.json` — generated, gitignored, whole-file overwrite
each run (cheap REST refresh, not a scarce gated pull — no timestamped audit directory
needed on the web-facing copy; an optional dated audit copy under `data/ta/` is fine but
not read by the site).

---

## 4. Web app — routes, gate, capture

### 4.1 Routes
```
/terminal                  desk dashboard (4 group sections: FX/METALS/ENERGY/INDEX) — gated
/terminal/[symbol]         instrument workstation (TradingView embed + levels) — gated
/terminal/card/[symbol]    1080x1350 capture card, chrome-stripped via ?capture=1 — gated
```

### 4.2 Gate (Design C, adopted as-is)
`web/middleware.ts`, matcher `["/terminal/:path*"]`. Env var `TERMINAL_KEY` (unset →
open, matches this sandbox/local dev). Cookie `terminal_key` (httpOnly, secure-in-prod,
sameSite=lax, path=`/terminal`, maxAge 400d). `?key=` query param checked every request,
sets the cookie on first successful match and serves that same request (no redirect
hop — matters for the capture script, which must not depend on a redirect chain).
Deny = bare `404`, plus `X-Robots-Tag: noindex,nofollow` and `Referrer-Policy:
strict-origin` on every `/terminal/*` response. `web/app/robots.ts` disallows `/terminal`.
Set `TERMINAL_KEY` in both Vercel Production and Preview env scopes; leave unset in
Development.

### 4.3 Chrome-stripping for capture (resolved mechanism — see §0)
Same middleware pass that checks the gate also handles capture-chrome-stripping, so
there's exactly one file doing request-time decisions for `/terminal/*`:

- When the matched path starts with `/terminal/card/` **and** `capture=1` is present,
  middleware sets a request header `x-capture-mode: 1` (via
  `NextResponse.next({ request: { headers } })`) before passing the request through.
- `web/app/layout.tsx` becomes an async Server Component that calls `headers()` from
  `next/headers`, checks for `x-capture-mode`, and conditionally omits `<Header/>` /
  `<Footer/>` around `{children}`. Server-rendered, so there is zero flash — a Playwright
  screenshot taken the instant the response lands is already chrome-free. This is a
  ~10-line diff to the one existing root layout, not a route-group restructure.
- `<main>` stays full-bleed either way; `CaptureCard` supplies its own `#0b0f17`
  background so it never depends on `<main>`'s padding assumptions.

### 4.4 Data loader
`web/lib/ta.ts` — server-only (`fs`), `existsSync`-guarded exactly like `getNewsData()`
(absence is a first-class, expected state, never a throw): `getTaDeskData()`,
`getTaInstrument(symbol)`, `getTaGroups()`. `web/lib/sessions.ts` — client-safe, pure
wall-clock math for the live session-clock strip (no `fs`, mirrors the existing
`lib/conflict.ts`/`lib/news.ts` split), using the unified 9-hour windows from §0.

### 4.5 Pages (mobile-first, dark-only, JetBrains Mono, `rounded-sm`, existing palette)
- `/terminal`: sticky session-clock strip under the existing Header, then 4 `GroupSection`
  blocks (FX/METALS/ENERGY/INDEX) of `InstrumentTile` cards, `grid-cols-2` on phone. Null
  data → single centered "TA desk data not generated yet" panel, never throw.
- `/terminal/[symbol]`: `notFound()` on unknown symbol, no `generateStaticParams`
  (gitignored data may be absent at build time — dynamic render). Reuses
  `TradingViewChart` verbatim with `inst.tv_symbol`. `LevelsPanel` (pivots table, ATR
  bands, session H/L), `PrevDayStats`, RSI gauge bar.
- `/terminal/card/[symbol]`: pure Server Component, `dynamic = "force-dynamic"`, no
  client JS, no live TradingView widget (async cross-origin iframe has no reliable
  "painted" signal — fatal for deterministic screenshots). Mini price sparkline rendered
  as inline server-side SVG from the `sparkline` array. `data-capture-ready="true"` on
  `<body>` as the Playwright wait-selector. Screenshot via
  `page.locator("#capture-canvas").screenshot()` at native 1080×1350 DOM size — never via
  the CSS-scaled preview wrapper used for on-screen human review.

### 4.6 Nav
Rename the existing home nav item `TERMINAL → HOME` (frees the word up), add
`{ href: "/terminal", label: "TA DESK" }`.

### 4.7 Refresh runner
`scripts/refresh_ta.py`, thin sibling of `refresh_daily.py` (pure `build_plan(args)`,
`--dry-run`, `--deploy`, `--keep-going`, one real step: `python pull_ta.py`). Pull
frequently (cheap, local REST), deploy on a coarser cadence or on demand — avoids
Vercel's deploy-count ceiling.

---

## 5. Open items carried forward (flagged, not silently resolved)

1. UTC-midnight day boundary vs. NY 17:00 FX convention — v1 ships UTC, revisit if it
   looks wrong to a trader.
2. DST-naive fixed-UTC session windows — up to ~1h drift across DST changes; acceptable
   for v1.
3. Weekly pivots — cut from v1 scope (see §0), clean fast-follow.
4. Gating implementation (§4.2) must land **before** production deploy — the capture-card
   route is deliberately bare-looking to make screenshots clean, which also makes it look
   unauthenticated if the gate isn't wired up yet.
