# Round 4 — Investor-Archetype Scorecards (Graham / Buffett / Lynch)
### MERGED v1 SPEC — deterministic, rule-based, zero-LLM. Thresholds FINAL.

Status: binding spec, supersedes Design A (methodology) and Design B (UI) drafts. This
document reconciles both against the actual codebase (`web/lib/data.ts`,
`scripts/export_site.py`, `scripts/aiinvest/siteexport.py`, `scripts/build_risk.py`,
`web/lib/risk.ts`, `web/lib/format.ts`) — every field and convention below was verified
against source, not assumed. Divergences from A and B, and why, are called out inline.

---

## 0. Field audit (ground truth, re-verified for this merge)

Canonical per-stock shape written by `siteexport.sanitize_stock` and typed in
`web/lib/data.ts`'s `Stock` interface:

| Group | Field | Verified | Notes |
|---|---|---|---|
| `valuation` | `price`, `pe` | yes | live |
| `valuation` | `fundamental_value`, `fundamental_valuation`, `fundamental_discount_pct` | yes | **OUR** intrinsic value + live-price-vs-value discount, recomputed every `export_site.py` run (`fundamental.discount_pct(price, fval)`) — this is the correct margin-of-safety anchor |
| `valuation` | `margin_of_safety_pct` | yes, but **do not use** | passthrough of a *stale* pre-computed field from the fundamental record (`rec.get("margin_of_safety_pct")`), not resynced to today's price like `fundamental_discount_pct` is. Both designs independently picked `fundamental_discount_pct` for margin-of-safety criteria — confirmed correct, keep that choice. |
| `fundamentals` | `gross_margin`, `operating_margin`, `net_margin`, `fcf_margin`, `roe`, `roa`, `roic`, `debt_to_equity`, `current_ratio`, `ps`, `pb`, `pfcf`, `rev_growth_yoy`, `eps_growth_yoy`, `sector`, `industry` | yes | all present in `Fundamentals` TS interface, all sourced from TradingView scanner fields |
| `performance` | `perf_1y`, `perf_ytd`, `beta` | yes | unused by any archetype criterion below |
| `history` | `annualDilutedEPS`, `annualTotalRevenue`, `annualGrossProfit`, `annualNetIncome`, `annualFreeCashFlow` | yes, **but conditionally populated** | passthrough of `factsheet.history` (`siteexport.py` line 57). Populated when the stock's dossier was built via `pull_dossier.py`/`pull_congress_stocks.py`/`pull_quantum.py` (all call `aiinvest.history.fetch_history`, Yahoo fundamentals-timeseries, keyless REST — confirmed live in `history.py`'s own docstring: "Verified live: NVDA annual revenue/net income/EPS multi-year"). Absent for a stock whose dossier hasn't been (re)pulled since this feature shipped, or where Yahoo returned nothing — **must be treated as optional, not guaranteed**, same as `valuation.market_cap` below. |
| top-level | `layer`, `symbol`, `as_of` | yes | |

**One field is genuinely optional/overlay-only, with real codebase precedent for handling it
safely**: `valuation.market_cap`.

- It is **not** in the `Valuation` TS interface (checked: `price`, `pe`, `profitability`,
  and the four `fundamental_*` fields only — no `market_cap`).
- It **is** written into the raw JSON dict by `export_site.py`'s `_overlay_fresh_market()`,
  which merges the day's `tradingview_ai-stack_*.json` batch via
  `export_quantum._stock_from_record`'s `market_cap_basic → valuation.market_cap` mapping —
  but only runs if that day's batch file exists on disk.
- **Working precedent already exists in this codebase**: `build_risk.py` line 589 reads it
  defensively — `market_cap = ((srec.get("valuation") or {}).get("market_cap"))` — and
  `risk.json`'s own `RiskStock.market_cap` field is `number | null`, used for cap-weighting
  with graceful `None` fallback everywhere it's consumed. This is the established, safe
  pattern for this exact field in this exact codebase.
- **Resolution**: unlike Design B (which dropped it) and unlike Design A's slight
  over-caution, we **include** the one Lynch criterion that needs it (`room_to_grow`),
  read with the identical `.get()` chain as `build_risk.py`, `evaluable=False` when absent
  — never defaulted to pass or fail. This is not "faking a proxy field" (the excluded-field
  policy in §5); it is reusing a field the codebase already treats as a first-class,
  nullable, optional signal.

**Fields confirmed absent from the entire pipeline** (no dividend field anywhere in
`analyst.py`/`siteexport.py`/`data.ts`; no discrete Lynch-style stock-category label; no
absolute revenue-level/"adequate size" field): excluded outright, see §5. Not faked.

