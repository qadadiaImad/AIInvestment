"""RED tests for backtest core: point-in-time fundamentals (no lookahead) + metrics."""
from aiinvest import backtest as bt


SERIES = [
    {"date": "2024-01-31", "value": 74.3},
    {"date": "2024-04-30", "value": 97.3},
    {"date": "2025-01-31", "value": 160.0},
    {"date": "2027-01-31", "value": 489.96},  # PROJECTED (future) — must never be used
]


def test_pit_uses_latest_value_knowable_by_asof_with_lag():
    # asof 2024-06-01, 45d lag -> cutoff 2024-04-17 -> only the 2024-01-31 point is knowable.
    assert bt.pit_fundamental_value(SERIES, "2024-06-01", lag_days=45) == 74.3


def test_pit_advances_after_period_becomes_knowable():
    # asof 2024-07-01 -> cutoff ~2024-05-17 -> the 2024-04-30 point is now usable.
    assert bt.pit_fundamental_value(SERIES, "2024-07-01", lag_days=45) == 97.3


def test_pit_never_uses_future_or_projected_points():
    # Even far in the future of the data, projected (2027) is excluded if beyond cutoff.
    assert bt.pit_fundamental_value(SERIES, "2026-06-01", lag_days=45) == 160.0


def test_pit_none_when_nothing_knowable_yet():
    assert bt.pit_fundamental_value(SERIES, "2023-06-01", lag_days=45) is None


# --- metrics ---

def test_cagr_doubling_over_one_year():
    eq = [1.0] + [None] * 0  # build a 252-step doubling
    eq = [1.0 * (2 ** (i / 252)) for i in range(253)]  # ends at 2.0 after 1y
    assert round(bt.cagr(eq, periods_per_year=252), 2) == 1.0  # +100%


def test_max_drawdown_simple():
    eq = [1.0, 1.2, 0.9, 1.1]  # peak 1.2 -> trough 0.9 = -25%
    assert round(bt.max_drawdown(eq), 3) == -0.25


def test_sharpe_positive_for_net_positive_returns():
    rets = [0.01, -0.002, 0.012, 0.001, 0.008, -0.001, 0.006]  # net positive, real variance
    assert bt.sharpe(rets, periods_per_year=252) > 0


def test_sharpe_zero_variance_is_zero():
    assert bt.sharpe([0.0, 0.0, 0.0], periods_per_year=252) == 0.0
