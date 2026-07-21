"""RED tests for historical price series + returns (Yahoo chart, keyless REST)."""
from aiinvest import price_history as ph


def test_chart_url_has_range_and_interval():
    url = ph.chart_url("NVDA", range="5y", interval="1d")
    assert "chart/NVDA" in url
    assert "range=5y" in url and "interval=1d" in url


PAYLOAD = {"chart": {"result": [{
    "timestamp": [1577836800, 1609459200, 1640995200],  # 2020-01-01, 2021-01-01, 2022-01-01
    "indicators": {"quote": [{"close": [100.0, 150.0, None]}]},
}]}}


def test_parse_history_pairs_dates_and_closes_skips_null():
    s = ph.parse_chart_history(PAYLOAD)
    assert s == [{"date": "2020-01-01", "close": 100.0},
                 {"date": "2021-01-01", "close": 150.0}]


def test_parse_empty_returns_list():
    assert ph.parse_chart_history({"chart": {"result": None}}) == []


def test_pct_return_uses_close_at_or_before_cutoff():
    s = [{"date": "2020-01-01", "close": 100.0}, {"date": "2021-01-01", "close": 150.0}]
    assert ph.pct_return(s, 365) == 50.0


def test_returns_summary_keys():
    s = [{"date": "2020-01-01", "close": 100.0}, {"date": "2021-01-01", "close": 150.0}]
    r = ph.returns_summary(s)
    assert set(r.keys()) == {"1y", "3y", "5y"}
    assert r["1y"] == 50.0


OHLC_PAYLOAD = {"chart": {"result": [{
    "timestamp": [1577836800, 1609459200, 1640995200],  # 2020-01-01, 2021-01-01, 2022-01-01
    "indicators": {"quote": [{
        "open": [99.0, 148.0, None],
        "high": [101.0, 151.0, 160.0],
        "low": [98.0, 147.0, 155.0],
        "close": [100.0, 150.0, None],
    }]},
}]}}


def test_parse_chart_ohlc_daily_skips_null_bars():
    bars = ph.parse_chart_ohlc(OHLC_PAYLOAD, intraday=False)
    assert bars == [
        {"date": "2020-01-01", "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0},
        {"date": "2021-01-01", "open": 148.0, "high": 151.0, "low": 147.0, "close": 150.0},
    ]


def test_parse_chart_ohlc_intraday_uses_datetime_key():
    bars = ph.parse_chart_ohlc(OHLC_PAYLOAD, intraday=True)
    assert bars[0]["datetime"] == "2020-01-01T00:00:00Z"
    assert "date" not in bars[0]


def test_parse_chart_ohlc_empty_returns_list():
    assert ph.parse_chart_ohlc({"chart": {"result": None}}) == []
