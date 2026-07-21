# AI STACK TERMINAL — Round 5 Design: Portfolio Module (merged v1)

Fincept-style "portfolio management" desk: the owner's real positions → exposure, P&L,
risk. Mirrors the Round 1–4 conventions (`aiinvest/<domain>.py` pure math +
`build_<domain>.py` network-free assembly + `web/lib/<domain>.ts` existsSync-guarded
reader + gated `/terminal/<domain>` page + `/terminal/card/<domain>` capture card), with
**three privacy deviations from that pattern**, because this is the one module touching
real dollar positions. This document supersedes the two Round-5 drafts ("Design A / data"
and "Design B / UI", the latter of which did not produce usable content) — it is the
single authority for implementation. Field names below are **final**.

---

## 0. Privacy architecture (read first — non-negotiable)

| Round 1–4 pattern | Portfolio module deviation | Why |
|---|---|---|
| Output → `web/public/data/<x>.json` | Output → **`web/data/portfolio.json`** (no `public/`) | `web/public/**` is served as a static asset by literal URL — the `/terminal` proxy matcher (`web/proxy.ts`, `matcher: ["/terminal/:path*"]`) never sees `/data/portfolio.json` requests, so anything under `public/` bypasses the key-gate entirely. `web/data/portfolio.json` is read server-side only, via `fs.readFileSync(path.join(process.cwd(), "data", "portfolio.json"))` — same technique `lib/risk.ts` already uses for `public/data/risk.json`, just pointed at a non-public directory. Never fetchable by URL. |
| Input → `data/<x>/...` (gitignored) | Input → **`data/portfolio/positions.json`** (gitignored, unchanged pattern) | `data/` is already blanket-ignored at repo root (`.gitignore`: `data/`). Owner hand-edits this file locally; never committed, never leaves the machine except as the computed aggregates. |
| Capture card shows real numbers | Capture card shows **percentages/ratios only** — weights, P&L %, day change %, layer mix %, HHI, vol/VaR/Sharpe/beta. **No dollar amounts anywhere on `/terminal/card/portfolio`,** not even in capture mode. Absolute `$` figures render **only on the gated `/terminal/portfolio` page**, behind the same `terminal_key` cookie/query gate as every other desk (`proxy.ts` matcher already covers it — no proxy change needed). | The capture card is designed to be screenshotted and shared; dollar amounts are exactly the datum that must never leave the gate. |

`.gitignore` additions (root):

```gitignore
# Portfolio module — server-only computed bundle (NOT public/, never gated-bypass-able)
web/data/

# data/ already ignores data/portfolio/positions.json as a whole-directory pattern.
# git will not descend into an ignored directory to evaluate file-level negations, so
# data/portfolio/ must be re-included first, then re-blocked file-by-file, before the
# two committed template files can be un-ignored:
!data/portfolio/
data/portfolio/*
!data/portfolio/positions.example.json
!data/portfolio/README.md
```

`data/portfolio/positions.json` itself stays ignored — re-blocked by `data/portfolio/*`
and never explicitly un-ignored.

---

## 1. `data/portfolio/positions.json` — input schema (owner hand-edited)

```json
{
  "base_currency": "USD",
  "cash_usd": 1000.00,
  "positions": [
    {
      "symbol": "NVDA",
      "quantity": 10,
      "cost_basis_per_share": 400.00,
      "acquired_date": "2024-01-10",
      "note": "core position"
    },
    {
      "symbol": "MSFT",
      "quantity": 20,
      "cost_basis_per_share": 250.00,
      "acquired_date": "2024-02-01"
    }
  ]
}
```

**Field rules**

| Field | Required | Rule |
|---|---|---|
| `base_currency` | no | defaults `"USD"`; anything else → warning `"base_currency: only USD supported, treating as USD"` (no FX conversion in v1) |
| `cash_usd` | no | defaults `0.0`; must be finite and `>= 0`, else clamped to `0.0` + warning `"cash_usd: invalid/negative, treated as 0"` |
| `positions[].symbol` | **yes** | non-empty string, trimmed + uppercased. Row **dropped** (warning `"row {i}: missing/empty symbol, dropped"`) if absent — structurally unusable, not an "unknown symbol" |
| `positions[].quantity` | **yes** | must be finite and **`> 0`**. Row **dropped** (warning `"{symbol}: quantity <= 0 or non-numeric, row dropped"`) if not |
| `positions[].cost_basis_per_share` | no | if present, must be finite and `> 0`; else stored `null` + warning `"{symbol}: cost_basis_per_share missing/invalid — P&L unavailable for this lot"`. Row **not dropped** — a position with unknown cost basis still has market value, weight, and layer, it just can't show P&L |
| `positions[].acquired_date` | no | ISO `YYYY-MM-DD` or `null`; invalid strings → `null` + warning, row kept |
| `positions[].note` | no | free string, passed through verbatim, truncated to 280 chars |

**Multiple rows, same symbol (lots).** Rows sharing a `symbol` are merged into one
per-symbol position before pricing:
- `quantity` = sum of the lots' quantities
- `cost_basis_per_share` = quantity-weighted average across lots that HAVE a cost basis
  (lots missing cost basis excluded from the average, not treated as zero); `null` if none
