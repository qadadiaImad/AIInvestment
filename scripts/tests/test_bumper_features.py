import pytest

from bumper import features as f


def _closes(vals, start="2021-01"):
    y, m = map(int, start.split("-"))
    out = []
    for v in vals:
        out.append((f"{y:04d}-{m:02d}", v))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def test_run_start_is_first_qualifying_window_not_best():
    # flat for a year; windows starting at months 0-2 reach only 2.0-2.4x, the window
    # starting at month 3 is the first to clear 2.5x; a much bigger window comes later.
    vals = [10] * 12 + [20, 22, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60] + [60] * 3 + [60 + 40 * i for i in range(1, 13)]
    c = _closes(vals)
    assert f.run_start(c, months=12, min_multiple=2.5) == c[3][0]
    i, mult = f.best_forward_window(c, 12)
    assert mult > 4  # the later window is bigger, but run_start picked the first one


def test_run_start_none_when_no_window_qualifies():
    c = _closes([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])
    assert f.run_start(c, months=12, min_multiple=2.5) is None


def test_value_at_respects_lag_and_order():
    s = [("2023-03-31", 1.0), ("2023-06-30", 2.0), ("2023-09-30", 3.0)]
    assert f.value_at(s, "2023-07-15") == (2.0, "2023-06-30")
    assert f.value_at(s, "2023-03-30") == (None, None)
    assert f.value_at(s, "2025-01-01") == (None, None)  # too stale


def test_ttm_and_yoy():
    rev = [(f"20{y}-{q}", v) for (y, q, v) in [
        ("22", "03-31", 10), ("22", "06-30", 10), ("22", "09-30", 10), ("22", "12-31", 10),
        ("23", "03-31", 20), ("23", "06-30", 25), ("23", "09-30", 30), ("23", "12-31", 35)]]
    assert f.ttm(rev, "2023-12-31") == 110
    assert f.yoy_growth(rev, "2023-12-31") == pytest.approx(2.5)  # 35/10 - 1
    assert f.ttm(rev, "2022-06-30") is None


def test_features_vector_runway_and_dilution():
    q = {
        "revenue": [("2023-03-31", 5), ("2023-06-30", 6), ("2023-09-30", 8), ("2023-12-31", 11)],
        "rnd": [("2023-03-31", 4), ("2023-06-30", 4), ("2023-09-30", 5), ("2023-12-31", 5)],
        "ocf": [("2023-03-31", -10), ("2023-06-30", -10), ("2023-09-30", -10), ("2023-12-31", -10)],
        "cash": [("2023-12-31", 120)],
        "shares": [("2022-12-31", 100), ("2023-12-31", 130)],
    }
    x = f.features_at("2024-01-15", q)
    assert x["revenue_ttm"] == 30
    assert x["rnd_to_rev"] == pytest.approx(18 / 30)
    assert x["runway_years"] == pytest.approx(3.0)
    assert x["shares_growth_yoy"] == pytest.approx(0.3)
    assert x["profitable"] is False


def test_months_before_and_auc():
    assert f.months_before("2024-03", 12) == "2023-03-01"
    assert f.months_before("2024-01", 2) == "2023-11-01"
    assert f.auc([3, 4, 5], [1, 2]) == 1.0
    assert f.auc([1, 2], [1, 2]) == 0.5
    assert f.auc([], [1]) is None
