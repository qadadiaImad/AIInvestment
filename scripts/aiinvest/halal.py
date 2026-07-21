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