- `acquired_date` = earliest non-null date among the lots
- `note` = lot notes joined with `"; "`
- `lots_merged` = count, for display (`"NVDA (2 lots)"`)
- warning `"{symbol}: {n} lots merged"` when `n > 1`

**Unknown-symbol handling — never dropped.** A symbol not in `site.json` and with no
`prices/<SYM>.json` file still gets a full position row: `last_price: null`,
`market_value_usd: null`, `weight_pct: null`, `layer: null`, plus warning
`"{symbol}: no price data available (not in AI-stack universe, no price file) — excluded
from valued aggregates"`. Stays visible in `positions[]` with quantity/cost-basis so the
owner sees it's tracked but unpriced.

Missing `data/portfolio/positions.json` entirely → the whole pipeline degrades to the
**empty-state bundle** (§5), not an error, exit code 0. `web/lib/portfolio.ts`'s reader
returns `null` on that bundle (mirroring `getRiskData()`), and the page shows: *"No
positions file yet — copy `data/portfolio/positions.example.json` to
`data/portfolio/positions.json` and edit it with your holdings."*

---

## 2. Computed per-position fields

Price resolution order (first hit wins):

1. `web/public/data/prices/<SYM>.json` → last valid bar's `close` as `last_price`, its
   `date` as `price_as_of`, `price_source = "prices_file"`. Also gives the previous valid
   bar for day-change and the full return series for the risk block.
2. Fallback: `site.json.stocks[SYM].valuation.price` (no history, no day-change, no risk-
   series eligibility) → `price_source = "site_json_fallback"`,
   `price_as_of = site.json.stocks[SYM].as_of`. Warning `"{symbol}: no price history
   file, using latest site.json quote (no day-change, excluded from risk series)"`.
3. Neither → `null` (unknown-symbol case above).

`layer` = `site.json.stocks[SYM].layer` if in the universe, else `null` — an ETF like
`SPY` or a non-AI-stack name is not silently forced into a layer; bucketed as
`"unclassified"` at the aggregate level (§3).

Per-position output object:

```json
{
  "symbol": "NVDA",
  "quantity": 10.0,
  "lots_merged": 1,
  "cost_basis_per_share": 400.00,
  "cost_basis_total_usd": 4000.00,
  "acquired_date": "2024-01-10",
  "note": "core position",
  "layer": "L1-chips",
  "last_price": 550.00,
  "price_as_of": "2026-07-14",
  "price_source": "prices_file",
  "market_value_usd": 5500.00,
  "weight_pct": 44.4265,
  "unrealized_pnl_usd": 1500.00,
  "unrealized_pnl_pct": 37.5,
  "day_change_pct": 10.0,
  "day_change_usd": 500.00,
  "warnings": []
}
```

Formulas (reuse `aiinvest/risk.py` wherever a function already exists — never
reimplement vol/VaR/Sharpe/drawdown/beta/correlation/day-change math):

- `cost_basis_total_usd = quantity * cost_basis_per_share` (null if cost basis null)
- `market_value_usd = quantity * last_price` (null if `last_price` null)
- `weight_pct = market_value_usd / total_value_usd * 100` — denominator is the portfolio
  total **including cash** (§3); null if `market_value_usd` null
- `unrealized_pnl_usd = market_value_usd - cost_basis_total_usd` (null if either null)
- `unrealized_pnl_pct = unrealized_pnl_usd / cost_basis_total_usd * 100` (null if
  `cost_basis_total_usd` null or `0`)
- `day_change_pct = risk.day_change_pct(valid_bars)` — reused verbatim, needs the last 2
  valid bars from the price file; null on the `site_json_fallback` path or `<2` bars
- `day_change_usd = quantity * (last_close - prev_close)` — **not**
  `market_value_usd * day_change_pct / 100`, because `market_value_usd` is priced at
  *today's* close while `day_change_pct` is relative to *yesterday's* close; the two
  don't compose that way. This is a load-bearing correctness note — see the regression
  test in §8 Fixture C.

---

## 3. Portfolio aggregates

Let `V = total_value_usd = cash_usd + Σ market_value_usd` (sum over priced positions).

| Field | Formula |
|---|---|
| `total_value_usd` | `cash_usd + Σ market_value_usd` |
| `invested_value_usd` | `Σ market_value_usd` (excludes cash) |
| `cash_usd`, `cash_weight_pct` | `cash_usd`; `cash_usd / total_value_usd * 100` |
| `total_cost_basis_usd` | `Σ cost_basis_total_usd` over positions where **both** `market_value_usd` and `cost_basis_total_usd` are non-null |
| `total_unrealized_pnl_usd` | `Σ unrealized_pnl_usd` over that same subset |
| `total_unrealized_pnl_pct` | `total_unrealized_pnl_usd / total_cost_basis_usd * 100` |
| `day_pnl_usd` | `Σ day_change_usd` over positions where it's non-null |
| `day_pnl_pct` | `day_pnl_usd / (total_value_usd - day_pnl_usd) * 100` — relative to yesterday's implied total value (cash assumed flat day-over-day) |
| `n_positions`, `n_positions_priced`, `n_positions_unpriced` | counts |
| `layer_exposure[]` | one entry per `{L0-energy … L4-application, "unclassified", "cash"}` bucket: `{layer, weight_pct, market_value_usd, n_positions}`. `"unclassified"` = priced positions with `layer: null`. `"cash"` = the cash bucket. Sums to ~100% (modulo unpriced positions, excluded and separately warned) |
| `concentration.top1_weight_pct` / `top3_weight_pct` | weight of the largest / sum of largest-3 **priced, non-cash** positions, against `invested_value_usd` |
| `concentration.hhi` | `Σ (market_value_usd_i / invested_value_usd)^2` over priced positions, 0–1 scale (1.0 = single-name); `basis: "invested_value_excluding_cash"` |

