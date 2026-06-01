"""Tests for export_quantum.py — assembles web/public/data/quantum.json.

PURE FUNCTION focus (`build`) — no filesystem writes. We feed a small synthetic
TradingView-batch fixture (mirroring what pull_quantum.py writes to data/quantum/)
plus fundamental_value records, and assert on the merged bundle the site consumes.

Honesty rails (CLAUDE.md / spec):
- NEVER reference GuruFocus — the bundle must be byte-clean of the banned terms.
- Every stock + capital_web node carries sector:"Quantum".
- Pre-revenue pure-plays show NULLs, not fabricated numbers.
- capital_web comes from quantum_capital_web.build_graph() and must validate.
"""
import json

import export_quantum as eq
from aiinvest import quantum_stack


def _env(value, unit="usd", raw=None):
    """A TradingView-style stamped envelope (schema.make_envelope shape)."""
    return {
        "value": value,
        "raw": raw if raw is not None else value,
        "unit": unit,
        "dirty": False,
        "retrieved_at": "2026-06-01T00:00:00Z",
        "source": "tradingview",
        "source_url": "https://scanner.tradingview.com/america/scan",
        "source_class": "api",
    }


def _record(sym, ticker, *, price=None, pe=None, net_margin=None, roe=None,
            rev_growth=None, perf_y=None, desc=None, next_earn=None):
    return {
        "symbol": sym,
        "ticker": ticker,
        "stack_layer": quantum_stack.layer_of(ticker),
        "as_of": "2026-06-01T00:00:00Z",
        "metrics": {
            "description": _env(desc, unit="text"),
            "close": _env(price),
            "price_earnings_ttm": _env(pe, unit="ratio"),
            "net_margin_ttm": _env(net_margin, unit="pct"),
            "return_on_equity": _env(roe, unit="pct"),
            "total_revenue_yoy_growth_ttm": _env(rev_growth, unit="pct"),
            "Perf.Y": _env(perf_y, unit="pct"),
            "earnings_release_next_date": _env(next_earn, unit="text"),
        },
    }


def _batch():
    """A minimal quantum TradingView batch (data/quantum/<date>/...json shape)."""
    return {
        "batch_metadata": {
            "batch_timestamp": "2026-06-01T00:00:00Z",
            "total_symbols_requested": 3,
            "successful_symbols": 2,
            "failed_symbols": ["NASDAQ:HQ"],
            "retrieval_mode": "rest",
            "providers_used": ["tradingview"],
        },
        "financial_data": {
            # profitable demand-side name (Q5) — has real numbers
            "JPM": _record("JPM", "NYSE:JPM", price=270.0, pe=13.5, net_margin=31.0,
                           roe=16.0, rev_growth=8.0, perf_y=22.0, desc="JPMorgan Chase",
                           next_earn="2026-07-15"),
            # pre-revenue pure-play (Q1) — mostly NULL, must NOT be fabricated
            "IONQ": _record("IONQ", "NYSE:IONQ", price=45.0, pe=None, net_margin=None,
                            roe=None, rev_growth=None, perf_y=120.0, desc="IonQ Inc"),
        },
    }


def _fundamentals():
    """fundamental_value records keyed by bare symbol (data/fundamental-style)."""
    return {
        "JPM": {"symbol": "JPM", "fundamental_value": 320.0,
                "margin_of_safety_pct": 9.4,
                "fundamental_value_series": [{"date": "2025-01-31", "value": 300.0}],
                "source": "fundamental-model"},
        # IONQ pre-revenue: no intrinsic value model -> absent
    }


# --------------------------------------------------------------------------- shape

def test_bundle_has_required_top_level_keys():
    out = eq.build(_batch(), _fundamentals())
    for k in ("generated_at", "disclaimer", "sources", "layers", "stocks",
              "capital_web", "screener"):
        assert k in out, f"missing key {k}"
    assert out["generated_at"].endswith("Z")


def test_layers_mirror_quantum_stack():
    out = eq.build(_batch(), _fundamentals())
    # layers map layer -> bare symbols, exactly the quantum_stack universe
    assert set(out["layers"]) == set(quantum_stack.LAYERS)
    assert "IONQ" in out["layers"]["Q1-hardware"]
    assert "JPM" in out["layers"]["Q5-applications"]


def test_every_stock_stamped_quantum_sector():
    out = eq.build(_batch(), _fundamentals())
    assert out["stocks"]  # non-empty
    for sym, s in out["stocks"].items():
        assert s["sector"] == "Quantum", f"{sym} not stamped Quantum"


def test_capital_web_nodes_stamped_quantum_and_validate():
    from aiinvest import quantum_capital_web
    out = eq.build(_batch(), _fundamentals())
    g = out["capital_web"]
    assert g["nodes"] and g["edges"]
    for n in g["nodes"]:
        assert n["sector"] == "Quantum"
    # the graph must still validate (no dangling edges)
    quantum_capital_web.validate(g)


def test_fundamental_value_folded_in_and_tagged():
    out = eq.build(_batch(), _fundamentals())
    jpm = out["stocks"]["JPM"]["valuation"]
    assert jpm["fundamental_value"] == 320.0
    # our own tag computed from live price (270 vs 320 -> undervalued)
    assert jpm["fundamental_valuation"] == "Undervalued"
    assert jpm["fundamental_discount_pct"] is not None


def test_pre_revenue_stock_shows_nulls_not_fabricated():
    out = eq.build(_batch(), _fundamentals())
    ionq = out["stocks"]["IONQ"]
    assert ionq["valuation"].get("pe") is None
    assert ionq["fundamentals"].get("net_margin") is None
    # no fundamental_value was supplied -> must be absent/None, never invented
    assert ionq["valuation"].get("fundamental_value") is None


def test_screener_rows_one_per_stock():
    out = eq.build(_batch(), _fundamentals())
    syms = {r["symbol"] for r in out["screener"]}
    assert syms == set(out["stocks"])
    jpm = next(r for r in out["screener"] if r["symbol"] == "JPM")
    assert jpm["layer"] == "Q5-applications"
    assert jpm["price"] == 270.0
    assert jpm["fundamental_value"] == 320.0


def test_no_gurufocus_leak_anywhere():
    out = eq.build(_batch(), _fundamentals())
    blob = json.dumps(out).lower()
    for term in ("guru", "gf value", "gf_value", "value trap", "gf score"):
        assert term not in blob, f"leaked: {term}"


def test_disclaimer_is_educational_not_advice():
    out = eq.build(_batch(), _fundamentals())
    d = out["disclaimer"].lower()
    assert "not" in d and "advice" in d


def test_missing_fundamentals_arg_is_optional():
    # build must work with no fundamental_value records at all
    out = eq.build(_batch(), {})
    assert out["stocks"]["JPM"]["valuation"].get("fundamental_value") is None
