"""The failed-break detector behind the previous-day-high/low quiz reel.

The strategy the reel teaches: mark yesterday's high and low, and a break above
the high only counts with ACCEPTANCE (closes holding above the line). These
tests pin the detector's honesty rules:

  * a "failed break" needs real acceptance first (>= min_above closes above) —
    one poke over the line failing is noise, not a story,
  * the decision bar is the LAST close above the line — the moment of maximum
    breakout belief, chosen by definition rather than by eyeing the outcome,
  * a break that holds into the end of the tape is NOT a failed break — the
    detector reports nothing rather than nudging the window,
  * the reveal after the decision must actually fall, or there is no SELL reel.
"""
import pytest

from ta_quiz import find_real_pdhl as pdhl


def _bar(o, h, l, c, date="2026-07-24 14:00Z"):
    return {"date": date, "o": o, "h": h, "l": l, "c": c}


PDH, PDL = 110.0, 100.0

_BELOW = [_bar(105, 106, 104, 105) for _ in range(6)]        # inside the range
_ABOVE = [_bar(110, 112, 109.5, 111) for _ in range(4)]      # acceptance run
_FAIL = [_bar(110, 110.5, 107, 108) for _ in range(6)]       # back inside, stays


def test_resample_aggregates_ohlc_in_groups():
    ones = [
        _bar(10, 12, 9, 11), _bar(11, 15, 11, 14), _bar(14, 14, 8, 9),
        _bar(9, 10, 9, 10), _bar(10, 13, 10, 12),
    ]
    out = pdhl.resample(ones, 5)

    assert len(out) == 1
    assert out[0]["o"] == 10 and out[0]["c"] == 12
    assert out[0]["h"] == 15 and out[0]["l"] == 8


def test_resample_drops_a_trailing_partial_group():
    ones = [_bar(10, 12, 9, 11) for _ in range(12)]

    assert len(pdhl.resample(ones, 5)) == 2


def test_detects_failed_break_with_decision_on_last_close_above():
    bars = _BELOW + _ABOVE + _FAIL

    hit = pdhl.find_setup(bars, PDH, min_above=3)

    assert hit is not None
    assert hit["break_at"] == 6            # first close above the line
    assert hit["decision"] == 9            # LAST close above the line
    assert hit["closes_above"] == 4


def test_no_detection_when_the_break_holds_to_the_end():
    bars = _BELOW + _ABOVE                 # accepted above, never came back

    assert pdhl.find_setup(bars, PDH, min_above=3) is None


def test_no_detection_without_real_acceptance():
    bars = _BELOW + [_bar(110, 112, 109, 111)] + _FAIL   # one poke, not a break

    assert pdhl.find_setup(bars, PDH, min_above=3) is None


def test_no_detection_when_price_never_breaks():
    assert pdhl.find_setup(_BELOW * 3, PDH, min_above=3) is None


def test_no_detection_when_the_fail_lacks_reveal_room():
    """Decision on the tape's last bars leaves nothing to reveal — not a reel."""
    bars = _BELOW + _ABOVE + _FAIL[:2]

    assert pdhl.find_setup(bars, PDH, min_above=3, min_reveal=6) is None


def test_prev_day_levels_picks_the_prior_trading_day():
    daily = [
        {"date": "2026-07-22", "o": 1, "h": 108, "l": 99, "c": 1},
        {"date": "2026-07-23", "o": 1, "h": 110, "l": 100, "c": 1},
        {"date": "2026-07-27", "o": 1, "h": 111, "l": 101, "c": 1},  # after
    ]
    lv = pdhl.prev_day_levels(daily, "2026-07-24")

    assert lv == {"date": "2026-07-23", "pdh": 110, "pdl": 100}


def test_prev_day_levels_refuses_a_gap_it_cannot_bridge():
    daily = [{"date": "2026-07-27", "o": 1, "h": 111, "l": 101, "c": 1}]

    assert pdhl.prev_day_levels(daily, "2026-07-24") is None


def test_lesson_fixture_carries_the_detector_indices_and_tape():
    """The sequel reel's beats are timed off breakAt/decisionAt — they must be
    the detector's indices, re-based to the trimmed window, not re-derived."""
    setup = _BELOW + _ABOVE
    reveal = _FAIL
    hit = {"break_at": 6, "decision": 9, "closes_above": 4}

    fx = pdhl.build_lesson(
        {"symbol": "SPY", "retrieved_at": "2026-07-26T00:00:00Z"},
        "2026-07-24", setup, reveal,
        {"date": "2026-07-23", "pdh": PDH, "pdl": PDL},
        hit, start=0,
    )

    assert fx["breakAt"] == 6
    assert fx["decisionAt"] == 9
    assert len(fx["candles"]) == len(setup) + len(reveal)
    assert fx["levelPrice"] == PDH and fx["level2Price"] == PDL
    assert fx["durationInFrames"] >= 600
