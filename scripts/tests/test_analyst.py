"""RED tests for the deterministic fact-sheet generator."""
from aiinvest import analyst

NOW = "2026-05-30T13:00:00Z"

DOSSIER = {
    "symbol": "NVDA", "layer": "L1-chips", "as_of": NOW,
    "metrics": {
        "current_price": {"value": 211.14, "sources": ["tradingview", "yahoo"], "agree": True, "stale": False},
        "gf_value": {"value": 334.32, "stale": False},
        "price_earnings_ttm": {"value": 32.33, "stale": False},
        "valuation_verdict": {"value": "Possible Value Trap", "stale": False},
    },
    "filings": [{"form": "10-K", "filing_date": "2026-02-25"}],
    "catalysts": [{"id": "NVDA-earnings", "date": "2026-08-26", "type": "earnings", "entities": ["NVDA"]}],
    "relationships": {
        "edges_from": [],
        "edges_to": [{"src": "anthropic", "dst": "NVDA", "type": "compute_commitment", "attrs": {}}],
        "lab_exposure": [],
    },
}


def test_discount_pct_is_gf_value_vs_price():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert fs["valuation"]["discount_pct"] == 36.8  # (334.32-211.14)/334.32*100


def test_profitability_flag_profitable_for_positive_pe():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert fs["valuation"]["profitability"] == "profitable"


def test_constraint_pulled_for_layer():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert "packaging" in fs["constraint"]["physical_bottleneck"].lower() \
        or "hbm" in fs["constraint"]["physical_bottleneck"].lower()


def test_value_trap_verdict_raises_risk_flag():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert any("trap" in f.lower() for f in fs["risk_flags"])


def test_relationships_list_counterparties():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert any(c["node"] == "anthropic" for c in fs["relationships"]["counterparties"])


def test_catalysts_carried_through():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert fs["catalysts"][0]["id"] == "NVDA-earnings"


def test_stale_metric_appears_in_verify_live():
    d = {**DOSSIER, "metrics": {**DOSSIER["metrics"],
         "current_price": {"value": 211.14, "stale": True}}}
    fs = analyst.fact_sheet(d, NOW)
    assert "current_price" in fs["verify_live"]


def test_private_lab_is_pre_revenue_venture():
    d = {"symbol": "anthropic", "layer": "private-lab", "as_of": NOW,
         "metrics": {}, "filings": [], "catalysts": [],
         "relationships": {"edges_from": [], "edges_to": [], "lab_exposure": []}}
    fs = analyst.fact_sheet(d, NOW)
    assert fs["valuation"]["profitability"].startswith("pre-revenue")
    assert any("venture" in f.lower() for f in fs["risk_flags"])


# --- enriched fundamentals + performance blocks ---

DOSSIER_FUND = {
    "symbol": "NVDA", "layer": "L1-chips", "as_of": NOW,
    "metrics": {
        "net_margin_ttm": {"value": 55.2},
        "return_on_equity": {"value": 119.3},
        "total_revenue_yoy_growth_ttm": {"value": 114.0},
        "Perf.Y": {"value": 23.4},
        "industry": {"value": "Semiconductors"},
    },
    "filings": [], "catalysts": [],
    "relationships": {"edges_from": [], "edges_to": [], "lab_exposure": []},
}


def test_fundamentals_block_populated():
    fs = analyst.fact_sheet(DOSSIER_FUND, NOW)
    assert fs["fundamentals"]["net_margin"] == 55.2
    assert fs["fundamentals"]["roe"] == 119.3
    assert fs["fundamentals"]["rev_growth_yoy"] == 114.0
    assert fs["fundamentals"]["industry"] == "Semiconductors"


def test_performance_block_populated():
    fs = analyst.fact_sheet(DOSSIER_FUND, NOW)
    assert fs["performance"]["perf_1y"] == 23.4


def test_fundamentals_absent_metrics_are_none():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert fs["fundamentals"]["roic"] is None
    assert fs["performance"]["beta"] is None


def test_existing_keys_unchanged_with_new_blocks():
    fs = analyst.fact_sheet(DOSSIER, NOW)
    assert fs["valuation"]["discount_pct"] == 36.8
    assert fs["symbol"] == "NVDA"


def test_peer_and_history_passthrough_from_dossier():
    d = {**DOSSIER,
         "peer_stats": {"industry": {"net_margin_ttm": {"value": 63.0, "percentile": 92.0}}},
         "history": {"annualTotalRevenue": [{"date": "2025-01-31", "value": 130e9}]}}
    fs = analyst.fact_sheet(d, NOW)
    assert fs["peer_comparison"]["industry"]["net_margin_ttm"]["percentile"] == 92.0
    assert fs["history"]["annualTotalRevenue"][0]["value"] == 130e9
