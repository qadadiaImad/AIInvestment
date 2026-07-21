# Halal Screening Engine + `/halal` Surface — Design Spec

**Date:** 2026-07-21
**Status:** Approved design (Approach A), pre-implementation
**Owner decisions:** universe = existing 128 (engine universe-agnostic) · standard = AAOIFI verdict + FTSE/MSCI breakdown · surface = dedicated `/halal` page + stock-page verdict blocks · release model = always-shippable increments

---

## 1. What this is

A Sharia-compliance screening layer on top of the existing AIInvestment data engine and
Vercel dashboard. Every verdict is a **computed methodology result, not a fatwa**: the
product shows the worked math per standard, the data provenance per input, and an explicit
"we are not a Sharia board" disclaimer. Purification amounts are computed where data
permits and marked `insufficient data` where it does not.

**Positioning (from competitor research, 2026-07-21):** the incumbent apps' top complaint
classes are stale data with no visible freshness (Zoya, Islamicly, IdealRatings), opaque
or paywalled "why" (Finispia's one-word reasons, Zoya's paywalled explanations), and
unexplained disagreement between apps. The open lane is **the referee**: worked
calculations per standard, side by side, every number stamped `retrieved_at` + source.
This is exactly what this repo's envelope schema already does.

**Explicitly out of scope for this spec:** the Skool education funnel (separate spec once
this ships), universe expansion beyond the 128, S&P/DJIM trailing-average screens (v1.1),
SEC XBRL interest-income ingestion (v1.1).

---

## 2. Verified methodology facts the engine encodes

All thresholds below were verified against primary sources on 2026-07-21 (workflow
`wf_b855afce-b1a`; source URLs retained in the research output and repeated in the
ruleset citations). Key corrections vs. common online descriptions:

| Standard | Financial screens (v1 scope in bold) | Denominator | Business screen |
|---|---|---|---|
| **AAOIFI SS 21** | **debt < 30%**, **interest-taking deposits < 30%** | **spot market cap** (clause 3/4/5: "last verified financial position" — trailing averages are screener convention, not standard text) | **impermissible income < 5% of total income** (3/4/4) |
| **FTSE Yasaar v4.6 (Feb 2026)** | **debt < 33.333%**, **cash+interest-bearing < 33.333%**, **receivables+cash < 50%** | **total assets** | prohibited sectors + interest/non-compliant income < 5% of revenue (4.3.1, 4.3.2.D) |
| **MSCI Islamic Index Series (Dec 2025)** | **debt < 33.33%**, **cash+interest-bearing securities < 33.33%**, **receivables+cash < 70%** (raised from 33.33% in Apr 2025 restructure) | **total assets** | prohibited activities + 5% of Total Income incl. all interest income |
| S&P Shariah (May 2025) — *v1.1* | leverage-only since 2023-09-15 (cash + receivables screens **removed**) — debt < 33% | 36-month avg market value of equity | NPI incl. all interest < 5% |
| DJIM (May 2025) — *v1.1* | leverage-only since 2023 — interest-bearing debt < 33% | 24-month avg market cap | NPI incl. all interest < 5% |

- **AAOIFI purification (3/4/6):** obligatory, per-share, **dividend-independent**:
  impermissible income ÷ shares outstanding × shares held; owed by whoever holds at
  period end; may not be used for any benefit including taxes.
- FTSE/S&P/DJIM publish advisory purification ratios only; MSCI bakes a dividend
  adjustment factor into index total-return calculation. v1 implements the AAOIFI method.
- S&P/DJIM dropped their cash and receivables screens in 2023; most third-party sites
  still describe the old three-ratio versions. Rendering current rules correctly is
  itself a credibility feature.

---

## 3. Architecture & data flow

```
TradingView scan (existing daily pull, + halal balance-sheet columns)
        │
        ▼
scripts/aiinvest/halal.py            NEW — ruleset engine (pure computation)
        │        ▲
        │        │ reads
        │   scripts/aiinvest/data/halal/business_activity.json   NEW — curated, in git
        ▼
scripts/export_halal.py              NEW — builds web/public/data/halal.json
        │
        ▼
web/lib/data.ts                      merge (same pattern as quantum.json)
        │
        ├── web/app/halal/           NEW route
        └── web/app/stocks/[symbol]  verdict block added
```

