# Halal Screening Engine v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v1 of the halal screening engine per `docs/superpowers/specs/2026-07-21-halal-screening-design.md`: AAOIFI/FTSE/MSCI ratio screens over the 128-ticker universe, a curated business-activity file, `halal.json` export, a `/halal` page + stock-page verdict cards, deployed to Vercel.

**Architecture:** Standards encoded as data (`RULESETS`) in a new pure-computation module `scripts/aiinvest/halal.py`; a new `pull_halal.py` scans all 128 tickers (AI + Quantum) in one TradingView REST POST with balance-sheet columns; `export_halal.py` joins ratios + curated business activity into `web/public/data/halal.json` (optional bundle, quantum.json pattern); web loads it via `getHalalData()` and renders `/halal` + per-stock "Show the math" cards.

**Tech Stack:** Python 3 + pytest (scripts/), Next.js 16 App Router + React 19 + TypeScript + vitest (web/), TradingView scanner REST, Vercel.

## Global Constraints

- **Verdicts are computed methodology results, not fatwas.** Every rendered verdict surface carries the disclaimer (spec §1, §7): "Computed from published methodologies — we are not a Sharia board. Educational only; not financial or religious advice."
- **Missing/dirty data → `unknown`/`insufficient_data`, visibly. Never a silent pass, never dropped, never guessed** (spec §8).
- **Every datum carries `retrieved_at` + source** (CLAUDE.md rule 3). Export refuses records without it.
- **The AI pipeline stays byte-identical**: halal columns go in a separate `HALAL_COLUMNS` list and a separate `pull_halal.py` scan — do NOT touch `DEFAULT_COLUMNS`.
- **TDD**: every task = failing test → run (expect FAIL) → minimal implementation → run (expect PASS) → commit. Python tests run from `scripts/`: `python -m pytest tests/test_halal.py -v`. Web tests: `cd web && npx vitest run`.
- **Next.js 16 warning (web/AGENTS.md):** this is NOT the Next.js in your training data. Read the relevant guide in `web/node_modules/next/dist/docs/` before writing any web code.
- **No GuruFocus terms** anywhere in halal outputs (siteexport leak-check convention).
- Commit messages end with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- v1 thresholds (verified 2026-07-21, spec §2): AAOIFI debt<30% & cash<30% of **spot market cap**, activity<5%; FTSE debt<33.333% & cash<33.333% & (AR+cash)<50% of **total assets**; MSCI debt<33.33% & cash<33.33% & (AR+cash)<70% of **total assets**.

---

### Task 1: Register halal balance-sheet columns in the TradingView client

**Files:**
- Modify: `scripts/aiinvest/tradingview.py` (COLUMNS dict, ~line 56; add `HALAL_COLUMNS` list after `DEFAULT_COLUMNS`, ~line 71)
- Test: `scripts/tests/test_tradingview.py` (append)

**Interfaces:**
- Consumes: existing `COLUMNS` dict (`col -> (unit, kind)`), `DEFAULT_COLUMNS`.
- Produces: `tradingview.HALAL_COLUMNS: list[str]` — the exact column list `pull_halal.py` (Task 6) passes to `scan()`. New COLUMNS entries: `total_assets_fq`, `total_debt_fq`, `long_term_debt_fq`, `short_term_debt_fq`, `cash_n_short_term_invest_fq`, `cash_n_equivalents_fq`, `total_revenue_ttm`, `total_revenue_fy`, `receivables_turnover_fy`, `net_income_fy` (all `("usd","num")` except `receivables_turnover_fy` `("ratio","num")`).

- [ ] **Step 1: Write the failing test** — append to `scripts/tests/test_tradingview.py`:

```python
# --- halal screening balance-sheet columns (verified live 2026-07-21) ---

def test_halal_columns_registered_with_unit_and_kind():
    expected = {
        "total_assets_fq": ("usd", "num"),
        "total_debt_fq": ("usd", "num"),
        "long_term_debt_fq": ("usd", "num"),
        "short_term_debt_fq": ("usd", "num"),
        "cash_n_short_term_invest_fq": ("usd", "num"),
        "cash_n_equivalents_fq": ("usd", "num"),
        "total_revenue_ttm": ("usd", "num"),
        "total_revenue_fy": ("usd", "num"),
        "receivables_turnover_fy": ("ratio", "num"),
        "net_income_fy": ("usd", "num"),
    }
    for col, (unit, kind) in expected.items():
        assert col in tv.COLUMNS, f"{col} missing from COLUMNS"
        assert tv.COLUMNS[col] == (unit, kind)


def test_halal_columns_list_exists_and_is_not_in_default():
    # HALAL_COLUMNS is a SEPARATE list: the AI-stack daily pull stays byte-identical.
    for col in ["total_assets_fq", "total_debt_fq", "cash_n_short_term_invest_fq",
                "receivables_turnover_fy", "market_cap_basic", "close"]:
        assert col in tv.HALAL_COLUMNS, f"{col} not in HALAL_COLUMNS"
    assert "total_assets_fq" not in tv.DEFAULT_COLUMNS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_tradingview.py -v -k halal`
Expected: FAIL — `AttributeError: module 'aiinvest.tradingview' has no attribute 'HALAL_COLUMNS'` / KeyError on COLUMNS.

- [ ] **Step 3: Implement** — in `scripts/aiinvest/tradingview.py`, add to `COLUMNS` (before the closing brace, after `"industry"`):

```python
    # --- halal screening balance-sheet / income inputs (verified live 2026-07-21;
    #     scanner returns 200+null for unknown columns — every id below was checked
    #     against GET /america/metainfo, the authoritative 3,771-field list) ---
    "total_assets_fq": ("usd", "num"),
    "total_debt_fq": ("usd", "num"),
    "long_term_debt_fq": ("usd", "num"),
    "short_term_debt_fq": ("usd", "num"),
    "cash_n_short_term_invest_fq": ("usd", "num"),
    "cash_n_equivalents_fq": ("usd", "num"),
    "total_revenue_ttm": ("usd", "num"),
    "total_revenue_fy": ("usd", "num"),
    "receivables_turnover_fy": ("ratio", "num"),
    "net_income_fy": ("usd", "num"),
```

and after `DEFAULT_COLUMNS`:

```python
# Halal-screen pull (pull_halal.py). SEPARATE from DEFAULT_COLUMNS so the AI-stack
# daily pull stays byte-identical. close + market_cap_basic ride along for the
# spot-market-cap denominator and implied shares outstanding.
HALAL_COLUMNS = [
    "close", "market_cap_basic",
    "total_assets_fq", "total_debt_fq", "long_term_debt_fq", "short_term_debt_fq",
    "cash_n_short_term_invest_fq", "cash_n_equivalents_fq",
    "total_revenue_ttm", "total_revenue_fy", "receivables_turnover_fy",
    "net_income_fy",
]
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd scripts && python -m pytest tests/test_tradingview.py -v`
Expected: ALL PASS (existing + new).

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/tradingview.py scripts/tests/test_tradingview.py
git commit -m "feat(halal): register balance-sheet scanner columns + HALAL_COLUMNS list"
```

---

### Task 2: Ruleset engine — inputs + per-test computation (`halal.py` part 1)

**Files:**
- Create: `scripts/aiinvest/halal.py`
- Test: `scripts/tests/test_halal.py` (create)

**Interfaces:**
- Consumes: envelope dicts from `tradingview.parse_scan_response` (each metric: `{"value", "raw", "unit", "dirty", "retrieved_at", ...}`).
- Produces (used by Tasks 3–4, 7):
  - `STANDARDS: list[dict]` — keys `key`, `name`, `activity_threshold_pct`, `tests: list[dict]` (each test: `id`, `label`, `numerator: list[str]`, `denominator: str`, `threshold: float`, `citation: str`).
  - `CONVENTIONS: list[str]` — the four disclosed v1 conventions (spec §4).
  - `inputs_from_metrics(metrics: dict) -> dict` — returns `{"total_debt": float|None, "cash": float|None, "receivables": float|None, "total_assets": float|None, "market_cap": float|None, "revenue_ttm": float|None, "close": float|None, "inputs_asof": str|None}` (receivables = revenue_fy / receivables_turnover_fy, `None`-safe).
  - `compute_test(test: dict, inputs: dict) -> dict` — `{"id","label","numerator_value","denominator_value","ratio","threshold","margin","status" ("pass"|"fail"|"unknown"),"citation"}`.

- [ ] **Step 1: Write the failing test** — create `scripts/tests/test_halal.py`:

```python
"""RED tests for the halal ruleset engine (pure computation, no I/O)."""
from aiinvest import halal


