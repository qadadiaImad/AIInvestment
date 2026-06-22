"""RED tests for the one-ticker dossier assembler (the data-side capstone)."""
from aiinvest import dossier


NOW = "2026-05-30T13:00:00Z"

TV = {"metrics": {"close": {"value": 211.14, "retrieved_at": NOW},
                  "price_earnings_ttm": {"value": 32.33, "retrieved_at": NOW}}}
YH = {"metrics": {"current_price": {"value": 211.14, "retrieved_at": NOW}}}
GF = {"metrics": {"gf_value": {"value": 334.32, "retrieved_at": NOW}}}

GRAPH = {
    "nodes": [
        {"id": "NVDA", "name": "NVIDIA", "type": "public", "ticker": "NASDAQ:NVDA", "layer": "L1-chips"},
        {"id": "anthropic", "name": "Anthropic", "type": "private", "ticker": None, "layer": "private-lab"},
    ],
    "edges": [
        {"src": "anthropic", "dst": "NVDA", "type": "compute_commitment", "attrs": {},
         "certainty": "reported", "source_class": "x", "source_url": "x", "retrieved_at": NOW},
    ],
}

CATS = [
    {"id": "NVDA-earnings", "date": "2026-08-26", "type": "earnings", "entities": ["NVDA"],
     "certainty": "reported", "source_class": "api", "source_url": "tradingview", "retrieved_at": NOW},
    {"id": "anthropic-ipo", "date": "2026-10-01", "type": "ipo", "entities": ["anthropic"],
     "certainty": "reported", "source_class": "x", "source_url": "x", "retrieved_at": NOW},
]

FILINGS = [{"form": "10-K", "filing_date": "2026-02-25", "accession": "0001045810-26-000021"}]


def test_dossier_has_symbol_and_layer():
    d = dossier.build_dossier("NVDA", {"tradingview": TV, "yahoo": YH}, FILINGS, CATS, GRAPH, NOW)
    assert d["symbol"] == "NVDA"
    assert d["layer"] == "L1-chips"
    assert d["as_of"] == NOW


def test_dossier_merges_metrics_cross_source():
    d = dossier.build_dossier("NVDA", {"tradingview": TV, "yahoo": YH, "gurufocus": GF}, FILINGS, CATS, GRAPH, NOW)
    px = d["metrics"]["current_price"]
    assert px["value"] == 211.14
    assert set(px["sources"]) == {"tradingview", "yahoo"}
    assert d["metrics"]["gf_value"]["value"] == 334.32


def test_dossier_attaches_only_this_tickers_catalysts():
    d = dossier.build_dossier("NVDA", {"tradingview": TV}, FILINGS, CATS, GRAPH, NOW)
    ids = {c["id"] for c in d["catalysts"]}
    assert ids == {"NVDA-earnings"}  # anthropic-ipo is not NVDA's catalyst


def test_dossier_attaches_relationships():
    d = dossier.build_dossier("NVDA", {"tradingview": TV}, FILINGS, CATS, GRAPH, NOW)
    rel = d["relationships"]
    # Anthropic has a compute commitment TO Nvidia -> inbound edge.
    assert any(e["src"] == "anthropic" for e in rel["edges_to"])


def test_dossier_includes_filings():
    d = dossier.build_dossier("NVDA", {"tradingview": TV}, FILINGS, CATS, GRAPH, NOW)
    assert d["filings"][0]["form"] == "10-K"