**Worked example** (the canonical pytest fixture, §8): NVDA 10sh @ cost 400, price
500→550 (day +10%); MSFT 20sh @ cost 250, price 300→294 (day −2%); cash 1000.

```
NVDA: mv=5500, pnl=+1500 (+37.5%), day_chg=+500
MSFT: mv=5880, pnl=+880 (+17.6%),  day_chg=-120
total_value = 5500+5880+1000 = 12380
invested_value = 11380
weight NVDA = 5500/12380*100 = 44.4265%
weight MSFT = 5880/12380*100 = 47.4959%
cash_weight  = 1000/12380*100 =  8.0775%
total_cost_basis = 4000+5000 = 9000
total_unrealized_pnl = 1500+880 = 2380  ->  2380/9000*100 = 26.4444%
day_pnl = 500-120 = 380  ->  380/(12380-380)*100 = 380/12000*100 = 3.1667%
top1 = 5880/11380*100 = 51.6696%   top3 = (5500+5880)/11380*100 = 100%
hhi  = (5500/11380)^2 + (5880/11380)^2 = 0.23359 + 0.26696 = 0.50055
layer_exposure: L1-chips 44.4265%, L2-infra 47.4959%, cash 8.0775%, others 0%
```

---

## 4. Risk block — reusing `aiinvest/risk.py` on a weighted portfolio return series

**Construction.** For each priced position with a `prices_file`-sourced return series,
take its full daily-return map `{date: ret}` via `risk.daily_returns` (exactly as
`build_risk.py` does per stock). Restrict to positions that: are priced, have
`price_source == "prices_file"`, and have `>= risk.MIN_BARS` (60) return bars in the
trailing `window` (252 — both same defaults as `build_risk.py`, both CLI-overridable).

Call this the **included set** `S`, weights **renormalized within `S`**:
`w_i = market_value_usd_i / Σ_{j∈S} market_value_usd_j` (what the priced,
sufficiently-historied slice of the book would have returned — not diluted by cash or
unpriced names).

Use the **intersection of dates common to all of `S`** (mirrors `build_risk.py`'s
correlation-block philosophy of only comparing fully-overlapping dates; a union would
create false zero-return days for symbols missing that date):

```
portfolio_ret[d] = Σ_{i∈S} w_i * ret_i[d]     for each date d in the common-date set
```

Feed that single `[{"date","ret"}]`-shaped series straight into the **same** `risk.py`
functions `build_risk.py` uses per-stock:

| Output field | Call |
|---|---|
| `vol_annualized_pct` | `risk.annualized_vol_pct(window_vals)` |
| `var95_1d_pct` | `risk.historical_var_pct(window_vals, 0.95)` |
| `sharpe_1y` | `risk.sharpe_ratio(window_vals, rf_annual, 252)` — `rf_annual` sourced identically to `build_risk.py`: `graph_analysis.json:macro.snapshot.dff` if present, else `--rf-annual` CLI default `0.04` |
| `beta_vs_spy` | `risk.beta(xs, ys)` where `xs, ys = risk.align_series(portfolio_ret_map, spy_full_ret)` |
| `max_pairwise_correlation` | among the top-N held-in-`S` symbols by weight (default N=5, CLI `--top-n-correlation`): pairwise `risk.pearson_correlation` on `risk.align_series`-aligned windows, report the max-`abs()` pair as `{"a","b","value"}` (tie-break alphabetical) |

**Methodology note (stored verbatim in `risk.methodology_note`):**

> "This portfolio return series applies TODAY'S position weights to each holding's OWN
> historical daily-return series ('fixed-weight, as-if-held-at-current-composition'
> proxy) — it is NOT a reconstruction of the account's actual historical share counts or
> cost basis (true buy-and-hold). Past vol/VaR/Sharpe/beta therefore show what the
> CURRENT portfolio composition would have earned or lost historically, not what this
> account actually experienced while positions were being built up over time. Cash and
> any holding lacking sufficient price history are excluded from the series (see
> `series_coverage`), which is a further departure from the literal book — check
> `weight_coverage_pct` before trusting these numbers on a thin-history portfolio."

This fixed-weight simplification note is **mandatory** — it must ship verbatim in the
JSON and be surfaced on the gated page (not just buried in a warning array).

