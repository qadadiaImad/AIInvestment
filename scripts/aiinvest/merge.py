"""Cross-source merge + freshness flagging.

Joins per-source symbol records (Yahoo + TradingView + GuruFocus + ...) into one record
where each metric carries: the chosen value, which sources reported it, whether they
agree (cross-validation), and whether it's stale (Rule #1 "verify live").
"""
from __future__ import annotations

import datetime

# Canonical metric names so the same concept from different providers merges into one field.
ALIASES = {"close": "current_price", "price": "current_price"}


def canonical(name):
    return ALIASES.get(name, name)


def cross_check(values, rel_tol=0.01):
    """True if all non-None numeric values agree within a relative tolerance."""
    nums = [v for v in values if isinstance(v, (int, float))]
    if len(nums) < 2:
        return True
    lo, hi = min(nums), max(nums)
    if hi == 0:
        return lo == 0
    return (hi - lo) / abs(hi) <= rel_tol


def _parse(ts):
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def is_stale(retrieved_at, now, max_age_hours=24):
    """True if a datum is older than max_age_hours relative to ``now`` (ISO-8601 UTC)."""
    age = _parse(now) - _parse(retrieved_at)
    return age.total_seconds() > max_age_hours * 3600


def merge_symbol(symbol, source_records, now, max_age_hours=24):
    """Combine {source: record} into one cross-validated, freshness-flagged record."""
    merged = {}
    for source, record in source_records.items():
        for raw_name, env in record.get("metrics", {}).items():
            name = canonical(raw_name)
            slot = merged.setdefault(name, {"value": None, "sources": [], "_vals": [],
                                            "_ts": [], "agree": True, "stale": False})
            if env.get("value") is not None:
                slot["sources"].append(source)
                slot["_vals"].append(env["value"])
                if slot["value"] is None:
                    slot["value"] = env["value"]
            if env.get("retrieved_at"):
                slot["_ts"].append(env["retrieved_at"])

    for name, slot in merged.items():
        slot["agree"] = cross_check(slot.pop("_vals"))
        ts = slot.pop("_ts")
        slot["stale"] = any(is_stale(t, now, max_age_hours) for t in ts) if ts else False
    return {"symbol": symbol, "metrics": merged}