def _env(value, retrieved_at="2026-07-21T14:00:00Z"):
    return {"value": value, "raw": value, "unit": "usd", "dirty": False,
            "retrieved_at": retrieved_at, "source": "tradingview",
            "source_url": "u", "source_class": "api"}


# NVDA live values from the 2026-07-21 field probe (workflow wf_b855afce-b1a).
NVDA_METRICS = {
    "close": _env(200.0),
    "market_cap_basic": _env(4919375940781.0),
    "total_assets_fq": _env(259474000000.0),
    "total_debt_fq": _env(12814000000.0),
    "cash_n_short_term_invest_fq": _env(80572000000.0),
    "total_revenue_ttm": _env(253491000000.0),
    "total_revenue_fy": _env(215938000000.0),
    "receivables_turnover_fy": _env(7.0188),
}


def test_standards_registry_shape():
    keys = [s["key"] for s in halal.STANDARDS]
    assert keys == ["AAOIFI", "FTSE", "MSCI"]
    for s in halal.STANDARDS:
        assert s["activity_threshold_pct"] == 5.0
        for t in s["tests"]:
            assert t["citation"], f"{t['id']} missing citation"
            assert 0 < t["threshold"] < 1


def test_aaoifi_thresholds_are_30pct_of_market_cap():
    aaoifi = halal.STANDARDS[0]
    assert [t["threshold"] for t in aaoifi["tests"]] == [0.30, 0.30]
    assert all(t["denominator"] == "market_cap" for t in aaoifi["tests"])


def test_ftse_msci_use_total_assets_denominator():
    for s in halal.STANDARDS[1:]:
        assert all(t["denominator"] == "total_assets" for t in s["tests"])


def test_inputs_from_metrics_extracts_and_derives():
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    assert inp["total_debt"] == 12814000000.0
    assert inp["market_cap"] == 4919375940781.0
    # receivables proxy = revenue_fy / turnover_fy  (≈ 30.77B for NVDA)
    assert abs(inp["receivables"] - 215938000000.0 / 7.0188) < 1e6
    assert inp["inputs_asof"] == "2026-07-21T14:00:00Z"


def test_inputs_missing_turnover_gives_none_receivables():
    m = dict(NVDA_METRICS)
    del m["receivables_turnover_fy"]
    assert halal.inputs_from_metrics(m)["receivables"] is None


def test_compute_test_nvda_aaoifi_debt_passes_with_margin():
    aaoifi_debt = halal.STANDARDS[0]["tests"][0]
    r = halal.compute_test(aaoifi_debt, halal.inputs_from_metrics(NVDA_METRICS))
    assert r["status"] == "pass"
    assert abs(r["ratio"] - 0.0026) < 0.0005          # ≈0.26%, golden from live probe
    assert abs(r["margin"] - (0.30 - r["ratio"])) < 1e-9


def test_compute_test_missing_input_is_unknown_never_pass():
    aaoifi_debt = halal.STANDARDS[0]["tests"][0]
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    inp["total_debt"] = None
    r = halal.compute_test(aaoifi_debt, inp)
    assert r["status"] == "unknown"
    assert r["ratio"] is None


def test_compute_test_zero_denominator_is_unknown():
    aaoifi_debt = halal.STANDARDS[0]["tests"][0]
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    inp["market_cap"] = 0.0
    assert halal.compute_test(aaoifi_debt, inp)["status"] == "unknown"


def test_utility_debt_load_fails_aaoifi_debt_test():
    # Structural expectation from the spec: heavy-leverage utility profile.
    # Synthetic values shaped like SO: debt ~60B vs mcap ~90B -> 66% > 30%.
    inp = {"total_debt": 60e9, "market_cap": 90e9, "cash": 1e9,
           "receivables": 3e9, "total_assets": 140e9, "revenue_ttm": 27e9,
           "close": 80.0, "inputs_asof": "2026-07-21T14:00:00Z"}
    r = halal.compute_test(halal.STANDARDS[0]["tests"][0], inp)
    assert r["status"] == "fail"
    assert r["margin"] < 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_halal.py -v`
Expected: FAIL — `ModuleNotFoundError`/`ImportError: cannot import name 'halal'`.

- [ ] **Step 3: Implement** — create `scripts/aiinvest/halal.py`:

```python
"""Halal (Sharia-compliance) ruleset engine — pure computation, no I/O.

Standards are DATA, not code: `STANDARDS` encodes AAOIFI SS 21 / FTSE Yasaar /
MSCI Islamic ratio screens with their citations (all thresholds verified against
primary methodology texts 2026-07-21 — see docs/superpowers/specs/
2026-07-21-halal-screening-design.md §2). A missing or dirty input yields
status "unknown", NEVER a silent pass.

Verdicts are computed methodology results, not fatwas. Educational only —
not financial or religious advice.
"""
from __future__ import annotations

# Disclosed v1 conventions (spec §4) — rendered verbatim in the UI.
CONVENTIONS = [
    "AAOIFI ratios use SPOT market capitalization per SS 21 clause 3/4/5 "
    "('last verified financial position'); trailing averages are screener "
    "conventions, not standard text.",
    "TradingView total_debt_fq proxies interest-bearing debt; whether it "
    "includes operating-lease liabilities is a known screener divergence "
    "point (cross-validated in tests, disclosed here).",
    "Total cash + short-term investments proxies interest-bearing deposits "
    "and securities (conservative: overstates the numerator).",
    "Receivables are approximated as revenue_fy / receivables_turnover_fy "
    "(average AR); exact point-in-time AR arrives with SEC XBRL in v1.1.",
]

_AAOIFI_SRC = ("AAOIFI Shari'ah Standard No. 21, clause {c} (standard text via "
               "PSE-hosted PDF, retrieved 2026-07-21)")
_FTSE_SRC = ("FTSE Yasaar Global Equity Shariah Index Series Ground Rules v4.6 "
             "(Feb 2026), rule {c}")
_MSCI_SRC = "MSCI Islamic Index Series Methodology (Dec 2025), section {c}"

STANDARDS = [
    {
        "key": "AAOIFI",
        "name": "AAOIFI Shari'ah Standard No. 21",
        "activity_threshold_pct": 5.0,
        "activity_citation": _AAOIFI_SRC.format(c="3/4/4"),
        "tests": [
            {"id": "aaoifi_debt", "label": "Interest-bearing debt / market cap",
             "numerator": ["total_debt"], "denominator": "market_cap",
             "threshold": 0.30, "citation": _AAOIFI_SRC.format(c="3/4/2")},
            {"id": "aaoifi_cash", "label": "Interest-bearing deposits & securities / market cap",
             "numerator": ["cash"], "denominator": "market_cap",
             "threshold": 0.30, "citation": _AAOIFI_SRC.format(c="3/4/3")},
        ],
    },
    {
        "key": "FTSE",
        "name": "FTSE Yasaar Global Equity Shariah Index Series",
        "activity_threshold_pct": 5.0,
        "activity_citation": _FTSE_SRC.format(c="4.3.1 + 4.3.2.D"),
        "tests": [
            {"id": "ftse_debt", "label": "Debt / total assets",
             "numerator": ["total_debt"], "denominator": "total_assets",
             "threshold": 1 / 3, "citation": _FTSE_SRC.format(c="4.3.2.A")},
            {"id": "ftse_cash", "label": "Cash + interest-bearing items / total assets",
             "numerator": ["cash"], "denominator": "total_assets",
             "threshold": 1 / 3, "citation": _FTSE_SRC.format(c="4.3.2.B")},
            {"id": "ftse_receivables", "label": "Receivables + cash / total assets",
             "numerator": ["receivables", "cash"], "denominator": "total_assets",
             "threshold": 0.50, "citation": _FTSE_SRC.format(c="4.3.2.C")},
        ],
    },
    {
        "key": "MSCI",
        "name": "MSCI Islamic Index Series",
        "activity_threshold_pct": 5.0,
        "activity_citation": _MSCI_SRC.format(c="2.1"),
        "tests": [
            {"id": "msci_debt", "label": "Total debt / total assets",
             "numerator": ["total_debt"], "denominator": "total_assets",
             "threshold": 0.3333, "citation": _MSCI_SRC.format(c="2.2")},
            {"id": "msci_cash", "label": "Cash + interest-bearing securities / total assets",
             "numerator": ["cash"], "denominator": "total_assets",
             "threshold": 0.3333, "citation": _MSCI_SRC.format(c="2.2")},
            {"id": "msci_receivables", "label": "Receivables + cash / total assets",
             "numerator": ["receivables", "cash"], "denominator": "total_assets",
             "threshold": 0.70, "citation": _MSCI_SRC.format(c="2.2, Apr-2025 revision")},
        ],
    },
]


