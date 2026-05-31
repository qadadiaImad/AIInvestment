"""Fundamental-value valuation logic — our own, generic (never references the source name).

`fundamental_value` is an intrinsic-value estimate retrieved per ticker. The valuation tag
and discount are computed HERE from our own live price, so the published label is ours, not
a third party's.
"""
from __future__ import annotations


def valuation_tag(price, value, band=0.10):
    """Undervalued / Fairly Valued / Overvalued from price-vs-fundamental-value (None if bad)."""
    if not isinstance(price, (int, float)) or not isinstance(value, (int, float)) or value <= 0:
        return None
    ratio = price / value
    if ratio < 1 - band:
        return "Undervalued"
    if ratio > 1 + band:
        return "Overvalued"
    return "Fairly Valued"


def discount_pct(price, value):
    """(value - price)/value * 100, rounded; positive = price below fundamental value."""
    if not isinstance(price, (int, float)) or not isinstance(value, (int, float)) or value <= 0:
        return None
    return round((value - price) / value * 100, 1)


def _series(pairs):
    """[[date, value], ...] -> [{date, value}], skipping null values."""
    out = []
    for item in pairs or []:
        if not item or len(item) < 2 or item[1] is None:
            continue
        out.append({"date": item[0], "value": item[1]})
    return out


def parse_valuation_chart(payload):
    """Parse the valuation-chart JSON into generic fields (no source naming).

    `fundamental_value` (current), `margin_of_safety_pct`, the historical/projected
    `fundamental_value_series`, and the `price_series`.
    """
    p = payload or {}
    return {
        "fundamental_value": p.get("gf_value") if p.get("gf_value") is not None else p.get("iv"),
        "margin_of_safety_pct": p.get("ms"),
        "fundamental_value_series": _series(p.get("medps")),
        "price_series": _series(p.get("price")),
    }
