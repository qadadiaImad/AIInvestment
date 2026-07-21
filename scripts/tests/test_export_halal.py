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
