"""Yahoo Finance REST helper — keyless chart endpoint (verified live: NVDA 211.14).

REST-first, no browser. The v8 chart endpoint returns price/52wk without a crumb; the
v10 quoteSummary fundamentals endpoint now needs a crumb+cookie, so prefer TradingView
for fundamentals (see providers/README.md).
"""
from __future__ import annotations

from . import schema

SOURCE = "yahoo"
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range}"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# meta key -> (canonical name, unit)
_META = {
    "regularMarketPrice": ("current_price", "usd"),
    "chartPreviousClose": ("previous_close", "usd"),
    "fiftyTwoWeekHigh": ("fifty_two_week_high", "usd"),
    "fiftyTwoWeekLow": ("fifty_two_week_low", "usd"),
}


def chart_url(symbol, interval="1d", range="1d"):
    return CHART.format(symbol=symbol, interval=interval, range=range)


def parse_chart(payload, source_url, retrieved_at):
    """Parse the v8 chart payload -> per-symbol record of stamped envelopes (or None)."""
    result = (payload.get("chart", {}) or {}).get("result")
    if not result:
        return None
    meta = result[0].get("meta", {})
    metrics = {}
    for key, (name, unit) in _META.items():
        raw = meta.get(key)
        metrics[name] = schema.make_envelope(
            value=schema.parse_number(raw) if raw is not None else None,
            raw=raw, unit=unit, source=SOURCE, source_url=source_url,
            source_class="api", retrieved_at=retrieved_at,
        )
    return {"symbol": meta.get("symbol"), "currency": meta.get("currency"), "metrics": metrics}


def fetch_chart(symbol, retrieved_at=None, session=None):
    import datetime
    import requests
    if retrieved_at is None:
        retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = chart_url(symbol)
    http = session or requests
    resp = http.get(url, headers={"User-Agent": _UA}, timeout=20)
    resp.raise_for_status()
    return parse_chart(resp.json(), url, retrieved_at)