**Correction to Design A**: Design A's methodology doc claimed "no multi-year
earnings-history array beyond the two YoY-growth scalars" and excluded Graham's
earnings-stability test on that basis. This is **factually wrong** — `history.py` and its
callers demonstrate a real, working, multi-year `annualDilutedEPS` series. We restore an
earnings-stability criterion (G4 below), marked `evaluable=False` when the array is absent
or has fewer than 3 points — same honesty discipline as every other optional field.

---

## 1. Scoring model (final, shared by all three archetypes)

Adopts Design A's weighted/renormalized model — more rigorous than Design B's flat
pass-count, and it's what makes "never punish a stock for a data gap" actually true.
Adopts Design B's **verdict-band thresholds**, changed to match the site's one existing
health-band convention (`healthColor`/`healthTextClass` in `lib/format.ts`, already used
by risk/macro) rather than inventing a fourth threshold set — this is a correction to
Design A's own bands (`>=75/50-74/<50`), replaced with the site-canonical `>70/50-70/<50`.

```python
# per-criterion evaluation
criterion(stock) -> {
  key, label, field, comparator, unit, threshold,
  actual: float | None,
  evaluable: bool,
  pass: bool | None,   # None iff not evaluable
  weight: int,
  note: str | None,    # non-null only for G3's PB->PS fallback disclosure
}
```

**Dirty-value / evaluability rule** — reuses `build_risk.py`'s exact `_DIRTY_STRINGS` set
verbatim (do not reinvent a second list):
`{"", ".", "-", "--", "n/a", "na", "none", "null"}` (case-insensitive), plus `None`, plus
non-finite float (`nan`/`inf`) → `evaluable=False`. Multiples that are meaningless at or
below zero (`pe`, `pb`, `ps`, `pfcf`, `market_cap`, and the `pe*eps_growth_yoy` PEG ratio)
additionally require `value > 0` (or, for PEG, `eps_growth_yoy > 0`) to be evaluable — a
negative P/E is "unprofitable," not "cheap," and is scored by the dedicated
`earnings_positive`/`earnings_backed` criteria instead, never by a nonsense ratio.

**Score** (0–100), evaluable-only weighted-pass ratio:

```
evaluable = [c for c in criteria if c.evaluable]
n_pass = sum(1 for c in evaluable if c.pass)                      # simple count, for UI "n/N pass"
evaluable_weight = sum(c.weight for c in evaluable)
score = None if not evaluable else round(100 * sum(c.weight for c in evaluable if c.pass) / evaluable_weight)
```

**Verdict** — dual gate, both must pass or the result is `not_evaluable` (score `None`):

```
MIN_EVALUABLE_CRITERIA = 3
MIN_EVALUABLE_WEIGHT_PCT = 50   # of the archetype's 100-point weight budget

if n_evaluable < MIN_EVALUABLE_CRITERIA or evaluable_weight < MIN_EVALUABLE_WEIGHT_PCT:
    verdict = "not_evaluable"; score = None
elif score > 70:  verdict = "strong_fit"
elif score >= 50: verdict = "partial_fit"
else:             verdict = "poor_fit"
```

(`score > 70` / `50 <= score <= 70` / `score < 50` — byte-identical band logic to
`healthColor()`, so the web layer's existing color function can be reused unmodified;
see §7.)

**`likes[]` / `concerns[]`** — fixed sentence templates (§3–5), **no free text, no LLM**.
For each evaluable+scored criterion compute a normalized margin: `ge` →
`(actual-threshold)/abs(threshold)`; `le` → `(threshold-actual)/abs(threshold)` (guard
`threshold==0` by falling back to raw diff). `likes` = passing criteria's template
sentences sorted margin-desc (best first), `concerns` = failing criteria's sorted
margin-asc (worst first); **both capped at 3 entries** (Design B's cap — keeps a capture
card/panel bullet list bounded regardless of how many criteria an archetype has).
Not-evaluable criteria go to neither list — they produce one `warnings[]` entry each, in
the fixed format `"{archetype}.{key}: {field} unavailable — criterion skipped"`.

---

## 2. GRAHAM — Defensive Value (7 criteria, weights sum 100)

