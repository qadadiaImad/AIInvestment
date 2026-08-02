"""Tests for the Hormuz oil-reel pattern + trade maths.

Everything the reel puts on screen as a number comes from here. The point of
these tests is that a definition can't quietly drift into whatever happened to
look good on the chart — the scanner must FIND a bar that already satisfies the
definition, and the trade must resolve by one rule that display and statistic
both read from.
"""
import pytest

from oil_reel.hormuz import (
    crisis_split,
    find_inside_bar_breakout,
    resolve_trade,
    base_rate,
)


def bar(d, o, h, l, c):
    return {"d": d, "o": o, "h": h, "l": l, "c": c}


# A clean textbook sequence: a wide "mother" bar, a bar that coils entirely
# inside it, then a close above the mother's high.
CLEAN = [
    bar("2026-01-05", 100, 102, 99, 101),   # 0
    bar("2026-01-06", 101, 110, 98, 104),   # 1: MOTHER (wide)
    bar("2026-01-07", 105, 108, 101, 103),  # 2: INSIDE (h<=110, l>=98)
    bar("2026-01-08", 103, 113, 102, 112),  # 3: TRIGGER (close 112 > 110)
]


class TestFindInsideBarBreakout:
    def test_finds_the_textbook_sequence(self):
        got = find_inside_bar_breakout(CLEAN)
        assert got is not None
        assert (got["mother"], got["inside"], got["trigger"]) == (1, 2, 3)

    def test_inside_bar_must_be_inside_on_BOTH_sides(self):
        # high is inside but the low pokes below the mother's low: not an
        # inside bar. A bar that only respects one side is a lower high, not
        # a compression.
        bars = list(CLEAN)
        bars[2] = bar("2026-01-07", 105, 108, 97, 103)
        assert find_inside_bar_breakout(bars) is None

    def test_trigger_must_CLOSE_above_the_mother_high_not_merely_touch_it(self):
        # a wick through the level is not a breakout — that is exactly the
        # trap the reel is about
        bars = list(CLEAN)
        bars[3] = bar("2026-01-08", 103, 113, 102, 109)  # pokes 113, closes 109
        assert find_inside_bar_breakout(bars) is None

    def test_returns_none_on_a_window_with_no_compression(self):
        trending = [bar(f"2026-01-{i:02d}", 100 + i, 105 + i, 99 + i, 104 + i) for i in range(1, 9)]
        assert find_inside_bar_breakout(trending) is None

    def test_takes_the_FIRST_qualifying_sequence_not_the_prettiest(self):
        # two valid sequences; the scanner must not shop for the better one
        bars = CLEAN + [
            bar("2026-01-09", 112, 130, 111, 129),  # 4 mother
            bar("2026-01-12", 120, 128, 115, 121),  # 5 inside
            bar("2026-01-13", 122, 140, 120, 138),  # 6 trigger
        ]
        got = find_inside_bar_breakout(bars)
        assert (got["mother"], got["inside"], got["trigger"]) == (1, 2, 3)


class TestResolveTrade:
    """Entry at the trigger close, stop under the coil, target at R multiple."""

    def test_entry_stop_target_come_from_the_pattern_not_from_the_outcome(self):
        t = resolve_trade(CLEAN, mother=1, inside=2, trigger=3, rr=2.0)
        # prices come out rounded to the cent — they go on screen as prices
        assert t["entry"] == 112               # trigger close
        assert t["stop"] == pytest.approx(101 * 0.998, abs=0.01)  # inside low, padded
        risk = 112 - 101 * 0.998
        assert t["target"] == pytest.approx(112 + 2 * risk, abs=0.01)

    def test_target_reached_before_stop_is_a_win_and_records_the_bar(self):
        risk = 112 - 101 * 0.998
        tgt = 112 + 2 * risk
        bars = CLEAN + [
            bar("2026-01-09", 112, 114, 111, 113),
            bar("2026-01-12", 113, tgt + 1, 112, tgt),
        ]
        t = resolve_trade(bars, 1, 2, 3, rr=2.0)
        assert t["outcome"] == "win"
        assert t["tpAt"] == 2                  # bars AFTER the trigger

    def test_stop_first_is_a_loss(self):
        bars = CLEAN + [bar("2026-01-09", 110, 111, 90, 95)]
        t = resolve_trade(bars, 1, 2, 3, rr=2.0)
        assert t["outcome"] == "loss"
        assert t["tpAt"] is None

    def test_a_bar_holding_BOTH_stop_and_target_resolves_as_a_loss(self):
        # daily bars can't order two intrabar touches; assuming the good one
        # is how a backtest lies to you
        risk = 112 - 101 * 0.998
        bars = CLEAN + [bar("2026-01-09", 112, 112 + 3 * risk, 90, 100)]
        t = resolve_trade(bars, 1, 2, 3, rr=2.0)
        assert t["outcome"] == "loss"

    def test_unresolved_within_the_horizon_is_open_not_a_win(self):
        bars = CLEAN + [bar(f"2026-02-{i:02d}", 112, 113, 111, 112) for i in range(1, 9)]
        t = resolve_trade(bars, 1, 2, 3, rr=2.0, horizon=5)
        assert t["outcome"] == "open"

    def test_negligible_risk_is_untradeable(self):
        # stop sits 0.28% under entry — below that any slippage dominates the
        # trade and the R multiple is fiction, so it is not a sample
        flat = [
            bar("2026-01-05", 100.00, 100.20, 99.90, 100.00),
            bar("2026-01-06", 100.00, 100.35, 100.25, 100.30),  # mother
            bar("2026-01-07", 100.30, 100.34, 100.28, 100.31),  # inside
            bar("2026-01-08", 100.31, 100.40, 100.30, 100.36),  # trigger
        ]
        assert find_inside_bar_breakout(flat) is not None  # the shape is there
        assert resolve_trade(flat, 1, 2, 3, rr=2.0) is None  # the trade isn't


