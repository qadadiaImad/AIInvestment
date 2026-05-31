"""Public-site exporter sanitizer.

Turns an internal fact sheet (+ narrative) into a publishable stock record with **all
GuruFocus content removed** — GF Value, the GF valuation verdict, the GF-derived discount,
the GF risk flag, and any narrative prose that mentions GuruFocus. The site publishes our
own derived analysis + links to TradingView/Yahoo/SEC/FRED only. Never references GuruFocus.
"""
from __future__ import annotations

import copy

# Anything matching these (case-insensitive) is scrubbed from published content.
_GF_TERMS = ("guru", "gf value", "gf_value", "gf-value", "value trap", "value-trap", "gf score")
_DROP = object()


def _has_gf(s):
    s = str(s).lower()
    return any(t in s for t in _GF_TERMS)


def _clean(v):
    """Recursively drop GF-bearing strings and GF-keyed entries; preserve numbers/None."""
    if isinstance(v, str):
        return _DROP if _has_gf(v) else v
    if isinstance(v, list):
        return [c for c in (_clean(x) for x in v) if c is not _DROP]
    if isinstance(v, dict):
        out = {}
        for k, val in v.items():
            if _has_gf(k):
                continue
            c = _clean(val)
            if c is _DROP:
                continue
            out[k] = c
        return out
    return v  # numbers, None, bool


def sanitize_stock(factsheet, narrative=None):
    """Build a publishable, GuruFocus-free stock record from an internal fact sheet."""
    fs = copy.deepcopy(factsheet or {})
    val = dict(fs.get("valuation", {}) or {})
    # GF-derived valuation fields removed explicitly (key/value may not self-flag).
    for k in ("gf_value", "discount_pct", "verdict"):
        val.pop(k, None)

    out = {
        "symbol": fs.get("symbol"),
        "layer": fs.get("layer"),
        "as_of": fs.get("as_of"),
        "valuation": val,
        "fundamentals": fs.get("fundamentals", {}),
        "performance": fs.get("performance", {}),
        "peer_comparison": fs.get("peer_comparison", {}),
        "history": fs.get("history", {}),
        "constraint": fs.get("constraint", {}),
        "catalysts": fs.get("catalysts", []),
        "relationships": fs.get("relationships", {}),
        "risk_flags": fs.get("risk_flags", []),
        "narrative": narrative or {},
    }
    return _clean(out)
