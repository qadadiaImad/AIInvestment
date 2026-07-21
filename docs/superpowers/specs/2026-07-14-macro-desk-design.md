# AI STACK TERMINAL — `/terminal/macro` Macro Desk — Merged Design (Round 3, v1)

> Lead-architect merge of DESIGN A (macro-data-designer) and DESIGN B (macro-UI-designer).
> This document is the single binding spec. Field names below are **FINAL** — do not
> rename in implementation. Where A and B disagreed, the resolution and reasoning is
> recorded inline so neither sub-agent's work is silently discarded.

Educational / research only — not financial advice. Regime labels are rule-based
descriptive flags, not predictions.

---

## 0. What changed in the merge (resolution log)

| Question | A said | B said | **Resolved** | Why |
|---|---|---|---|---|
| Series count | 8, keyless FRED, capped deliberately at 8/~10 | 14 (suggestion only, "owner's puller decides final list") | **A's 8**, unchanged | A's set is already fully TDD-planned (13 pytest cases, hand-computed fixtures); B's extra 6 (SOFR, T10YIE, PCEPI, RRPONTSYD, M2SL, DCOILWTICO, DHHNGSP) have zero test coverage in either doc and would blow past the repo's own "cap at ~10" note. Nothing stops a Round 4 from adding a WTI/NATGAS energy series later — v1 ships lean. |
| Category grouping | 5 lowercase categories (rates/inflation/liquidity/volatility/energy) | 4 uppercase UI groups (RATES/INFLATION/LIQUIDITY_VOL/ENERGY) | **B's 4 groups** | 4 groups map 1:1 onto the 4 regime chips (curve/real_rate/liquidity/vix) — cleaner grid, cleaner regime strip. `VIXCLS` and `WALCL` both sit in `LIQUIDITY_VOL`. |
| Per-series JSON shape | Nested (`latest: {date,value}`, `previous: {...}`, `change: {abs,pct}`) | Flat scalars (`last`, `previous`, `change_abs`, `change_pct`, `as_of`) | **B's flat scalars** | Matches the *established repo convention* verbatim: `TaPrice` in `web/lib/ta.ts` and every field in `RiskStock`/`RiskLayer` (`web/lib/risk.ts`) are flat scalars, never `{date,value}` envelopes. Consistency with `ta_desk.json`/`risk.json` beats either sub-design's local preference. |
| Sparkline point shape | `{date, value}`, key `history` | `{t, v}`, key `sparkline` | **B's `{t,v}` / `sparkline`** | Mirrors `TaSparklinePoint {t,c}` naming convention exactly (short keys, `t`=date). |
| Regime block shape | Object keyed by rule name (`regime.curve`, `regime.real_rate`, ...), each with bespoke fields | Uniform array of 4 chips, same shape each (`key,label,state,value,value_label,basis`) | **B's uniform chip array**, under `regime.chips[]`, plus `regime.headline` (A's composed string, kept) | A uniform array is directly `.map()`-able by `MacroRegimeStrip` with zero special-casing; A's bespoke per-key fields (`nominal_10y`, `cpi_yoy`, `pct_change_91d`) are folded into the chip's `basis` string instead of separate fields, keeping the array uniform. |
| Regime **thresholds & state vocabulary** | Fully spelled out, hand-computed pytest fixtures (curve inverted/flat/normal, real_rate restrictive/neutral/accommodative, liquidity expanding/flat/contracting, vix complacent/normal/elevated/stressed) | Sketch only (steep/flat/inverted; different liquidity/vol vocab: draining/stable/calm) | **A's thresholds and vocabulary, verbatim** | Per the task framing ("regime rules final") — A is the rules-of-record; A also ships the real-rate formula using series already in the 8-series set (`DGS10 − CPI YoY`), where B's `DGS10 − T10YIE` needs a 9th series (`T10YIE`) that didn't survive the series-count resolution above. |
| Chip → color mapping | n/a (data layer didn't own color) | 3-state traffic light (steep/accommodative/expanding/calm=green; flat/neutral/stable/elevated=amber; inverted/restrictive/draining/stressed=red) | **B's traffic-light pattern, remapped onto A's vocab** — table in §4 | Translated key-by-key (A.normal↔B.steep, A.flat↔B.flat, A.contracting↔B.draining, A.complacent+A.normal↔B.calm) so the visual language B designed survives with A's final state names. |
| `WALCL` units | Raw `$M` (FRED native), never silently rescaled | Displays as `$___B` | **Store raw `$M` (A), rescale only in the web formatter (B)** | Keeps "never fabricate/rescale a stamped number" (A's doctrine) while still giving the UI a readable `$B` figure — the div-by-1000 happens in `macroValue()`, not in the JSON. |
| `T10Y2Y` vs `DGS2−DGS10` | Fetch `T10Y2Y` directly (FRED's own spread) *and* fetch `DGS2` separately for cross-validation | Compute spread from `DGS10−DGS2` at read time, no dedicated `T10Y2Y` series | **Fetch `T10Y2Y` directly as its own series card (A)**; `DGS2` stays in the set too (own card) | Both series earn their keep as independent RATES cards a trader would want to see (2Y and 10Y-2Y spread are each meaningful on their own), and the curve regime rule reads `T10Y2Y.last` directly — no derived arithmetic at regime-compute time, one less place to get sign-convention wrong. |
| History window | 365d daily/weekly, 1825d (5y) monthly | not specified | **A's windowing, unchanged** | Only A addressed sparkline sparsity on monthly series. |
| Downsample algorithm | Evenly-spaced index-pick, ~60pts, endpoints preserved | not specified | **A's algorithm, unchanged** | Only A specified it; reused verbatim. |

Series set, transforms, and regime thresholds below are **FINAL**. Field names in §2–§4 are
**FINAL**. UI component names/files in §6 are final for this round.

---

## 1. Series set (final, 8 series, keyless FRED CSV only)

All via `scripts/aiinvest/fred.py:fetch_csv(series_id)` (keyless `fredgraph.csv`, no API
key). FRED's `"."` sentinel is already mapped to `None` by `parse_fred_csv`.

| `series_id` | `symbol` | `display_name` | `group` | `frequency` | `unit` | `unit_kind` | `decimals` | `transform` | why |
|---|---|---|---|---|---|---|---|---|---|
| `DGS2` | `2Y` | 2-Year Treasury Yield | `RATES` | daily | `%` | `pct` | 2 | `level` | Short end / Fed-path proxy |
| `DGS10` | `10Y` | 10-Year Treasury Yield | `RATES` | daily | `%` | `pct` | 2 | `level` | Discount rate for every AI-capex DCF; feeds `macro_stress.py` Channel 1 |
| `DFF` | `FEDFUNDS` | Fed Funds Effective Rate | `RATES` | daily | `%` | `pct` | 2 | `level` | Cost of leveraged neocloud debt; feeds `macro_stress.py` Channel 1 & 3 |
| `T10Y2Y` | `2S10S` | 10Y–2Y Curve Spread | `RATES` | daily | `%` | `pct` | 2 | `level` | Curve regime input (§4.1) |
| `CPIAUCSL` | `CPI` | CPI, Year-over-Year | `INFLATION` | monthly | `%` | `pct` | 2 | `yoy_pct` | Real-rate regime input; Fed-path context |
| `WALCL` | `FEDBS` | Fed Total Assets (Balance Sheet) | `LIQUIDITY_VOL` | weekly | `$M` | `usd_millions` | 0 | `level` | QT/QE regime input; multiple-compression backdrop |
| `VIXCLS` | `VIX` | CBOE Volatility Index | `LIQUIDITY_VOL` | daily | `index` | `index` | 1 | `level` | Vol regime input; risk-appetite gauge for high-beta AI-stack names |
| `APU000072610` | `ELEC` | US Avg Electricity Price | `ENERGY` | monthly | `$/kWh` | `usd_small` | 3 | `level` | Layer 0 of the stack ("energy — the gatekeeper"); reused by `macro_stress.py` Channel 2 |

Fixed `series[]` order in `macro.json` = table order above. `groups` iteration order for
the UI (not stored in the JSON — matches `TA_GROUP_ORDER`/`RiskLayer` precedent of living
in `format.ts`, not the data file) = `RATES, INFLATION, LIQUIDITY_VOL, ENERGY`.

**Considered, rejected for v1:** World Bank/IMF global electricity/generation-capacity
series (annual cadence, non-keyless JSON API, would sit stale for up to 12mo beside
daily/weekly FRED series — violates Rule #1 unmarked); FRED `SOFR`, `T10YIE`, `PCEPI`,
`RRPONTSYD`, `M2SL`, `DCOILWTICO`, `DHHNGSP` (no test coverage in either source design,
would exceed the repo's own ~10-series cap note — candidates for a future round, each
individually TDD'd the same way this round's 8 were).

### 1.1 CPI YoY transform

`CPIAUCSL` is a raw index (e.g. `314.2`) — transformed to **CPI YoY %** before it ever
reaches `macro.json`. Output series keeps `series_id: "CPIAUCSL"`, `transform: "yoy_pct"`,
`unit: "%"`, `unit_kind: "pct"`.

```
yoy_pct[i] = (value[i] - value[i-~12mo]) / value[i-~12mo] * 100
```

"~12 months prior" is found by **nearest-date match within ±20 days** of
`date[i] - 365 days` (via `nearest_by_offset`, §5), not raw list-index `-12` — FRED
occasionally revises/reorders monthly rows. Rows with no valid comparator (start of
series) are **dropped**, never zero/None-filled.

---

## 2. Per-series payload (final shape)

One object per series in `series[]`. Flat scalars — no per-leaf `{date,value}` envelope
(matches `TaPrice`/`RiskStock` convention).

```jsonc
{
  "series_id": "DGS10",
  "symbol": "10Y",
  "display_name": "10-Year Treasury Yield",
  "group": "RATES",
  "frequency": "daily",
  "unit": "%",
  "unit_kind": "pct",
  "decimals": 2,
  "transform": "level",
  "last": 4.42,
  "previous": 4.39,
  "change_abs": 0.03,
  "change_pct": 0.68,
  "value_1y_ago": 4.18,
  "change_1y_pct": 5.74,
  "as_of": "2026-07-11",
  "history_window_days": 365,
  "sparkline": [{ "t": "2025-07-14", "v": 4.20 }, { "t": "2025-07-16", "v": 4.19 }],
  "retrieved_at": "2026-07-14T12:00:03Z",
  "source": "fred",
  "source_class": "api",
  "source_url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
  "warnings": []
}
```

Field notes (binding):
- `unit_kind` drives the web formatter (`macroValue()`, §6): `"pct"` → `4.42%`;
  `"usd_millions"` → raw value is FRED-native millions, the formatter divides by 1000 and
  renders `$B` (e.g. stored `7105234` → displayed `$7,105B`) — **the stamped number in
  the JSON stays raw millions, never rescaled at pull time**; `"usd_small"` → `$0.183`
  (electricity, small-decimal dollars); `"index"` → bare number (VIX).
- `history_window_days`: `365` for daily/weekly series (`DGS2`, `DGS10`, `DFF`, `T10Y2Y`,
  `VIXCLS`, `WALCL`); `1825` (5y) for monthly series (`CPIAUCSL` post-transform,
  `APU000072610`) — a 1y window on a monthly series is only ~12 points, too sparse.
- `sparkline`: downsampled to **≤60 points**, chronological, `{t: "YYYY-MM-DD", v: number}`
  — mirrors `TaSparklinePoint {t,c}` naming.
- `value_1y_ago` / `change_1y_pct`: nearest observation within ±20 days of "365 days
  before `as_of`", found against the **full raw series** (before downsampling/windowing).
  **`null`** (never omitted) when no comparator exists (series too short) — append a
  `warnings[]` entry when this happens.
- `previous` is the **prior reading**, not the prior calendar day (matters for
  weekly/monthly series).
- `source`/`source_class`/`source_url`/`retrieved_at` are stamped **per series** (each
  series is its own independent GET) in addition to the whole-run top-level stamp.

### Downsample algorithm (final, `aiinvest/macro.py:downsample`)

```python
def downsample(rows, target_n=60):
    n = len(rows)
    if n <= target_n:
        return rows
    if target_n <= 1:
        return [rows[0]]
    step = (n - 1) / (target_n - 1)
    idxs = sorted({round(i * step) for i in range(target_n)})
    return [rows[i] for i in idxs]
```

Straight sample-pick (no averaging/binning) — every plotted point is a real FRED
observation, first/last always preserved.

---

## 3. Nearest-by-offset helper (final, shared by change_1y and liquidity 91d)

```python
def nearest_by_offset(rows, from_date, offset_days, tolerance_days):
    """rows: [{"date","value"}], ascending, value may be None (skip those).
    Returns the row whose date is nearest to from_date - offset_days,
    within +/- tolerance_days. None if nothing qualifies."""
```

Used for:
- `change_1y_pct` / `value_1y_ago`: `offset_days=365`, `tolerance_days=20` (generous —
  covers monthly CPI's revision drift).
- `liquidity` regime's 91-day WALCL comparator (§4.3): `offset_days=91`,
  `tolerance_days=10` (WALCL is weekly — a 10-day window always contains ≥1 candidate).
- `yoy_pct` transform (§1.1): `offset_days=365`, `tolerance_days=20`.

---

## 4. Regime block (final — rules, thresholds, and vocabulary are locked)

`regime.chips[]` is a **uniform array of exactly 4 objects**, fixed order
`curve, real_rate, liquidity, vix`, always present (never fewer than 4) even when an
input series is missing — in that case the chip's `state`/`value`/`value_label`/`as_of`
are `null` and a `warnings[]` entry names the cause. `regime.headline` is a single
composed string.

Chip shape (uniform, all 4 keys use this same shape):

```jsonc
{
  "key": "curve",
  "label": "10Y–2Y Curve",
  "state": "inverted",
  "value": -0.18,
  "value_label": "-0.18 pts",
  "basis": "T10Y2Y latest",
  "rule": "T10Y2Y < 0 -> inverted; 0-0.25 -> flat; >=0.25 -> normal",
  "as_of": "2026-07-11"
}
```

### 4.1 `curve` — is the curve inverted?
Input: `T10Y2Y.last`.
```
value <  0.00        -> "inverted"
0.00 <= value < 0.25  -> "flat"
value >= 0.25         -> "normal"
```
`label: "10Y–2Y Curve"`, `basis: "T10Y2Y latest"`.

### 4.2 `real_rate` — real-rate proxy (Fisher approximation)
Input: `DGS10.last − CPIAUCSL(yoy).last`.
```
real_rate = DGS10.last - CPI_YoY.last
real_rate >  2.0        -> "restrictive"
0.0 <= real_rate <= 2.0 -> "neutral"
real_rate <  0.0        -> "accommodative"
```
`label: "Real Rate (10Y − CPI YoY)"`, `value: real_rate`,
`basis: "DGS10 4.42% − CPI YoY 2.11%"` (formatted at compute time, both inputs folded
into the string — no separate `nominal_10y`/`cpi_yoy` fields, keeps the chip shape
uniform). `state: null` (+ warning) if either input is `null`.

### 4.3 `liquidity` — WALCL 3-month (91-day) direction
Input: `WALCL.last` vs. the WALCL observation ~91 days prior (via `nearest_by_offset`
against WALCL's full raw series, tolerance 10 days).
```
pct_change_91d = (latest - past_91d) / past_91d * 100
pct_change_91d >  +1.0%          -> "expanding"   (QE-like)
-1.0% <= pct_change_91d <= +1.0% -> "flat"
pct_change_91d <  -1.0%          -> "contracting" (QT-like)
```
`label: "Fed Balance Sheet"`, `value: pct_change_91d`, `basis: "WALCL 91d % change"`.

### 4.4 `vix` — bucket
Input: `VIXCLS.last`.
```
value < 15        -> "complacent"
15 <= value < 20   -> "normal"
20 <= value < 30   -> "elevated"
value >= 30        -> "stressed"
```
`label: "VIX"`, `basis: "VIXCLS latest level"`.

### 4.5 `headline` (deterministic, not LLM narrative)

Fixed priority order `curve, real_rate, liquidity, vix`; a family is mentioned only when
its state is non-null **and** non-neutral (`vix`'s "complacent" also counts as neutral —
not a stress signal):

```python
NEUTRAL = {"curve": "normal", "real_rate": "neutral", "liquidity": "flat"}
VIX_NEUTRAL = {"normal", "complacent"}

def build_headline(chips_by_key):
    parts = []
    for key in ("curve", "real_rate", "liquidity", "vix"):
        chip = chips_by_key[key]
        state = chip["state"]
        if state is None:
            continue
        if key == "vix":
            if state in VIX_NEUTRAL:
                continue
        elif state == NEUTRAL[key]:
            continue
        parts.append(f"{chip['label']} {state}")
    return " · ".join(parts) if parts else "No macro stress signals"
```

Example: `"10Y–2Y Curve inverted · Real Rate (10Y − CPI YoY) restrictive · Fed Balance Sheet contracting · VIX elevated"`.
(Data-designer's original A §3.5 used shorter hand-written labels like `"Curve inverted"`;
final implementation may use a short label map instead of `chip['label']` verbatim if the
composed string runs long on the capture card — either is acceptable, the **priority
order and neutral-skip logic are what's locked**.)

### 4.6 State vocabulary (final, locked)
- `curve`: `"inverted" | "flat" | "normal" | null`
- `real_rate`: `"restrictive" | "neutral" | "accommodative" | null`
- `liquidity`: `"expanding" | "flat" | "contracting" | null`
- `vix`: `"complacent" | "normal" | "elevated" | "stressed" | null`

---

## 5. `macro.json` — full contract (final)

```jsonc
{
  "generated_at": "2026-07-14T12:00:05Z",
  "schema_version": "macro-desk-v1",
  "source": "fred",
  "source_class": "api",
  "disclaimer": "Educational research only — not financial advice. Regime labels are rule-based, not predictive.",
  "series": [ /* exactly 8 objects, §2 shape, fixed §1 table order */ ],
  "regime": {
    "headline": "10Y–2Y Curve inverted · Real Rate (10Y − CPI YoY) restrictive · Fed Balance Sheet contracting · VIX elevated",
    "chips": [
      { "key": "curve", "label": "10Y–2Y Curve", "state": "inverted", "value": -0.18, "value_label": "-0.18 pts", "basis": "T10Y2Y latest", "rule": "T10Y2Y < 0 -> inverted; 0-0.25 -> flat; >=0.25 -> normal", "as_of": "2026-07-11" },
      { "key": "real_rate", "label": "Real Rate (10Y − CPI YoY)", "state": "restrictive", "value": 2.31, "value_label": "+2.31 pts", "basis": "DGS10 4.42% − CPI YoY 2.11%", "rule": "DGS10 - CPI_YoY; >2.0 restrictive, 0-2.0 neutral, <0.0 accommodative", "as_of": "2026-07-11" },
      { "key": "liquidity", "label": "Fed Balance Sheet", "state": "contracting", "value": -1.8, "value_label": "-1.8%", "basis": "WALCL 91d % change", "rule": "WALCL 91d %chg; >+1.0 expanding, -1.0..+1.0 flat, <-1.0 contracting", "as_of": "2026-07-09" },
      { "key": "vix", "label": "VIX", "state": "elevated", "value": 24.3, "value_label": "24.3", "basis": "VIXCLS latest level", "rule": "VIX <15 complacent, 15-20 normal, 20-30 elevated, >=30 stressed", "as_of": "2026-07-11" }
    ]
  },
  "warnings": []
}
```

### Compact annotated example (2 series + full regime block, as requested)

```jsonc
{
  "generated_at": "2026-07-14T12:00:05Z",
  "schema_version": "macro-desk-v1",
  "source": "fred",                 // whole-run stamp; every series repeats this per-item
  "source_class": "api",            // keyless FRED CSV = REST, never "html"/"xhr-json"
  "disclaimer": "Educational research only — not financial advice. Regime labels are rule-based, not predictive.",
  "series": [
    {
      "series_id": "DGS10", "symbol": "10Y", "display_name": "10-Year Treasury Yield",
      "group": "RATES", "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
      "transform": "level",
      "last": 4.42, "previous": 4.39, "change_abs": 0.03, "change_pct": 0.68,
      "value_1y_ago": 4.18, "change_1y_pct": 5.74,
      "as_of": "2026-07-11", "history_window_days": 365,
      "sparkline": [{ "t": "2025-07-14", "v": 4.20 }, { "t": "2026-07-11", "v": 4.42 }],
      "retrieved_at": "2026-07-14T12:00:03Z", "source": "fred", "source_class": "api",
      "source_url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
      "warnings": []
    },
    {
      "series_id": "CPIAUCSL", "symbol": "CPI", "display_name": "CPI, Year-over-Year",
      "group": "INFLATION", "frequency": "monthly", "unit": "%", "unit_kind": "pct", "decimals": 2,
      "transform": "yoy_pct",                       // raw index -> YoY % before it ever hits this file
      "last": 2.11, "previous": 2.04, "change_abs": 0.07, "change_pct": 3.43,
      "value_1y_ago": 2.85, "change_1y_pct": -25.96,
      "as_of": "2026-06-01", "history_window_days": 1825,  // 5y window: monthly series need more points to read a cycle
      "sparkline": [{ "t": "2021-07-01", "v": 5.37 }, { "t": "2026-06-01", "v": 2.11 }],
      "retrieved_at": "2026-07-14T12:00:04Z", "source": "fred", "source_class": "api",
      "source_url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL",
      "warnings": []
    }
  ],
  "regime": {
    "headline": "10Y–2Y Curve inverted · Real Rate (10Y − CPI YoY) restrictive · Fed Balance Sheet contracting · VIX elevated",
    "chips": [
      { "key": "curve", "label": "10Y–2Y Curve", "state": "inverted", "value": -0.18, "value_label": "-0.18 pts", "basis": "T10Y2Y latest", "rule": "T10Y2Y < 0 -> inverted; 0-0.25 -> flat; >=0.25 -> normal", "as_of": "2026-07-11" },
      { "key": "real_rate", "label": "Real Rate (10Y − CPI YoY)", "state": "restrictive", "value": 2.31, "value_label": "+2.31 pts", "basis": "DGS10 4.42% − CPI YoY 2.11%", "rule": "DGS10 - CPI_YoY; >2.0 restrictive, 0-2.0 neutral, <0.0 accommodative", "as_of": "2026-07-11" },
      { "key": "liquidity", "label": "Fed Balance Sheet", "state": "contracting", "value": -1.8, "value_label": "-1.8%", "basis": "WALCL 91d % change", "rule": "WALCL 91d %chg; >+1.0 expanding, -1.0..+1.0 flat, <-1.0 contracting", "as_of": "2026-07-09" },
      { "key": "vix", "label": "VIX", "state": "elevated", "value": 24.3, "value_label": "24.3", "basis": "VIXCLS latest level", "rule": "VIX <15 complacent, 15-20 normal, 20-30 elevated, >=30 stressed", "as_of": "2026-07-11" }
    ]
  },
  "warnings": []                    // e.g. "DFF: fetch failed (ConnectionError); series omitted"
}
```

`schema_version` bumps to `"macro-desk-v1"` (parallel to `ta-desk-v1`/`risk-desk-v1`).
Top-level `warnings[]` aggregates whole-series fetch failures and any regime chip that
went `null` for lack of input — per-series `warnings[]` covers series-local issues (e.g.
short history).

---

## 6. Chip state → color mapping (final, `web/lib/format.ts`)

Traffic-light, categorical (not interpolated) — B's pattern, remapped onto A's final
vocabulary:

| Color | curve | real_rate | liquidity | vix |
|---|---|---|---|---|
| green `#34d399` | `normal` | `accommodative` | `expanding` | `complacent`, `normal` |
| amber `#f59e0b` | `flat` | `neutral` | `flat` | `elevated` |
| red `#fb7185` | `inverted` | `restrictive` | `contracting` | `stressed` |
| grey `#6b7280` | `null` | `null` | `null` | `null` |

```ts
export function regimeColor(key: MacroRegimeKey, state: string | null): string {
  const GREEN = "#34d399", AMBER = "#f59e0b", RED = "#fb7185", GREY = "#6b7280";
  if (state == null) return GREY;
  if (key === "curve") return state === "normal" ? GREEN : state === "flat" ? AMBER : RED;
  if (key === "real_rate") return state === "accommodative" ? GREEN : state === "neutral" ? AMBER : RED;
  if (key === "liquidity") return state === "expanding" ? GREEN : state === "flat" ? AMBER : RED;
  // vix
  return state === "complacent" || state === "normal" ? GREEN : state === "elevated" ? AMBER : RED;
}
```

Every colored chip carries its `value_label` as visible text beside the color — no
hue-alone encoding (matches `contrastText()`'s house mandate).

---

## 7. Module plan — `scripts/aiinvest/macro.py` (pure, zero I/O)

```
SERIES_META = {  # series_id -> static metadata, §1 table
    "DGS2":    {"symbol": "2Y",  "display_name": "2-Year Treasury Yield", "group": "RATES",
                "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
                "transform": "level", "history_window_days": 365},
    "DGS10":   {..., "symbol": "10Y", "group": "RATES", "history_window_days": 365},
    "DFF":     {..., "symbol": "FEDFUNDS", "group": "RATES", "history_window_days": 365},
    "T10Y2Y":  {..., "symbol": "2S10S", "group": "RATES", "history_window_days": 365},
    "CPIAUCSL": {..., "symbol": "CPI", "group": "INFLATION", "unit_kind": "pct",
                 "transform": "yoy_pct", "frequency": "monthly", "history_window_days": 1825},
    "WALCL":   {..., "symbol": "FEDBS", "group": "LIQUIDITY_VOL", "unit": "$M",
                "unit_kind": "usd_millions", "decimals": 0, "frequency": "weekly",
                "history_window_days": 365},
    "VIXCLS":  {..., "symbol": "VIX", "group": "LIQUIDITY_VOL", "unit": "index",
                "unit_kind": "index", "decimals": 1, "history_window_days": 365},
    "APU000072610": {..., "symbol": "ELEC", "group": "ENERGY", "unit": "$/kWh",
                      "unit_kind": "usd_small", "decimals": 3, "frequency": "monthly",
                      "history_window_days": 1825},
}

def downsample(rows, target_n=60) -> list[{"date","value"}]              # §2
def nearest_by_offset(rows, from_date, offset_days, tolerance_days) -> row | None  # §3
def yoy(rows, tolerance_days=20) -> list[{"date","value"}]               # §1.1
def build_series_payload(series_id, raw_rows, meta, retrieved_at, source_url) -> dict  # §2 shape

def curve_chip(t10y2y_value, as_of) -> dict            # §4.1
def real_rate_chip(dgs10_value, cpi_yoy_value, as_of) -> dict   # §4.2
def liquidity_chip(latest, past_91d, as_of) -> dict     # §4.3
def vix_chip(vix_value, as_of) -> dict                  # §4.4
def build_headline(chips_by_key) -> str                 # §4.5
def build_regime(series_by_id) -> dict                  # assembles chips[] + headline, §5
```

## 8. `scripts/pull_macro.py` — thin network CLI (mirrors `pull_ta.py`)

```
1. For each id in SERIES_META: fred.fetch_csv(id) -> raw rows (dirty "." already -> None)
2. Apply transform: yoy() for CPIAUCSL, identity for the rest
3. Compute change_abs/change_pct (latest vs previous reading)
4. Compute value_1y_ago/change_1y_pct via nearest_by_offset(offset=365, tolerance=20)
   against the FULL series (pre-window-slice)
5. Slice to history_window_days, downsample() -> sparkline[]
6. build_series_payload() -> stamp retrieved_at (UTC now) + source_url
7. Reuse pull_ta.py's numeric-sanity walk (non-finite float / dirty sentinel check) per series
8. build_regime(series_by_id): for liquidity, pull WALCL's 91-day comparator via
   nearest_by_offset(offset=91, tolerance=10) against WALCL's full raw series
9. write web/public/data/macro.json (json.dumps(bundle, indent=2))

CLI flags: --series DGS10,VIXCLS (debug subset) · --out (default web/public/data/macro.json)
· --max-workers (ThreadPoolExecutor, default 4 — 8 lightweight CSV GETs, no browser,
  no Mode-A/B gating concern per CLAUDE.md §3 scope)

Per-series fetch failure: caught individually, series omitted from series[], id+reason
appended to top-level warnings[]; run does NOT abort. Any regime chip whose input series
failed -> that chip's state/value/value_label/as_of are null + a warning naming which
chip and which missing series; chip itself stays in the array (always 4 chips).
```

### `scripts/refresh_daily.py` hook (guarded, matches `build_risk.py`'s wiring)
```python
if os.path.exists(str(SCRIPTS / "pull_macro.py")):
    add("pull macro dashboard -> macro.json", [PY, "pull_macro.py"])
```
Placed after the risk step. `macro.json` is a standalone artifact consumed directly by
`web/lib/macro.ts` — not folded into `site.json`, same as `risk.json`/`ta_desk.json`.

---

## 9. Pytest case list (TDD before any network code)

`scripts/tests/test_macro.py` (pure, hand-computed fixtures, no mocking — mirrors
`test_ta.py`):

1. **`downsample`** — identity when `len <= target_n`; 365→60 exact cap with
   `out[0]==rows[0]`/`out[-1]==rows[-1]`; `target_n=1` doesn't `ZeroDivisionError`.
2. **`yoy`** — hand fixture 24 monthly rows, `2.0%` YoY at month 12; first-12-months
   dropped (not filled); a `None` mid-series row excluded as both target and comparator;
   372-day-back comparator within 20d tolerance still matches.
3. **`nearest_by_offset`** — exact match; no match within tolerance → `None`; two
   candidates (+5d, +15d) → nearer (+5d) wins.
4. **`curve_chip`** — table: `-0.5→inverted`, `0.0→flat`, `0.24→flat`, `0.25→normal`,
   `1.2→normal`, `None→state None + warning`.
5. **`real_rate_chip`** — `dgs10=4.42, cpi_yoy=2.11 → 2.31 → restrictive`; boundary
   `2.0→neutral` (inclusive); `-0.01→accommodative`; either input `None`→ `None` + warning.
6. **`liquidity_chip`** — `latest=7100000, past_91d=7228000 → -1.77%→contracting`;
   boundary `+1.0%→flat` (inclusive); `+1.01%→expanding`.
7. **`vix_chip`** — table: `12→complacent`, `14.99→complacent`, `15→normal`,
   `19.99→normal`, `20→elevated`, `29.99→elevated`, `30→stressed`, `50→stressed`.
8. **`build_headline`** — all 4 neutral → `"No macro stress signals"`; only curve
   inverted → single-part string, no trailing separator; all 4 non-neutral → fixed
   priority order regardless of dict insertion order (shuffled-key input fixture);
   `vix="complacent"` alone → still `"No macro stress signals"` (not a stress flag).
9. **`build_series_payload`** — 400 hand-built daily rows, `"level"` transform: hand-check
   `last`/`previous`/`change_abs`/`change_pct`; `len(sparkline) <= 60`; `change_1y_pct`
   computed against nearest ~365d-back row; 30-row too-short fixture →
   `value_1y_ago: null`, `change_1y_pct: null` + `warnings` entry (never silent omission).

`scripts/tests/test_pull_macro.py` (thin integration, `requests.get` monkeypatched per
series id — mirrors `test_pull_ta.py`'s `_install_fake_get`):

10. **Contract shape** — mocked CSVs for all 8 series → top-level keys exactly match §5;
    `schema_version=="macro-desk-v1"`; `len(series)==8` in fixed §1 order;
    `len(regime["chips"])==4` in fixed key order.
11. **Partial-failure resilience** — `T10Y2Y`'s GET raises `ConnectionError` → `main()`
    still returns 0; bundle has 7 series; top-level `warnings` names `T10Y2Y` + reason;
    `regime.chips` still has 4 entries but the `curve` chip has `state: null` + its own
    warning.
12. **`--series` subset flag** — `--series DGS10,VIXCLS` → bundle has exactly those 2
    series; chips needing a missing input (e.g. `real_rate` needs `CPIAUCSL`) are
    `state: null` + warned, not crashed.
13. **Dirty-value rejection** — a mocked CSV row with `"."` → confirmed absent from
    `sparkline`/`last`/`previous` anywhere in the bundle (`"." not in json.dumps(bundle)`
    string-search style check, adapted from `test_pull_ta.py`).

---

## 10. Web layer (final — file list, types, reader, page, components)

Everything below is a structural clone of the already-shipped Risk desk
(`web/app/terminal/risk/page.tsx`, `web/lib/risk.ts`, `web/components/terminal/
RiskLayerStrip.tsx` / `GroupSection.tsx` / `InstrumentTile.tsx` / `RiskCaptureCard.tsx`),
retargeted at the field names in §2/§5 above. Gate (`web/proxy.ts`, matcher
`/terminal/:path*`) already covers the new routes — **do not touch `proxy.ts`**.

### 10.1 New files
```
web/lib/macro.ts                                   reader: getMacroData / getMacroGroups / getMacroSeries
web/app/terminal/macro/page.tsx                     MACRO DESK screen
web/app/terminal/card/macro/page.tsx                 capture-card route (?capture=1 bypass, notFound() on missing data)
web/components/terminal/MacroRegimeStrip.tsx         4-chip strip, consumes regime.chips[] directly
web/components/terminal/MacroGroupSection.tsx        group header + responsive panel grid (clone of GroupSection)
web/components/terminal/MacroPanel.tsx               per-series stat panel: big value, change badge, sparkline (clone of InstrumentTile, non-Link — no per-symbol detail page this round)
web/components/terminal/MacroSparkline.tsx            standalone hand-rolled SVG, {t,v}[] shape (NOT a reuse of Sparkline.tsx — that's hardcoded to usd()/EPS HistoryPoint)
web/components/terminal/MacroCaptureCard.tsx          1080x1350 "MACRO PULSE" card (clone of RiskCaptureCard, own local CardMacroSparkline — capture cards never import screen components)
```

### 10.2 Modified files
```
web/lib/format.ts            + MACRO_GROUP_ORDER/LABELS/COLORS, regimeColor(key,state), regimeLabel(state),
                                macroValue(v, unitKind, decimals), macroChangeColor (thin wrapper on riskDivergingColor)
web/components/terminal/TerminalSubNav.tsx   + { href: "/terminal/macro", label: "MACRO" } entry
```

### 10.3 Reused verbatim, unmodified
```
web/components/terminal/CardScaleShell.tsx
web/lib/format.ts: signedPct, DASH, contrastText, riskDivergingColor
```

### 10.4 `web/lib/macro.ts` types (final — field-for-field mirror of §2/§5)

```ts
export type MacroGroup = "RATES" | "INFLATION" | "LIQUIDITY_VOL" | "ENERGY";
export type MacroUnitKind = "pct" | "usd_millions" | "usd_small" | "index";
export type MacroTransform = "level" | "yoy_pct";
export type MacroRegimeKey = "curve" | "real_rate" | "liquidity" | "vix";

export interface MacroSparkPoint { t: string; v: number; }

export interface MacroSeries {
  series_id: string;
  symbol: string;
  display_name: string;
  group: MacroGroup;
  frequency: "daily" | "weekly" | "monthly";
  unit: string;
  unit_kind: MacroUnitKind;
  decimals: number;
  transform: MacroTransform;
  last: number | null;
  previous: number | null;
  change_abs: number | null;
  change_pct: number | null;
  value_1y_ago: number | null;
  change_1y_pct: number | null;
  as_of: string | null;
  history_window_days: number;
  sparkline: MacroSparkPoint[];
  retrieved_at: string;
  source: string;
  source_class: "api";
  source_url: string;
  warnings: string[];
}

export interface MacroRegimeChip {
  key: MacroRegimeKey;
  label: string;
  state: string | null;
  value: number | null;
  value_label: string;
  basis: string;
  rule: string;
  as_of: string | null;
}

export interface MacroRegime {
  headline: string;
  chips: MacroRegimeChip[]; // always length 4, fixed order curve/real_rate/liquidity/vix
}

export interface MacroData {
  generated_at: string;
  schema_version: string;
  source: string;
  source_class: string;
  disclaimer: string;
  series: MacroSeries[];
  regime: MacroRegime;
  warnings: string[];
}
```

Reader (`getMacroData`, `getMacroGroups`, `getMacroSeries`) is a verbatim structural
mirror of `getRiskData`/`getRiskStocksByLayer`/`getRiskStock` in `web/lib/risk.ts` —
`existsSync`-guarded, try/catch `JSON.parse`, module-singleton cache, never throws,
validates `Array.isArray(parsed.series)` and `Array.isArray(parsed.regime?.chips)` before
trusting the parse.

### 10.5 Page/component behavior (final, unchanged from DESIGN B except field renames)

- `/terminal/macro`: `force-dynamic`, `TerminalSubNav currentPath="/terminal/macro"`,
  header with `Updated {generated_at}` + `Capture card →` link, empty-state block when
  `getMacroData()` is null, `MacroRegimeStrip` fed `data.regime.chips`, one
  `MacroGroupSection` per `MACRO_GROUP_ORDER` group fed `getMacroGroups()[group]`,
  top-level `warnings[]` rendered as amber lines, footer disclaimer notes macro series
  are lagging/backward-looking (release-lag caveat, not a VaR-style model caveat).
- `MacroRegimeStrip`: horizontally-scrollable, exactly 4 chips from `regime.chips`
  (never resorted client-side), each chip pill reuses the `TrendBadge` color+border+
  `1a`-alpha-fill visual idiom, using `regimeColor(chip.key, chip.state)`.
- `MacroGroupSection` / `MacroPanel`: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` (one
  fewer tier than `GroupSection`'s FX tiles — a macro panel carries a full sparkline +
  longer display name, needs more width). `MacroPanel` is a plain `<div>`, not a `<Link>`
  (no per-symbol detail page this round). Background stays flat `#0e131d` — no
  heat-tinting; this is a "read the number" desk, not the risk desk's "scan for
  outliers" heatmap.
- `MacroSparkline`: server component, pure SVG, emerald/rose direction-of-travel stroke
  (up = last point ≥ first point in window), no client JS.
- `/terminal/card/macro` + `MacroCaptureCard`: `notFound()` when data absent,
  `?capture=1` bypasses `CardScaleShell`, motion-kill style tag under capture mode.
  Card shows eyebrow `● MACRO PULSE`, headline `MACRO DESK`, all 4 regime chips
  (card-local pill clone using `regimeColor`/`state`), up to 4 headline series rows (one
  representative series per group present, `MACRO_GROUP_ORDER` precedence, own
  `CardMacroSparkline`), and an **unconditional** NFA footer line
  (`Educational research only — not financial advice. NFA.`) bottom-anchored via
  `marginTop: "auto"`.

### 10.6 `format.ts` additions (final)

```ts
export const MACRO_GROUP_ORDER: MacroGroup[] = ["RATES", "INFLATION", "LIQUIDITY_VOL", "ENERGY"];

export const MACRO_GROUP_LABELS: Record<string, string> = {
  RATES: "RATES", INFLATION: "INFLATION", LIQUIDITY_VOL: "LIQUIDITY & VOL", ENERGY: "ENERGY",
};

// ENERGY reuses LAYER_COLORS["L0-energy"] deliberately — ties the macro ENERGY
// group visually to the L0 chip color used everywhere else in the terminal.
export const MACRO_GROUP_COLORS: Record<string, string> = {
  RATES: "#3b82f6", INFLATION: "#a78bfa", LIQUIDITY_VOL: "#06b6d4", ENERGY: "#f59e0b",
};

export function regimeColor(key: MacroRegimeKey, state: string | null): string { /* §6 table */ }
export function regimeLabel(state: string | null): string { return state == null ? DASH : titleCase(state); }

// unit_kind -> display string. The ONE place that maps unit_kind -> formatted text.
export function macroValue(v: number | null, unitKind: MacroUnitKind, decimals: number): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  if (unitKind === "pct") return `${v.toFixed(decimals)}%`;
  if (unitKind === "usd_millions") return `$${(v / 1000).toLocaleString("en-US", { maximumFractionDigits: 0 })}B`;
  if (unitKind === "usd_small") return `$${v.toFixed(decimals)}`;
  return v.toFixed(decimals); // index
}

export function macroChangeColor(v: number | null, domainAbsMax: number): string {
  return riskDivergingColor(v, domainAbsMax); // direct reuse, no reimplementation
}
```

---

## 11. Design-discipline checklist (traced to house rules, both sub-designs agreed)

- **REST-first:** 100% FRED keyless CSV, zero Playwright — no gated/no-API macro source
  in scope. `source_class: "api"` throughout, top-level and per-series.
- **Stamp everything:** every `MacroSeries` carries `retrieved_at` (UTC ISO-8601),
  `source: "fred"`, `source_class: "api"`, `source_url`; `generated_at` stamps the
  whole run.
- **Sandbox caveat honored:** `fred.stlouisfed.org` is egress-blocked in this sandbox —
  `macro.py` is TDD'd against hand-computed fixtures (§9, cases 1–9), `pull_macro.py`
  against mocked CSV text (§9, cases 10–13); the live pull runs on the owner's machine.
- **Dirty-value doctrine:** FRED's `"."` sentinel is already `None` by the time
  `fred.py:parse_fred_csv` hands rows to `macro.py` — never a stray string in the bundle.
- **`existsSync` degrade:** `getMacroData()` never throws; `/terminal/macro` shows the
  same empty-state idiom as TA/Risk when `macro.json` is absent; `/terminal/card/macro`
  404s via `notFound()`.
- **NFA footer on capture surfaces:** unconditional on `MacroCaptureCard`, identical
  wording to `CaptureCard`/`RiskCaptureCard`.
- **Gate untouched:** `proxy.ts`'s `/terminal/:path*` matcher already covers both new
  routes; zero gate changes this round.
- **Color discipline:** regime chips are categorical (3–4 state traffic light, not
  interpolated); series change badges reuse the existing diverging emerald/rose pair
  (`signedPct`/`riskDivergingColor`), never a new hue; every colored element carries its
  value as visible text.
- **Bundles are generated + gitignored:** `web/public/data/macro.json` is produced by
  `scripts/pull_macro.py` on the owner's machine, not committed, not built by this repo's
  CI/Vercel build.

Not financial advice — regime labels are rule-based descriptive flags, not predictions.