def _val(metrics, col):
    env = metrics.get(col)
    if isinstance(env, dict):
        return env.get("value")
    return None


def inputs_from_metrics(metrics):
    """Extract + derive the screen inputs from a per-symbol metrics dict.

    Derived: receivables ≈ total_revenue_fy / receivables_turnover_fy (average
    AR — disclosed convention #4). None-safe throughout: absent -> None.
    """
    rev_fy = _val(metrics, "total_revenue_fy")
    turns = _val(metrics, "receivables_turnover_fy")
    receivables = (rev_fy / turns) if rev_fy and turns else None
    asof = None
    for env in metrics.values():
        if isinstance(env, dict) and env.get("retrieved_at"):
            asof = env["retrieved_at"]
            break
    return {
        "total_debt": _val(metrics, "total_debt_fq"),
        "cash": _val(metrics, "cash_n_short_term_invest_fq"),
        "receivables": receivables,
        "total_assets": _val(metrics, "total_assets_fq"),
        "market_cap": _val(metrics, "market_cap_basic"),
        "revenue_ttm": _val(metrics, "total_revenue_ttm"),
        "close": _val(metrics, "close"),
        "inputs_asof": asof,
    }


def compute_test(test, inputs):
    """One ratio screen -> worked result. Missing/zero inputs -> 'unknown'."""
    parts = [inputs.get(name) for name in test["numerator"]]
    denom = inputs.get(test["denominator"])
    if any(p is None for p in parts) or denom is None or denom <= 0:
        num = None if any(p is None for p in parts) else sum(parts)
        return {"id": test["id"], "label": test["label"],
                "numerator_value": num, "denominator_value": denom,
                "ratio": None, "threshold": test["threshold"], "margin": None,
                "status": "unknown", "citation": test["citation"]}
    num = sum(parts)
    ratio = num / denom
    return {"id": test["id"], "label": test["label"],
            "numerator_value": num, "denominator_value": denom,
            "ratio": ratio, "threshold": test["threshold"],
            "margin": test["threshold"] - ratio,
            "status": "pass" if ratio < test["threshold"] else "fail",
            "citation": test["citation"]}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd scripts && python -m pytest tests/test_halal.py -v`
Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/halal.py scripts/tests/test_halal.py
git commit -m "feat(halal): ruleset engine — STANDARDS registry + worked per-test computation"
```

---

### Task 3: Verdict assembly + purification (`halal.py` part 2)

**Files:**
- Modify: `scripts/aiinvest/halal.py` (append)
- Test: `scripts/tests/test_halal.py` (append)

**Interfaces:**
- Consumes: `STANDARDS`, `compute_test`, `inputs_from_metrics` (Task 2); curated entries shaped per Task 4 (`{"status": "clean"|"prohibited"|"questionable", "impermissible_revenue_pct": {"value": float|None, ...}|None, "methodology_notes": {...}, ...}`).
- Produces (used by Task 7):
  - `compute_standard(std: dict, inputs: dict, activity_pct: float|None) -> dict` — `{"key","name","status" ("pass"|"fail"|"unknown"),"tests":[...],"activity_status","activity_threshold_pct","activity_citation"}`.
  - `purification(inputs: dict, activity_pct: float|None) -> dict` — `{"per_share": float|None, "status": "computed"|"insufficient_data", "missing": str|None, "basis": str|None}`.
  - `verdict(symbol: str, metrics: dict, curated: dict|None) -> dict` — the per-ticker object of spec §6 (`overall`, `overall_basis`, `standards`, `business`, `purification`, `inputs_asof`).

**Verdict precedence (spec §6, encode exactly):** business `prohibited` → `not_halal` (ratios still computed + shown). business `questionable` → `questionable`. No curated entry → `insufficient_data`. Else: AAOIFI standard fail → `not_halal`; AAOIFI unknown → `insufficient_data`; AAOIFI pass → `halal`.

- [ ] **Step 1: Write the failing tests** — append to `scripts/tests/test_halal.py`:

```python
CLEAN = {"status": "clean", "impermissible_revenue_pct": None,
         "methodology_notes": {}, "confidence": "high"}
BANK = {"status": "prohibited", "impermissible_revenue_pct": {"value": 100.0},
        "methodology_notes": {"aaoifi": {"stance": "fail",
                                         "reason": "conventional banking"}},
        "confidence": "high"}
CRYPTO_Q = {"status": "questionable", "impermissible_revenue_pct": None,
            "methodology_notes": {"aaoifi": {"stance": "questionable",
                                             "reason": "crypto scholar split"}},
            "confidence": "medium"}


def test_compute_standard_all_pass_is_pass():
    r = halal.compute_standard(halal.STANDARDS[0],
                               halal.inputs_from_metrics(NVDA_METRICS), 0.0)
    assert r["status"] == "pass"
    assert len(r["tests"]) == 2
    assert r["activity_status"] == "pass"


def test_compute_standard_activity_breach_fails():
    r = halal.compute_standard(halal.STANDARDS[0],
                               halal.inputs_from_metrics(NVDA_METRICS), 12.0)
    assert r["activity_status"] == "fail"
    assert r["status"] == "fail"


def test_compute_standard_unknown_activity_is_unknown_not_pass():
    r = halal.compute_standard(halal.STANDARDS[0],
                               halal.inputs_from_metrics(NVDA_METRICS), None)
    assert r["activity_status"] == "unknown"
    assert r["status"] == "unknown"      # ratios pass but activity undetermined


def test_verdict_clean_business_passing_ratios_is_halal():
    v = halal.verdict("NVDA", NVDA_METRICS, {**CLEAN,
                      "impermissible_revenue_pct": {"value": 0.0}})
    assert v["overall"] == "halal"
    assert v["overall_basis"] == "AAOIFI"
    assert set(v["standards"]) == {"AAOIFI", "FTSE", "MSCI"}


def test_verdict_prohibited_business_is_not_halal_regardless_of_ratios():
    v = halal.verdict("JPM", NVDA_METRICS, BANK)   # even with passing ratios
    assert v["overall"] == "not_halal"


def test_verdict_questionable_business_is_questionable():
    assert halal.verdict("IREN", NVDA_METRICS, CRYPTO_Q)["overall"] == "questionable"


def test_verdict_no_curated_entry_is_insufficient_data():
    assert halal.verdict("XXXX", NVDA_METRICS, None)["overall"] == "insufficient_data"


def test_purification_needs_activity_pct():
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    p = halal.purification(inp, None)
    assert p["status"] == "insufficient_data"
    assert p["per_share"] is None
    q = halal.purification(inp, 2.0)
    # 2% of revenue_ttm / implied shares (mcap/close)
    shares = 4919375940781.0 / 200.0
    assert abs(q["per_share"] - 0.02 * 253491000000.0 / shares) < 1e-6
    assert q["status"] == "computed"
    assert "derived" in q["basis"]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd scripts && python -m pytest tests/test_halal.py -v -k "verdict or standard or purification"`
Expected: FAIL — `AttributeError: ... 'compute_standard'`.

- [ ] **Step 3: Implement** — append to `scripts/aiinvest/halal.py`:

