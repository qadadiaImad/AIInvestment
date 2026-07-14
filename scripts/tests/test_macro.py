"""Hand-computable fixtures for aiinvest.macro — every expected number derived in a
comment. Mirrors tests/test_ta.py's style: pure functions, no mocking, no network.

Spec: docs/superpowers/specs/2026-07-14-macro-desk-design.md §1-§9.
"""
import datetime

import pytest

from aiinvest import macro


def _row(date, value):
    return {"date": date, "value": value}


# --------------------------------------------------------------------------- downsample


def test_downsample_identity_when_len_le_target():
    rows = [_row(f"2026-01-{i:02d}", float(i)) for i in range(1, 11)]  # 10 rows
    out = macro.downsample(rows, target_n=60)
    assert out == rows


def test_downsample_365_to_60_exact_cap_endpoints_preserved():
    rows = [_row((datetime.date(2025, 1, 1) + datetime.timedelta(days=i)).isoformat(), float(i))
            for i in range(365)]
    out = macro.downsample(rows, target_n=60)
    assert len(out) <= 60
    assert out[0] == rows[0]
    assert out[-1] == rows[-1]


def test_downsample_target_n_one_no_zero_division():
    rows = [_row(f"2026-01-{i:02d}", float(i)) for i in range(1, 11)]
    out = macro.downsample(rows, target_n=1)
    assert out == [rows[0]]


# --------------------------------------------------------------------------- nearest_by_offset


def test_nearest_by_offset_exact_match():
    rows = [_row("2025-07-14", 1.0), _row("2026-07-14", 2.0)]
    got = macro.nearest_by_offset(rows, "2026-07-14", offset_days=365, tolerance_days=5)
    assert got == rows[0]


def test_nearest_by_offset_no_match_within_tolerance_returns_none():
    rows = [_row("2020-01-01", 1.0)]
    got = macro.nearest_by_offset(rows, "2026-07-14", offset_days=365, tolerance_days=5)
    assert got is None


def test_nearest_by_offset_two_candidates_nearer_wins():
    # target = 2026-07-14 - 365d = 2025-07-14. Candidates at +5d (2025-07-19) and
    # +15d (2025-07-29) from target -> the +5d one is nearer.
    rows = [_row("2025-07-19", 10.0), _row("2025-07-29", 20.0)]
    got = macro.nearest_by_offset(rows, "2026-07-14", offset_days=365, tolerance_days=20)
    assert got == rows[0]


def test_nearest_by_offset_skips_none_values():
    rows = [_row("2025-07-14", None), _row("2025-07-15", 5.0)]
    got = macro.nearest_by_offset(rows, "2026-07-14", offset_days=365, tolerance_days=5)
    assert got == rows[1]


# --------------------------------------------------------------------------- yoy


def _monthly_rows(start="2024-07-01", n=24, values=None):
    rows = []
    d = datetime.date.fromisoformat(start)
    for i in range(n):
        month = ((d.month - 1 + i) % 12) + 1
        year = d.year + (d.month - 1 + i) // 12
        date = datetime.date(year, month, 1).isoformat()
        val = values[i] if values is not None else 100.0 + i
        rows.append(_row(date, val))
    return rows


def test_yoy_known_2pct_at_month_12():
    # 24 monthly rows, index starts at 100.0 in month 0, grows so that month-12 value is
    # exactly 2% above month-0's value: 100.0 -> 102.0.
    values = [100.0 + i for i in range(24)]
    values[12] = values[0] * 1.02  # 102.0, exactly 2% YoY vs month 0
    rows = _monthly_rows(values=values)
    out = macro.yoy(rows, tolerance_days=20)
    by_date = {r["date"]: r["value"] for r in out}
    assert by_date[rows[12]["date"]] == pytest.approx(2.0)


def test_yoy_first_year_dropped_not_filled():
    values = [100.0 + i for i in range(24)]
    rows = _monthly_rows(values=values)
    out = macro.yoy(rows, tolerance_days=20)
    out_dates = {r["date"] for r in out}
    # first ~11 months have no comparator ~365d back -> dropped, never zero-filled
    assert rows[0]["date"] not in out_dates
    assert rows[5]["date"] not in out_dates


def test_yoy_none_mid_series_row_excluded_as_target_and_comparator():
    values = [100.0 + i for i in range(24)]
    rows = _monthly_rows(values=values)
    rows[0] = _row(rows[0]["date"], None)  # would-be comparator for month 12
    out = macro.yoy(rows, tolerance_days=20)
    out_dates = {r["date"] for r in out}
    assert rows[0]["date"] not in out_dates  # None row never a target
    assert rows[12]["date"] not in out_dates  # its comparator (month 0) is None -> dropped


