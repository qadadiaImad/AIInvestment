"""RED tests for the per-ticker HTML dashboard renderer."""
from aiinvest import dashboard

FS = {
    "symbol": "NVDA", "layer": "L1-chips", "as_of": "2026-05-30T13:00:00Z",
    "valuation": {"price": 211.14, "gf_value": 334.32, "discount_pct": 36.8, "pe": 32.33,
                  "verdict": "Possible Value Trap", "profitability": "profitable"},
    "constraint": {"physical_bottleneck": "CoWoS packaging + HBM",
                   "regulatory_bottleneck": "GPU export controls", "lead_time_note": "quarters-to-years"},
    "relationships": {"counterparties": [{"node": "anthropic", "type": "compute_commitment", "usd": None}],
                      "single_counterparty_flags": [], "lab_exposure": []},
    "catalysts": [{"id": "NVDA-earnings", "date": "2026-08-26", "title": "NVDA earnings", "type": "earnings"}],
    "verify_live": ["current_price"],
    "risk_flags": ["Extreme P/E (32) — priced for perfection"],
}

NARR = {"valuation_take": "Trades below GF Value but flagged a trap.",
        "bottleneck_rationale": "HBM is the binding constraint.",
        "scenarios": ["Bull: packaging eases", "Bear: export controls tighten"],
        "risks": ["Concentration"], "synthesis": "Power + packaging are the scarce links."}


def test_starts_with_doctype_and_shows_symbol_layer():
    html = dashboard.to_html(FS, NARR)
    assert html.strip().lower().startswith("<!doctype html")
    assert "NVDA" in html and "L1-chips" in html


def test_renders_narrative_sections():
    html = dashboard.to_html(FS, NARR)
    assert "packaging eases" in html
    assert "scarce links" in html


def test_verify_live_indicator_when_stale_present():
    html = dashboard.to_html(FS, NARR)
    assert "verify live" in html.lower()


def test_disclaimer_always_present():
    html = dashboard.to_html(FS, NARR)
    assert "not financial advice" in html.lower()


def test_tolerates_missing_values_and_empty_narrative():
    fs = {**FS, "valuation": {**FS["valuation"], "gf_value": None, "discount_pct": None},
          "verify_live": []}
    html = dashboard.to_html(fs, {})
    assert html.strip().lower().startswith("<!doctype html")
    assert "not financial advice" in html.lower()


# --- enriched sections: fundamentals, performance, peer comparison ---

FS_RICH = {
    **FS,
    "fundamentals": {"gross_margin": 74.1, "operating_margin": 64.0, "net_margin": 63.0,
                     "fcf_margin": 41.8, "roe": 114.3, "roa": 83.0, "roic": 106.2,
                     "debt_to_equity": 0.07, "current_ratio": 3.44, "ps": 20.6, "pb": 26.2,
                     "pfcf": 48.5, "rev_growth_yoy": 70.7, "eps_growth_yoy": 110.3,
                     "sector": "Electronic Technology", "industry": "Semiconductors"},
    "performance": {"perf_1y": 48.4, "perf_ytd": 11.2, "beta": 1.45},
    "peer_comparison": {
        "industry": {"net_margin_ttm": {"value": 63.0, "median": 29.7, "percentile": 92.0, "n": 150}},
        "layer": {"net_margin_ttm": {"value": 63.0, "median": 41.5, "percentile": 80.0, "n": 26}},
    },
}


def test_fundamentals_section_renders_values():
    html = dashboard.to_html(FS_RICH, NARR)
    assert "74.1" in html        # gross margin
    assert "114.3" in html       # ROE
    assert "Semiconductors" in html


def test_performance_section_renders():
    html = dashboard.to_html(FS_RICH, NARR)
    assert "48.4" in html        # 1Y perf


def test_peer_comparison_renders_percentile():
    html = dashboard.to_html(FS_RICH, NARR)
    assert "92" in html          # industry percentile for net margin
    assert "29.7" in html        # industry median


def test_rich_sections_optional_when_absent():
    # The base FS (no fundamentals/peer blocks) must still render fine.
    html = dashboard.to_html(FS, NARR)
    assert html.strip().lower().startswith("<!doctype html")
    assert "not financial advice" in html.lower()


# --- multi-year history sparklines ---

FS_HIST = {
    **FS_RICH,
    "history": {
        "annualTotalRevenue": [{"date": "2024-01-31", "value": 60.9e9},
                               {"date": "2025-01-31", "value": 130.5e9},
                               {"date": "2026-01-31", "value": 215.9e9}],
        "annualNetIncome": [{"date": "2024-01-31", "value": 29.8e9},
                            {"date": "2025-01-31", "value": 72.9e9},
                            {"date": "2026-01-31", "value": 120e9}],
    },
}


def test_sparkline_returns_svg_polyline():
    svg = dashboard._sparkline([1, 2, 4, 8])
    assert svg.startswith("<svg")
    assert "polyline" in svg.lower()


def test_sparkline_empty_is_blank():
    assert dashboard._sparkline([]) == ""


def test_history_section_renders_sparkline():
    html = dashboard.to_html(FS_HIST, NARR)
    assert "<svg" in html
    assert "polyline" in html.lower()


def test_history_absent_still_renders():
    html = dashboard.to_html(FS, NARR)  # no history key
    assert html.strip().lower().startswith("<!doctype html")
