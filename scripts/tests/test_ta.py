"""Hand-computable fixtures for aiinvest.ta — every expected number derived in a comment.

`test_rsi_known_oscillation` uses 15 closes (period+1), not 20, so the Wilder seed IS
the final value (14 diffs exactly fill the period, no continuation smoothing) — this
keeps the fixture hand-computable without walking 5 extra recursive smoothing steps.
`nearest_level` labels are upper-cased ("R1"/"PP"/...) to match the binding ta_desk.json
v1 contract's `nearest_level.label` example, not the lowercase shorthand in prose specs.
"""
import datetime

import pytest

from aiinvest import ta


def _bar(date, o, h, lo, c):
    return {"date": date, "open": o, "high": h, "low": lo, "close": c}


# --------------------------------------------------------------------------- pivots


def test_classic_pivots_daily():
    # H=110, L=100, C=105 -> pp=(110+100+105)/3=105
    p = ta.classic_pivots(high=110, low=100, close=105)
    assert p["pp"] == pytest.approx(105)
    assert p["r1"] == pytest.approx(110)   # 2*105-100
    assert p["s1"] == pytest.approx(100)   # 2*105-110
    assert p["r2"] == pytest.approx(115)   # 105+(110-100)
    assert p["s2"] == pytest.approx(95)    # 105-(110-100)
    assert p["r3"] == pytest.approx(120)   # 110+2*(105-100)
    assert p["s3"] == pytest.approx(90)    # 100-2*(110-105)


def test_daily_pivots_basis_excludes_todays_partial_bar():
    series = [
        _bar("2026-07-12", 100, 102, 99, 101),
        _bar("2026-07-13", 101, 105, 100, 104),
        _bar("2026-07-14", 104, 106, 103, 105),  # today's still-forming bar
    ]
    basis = ta.daily_pivots_basis(series, as_of_date="2026-07-14")
    assert basis == series[1]


def test_daily_pivots_basis_none_for_empty_series():
    assert ta.daily_pivots_basis([], as_of_date="2026-07-14") is None


# --------------------------------------------------------------------------- ATR


def test_true_range_gap_up_case():
    # H=105, L=103, prev_close=100 -> max(2, 5, 3) = 5
    assert ta.true_range(high=105, low=103, prev_close=100) == 5


def test_atr_constant_true_range():
    # 15 bars, close constant at 100, high=101/low=99 -> every TR (bars 2..15) = 2
    series = [_bar(f"2026-06-{i:02d}", 100, 101, 99, 100) for i in range(1, 16)]
    assert ta.atr(series, 14) == pytest.approx(2.0)


def test_atr_insufficient_history_returns_none():
    series = [_bar(f"2026-06-{i:02d}", 100, 101, 99, 100) for i in range(1, 10)]
    assert ta.atr(series, 14) is None


def test_atr_bands_none_when_atr_none():
    assert ta.atr_bands(100.0, None) is None


def test_atr_bands_basic():
    bands = ta.atr_bands(price=100.0, atr_value=2.0)
    assert bands == {"upper_1x": 102.0, "lower_1x": 98.0, "upper_2x": 104.0, "lower_2x": 96.0}


# --------------------------------------------------------------------------- RSI


def test_rsi_all_gains_is_100():
    closes = [float(i) for i in range(1, 22)]  # 1..21, monotonic +1 diffs -> avg_loss=0
    assert ta.rsi(closes, 14) == 100.0


def test_rsi_known_oscillation():
    closes = [100.0]
    for i in range(14):
        closes.append(closes[-1] + (2 if i % 2 == 0 else -1))
    assert len(closes) == 15  # 14 diffs == period -> seed IS the final value, no smoothing
    # diffs: [+2,-1]*7 -> avg_gain=(7*2)/14=1.0, avg_loss=(7*1)/14=0.5, RS=2.0
    value = ta.rsi(closes, 14)
    assert value == pytest.approx(100 - 100 / 3, rel=1e-6)  # ~66.67


def test_rsi_insufficient_history_returns_none():
    closes = [float(i) for i in range(1, 10)]  # 9 closes -> 8 diffs < 14
    assert ta.rsi(closes, 14) is None