def test_yoy_372_day_back_comparator_within_tolerance_still_matches():
    # Two rows 372 days apart (comparator is 7 days beyond the 365d target, within a 20d
    # tolerance) -> still matches and produces a YoY value.
    rows = [_row("2025-07-14", 100.0), _row("2026-07-21", 105.0)]
    out = macro.yoy(rows, tolerance_days=20)
    by_date = {r["date"]: r["value"] for r in out}
    assert rows[1]["date"] in by_date
    assert by_date[rows[1]["date"]] == pytest.approx((105.0 - 100.0) / 100.0 * 100)


# --------------------------------------------------------------------------- curve_chip


@pytest.mark.parametrize("value,expected", [
    (-0.5, "inverted"),
    (0.0, "flat"),
    (0.24, "flat"),
    (0.25, "normal"),
    (1.2, "normal"),
])
def test_curve_chip_thresholds(value, expected):
    chip, warning = macro.curve_chip(value, "2026-07-11")
    assert chip["state"] == expected
    assert chip["key"] == "curve"
    assert warning is None


def test_curve_chip_none_input_state_null_plus_warning():
    chip, warning = macro.curve_chip(None, None)
    assert chip["state"] is None
    assert chip["value"] is None
    assert chip["key"] == "curve"
    assert warning is not None


# --------------------------------------------------------------------------- real_rate_chip


def test_real_rate_chip_restrictive():
    chip, warning = macro.real_rate_chip(4.42, 2.11, "2026-07-11")
    assert chip["value"] == pytest.approx(2.31)
    assert chip["state"] == "restrictive"
    assert warning is None


def test_real_rate_chip_boundary_2pt0_is_neutral_inclusive():
    chip, _ = macro.real_rate_chip(4.0, 2.0, "2026-07-11")
    assert chip["value"] == pytest.approx(2.0)
    assert chip["state"] == "neutral"


def test_real_rate_chip_negative_is_accommodative():
    chip, _ = macro.real_rate_chip(1.99, 2.0, "2026-07-11")
    assert chip["value"] == pytest.approx(-0.01)
    assert chip["state"] == "accommodative"


def test_real_rate_chip_none_input_state_null_plus_warning():
    chip, warning = macro.real_rate_chip(None, 2.0, None)
    assert chip["state"] is None
    assert warning is not None
    chip2, warning2 = macro.real_rate_chip(4.0, None, None)
    assert chip2["state"] is None
    assert warning2 is not None


# --------------------------------------------------------------------------- liquidity_chip


def test_liquidity_chip_contracting():
    chip, warning = macro.liquidity_chip(7100000, 7228000, "2026-07-09")
    # (7100000-7228000)/7228000*100 = -1.7709...
    assert chip["value"] == pytest.approx(-1.7709, abs=1e-3)
    assert chip["state"] == "contracting"
    assert warning is None


def test_liquidity_chip_boundary_plus1pct_is_flat_inclusive():
    past = 1000000.0
    latest = past * 1.01  # exactly +1.0%
    chip, _ = macro.liquidity_chip(latest, past, "2026-07-09")
    assert chip["value"] == pytest.approx(1.0)
    assert chip["state"] == "flat"


def test_liquidity_chip_just_above_plus1pct_is_expanding():
    past = 1000000.0
    latest = past * 1.0101  # +1.01%
    chip, _ = macro.liquidity_chip(latest, past, "2026-07-09")
    assert chip["state"] == "expanding"


def test_liquidity_chip_none_input_state_null_plus_warning():
    chip, warning = macro.liquidity_chip(None, 7228000, None)
    assert chip["state"] is None
    assert warning is not None


# --------------------------------------------------------------------------- vix_chip


@pytest.mark.parametrize("value,expected", [
    (12, "complacent"),
    (14.99, "complacent"),
    (15, "normal"),
    (19.99, "normal"),
    (20, "elevated"),
    (29.99, "elevated"),
    (30, "stressed"),
    (50, "stressed"),
])
def test_vix_chip_thresholds(value, expected):
    chip, warning = macro.vix_chip(value, "2026-07-11")
    assert chip["state"] == expected
    assert warning is None


def test_vix_chip_none_input_state_null_plus_warning():
    chip, warning = macro.vix_chip(None, None)
    assert chip["state"] is None
    assert warning is not None


# --------------------------------------------------------------------------- build_headline


def _chip(key, label, state):
    return {"key": key, "label": label, "state": state, "value": None,
            "value_label": None, "basis": "", "rule": "", "as_of": None}


def test_build_headline_all_neutral_no_stress_signals():
    chips_by_key = {
        "curve": _chip("curve", "10Y–2Y Curve", "normal"),
        "real_rate": _chip("real_rate", "Real Rate (10Y − CPI YoY)", "neutral"),
        "liquidity": _chip("liquidity", "Fed Balance Sheet", "flat"),
        "vix": _chip("vix", "VIX", "normal"),
    }
    assert macro.build_headline(chips_by_key) == "No macro stress signals"