class TestBaseRate:
    """The honest bit: how often this pattern actually pays, on this series."""

    def test_counts_every_occurrence_not_only_the_ones_that_worked(self):
        # one winner, one loser -> 50%, and the loser must be in the sample
        risk = 112 - 101 * 0.998
        seq = CLEAN + [bar("2026-01-09", 112, 112 + 2 * risk + 1, 111, 118)]
        seq += [
            bar("2026-02-01", 118, 130, 117, 120),   # mother
            bar("2026-02-02", 121, 128, 118, 124),   # inside
            bar("2026-02-03", 124, 133, 123, 131),   # trigger
            bar("2026-02-04", 130, 131, 100, 105),   # stopped
        ]
        r = base_rate(seq, rr=2.0)
        assert r["n"] == 2
        assert r["wins"] == 1
        assert r["pct"] == 50

    def test_open_trades_stay_in_the_denominator(self):
        seq = CLEAN + [bar(f"2026-02-{i:02d}", 112, 113, 111, 112) for i in range(1, 9)]
        r = base_rate(seq, rr=2.0, horizon=4)
        assert r["n"] == 1 and r["wins"] == 0 and r["pct"] == 0

    def test_empty_sample_reports_no_percentage_rather_than_zero(self):
        r = base_rate([bar("2026-01-05", 100, 101, 99, 100)], rr=2.0)
        assert r["n"] == 0 and r["pct"] is None


class TestCrisisSplit:
    """The claim 'the crisis is what makes it work' must be a computation,
    not an assertion: fires within `within` sessions AFTER a >=shock-size
    daily move go in one bucket, everything else in the other."""

    def _series(self):
        bars = [
            bar("2026-01-02", 100, 101, 99, 100),
            bar("2026-01-05", 106, 108, 105, 107),   # 1: SHOCK day (+7%)
            bar("2026-01-06", 107, 116, 104, 110),   # 2: mother
            bar("2026-01-07", 111, 114, 107, 109),   # 3: inside
            bar("2026-01-08", 109, 119, 108, 118),   # 4: trigger (crisis-conditioned)
            bar("2026-01-09", 117, 118, 95, 100),    # 5: stopped -> loss
        ]
        # filler that can never form an inside bar: highs and lows both rise
        p = 100.0
        for k in range(16):
            bars.append(bar(f"2026-02-{k+1:02d}", p, p + 3, p - 1, p + 2))
            p += 1.0
        # a QUIET fire, far outside the shock window
        q = p
        bars += [
            bar("2026-03-02", q, q + 12, q - 2, q + 4),          # mother
            bar("2026-03-03", q + 5, q + 9, q + 1, q + 3),       # inside
            bar("2026-03-04", q + 3, q + 14, q + 2, q + 13),     # trigger
            bar("2026-03-05", q + 13, q + 60, q + 12, q + 50),   # runs -> win
        ]
        return bars

    def test_buckets_split_on_shock_proximity(self):
        s = crisis_split(self._series(), rr=2.0, horizon=12, shock=0.06, within=10)
        assert s["crisis"]["n"] == 1 and s["crisis"]["losses"] == 1
        assert s["quiet"]["n"] == 1 and s["quiet"]["wins"] == 1

    def test_shock_days_are_reported_with_dates(self):
        s = crisis_split(self._series(), rr=2.0, horizon=12, shock=0.06, within=10)
        assert "2026-01-05" in s["shockDays"]

    def test_a_fire_on_the_shock_day_itself_is_not_conditioned(self):
        # 'after the shock' means strictly after — the shock bar can't be its
        # own confirmation
        bars = self._series()
        s = crisis_split(bars, rr=2.0, horizon=12, shock=0.06, within=0)
        assert s["crisis"]["n"] == 0