`series_coverage`: `{n_holdings_included, n_holdings_total_priced,
weight_coverage_pct (= Σ w_i market_value over S / invested_value_usd * 100),
excluded: [{"symbol","reason"}]}`. Warning `"risk series covers only {x}% of invested
value by weight — treat vol/VaR/Sharpe/beta as indicative only"` whenever
`weight_coverage_pct < 80`.

If `|S| == 0` the whole `risk` block is null-filled with one warning `"no holdings have
sufficient price history for a risk series (need >={min_bars} return bars each)"` —
mirrors `build_risk.py`'s degrade-not-crash pattern.

---

## 5. `web/data/portfolio.json` — output schema (final)

```json
{
  "generated_at": "2026-07-14T18:32:00Z",
  "schema_version": "portfolio-v1",
  "source_class": "computed",
  "disclaimer": "Educational research only — not financial advice. Historical risk measures do not predict future losses.",
  "positions_source": {
    "path": "data/portfolio/positions.json",
    "mtime": "2026-07-14T09:11:00Z",
    "n_raw_rows": 3,
    "n_positions_after_merge": 2,
    "found": true
  },
  "prices_source": {
    "provider": "yahoo-finance-chart-api",
    "source_class": "api",
    "batch_retrieved_at": "2026-07-14T06:00:00Z"
  },
  "site_source": { "generated_at": "2026-07-14T06:05:00Z" },
  "params": {
    "base_currency": "USD",
    "window_trading_days": 252,
    "min_bars": 60,
    "rf_annual": 0.04,
    "rf_source": "cli-default",
    "top_n_correlation": 5,
    "var_confidence": 0.95
  },
  "positions": [
    {
      "symbol": "NVDA", "quantity": 10.0, "lots_merged": 1,
      "cost_basis_per_share": 400.00, "cost_basis_total_usd": 4000.00,
      "acquired_date": "2024-01-10", "note": "core position", "layer": "L1-chips",
      "last_price": 550.00, "price_as_of": "2026-07-14", "price_source": "prices_file",
      "market_value_usd": 5500.00, "weight_pct": 44.4265,
      "unrealized_pnl_usd": 1500.00, "unrealized_pnl_pct": 37.5,
      "day_change_pct": 10.0, "day_change_usd": 500.00, "warnings": []
    },
    {
      "symbol": "MSFT", "quantity": 20.0, "lots_merged": 1,
      "cost_basis_per_share": 250.00, "cost_basis_total_usd": 5000.00,
      "acquired_date": "2024-02-01", "note": null, "layer": "L2-infra",
      "last_price": 294.00, "price_as_of": "2026-07-14", "price_source": "prices_file",
      "market_value_usd": 5880.00, "weight_pct": 47.4959,
      "unrealized_pnl_usd": 880.00, "unrealized_pnl_pct": 17.6,
      "day_change_pct": -2.0, "day_change_usd": -120.00, "warnings": []
    }
  ],
  "aggregates": {
    "total_value_usd": 12380.00,
    "invested_value_usd": 11380.00,
    "cash_usd": 1000.00,
    "cash_weight_pct": 8.0775,
    "total_cost_basis_usd": 9000.00,
    "total_unrealized_pnl_usd": 2380.00,
    "total_unrealized_pnl_pct": 26.4444,
    "day_pnl_usd": 380.00,
    "day_pnl_pct": 3.1667,
    "n_positions": 2,
    "n_positions_priced": 2,
    "n_positions_unpriced": 0,
    "layer_exposure": [
      { "layer": "L0-energy", "weight_pct": 0.0, "market_value_usd": 0.0, "n_positions": 0 },
      { "layer": "L1-chips", "weight_pct": 44.4265, "market_value_usd": 5500.00, "n_positions": 1 },
      { "layer": "L2-infra", "weight_pct": 47.4959, "market_value_usd": 5880.00, "n_positions": 1 },
      { "layer": "L3-models", "weight_pct": 0.0, "market_value_usd": 0.0, "n_positions": 0 },
      { "layer": "L4-application", "weight_pct": 0.0, "market_value_usd": 0.0, "n_positions": 0 },
      { "layer": "unclassified", "weight_pct": 0.0, "market_value_usd": 0.0, "n_positions": 0 },
      { "layer": "cash", "weight_pct": 8.0775, "market_value_usd": 1000.00, "n_positions": 0 }
    ],
    "concentration": {
      "top1_weight_pct": 51.6696,
      "top3_weight_pct": 100.0,
      "hhi": 0.50055,
      "basis": "invested_value_excluding_cash"
    }
  },
  "risk": {
    "vol_annualized_pct": 28.4,
    "var95_1d_pct": -2.9,
    "sharpe_1y": 0.85,
    "beta_vs_spy": 1.32,
    "max_pairwise_correlation": { "a": "MSFT", "b": "NVDA", "value": 0.61 },
    "series_coverage": {
      "n_holdings_included": 2,
      "n_holdings_total_priced": 2,
      "weight_coverage_pct": 100.0,
      "excluded": []
    },
    "methodology_note": "This portfolio return series applies TODAY'S position weights to each holding's OWN historical daily-return series ('fixed-weight, as-if-held-at-current-composition' proxy) — it is NOT a reconstruction of the account's actual historical share counts or cost basis (true buy-and-hold). Past vol/VaR/Sharpe/beta therefore show what the CURRENT portfolio composition would have earned or lost historically, not what this account actually experienced while positions were being built up over time. Cash and any holding lacking sufficient price history are excluded from the series (see series_coverage), which is a further departure from the literal book — check weight_coverage_pct before trusting these numbers on a thin-history portfolio.",
    "warnings": []
  },
  "warnings": []
}
```