- One new step in `scripts/refresh_daily.py` after the fundamentals pull.
- Pure REST throughout (Mode A trivial); no browser work anywhere in this feature.
- `halal.json` is optional at load time, exactly like `quantum.json` — the site builds
  and runs without it.

### TradingView columns added to the daily scan

Verified live 2026-07-21 against `scanner.tradingview.com/america/scan` (values
sanity-checked: NVDA mcap $4.92T, total_debt_fq $12.814B):

`total_assets_fq`, `total_debt_fq`, `long_term_debt_fq`, `short_term_debt_fq`,
`cash_n_short_term_invest_fq`, `cash_n_equivalents_fq`, `total_revenue_ttm`,
`receivables_turnover_fy`, `market_cap_basic` (already pulled), `net_income_fy`.

**Scanner gotchas (encode as tests, not comments):**
- Invalid column names return **HTTP 200 + null** — no error. The authoritative field
  list is `GET https://scanner.tradingview.com/america/metainfo` (3,771 fields). A test
  asserts every requested column exists in metainfo.
- `cash_n_short_term_invest_fq` / `cash_n_equivalents_fq` are **null for banks**
  (TradingView's bank statement template lacks the line). Harmless here: every bank in
  the universe already fails the business screen.
- There is **no raw accounts-receivable field**. v1 uses the proxy
  `AR ≈ total_revenue_fy / receivables_turnover_fy` (average AR), flagged
  `basis: "derived"` in the envelope. Exact AR (SEC XBRL
  `us-gaap:AccountsReceivableNetCurrent`) is a v1.1 upgrade.
- There is **no interest-income field** of any form. v1 computes the 5% impermissible-
  income test from curated segment data only; tickers where interest income is the
  decisive unknown (see §5, pre-revenue quantum) ship as `insufficient_data`.

---

## 4. Ruleset engine — `scripts/aiinvest/halal.py`

Standards are **data, not code**. A `RULESETS` structure; each test:

```python
{
  "id": "aaoifi_debt",
  "standard": "AAOIFI",
  "name": "Interest-bearing debt / market cap",
  "numerator": ["total_debt_fq"],          # field list, summed
  "denominator": "market_cap_basic",        # spot; see conventions
  "threshold": 0.30,
  "citation": "AAOIFI SS 21 clause 3/4/2 (via PSE-hosted standard text, retrieved 2026-07-21)",
}
```

`compute(fundamentals: dict) -> StandardResult` per standard, where each test result
carries: numerator value, denominator value, ratio, threshold, **margin to breach**,
`passed | failed | unknown`, and the inputs' `retrieved_at` + source. **A missing or
dirty input yields `unknown` — never a silent pass.** Dirty-value rejection reuses
`schema.py` `clean()`.

### Disclosed conventions (stored on the ruleset, rendered in the UI)

1. **Spot market cap** for AAOIFI (as written, clause 3/4/5). Trailing-average variants
   are a v1.1 toggle for S&P/DJIM.
2. **`total_debt_fq` as the interest-bearing-debt proxy.** Whether TradingView's figure
   includes operating-lease liabilities (a known screener divergence point) is
   documented by a cross-validation test against one 10-K; the convention and its
   uncertainty are disclosed.
3. **Total cash + short-term investments as the interest-bearing proxy** (conservative:
   overstates the numerator; industry practice).
4. **Receivables via turnover proxy** (average AR, `derived`).
5. **Shares outstanding implied** as `market_cap_basic / price`, flagged `derived`
   (used only for purification-per-share).

---

## 5. Curated business-activity file

`scripts/aiinvest/data/halal/business_activity.json` — committed to git,
human-reviewable, one entry per universe ticker:

```json
{
  "ticker": "INTU",
  "status": "prohibited",
  "categories": ["interest-based-finance-referrals"],
  "impermissible_revenue_pct": {
    "value": 12.0, "basis": "segment-data",
    "quote": "Credit Karma segment revenue $2,263M of $18.8B total; growth drivers: personal-loan referrals (+$221M), credit-card referrals (+$213M), auto insurance (+$99M)",
    "source_url": "(illustrative — the real entry carries the exact Intuit FY2025 IR press-release URL, re-verified at curation time)",
    "retrieved_at": "2026-07-21T00:00:00Z"
  },
  "methodology_notes": {
    "aaoifi": {"stance": "fail", "reason": ">5% impermissible income"},
    "sector_exclusion": {"stance": "fail", "reason": "conventional-finance revenue stream"}
  },
  "confidence": "medium-high",
  "last_reviewed": "2026-07-21"
}
```

- `status ∈ {clean, prohibited, questionable}`; `clean` entries may omit
  `impermissible_revenue_pct` and quotes; **every non-clean entry must carry quote +
  source** (schema test enforces).
- **Seed content** comes from the 2026-07-21 research pre-assessment:
  - 6 `prohibited`: JPM, GS, BCS, BBVA, HSBC (conventional banks, high confidence);
    INTU (Credit Karma ≈12% of revenue = interest-product referral fees, medium-high).
  - 15 `borderline` → resolved to `clean-with-note`, `prohibited`, or `questionable`
    during implementation via agent-assisted deep-dives with quotes: GOOGL, META
    (advertising methodology fork — `aaoifi: pass`, `sector_exclusion: fail`, both
    shown), MSFT (gaming+ads share), AMZN (alcohol/pork retail share, ads), APP
    (gambling-category advertisers), PLTR, BWXT, PH (defense concentration), HPE, DELL
    (captive finance arms), IREN, CORZ, WULF, APLD (crypto stance + shifting revenue
    mix → `questionable` with scholar-split note), BTQ (entity + revenue verification).
  - ~107 `clean` (semis, software, equipment, uranium, pipelines-as-business,
    utilities-as-business; pharma AZN/GSK/MRNA `clean` with excipient note).
- **Refresh cadence:** each filing season, or on a flagged corporate event. Manual edit
  or agent-assisted re-run; diffs are reviewable in git history.
- Structural expectations to verify at ratio stage (not encode as business status):
  utilities/midstream/REITs will largely fail debt ratios; pre-revenue quantum names
  may fail the 5% test on treasury interest once interest-income data exists (v1.1) —
  until then they render `insufficient_data` on that test, honestly.

---

## 6. Verdict assembly, purification, `halal.json`

Per ticker:

```json
{
  "ticker": "NVDA",
  "overall": "halal",
  "overall_basis": "AAOIFI",
  "standards": {
    "AAOIFI": {"status": "pass", "tests": [
      {"id": "aaoifi_debt", "numerator_value": 12814000000, "denominator_value": 4919375940781,
       "ratio": 0.0026, "threshold": 0.30, "margin": 0.2974, "passed": true,
       "inputs_asof": "2026-07-21T14:02:11Z", "source": "tradingview-scanner"}
    ]},
    "FTSE": {"status": "pass", "tests": ["..."]},
    "MSCI": {"status": "pass", "tests": ["..."]}
  },
  "business": { "status": "clean", "categories": [], "notes": "..." },
  "purification": {"per_share": null, "status": "insufficient_data",
                   "missing": "interest income (v1.1: SEC XBRL)"},
  "retrieved_at": "2026-07-21T14:02:11Z",
  "provenance": {"ratios": "tradingview-scanner", "business": "curated 2026-07-21"}
}
```

- `overall ∈ {halal, not_halal, questionable, insufficient_data}`; equals the AAOIFI
  outcome, with `questionable` as a **first-class verdict** (scholar-split or genuinely
  indeterminate — always with the reason shown).
- Verdict precedence: business `prohibited` → `not_halal` regardless of ratios;
  business `questionable` → `questionable`; else ratio outcomes decide; any decisive
  test `unknown` → `insufficient_data`.
- **Purification** (AAOIFI 3/4/6): `impermissible_income ÷ shares_outstanding`.
  Computable in v1 only where curated segment data supplies an impermissible-income
  figure; otherwise `insufficient_data` with the missing input named.

---

## 7. Web surface

- **`/halal` page:**
  - Methodology explainer: how each standard works, where they disagree (denominators,
    thresholds, sector exclusions), the disclosed conventions (§4), and who we are /
    are not (not a Sharia board; educational; not financial or religious advice).
  - Compliance screener table: verdict badge, per-standard pass/fail chips, margin
    bars, business-status column, **data-age badge** per row; filters: halal-only /
    fails-with-reasons / questionable / by stack layer / by sector (AI, Quantum).
- **Stock pages (`/stocks/[symbol]`):** compliance card with an expandable **"Show the
  math"** accordion per standard — numerator line item, denominator, ratio vs
  threshold, margin, source + timestamp; purification per share; business-activity
  notes with quotes. This accordion is the future content unit (each renders naturally
  into a carousel slide — content hook lands v1.2).
- **`/screener`:** rows gain `halal_status` for a badge/filter; no other change.
- **Loader (`web/lib/data.ts`):** load optional `halal.json`, attach verdicts to
  stocks + screener rows, expose `getHalalData()`. Follows the `quantum.json` merge
  pattern exactly.

---

## 8. Error handling & testing

**Failure posture:** a ticker with missing/dirty data ships as `insufficient_data`,
visibly — never dropped, never guessed. Export **refuses** any datum lacking
`retrieved_at` (provenance-mandatory test).

**pytest (TDD, in `scripts/tests/`):**
- Golden tests from live research values: NVDA AAOIFI debt ratio ≈ 0.26% → pass; JPM →
  business fail regardless of ratios; SO (utility) → expected debt-ratio fail; one
  `questionable` case (e.g. IREN); one `insufficient_data` case.
- Unknown-input propagation (missing field → test `unknown` → verdict rules).
- Curated-file schema validation: every universe ticker covered; every non-clean entry
  has quote + source; `last_reviewed` present.
- Metainfo test: every requested scanner column exists in the metainfo field list
  (guards the 200+null silent-failure mode).
- Cross-validation: `total_debt_fq` vs `long_term_debt_fq + short_term_debt_fq`
  reconciliation; one-name spot check vs 10-K documented.
- Export-shape validation for `halal.json`.

**vitest (web):** loader merge with and without `halal.json` present; verdict fields
reach screener rows and stock pages.

---

## 9. Release ladder

| Release | Contents |
|---|---|
| **v1 (ship first)** | 128 names · AAOIFI + FTSE + MSCI spot ratios · curated business file · `/halal` page + stock verdict blocks · provenance everywhere |
| v1.1 | S&P/DJIM trailing-avg leverage screens (avg-mcap series from existing 5y price data, approximation flagged) · SEC XBRL interest income (resolves pre-revenue-quantum 5% test properly) · exact AR from XBRL · purification calculator UI |
| v1.2 | Compliance-change alerts with provenance diffs · live coverage-honesty table · verdict-card → carousel/reel content hook |
| v2 | Universe expansion beyond the 128 · Skool education funnel (separate spec) |

---

## 10. Sources (retrieved 2026-07-21)

- AAOIFI SS 21 clause text: PSE-hosted standard PDF (documents.pse.com.ph) +
  aaoifi.com SS-21 page; corroboration: Amanah Advisors, Halal Ninja.
- FTSE Yasaar Global Equity Shariah Index Series Ground Rules v4.6 (lseg.com PDF).
- MSCI Islamic Index Series Methodology, Dec 2025 edition (msci.com PDFs).
- S&P Shariah / DJIM methodologies, May 2025 editions (spglobal.com via Wayback
  snapshots 2025-06-20; live 2026 editions return 403 to non-browser clients — deltas
  unverified, noted as a re-check item before productionizing thresholds).
- TradingView scanner field probe: live REST, 2026-07-21; metainfo endpoint (3,771 fields).
- Competitor scan: zoya.finance, musaffa.com, islamicly.com, amanah.finance,
  finispia.com, halalscreener.app, IdealRatings + review aggregators.
- Full research output: workflow `wf_b855afce-b1a` (session artifacts).

*Educational/research product. Not financial advice, not religious rulings.*
