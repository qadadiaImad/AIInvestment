"""Backtest core — point-in-time fundamentals (no lookahead) + performance metrics.

Pure stdlib so it's trivially testable. The vectorbt portfolio simulation lives in the
`run_backtest.py` runner; this module supplies the rigor-critical primitives.
"""
from __future__ import annotations

import datetime


def pit_fundamental_value(series, asof, lag_days=45):
    """Latest fundamental value KNOWABLE at `asof` (date <= asof - lag_days).

    Excludes any point dated after the cutoff — so future/projected points can never leak
    in (lookahead). `series` is [{date, value}]; returns the value or None.
    """
    cutoff = datetime.date.fromisoformat(asof[:10]) - datetime.timedelta(days=lag_days)
    best = None
    for p in series or []:
        v, d = p.get("value"), p.get("date")
        if v is None or not d:
            continue
        dd = datetime.date.fromisoformat(d[:10])
        if dd <= cutoff and (best is None or dd > best[0]):
            best = (dd, v)
    return best[1] if best else None


def cagr(equity, periods_per_year=252):
    """Compound annual growth rate from an equity curve (list of levels)."""
    eq = [e for e in equity if e is not None]
    if len(eq) < 2 or eq[0] <= 0:
        return 0.0
    years = (len(eq) - 1) / periods_per_year
    if years <= 0:
        return 0.0
    return (eq[-1] / eq[0]) ** (1 / years) - 1


def max_drawdown(equity):
    """Worst peak-to-trough decline of an equity curve (negative number)."""
    peak = None
    mdd = 0.0
    for e in equity:
        if e is None:
            continue
        peak = e if peak is None else max(peak, e)
        if peak > 0:
            mdd = min(mdd, (e - peak) / peak)
    return mdd


def sharpe(returns, periods_per_year=252):
    """Annualized Sharpe (rf=0). Zero/undefined variance -> 0.0."""
    r = [x for x in returns if x is not None]
    if len(r) < 2:
        return 0.0
    m = sum(r) / len(r)
    var = sum((x - m) ** 2 for x in r) / (len(r) - 1)
    sd = var ** 0.5
    if sd == 0:
        return 0.0
    return (m / sd) * (periods_per_year ** 0.5)
