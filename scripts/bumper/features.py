"""Pure feature logic for the bumper study (unit-tested; no I/O).

Conventions: monthly closes are a list of (YYYY-MM, close) ascending. Quarterly filing
series are lists of (end_date 'YYYY-MM-DD', value) ascending, one point per fiscal quarter.
"""
from __future__ import annotations

import bisect
import math


# --- run detection ----------------------------------------------------------------------

def best_forward_window(closes, months=12):
    """Return (start_index, multiple) of the `months`-long forward window with the largest
    close-to-close multiple. Requires at least months+1 points; else (None, None)."""
    if len(closes) <= months:
        return None, None
    best_i, best_m = None, -math.inf
    for i in range(len(closes) - months):
        a, b = closes[i][1], closes[i + months][1]
        if not a or not b or a <= 0:
            continue
        m = b / a
        if m > best_m:
            best_i, best_m = i, m
    return best_i, best_m


def run_start(closes, months=12, min_multiple=2.5):
    """Month label at which the first `months`-window returning >= min_multiple starts, else
    the start of the best window if it clears min_multiple, else None.

    "First" matters: a study that picks the *best* window sees the run with hindsight; the
    first qualifying window is what a live screen could have caught.
    """
    if len(closes) <= months:
        return None
    for i in range(len(closes) - months):
        a, b = closes[i][1], closes[i + months][1]
        if a and b and a > 0 and b / a >= min_multiple:
            return closes[i][0]
    return None


# --- filing series helpers --------------------------------------------------------------

def value_at(series, date, max_lag_days=200):
    """Latest filing value whose period end is on/before `date` (YYYY-MM-DD) and not older
    than max_lag_days. Returns (value, end_date) or (None, None)."""
    if not series:
        return None, None
    ends = [e for e, _ in series]
    i = bisect.bisect_right(ends, date) - 1
    if i < 0:
        return None, None
    end, val = series[i]
    if _days_between(end, date) > max_lag_days:
        return None, None
    return val, end


def _days_between(a, b):
    from datetime import date as _d
    ya, ma, da = map(int, a.split("-"))
    yb, mb, db = map(int, b.split("-"))
    return (_d(yb, mb, db) - _d(ya, ma, da)).days


def yoy_growth(series, date):
    """Growth of the quarterly value at `date` versus the value ~4 quarters earlier."""
    cur, end = value_at(series, date)
    if cur is None:
        return None
    prev, _ = value_at(series, _shift_year(end, -1), max_lag_days=120)
    if prev in (None, 0) or prev < 0:
        return None
    return cur / prev - 1.0


def _shift_year(d, years):
    y, m, dd = map(int, d.split("-"))
    y += years
    # clamp Feb 29
    if m == 2 and dd == 29:
        dd = 28
    return f"{y:04d}-{m:02d}-{dd:02d}"


def ttm(series, date):
    """Sum of the last four quarterly values on/before date (None if fewer than 4)."""
    ends = [e for e, _ in series]
    i = bisect.bisect_right(ends, date) - 1
    if i < 3:
        return None
    return sum(v for _, v in series[i - 3:i + 1])


# --- the feature vector ---------------------------------------------------------------------

def features_at(date, q):
    """q = dict of quarterly series: revenue, rnd, gross_profit, ocf, cash, shares.
    Returns the pre-run feature dict a live screen could compute on `date`."""
    rev_ttm = ttm(q.get("revenue", []), date)
    rnd_ttm = ttm(q.get("rnd", []), date)
    ocf_ttm = ttm(q.get("ocf", []), date)
    gp_ttm = ttm(q.get("gross_profit", []), date)
    cash, _ = value_at(q.get("cash", []), date)
    shares, _ = value_at(q.get("shares", []), date)
    out = {
        "revenue_ttm": rev_ttm,
        "rev_growth_yoy": yoy_growth(q.get("revenue", []), date),
        "rev_growth_yoy_prev": None,
        "rnd_to_rev": (abs(rnd_ttm) / rev_ttm) if rnd_ttm is not None and rev_ttm else None,
        "gross_margin": (gp_ttm / rev_ttm) if gp_ttm is not None and rev_ttm else None,
        "ocf_ttm": ocf_ttm,
        "cash": cash,
        "runway_years": (cash / -ocf_ttm) if cash is not None and ocf_ttm is not None and ocf_ttm < 0 else None,
        "shares_growth_yoy": yoy_growth(q.get("shares", []), date),
        "profitable": (ocf_ttm > 0) if ocf_ttm is not None else None,
    }
    # revenue acceleration: growth now minus growth a year earlier
    prev_date = _shift_year(date, -1)
    out["rev_growth_yoy_prev"] = yoy_growth(q.get("revenue", []), prev_date)
    if out["rev_growth_yoy"] is not None and out["rev_growth_yoy_prev"] is not None:
        out["rev_acceleration"] = out["rev_growth_yoy"] - out["rev_growth_yoy_prev"]
    else:
        out["rev_acceleration"] = None
    return out


def months_before(month_label, n):
    """'2024-03' minus n months -> 'YYYY-MM-01' date string."""
    y, m = map(int, month_label.split("-"))
    idx = y * 12 + (m - 1) - n
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}-01"


# --- simple separation stats (no scipy dependency) --------------------------------------

def auc(pos, neg):
    """Mann-Whitney AUC: P(random winner > random control). Ignores None."""
    pos = [x for x in pos if x is not None]
    neg = [x for x in neg if x is not None]
    if not pos or not neg:
        return None
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins / (len(pos) * len(neg))


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