```python
def compute_standard(std, inputs, activity_pct):
    """All ratio tests + the impermissible-income test for one standard.

    Ratio fail OR activity fail -> "fail"; any unknown (none failing) ->
    "unknown"; else "pass". activity_pct None -> activity unknown (honest).
    """
    tests = [compute_test(t, inputs) for t in std["tests"]]
    if activity_pct is None:
        activity_status = "unknown"
    else:
        activity_status = "pass" if activity_pct < std["activity_threshold_pct"] else "fail"
    statuses = [t["status"] for t in tests] + [activity_status]
    if "fail" in statuses:
        status = "fail"
    elif "unknown" in statuses:
        status = "unknown"
    else:
        status = "pass"
    return {"key": std["key"], "name": std["name"], "status": status,
            "tests": tests, "activity_status": activity_status,
            "activity_threshold_pct": std["activity_threshold_pct"],
            "activity_citation": std["activity_citation"]}


def purification(inputs, activity_pct):
    """AAOIFI 3/4/6 purification per share: impermissible income / shares.

    v1: impermissible income = curated activity_pct × revenue_ttm; shares
    implied as market_cap / close (disclosed as derived). Anything missing ->
    insufficient_data with the missing input NAMED.
    """
    if activity_pct is None:
        return {"per_share": None, "status": "insufficient_data",
                "missing": "impermissible income share (curated segment data; "
                           "interest income lands v1.1 via SEC XBRL)",
                "basis": None}
    rev, mcap, close = inputs.get("revenue_ttm"), inputs.get("market_cap"), inputs.get("close")
    if not rev or not mcap or not close:
        return {"per_share": None, "status": "insufficient_data",
                "missing": "revenue_ttm / market_cap / close", "basis": None}
    shares = mcap / close
    return {"per_share": (activity_pct / 100.0) * rev / shares,
            "status": "computed",
            "missing": None,
            "basis": "curated impermissible-income % × TTM revenue ÷ implied "
                     "shares outstanding (market_cap/close, derived)"}


def verdict(symbol, metrics, curated):
    """Assemble the per-ticker verdict object (spec §6). Precedence:
    business prohibited -> not_halal; questionable -> questionable; no curated
    entry -> insufficient_data; else AAOIFI outcome decides."""
    inputs = inputs_from_metrics(metrics)
    pct = None
    if curated:
        ipr = curated.get("impermissible_revenue_pct") or {}
        pct = ipr.get("value")
        if pct is None and curated.get("status") == "clean":
            pct = 0.0   # curated clean == no identified impermissible stream
    standards = {s["key"]: compute_standard(s, inputs, pct) for s in STANDARDS}

    if curated is None:
        overall = "insufficient_data"
    elif curated["status"] == "prohibited":
        overall = "not_halal"
    elif curated["status"] == "questionable":
        overall = "questionable"
    else:
        aaoifi = standards["AAOIFI"]["status"]
        overall = {"pass": "halal", "fail": "not_halal"}.get(aaoifi, "insufficient_data")

    return {"symbol": symbol, "overall": overall, "overall_basis": "AAOIFI",
            "standards": standards,
            "business": curated or {"status": "unknown", "methodology_notes": {}},
            "purification": purification(inputs, pct),
            "inputs_asof": inputs["inputs_asof"]}
```

- [ ] **Step 4: Run tests** — `cd scripts && python -m pytest tests/test_halal.py -v` — Expected: ALL PASS.
- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/halal.py scripts/tests/test_halal.py
git commit -m "feat(halal): verdict assembly with spec precedence + AAOIFI purification"
```

---

### Task 4: Curated business-activity seed file + schema validation

**Files:**
- Create: `scripts/aiinvest/data/halal/business_activity.json` (generated by the seed script below, then committed as data)
- Create: `scripts/seed_halal_activity.py` (the generator — kept for regeneration/review)
- Modify: `scripts/aiinvest/halal.py` (append `load_business_activity` + `validate_business_activity`)
- Test: `scripts/tests/test_halal.py` (append)

**Interfaces:**
- Produces: `halal.load_business_activity(path=None) -> dict[str, dict]` (default path `scripts/aiinvest/data/halal/business_activity.json`), `halal.validate_business_activity(entries: dict, universe: list[str]) -> list[str]` (returns problem strings, empty = valid).
- Entry schema (spec §5, with `evidence` holding quote+source for ALL non-clean entries): `{"ticker","status" ("clean"|"prohibited"|"questionable"),"categories":[...],"impermissible_revenue_pct": {"value","basis"}|None,"evidence": {"quote","source_url","retrieved_at"}|None,"methodology_notes": {...},"note": str|None,"confidence","last_reviewed"}`.
- Validation rules: every universe ticker present; status in enum; **non-clean ⇒ `evidence.quote` + `evidence.source_url` non-empty**; `last_reviewed` present.

**Seed classifications (2026-07-21 research, workflow `wf_b855afce-b1a`):**
- `prohibited` (6): JPM, GS, BCS, BBVA, HSBC (conventional banking, high confidence); INTU (Credit Karma ≈12% of FY2025 revenue = loan/credit-card referral fees, medium-high).
- `questionable` (8): IREN, CORZ, WULF, APLD (crypto scholar-split + fast-shifting BTC/AI revenue mix), APP (gambling-category advertiser share unknown), BWXT (naval-reactor/weapons-complex concentration, stance needed), HPE (Financial Services segment ≈11–12% of revenue, operating-lease vs interest mix decisive), BTQ (entity + revenue-source verification pending).
- `clean` with note (7): GOOGL, META (AAOIFI-threshold pass / S&P-style sector-exclusion fail — fork disclosed), MSFT (gaming ≈9% + ads ≈5% near thresholds), AMZN (alcohol/pork retail small % of ~$600B+, ads), PLTR (defense-exclusion methodologies flag; AAOIFI passes), PH (aerospace ~30%, defense subset), DELL (DFS captive financing, small vs ~$95B revenue), ET (MLP units — some methodologies exclude partnerships outright, disclosed).
- `clean` (rest → 107 total incl. the noted ones): all remaining L0/L1/L2/L4/Quantum names; AZN, GSK, MRNA clean with excipient note (istihalah/darura majority position).

- [ ] **Step 1: Write the failing tests** — append to `scripts/tests/test_halal.py`:

```python
import pathlib

from aiinvest import ai_stack, quantum_stack


def _universe():
    return sorted({t.split(":")[-1] for t in
                   ai_stack.all_tickers() + quantum_stack.all_tickers()})


def test_business_activity_file_covers_entire_universe():
    entries = halal.load_business_activity()
    problems = halal.validate_business_activity(entries, _universe())
    assert problems == [], "\n".join(problems)


def test_business_activity_known_seed_classifications():
    entries = halal.load_business_activity()
    for sym in ["JPM", "GS", "BCS", "BBVA", "HSBC", "INTU"]:
        assert entries[sym]["status"] == "prohibited", sym
    for sym in ["IREN", "CORZ", "WULF", "APLD", "APP", "BWXT", "HPE", "BTQ"]:
        assert entries[sym]["status"] == "questionable", sym
    assert entries["NVDA"]["status"] == "clean"
    assert entries["GOOGL"]["status"] == "clean"
    assert entries["GOOGL"]["methodology_notes"]["sector_exclusion"]["stance"] == "fail"


def test_validate_flags_missing_evidence_on_non_clean():
    bad = {"ZZZZ": {"ticker": "ZZZZ", "status": "prohibited", "categories": [],
                    "impermissible_revenue_pct": None, "evidence": None,
                    "methodology_notes": {}, "note": None,
                    "confidence": "high", "last_reviewed": "2026-07-21"}}
    problems = halal.validate_business_activity(bad, ["ZZZZ"])
    assert any("evidence" in p for p in problems)
```

- [ ] **Step 2: Run to verify failure** — `cd scripts && python -m pytest tests/test_halal.py -v -k business` — Expected: FAIL (`load_business_activity` missing).

- [ ] **Step 3a: Implement loader/validator** — append to `scripts/aiinvest/halal.py`:

```python
import json as _json
import pathlib as _pathlib

_ACTIVITY_PATH = _pathlib.Path(__file__).resolve().parent / "data" / "halal" / "business_activity.json"
_STATUSES = {"clean", "prohibited", "questionable"}


def load_business_activity(path=None):
    """Curated business-activity entries, keyed by bare symbol."""
    p = _pathlib.Path(path) if path else _ACTIVITY_PATH
    entries = _json.loads(p.read_text(encoding="utf-8"))
    return {e["ticker"]: e for e in entries}


def validate_business_activity(entries, universe):
    """Return a list of problem strings (empty == valid). Enforced (spec §5):
    full universe coverage; status enum; non-clean entries carry evidence
    (quote + source_url); last_reviewed present."""
    problems = []
    for sym in universe:
        if sym not in entries:
            problems.append(f"{sym}: missing from business_activity.json")
    for sym, e in entries.items():
        if e.get("status") not in _STATUSES:
            problems.append(f"{sym}: bad status {e.get('status')!r}")
        if not e.get("last_reviewed"):
            problems.append(f"{sym}: missing last_reviewed")
        if e.get("status") in ("prohibited", "questionable"):
            ev = e.get("evidence") or {}
            if not ev.get("quote") or not ev.get("source_url"):
                problems.append(f"{sym}: non-clean entry lacks evidence quote/source_url")
    return problems
