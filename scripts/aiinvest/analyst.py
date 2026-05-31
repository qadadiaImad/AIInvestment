"""Deterministic fact-sheet generator — the analyzable facts behind a dashboard.

Reads a dossier (dossier.build_dossier output) and computes valuation math, the relevant
constraint, relationship/risk summary, catalysts, and freshness flags. No interpretation
and no invented numbers — the narrative/scenarios are the LLM (analyst skill) layer.
"""
from __future__ import annotations

from . import constraints


def _v(metrics, name):
    m = metrics.get(name) or {}
    return m.get("value")


def fact_sheet(dossier, now):
    metrics = dossier.get("metrics", {})
    layer = dossier.get("layer")
    symbol = dossier.get("symbol")

    price = _v(metrics, "current_price")
    gf_value = _v(metrics, "gf_value")
    pe = _v(metrics, "price_earnings_ttm")
    verdict = _v(metrics, "valuation_verdict")

    discount_pct = None
    if isinstance(price, (int, float)) and isinstance(gf_value, (int, float)) and gf_value:
        discount_pct = round((gf_value - price) / gf_value * 100, 1)

    if layer == "private-lab" or pe is None or (isinstance(pe, (int, float)) and pe < 0):
        profitability = "pre-revenue / venture bet (size accordingly, not a value buy)"
    else:
        profitability = "profitable"

    # relationships
    rels = dossier.get("relationships", {})
    counterparties, single_cp = [], []
    for e in rels.get("edges_from", []) + rels.get("edges_to", []):
        other = e["dst"] if e["src"] == symbol else e["src"]
        attrs = e.get("attrs", {})
        usd = attrs.get("usd") or attrs.get("usd_per_month")
        counterparties.append({"node": other, "type": e["type"], "usd": usd})
        if attrs.get("termination_days") is not None:
            single_cp.append(f"{other}: {attrs['termination_days']}-day termination ({e['type']})")
    lab_exposure = rels.get("lab_exposure", [])

    # freshness
    verify_live = [name for name, m in metrics.items() if (m or {}).get("stale")]

    # risk flags
    risk_flags = []
    if profitability.startswith("pre-revenue"):
        risk_flags.append("Pre-revenue / story-stock: size as venture bet, not value buy")
    if layer == "private-lab":
        risk_flags.append("Pre-IPO: lockup & 'pop-then-drop' risk at the open")
    if verdict and "trap" in str(verdict).lower():
        risk_flags.append(f"GuruFocus value-trap warning ('{verdict}')")
    if isinstance(pe, (int, float)) and pe > 100:
        risk_flags.append(f"Extreme P/E ({pe:.0f}) — priced for perfection")
    if single_cp:
        risk_flags.append("Single-counterparty lease with short termination — concentration risk")
    if lab_exposure:
        risk_flags.append("Indirect private-lab exposure (pre-IPO valuation sensitivity)")

    return {
        "symbol": symbol,
        "layer": layer,
        "as_of": now,
        "valuation": {
            "price": price, "gf_value": gf_value, "discount_pct": discount_pct,
            "pe": pe, "verdict": verdict, "profitability": profitability,
        },
        "constraint": constraints.for_node(layer, symbol),
        "relationships": {
            "counterparties": counterparties,
            "single_counterparty_flags": single_cp,
            "lab_exposure": lab_exposure,
        },
        "fundamentals": {
            "gross_margin": _v(metrics, "gross_margin_ttm"),
            "operating_margin": _v(metrics, "operating_margin_ttm"),
            "net_margin": _v(metrics, "net_margin_ttm"),
            "fcf_margin": _v(metrics, "free_cash_flow_margin_ttm"),
            "roe": _v(metrics, "return_on_equity"),
            "roa": _v(metrics, "return_on_assets"),
            "roic": _v(metrics, "return_on_invested_capital"),
            "debt_to_equity": _v(metrics, "debt_to_equity"),
            "current_ratio": _v(metrics, "current_ratio"),
            "ps": _v(metrics, "price_sales_current"),
            "pb": _v(metrics, "price_book_fq"),
            "pfcf": _v(metrics, "price_free_cash_flow_ttm"),
            "rev_growth_yoy": _v(metrics, "total_revenue_yoy_growth_ttm"),
            "eps_growth_yoy": _v(metrics, "earnings_per_share_diluted_yoy_growth_ttm"),
            "sector": _v(metrics, "sector"),
            "industry": _v(metrics, "industry"),
        },
        "performance": {
            "perf_1y": _v(metrics, "Perf.Y"),
            "perf_ytd": _v(metrics, "Perf.YTD"),
            "beta": _v(metrics, "beta_1_year"),
        },
        "peer_comparison": dossier.get("peer_stats", {}),
        "history": dossier.get("history", {}),
        "catalysts": dossier.get("catalysts", []),
        "verify_live": verify_live,
        "risk_flags": risk_flags,
    }