def test_rsi_state_thresholds():
    assert ta.rsi_state(71) == "overbought"
    assert ta.rsi_state(29) == "oversold"
    assert ta.rsi_state(50) == "neutral"
    assert ta.rsi_state(None) is None


# --------------------------------------------------------------------------- SMA / trend


def test_sma_and_trend_state_bullish_stack():
    closes = [float(i) for i in range(1, 261)]  # 1..260
    sma20 = ta.sma(closes, 20)    # mean(241..260) = (241+260)/2
    sma50 = ta.sma(closes, 50)    # mean(211..260) = (211+260)/2
    sma200 = ta.sma(closes, 200)  # mean(61..260) = (61+260)/2
    assert sma20 == pytest.approx(250.5)
    assert sma50 == pytest.approx(235.5)
    assert sma200 == pytest.approx(160.5)

    trend = ta.trend_state(price=260.0, sma20=sma20, sma50=sma50, sma200=sma200)
    assert trend["state"] == "bullish"
    assert trend["price_above_sma20"] is True
    assert trend["price_above_sma50"] is True
    assert trend["price_above_sma200"] is True
    assert trend["sma50_above_sma200"] is True


def test_trend_state_unknown_when_sma_missing():
    trend = ta.trend_state(price=100.0, sma20=99.0, sma50=98.0, sma200=None)
    assert trend["state"] == "unknown"


def test_sma_none_when_insufficient_bars():
    assert ta.sma([1.0, 2.0, 3.0], 5) is None


# --------------------------------------------------------------------------- levels / price


def test_fifty_two_week_position_at_new_high():
    series = [_bar("2026-01-01", 100, 250, 90, 200), _bar("2026-02-01", 200, 260, 150, 260)]
    stats = ta.fifty_two_week_stats(series, last=260.0)
    assert stats["high"] == 260
    assert stats["position_pct"] == pytest.approx(100.0)


def test_fifty_two_week_position_midrange():
    series = [_bar("2026-01-01", 1, 260, 1, 1)]
    # (130.5-1)/(260-1)*100 = 129.5/259*100 = 50.0
    stats = ta.fifty_two_week_stats(series, last=130.5)
    assert stats["high"] == 260
    assert stats["low"] == 1
    assert stats["position_pct"] == pytest.approx(50.0)


def test_previous_day_ohlc_picks_last_bar_before_as_of():
    series = [
        _bar("2026-07-12", 100, 102, 99, 101),
        _bar("2026-07-13", 101, 105, 100, 104),
        _bar("2026-07-14", 104, 106, 103, 105),
    ]
    result = ta.previous_day_ohlc(series, as_of_date="2026-07-14")
    assert result["date"] == "2026-07-13"
    assert result["close"] == 104
    # change_pct vs the bar BEFORE it (2026-07-12, close=101): (104-101)/101*100
    assert result["change_pct"] == pytest.approx((104 - 101) / 101 * 100)


def test_previous_day_ohlc_none_for_empty_series():
    assert ta.previous_day_ohlc([], as_of_date="2026-07-14") is None


def test_day_change_pct_basic():
    assert ta.day_change_pct(102, 100) == pytest.approx(2.0)


def test_day_change_pct_none_on_zero_previous_close():
    assert ta.day_change_pct(102, 0) is None
    assert ta.day_change_pct(102, None) is None


def test_nearest_level_picks_closest_and_signs_distance():
    pivots = ta.classic_pivots(high=110, low=100, close=105)  # pp=105, r1=110
    price = 108.0  # dist to pp=3, dist to r1=2 -> r1 wins
    nearest = ta.nearest_level(price, pivots)
    assert nearest["label"] == "R1"
    assert nearest["value"] == pytest.approx(110)
    assert nearest["distance_pct"] == pytest.approx((110 - 108) / 108 * 100)
    assert nearest["distance_pct"] > 0  # level above price


def test_nearest_level_none_for_empty_pivots():
    assert ta.nearest_level(100.0, {}) is None


# --------------------------------------------------------------------------- sessions