| # | key | label | field(s) | rule (FINAL) | weight |
|---|---|---|---|---|---|
| G1 | `earnings_positive` | Positive current earnings | `fundamentals.net_margin` | `net_margin > 0` | 10 |
| G2 | `moderate_pe` | Moderate P/E | `valuation.pe` | `0 < pe <= 15` | 15 |
| G3 | `moderate_value_multiple` | Moderate P/B (P/S fallback) | `fundamentals.pb`, fallback `fundamentals.ps` | `pb` evaluable → `0 < pb <= 1.5`; else `ps` evaluable → `0 < ps <= 2.0`; else not_evaluable. `note` field records which was used, e.g. `"P/B unavailable — used P/S <= 2.0"`. | 15 |
| G4 | `earnings_stability` | No loss year (trailing EPS history) | `history.annualDilutedEPS` | needs `>= 3` points: `pass` iff every point's `value > 0` | 15 |
| G5 | `current_ratio` | Financial strength (liquidity) | `fundamentals.current_ratio` | `current_ratio >= 2.0` | 15 |
| G6 | `low_leverage` | Conservative leverage | `fundamentals.debt_to_equity` | `0 <= debt_to_equity <= 0.5` | 15 |
| G7 | `margin_of_safety` | Margin of safety vs our fundamental value | `valuation.fundamental_discount_pct` | `discount_pct >= 25` | 15 |

Dropped from Design A's set: `graham_number` (P/E×P/B ≤ 22.5) — a composite of G2+G3's own
inputs, not an independent signal; cut in favor of restoring `earnings_stability`, which
uses a genuinely different field. Recorded in `methodology.graham.excluded_criteria` as a
documented simplification, not a data gap.

**Sentence templates** (exact strings, `.format(value=..., field_label=...)`):
- G1 like: `"Profitable on a trailing-twelve-month basis (net margin {value:.1f}%)."` / concern: `"Currently unprofitable (net margin {value:.1f}%) — fails Graham's earnings test."`
- G2 like: `"P/E of {value:.1f} is at or below Graham's defensive ceiling of 15."` / concern: `"P/E of {value:.1f} exceeds Graham's defensive ceiling of 15."`
- G3 like: `"{field_label} of {value:.2f} is within Graham's value-multiple cap."` / concern: `"{field_label} of {value:.2f} exceeds Graham's value-multiple cap."` (`field_label` = `"P/B"` or `"P/S"` depending which was used)
- G4 like: `"No loss year across the last {n} annual EPS reports — earnings stability."` / concern: `"At least one loss year across the last {n} annual EPS reports."`
- G5 like: `"Current ratio of {value:.2f} clears Graham's 2.0x liquidity bar."` / concern: `"Current ratio of {value:.2f} is below Graham's 2.0x liquidity bar."`
- G6 like: `"Debt/equity of {value:.2f} is conservative (<= 0.5)."` / concern: `"Debt/equity of {value:.2f} exceeds Graham's 0.5 conservative cap."`
- G7 like: `"Trading at a {value:.1f}% discount to our fundamental-value estimate — a real margin of safety."` / concern: `"Only a {value:.1f}% discount (or a premium) to our fundamental-value estimate — insufficient margin of safety."`

---

## 3. BUFFETT — Quality / Moat, "Wonderful company at a fair price" (7 criteria, sum 100)

| # | key | label | field(s) | rule (FINAL) | weight |
|---|---|---|---|---|---|
| B1 | `high_roe` | High return on equity | `fundamentals.roe` | `roe >= 15` | 20 |
| B2 | `high_roic` | High return on invested capital (moat signal) | `fundamentals.roic` | `roic >= 12` | 20 |
| B3 | `gross_margin_moat` | Gross-margin moat proxy | `fundamentals.gross_margin` | `gross_margin >= 40` | 10 |
| B4 | `operating_efficiency` | Operating margin (TTM) | `fundamentals.operating_margin` | `operating_margin >= 15` | 10 |
| B5 | `low_debt` | Conservative balance sheet | `fundamentals.debt_to_equity` | `0 <= debt_to_equity <= 1.0` | 15 |
| B6 | `fcf_yield` | FCF yield via P/FCF | `fundamentals.pfcf` | needs `pfcf > 0`: `pfcf <= 25` (⇔ FCF yield ≥ 4%) | 15 |
| B7 | `fair_price` | Not overpaying | `valuation.fundamental_discount_pct` | `discount_pct >= -10` | 10 |

B3/B4 are explicitly labeled single-period (TTM) proxies in `methodology.buffett` — the
dataset has no historical-margin series, so we say so rather than pretend the multi-year
"consistency" test Buffett actually runs.

