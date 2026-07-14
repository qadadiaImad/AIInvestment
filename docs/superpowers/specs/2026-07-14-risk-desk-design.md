# AI STACK TERMINAL — `/terminal/risk` Risk Analytics Desk — Merged v1 Spec

Round 2 of the private Bloomberg-style workstation at `/terminal/*` (gate: `web/proxy.ts`,
shipped Round 1, untouched here). Merges **Design A** (data/`risk.json`, leans on already-
retrieved local files) and **Design B** (UI, Fincept-style heatmap + correlation matrix,
SPY benchmark + L3-models proxy). Lead-architect resolution below; conflicts are called out
explicitly, not silently split down the middle.

Educational/research only — not financial advice. `/terminal/*` gating is Round 1's,
unchanged by this round.

---

## 0. Resolutions (where A and B disagreed)

1. **New network calls vs. zero new network calls — the core architectural fork.**
   Design A computes `risk.json` entirely from files already on disk
   (`web/public/data/site.json` + `web/public/data/prices/<SYM>.json`, both produced by
   existing `export_site.py` / `pull_prices.py` steps in `refresh_daily.py`) — zero HTTP in
   the risk builder itself. Design B proposed a parallel `pull_risk.py` that re-fetches
   TradingView scanner + Yahoo chart data independently.
   **Resolution: Design A's architecture wins.** Two independent reasons, either one
   sufficient: (a) **sandbox caveat** — `query1.finance.yahoo.com` is egress-blocked here,
   so a second, duplicate fetch layer can't even be developed/tested against a live feed in
   this environment, only against fixtures, and fixture-driven development is exactly as
   easy against `build_risk.py` reading local JSON as it would be against a mocked
   `pull_risk.py`; (b) **CLAUDE.md's REST-first rule is about the *transport*, not about
   re-deriving data that's already been retrieved this run** — `pull_prices.py` already owns
   the Yahoo-chart-per-symbol transport and runs earlier in `refresh_daily.py`'s plan;
   standing up a second, parallel fetch path for the same tickers is duplication, not
   REST-first discipline. `build_risk.py` is therefore **network-free**, mirroring Design
   A's plan almost verbatim.