def test_session_ranges_partitions_by_utc_hour():
    bars = [{"datetime": f"2026-07-14T{h:02d}:00:00Z",
             "open": 100 + h, "high": 100 + h + 0.5, "low": 100 + h - 0.5, "close": 100 + h}
            for h in range(24)]
    as_of = datetime.datetime(2026, 7, 14, 23, 0, tzinfo=datetime.timezone.utc)
    sessions = ta.session_ranges(bars, as_of=as_of)

    assert sessions["date"] == "2026-07-14"  # contract: sessions.date = UTC date of as_of
    assert sessions["tokyo"]["high"] == pytest.approx(108.5)   # h=8 -> 100+8+0.5
    assert sessions["tokyo"]["low"] == pytest.approx(99.5)     # h=0 -> 100+0-0.5
    assert sessions["tokyo"]["bar_count"] == 9
    assert sessions["tokyo"]["window_utc"] == "00:00-09:00"

    assert sessions["london"]["high"] == pytest.approx(116.5)  # h=16
    assert sessions["london"]["low"] == pytest.approx(107.5)   # h=8
    assert sessions["london"]["bar_count"] == 9

    assert sessions["new_york"]["high"] == pytest.approx(121.5)  # h=21
    assert sessions["new_york"]["low"] == pytest.approx(112.5)   # h=13
    assert sessions["new_york"]["bar_count"] == 9


def test_session_complete_flag_false_for_future_window():
    bars = [{"datetime": "2026-07-14T05:00:00Z", "open": 1, "high": 1.5, "low": 0.5, "close": 1}]
    as_of = datetime.datetime(2026, 7, 14, 6, 0, tzinfo=datetime.timezone.utc)
    sessions = ta.session_ranges(bars, as_of=as_of)
    assert sessions["new_york"]["complete"] is False  # closes 22:00, as_of hour=6


def test_session_complete_flag_true_for_elapsed_window():
    bars = [{"datetime": "2026-07-14T05:00:00Z", "open": 1, "high": 1.5, "low": 0.5, "close": 1}]
    as_of = datetime.datetime(2026, 7, 14, 10, 0, tzinfo=datetime.timezone.utc)
    sessions = ta.session_ranges(bars, as_of=as_of)
    assert sessions["tokyo"]["complete"] is True  # closes 09:00, as_of hour=10


def test_session_ranges_empty_window_returns_none_high_low():
    bars = [{"datetime": "2026-07-14T20:00:00Z", "open": 1, "high": 1.5, "low": 0.5, "close": 1}]
    as_of = datetime.datetime(2026, 7, 14, 23, 0, tzinfo=datetime.timezone.utc)
    sessions = ta.session_ranges(bars, as_of=as_of)
    assert sessions["tokyo"]["bar_count"] == 0
    assert sessions["tokyo"]["high"] is None
    assert sessions["tokyo"]["low"] is None


def test_sparkline_from_intraday_trims_to_n_ascending():
    bars = [{"datetime": f"2026-07-{(i // 24) + 1:02d}T{i % 24:02d}:00:00Z",
             "open": float(i), "high": float(i), "low": float(i), "close": float(i)}
            for i in range(100)]
    spark = ta.sparkline_from_intraday(bars, n=48)
    assert len(spark) == 48
    assert spark[0]["c"] == 52.0   # index 100-48=52
    assert spark[-1]["c"] == 99.0
    assert spark[0]["t"] == bars[52]["datetime"]
    assert set(spark[0].keys()) == {"t", "c"}


def test_sparkline_from_intraday_shorter_than_n_returns_all():
    bars = [{"datetime": f"2026-07-14T{h:02d}:00:00Z", "open": h, "high": h, "low": h,
             "close": float(h)} for h in range(5)]
    spark = ta.sparkline_from_intraday(bars, n=48)
    assert len(spark) == 5


# --------------------------------------------------------------------------- universe


def test_universe_has_eleven_instruments_and_fixed_groups():
    assert len(ta.UNIVERSE) == 11
    assert ta.GROUPS == ["FX", "METALS", "ENERGY", "INDEX"]
    for sym, meta in ta.UNIVERSE.items():
        assert meta["group"] in ta.GROUPS
        assert meta["asset_class"] in ("fx", "commodity", "index")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
