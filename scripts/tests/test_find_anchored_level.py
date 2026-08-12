"""The zoom-out act's honesty rails.

The reel's second act claims "this line has been tested 10 times since 2021".
That claim is only worth making if the touches are real, distinct, and actually
behind the window - so these tests pin the counting rules rather than trusting
the scanner to have been careful.

Two rules carry the editorial weight:

  * a "visit" is a cluster, not a bar. Price sitting on a level for six sessions
    is ONE test of that level, not six. Counting bars would let any sideways
    chop advertise itself as a heavily-defended line.

  * the PLAYBACK window is capped at 126 bars (6 months). Owner ruling: history
    older than that is revealed by the camera, never played back bar by bar,
    because watching three years of tape print is boring. The cap lives here so
    a fixture cannot quietly ask for a ten-minute reel.

Everything else is refusal: too few visits, too little history, dirty bars. The
scanner reports UNMATCHED rather than widening the tolerance until it finds
what it was asked to find.
"""
import pytest

from ta_quiz import find_anchored_level as fal


def _bar(o, h, l, c, date="2024-01-01"):
    return {"date": date, "o": o, "h": h, "l": l, "c": c}


def _flat(n, price, start_day=1):
    """n bars that do NOT touch 100 - the filler between visits."""
    return [_bar(price, price + 0.2, price - 0.2, price, f"2024-01-{start_day + i:02d}")
            for i in range(n)]


def _touch(n, level=100.0, start_day=1):
    """n consecutive bars whose range straddles `level`."""
    return [_bar(level - 0.5, level + 0.5, level - 1.0, level + 0.3,
                 f"2024-02-{start_day + i:02d}") for i in range(n)]


# ----------------------------------------------------------------- visits

def test_consecutive_touching_bars_count_as_one_visit():
    # Six bars sitting on the level is one test of it, not six.
    bars = _flat(10, 90) + _touch(6)
    assert len(fal.visits(bars, 100.0, end=len(bars))) == 1


def test_touches_separated_by_a_gap_count_separately():
    bars = _flat(5, 90) + _touch(2) + _flat(20, 90) + _touch(2, start_day=20)
    assert len(fal.visits(bars, 100.0, end=len(bars))) == 2


def test_visits_after_the_end_index_are_not_counted():
    # The whole point is PRIOR touches; the formation's own bars must not
    # inflate the count of history behind it.
    bars = _flat(5, 90) + _touch(2) + _flat(20, 90) + _touch(2, start_day=20)
    assert len(fal.visits(bars, 100.0, end=7)) == 1


def test_a_visit_carries_the_date_of_its_first_bar():
    bars = _flat(5, 90) + _touch(3, start_day=11)
    assert fal.visits(bars, 100.0, end=len(bars))[0].date == "2024-02-11"


def test_bars_that_miss_the_level_by_more_than_the_tolerance_are_not_visits():
    bars = _flat(30, 90)  # tops out at 90.2, nowhere near 100
    assert fal.visits(bars, 100.0, end=len(bars)) == []


# ------------------------------------------------------------------ plan

def _series_with_history(n_visits=3, history=200):
    """A series with `n_visits` spaced touches, then filler, then a window."""
    bars = []
    for v in range(n_visits):
        bars += _touch(2, start_day=1 + v)
        bars += _flat(history // max(1, n_visits), 90)
    window_start = len(bars)
    bars += _touch(2, start_day=25) + _flat(20, 101)
    return bars, window_start, len(bars) - 1


def test_plan_reports_the_prior_visits_it_found():
    bars, ws, we = _series_with_history(n_visits=4)
    plan = fal.plan(bars, level=100.0, window_start=ws, window_end=we)
    assert len(plan["touches"]) == 4


def test_plan_refuses_when_fewer_than_three_prior_visits():
    bars, ws, we = _series_with_history(n_visits=2)
    with pytest.raises(fal.Unmatched, match="visits"):
        fal.plan(bars, level=100.0, window_start=ws, window_end=we)


def test_plan_refuses_when_history_is_shorter_than_six_months():
    # Three visits, but all of them inside the last 126 bars - there is no
    # "deep past" to zoom out to, so the second act has nothing to show.
    bars, ws, we = _series_with_history(n_visits=3, history=30)
    with pytest.raises(fal.Unmatched, match="history"):
        fal.plan(bars, level=100.0, window_start=ws, window_end=we)


def test_playback_window_is_capped_at_126_bars():
    bars, ws, we = _series_with_history(n_visits=4)
    plan = fal.plan(bars, level=100.0, window_start=ws, window_end=we)
    assert plan["live0"] >= plan["breakout"] - fal.PLAYBACK_MAX


def test_deep_viewport_reaches_back_past_the_oldest_visit():
    bars, ws, we = _series_with_history(n_visits=4)
    plan = fal.plan(bars, level=100.0, window_start=ws, window_end=we)
    assert plan["deep0"] <= plan["touches"][0]["i"]


def test_touches_are_flagged_by_whether_playback_reaches_them():
    bars, ws, we = _series_with_history(n_visits=4)
    plan = fal.plan(bars, level=100.0, window_start=ws, window_end=we)
    # The oldest visit is hundreds of bars back; playback only spans 126.
    assert plan["touches"][0]["inLive"] is False
    assert any(t["inLive"] for t in plan["touches"]) or plan["live0"] > plan["touches"][-1]["i"]


def test_plan_refuses_a_window_containing_a_dirty_bar():
    # CLAUDE.md 10.1: a close more than 15c outside the session range is
    # quarantined, and any window containing one is rejected outright.
    bars, ws, we = _series_with_history(n_visits=4)
    bars[we - 2] = _bar(100, 100.5, 99.5, 101.0)  # close 50c above the high
    with pytest.raises(fal.Unmatched, match="integrity"):
        fal.plan(bars, level=100.0, window_start=ws, window_end=we)
