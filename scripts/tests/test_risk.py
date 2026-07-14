"""Hand-computable fixtures for aiinvest.risk — every expected number derived in a
comment (mirrors the style of tests/test_ta.py)."""
import math

import pytest

from aiinvest import risk


# --------------------------------------------------------------------------- basic stats


def test_mean_basic():
    assert risk.mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_mean_none_when_empty():
    assert risk.mean([]) is None


def test_sample_variance_and_stdev_known_values():
    # xs=[1,2,3,4,5], mean=3; deviations -2,-1,0,1,2; sq-devs 4,1,0,1,4 sum=10
    # sample variance = 10/(5-1) = 2.5; stdev = sqrt(2.5) = 1.5811388...
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert risk.sample_variance(xs) == pytest.approx(2.5)
    assert risk.sample_stdev(xs) == pytest.approx(math.sqrt(2.5))


def test_sample_variance_none_below_2():
    assert risk.sample_variance([1.0]) is None
    assert risk.sample_stdev([]) is None


def test_sample_covariance_known_value():
    # xs=[1,2,3,4,5] mean=3, devs -2,-1,0,1,2
    # ys=[2,4,5,4,5] mean=4, devs -2,0,1,0,1
    # products: (-2*-2)=4, (-1*0)=0, (0*1)=0, (1*0)=0, (2*1)=2 -> sum=6
    # cov = 6 / (5-1) = 1.5
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 5.0, 4.0, 5.0]
    assert risk.sample_covariance(xs, ys) == pytest.approx(1.5)
    # and ys' own variance for cross-check with beta's denominator:
    # devs -2,0,1,0,1 -> sq 4,0,1,0,1 sum=6 -> var = 6/4 = 1.5
    assert risk.sample_variance(ys) == pytest.approx(1.5)


def test_sample_covariance_none_below_2_or_mismatched_lengths():
    assert risk.sample_covariance([1.0], [2.0]) is None
    assert risk.sample_covariance([1.0, 2.0], [1.0, 2.0, 3.0]) is None


# --------------------------------------------------------------------------- returns / windows


def test_daily_returns_basic():
    series = [{"date": "d1", "close": 100.0}, {"date": "d2", "close": 110.0},
              {"date": "d3", "close": 99.0}]
    out = risk.daily_returns(series)
    assert out[0] == {"date": "d2", "ret": pytest.approx(0.10)}
    assert out[1] == {"date": "d3", "ret": pytest.approx((99.0 - 110.0) / 110.0)}


def test_daily_returns_drops_non_finite_and_non_positive_closes():
    series = [{"date": "d1", "close": 100.0}, {"date": "d2", "close": float("nan")},
              {"date": "d3", "close": -5.0}, {"date": "d4", "close": 0.0},
              {"date": "d5", "close": 105.0}]
    out = risk.daily_returns(series)
    # only d1 and d5 survive filtering -> one return, d1->d5
    assert out == [{"date": "d5", "ret": pytest.approx((105.0 - 100.0) / 100.0)}]


def test_trailing_window_returns_last_n_or_all():
    returns = [{"date": f"d{i}", "ret": 0.01} for i in range(10)]
    assert len(risk.trailing_window(returns, 5)) == 5
    assert risk.trailing_window(returns, 5) == returns[-5:]
    assert risk.trailing_window(returns, 100) == returns


# --------------------------------------------------------------------------- vol / VaR / sharpe


def _alternating_60():
    # 60 returns alternating +0.01,-0.01,... (30 of each), mean=0
    return [0.01 if i % 2 == 0 else -0.01 for i in range(60)]


def test_annualized_vol_pct_known_value():
    # sample variance = sum(x^2)/(n-1) = 60*(0.0001)/59 = 0.0001016949...
    # stdev = sqrt(0.0001016949...) = 0.010084391...
    # annualized = stdev * sqrt(252) * 100 = 0.010084391 * 15.874507866 * 100 ~= 16.0065
    vol = risk.annualized_vol_pct(_alternating_60())
    assert vol == pytest.approx(16.0065, abs=0.01)


def test_annualized_vol_pct_none_below_min_bars():
    assert risk.annualized_vol_pct(_alternating_60()[:59]) is None


def test_quantile_linear_matches_numpy_linear_method():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    # numpy "linear": index = q*(n-1)
    assert risk.quantile_linear(xs, 0.0) == pytest.approx(1.0)
    assert risk.quantile_linear(xs, 1.0) == pytest.approx(5.0)
    assert risk.quantile_linear(xs, 0.5) == pytest.approx(3.0)
    assert risk.quantile_linear(xs, 0.25) == pytest.approx(2.0)
    # q=0.1 -> rank=0.1*4=0.4 -> 1 + 0.4*(2-1) = 1.4
    assert risk.quantile_linear(xs, 0.1) == pytest.approx(1.4)


def _evenly_spaced_100():
    # -0.05, -0.049, ..., 0.049 (100 values, step 0.001), already ascending
    return [round(-0.05 + i * 0.001, 10) for i in range(100)]


def test_historical_var_known_values():
    window = _evenly_spaced_100()
    # var95: rank = 0.05*(100-1) = 4.95 -> between index4=-0.046 and index5=-0.045
    #   interpolated = -0.046 + 0.95*0.001 = -0.04505 -> VaR95 = 4.505
    # var99: rank = 0.01*99 = 0.99 -> between index0=-0.05 and index1=-0.049
    #   interpolated = -0.05 + 0.99*0.001 = -0.04901 -> VaR99 = 4.901
    var95 = risk.historical_var_pct(window, 0.95)
    var99 = risk.historical_var_pct(window, 0.99)
    assert var95 == pytest.approx(4.505, abs=0.001)
    assert var99 == pytest.approx(4.901, abs=0.001)
    assert var99 > var95


