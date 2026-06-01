"""Tests for the congress-stocks slice.

PURE FUNCTION focus — no network, no filesystem writes:
  - aiinvest.congress_stocks.rank_top_congress_tickers: top-N by trade count, EXCLUDES
    covered (AI/Quantum) names, tie-broken alphabetically, deterministic.
  - export_congress_stocks.build: sector stamping ("Congress"), history fold,
    fundamental_value optional, and byte-clean of the gated-source terms.

Honesty rails (CLAUDE.md / spec):
- NEVER reference GuruFocus — the bundle must be byte-clean of the banned terms.
- Every stock carries sector:"Congress"; no curated capital_web graph for this slice.
- Missing fundamentals show NULLs, never fabricated numbers.
- The universe is the tail of self-reported, unverified congressional filings.
"""
import json

import export_congress_stocks as ec
from aiinvest import congress_stocks


# --------------------------------------------------------------------------- rank

def _doc(trades):
    return {"trades": [{"ticker": t} for t in trades]}


def test_rank_counts_and_orders_by_trade_count():
    # AAPL x3, MSFT x2, TSLA x1 -> ordered by descending count
    doc = _doc(["AAPL", "AAPL", "AAPL", "MSFT", "MSFT", "TSLA"])
    assert congress_stocks.rank_top_congress_tickers(doc, covered=set()) == \
        ["AAPL", "MSFT", "TSLA"]


def test_rank_top_n_truncates():
    doc = _doc(["A", "A", "B", "B", "C"])  # A=2, B=2, C=1
    assert congress_stocks.rank_top_congress_tickers(doc, covered=set(), n=2) == ["A", "B"]


def test_rank_tie_break_is_alphabetical():
    # BBB and AAA both appear twice -> alphabetical tie-break
    doc = _doc(["BBB", "BBB", "AAA", "AAA"])
    assert congress_stocks.rank_top_congress_tickers(doc, covered=set()) == ["AAA", "BBB"]


def test_rank_excludes_covered_names_bare_compare():
    doc = _doc(["NVDA", "NVDA", "NVDA", "PFE", "PFE", "JNJ"])
    # NVDA covered (bare), and pass a covered with an exchange prefix to prove bare compare
    covered = {"NVDA", "NASDAQ:JNJ"}
    out = congress_stocks.rank_top_congress_tickers(doc, covered=covered)
    assert "NVDA" not in out and "JNJ" not in out
    assert out == ["PFE"]


def test_rank_drops_empty_tickers_and_strips_exchange():
    doc = {"trades": [
        {"ticker": "NASDAQ:PFE"}, {"ticker": "PFE"},
        {"ticker": ""}, {"ticker": None}, {},
    ]}
    out = congress_stocks.rank_top_congress_tickers(doc, covered=set())
    assert out == ["PFE"]  # both PFE rows collapse to the bare symbol, count=2


def test_rank_deterministic():
    doc = _doc(["X", "X", "Y", "Z", "Z", "Z"])
    a = congress_stocks.rank_top_congress_tickers(doc, covered=set())
    b = congress_stocks.rank_top_congress_tickers(doc, covered=set())
    assert a == b == ["Z", "X", "Y"]


def test_rank_empty_doc_is_empty():
    assert congress_stocks.rank_top_congress_tickers({}, covered=set()) == []
    assert congress_stocks.rank_top_congress_tickers({"trades": []}, covered=set()) == []


# --------------------------------------------------------------------------- export

def _env(value, unit="usd", raw=None):
    return {
        "value": value, "raw": raw if raw is not None else value, "unit": unit,
        "dirty": False, "retrieved_at": "2026-06-01T00:00:00Z", "source": "tradingview",
        "source_url": "https://scanner.tradingview.com/america/scan", "source_class": "api",
    }


