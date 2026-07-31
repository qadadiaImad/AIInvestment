"""The honest hit rate behind the chart-patterns sheet.

The sheet's first cut printed ten formations and ten wins, because the scanner
kept only instances whose target filled (find_real_patterns.finish). A 10-of-10
strike rate reads as a claim about the PATTERNS, and it is not true - it is a
claim about the selection. These tests pin the arithmetic that replaces it:
resolve every detection the way a trader holding daily bars could have, then
report how often the formation actually paid.

The conservative calls are deliberate and are what make the number honest:
  * a bar whose range holds BOTH the stop and the target is not a win - daily
    bars cannot say which printed first, so it counts against,
  * a trade still open at the horizon is not a win either - it stays in the
    denominator, because "it never got there" is a real outcome.
"""
import pytest

from patterns_post import find_real_patterns as frp


def _bar(o, h, l, c, date="2024-01-01"):
    return {"date": date, "o": o, "h": h, "l": l, "c": c}


# A setup block is four flat bars with their lows at 100, then a breakout bar
# closing at 110. So stop = 100 * 0.998 = 99.8, risk = 10.2, 2R target = 130.4.
_SETUP = [_bar(100, 100, 100, 100) for _ in range(4)] + [_bar(101, 110, 100, 110)]
_AFTER = {
    "win": [_bar(111, 131, 110, 130)],           # clears 130.4, never sees 99.8
    "loss": [_bar(109, 112, 99, 100)],           # takes out 99.8 first
    "both": [_bar(110, 131, 99, 105)],           # one bar holds stop AND target
    "open": [_bar(111, 115, 110, 112) for _ in range(14)],
    # Five bars flat at 110: the stop lands 0.22 away on a 0.33 floor, so there
    # is no tradeable risk distance and the detection is not a sample at all.
    "flat": [],
}
_FLAT_SETUP = [_bar(110, 110, 110, 110) for _ in range(5)]


def _series(*kinds):
    """One price series carrying a setup per kind. Returns (bars, reveals)."""
    bars, reveals = [], []
    for kind in kinds:
        bars.extend(_FLAT_SETUP if kind == "flat" else _SETUP)
        reveals.append(len(bars) - 1)
        bars.extend(_AFTER[kind])
    return bars, reveals


def _insts(reveals, bias="bullish"):
    return [{"reveal": r, "bias": bias} for r in reveals]


def test_target_before_stop_is_a_win():
    bars, (r,) = _series("win")

    res = frp.resolve_trade(bars, r, bull=True)

    assert res["outcome"] == "win"
    assert res["tpAt"] == 1
    assert res["target"] == pytest.approx(130.4)


def test_stop_before_target_is_a_loss():
    bars, (r,) = _series("loss")

    assert frp.resolve_trade(bars, r, bull=True)["outcome"] == "loss"


def test_trade_unresolved_at_the_horizon_is_open():
    bars, (r,) = _series("open")

    res = frp.resolve_trade(bars, r, bull=True)

    assert res["outcome"] == "open"
    assert res["tpAt"] is None


def test_bar_holding_both_stop_and_target_is_not_a_win():
    """Daily bars cannot order two touches inside one session. Count it against."""
    bars, (r,) = _series("both")

    assert frp.resolve_trade(bars, r, bull=True)["outcome"] == "loss"


def test_trade_with_negligible_risk_is_untradeable():
    """An entry sitting on its own stop is not a trade, so it is not a sample."""
    bars, (r,) = _series("flat")

    assert frp.resolve_trade(bars, r, bull=True) is None


def test_bearish_stop_sits_above_the_structure():
    bars = [_bar(100, 100, 100, 100) for _ in range(4)] + [_bar(99, 100, 90, 90)]
    bars += [_bar(89, 90, 69, 70)]

    res = frp.resolve_trade(bars, 4, bull=False)

    assert res["stop"] == pytest.approx(100.2)
    assert res["outcome"] == "win"


def test_hit_rate_counts_open_trades_in_the_denominator():
    """Three detections, one win: the sheet must say 33%, not 100%."""
    bars, reveals = _series("win", "loss", "open")

    stats = frp.hit_rate(bars, _insts(reveals))

    assert (stats["wins"], stats["losses"], stats["open"]) == (1, 1, 1)
    assert stats["n"] == 3
    assert stats["pct"] == 33


def test_hit_rate_counts_one_trade_per_breakout_bar():
    """Two detections firing on the same bar are one trade, not two samples."""
    bars, (r,) = _series("win")

    assert frp.hit_rate(bars, _insts([r, r]))["n"] == 1


def test_hit_rate_drops_untradeable_detections_from_the_sample():
    bars, reveals = _series("flat", "win")

    stats = frp.hit_rate(bars, _insts(reveals))

    assert stats["n"] == 1
    assert stats["pct"] == 100


def test_hit_rate_of_no_tradeable_detections_is_reported_as_no_sample():
    bars, reveals = _series("flat")

    stats = frp.hit_rate(bars, _insts(reveals))

    assert stats["n"] == 0
    assert stats["pct"] is None