`positions_source.mtime` = `os.stat(positions_path).st_mtime` formatted UTC ISO — the
provenance stamp for owner-edited input, same spirit as `prices_retrieved_at` per stock
in `risk.json`. `found: false` + all-null/empty body is the **empty-state bundle** when
`data/portfolio/positions.json` doesn't exist yet:

```json
{
  "generated_at": "2026-07-14T18:32:00Z",
  "schema_version": "portfolio-v1",
  "source_class": "computed",
  "disclaimer": "Educational research only — not financial advice. Historical risk measures do not predict future losses.",
  "positions_source": { "path": "data/portfolio/positions.json", "mtime": null, "n_raw_rows": 0, "n_positions_after_merge": 0, "found": false },
  "prices_source": { "provider": "yahoo-finance-chart-api", "source_class": "api", "batch_retrieved_at": null },
  "site_source": { "generated_at": null },
  "params": { "base_currency": "USD", "window_trading_days": 252, "min_bars": 60, "rf_annual": 0.04, "rf_source": "cli-default", "top_n_correlation": 5, "var_confidence": 0.95 },
  "positions": [],
  "aggregates": null,
  "risk": null,
  "warnings": ["no positions file found at data/portfolio/positions.json — copy positions.example.json and edit it with your holdings"]
}
```

`web/lib/portfolio.ts`'s `getPortfolioData()` treats `found: false` as equivalent to
"no data" for page-rendering purposes but still returns the parsed object (not `null`) so
the page can show the exact copy-template message from `warnings[0]` — mirrors how
`getRiskData()` returns `null` on a genuinely missing/corrupt file, except here the
build script itself already produced a well-formed "empty" JSON, so the TS reader only
needs to return `null` when the **file** `web/data/portfolio.json` is absent (script never
run) vs. return the parsed empty-state object when the **positions input** was absent
(script ran, degraded on purpose). Both cases render the same "no positions yet" empty
state on the page; the distinction only matters for `existsSync` semantics in the reader.

---

## 6. Module plan — scripts (Python)

### `scripts/aiinvest/portfolio.py` (pure, zero I/O — TDD target)

```
validate_positions(raw) -> (clean_rows, warnings)        # §1 rules
merge_lots(clean_rows) -> merged_rows                     # §1 lot-merge
resolve_price(symbol, prices_json_or_None, site_stock_or_None) -> PriceInfo
  # PriceInfo = {last_price, price_as_of, price_source, prev_close_or_None}
compute_position(merged_row, price_info, layer, total_value_usd) -> position_dict  # §2
compute_aggregates(positions, cash_usd) -> aggregates_dict                          # §3
build_portfolio_return_series(positions, per_symbol_full_ret, window, min_bars)
  -> (window_vals: list[float], dates: list[str], included: list[symbol], coverage_pct)
top_pairwise_correlation(included_symbols_by_weight_desc, per_symbol_full_ret, top_n,
                          window, min_bars) -> {"a","b","value"} | None
compute_risk(positions, per_symbol_full_ret, spy_full_ret, rf_annual, args) -> risk_dict  # §4
```

### `scripts/build_portfolio.py` (CLI, network-free assembly — mirrors `build_risk.py`)

Reads `data/portfolio/positions.json` (default `--positions`), `web/public/data/site.json`,
`web/public/data/prices/*.json`, optional `web/public/data/graph_analysis.json` (rf rate).
Writes **`web/data/portfolio.json`** (default `--out`, note: *not* `web/public/data/`).
Same `_load_json`/`_utc_now`/`validate_bundle` dirty-string-walker helpers as
`build_risk.py` (copy, don't cross-import — same "not a shared-library target" convention
`build_risk.py` already documents). `pathlib.Path(...).exists()` guard on the positions
file produces the empty-state bundle (§5) and **exits 0** — a normal, expected state on a
fresh clone or CI, not a pipeline failure.

```
usage: build_portfolio.py [--positions data/portfolio/positions.json]
                           [--data web/public/data] [--out web/data/portfolio.json]
                           [--rf-annual 0.04] [--window 252] [--min-bars 60]
                           [--top-n-correlation 5]
```

Before writing, `pathlib.Path("web/data").mkdir(parents=True, exist_ok=True)` — unlike
`web/public/data`, `web/data/` won't already exist on a fresh clone.

### `scripts/refresh_daily.py` hook

Guarded exactly like the existing `build_risk.py`/`build_archetypes.py` hooks — added to
`build_plan()` right after the archetypes step (needs `site.json` + `prices/` fresh):

```python
if os.path.exists(str(SCRIPTS / "build_portfolio.py")):
    add("compute portfolio -> web/data/portfolio.json", [PY, "build_portfolio.py"])
```