def _record(sym, ticker, *, price=None, pe=None, net_margin=None, roe=None,
            rev_growth=None, perf_y=None, desc=None, next_earn=None):
    return {
        "symbol": sym, "ticker": ticker, "stack_layer": None,
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
    return {
        "batch_metadata": {
            "batch_timestamp": "2026-06-01T00:00:00Z", "sector": "Congress",
            "total_symbols_requested": 2, "successful_symbols": 2,
            "failed_symbols": [], "retrieval_mode": "rest",
            "providers_used": ["tradingview"],
        },
        "financial_data": {
            "PFE": _record("PFE", "NYSE:PFE", price=27.0, pe=11.0, net_margin=20.0,
                           roe=14.0, rev_growth=3.0, perf_y=5.0, desc="Pfizer Inc",
                           next_earn="2026-07-29"),
            "DIS": _record("DIS", "NYSE:DIS", price=110.0, pe=None, net_margin=None,
                           roe=None, rev_growth=None, perf_y=12.0, desc="Walt Disney Co"),
        },
    }


def _fundamentals():
    return {
        "PFE": {"symbol": "PFE", "fundamental_value": 40.0,
                "margin_of_safety_pct": 12.0,
                "fundamental_value_series": [{"date": "2025-01-31", "value": 38.0}]},
    }


def test_bundle_has_required_top_level_keys():
    out = ec.build(_batch(), _fundamentals())
    for k in ("generated_at", "disclaimer", "sources", "stocks", "capital_web", "screener"):
        assert k in out, f"missing key {k}"
    assert out["generated_at"].endswith("Z")


def test_every_stock_stamped_congress_sector():
    out = ec.build(_batch(), _fundamentals())
    assert out["stocks"]
    for sym, s in out["stocks"].items():
        assert s["sector"] == "Congress", f"{sym} not stamped Congress"


def test_no_curated_capital_web_for_congress():
    out = ec.build(_batch(), _fundamentals())
    g = out["capital_web"]
    assert g == {"nodes": [], "edges": []}


def test_fundamental_value_folded_in_and_tagged():
    out = ec.build(_batch(), _fundamentals())
    pfe = out["stocks"]["PFE"]["valuation"]
    assert pfe["fundamental_value"] == 40.0
    # 27 vs 40 -> undervalued; discount positive
    assert pfe["fundamental_valuation"] == "Undervalued"
    assert pfe["fundamental_discount_pct"] is not None


def test_missing_fundamentals_show_nulls_not_fabricated():
    out = ec.build(_batch(), _fundamentals())
    dis = out["stocks"]["DIS"]
    assert dis["valuation"].get("pe") is None
    assert dis["fundamentals"].get("net_margin") is None
    assert dis["valuation"].get("fundamental_value") is None


def test_fundamentals_arg_optional():
    out = ec.build(_batch(), {})
    assert out["stocks"]["PFE"]["valuation"].get("fundamental_value") is None


def test_screener_one_row_per_stock_stamped_congress():
    out = ec.build(_batch(), _fundamentals())
    syms = {r["symbol"] for r in out["screener"]}
    assert syms == set(out["stocks"])
    for r in out["screener"]:
        assert r["sector"] == "Congress"
    pfe = next(r for r in out["screener"] if r["symbol"] == "PFE")
    assert pfe["price"] == 27.0
    assert pfe["fundamental_value"] == 40.0


def test_no_gurufocus_leak_anywhere():
    out = ec.build(_batch(), _fundamentals())
    blob = json.dumps(out).lower()
    for term in ("guru", "gf value", "gf_value", "value trap", "gf score"):
        assert term not in blob, f"leaked: {term}"


def test_disclaimer_is_educational_not_advice():
    out = ec.build(_batch(), _fundamentals())
    d = out["disclaimer"].lower()
    assert "not" in d and "advice" in d


# ----------------------------------------------------------------- history (annual)

_ANNUAL_KEYS = ("annualTotalRevenue", "annualGrossProfit", "annualNetIncome",
                "annualFreeCashFlow", "annualDilutedEPS")


def test_history_folded_in_when_fundamentals_carry_it():
    funds = _fundamentals()
    funds["DIS"] = {
        "symbol": "DIS",
        "history": {
            "annualTotalRevenue": [{"date": "2025-09-30", "value": 91000000000.0}],
            "annualGrossProfit": [{"date": "2025-09-30", "value": 30000000000.0}],
            "annualNetIncome": [{"date": "2025-09-30", "value": 5000000000.0}],
            "annualFreeCashFlow": [{"date": "2025-09-30", "value": 8000000000.0}],
            "annualDilutedEPS": [{"date": "2025-09-30", "value": 2.7}],
        },
    }
    out = ec.build(_batch(), funds)
    hist = out["stocks"]["DIS"]["history"]
    assert hist
    for k in _ANNUAL_KEYS:
        assert k in hist, f"missing {k}"
    assert hist["annualTotalRevenue"][0]["value"] == 91000000000.0


def test_history_absent_yields_empty_dict_no_crash():
    out = ec.build(_batch(), _fundamentals())
    assert out["stocks"]["PFE"]["history"] == {}
    assert out["stocks"]["DIS"]["history"] == {}
