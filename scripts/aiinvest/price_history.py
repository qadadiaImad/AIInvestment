"""Historical market-price series + returns — Yahoo chart endpoint (keyless REST).

Same endpoint as `yahoo.py` (current price) with a `range`; returns daily closes. Pure
`parse_chart_history` / `pct_return` / `returns_summary`; `fetch_history` is the thin GET.
"""
from __future__ import annotations

import datetime

CHART = ("https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
         "?interval={interval}&range={range}")
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def chart_url(symbol, range="5y", interval="1d"):
    return CHART.format(symbol=symbol, range=range, interval=interval)


def parse_chart_history(payload):
    """Yahoo chart payload -> ascending [{date, close}] (null closes skipped)."""
    result = (payload.get("chart", {}) or {}).get("result")
    if not result:
        return []
    res = result[0]
    ts = res.get("timestamp") or []
    quote = ((res.get("indicators", {}) or {}).get("quote") or [{}])
    closes = (quote[0] if quote else {}).get("close") or []
    out = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date().isoformat()
        out.append({"date": d, "close": round(float(c), 4)})
    return out


def pct_return(series, days):
    """% change from the close at/before (last_date - days) to the latest close."""
    if not series or len(series) < 2:
        return None
    last = series[-1]
    cutoff = datetime.date.fromisoformat(last["date"]) - datetime.timedelta(days=days)
    past = None
    for p in series:
        if datetime.date.fromisoformat(p["date"]) <= cutoff:
            past = p
        else:
            break
    if not past or not past["close"]:
        return None
    return round((last["close"] - past["close"]) / past["close"] * 100, 1)


def returns_summary(series):
    return {"1y": pct_return(series, 365), "3y": pct_return(series, 1095),
            "5y": pct_return(series, 1825)}


def fetch_history(symbol, range="5y", interval="1d", session=None):
    import requests
    http = session or requests
    resp = http.get(chart_url(symbol, range, interval), headers={"User-Agent": _UA}, timeout=25)
    resp.raise_for_status()
    return parse_chart_history(resp.json())