No guard on `data/portfolio/positions.json` — the script degrades gracefully (§1/§5), so
the hook only checks the *script* exists, consistent with every other guarded step.

### `data/portfolio/positions.example.json` (committed template)

```json
{
  "base_currency": "USD",
  "cash_usd": 0.0,
  "positions": [
    {
      "symbol": "NVDA",
      "quantity": 10,
      "cost_basis_per_share": 450.00,
      "acquired_date": "2024-06-01",
      "note": "example row — delete and replace with your real positions"
    }
  ]
}
```

### `data/portfolio/README.md` (committed)

Short instructions: `cp positions.example.json positions.json`, edit fields per §1's
table, run `python build_portfolio.py` (or the daily refresh), output lands at
`web/data/portfolio.json` (never `public/`, never committed, never gate-bypassable).

---

## 7. Module plan — web (Next.js) — UI design

Design B (UI) was not usable; this section is the merged authority for the web side,
built from the actual Round 1–4 conventions already in the repo (`lib/risk.ts`,
`app/terminal/risk/page.tsx`, `app/terminal/card/risk/page.tsx`,
`components/terminal/{TerminalSubNav,CardScaleShell,CaptureChromeStrip,RiskCaptureCard}`).

### `web/lib/portfolio.ts` (server-only reader, mirrors `lib/risk.ts`)

```ts
const file = path.join(process.cwd(), "data", "portfolio.json"); // NOT "public/data"
```

- `PortfolioData`, `PortfolioPosition`, `PortfolioAggregates`, `PortfolioLayerExposure`,
  `PortfolioConcentration`, `PortfolioRisk`, `PortfolioSeriesCoverage` TS interfaces
  mirroring the §5 JSON contract **verbatim** (same discipline as `RiskData` in
  `lib/risk.ts`: no renamed fields, no invented envelope objects).
- `getPortfolioData(): PortfolioData | null` — existsSync-guarded on
  `web/data/portfolio.json`, try/catch JSON.parse, module-singleton cache (`cachedPortfolio`
  / `portfolioLoaded`), never throws. Returns `null` only when the file itself is absent
  or unparseable (script never run). When the file exists but encodes the empty-state
  bundle (`positions_source.found === false`), it is returned as-is — the page
  distinguishes "never run" (`null` → generic "not generated yet" message, same as every
  other desk) from "run, no positions yet" (`found: false` → the specific
  copy-the-template message, sourced from `data.warnings[0]`).
- No extra derived helpers needed beyond the plain reader — all aggregation already
  happened in Python; the page renders the bundle directly (simplicity first).

### `/terminal/portfolio` page (`web/app/terminal/portfolio/page.tsx`)

`export const dynamic = "force-dynamic"` (same reasoning as every other desk: the file is
gitignored/owner-generated, may not exist at build time). Add
`{ href: "/terminal/portfolio", label: "PORTFOLIO" }` to `TerminalSubNav`'s `SUB_NAV`
array (5th tab, after ARCHETYPES) — this is the only proxy-adjacent change, and it's a
label addition, not a matcher/gate change (the existing `matcher: ["/terminal/:path*"]`
already covers `/terminal/portfolio` and `/terminal/card/portfolio`).

Layout, top to bottom, following the risk-desk page's structure:

1. `TerminalSubNav currentPath="/terminal/portfolio"` + header row (title, `Updated
   {generated_at}`, `Capture card →` link to `/terminal/card/portfolio`).
2. Empty state (no `getPortfolioData()` result, or `found === false`): bordered panel,
   *"No positions file yet — copy `data/portfolio/positions.example.json` to
   `data/portfolio/positions.json` and edit it with your holdings."* — reuses the exact
   `warnings[0]` string from the empty-state bundle so the message is defined once, in
   Python, not duplicated in TSX copy.
3. Amber NFA banner (same convention as risk desk): *"Historical risk measures
   (volatility, VaR, Sharpe, beta, correlation) are backward-looking, computed on a
   fixed-weight proxy series (see methodology note below), and do not predict future
   losses. Not investment advice."*
4. **Summary strip** — 4 stat tiles: `total_value_usd`, `day_pnl_usd` (+ `day_pnl_pct`),
   `total_unrealized_pnl_usd` (+ `total_unrealized_pnl_pct`), `cash_usd` (+
   `cash_weight_pct`). Dollar amounts render here — this page is behind the gate.
