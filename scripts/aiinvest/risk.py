"""Pure risk-desk computations (returns -> vol/VaR/Sharpe/drawdown/beta/correlation).

Zero HTTP, zero I/O — every function here is a pure transform over plain dicts/lists/
floats, unit-tested in isolation (see tests/test_risk.py). `build_risk.py` is the thin
network-free assembly layer that reads already-retrieved local JSON (site.json,
prices/<SYM>.json) and calls these. See
docs/superpowers/specs/2026-07-14-risk-desk-design.md for the binding risk.json v1
contract these functions feed.

Sign conventions (do not get these backwards):
  - VaR is reported POSITIVE (loss magnitude).
  - max_drawdown is reported NEGATIVE.
  - Annualization always uses sqrt(periods_per_year) (default 252) — NEVER sqrt(n).

Formulas:
  Sample stdev/variance/covariance: ddof=1 (n-1 denominator), matches numpy's default
    `ddof=1` behavior used throughout this module for consistency with beta's covariance/
    variance reuse.
  quantile_linear: numpy's "linear" interpolation method — rank = q*(n-1), interpolate
    between the two bracketing order statistics.
  Historical VaR: -quantile_linear(sorted(window), 1-confidence) * 100 (positive loss %).
  Sharpe: (mean(window)*periods_per_year - rf_annual) / (stdev(window)*sqrt(periods_per_year)).
  Max drawdown: min over the running-peak-relative pct change, walking the window forward.
  Beta: sample_covariance(xs, ys) / sample_variance(ys) — xs = the series being measured
    (e.g. a stock), ys = the benchmark (e.g. SPY). Standard beta-vs-benchmark formula.
"""
from __future__ import annotations

import math

MIN_BARS = 60
WINDOW = 252


# --------------------------------------------------------------------------- basic stats


def mean(xs):
    if not xs:
        return None
    return sum(xs) / len(xs)


def sample_variance(xs):
    """ddof=1 sample variance. None if n<2."""
    n = len(xs)
    if n < 2:
        return None
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (n - 1)


def sample_stdev(xs):
    """ddof=1 sample stdev (= sqrt(sample_variance)). None if n<2."""
    var = sample_variance(xs)
    if var is None:
        return None
    return math.sqrt(var)


def sample_covariance(xs, ys):
    """ddof=1 sample covariance of paired lists. None if n<2 or lengths differ."""
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    mx = mean(xs)
    my = mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n - 1)


# --------------------------------------------------------------------------- returns


def daily_returns(series):
    """Ascending [{"date","close"}] -> [{"date","ret"}] simple daily returns.

    Bars with a non-finite or non-positive close are dropped as data gaps BEFORE the
    diff is taken (so a return is never computed against a dirty close) — this means the
    date of a return is the date of the later of two consecutive VALID bars, which may
    skip over a dropped date.
    """
    valid = [b for b in series
             if isinstance(b.get("close"), (int, float))
             and not isinstance(b.get("close"), bool)
             and math.isfinite(b["close"]) and b["close"] > 0]
    out = []
    for i in range(1, len(valid)):
        prev_c = valid[i - 1]["close"]
        cur_c = valid[i]["close"]
        if prev_c == 0:
            continue
        out.append({"date": valid[i]["date"], "ret": (cur_c - prev_c) / prev_c})
    return out


def trailing_window(returns, n=252):
    """Last n elements, or all of them if fewer than n are available."""
    if len(returns) <= n:
        return list(returns)
    return list(returns[-n:])


# --------------------------------------------------------------------------- risk measures


def annualized_vol_pct(window_returns, periods_per_year=252):
    """Annualized volatility, in percent. None if n<MIN_BARS."""
    if len(window_returns) < MIN_BARS:
        return None
    vol = sample_stdev(window_returns)
    if vol is None:
        return None
    return vol * math.sqrt(periods_per_year) * 100


def quantile_linear(sorted_xs, q):
    """numpy "linear"-interpolation-equivalent quantile of an ALREADY-SORTED list."""
    n = len(sorted_xs)
    if n == 1:
        return sorted_xs[0]
    rank = q * (n - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return sorted_xs[lo]
    frac = rank - lo
    return sorted_xs[lo] + frac * (sorted_xs[hi] - sorted_xs[lo])


def historical_var_pct(window_returns, confidence):
    """Historical (non-parametric) 1-day VaR, reported POSITIVE (loss magnitude), in
    percent. None if n<MIN_BARS."""
    n = len(window_returns)
    if n < MIN_BARS:
        return None
    xs = sorted(window_returns)
    q = quantile_linear(xs, 1 - confidence)
    return -q * 100


def sharpe_ratio(window_returns, rf_annual=0.04, periods_per_year=252):
    """Annualized Sharpe ratio. None if n<MIN_BARS or the window has zero variance."""
    if len(window_returns) < MIN_BARS:
        return None
    vol = sample_stdev(window_returns)
    if vol is None or math.isclose(vol, 0.0, abs_tol=1e-12):
        return None
    ann_vol = vol * math.sqrt(periods_per_year)
    ann_ret = mean(window_returns) * periods_per_year
    return (ann_ret - rf_annual) / ann_vol


def max_drawdown_pct(closes_window):
    """Max peak-to-trough drawdown over the window, reported NEGATIVE. None if <2 closes."""
    if len(closes_window) < 2:
        return None
    peak = closes_window[0]
    worst = 0.0
    for c in closes_window:
        if c > peak:
            peak = c
        if peak > 0:
            dd = (c - peak) / peak * 100
            if dd < worst:
                worst = dd
    return worst


def day_change_pct(series):
    """Close-to-close % change using the LAST TWO bars only. None if <2 bars available.
    Independent of MIN_BARS by design — a fresh IPO with only 2 daily bars still has a
    day change even though it has no vol/VaR/Sharpe."""
    if len(series) < 2:
        return None
    prev = series[-2]["close"]
    last = series[-1]["close"]
    if not prev:
        return None
    return (last - prev) / prev * 100


def pearson_correlation(xs, ys):
    """Pearson correlation of paired lists. None if n<2 or either series is constant."""
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    sx = sample_stdev(xs)
    sy = sample_stdev(ys)
    if sx is None or sy is None or math.isclose(sx, 0.0, abs_tol=1e-12) \
            or math.isclose(sy, 0.0, abs_tol=1e-12):
        return None
    cov = sample_covariance(xs, ys)
    if cov is None:
        return None
    return cov / (sx * sy)


def beta(xs, ys):
    """Beta of xs vs. benchmark ys = cov(xs, ys) / var(ys). None if n<2 or var(ys)==0."""
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    var_y = sample_variance(ys)
    if var_y is None or math.isclose(var_y, 0.0, abs_tol=1e-12):
        return None
    cov = sample_covariance(xs, ys)
    if cov is None:
        return None
    return cov / var_y


# --------------------------------------------------------------------------- alignment / aggregation


def align_series(a, b):
    """a, b: dict[date -> ret]. Returns (xs, ys) over the common dates only, date-ordered."""
    common = sorted(set(a) & set(b))
    return [a[d] for d in common], [b[d] for d in common]


def layer_return_series(per_symbol_returns, symbols):
    """per_symbol_returns: dict[sym -> dict[date -> ret]]. Equal-weighted mean of that
    date's return across whichever of `symbols` has data that day (>=1 contributor per
    date is enough — a layer's series is never held hostage by its thinnest member)."""
    by_date = {}
    for sym in symbols:
        series = per_symbol_returns.get(sym) or {}
        for d, r in series.items():
            by_date.setdefault(d, []).append(r)
    return {d: mean(vals) for d, vals in by_date.items()}
