"""RED tests for the Yahoo REST helper (chart endpoint — verified live)."""
from aiinvest import yahoo


def test_chart_url_default_1d():
    assert yahoo.chart_url("NVDA") == \
        "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1d&range=1d"


SAMPLE = {"chart": {"result": [{"meta": {
    "symbol": "NVDA", "currency": "USD", "regularMarketPrice": 211.14,
    "chartPreviousClose": 214.25, "fiftyTwoWeekHigh": 236.54, "fiftyTwoWeekLow": 135.4,
}}], "error": None}}


def test_parse_chart_returns_symbol_and_price_envelope():
    rec = yahoo.parse_chart(SAMPLE, "url", "2026-05-30T12:00:00Z")
    assert rec["symbol"] == "NVDA"
    px = rec["metrics"]["current_price"]
    assert px["value"] == 211.14
    assert px["unit"] == "usd"
    assert px["source"] == "yahoo"
    assert px["source_class"] == "api"


def test_parse_chart_includes_52wk_range():
    rec = yahoo.parse_chart(SAMPLE, "url", "t")
    assert rec["metrics"]["fifty_two_week_high"]["value"] == 236.54
    assert rec["metrics"]["fifty_two_week_low"]["value"] == 135.4


def test_parse_chart_returns_none_when_no_result():
    assert yahoo.parse_chart({"chart": {"result": None, "error": "Not Found"}}, "u", "t") is None