5. **`PortfolioLayerMix`** component — horizontal 100%-stacked bar of `layer_exposure[]`
   by `weight_pct`, using the existing layer color convention from `lib/format.ts`
   (`layerLabel`, and whatever layer color scale `RiskLayerStrip`/`RiskStackHeatmap`
   already use — reuse, don't invent a new palette) plus a distinct neutral swatch for
   `cash`. Percent-only labels on the bar itself; a legend row underneath may show
   `market_value_usd` per bucket since this is the gated page.
6. **`PortfolioHoldingsTable`** component — one row per `positions[]` entry: symbol
   (+ `(N lots)` suffix when `lots_merged > 1`), layer badge, quantity, last price
   (+ `price_as_of`, greyed if `price_source === "site_json_fallback"`), market value,
   weight %, cost basis, unrealized P&L $ and %, day change $ and %. Null cells render
   the shared `DASH` constant from `lib/format.ts` (same convention as every other
   table in this codebase). Unpriced rows (unknown symbol) render with a muted/dashed
   row style and a small "unpriced" tag instead of the numeric columns.
7. **Concentration + risk panel** — `top1_weight_pct`/`top3_weight_pct`/`hhi` as three
   small stat tiles, then `risk.*` (vol/VaR/Sharpe/beta/max_pairwise_correlation) as a
   second row of stat tiles, all `DASH` when `risk` is `null`. The
   `risk.methodology_note` renders verbatim in a muted callout directly under this panel
   — not paraphrased, not omitted (the fixed-weight simplification is mandatory
   visible copy, not just JSON payload). `series_coverage.weight_coverage_pct` shown
   inline (`"risk series covers 100% of invested value"` / the `<80%` warning string).
8. Non-dollar `warnings[]` and `positions[].warnings[]` render as a flat `⚠` list (same
   style as risk desk's `data.warnings`), dollar warnings included since this page is
   gated.
9. Footer disclaimer paragraph, same convention as every other desk.

No new client-side interactivity is required for v1 (no sorting/filtering) — simplicity
first; the table is a static server-rendered list ordered by `weight_pct` descending,
cash-and-unpriced rows last.

### `/terminal/card/portfolio` (`web/app/terminal/card/portfolio/page.tsx`)

Mirrors `app/terminal/card/risk/page.tsx` exactly: `force-dynamic`, `notFound()` when
`getPortfolioData()` is `null` **or** `found === false` (an empty-state bundle has
nothing shareable — a 404 here is the correct, loud failure for the capture script to
catch, never a broken/empty screenshot), `?capture=1` branch renders
`<CaptureChromeStrip />` + bare `<PortfolioCaptureCard data={...} />`, else wraps in
`<CardScaleShell>` for on-screen phone preview.

### `PortfolioCaptureCard` (`web/components/terminal/PortfolioCaptureCard.tsx`)

Same construction discipline as `RiskCaptureCard`: 1080×1350, `id="capture-canvas"`,
`data-capture-ready="true"`, all-px inline styles, no client JS, brand header (`AI·STACK
TERMINAL`), NFA footer rendered unconditionally.

**Privacy enforcement, concretely:** the component's prop type is declared narrower than
`PortfolioData` — a hand-picked `PortfolioCardData` type that structurally omits every
`*_usd` field, so a future accidental `data={fullPortfolioData}` wire-up fails to
typecheck rather than silently leaking a dollar figure onto a screenshot:

```ts
export interface PortfolioCardData {
  generated_at: string;
  layer_exposure: { layer: string; weight_pct: number }[];   // no market_value_usd
  total_unrealized_pnl_pct: number | null;
  day_pnl_pct: number | null;
  concentration: { top1_weight_pct: number | null; top3_weight_pct: number | null; hhi: number | null };
  risk: {
    vol_annualized_pct: number | null;
    var95_1d_pct: number | null;
    sharpe_1y: number | null;
    beta_vs_spy: number | null;
  } | null;
  n_positions: number;
}

function toCardData(data: PortfolioData): PortfolioCardData { /* explicit field-by-field pick, never a spread */ }
```

The page component calls `toCardData(data)` before handing props to
`PortfolioCaptureCard` — the transform lives in the page (or a small `lib/portfolio.ts`
helper), not inside the card component, so the card component itself is structurally
incapable of receiving a dollar field even if the caller tried.

Card content (all percentages/ratios, no `$`):
1. Brand + eyebrow (`● PORTFOLIO SNAPSHOT`), title "PORTFOLIO".
2. Layer-mix mini bar (reuse the `layer_exposure[].weight_pct` values, same color
   convention as the page's `PortfolioLayerMix`, percent labels only).
3. 3 headline stat blocks: Day P&L % (`day_pnl_pct`), Total Unrealized P&L %
   (`total_unrealized_pnl_pct`), Top-3 Concentration % (`concentration.top3_weight_pct`).
4. Small risk row: Vol (annualized %), VaR95 1-day %, Sharpe, Beta vs SPY — `DASH` when
   `risk` is `null`, plus one-line note "fixed-weight proxy — see terminal for
   methodology" (short form of §4's mandatory note; the full note is page-only copy,
   too long for a card).
5. Footer: `generated_at` (humanized, UTC) + `portfolio-v1` + mandatory NFA line.

### `TerminalSubNav` change

Add one entry to the existing `SUB_NAV` array (`web/components/terminal/TerminalSubNav.tsx`):

```ts
const SUB_NAV = [
  { href: "/terminal", label: "TA DESK" },
  { href: "/terminal/risk", label: "RISK" },
  { href: "/terminal/macro", label: "MACRO" },
  { href: "/terminal/archetypes", label: "ARCHETYPES" },
  { href: "/terminal/portfolio", label: "PORTFOLIO" },
] as const;
```

No changes needed to `web/proxy.ts` — its matcher (`/terminal/:path*`) already covers
both new routes.

---

## 8. `scripts/tests/test_portfolio.py` — pytest plan (hand-computed fixtures)

**Fixture A — the 2-position + cash portfolio from §3's worked example.**

- `test_compute_position_nvda_matches_hand_calc` — mv=5500, pnl_usd=1500, pnl_pct=37.5,
  day_chg_pct=10.0, day_chg_usd=500, weight_pct≈44.4265 (total_value=12380)
- `test_compute_position_msft_matches_hand_calc` — mv=5880, pnl_usd=880, pnl_pct=17.6,
  day_chg_pct=-2.0, day_chg_usd=-120, weight_pct≈47.4959
- `test_compute_aggregates_totals` — total_value=12380, invested=11380,
  cash_weight_pct≈8.0775, total_cost_basis=9000, total_unrealized_pnl_usd=2380,
  total_unrealized_pnl_pct≈26.4444, day_pnl_usd=380, day_pnl_pct≈3.1667
- `test_compute_aggregates_concentration` — top1≈51.6696, top3=100.0, hhi≈0.50055
- `test_layer_exposure_buckets_sum_to_100` — L1-chips≈44.4265, L2-infra≈47.4959,
  cash≈8.0775, unclassified=0, `sum(weight_pct for all buckets) == pytest.approx(100)`

**Fixture B — validation rules (§1)**

- `test_validate_positions_drops_nonpositive_quantity` — `quantity: 0` and `quantity: -5`
  both dropped + warning per row
- `test_validate_positions_drops_missing_symbol`
- `test_validate_positions_keeps_row_with_missing_cost_basis` — kept, `null` cost basis,
  warning, not dropped
- `test_merge_lots_weighted_average_cost_basis` — two NVDA rows, qty 5@400 + qty 5@500 →
  merged qty=10, cost_basis_per_share = (5*400+5*500)/10 = 450.0 exactly
- `test_merge_lots_earliest_acquired_date_wins`
- `test_unknown_symbol_never_dropped` — no site.json entry, no price file → position
  present with `last_price: None`, `market_value_usd: None`, `layer: None`, warning
  present, excluded from `total_value_usd`/`weight_pct`/`layer_exposure` (aggregates
  equal Fixture A's values — the unknown symbol contributes 0 to every dollar aggregate)

**Fixture C — day-change $/% formula divergence (regression test for §2's correctness note)**

- `test_day_change_usd_uses_prev_close_not_current_market_value` — construct a case where
  `market_value_usd * day_change_pct/100 != quantity*(last-prev)` and assert the function
  returns the `quantity*(last-prev)` value, not the naive one

**Fixture D — risk-series construction (§4), invariant-based (mirrors `test_risk.py`'s
`_alternating_60()` style)**

- `test_portfolio_series_equals_shared_series_when_holdings_identical`
- `test_portfolio_series_cancels_to_zero_for_offsetting_equal_weight_holdings` — +0.01/
  -0.01 constant series, 50/50 weight → 60 zeros → `risk.sharpe_ratio` returns `None`
  (zero-variance branch — proof the glue feeds `risk.py` correctly)
- `test_beta_is_one_when_portfolio_series_equals_spy_series`
- `test_max_pairwise_correlation_is_one_for_identical_top2_holdings`
- `test_series_excludes_holding_below_min_bars` — 40-bar holding (<60) excluded from `S`,
  appears in `series_coverage.excluded` with reason `"insufficient history (40 bars, need
  >=60)"`, `weight_coverage_pct` reflects remaining weight only
- `test_weight_coverage_warning_below_80pct`
- `test_risk_block_null_when_no_holding_qualifies` — all fields `None`, one warning, no
  exception

**Fixture E — empty-state / degradation (`build_portfolio.py` integration test)**

- `test_build_portfolio_missing_positions_file_produces_empty_bundle` — `found: false`,
  `positions: []`, `aggregates`/`risk` null, one warning, exit code 0
- `test_build_portfolio_writes_to_web_data_not_public` — regression guardrail: default
  `--out` resolves under `web/data/`, never `web/public/data/`

Run with `cd scripts && python -m pytest tests/test_portfolio.py -q`.

---

## 9. Provenance / caveats summary (per CLAUDE.md §1.7)

- Every dollar figure traces to `positions_source.mtime` (owner input, hand-edited, not
  live-retrieved) crossed with `prices_source.batch_retrieved_at` (the live Yahoo pull
  powering `last_price`/returns).
- `risk.*` figures are explicitly labeled indicative/backward-looking via
  `risk.methodology_note` (mandatory, verbatim, rendered on the gated page — this is the
  fixed-weight simplification disclosure) and `series_coverage` — never presented as a
  forecast.
- Unknown symbols, missing cost basis, thin price history, and sub-80%-weight-coverage
  risk series are all surfaced as explicit warnings in the bundle and (non-dollar ones)
  on the capture card — nothing silently dropped or assumed.
- Capture card is percentage/ratio-only by construction (narrowed TS prop type, no
  dollar fields reachable) — dollar figures exist only behind the `terminal_key` gate on
  `/terminal/portfolio`.
- Educational/research only — not financial advice; this module computes descriptive
  statistics on the owner's own disclosed holdings, it does not recommend trades.