**Sentence templates:**
- B1 like `"ROE of {value:.1f}% clears the 15% quality bar."` / concern `"ROE of {value:.1f}% is below the 15% quality bar."`
- B2 like `"ROIC of {value:.1f}% suggests durable capital efficiency (moat signal)."` / concern `"ROIC of {value:.1f}% is below the 12% moat threshold."`
- B3 like `"Gross margin of {value:.1f}% points to pricing power."` / concern `"Gross margin of {value:.1f}% is below the 40% moat-proxy bar."`
- B4 like `"Operating margin of {value:.1f}% (TTM) is solid."` / concern `"Operating margin of {value:.1f}% (TTM) is thin."`
- B5 like `"Debt/equity of {value:.2f} is within Buffett's comfort zone (<= 1.0)."` / concern `"Debt/equity of {value:.2f} exceeds Buffett's 1.0 comfort ceiling."`
- B6 like `"P/FCF of {value:.1f} implies a ~{yield:.1f}% FCF yield."` (`yield = 100/value`) / concern `"P/FCF of {value:.1f} implies a FCF yield under 4%."`
- B7 like `"Priced at or below our fundamental-value estimate ({value:+.1f}%) — not overpaying."` / concern `"Priced {value:+.1f}% vs our fundamental-value estimate — paying up beyond Buffett's comfort."`

---

## 4. LYNCH — Growth at a Reasonable Price / GARP (5 criteria, sum 100)

| # | key | label | field(s) | rule (FINAL) | weight |
|---|---|---|---|---|---|
| L1 | `peg` | PEG (P/E vs EPS growth) | `valuation.pe`, `fundamentals.eps_growth_yoy` | needs `pe>0` and `eps_growth_yoy>0`: `PEG = pe/eps_growth_yoy <= 1.5` | 25 |
| L2 | `growth_band` | Steady-grower revenue band | `fundamentals.rev_growth_yoy` | `15 <= rev_growth_yoy <= 50` | 20 |
| L3 | `avoid_hot_story` | Avoid story-stock pricing | `fundamentals.ps` | needs `ps>0`: `ps <= 10` | 20 |
| L4 | `room_to_grow` | Room to grow (market-cap band) | `valuation.market_cap` (**optional, `.get()`-chained exactly like `build_risk.py`**) | `0 < market_cap <= 200_000_000_000` ($200B) | 15 |
| L5 | `earnings_backed` | Growth is earnings-backed | `fundamentals.net_margin` | `net_margin > 0` | 20 |

L2 is a band, not a floor — under 15% is a boring stalwart by this scorecard's standard,
over 50% is flagged as probably-already-priced-in (an independent signal from L3's
price/sales check: L3 looks at *price relative to sales*, L2 at the *growth rate itself*).
L4 is `not_evaluable`, never defaulted pass/fail, whenever the overlay batch hasn't merged
`market_cap` in for that run.

**Sentence templates:**
- L1 like `"PEG of {value:.2f} is at or below Lynch's 1.5 GARP threshold."` / concern `"PEG of {value:.2f} exceeds Lynch's 1.5 GARP threshold."`
- L2 like `"Revenue growth of {value:.1f}% is in Lynch's steady-grower band (15-50%)."` / concern `"Revenue growth of {value:.1f}% is outside Lynch's 15-50% steady-grower band."`
- L3 like `"P/S of {value:.1f} is not priced like a hot story (<= 10)."` / concern `"P/S of {value:.1f} is priced like a hot story (> 10) — Lynch would be wary."`
- L4 like `"Market cap of ${value:,.0f} still leaves room to grow (<= $200B)."` / concern `"Market cap of ${value:,.0f} is mega-cap territory — limited room left to multiply."`
- L5 like `"Growth is earnings-backed (net margin {value:.1f}%)."` / concern `"Unprofitable on a net-margin basis ({value:.1f}%) — growth isn't earnings-backed yet."`

---

## 5. Explicitly excluded classic criteria (say-so, not fake proxies)

Recorded verbatim in `methodology.<archetype>.excluded_criteria[]`:

- **Graham**: "20-year uninterrupted dividend record" — no dividend field anywhere in the
  schema (checked `analyst.py`, `siteexport.py`, `data.ts`). "Graham Number (P/E×P/B ≤
  22.5)" — a composite of already-scored G2/G3 inputs, cut for independence, not data
  absence. "Adequate size" (Graham-era revenue floor) — no absolute revenue-level field;
  `market_cap` exists but is optional/overlay-only and is deliberately reserved for Lynch's
  room-to-grow band instead of duplicated here.
- **Buffett**: "Consistent (multi-year) margins/ROE" — only a TTM snapshot is available;
  B2/B3/B4 are labeled single-period proxies, not the real multi-year test.