def test_historical_var_none_below_min_bars():
    assert risk.historical_var_pct(_evenly_spaced_100()[:59], 0.95) is None


def test_sharpe_known_value():
    # mean=0 -> annualized return = 0; vol as computed above ~0.160065
    # sharpe = (0 - 0.04) / 0.160065 ~= -0.24990 ~= -0.250
    sharpe = risk.sharpe_ratio(_alternating_60(), rf_annual=0.04)
    assert sharpe == pytest.approx(-0.250, abs=0.01)


def test_sharpe_none_on_zero_variance():
    flat = [0.001] * 60
    assert risk.sharpe_ratio(flat) is None


def test_sharpe_none_below_min_bars():
    assert risk.sharpe_ratio(_alternating_60()[:59]) is None


# --------------------------------------------------------------------------- drawdown / day change


def test_max_drawdown_known_value():
    # closes 100,110,105,90,95,120 -> running peak 100,110,110,110,110,120
    # drawdowns: 0, 0, (105-110)/110=-4.545%, (90-110)/110=-18.1818%,
    #            (95-110)/110=-13.636%, (120-120)/120=0 -> worst = -18.1818%
    dd = risk.max_drawdown_pct([100.0, 110.0, 105.0, 90.0, 95.0, 120.0])
    assert dd == pytest.approx(-18.1818, abs=0.01)


def test_max_drawdown_none_below_2_closes():
    assert risk.max_drawdown_pct([100.0]) is None
    assert risk.max_drawdown_pct([]) is None


def test_day_change_pct_needs_exactly_2_bars():
    series = [{"date": "d1", "close": 100.0}, {"date": "d2", "close": 102.0}]
    assert risk.day_change_pct(series) == pytest.approx(2.0)


def test_day_change_pct_none_on_1_bar():
    assert risk.day_change_pct([{"date": "d1", "close": 100.0}]) is None
    assert risk.day_change_pct([]) is None


# --------------------------------------------------------------------------- correlation / beta


def test_pearson_correlation_perfect_positive():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert risk.pearson_correlation(xs, ys) == pytest.approx(1.0)


def test_pearson_correlation_perfect_negative():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [10.0, 8.0, 6.0, 4.0, 2.0]
    assert risk.pearson_correlation(xs, ys) == pytest.approx(-1.0)


def test_pearson_correlation_none_on_constant_series():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [5.0, 5.0, 5.0, 5.0, 5.0]
    assert risk.pearson_correlation(xs, ys) is None


def test_pearson_correlation_none_below_2():
    assert risk.pearson_correlation([1.0], [2.0]) is None


def test_beta_known_value_stock_moves_2x_benchmark():
    # ys (benchmark) = [1,2,3,4,5], xs (stock) = [2,4,6,8,10] = 2*ys
    # mean_ys=3, devs -2,-1,0,1,2 -> var_ys = (4+1+0+1+4)/4 = 2.5
    # mean_xs=6, devs -4,-2,0,2,4
    # cov(xs,ys) = ((-4*-2)+(-2*-1)+0+(2*1)+(4*2)) / 4 = (8+2+0+2+8)/4 = 20/4 = 5.0
    # beta = cov / var_ys = 5.0 / 2.5 = 2.0 (stock moves 2x the benchmark)
    ys = [1.0, 2.0, 3.0, 4.0, 5.0]
    xs = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert risk.beta(xs, ys) == pytest.approx(2.0)


def test_beta_none_when_benchmark_constant():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [5.0, 5.0, 5.0, 5.0, 5.0]
    assert risk.beta(xs, ys) is None


def test_beta_none_below_2():
    assert risk.beta([1.0], [2.0]) is None


# --------------------------------------------------------------------------- alignment / layer series


def test_align_series_intersects_dates_in_order():
    a = {"2026-01-01": 0.01, "2026-01-02": 0.02, "2026-01-03": 0.03}
    b = {"2026-01-02": 0.05, "2026-01-03": 0.06, "2026-01-04": 0.07}
    xs, ys = risk.align_series(a, b)
    assert xs == [0.02, 0.03]
    assert ys == [0.05, 0.06]


def test_align_series_empty_when_no_overlap():
    xs, ys = risk.align_series({"d1": 0.01}, {"d2": 0.02})
    assert xs == [] and ys == []


def test_layer_return_series_equal_weighted_with_missing_day():
    # A has data on d1,d2; B has data only on d1.
    # d1 -> mean(0.02, 0.06) = 0.04 ; d2 -> mean(0.04) = 0.04 (only A contributes)
    per_symbol = {"A": {"d1": 0.02, "d2": 0.04}, "B": {"d1": 0.06}}
    out = risk.layer_return_series(per_symbol, ["A", "B"])
    assert out == {"d1": pytest.approx(0.04), "d2": pytest.approx(0.04)}


def test_layer_return_series_empty_symbols_list_is_empty():
    assert risk.layer_return_series({"A": {"d1": 0.01}}, []) == {}


# --------------------------------------------------------------------------- module constants


def test_module_constants():
    assert risk.MIN_BARS == 60
    assert risk.WINDOW == 252


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
