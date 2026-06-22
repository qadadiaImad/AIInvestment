"""TradingView scanner REST client.

REST-first per CLAUDE.md: fundamentals come from a single POST to the scanner endpoint,
no browser. Pure functions (`build_scan_payload`, `parse_scan_response`) are unit-tested;
`scan()` is the thin network layer.

Endpoint verified live 2026-05-30 (NVDA: close 211.14, P/E 32.33, mcap $5.11T).
"""
from __future__ import annotations

from . import schema

SCAN_URL = "https://scanner.tradingview.com/{market}/scan"
SOURCE = "tradingview"

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# tv column id -> (unit, kind). kind: "num" -> parse_number, "text" -> clean.
COLUMNS = {
    "close": ("usd", "num"),
    "market_cap_basic": ("usd", "num"),
    "price_earnings_ttm": ("ratio", "num"),
    "earnings_per_share_diluted_ttm": ("usd_per_share", "num"),
    "price_book_fq": ("ratio", "num"),
    "price_revenue_ttm": ("ratio", "num"),
    "dividend_yield_recent": ("pct", "num"),
    "Recommend.All": ("ratio", "num"),
    "sector": ("text", "text"),
    "description": ("text", "text"),
    "earnings_release_next_date": ("text", "text"),
    # --- margins (TTM) ---
    "gross_margin_ttm": ("pct", "num"),
    "operating_margin_ttm": ("pct", "num"),
    "net_margin_ttm": ("pct", "num"),
    "free_cash_flow_margin_ttm": ("pct", "num"),
    # --- returns ---
    "return_on_equity": ("pct", "num"),
    "return_on_assets": ("pct", "num"),
    "return_on_invested_capital": ("pct", "num"),
    # --- leverage / liquidity ---
    "debt_to_equity": ("ratio", "num"),
    "current_ratio": ("ratio", "num"),
    # --- valuation multiples ---
    "price_sales_current": ("ratio", "num"),
    "price_free_cash_flow_ttm": ("ratio", "num"),
    # --- growth (YoY, TTM) ---
    "total_revenue_yoy_growth_ttm": ("pct", "num"),
    "earnings_per_share_diluted_yoy_growth_ttm": ("pct", "num"),
    # --- performance / risk ---
    "Perf.Y": ("pct", "num"),
    "Perf.YTD": ("pct", "num"),
    "beta_1_year": ("ratio", "num"),
    # --- classification ---
    "industry": ("text", "text"),
}

# Sensible default fundamentals pull.
DEFAULT_COLUMNS = [
    "description", "close", "market_cap_basic", "price_earnings_ttm",
    "earnings_per_share_diluted_ttm", "price_book_fq", "price_revenue_ttm",
    "dividend_yield_recent", "sector", "industry",
    "earnings_release_next_date", "Recommend.All",
    "gross_margin_ttm", "operating_margin_ttm", "net_margin_ttm",
    "free_cash_flow_margin_ttm",
    "return_on_equity", "return_on_assets", "return_on_invested_capital",
    "debt_to_equity", "current_ratio",
    "price_sales_current", "price_free_cash_flow_ttm",
    "total_revenue_yoy_growth_ttm", "earnings_per_share_diluted_yoy_growth_ttm",
    "Perf.Y", "Perf.YTD", "beta_1_year",
]


def build_scan_payload(tickers, columns):
    """Build the scanner POST body for explicit tickers."""
    return {
        "symbols": {"tickers": list(tickers), "query": {"types": []}},
        "columns": list(columns),
    }


def _envelope_for(col, raw, source_url, retrieved_at):
    unit, kind = COLUMNS.get(col, ("text", "text"))
    value = schema.parse_number(raw) if kind == "num" else schema.clean(raw)
    return schema.make_envelope(
        value=value, raw=raw, unit=unit, source=SOURCE,
        source_url=source_url, source_class="api", retrieved_at=retrieved_at,
    )


def parse_scan_response(resp_json, columns, source_url, retrieved_at):
    """Map scanner JSON to a list of per-symbol records of stamped envelopes."""
    records = []
    for row in resp_json.get("data", []):
        ticker = row.get("s", "")
        values = row.get("d", []) or []
        metrics = {}
        for i, col in enumerate(columns):
            raw = values[i] if i < len(values) else None
            metrics[col] = _envelope_for(col, raw, source_url, retrieved_at)
        records.append({
            "symbol": ticker.split(":")[-1],
            "ticker": ticker,
            "metrics": metrics,
        })
    return records


def scan(tickers, columns=None, market="america", retrieved_at=None, timeout=25,
         session=None):
    """Hit the scanner endpoint and return parsed per-symbol records.

    Network layer kept thin; pure logic above is what the tests exercise.
    """
    import datetime
    import requests

    columns = columns or DEFAULT_COLUMNS
    if retrieved_at is None:
        retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
    url = SCAN_URL.format(market=market)
    payload = build_scan_payload(tickers, columns)
    http = session or requests
    resp = http.post(url, json=payload, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    return parse_scan_response(resp.json(), columns, url, retrieved_at)
