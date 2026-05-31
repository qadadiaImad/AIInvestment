"""Multi-year fundamentals history — Yahoo fundamentals-timeseries (keyless REST).

REST-first, no browser, no API key. Verified live: NVDA annual revenue/net income/EPS
multi-year. Pure `parse_timeseries`; `fetch_history` is the thin network layer.
"""
from __future__ import annotations

from . import schema

BASE = ("https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/"
        "timeseries/{symbol}")
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

DEFAULT_TYPES = ["annualTotalRevenue", "annualNetIncome", "annualGrossProfit",
                 "annualDilutedEPS", "annualFreeCashFlow"]


def timeseries_url(symbol, types, period1=1262304000, period2=2000000000):
    return (f"{BASE.format(symbol=symbol)}?symbol={symbol}&type={','.join(types)}"
            f"&period1={period1}&period2={period2}&merge=false")


def parse_timeseries(payload):
    """Yahoo timeseries JSON -> {metric: [{date, value}]} (nulls skipped, values floats)."""
    out = {}
    for series in (payload.get("timeseries", {}) or {}).get("result", []) or []:
        types = (series.get("meta", {}) or {}).get("type") or []
        if not types:
            continue
        metric = types[0]
        points = []
        for pt in series.get(metric, []) or []:
            if not pt:
                continue
            val = schema.parse_number((pt.get("reportedValue", {}) or {}).get("raw"))
            points.append({"date": pt.get("asOfDate"), "value": val})
        out[metric] = points
    return out


def fetch_history(symbol, types=None, session=None):
    import requests
    types = types or DEFAULT_TYPES
    http = session or requests
    resp = http.get(timeseries_url(symbol, types), headers={"User-Agent": _UA}, timeout=25)
    resp.raise_for_status()
    return parse_timeseries(resp.json())