2. **SPY benchmark + L3-models proxy (Design B's best UI idea) vs. zero-new-network
   (Design A's architectural constraint) — reconciled, not dropped.** Design B's SPY row
   and hyperscaler-proxy for `L3-models` are genuinely the most useful additions on the
   correlation page ("is the AI stack more/less correlated with the broad market than with
   itself" is exactly the question a risk desk answers first) — cutting them to satisfy the
   zero-new-network rule would lose real value. **Resolution:** extend the *existing*
   `pull_prices.py` ticker list with one line, `+ ["SPY"]`, so `prices/SPY.json` exists on
   disk the same way every AI-stack symbol's price file does — same transport, same script,
   same `retrieved_at` batch stamp, zero new script, zero new architecture. `build_risk.py`
   then reads `prices/SPY.json` exactly like any other symbol; it stays network-free. SPY is
   **not** added to `site.json["stocks"]` or `per_stock[]` — it is a benchmark input only
   (used for `correlations.layers`'s 6th row/column and each stock's `beta_vs_spy`), per
   Design B's own "excluded from `stocks`" call.
   `L3-models`' correlation series is Design B's documented proxy: the equal-weighted daily
   return series of `{GOOGL, MSFT, AMZN, META}` (already counted under `L2-infra` for every
   other purpose — reused *only* for this one correlation series, never double-counted in
   `per_layer` aggregates or market-cap totals). This directly reuses Design A's own
   `layer_return_series()` function with a hardcoded proxy member list instead of
   `layers["L3-models"]` (which is `[]`) — no new mechanism, one new call site. A mandatory
   `l3_models_note` string ships next to the matrix so the approximation is never silently
   assumed.
3. **Correlation scope.** Both designs independently converged on "two matrices, not a full
   N×N" — full agreement, no conflict. Final: **layer×layer, 6×6** (5 AI-stack layers + SPY,
   per §0.2) and **top-15-by-market-cap stock×stock**. This is the same ~(6²+15²)=261-cell
   ceiling Design A sized for "tractable," now answering both designs' macro questions
   (stack-vs-market via SPY, stack-internal-structure via the 5 layers) in one block.
4. **Universe size discrepancy ("46" vs "~90").** Not a real conflict: Design A reads
   whatever's in `site.json["stocks"]` (already AI-stack-scoped by `export_site.py`), Design
   B's `ai_stack.all_tickers()` is the same underlying universe, just counted directly from
   `aiinvest/ai_stack.py`'s `LAYERS` dict instead of via the exported file. Reading
   `site.json` (Design A's approach) is authoritative because it's already-materialized on
   disk and matches every other Round-1/Round-2 data consumer's convention
   (`fs.existsSync`-guarded local read, never re-derive from Python source at request time).
   Whatever count `site.json["stocks"]` has on a given day is the risk universe that day.
5. **`day_change_pct` transport.** Design B wanted a TradingView-scanner-derived day change;
   ruled out by §0.1 (no new TradingView call). Design A's price-file-derived
   close-to-close change (Yahoo daily bars, last two bars of the series) is kept as the only
   `day_change_pct` source — cheaper, already-available, and explicitly documented as
   distinct from `site.json`'s own TradingView-snapshot day move (different source, not to
   be conflated — Design A's own callout, kept verbatim).
6. **Per-stock beta.** Design B asked for `beta_vs_spy`; Design A's module list didn't have
   one (Design A was written before SPY entered scope in its own document). Now that SPY
   price history exists on disk (§0.2), beta is a cheap pure-function addition — sample
   covariance / sample variance over the same aligned-date, same-window return pairs already
   needed for correlation. Added to `risk.py` and `per_stock` (see §2, §4). No new
   architecture.
7. **Per-layer day-change aggregate (needed for Design B's `headline.worst_layer` /
   capture-card feature, absent from Design A's `per_layer`).** Added: `day_change_pct` +
   `day_change_basis` on `per_layer`, computed with the exact same cap-weight-with-
   equal-weight-fallback machinery Design A already built for `vol_cap_weighted_pct` (one
   more application of an existing rule, not a new one).
8. **Schema field names — Design A's shape is the base** (`per_stock[]`, `per_layer[]`,
   `correlations.layers` / `correlations.top_stocks`, `source_class: "computed"`,
   `prices_source` provenance block, exhaustive `warnings[]` doctrine) because it is fully
   specified down to edge cases and already carries the repo's flattening precedent
   (`ta_desk.json`) forward correctly. Design B's genuinely additive ideas —
   `benchmark_symbol`, `l3_models_note`, a `headline` block for the capture card,
   `risk_free_source` provenance, `beta_vs_spy` — are folded in as named fields inside that
   base shape (§2). `schema_version` is `"risk-desk-v1"` (matches `pull_ta.py`'s
   `"ta-desk-v1"` naming convention over Design A's plain `"risk-v1"`).
9. **Risk-free rate.** Design A: flat CLI-configurable default (`0.04`). Design B: read
   live from `web/public/data/graph_analysis.json`'s `macro.snapshot.dff` (FRED, via an
   already-generated local file — no new network call, so it's compatible with §0.1).
   **Resolution: try the local file first (existsSync-guarded, never throws), fall back to
   the CLI default with a warning if absent.** Best of both — live when available, never a
   hard dependency.
10. **UI treemap-vs-SVG, nav placement, `/terminal/card/risk` routing.** Design B's answers
    (§0.3–0.6 of Design B, unchanged) are adopted as-is — they're UI-only decisions Design A
    never addressed, no conflict to resolve.

---

## 1. Universe & scope (final)

- **AI-stack universe**: every symbol key in `web/public/data/site.json["stocks"]` (already
  layer-tagged `L0-energy…L4-application`; `L3-models` has zero direct members — public
  exposure is proxy-only, per `aiinvest/ai_stack.py`'s own comment).
- **Benchmark**: `SPY`, fetched by the same `pull_prices.py` pass (§0.2), used only for the
  6×6 layer-correlation matrix and per-stock `beta_vs_spy` — never in `per_stock[]`, never
  ranked in `correlation_top_stocks`.
- **`L3-models` correlation proxy**: equal-weighted daily return series of
  `{GOOGL, MSFT, AMZN, META}` (bare symbols), used *only* inside
  `correlations.layers` — never affects `per_layer["L3-models"]`'s own aggregates (which
  stay `null`/`0`, "no public tickers" case) and never double-counts those four names' risk
  into two layers.
- **Correlation scope**: layer×layer (6×6: 5 layers + SPY) and top-15-by-market-cap
  stock×stock (AI-stack only, no SPY). No full N×N stock matrix — both source designs agreed
  this is the tractable, decision-useful cut.

---

## 2. Per-stock / per-layer metrics — final formulas

All formulas, `MIN_BARS = 60`, `WINDOW = 252`, VaR sign convention (positive = loss
magnitude), max-drawdown sign convention (negative), and the full edge-case table are
**Design A §1.2/§1.3, adopted verbatim** — that document is complete and rigorously
specified; restating it here would just be a lossy copy. Two additions on top of it:

### 2.1 `beta_vs_spy` (new — resolves Design B's ask)

```
beta(stock_window_returns, bench_window_returns) -> float | None
```
- Inputs: the stock's own trailing-window returns and SPY's, **aligned on common dates**
  first via the same `align_series()` helper §3 already needs for correlation, *then*
  windowed to the same trailing period.
- `beta = sample_covariance(x, y) / sample_variance(y)` (both `ddof=1`, consistent with
  `sample_stdev`).
- `None` if aligned overlap `< MIN_BARS` or `sample_variance(y) == 0`.
- Edge case additions to Design A's §1.3 table: no SPY price file / insufficient SPY history
  → `beta_vs_spy: null`, warning `"beta_vs_spy: SPY price history unavailable or
  insufficient"`. Aligned overlap `< MIN_BARS` → `null`, warning `"beta_vs_spy: insufficient
  aligned overlap with SPY (n={n}, need >={MIN_BARS})"`.

### 2.2 `per_layer.day_change_pct` (new — feeds `headline.worst_layer`)

Same cap-weight-with-fallback machinery as `vol_cap_weighted_pct` (Design A §2's rule,
applied a second time): cap-weighted mean of constituent `day_change_pct` if
`n_with_market_cap >= 2` and `>= 50%` of `n_with_metrics`, else equal-weighted mean with
`day_change_basis = "equal_weighted_fallback"` and a mirrored warning. `null` for an empty
layer (`L3-models`), same as every other `per_layer` aggregate.

---

## 3. Correlation — final method (merges A §3 + B §0.2)

**Method**: 1-year daily simple-return Pearson correlation, `pearson_correlation()` +
`align_series()` + `min_overlap_days = 60`, exactly as Design A §3.1–3.2 specifies
(including the "diagonal requires the series' own ≥60 bars, else excluded from `order[]`
entirely" rule — this is what makes an empty/thin `L3-models` proxy or a thin SPY history
degrade to "excluded + warned," never a fabricated `1.0` next to `null`s).

**`correlations.layers`** — 6×6, `order = ["L0-energy","L1-chips","L2-infra","L3-models",
"L4-application","SPY"]` (any entry individually failing the ≥60-bar diagonal check is
dropped from `order`, per the rule above — e.g. if SPY's price file is somehow absent, the
matrix degrades to 5×5 and a warning names it, never a crash). Layer series = Design A
§3.3's `layer_return_series()` (equal-weighted mean of same-day constituent returns, ≥1
contributor per date) — for `L3-models`, called with the hyperscaler proxy list instead of
`layers["L3-models"]`. SPY's own series is just its own `daily_returns()` output, no
aggregation needed. Ships `l3_models_note` (Design B's exact footnote text) alongside the
matrix, always present when `L3-models` is `null`-avoided-*or*-included (i.e. always present
— it's informational regardless of whether L3 made it into `order`).

**`correlations.top_stocks`** — Design A §3.4 verbatim: rank AI-stack stocks by
`market_cap` desc (fallback to `n_returns_window` desc + symbol asc if `<50%` of the
universe has `market_cap`), admit candidates that individually clear `MIN_BARS`, fall
through to the next-ranked candidate on a skip, stop at 15 or exhaustion.
`candidates_skipped: [{symbol, reason}]` structured log, `ranked_by` field names which
ranking was actually used. SPY is never a candidate here (§1).

---

## 4. `risk.json` — final contract

File: `web/public/data/risk.json`. Generated, **gitignored**, whole-file overwrite each run,
pretty-printed (`json.dumps(..., indent=2)`) — same convention as `ta_desk.json`. See the
`contract` field of this task's structured output for a compact 2-stock/2-layer annotated
example with every field name final. Full-shape notes:

- **`source_class: "computed"`** at top level (Design A's deliberate enum extension —
  `risk.json` performs zero new retrieval; every number is a pure function of
  already-stamped local files). `prices_source` block names the *real* underlying retrieval
  class (`"api"`, Yahoo chart, via `pull_prices.py`) so provenance isn't lost, just
  relocated — unchanged from Design A.
- **`params.risk_free_rate_annual` + `params.risk_free_source`**: read from
  `graph_analysis.json`'s `macro.snapshot.dff` if that file exists (existsSync-guarded,
  never throws) → `risk_free_source: "graph_analysis.json:macro.snapshot.dff"`; else the
  `--rf-annual` CLI default (`0.04`) → `risk_free_source: "cli-default"` + a top-level
  warning. Resolves §0.9.
- **`benchmark_symbol: "SPY"`** at top level (Design B).
- **`per_stock[]`**: Design A's fields **plus** `beta_vs_spy` (§2.1). Every symbol in
  `site.json["stocks"]` gets an entry, all-`null` if unusable — doctrine unchanged.
- **`per_layer[]`**: Design A's fields **plus** `day_change_pct` / `day_change_basis`
  (§2.2). Exactly 5 entries always, `L3-models` all-`null` except its correlation
  participation lives in a separate block (§3), not here — its "no public tickers" warning
  is unchanged from Design A.
- **`correlations.layers`**: Design A's block shape, `order` now up to 6 (incl. SPY),
  `l3_models_note` field added (Design B). `correlations.top_stocks`: Design A's block,
  unchanged.
- **`headline`** (new top-level block, Design B, cheap to assemble from already-computed
  `per_layer`/`correlations`): `worst_layer` (argmin of the 5 real layers'
  `day_change_pct`, ties broken alphabetically), `universe_var95_1d_pct` (cap-weighted mean
  of `var95_1d_pct` across the whole universe, same fallback rule as §2.2/Design A §2),
  `top_correlation_pair` (highest-absolute-value **off-diagonal** cell within
  `correlations.layers`' 5 real layers **only** — SPY intentionally excluded from this one
  pick, since "which two AI-stack layers move together most" is a different, cleaner
  question than "how correlated is a layer with the market," and conflating them in one
  headline number would bury the more interesting internal-structure signal).
- **Warnings conventions**: unchanged from Design A §4 — per-stock `"{field}: {reason}"`,
  per-layer same style, correlation blocks carry their own `warnings[]` +
  `candidates_skipped[]`, global `warnings[]` for build-wide notes, **never a silently
  dropped key**.

---

## 5. Module plan (final)

### `scripts/aiinvest/risk.py` — pure, zero I/O, zero HTTP

Design A §5's full function list, **plus**:
```python
sample_covariance(xs, ys) -> float | None   # ddof=1; None if n<2
sample_variance(xs) -> float | None         # ddof=1; None if n<2
beta(xs, ys) -> float | None                # cov(x,y)/var(y); None if n<2 or var(y)==0
```
(`sample_variance` is `sample_stdev(xs)**2` restated for direct reuse in `beta`'s
denominator without a sqrt-then-square round trip; trivial, unit-tested identically to every
other pure function in the module.)

### `scripts/pull_prices.py` — one-line extension

```python
tickers = list(dict.fromkeys(ai_stack.all_tickers() + quantum_stack.all_tickers() + ["SPY"]))
```
`SPY` needs no `EXCHANGE:` prefix — `_one()` already does `full_ticker.split(":")[-1]`, a
no-op for a bare symbol. This is the **only** change to any existing Round-1 file. No other
existing script is modified.

### `scripts/build_risk.py` — thin, network-free assembly (Design A §5's plan + SPY/proxy/beta/headline wiring)

1. Args: `--data <repo>/web/public/data`, `--out .../risk.json`, `--rf-annual 0.04`,
   `--window 252`, `--min-bars 60`, `--correlation-top-n 15`.
2. `site.json` missing → write minimal valid empty bundle (Design A §5 step 2, unchanged),
   return 0.
3. Load `site.json["stocks"]`, `site.json["layers"]`.
4. Load `graph_analysis.json` if present for `risk_free_rate_annual` / `risk_free_source`
   (§4); else CLI default + warning.
5. Load `prices/SPY.json` if present (guarded — absence degrades gracefully: no beta, no
   SPY row in `correlations.layers`, warnings say so, never a crash).
6. Per-symbol: compute `per_stock` per Design A §1 + `beta_vs_spy` per §2.1.
7. Assemble `per_layer` per Design A §2 + `day_change_pct`/`day_change_basis` per §2.2.
8. Assemble `correlations.layers` (6×6 incl. SPY + L3 hyperscaler-proxy series) and
   `correlations.top_stocks` (15×15, AI-stack only), per §3.
9. Assemble `headline` per §4.
10. Validate (Design A §5 step 7's local dirty/non-finite walker, unchanged) → write
    pretty-printed JSON → print `f"risk: {n_ok}/{n_total} symbols with metrics -> {out_path}"`
    + warnings-count line.

### `refresh_daily.py` hook

Unchanged from Design A §5's plan — guarded `os.path.exists(SCRIPTS / "build_risk.py")`
step inserted after `"export site.json"` (which now also guarantees `prices/SPY.json` is
current, since that's produced by the earlier `pull_prices.py` step in the same run).

### Tests

`scripts/tests/test_risk.py` (pure functions) = Design A §6's 15-case list for the shared
functions **plus**:
- `test_beta_known_value` — hand-computed fixture (e.g. `ys = 2*xs` → `beta == 2.0`;
  `ys` constant → `beta is None`).
- `test_sample_covariance_and_variance_known_values`.

`scripts/tests/test_build_risk.py` = Design A §6's 9-case list (16–24) **plus**:
- `test_correlation_layers_includes_spy_when_present`.
- `test_correlation_layers_degrades_when_spy_missing` — no `prices/SPY.json` → SPY absent
  from `order`, warning present, no crash.
- `test_l3_models_proxy_series_uses_hyperscaler_basket` — hand-verify the proxy series
  values against a fixture with known GOOGL/MSFT/AMZN/META returns.
- `test_beta_vs_spy_null_without_spy_history`.
- `test_per_layer_day_change_cap_weighted_and_fallback` — mirrors
  `test_per_layer_cap_weighted_fallback` (case 19) for the new field.
- `test_headline_worst_layer_and_top_correlation_pair` — fixture with a known worst-day-change
  layer and a known max-correlation layer pair; assert SPY is excluded from the
  `top_correlation_pair` pick even when it's the single highest correlation in the raw
  matrix.
- Extend case 24 (`test_contract_shape_matches_schema`) to the new final key set (`headline`,
  `benchmark_symbol`, `beta_vs_spy`, `day_change_pct`/`day_change_basis` on `per_layer`,
  `risk_free_source`, `l3_models_note`).

---

## 6. Web app — final (Design B, adopted as-is)

Design B's UI section (§1, §4–§10 of Design B) is adopted **without changes** — it was
already internally consistent, correctly scoped to "terminal-area-only" nav (CLAUDE.md's own
"don't touch global chrome" precedent), and every color/contrast/routing decision it made
(`web/lib/risk.ts`, `web/lib/format.ts` additions, `TerminalSubNav`, `RiskLayerStrip`,
`RiskStackHeatmap`/`RiskHeatmapTile`, `RiskCorrelationMatrix`, `RiskCaptureCard`, the two new
routes) is compatible with the merged data contract in §4 above — the only field-level
deltas the web side needs to absorb are:
- `RiskStock.beta_vs_spy` now genuinely sourced (Design B already speced this field on the
  TS interface; it's now backed by real data instead of a placeholder).
- `RiskLayerSummary` gains `day_change_pct` / `day_change_basis` (was already expected by
  Design B's `RiskLayerStrip`/heatmap day%-toggle; now has a concrete source).
- `correlation_layers` in `web/lib/risk.ts`'s TS type gains the `l3_models_note` field
  (Design B already had this in its sketch — now it's guaranteed present, not optional).
- `headline.top_correlation_pair` is now explicitly "layers only, SPY excluded" — the
  capture card's headline stat #3 should render as `"{a} ↔ {b}"` using layer labels
  (`layerLabel()`), never `SPY`.

No other web-side change from Design B's spec. `/terminal/risk`, `/terminal/card/risk`,
`TerminalSubNav`, the color functions in `format.ts`, and the component inventory in Design
B §5 are the binding UI spec for this round.

---

## 7. Open items (carried forward, not silently resolved)

1. `L3-models`'s correlation proxy is a real methodological approximation (Design B's own
   caveat, §10.1 of Design B) — surfaced via `l3_models_note`, not hidden. Unchanged.
2. Historical (non-parametric) VaR only in v1, no parametric/Monte-Carlo cross-check
   (Design B §10.2). Unchanged.
3. `correlation_top_stocks` (universe-wide ranking) vs. the heatmap's per-layer-normalized
   tile sizing are two different normalization scopes on the same page (Design B §10.3) —
   still needs the one-line UI caption Design B calls for.
4. Sharpe stays plain colored text, not heat-mapped (Design B §10.4) — v2 candidate.
5. **New, from this merge**: `beta_vs_spy` and `per_layer.day_change_pct` are additions
   beyond both source designs' original scope, justified in §0.6/§0.7 as cheap given SPY is
   now on disk — flagged here so a future reviewer knows they were a merge-time addition,
   not an oversight in either original design.