- **Lynch**: "Category classification" (fast grower / stalwart / cyclical / turnaround /
  asset play) — itself a qualitative judgment Lynch made narratively; the quantitative
  stand-in (growth-rate band, L2) is used instead of inventing a discrete label.

---

## 6. `archetypes.json` schema

Top-level conventions match `risk.json`'s established shape exactly (`schema_version`,
`source_class="computed"`, `disclaimer`, `warnings[]`) — verified against
`web/public/data/risk.json` and `build_risk.py`, not guessed.

```jsonc
{
  "schema_version": "archetypes-v1",
  "methodology_version": "graham-buffett-lynch-v1.0",
  "generated_at": "2026-07-15T00:00:00Z",
  "source_class": "computed",
  "disclaimer": "Rule-based scorecard — not a prediction, not investment advice. Deterministic checklist against public fundamentals, not an opinion about what Graham/Buffett/Lynch would actually say about a name today.",
  "source": { "name": "site.json", "path": "web/public/data/site.json", "generated_at": "<site.json's own generated_at, passed through>" },
  "min_evaluable_criteria": 3,
  "min_evaluable_weight_pct": 50,
  "universe": { "n_symbols": 46, "layers": ["L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"] },
  "methodology": {
    "graham":  { "name": "Graham — Defensive Value",        "criteria": [ /* 7 static rows: key,label,field,comparator,unit,threshold,weight,note */ ], "excluded_criteria": ["20-year dividend record (no dividend field)", "Graham Number P/E x P/B (composite of already-scored P/E and P/B criteria)", "adequate size (no revenue-level field; market cap reserved for Lynch)"] },
    "buffett": { "name": "Buffett — Quality Moat",           "criteria": [ /* 7 rows */ ], "excluded_criteria": ["multi-year margin/ROE consistency (only TTM snapshot available; B2-B4 labeled single-period proxies)"] },
    "lynch":   { "name": "Lynch — Growth at a Reasonable Price", "criteria": [ /* 5 rows */ ], "excluded_criteria": ["category classification fast-grower/stalwart/cyclical/turnaround/asset-play (qualitative judgment; growth-rate band L2 used as quantitative stand-in)"] }
  },
  "per_stock": [
    {
      "symbol": "NVDA",
      "layer": "L1-chips",
      "as_of": "2026-07-14",
      "archetypes": {
        "graham": {
          "score": 43,
          "verdict": "poor_fit",
          "n_pass": 3,
          "n_evaluable": 7,
          "n_total": 7,
          "evaluable_weight_pct": 100,
          "criteria": [
            {"key": "earnings_positive", "label": "Positive current earnings", "field": "fundamentals.net_margin", "comparator": "gt", "unit": "pct", "threshold": 0, "actual": 55.8, "evaluable": true, "pass": true, "weight": 10, "note": null},
            {"key": "moderate_pe", "label": "Moderate P/E", "field": "valuation.pe", "comparator": "le", "unit": "x", "threshold": 15, "actual": 46.2, "evaluable": true, "pass": false, "weight": 15, "note": null},
            {"key": "moderate_value_multiple", "label": "Moderate P/B (P/S fallback)", "field": "fundamentals.pb", "comparator": "le", "unit": "x", "threshold": 1.5, "actual": 28.4, "evaluable": true, "pass": false, "weight": 15, "note": null}
            /* ... 4 more criteria (earnings_stability, current_ratio, low_leverage, margin_of_safety) ... */
          ],
          "likes": ["Profitable on a trailing-twelve-month basis (net margin 55.8%)."],
          "concerns": ["P/E of 46.2 exceeds Graham's defensive ceiling of 15.", "P/B of 28.4 exceeds Graham's value-multiple cap."]
        },
        "buffett": {
          "score": 88, "verdict": "strong_fit", "n_pass": 6, "n_evaluable": 7, "n_total": 7, "evaluable_weight_pct": 100,
          "criteria": [
            {"key": "high_roe", "label": "High return on equity", "field": "fundamentals.roe", "comparator": "ge", "unit": "pct", "threshold": 15, "actual": 91.4, "evaluable": true, "pass": true, "weight": 20, "note": null}
            /* ... 6 more ... */
          ],
          "likes": ["ROE of 91.4% clears the 15% quality bar."],
          "concerns": []
        },
        "lynch": {
          "score": 40, "verdict": "poor_fit", "n_pass": 2, "n_evaluable": 4, "n_total": 5, "evaluable_weight_pct": 85,
          "criteria": [
            {"key": "peg", "label": "PEG (P/E vs EPS growth)", "field": "valuation.pe", "comparator": "le", "unit": "num", "threshold": 1.5, "actual": 1.9, "evaluable": true, "pass": false, "weight": 25, "note": null},
            {"key": "room_to_grow", "label": "Room to grow (market-cap band)", "field": "valuation.market_cap", "comparator": "le", "unit": "num", "threshold": 200000000000, "actual": null, "evaluable": false, "pass": null, "weight": 15, "note": null}
            /* ... 3 more ... */
          ],
          "likes": [],
          "concerns": ["PEG of 1.90 exceeds Lynch's 1.5 GARP threshold."]
        }
      },
      "warnings": ["lynch.room_to_grow: valuation.market_cap unavailable (overlay batch not yet merged) — criterion skipped"]
    }
  ],
  "top": {
    "graham":  [{"symbol": "AVGO", "score": 91}, /* top 15, strong/partial only, score desc, ties -> symbol asc */],
    "buffett": [ /* ... */ ],
    "lynch":   [ /* ... */ ]
  },
  "counts": {
    "graham":  {"strong_fit": 4, "partial_fit": 12, "poor_fit": 20, "not_evaluable": 3},
    "buffett": {"strong_fit": 6, "partial_fit": 15, "poor_fit": 17, "not_evaluable": 1},
    "lynch":   {"strong_fit": 3, "partial_fit": 10, "poor_fit": 22, "not_evaluable": 4}
  },
  "warnings": []
}
```

