"""RED tests for the public-site exporter sanitizer — must strip ALL GuruFocus content."""
from aiinvest import siteexport


FACTSHEET = {
    "symbol": "NVDA", "layer": "L1-chips", "as_of": "2026-05-30T13:00:00Z",
    "valuation": {"price": 211.14, "gf_value": 334.32, "discount_pct": 36.8, "pe": 32.33,
                  "verdict": "Possible Value Trap", "profitability": "profitable"},
    "fundamentals": {"net_margin": 63.0, "roe": 114.3, "sector": "Electronic Technology"},
    "performance": {"perf_1y": 48.4},
    "peer_comparison": {"industry": {"net_margin_ttm": {"value": 63.0, "percentile": 92.0}}},
    "history": {"annualTotalRevenue": [{"date": "2025-01-31", "value": 130e9}]},
    "constraint": {"physical_bottleneck": "CoWoS packaging + HBM"},
    "catalysts": [{"id": "NVDA-earnings", "date": "2026-08-26"}],
    "relationships": {"counterparties": [{"node": "TSM", "type": "customer"}]},
    "risk_flags": ["GuruFocus value-trap warning ('Possible Value Trap')",
                   "Extreme P/E (32) — priced for perfection"],
}
NARRATIVE = {
    "valuation_take": "At ~$211 the stock screens ~37% below GuruFocus's ~$334 GF Value.",
    "bottleneck_rationale": "HBM is the binding constraint.",
    "scenarios": ["Bull: packaging eases", "Base: GF Value gap closes"],
    "risks": ["Customer concentration"],
    "synthesis": "Power + packaging are the scarce links.",
}


def test_valuation_drops_gf_fields_keeps_pe():
    s = siteexport.sanitize_stock(FACTSHEET, NARRATIVE)
    assert "gf_value" not in s["valuation"]
    assert "discount_pct" not in s["valuation"]
    assert "verdict" not in s["valuation"]
    assert s["valuation"]["pe"] == 32.33
    assert s["valuation"]["price"] == 211.14


def test_gf_risk_flag_removed_other_kept():
    s = siteexport.sanitize_stock(FACTSHEET, NARRATIVE)
    assert not any("guru" in f.lower() for f in s["risk_flags"])
    assert any("P/E" in f for f in s["risk_flags"])


def test_narrative_gf_mentions_removed():
    s = siteexport.sanitize_stock(FACTSHEET, NARRATIVE)
    # valuation_take mentioned GuruFocus -> dropped; a scenario mentioned GF Value -> filtered.
    assert "valuation_take" not in s["narrative"]
    assert all("gf value" not in x.lower() for x in s["narrative"].get("scenarios", []))
    assert s["narrative"]["bottleneck_rationale"]  # clean field kept


def test_no_gurufocus_substring_anywhere():
    import json
    s = siteexport.sanitize_stock(FACTSHEET, NARRATIVE)
    blob = json.dumps(s).lower()
    for term in ("guru", "gf value", "gf_value", "value trap", "gf score"):
        assert term not in blob, f"leaked: {term}"


def test_keeps_fundamentals_peers_history_constraint():
    s = siteexport.sanitize_stock(FACTSHEET, NARRATIVE)
    assert s["fundamentals"]["roe"] == 114.3
    assert s["peer_comparison"]["industry"]["net_margin_ttm"]["percentile"] == 92.0
    assert s["history"]["annualTotalRevenue"][0]["value"] == 130e9
    assert "CoWoS" in s["constraint"]["physical_bottleneck"]