```

- [ ] **Step 3b: Create the seed generator** — create `scripts/seed_halal_activity.py`. It embeds the full classification tables (per-ticker status, categories, evidence quotes + source URLs from the 2026-07-21 research for every prohibited/questionable entry, methodology_notes for the fork names, notes for pharma/ET/DELL/PLTR/PH/MSFT/AMZN) and writes `scripts/aiinvest/data/halal/business_activity.json`. Structure:

```python
"""Generate the curated halal business-activity seed file (2026-07-21 research).

One-shot generator kept in-repo so the seed is reviewable + regenerable. The
OUTPUT file is the source of truth going forward — hand-edit it for updates,
rerun this only to rebuild from scratch. Non-clean entries carry evidence
(quote + source_url) enforced by halal.validate_business_activity.
"""
from __future__ import annotations

import json
import pathlib

from aiinvest import ai_stack, halal, quantum_stack

REVIEWED = "2026-07-21"

# --- non-clean + noted entries: full researched detail -----------------------
DETAILED = {
    "JPM": {
        "status": "prohibited", "categories": ["conventional-banking"],
        "impermissible_revenue_pct": {"value": None, "basis": "core-business"},
        "evidence": {
            "quote": "Conventional bank - core business is interest-based lending, deposits, credit cards, and conventional trading.",
            "source_url": "https://www.jpmorganchase.com/ir",
            "retrieved_at": "2026-07-21T00:00:00Z"},
        "methodology_notes": {
            "aaoifi": {"stance": "fail", "reason": "conventional financial institution"},
            "sector_exclusion": {"stance": "fail", "reason": "conventional finance sector"}},
        "note": None, "confidence": "high",
    },
    # ... GS, BCS, BBVA, HSBC: same shape as JPM (banking), each with its own
    #     IR source_url and quote.  INTU: prohibited, categories
    #     ["interest-based-finance-referrals"], impermissible ~12%,
    #     evidence quote = Credit Karma FY2025 segment numbers + growth drivers,
    #     source_url = Intuit FY2025 results press release (2025-08-21).
    # ... IREN/CORZ/WULF/APLD: questionable, categories ["crypto-mining"],
    #     evidence = latest revenue-mix statement + IR URL, note = scholar split
    #     on bitcoin permissibility + fast-shifting AI-hosting mix.
    # ... APP (gambling-category advertiser share), BWXT (naval reactors),
    #     HPE (FS segment ~11-12%, lease-vs-interest mix), BTQ (entity verify):
    #     questionable, each with evidence quote + source.
    # ... GOOGL/META: clean; methodology_notes aaoifi pass / sector_exclusion
    #     fail with reasons; evidence = ad-revenue share statement + 10-K URL.
    # ... MSFT/AMZN/PLTR/PH/DELL/ET/AZN/GSK/MRNA: clean with note (see plan
    #     Task-4 header for each note's content) - notes are text, no evidence
    #     object required for clean entries.
}
# The implementer fills DETAILED completely from the Task-4 header tables +
# research output (workflow wf_b855afce-b1a); every prohibited/questionable
# entry MUST have a real quote and a real URL. No placeholder text may remain.