def test_build_headline_only_curve_inverted_no_trailing_separator():
    chips_by_key = {
        "curve": _chip("curve", "10Y–2Y Curve", "inverted"),
        "real_rate": _chip("real_rate", "Real Rate (10Y − CPI YoY)", "neutral"),
        "liquidity": _chip("liquidity", "Fed Balance Sheet", "flat"),
        "vix": _chip("vix", "VIX", "normal"),
    }
    headline = macro.build_headline(chips_by_key)
    assert headline == "10Y–2Y Curve inverted"
    assert not headline.endswith("·")


def test_build_headline_all_non_neutral_fixed_priority_order_regardless_of_dict_order():
    # Shuffled insertion order — output must still follow curve/real_rate/liquidity/vix.
    chips_by_key = {
        "vix": _chip("vix", "VIX", "stressed"),
        "liquidity": _chip("liquidity", "Fed Balance Sheet", "contracting"),
        "curve": _chip("curve", "10Y–2Y Curve", "inverted"),
        "real_rate": _chip("real_rate", "Real Rate (10Y − CPI YoY)", "restrictive"),
    }
    headline = macro.build_headline(chips_by_key)
    idx_curve = headline.index("10Y–2Y Curve")
    idx_rr = headline.index("Real Rate")
    idx_liq = headline.index("Fed Balance Sheet")
    idx_vix = headline.index("VIX")
    assert idx_curve < idx_rr < idx_liq < idx_vix


def test_build_headline_vix_complacent_alone_is_not_a_stress_flag():
    chips_by_key = {
        "curve": _chip("curve", "10Y–2Y Curve", "normal"),
        "real_rate": _chip("real_rate", "Real Rate (10Y − CPI YoY)", "neutral"),
        "liquidity": _chip("liquidity", "Fed Balance Sheet", "flat"),
        "vix": _chip("vix", "VIX", "complacent"),
    }
    assert macro.build_headline(chips_by_key) == "No macro stress signals"


# --------------------------------------------------------------------------- build_series_payload


def _daily_rows(n=400, start="2025-06-10", base=100.0, step=0.01):
    d0 = datetime.date.fromisoformat(start)
    return [_row((d0 + datetime.timedelta(days=i)).isoformat(), base + i * step)
            for i in range(n)]


_META_LEVEL = {
    "symbol": "10Y", "display_name": "10-Year Treasury Yield", "group": "RATES",
    "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
    "transform": "level", "history_window_days": 365,
}


def test_build_series_payload_level_transform_hand_checked():
    rows = _daily_rows(n=400)
    payload = macro.build_series_payload("DGS10", rows, _META_LEVEL, "2026-07-14T12:00:03Z",
                                          "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10")
    last_row, prev_row = rows[-1], rows[-2]
    assert payload["last"] == pytest.approx(last_row["value"])
    assert payload["previous"] == pytest.approx(prev_row["value"])
    assert payload["change_abs"] == pytest.approx(last_row["value"] - prev_row["value"])
    assert payload["change_pct"] == pytest.approx(
        (last_row["value"] - prev_row["value"]) / prev_row["value"] * 100)
    assert payload["as_of"] == last_row["date"]
    assert len(payload["sparkline"]) <= 60
    # change_1y_pct computed against nearest ~365d-back row (within tolerance)
    assert payload["value_1y_ago"] is not None
    assert payload["change_1y_pct"] == pytest.approx(
        (payload["last"] - payload["value_1y_ago"]) / payload["value_1y_ago"] * 100)
    assert payload["series_id"] == "DGS10"
    assert payload["symbol"] == "10Y"
    assert payload["retrieved_at"] == "2026-07-14T12:00:03Z"
    assert payload["source"] == "fred"
    assert payload["source_class"] == "api"
    assert payload["warnings"] == []


def test_build_series_payload_too_short_history_null_change_1y_plus_warning():
    rows = _daily_rows(n=30)  # far short of 365d back
    payload = macro.build_series_payload("DGS10", rows, _META_LEVEL, "2026-07-14T12:00:03Z",
                                          "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10")
    assert payload["value_1y_ago"] is None
    assert payload["change_1y_pct"] is None
    assert any("value_1y_ago" in w for w in payload["warnings"])


# --------------------------------------------------------------------------- SERIES_META


def test_series_meta_has_exactly_the_final_eight_series_in_order():
    assert list(macro.SERIES_META.keys()) == [
        "DGS2", "DGS10", "DFF", "T10Y2Y", "CPIAUCSL", "WALCL", "VIXCLS", "APU000072610",
    ]
    for sid, meta in macro.SERIES_META.items():
        assert meta["group"] in ("RATES", "INFLATION", "LIQUIDITY_VOL", "ENERGY")
        assert meta["transform"] in ("level", "yoy_pct")
        assert meta["history_window_days"] in (365, 1825)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
