import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pull_physical_ai as pp


def _rec(sym, ticker, ccy, close, mcap):
    return {"symbol": sym, "ticker": ticker, "metrics": {
        "currency": {"value": ccy}, "close": {"value": close}, "market_cap_basic": {"value": mcap}}}


FX = {"rates": {"CNY": 7.0, "GBP": 0.8}, "source_url": "https://api.frankfurter.app/latest"}


def test_usd_fields_added_from_local_currency():
    r = pp.add_usd_fields(_rec("300748", "SZSE:300748", "CNY", 35.0, 70e9), FX, "2026-09-22T00:00:00Z")
    assert r["metrics"]["market_cap_usd"]["value"] == 10e9
    assert r["metrics"]["price_usd"]["value"] == 5.0


def test_pence_quotes_convert_via_pounds():
    r = pp.add_usd_fields(_rec("MKA", "LSE:MKA", "GBX", 80.0, 8e7), FX, "t")
    assert r["metrics"]["price_usd"]["value"] == 1.0


def test_assemble_batch_reports_failures_and_stamps_market():
    recs = [pp.add_usd_fields(_rec("300748", "SZSE:300748", "CNY", 35.0, 70e9), FX, "t")]
    b = pp.assemble_batch(recs, ["SZSE:300748", "NYSE:MP"], "t", FX)
    fd = b["financial_data"]["300748"]
    assert fd["market"] == "china" and fd["country"] == "CN" and fd["stack_layer"] == "P2-magnets"
    assert b["batch_metadata"]["failed_symbols"] == ["NYSE:MP"]
    assert b["batch_metadata"]["fx"] is FX