`comparator` values used: `"gt"` (G1/G7's `>` , L5's `>`), `"ge"` (≥), `"le"` (≤). `unit`
dispatches UI formatting: `"x"` (ratio, 1dp), `"pct"` (percentage, 1dp), `"num"` (plain
number — PEG, market cap).

---

## 7. Module plan

### `scripts/aiinvest/archetypes.py` — pure rules, no I/O, no network
Mirrors `aiinvest/risk.py`'s shape.

```python
_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}  # verbatim from build_risk.py

CRITERIA = {"graham": [...], "buffett": [...], "lynch": [...]}      # static metadata, §2-4

MIN_EVALUABLE_CRITERIA = 3
MIN_EVALUABLE_WEIGHT_PCT = 50

def _is_valid_number(v, positive=False): ...   # dirty-value + finite + optional >0 gate
def _extract(stock, field_path): ...            # dotted-path getter, e.g. "fundamentals.roe"

def evaluate_criterion(stock, spec) -> dict: ...            # one criterion row, §6 shape
def score_archetype(criteria_results) -> tuple[int|None, str]: ...   # (score, verdict), §1
def likes_and_concerns(archetype_key, criteria_results) -> tuple[list[str], list[str], list[str]]: ...  # (likes, concerns, warnings)
def evaluate_stock(stock: dict) -> dict: ...     # {archetypes: {...}, warnings: [...]}
def build_archetypes(site: dict, generated_at: str) -> dict: ...     # full bundle, §6
```

### `scripts/build_archetypes.py` — CLI, does the I/O
Mirrors `build_risk.py`: `NETWORK-FREE`, reads `web/public/data/site.json` (only input),
writes `web/public/data/archetypes.json`, `source_class="computed"` — zero new retrieval,
every input number was already stamped upstream; this stage adds `methodology_version`,
not a new fact.

```
Usage:
    python build_archetypes.py
    python build_archetypes.py --site /tmp/site.json --out /tmp/archetypes.json
```

Guard: missing/unparseable `site.json` → print error, exit 1, **do not write** a bundle
claiming scores it couldn't compute (same pattern as `build_risk.py`'s abort-on-`None`).

