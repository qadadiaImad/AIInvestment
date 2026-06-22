"""RED tests for the multi-year fundamentals history (Yahoo timeseries, keyless REST)."""
from aiinvest import history


PAYLOAD = {"timeseries": {"result": [
    {"meta": {"symbol": ["NVDA"], "type": ["annualTotalRevenue"]},
     "annualTotalRevenue": [
         {"asOfDate": "2024-01-31", "reportedValue": {"raw": 60922000000, "fmt": "60.92B"}},
         {"asOfDate": "2025-01-31", "reportedValue": {"raw": 130497000000}},
         None]},
    {"meta": {"symbol": ["NVDA"], "type": ["annualNetIncome"]},
     "annualNetIncome": [
         {"asOfDate": "2024-01-31", "reportedValue": {"raw": 29760000000}},
         {"asOfDate": "2025-01-31", "reportedValue": {"raw": 72880000000}}]},
]}}


def test_url_has_symbol_types_and_period():
    url = history.timeseries_url("NVDA", ["annualTotalRevenue", "annualNetIncome"])
    assert "timeseries/NVDA" in url
    assert "annualTotalRevenue" in url
    assert "period1=" in url and "period2=" in url


def test_parse_returns_series_per_metric():
    h = history.parse_timeseries(PAYLOAD)
    assert set(h.keys()) == {"annualTotalRevenue", "annualNetIncome"}


def test_parse_revenue_points_skip_nulls_and_are_floats():
    h = history.parse_timeseries(PAYLOAD)
    rev = h["annualTotalRevenue"]
    assert rev == [{"date": "2024-01-31", "value": 60922000000.0},
                   {"date": "2025-01-31", "value": 130497000000.0}]


def test_parse_empty_payload_is_empty_dict():
    assert history.parse_timeseries({"timeseries": {"result": []}}) == {}
    assert history.parse_timeseries({}) == {}
