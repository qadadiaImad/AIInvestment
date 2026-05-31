"""RED tests for the TradingView scanner client (pure request/response logic)."""
from aiinvest import tradingview as tv


# --- build_scan_payload(): the POST body shape scanner.tradingview.com expects ---

def test_build_payload_has_tickers_and_empty_query_types():
    p = tv.build_scan_payload(["NASDAQ:NVDA", "NYSE:VST"], ["close"])
    assert p["symbols"]["tickers"] == ["NASDAQ:NVDA", "NYSE:VST"]
    assert p["symbols"]["query"]["types"] == []


def test_build_payload_passes_columns_through():
    p = tv.build_scan_payload(["NASDAQ:NVDA"], ["close", "price_earnings_ttm"])
    assert p["columns"] == ["close", "price_earnings_ttm"]


# --- parse_scan_response(): scanner JSON -> per-symbol records of envelopes ---

SAMPLE = {
    "totalCount": 2,
    "data": [
        {"s": "NASDAQ:NVDA", "d": [211.14, 5109587985229.0, 32.33, "Electronic Technology"]},
        {"s": "NYSE:VST", "d": [200.0, None, 12.5, "Utilities"]},
    ],
}
COLS = ["close", "market_cap_basic", "price_earnings_ttm", "sector"]


def test_parse_returns_one_record_per_symbol():
    recs = tv.parse_scan_response(SAMPLE, COLS, "url", "2026-05-30T14:00:00Z")
    assert len(recs) == 2


def test_parse_strips_exchange_prefix_into_symbol():
    recs = tv.parse_scan_response(SAMPLE, COLS, "url", "2026-05-30T14:00:00Z")
    assert recs[0]["symbol"] == "NVDA"
    assert recs[0]["ticker"] == "NASDAQ:NVDA"


def test_parse_numeric_column_becomes_float_envelope():
    recs = tv.parse_scan_response(SAMPLE, COLS, "url", "2026-05-30T14:00:00Z")
    pe = recs[0]["metrics"]["price_earnings_ttm"]
    assert pe["value"] == 32.33
    assert pe["unit"] == "ratio"
    assert pe["source"] == "tradingview"
    assert pe["source_class"] == "api"
    assert pe["dirty"] is False


def test_parse_text_column_uses_clean_not_number():
    recs = tv.parse_scan_response(SAMPLE, COLS, "url", "2026-05-30T14:00:00Z")
    assert recs[0]["metrics"]["sector"]["value"] == "Electronic Technology"


def test_parse_missing_numeric_is_none_and_not_dirty():
    # TradingView returns null for a genuinely-absent field -> value None, dirty False.
    recs = tv.parse_scan_response(SAMPLE, COLS, "url", "2026-05-30T14:00:00Z")
    mcap = recs[1]["metrics"]["market_cap_basic"]
    assert mcap["value"] is None
    assert mcap["dirty"] is False


def test_parse_empty_data_returns_empty_list():
    assert tv.parse_scan_response({"data": []}, COLS, "url", "t") == []


# --- enriched fundamental column set: all VERIFIED working on TradingView ---

def test_new_fundamental_columns_registered_with_kind():
    for col in [
        "gross_margin_ttm", "operating_margin_ttm", "net_margin_ttm",
        "free_cash_flow_margin_ttm", "return_on_equity", "return_on_assets",
        "return_on_invested_capital", "debt_to_equity", "current_ratio",
        "price_sales_current", "price_free_cash_flow_ttm",
        "total_revenue_yoy_growth_ttm", "earnings_per_share_diluted_yoy_growth_ttm",
        "Perf.Y", "Perf.YTD", "beta_1_year", "industry",
    ]:
        assert col in tv.COLUMNS, f"{col} missing from COLUMNS"
        unit, kind = tv.COLUMNS[col]
        assert kind in ("num", "text")


def test_margin_columns_are_numeric_pct():
    for col in ["gross_margin_ttm", "net_margin_ttm", "Perf.Y"]:
        unit, kind = tv.COLUMNS[col]
        assert kind == "num"
        assert unit == "pct"


def test_industry_is_text():
    unit, kind = tv.COLUMNS["industry"]
    assert kind == "text"
    assert unit == "text"


def test_new_columns_in_default_columns():
    for col in [
        "gross_margin_ttm", "net_margin_ttm", "return_on_equity",
        "return_on_invested_capital", "debt_to_equity", "current_ratio",
        "price_sales_current", "total_revenue_yoy_growth_ttm",
        "earnings_per_share_diluted_yoy_growth_ttm", "Perf.Y", "Perf.YTD",
        "beta_1_year", "industry",
    ]:
        assert col in tv.DEFAULT_COLUMNS, f"{col} not in DEFAULT_COLUMNS"
