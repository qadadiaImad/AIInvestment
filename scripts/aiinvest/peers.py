"""Cross-sectional peer benchmarking for AI-stack names.

Answers "is NVDA's margin / ROE / valuation high or low vs its peers?" by comparing a
target's fundamentals against (a) its TradingView industry peers and (b) its AI-stack
layer peers. Pure stat functions (`benchmark`, `peer_stats`) are unit-tested with
fixtures; the network functions are thin wrappers over the tradingview scanner.
"""
from __future__ import annotations

from . import ai_stack, tradingview

SCAN_URL = "https://scanner.tradingview.com/{market}/scan"
SOURCE = "tradingview"

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


# --- pure stats ---------------------------------------------------------------

def _percentile(sorted_vals, q):
    """Linear-interpolated percentile (q in 0..100) of a sorted non-empty list."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = (q / 100.0) * (len(sorted_vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def benchmark(value, peer_values):
    """Summarize ``value`` against a distribution of ``peer_values``.

    Returns ``{"n", "median", "p25", "p75", "percentile"}``. ``n`` counts non-None
    peers. ``percentile`` is the % of non-None peers <= value (0..100); it is None
    when value is None or there are no peers. The dict is always returned.
    """
    vals = sorted(v for v in peer_values if v is not None)
    n = len(vals)
    out = {
        "n": n,
        "median": _percentile(vals, 50) if n else None,
        "p25": _percentile(vals, 25) if n else None,
        "p75": _percentile(vals, 75) if n else None,
        "percentile": None,
    }
    if value is not None and n:
        below = sum(1 for v in vals if v <= value)
        out["percentile"] = 100.0 * below / n
    return out


def peer_stats(target_metrics, peer_records, metric_names):
    """Benchmark each metric in ``metric_names`` against the peer cross-section.

    ``target_metrics`` maps metric -> value. ``peer_records`` are tradingview-shaped
    records (``{"symbol","ticker","metrics":{col:{"value":...}}}``). For each metric we
    gather peer values, drop one occurrence of the target's own value if present, and
    benchmark. Returns ``{metric: {"value","median","percentile","n"}}``.
    """
    out = {}
    for metric in metric_names:
        target_val = target_metrics.get(metric)
        peer_vals = []
        for rec in peer_records:
            env = rec.get("metrics", {}).get(metric)
            if env is not None:
                peer_vals.append(env.get("value"))
        # Drop the target's own observation (one occurrence) from the peer set.
        if target_val is not None and target_val in peer_vals:
            peer_vals.remove(target_val)
        b = benchmark(target_val, peer_vals)
        out[metric] = {
            "value": target_val,
            "median": b["median"],
            "percentile": b["percentile"],
            "n": b["n"],
        }
    return out


# --- network (thin; mirrors tradingview.py) -----------------------------------

def scan_industry(industry, columns, limit=300, market="america", retrieved_at=None,
                  timeout=25, session=None):
    """Return scanner records for every name in a TradingView ``industry``.

    Uses the filter-based scanner body (verified working) then reuses
    ``tradingview.parse_scan_response`` to map rows -> stamped records.
    """
    import datetime
    import requests

    if retrieved_at is None:
        retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
    url = SCAN_URL.format(market=market)
    payload = {
        "filter": [{"left": "industry", "operation": "equal", "right": industry}],
        "columns": list(columns),
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, limit],
        "markets": [market],
    }
    http = session or requests
    resp = http.post(url, json=payload, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    return tradingview.parse_scan_response(resp.json(), columns, url, retrieved_at)


def layer_peers(symbol, layer, columns, **kwargs):
    """Scan the other tickers in ``ai_stack.LAYERS[layer]`` (excluding ``symbol``).

    ``symbol`` is matched against the full ``EXCHANGE:SYM`` tickers and also by the
    bare symbol after the colon, so either form excludes the target.
    """
    bare = symbol.split(":")[-1]
    tickers = [t for t in ai_stack.LAYERS.get(layer, [])
               if t != symbol and t.split(":")[-1] != bare]
    if not tickers:
        return []
    return tradingview.scan(tickers, columns=columns, **kwargs)