### `refresh_daily.py` hook
Insert right after the risk hook (both are pure "computed from `site.json`" steps; order
between them doesn't matter):

```python
if os.path.exists(str(SCRIPTS / "build_risk.py")):
    add("compute risk analytics -> risk.json", [PY, "build_risk.py"])

if os.path.exists(str(SCRIPTS / "build_archetypes.py")):
    add("compute investor-archetype scorecards -> archetypes.json", [PY, "build_archetypes.py"])

if os.path.exists(str(SCRIPTS / "pull_macro.py")):
    add("pull macro dashboard -> macro.json", [PY, "pull_macro.py"])
```

### Web reader — target shape for the next round (not built this round)
`web/lib/archetypes.ts` mirrors `getRiskData()`: `existsSync`-guarded, try/catch
`JSON.parse`, module-singleton cache, never throws.

```ts
export type ArchetypeKey = "graham" | "buffett" | "lynch";
export type Comparator = "gt" | "ge" | "le";
export type CriterionUnit = "x" | "pct" | "num";

export interface ArchetypeCriterion {
  key: string; label: string; field: string;
  comparator: Comparator; unit: CriterionUnit;
  threshold: number; actual: number | null;
  evaluable: boolean; pass: boolean | null;
  weight: number; note: string | null;
}
export interface ArchetypeScorecard {
  score: number | null; verdict: "strong_fit" | "partial_fit" | "poor_fit" | "not_evaluable";
  n_pass: number; n_evaluable: number; n_total: number; evaluable_weight_pct: number;
  criteria: ArchetypeCriterion[]; likes: string[]; concerns: string[];
}
export interface ArchetypeStockRecord {
  symbol: string; layer: string; as_of: string | null;
  archetypes: Record<ArchetypeKey, ArchetypeScorecard>;
  warnings: string[];
}
export interface ArchetypeData {
  schema_version: string; methodology_version: string; generated_at: string;
  source_class: string; disclaimer: string;
  source: { name: string; path: string; generated_at: string | null };
  min_evaluable_criteria: number; min_evaluable_weight_pct: number;
  universe: { n_symbols: number; layers: string[] };
  methodology: Record<ArchetypeKey, { name: string; criteria: unknown[]; excluded_criteria: string[] }>;
  per_stock: ArchetypeStockRecord[];
  top: Record<ArchetypeKey, { symbol: string; score: number }[]>;
  counts: Record<ArchetypeKey, Record<"strong_fit" | "partial_fit" | "poor_fit" | "not_evaluable", number>>;
  warnings: string[];
}

export function getArchetypeData(): ArchetypeData | null { /* ... */ }
export function getArchetypeForSymbol(symbol: string): ArchetypeStockRecord | null { /* case-insensitive lookup */ }
export function getArchetypeRows(): ArchetypeStockRecord[] { /* data?.per_stock ?? [] */ }
export function getArchetypeTopN(archetype: ArchetypeKey, n = 5): { symbol: string; score: number }[] { /* data?.top[archetype].slice(0, n) ?? [] */ }
```

`lib/format.ts` additions for the eventual UI: `ARCHETYPE_ORDER/LABELS/SUBTITLES/COLORS`,
`archetypeScoreColor`/`archetypeScoreTextClass` (thin wrappers over `healthColor`/
`healthTextClass` — **do not invent a fourth threshold set**, the backend's verdict bands
already match), `archetypeVerdictLabel`, `criterionMarkColor`/`criterionMarkGlyph`
(reusing the site's existing emerald/rose pass-fail pair), `archetypeCriterionValue(v,
unit)` (dispatches to `ratio`/`pct`/`num`), `ARCHETYPE_DISCLAIMER`. Full UI component/page
plan (panel, screener, capture card) is documented in Design B and remains the target for
the next round — not rebuilt here since this document's job is the pipeline contract.

---

## 8. Test plan — `scripts/tests/test_archetypes.py`

Hand-built fixture stocks, one field changed at a time, boundary-exact (style of
`test_risk.py`).

**Extraction / dirty-value handling**
- missing field → `evaluable=False`; dirty string (`"."`, `"n/a"`, etc.) → `evaluable=False`, not a crash; `nan`/`inf` → `evaluable=False`; negative multiple (`pe=-5.0`) → `evaluable=False` for `moderate_pe`, not "cheap".

**Graham boundaries**
- G1: `net_margin=0.0` fail, `0.01` pass.
- G2: `pe=15.0` pass, `15.01` fail.
- G3: `pb` absent + `ps=2.0` → pass via fallback, `note` names it; both present, `pb=1.6` fail / `ps=1.0` would-pass → uses `pb`, fails.
- G4: `annualDilutedEPS` with 2 points → `not_evaluable`; 3 points all `>0` → pass; one point `<=0` → fail.
- G5: `current_ratio=2.0` pass, `1.99` fail.
- G6: `debt_to_equity=0.5` pass, `0.51` fail, `0.0` pass (no debt).
- G7: `discount_pct=25.0` pass, `24.99` fail, `-5.0` fail.

**Buffett boundaries** — B1–B4 each `>=` threshold edge-pass/edge-minus-epsilon-fail; B5 `1.0` pass/`1.01` fail; B6 `pfcf=-10.0` → `not_evaluable` (never scored as fail), `pfcf=25.0` pass/`25.01` fail; B7 `discount_pct=-10.0` pass/`-10.01` fail.

**Lynch boundaries** — L1 `eps_growth_yoy=-5.0` → `not_evaluable`; `pe=15.0, eps_growth_yoy=10.0` → PEG 1.5 pass; `pe=15.15` → PEG 1.515 fail. L2 `14.99` fail/`15.0` pass/`50.0` pass/`50.01` fail. L3 `10.0` pass/`10.01` fail. L4 `market_cap` absent → `not_evaluable`, doesn't affect other criteria; `200_000_000_000` pass/`200_000_000_001` fail. L5 `net_margin=0.0` fail/`0.01` pass.

**Scoring / verdict** — hand-computed weighted average for a known pass/fail mix;
renormalization when a criterion is missing (denominator excludes its weight, doesn't
dilute the score); band edges `71→strong_fit`, `70→partial_fit`, `50→partial_fit`,
`49→poor_fit`; only-2-evaluable (even high-weight) → `not_evaluable`; 4 evaluable but
`< 50%` of weight → `not_evaluable`; all-pass → `score=100`; all-fail-but-evaluable →
`score=0`, `verdict=poor_fit` (evaluability ≠ passing).

**likes/concerns** — exact string match (not substring) against templates for one pass +
one fail case per archetype; margin-sort order verified with 4+ failing criteria (worst
margin first); cap-at-3 verified with an archetype that has >3 failures; not-evaluable
criterion appears in neither list, produces the exact `warnings[]` wording.

**`build_archetypes` bundle assembly** — top-level key shape; `excluded_criteria`
non-empty per archetype; `top` list sorts desc with symbol-asc tie-break and excludes
`not_evaluable`; `counts` sums to `len(per_stock)` per archetype.

**CLI wiring (`test_build_archetypes.py`, mirrors `test_build_risk.py`)** — missing
`site.json` → exit 1, no output written; valid temp fixture → output round-trips through
`evaluate_stock` for a known symbol.

**`refresh_daily.py` hook** — step present when `build_archetypes.py` exists on disk
(temp-dir monkeypatch of `SCRIPTS`, same technique as existing risk/macro hook tests),
absent → step list unchanged (`existsSync`-style degradation).

---

## 9. House-rule compliance notes

- **Stamp everything**: `generated_at` + `source.generated_at` (passthrough from
  `site.json`, so a stale scorecard traces to a stale upstream pull) + top-level
  `source_class: "computed"`, identical convention to `risk.json`.
- **Rule-based, not predictive**: top-level `disclaimer` says so explicitly; every
  `methodology.<archetype>` documents `excluded_criteria` so nothing is silently dropped.
- **NFA**: same disclaimer family as `export_site.py`'s `DISCLAIMER` / `build_risk.py`'s.
- **existsSync degradation**: `refresh_daily.py`'s `os.path.exists` gate (present today,
  reused verbatim) and the eventual `archetypes.ts` reader (documented in §7, next round)
  both degrade absence to `null`, never a crash — matching `risk.ts`/`macro.ts`/`news.ts`.
- **No LLM anywhere**: `archetypes.py` is arithmetic + a static string-template lookup,
  testable byte-for-byte (§8's exact-string-match tests keep it that way as the codebase
  evolves).
- **Field-verification discipline**: every field cited above was checked against
  `web/lib/data.ts`, `scripts/aiinvest/siteexport.py`, `scripts/export_site.py`,
  `scripts/aiinvest/history.py`, and `scripts/build_risk.py`'s existing `market_cap`
  handling before being admitted into a threshold rule — nothing here was guessed from
  Design A's or Design B's prose alone.

---

## Addendum (shipped same round): UI surfaces

Contrary to §7's "next round" note, the UI layer shipped in the same round under
the orchestrator's build brief, using the established terminal patterns as its
spec-by-precedent (RiskCaptureCard/MacroPanel conventions):
- `ArchetypePanel` on `/stocks/[symbol]` (renders nothing when archetypes.json
  or the symbol is absent — never a broken shell).
- `/terminal/archetypes` screener (sortable per-archetype scores, layer chips).
- `/terminal/card/archetype/[symbol]` 4:5 capture card (bundle `generated_at`
  stamp + underlying `as_of`, NFA footer, `?capture=1` chrome strip).
- Verdict colors reuse `lib/format.ts` health bands (single source).

Also fixed this round (integration finding): the ROOT layout must stay static —
`?capture=1` chrome-stripping moved from a root-layout `headers()` call to the
per-card-page `<CaptureChromeStrip />` global style; the layout `headers()` call
was making every SSG route dynamic and turning `/stocks/[symbol]` 404s into 500s.
