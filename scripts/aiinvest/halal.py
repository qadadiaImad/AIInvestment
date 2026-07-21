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


# ---------------------------------------------------------------------------
# Task 4: curated business-activity loader + validator
# ---------------------------------------------------------------------------
import json as _json
import pathlib as _pathlib

_ACTIVITY_PATH = (_pathlib.Path(__file__).resolve().parent
                  / "data" / "halal" / "business_activity.json")
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