def main():
    universe = sorted({t.split(":")[-1] for t in
                       ai_stack.all_tickers() + quantum_stack.all_tickers()})
    entries = []
    for sym in universe:
        if sym in DETAILED:
            e = {"ticker": sym, **DETAILED[sym], "last_reviewed": REVIEWED}
        else:
            e = {"ticker": sym, "status": "clean", "categories": [],
                 "impermissible_revenue_pct": None, "evidence": None,
                 "methodology_notes": {}, "note": None,
                 "confidence": "high", "last_reviewed": REVIEWED}
        entries.append(e)
    out = pathlib.Path(__file__).resolve().parent / "aiinvest" / "data" / "halal" / "business_activity.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    problems = halal.validate_business_activity({e["ticker"]: e for e in entries}, universe)
    print(f"Wrote {out} ({len(entries)} entries); problems: {problems or 'none'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3c: Fill `DETAILED` completely** (all 6 prohibited + 8 questionable with real quotes/URLs from the research output; the noted-clean entries with their notes), run `cd scripts && python seed_halal_activity.py` — Expected: `problems: none`.
- [ ] **Step 4: Run tests** — `cd scripts && python -m pytest tests/test_halal.py -v` — Expected: ALL PASS.
- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/halal.py scripts/seed_halal_activity.py scripts/aiinvest/data/halal/business_activity.json scripts/tests/test_halal.py
git commit -m "feat(halal): curated business-activity seed (128 names) + schema validation"
```

---

### Task 5: `pull_halal.py` — one REST scan for the 128-ticker universe

**Files:**
- Create: `scripts/pull_halal.py`
- Test: `scripts/tests/test_pull_halal.py` (create)

**Interfaces:**
- Consumes: `tradingview.scan(tickers, columns=tradingview.HALAL_COLUMNS)`, `ai_stack.all_tickers()`, `quantum_stack.all_tickers()`.
- Produces: `data/halal/<YYYY-MM-DD>/tradingview_halal_<stamp>.json` with the batch envelope shape (`batch_metadata` + `financial_data` keyed by bare symbol — mirrors `pull_quantum.assemble_batch`, lines 75–101 of `scripts/pull_quantum.py`). Pure function `assemble_batch(records, requested_tickers, retrieved_at)` exported for Task 7's tests.

- [ ] **Step 1: Write the failing test** — create `scripts/tests/test_pull_halal.py`:

```python
"""RED tests for the halal pull CLI (pure assembly logic only — no network)."""
import pull_halal


def test_universe_is_ai_plus_quantum_deduped():
    tickers = pull_halal.universe_tickers()
    assert "NASDAQ:NVDA" in tickers and "NYSE:JPM" in tickers
    assert len(tickers) == len(set(tickers))
    assert len(tickers) >= 120           # 108 AI + 20 quantum minus overlaps


def test_assemble_batch_shapes_and_miss_reporting():
    records = [{"symbol": "NVDA", "ticker": "NASDAQ:NVDA", "metrics": {}}]
    batch = pull_halal.assemble_batch(records, ["NASDAQ:NVDA", "NYSE:ZZZ"],
                                      "2026-07-21T14:00:00Z")
    md = batch["batch_metadata"]
    assert md["total_symbols_requested"] == 2
    assert md["successful_symbols"] == 1
    assert md["failed_symbols"] == ["NYSE:ZZZ"]
    assert md["scope"] == "halal"
    assert batch["financial_data"]["NVDA"]["as_of"] == "2026-07-21T14:00:00Z"
```

Note: `scripts/tests/` imports CLI modules from the parent dir the same way `test_dashboard.py` and friends do (pytest rootdir `scripts/` puts it on `sys.path`). If the import fails, add the same `sys.path` shim used by the neighboring CLI tests.

- [ ] **Step 2: Run to verify failure** — `cd scripts && python -m pytest tests/test_pull_halal.py -v` — Expected: FAIL (`ModuleNotFoundError: pull_halal`).

- [ ] **Step 3: Implement** — create `scripts/pull_halal.py` (mirrors `pull_quantum.py` minus history):

```python
"""Pull halal-screen balance-sheet inputs for the FULL universe (AI + Quantum)
via TradingView's scanner (REST) and write the batch.

One POST covers all ~128 tickers (bulk verified). SEPARATE from the AI/quantum
daily pulls so those stay byte-identical. Writes
data/halal/<date>/tradingview_halal_<stamp>.json.

Educational/research only — not financial advice, not religious rulings.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

from aiinvest import ai_stack, quantum_stack, tradingview


def universe_tickers():
    """AI + Quantum tradeable tickers, de-duplicated, order-stable."""
    seen, out = set(), []
    for t in ai_stack.all_tickers() + quantum_stack.all_tickers():
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def assemble_batch(records, requested_tickers, retrieved_at):
    """Batch envelope (mirrors pull_quantum.assemble_batch; scope 'halal')."""
    financial_data, seen = {}, set()
    for rec in records:
        seen.add(rec["ticker"])
        financial_data[rec["symbol"]] = {
            "symbol": rec["symbol"], "ticker": rec["ticker"],
            "as_of": retrieved_at, "metrics": rec["metrics"],
        }
    failed = [t for t in requested_tickers if t not in seen]
    return {
        "batch_metadata": {
            "batch_timestamp": retrieved_at, "scope": "halal",
            "total_symbols_requested": len(requested_tickers),
            "successful_symbols": len(financial_data),
            "failed_symbols": failed,
            "retrieval_mode": "rest", "providers_used": ["tradingview"],
        },
        "financial_data": financial_data,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull halal-screen inputs via TradingView REST.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Smoke a small subset (first N tickers).")
    ap.add_argument("--verify-columns", action="store_true",
                    help="Check every HALAL_COLUMNS id against GET /america/metainfo "
                         "(the scanner returns 200+null for unknown columns — this is "
                         "the only real validation) and exit.")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"))
    args = ap.parse_args(argv)

    if args.verify_columns:
        import requests
        meta = requests.get("https://scanner.tradingview.com/america/metainfo",
                            headers={"User-Agent": tradingview._UA}, timeout=25).json()
        known = {f.get("n") for f in meta.get("fields", [])}
        missing = [c for c in tradingview.HALAL_COLUMNS if c not in known]
        print(f"metainfo fields={len(known)}; HALAL_COLUMNS={len(tradingview.HALAL_COLUMNS)}; "
              f"missing={missing or 'none'}")
        return 1 if missing else 0

    tickers = universe_tickers()
    if args.limit is not None:
        tickers = tickers[:args.limit]

    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    records = tradingview.scan(tickers, columns=tradingview.HALAL_COLUMNS,
                               retrieved_at=stamp)
    batch = assemble_batch(records, tickers, stamp)

    out_dir = pathlib.Path(args.out) / "halal" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"tradingview_halal_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")

    md = batch["batch_metadata"]
    print(f"Wrote {out_path}")
    print(f"  requested={md['total_symbols_requested']} ok={md['successful_symbols']} "
          f"failed={len(md['failed_symbols'])}")
    if md["failed_symbols"]:
        print(f"  unresolved: {', '.join(md['failed_symbols'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests** — `cd scripts && python -m pytest tests/test_pull_halal.py -v` — Expected: PASS. Then live smoke: `python pull_halal.py --limit 3` — Expected: writes a batch, `ok=3 failed=0`, NVDA metrics contain non-null `total_debt_fq`.
- [ ] **Step 5: Commit**

```bash
git add scripts/pull_halal.py scripts/tests/test_pull_halal.py
git commit -m "feat(halal): pull_halal CLI — one REST scan over the 128-ticker universe"
```

---

### Task 6: `export_halal.py` — build `web/public/data/halal.json`

**Files:**
- Create: `scripts/export_halal.py`
- Test: `scripts/tests/test_export_halal.py` (create)

**Interfaces:**
- Consumes: latest `data/halal/*/tradingview_halal_*.json` batch; `halal.verdict`, `halal.load_business_activity`, `halal.CONVENTIONS`; `ai_stack.layer_of` / `quantum_stack.layer_of` for layer tags.
- Produces: `web/public/data/halal.json`:

```json
{
  "generated_at": "...", "disclaimer": "...", "conventions": ["...x4"],
  "methodology_note": "AAOIFI verdict basis; FTSE + MSCI shown side by side...",
  "verdicts": { "NVDA": { "symbol", "layer", "overall", "overall_basis",
                          "standards", "business", "purification", "inputs_asof" } }
}
```

- Pure `build(batch, activity) -> dict` exported for tests. `main()` refuses (exit 2) if any verdict record lacks `inputs_asof` **and** ratios are present (provenance-mandatory), or if the activity file fails validation.

- [ ] **Step 1: Write the failing test** — create `scripts/tests/test_export_halal.py`:

```python
"""RED tests for the halal.json export (pure build; no I/O)."""
import export_halal
from aiinvest import halal


def _env(v):
    return {"value": v, "raw": v, "unit": "usd", "dirty": False,
            "retrieved_at": "2026-07-21T14:00:00Z", "source": "tradingview",
            "source_url": "u", "source_class": "api"}


BATCH = {"batch_metadata": {"batch_timestamp": "2026-07-21T14:00:00Z"},
         "financial_data": {"NVDA": {"symbol": "NVDA", "ticker": "NASDAQ:NVDA",
                                     "as_of": "2026-07-21T14:00:00Z",
                                     "metrics": {
             "close": _env(200.0), "market_cap_basic": _env(4919375940781.0),
             "total_assets_fq": _env(259474000000.0),
             "total_debt_fq": _env(12814000000.0),
             "cash_n_short_term_invest_fq": _env(80572000000.0),
             "total_revenue_ttm": _env(253491000000.0),
             "total_revenue_fy": _env(215938000000.0),
             "receivables_turnover_fy": _env(7.0188)}}}}

ACTIVITY = {"NVDA": {"ticker": "NVDA", "status": "clean", "categories": [],
                     "impermissible_revenue_pct": None, "evidence": None,
                     "methodology_notes": {}, "note": None,
                     "confidence": "high", "last_reviewed": "2026-07-21"}}


def test_build_produces_verdict_with_conventions_and_disclaimer():
    bundle = export_halal.build(BATCH, ACTIVITY)
    assert bundle["conventions"] == halal.CONVENTIONS
    assert "not financial" in bundle["disclaimer"].lower()
    assert "sharia board" in bundle["disclaimer"].lower()
    v = bundle["verdicts"]["NVDA"]
    assert v["overall"] == "halal"
    assert v["layer"] == "L1-chips"
    assert v["standards"]["AAOIFI"]["tests"][0]["ratio"] < 0.01


def test_build_symbol_missing_from_activity_is_insufficient_data():
    bundle = export_halal.build(BATCH, {})
    assert bundle["verdicts"]["NVDA"]["overall"] == "insufficient_data"


def test_build_never_emits_gurufocus_terms():
    import json
    s = json.dumps(export_halal.build(BATCH, ACTIVITY)).lower()
    for term in ("guru", "gf value", "gf_value", "gf score"):
        assert term not in s
```

- [ ] **Step 2: Run to verify failure** — `cd scripts && python -m pytest tests/test_export_halal.py -v` — Expected: FAIL (module missing).

- [ ] **Step 3: Implement** — create `scripts/export_halal.py`:

```python
"""Export the halal-screening bundle: web/public/data/halal.json.

Joins the latest pull_halal.py batch (ratio inputs) with the curated
business-activity file into per-ticker verdicts (aiinvest.halal.verdict).
Optional bundle — the site builds without it (quantum.json pattern).

Verdicts are computed methodology results, NOT fatwas. Educational only.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib

from aiinvest import ai_stack, halal, quantum_stack

DISCLAIMER = (
    "Computed from published screening methodologies (AAOIFI SS 21, FTSE "
    "Yasaar, MSCI Islamic) — we are not a Sharia board and this is not a "
    "fatwa, not financial advice, and not a recommendation to buy or sell "
    "any security. Every figure is date-stamped and decays; missing data is "
    "shown as 'insufficient data', never guessed. Verify against primary "
    "sources and consult a qualified scholar before acting.")

METHODOLOGY_NOTE = (
    "Overall verdict basis: AAOIFI SS 21. FTSE Yasaar and MSCI Islamic "
    "results are shown side by side because the standards genuinely disagree "
    "(denominators, thresholds, sector exclusions) — the same company can "
    "pass one and fail another. Expand any test to see the worked math.")


def _layer_of(ticker):
    return ai_stack.layer_of(ticker) or quantum_stack.layer_of(ticker)


def build(batch, activity):
    """Assemble the halal.json bundle. Pure (no I/O)."""
    verdicts = {}
    for sym, rec in (batch.get("financial_data") or {}).items():
        v = halal.verdict(sym, rec.get("metrics", {}) or {}, activity.get(sym))
        v["layer"] = _layer_of(rec.get("ticker"))
        verdicts[sym] = v
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"generated_at": now, "disclaimer": DISCLAIMER,
            "methodology_note": METHODOLOGY_NOTE,
            "conventions": halal.CONVENTIONS, "verdicts": verdicts}


def _latest_batch(data_root):
    paths = sorted(glob.glob(str(data_root / "halal" / "*" / "tradingview_halal_*.json")))
    if not paths:
        return None
    return json.loads(pathlib.Path(paths[-1]).read_text(encoding="utf-8"))


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Export the halal-screening bundle.")
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(repo / "web" / "public" / "data" / "halal.json"))
    args = ap.parse_args(argv)

    batch = _latest_batch(pathlib.Path(args.data))
    if batch is None:
        print("No halal batch found — run pull_halal.py first.")
        return 2

    activity = halal.load_business_activity()
    universe = sorted({t.split(":")[-1] for t in
                       ai_stack.all_tickers() + quantum_stack.all_tickers()})
    problems = halal.validate_business_activity(activity, universe)
    if problems:
        print("business_activity.json INVALID — refusing to export:")
        for p in problems:
            print(f"  - {p}")
        return 2

    bundle = build(batch, activity)

    # Provenance-mandatory: any verdict with computed ratios must carry inputs_asof.
    unstamped = [s for s, v in bundle["verdicts"].items()
                 if v.get("inputs_asof") is None
                 and any(t["ratio"] is not None
                         for std in v["standards"].values() for t in std["tests"])]
    if unstamped:
        print(f"UNSTAMPED verdicts (refusing to export): {unstamped}")
        return 2

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    counts = {}
    for v in bundle["verdicts"].values():
        counts[v["overall"]] = counts.get(v["overall"], 0) + 1
    print(f"Wrote {out}")
    print(f"  verdicts={len(bundle['verdicts'])} breakdown={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests** — `cd scripts && python -m pytest tests/test_export_halal.py -v` — Expected: PASS.
- [ ] **Step 5: Commit**

```bash
git add scripts/export_halal.py scripts/tests/test_export_halal.py
git commit -m "feat(halal): export halal.json — verdicts + conventions + provenance gate"
```

---

### Task 7: Wire halal steps into `refresh_daily.py`

**Files:**
- Modify: `scripts/refresh_daily.py` (`build_plan`, after the quantum block ~line 76)
- Test: `scripts/tests/test_refresh_halal.py` (create)

**Interfaces:**
- Consumes: `build_plan(args)` pure-function contract (list of `{"label","cmd","cwd"}`).
- Produces: two guarded steps — `"pull halal inputs"` (`pull_halal.py`) and `"export halal.json"` (`export_halal.py`) — added after the quantum export, before `build screener`, only when the CLIs exist (same `os.path.exists` guard the quantum steps use).

- [ ] **Step 1: Write the failing test** — create `scripts/tests/test_refresh_halal.py`:

```python
"""Halal steps appear in the daily plan (pure build_plan, no subprocess)."""
import argparse

import refresh_daily


def _args(**kw):
    ns = argparse.Namespace(dry_run=False, with_backtest=False,
                            deploy=False, keep_going=False)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def test_halal_steps_in_plan_between_quantum_and_screener():
    labels = [s["label"] for s in refresh_daily.build_plan(_args())]
    assert "pull halal inputs" in labels
    assert "export halal.json" in labels
    assert labels.index("export halal.json") < labels.index("build screener")
    assert labels.index("pull halal inputs") < labels.index("export halal.json")
```

- [ ] **Step 2: Run to verify failure** — `cd scripts && python -m pytest tests/test_refresh_halal.py -v` — Expected: FAIL (labels absent).

- [ ] **Step 3: Implement** — in `scripts/refresh_daily.py` `build_plan`, after the quantum `export_quantum.py` guard block (line ~76), insert:

```python
    # Halal screening vertical (OPTIONAL — only when the halal CLIs exist).
    # One REST scan over the full universe + verdict export (halal.json).
    if os.path.exists(str(SCRIPTS / "pull_halal.py")):
        add("pull halal inputs", [PY, "pull_halal.py"])
    if os.path.exists(str(SCRIPTS / "export_halal.py")):
        add("export halal.json", [PY, "export_halal.py"])
```

- [ ] **Step 4: Run tests** — `cd scripts && python -m pytest tests/test_refresh_halal.py tests/test_dashboard.py -v` — Expected: PASS (and no existing refresh tests broken: run `python -m pytest -q`).
- [ ] **Step 5: Commit**

```bash
git add scripts/refresh_daily.py scripts/tests/test_refresh_halal.py
git commit -m "feat(halal): wire pull/export steps into the daily refresh plan"
```

---

### Task 8: Web types + loader — `getHalalData()` (client-safe helpers split)

**Files:**
- Create: `web/lib/halal.ts` (client-safe: types + display helpers, NO `node:fs` — mirrors `lib/news.ts` / `lib/conflict.ts` convention)
- Modify: `web/lib/data.ts` (append server-side loader + re-exports)
- Test: `web/lib/halal.test.ts` (create; vitest, mirrors `egograph.test.ts`)

**Interfaces:**
- Produces in `web/lib/halal.ts`:

```typescript
export type HalalOverall = "halal" | "not_halal" | "questionable" | "insufficient_data";
export type HalalTestStatus = "pass" | "fail" | "unknown";
export interface HalalTestResult { id: string; label: string;
  numerator_value: number | null; denominator_value: number | null;
  ratio: number | null; threshold: number; margin: number | null;
  status: HalalTestStatus; citation: string; }
export interface HalalStandardResult { key: string; name: string;
  status: HalalTestStatus; tests: HalalTestResult[];
  activity_status: HalalTestStatus | "unknown"; activity_threshold_pct: number;
  activity_citation: string; }
export interface HalalBusiness { status: string; categories?: string[];
  impermissible_revenue_pct?: { value: number | null; basis?: string } | null;
  evidence?: { quote: string; source_url: string; retrieved_at: string } | null;
  methodology_notes?: Record<string, { stance: string; reason: string }>;
  note?: string | null; confidence?: string; last_reviewed?: string; }
export interface HalalPurification { per_share: number | null;
  status: "computed" | "insufficient_data"; missing: string | null;
  basis: string | null; }
export interface HalalVerdict { symbol: string; layer: string | null;
  overall: HalalOverall; overall_basis: string;
  standards: Record<string, HalalStandardResult>; business: HalalBusiness;
  purification: HalalPurification; inputs_asof: string | null; }
export interface HalalData { generated_at: string; disclaimer: string;
  methodology_note: string; conventions: string[];
  verdicts: Record<string, HalalVerdict>; }
// display helpers (unit-tested):
export function overallLabel(o: HalalOverall): string;      // "Halal" | "Not halal" | "Questionable" | "Insufficient data"
export function overallTone(o: HalalOverall): "pass" | "fail" | "warn" | "muted";
export function fmtRatioPct(r: number | null): string;      // 0.0026 -> "0.26%" ; null -> "—"
```

- Produces in `web/lib/data.ts`: `getHalalData(): HalalData | null` (reads `public/data/halal.json`, cached, null-safe absent/corrupt — copy the `getNewsData` pattern exactly, lines 851–869) and `export type { ... } from "./halal"` re-exports.

- [ ] **Step 1: Write the failing test** — create `web/lib/halal.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { fmtRatioPct, overallLabel, overallTone } from "./halal";

describe("halal display helpers", () => {
  it("labels every overall verdict", () => {
    expect(overallLabel("halal")).toBe("Halal");
    expect(overallLabel("not_halal")).toBe("Not halal");
    expect(overallLabel("questionable")).toBe("Questionable");
    expect(overallLabel("insufficient_data")).toBe("Insufficient data");
  });
  it("maps verdicts to tones", () => {
    expect(overallTone("halal")).toBe("pass");
    expect(overallTone("not_halal")).toBe("fail");
    expect(overallTone("questionable")).toBe("warn");
    expect(overallTone("insufficient_data")).toBe("muted");
  });
  it("formats ratios as percentages, em-dash for null", () => {
    expect(fmtRatioPct(0.0026)).toBe("0.26%");
    expect(fmtRatioPct(0.5)).toBe("50.00%");
    expect(fmtRatioPct(null)).toBe("—");
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd web && npx vitest run lib/halal.test.ts` — Expected: FAIL (module missing).
- [ ] **Step 3: Implement** — create `web/lib/halal.ts` with the interfaces above plus:

```typescript
export function overallLabel(o: HalalOverall): string {
  return { halal: "Halal", not_halal: "Not halal", questionable: "Questionable",
           insufficient_data: "Insufficient data" }[o];
}
export function overallTone(o: HalalOverall): "pass" | "fail" | "warn" | "muted" {
  return { halal: "pass", not_halal: "fail", questionable: "warn",
           insufficient_data: "muted" }[o] as "pass" | "fail" | "warn" | "muted";
}
export function fmtRatioPct(r: number | null): string {
  if (r === null || r === undefined || Number.isNaN(r)) return "—";
  return `${(r * 100).toFixed(2)}%`;
}
```

Then append to `web/lib/data.ts` (after the news section):

```typescript
// ---- Halal screening (public/data/halal.json) ----
// Types + client-safe helpers live in lib/halal.ts (no node:fs); re-exported.
export type { HalalData, HalalVerdict, HalalOverall, HalalStandardResult,
  HalalTestResult, HalalBusiness, HalalPurification } from "./halal";
export { overallLabel, overallTone, fmtRatioPct } from "./halal";
import type { HalalData } from "./halal";

let cachedHalal: HalalData | null = null;
let halalLoaded = false;

export function getHalalData(): HalalData | null {
  if (halalLoaded) return cachedHalal;
  halalLoaded = true;
  const file = path.join(process.cwd(), "public", "data", "halal.json");
  if (!fs.existsSync(file)) { cachedHalal = null; return null; }
  try {
    cachedHalal = JSON.parse(fs.readFileSync(file, "utf-8")) as HalalData;
  } catch { cachedHalal = null; }
  return cachedHalal;
}
```

- [ ] **Step 4: Run tests** — `cd web && npx vitest run` — Expected: ALL PASS (halal + existing egograph). Then `npx tsc --noEmit` (or `npm run build` typecheck) — Expected: clean.
- [ ] **Step 5: Commit**

```bash
git add web/lib/halal.ts web/lib/halal.test.ts web/lib/data.ts
git commit -m "feat(halal): web types, client-safe helpers, getHalalData loader"
```

---

### Task 9: Stock-page verdict card — "Show the math"

**Files:**
- Create: `web/components/HalalCard.tsx` (server component — uses native `<details>` accordions, zero client JS)
- Modify: `web/app/stocks/[symbol]/page.tsx` (render `<HalalCard verdict={...} disclaimer={...} />` when `getHalalData()?.verdicts[symbol]` exists)

**Interfaces:**
- Consumes: `HalalVerdict`, helpers from `web/lib/halal.ts`.
- Produces: `<HalalCard verdict={HalalVerdict} disclaimer={string} conventions={string[]} />`.

**Before coding: read `web/node_modules/next/dist/docs/` guides for App Router server components (web/AGENTS.md — Next.js 16 differs from training data), and read the existing stock page to match its section structure and styling idioms.**

Component content requirements (all from spec §7):
- Header row: verdict badge (`overallLabel` + `overallTone` styling consistent with existing badge idioms), `overall_basis` note ("AAOIFI basis"), data-age (`inputs_asof`).
- One `<details>` per standard: summary = standard name + status chip; body = a table of tests (label, numerator value, denominator value, ratio via `fmtRatioPct`, threshold, margin — colored by sign, status) + activity row + each test's citation in small text.
- Business block: status, categories, note, methodology_notes forks rendered as "AAOIFI: pass — reason / Sector-exclusion: fail — reason", evidence quote + source link when present.
- Purification block: per-share value or "Insufficient data — {missing}".
- Footer: the disclaimer text + conventions in a `<details>` ("Our disclosed conventions").
- Verify: `cd web && npm run build` passes; manually load a stock page with and without `halal.json` present (card renders / is absent — no crash).
- Commit: `feat(halal): stock-page verdict card with worked per-standard math`

---

### Task 10: `/halal` page — screener table + methodology explainer

**Files:**
- Create: `web/app/halal/page.tsx` (server component: loads data, renders explainer + disclaimer + table)
- Create: `web/components/HalalTable.tsx` (client component: filterable table — model state handling on `ScreenerTable.tsx`)
- Modify: `web/components/Header.tsx` (add "Halal" nav link)

**Interfaces:**
- Consumes: `getHalalData()`, `getSiteData()` (for name/sector enrichment), lib helpers.
- Produces: route `/halal`.

**Before coding: read the Next.js 16 docs (as Task 9) and `web/components/ScreenerTable.tsx` + `web/app/screener/page.tsx` to mirror their table/filter idioms and styling.**

Page content requirements (spec §7):
- Hero: "Halal screening — the worked math, every standard, every number stamped." + `methodology_note` + `generated_at`.
- Methodology explainer section: the three standards' rules at a glance (threshold table), where they disagree, the four conventions, and the who-we-are-not disclaimer block (verbatim `disclaimer` from the bundle).
- `HalalTable`: one row per verdict — symbol (links to `/stocks/[symbol]`), layer, sector(s), overall badge, per-standard chips (AAOIFI/FTSE/MSCI status), business status, AAOIFI debt-ratio margin bar, `inputs_asof` age badge. Filters: All / Halal / Not halal / Questionable / Insufficient data; layer dropdown. Default sort: overall (halal first), then symbol.
- Empty state: if `getHalalData()` returns null, render the explainer + "Screening data not yet generated." (page must not crash — mirrors /news null handling).
- Verify: `npm run build` passes; `/halal` renders with the real `halal.json` from Task 12's pipeline run (or a locally generated one via Tasks 5–6 CLIs).
- Commit: `feat(halal): /halal screener page + methodology explainer + nav`

---

### Task 11: `/screener` halal badge column

**Files:**
- Modify: `web/app/screener/page.tsx` (pass `halal` map: `symbol -> HalalOverall`, built from `getHalalData()`)
- Modify: `web/components/ScreenerTable.tsx` (optional `halal?: Record<string, HalalOverall>` prop → when present, render a "Halal" column with the tone-colored label, linking to `/halal`)

**Interfaces:**
- Consumes: `getHalalData()`, `overallLabel`/`overallTone`.
- Produces: optional badge column; **prop absent → table renders exactly as today** (backward-compatible — congress/quantum uses of the table unaffected).

- Verify: `npm run build`; `/screener` shows badges when halal.json exists, unchanged when absent.
- Commit: `feat(halal): halal verdict badge column on the main screener`

---

### Task 12: Full pipeline run, live validation, deploy

**Files:** none created — this is the end-to-end verification + ship task.

- [ ] **Step 1: Full test suites** — `cd scripts && python -m pytest -q` (ALL pass, including pre-existing) and `cd web && npx vitest run && npm run build` (clean).
- [ ] **Step 2: Live pipeline** — `cd scripts && python pull_halal.py --verify-columns` (Expected: `missing=none` — the spec §8 metainfo gate), then `python pull_halal.py && python export_halal.py`. Expected: `verdicts=128` (or 128 minus unresolved tickers, each listed), breakdown printed. **Sanity-check against research expectations:** JPM/GS/BCS/BBVA/HSBC/INTU = `not_halal`; NVDA/AMD/ASML = `halal`; most regulated utilities (SO, D, DUK, AEP...) = `not_halal` with `aaoifi_debt` status `fail` (their business is clean — the ratio kills them; confirm the standards block shows exactly that); IREN/CORZ/WULF/APLD/APP/BWXT/HPE/BTQ = `questionable`. Paste the actual breakdown into the task report.
- [ ] **Step 3: Dry-run the orchestrator** — `python refresh_daily.py --dry-run` shows the halal steps in order.
- [ ] **Step 4: Local render check** — `cd web && npm run dev`, load `/halal` and 3 stock pages (NVDA halal, JPM not_halal, IREN questionable): verdict cards show worked math, citations, provenance timestamps, disclaimer.
- [ ] **Step 5: Deploy** — `cd web && vercel --prod --yes`. Load the production `/halal` URL; verify verdicts + timestamps render.
- [ ] **Step 6: Commit any remaining artifacts + tag the release**

```bash
git add -A
git commit -m "feat(halal): v1 ship — live halal.json + validated deploy"
git tag halal-v1
```

---

## Self-Review (run after writing, before execution)

1. **Spec coverage:** §2 thresholds → Task 2 STANDARDS; §3 flow → Tasks 5/6/7; §4 engine+conventions → Task 2; §5 curated file → Task 4; §6 verdict/purification → Task 3; §7 web surfaces → Tasks 8–11; §8 tests/failure posture → every task + Task 6 provenance gate; §9 v1 ladder → Task 12. Deviation from spec §5: evidence quote/source live in an `evidence` object (not nested in `impermissible_revenue_pct`) so questionable-without-pct entries carry evidence too — spec's enforcement intent (non-clean ⇒ quote+source) is kept and tested.
2. **Placeholders:** Task 4's `DETAILED` dict is intentionally abridged in-plan with an explicit completion instruction + validation gate (`validate_business_activity` + `test_business_activity_known_seed_classifications` make missing content a hard test failure — it cannot ship abridged).
3. **Type consistency:** `HALAL_COLUMNS` (T1) → `pull_halal.scan(columns=...)` (T5); envelope metrics keys (T5 batch) → `inputs_from_metrics` (T2); `verdict()` output keys (T3) → `export_halal.build` (T6) → `web/lib/halal.ts` interfaces (T8) → components (T9–11). `status` enums match across Python and TS ("pass"/"fail"/"unknown"; overall enum identical).
