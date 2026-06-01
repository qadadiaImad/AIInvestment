"""TDD tests for fed_path.py — PURE math only (no network).

Network functions (fetch_zq_quotes, fetch_sep_dots, build_fed_path) are thin wrappers
and are excluded from unit tests per repo convention (they live in the module but are
not tested here to avoid network calls in CI). All PURE functions are covered below.

Educational/research only — not investment advice.
"""
from __future__ import annotations

import datetime
import pytest
from aiinvest import fed_path


# ---------------------------------------------------------------------------
# FOMC_2026 calendar
# ---------------------------------------------------------------------------

def test_fomc_2026_has_eight_meetings():
    assert len(fed_path.FOMC_2026) == 8


def test_fomc_2026_meeting_keys():
    first = fed_path.FOMC_2026[0]
    assert "date" in first
    assert "is_sep" in first


def test_fomc_2026_first_meeting_is_jan():
    first = fed_path.FOMC_2026[0]
    assert first["date"].month == 1


def test_fomc_2026_has_exactly_four_sep_meetings():
    sep_count = sum(1 for m in fed_path.FOMC_2026 if m["is_sep"])
    assert sep_count == 4


def test_fomc_2026_sep_meetings_are_mar_jun_sep_dec():
    sep_months = {m["date"].month for m in fed_path.FOMC_2026 if m["is_sep"]}
    assert sep_months == {3, 6, 9, 12}


def test_fomc_2026_dates_are_datetime_date():
    for m in fed_path.FOMC_2026:
        assert isinstance(m["date"], datetime.date)


def test_fomc_2026_dates_are_in_2026():
    for m in fed_path.FOMC_2026:
        assert m["date"].year == 2026


def test_fomc_2026_dates_are_ordered():
    dates = [m["date"] for m in fed_path.FOMC_2026]
    assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# implied_path_from_quotes() — PURE day-weighted rate path
# ---------------------------------------------------------------------------
# Fixture: simple two-month scenario (Jan + Feb 2026).
# Jan 2026 FOMC = 2026-01-29; Feb has no FOMC meeting (not a meeting month in 2026).
# We supply ZQ prices for two contract months to verify the day-weighting.

# ZQ contract months used in tests
# ZQF26 = Jan 2026  (settlement mid-Jan but convention maps to whole-month rate)
# ZQG26 = Feb 2026  (no FOMC meeting in Feb — used to interpolate March)
# ZQH26 = Mar 2026  (FOMC 2026-03-18, SEP meeting)

# Rate rule:  implied_rate(month) = 100 - price
# For a meeting month, the day-weighting formula is:
#   avg_rate = (days_before_meeting / days_in_month) * prior_rate
#            + (days_from_meeting_to_eom / days_in_month) * meeting_rate
#
# => meeting_rate = (avg_rate * days_in_month - days_before_meeting * prior_rate)
#                  / days_from_meeting_to_eom
#
# where days_before_meeting = meeting_day - 1
#       days_from_meeting_to_eom = days_in_month - meeting_day + 1
#
# For a non-meeting month, the whole-month implied rate is taken as-is.


def _days_in_month(year, month):
    """Return number of calendar days in month."""
    import calendar
    return calendar.monthrange(year, month)[1]


class TestImpliedPathFromQuotes:

    # -----------------------------------------------------------------------
    # Basic happy-path: two contracts, one meeting month
    # -----------------------------------------------------------------------

    def test_returns_dict_with_meeting_date_keys(self):
        # Jan 2026 FOMC: 2026-01-29 (last meeting day of a 2-day meeting)
        # Price 95.64 => implied rate = 4.36%
        quotes = {(2026, 1): 95.64}
        path = fed_path.implied_path_from_quotes(quotes)
        assert isinstance(path, dict)
        # Key should be a datetime.date corresponding to the Jan meeting
        assert datetime.date(2026, 1, 29) in path

    def test_meeting_date_rate_equals_day_weighted_extraction(self):
        """
        Verify the actual day-weighting math for Jan-2026.

        Jan 2026 has 31 days. FOMC date = 29th.
        days_before = 28 (days 1-28 carry prior rate)
        days_from   = 3  (days 29-31 carry new rate)

        avg_rate (from futures) = 100 - 95.64 = 4.36
        We need a prior rate (Dec-2025 rate before Jan meeting).
        If prior_rate is supplied as 4.50 (the DFF before the meeting):
          new_rate = (4.36*31 - 28*4.50) / 3 = (135.16 - 126.00) / 3 = 3.053...
        """
        quotes = {(2026, 1): 95.64}
        prior_rate = 4.50  # rate in effect entering the meeting month
        path = fed_path.implied_path_from_quotes(quotes, prior_rate=prior_rate)
        expected = (4.36 * 31 - 28 * 4.50) / 3
        assert abs(path[datetime.date(2026, 1, 29)] - expected) < 1e-9

    def test_no_meeting_month_returns_whole_month_rate(self):
        """
        Feb 2026 has no FOMC meeting. The implied rate for a non-meeting month
        is simply 100 - price, returned under the key None or the last day of month.
        Actually per spec: non-meeting months set the inter-meeting rate; they do NOT
        appear as meeting-date keys. Only meeting months produce per-meeting-date keys.
        """
        quotes = {(2026, 2): 95.80}  # Feb — no FOMC
        # implied_path_from_quotes should return no entry for a non-meeting month
        path = fed_path.implied_path_from_quotes(quotes)
        # Feb 2026 has no FOMC meeting, so no key in path for February
        feb_keys = [d for d in path if d.month == 2]
        assert feb_keys == []

    def test_march_meeting_uses_feb_implied_as_prior(self):
        """
        Mar-2026 FOMC = 2026-03-18.
        Supply Feb (non-meeting) and Mar quotes.
        prior_rate for Mar = implied_rate(Feb) = 100 - price_feb.

        Mar has 31 days. Meeting day = 18.
        days_before = 17, days_from = 14.
        prior_rate = 100 - price_feb
        avg_rate_mar = 100 - price_mar
        expected = (avg_rate_mar*31 - 17*(100-price_feb)) / 14
        """
        price_feb = 95.80
        price_mar = 95.72
        quotes = {(2026, 2): price_feb, (2026, 3): price_mar}
        path = fed_path.implied_path_from_quotes(quotes)
        prior = 100 - price_feb
        avg_mar = 100 - price_mar
        expected = (avg_mar * 31 - 17 * prior) / 14
        assert abs(path[datetime.date(2026, 3, 18)] - expected) < 1e-9

    def test_empty_quotes_returns_empty_dict(self):
        path = fed_path.implied_path_from_quotes({})
        assert path == {}

    def test_all_fomc_meeting_months_produce_keys(self):
        """
        If all 8 FOMC-meeting months of 2026 are supplied, we get 8 keys.
        Meeting months in 2026: Jan, Mar, Apr, Jun, Jul, Sep, Nov, Dec.
        """
        meeting_months = [1, 3, 4, 6, 7, 9, 11, 12]
        quotes = {(2026, m): 95.50 for m in meeting_months}
        # Also need non-meeting months for proper prior chaining, but a minimal
        # fixture with only meeting months should still produce 8 keys.
        path = fed_path.implied_path_from_quotes(quotes, prior_rate=4.50)
        assert len(path) == 8

    def test_implied_rate_100_minus_price(self):
        """Spot-check: price 96.36 => implied rate 3.64."""
        quotes = {(2026, 1): 96.36}
        path = fed_path.implied_path_from_quotes(quotes, prior_rate=3.64)
        # When avg_rate == prior_rate (flat), day-weighting gives the same rate.
        # avg = 100 - 96.36 = 3.64; prior = 3.64 => new_rate = 3.64
        jan_rate = path[datetime.date(2026, 1, 29)]
        assert abs(jan_rate - 3.64) < 1e-9

    def test_rate_is_float(self):
        quotes = {(2026, 1): 95.64}
        path = fed_path.implied_path_from_quotes(quotes, prior_rate=4.50)
        for v in path.values():
            assert isinstance(v, float)


# ---------------------------------------------------------------------------
# scenarios() — base / bull / bear
# ---------------------------------------------------------------------------

class TestScenarios:

    BASE = {
        datetime.date(2026, 1, 29): 4.50,
        datetime.date(2026, 3, 18): 4.25,
        datetime.date(2026, 4, 29): 4.25,  # hold priced
        datetime.date(2026, 6, 17): 4.00,
        datetime.date(2026, 7, 29): 4.00,  # hold priced
    }

    def test_scenarios_returns_three_keys(self):
        s = fed_path.scenarios(self.BASE)
        assert set(s.keys()) == {"base", "bull", "bear"}

    def test_base_scenario_equals_input_path(self):
        s = fed_path.scenarios(self.BASE)
        assert s["base"] == self.BASE

    def test_bull_is_minus_25bps_at_next_hold_meeting(self):
        """
        Next hold-priced meeting = first meeting where rate == previous meeting rate.
        In BASE: Apr-29 (4.25 == Mar-18 4.25). Bull applies -25bps from that meeting
        onward.
        """
        s = fed_path.scenarios(self.BASE)
        bull = s["bull"]
        # Apr-29 and beyond should be 25bps lower than base
        pivot = datetime.date(2026, 4, 29)
        for d, v in bull.items():
            if d >= pivot:
                assert abs(v - (self.BASE[d] - 0.25)) < 1e-9
            else:
                assert v == self.BASE[d]

    def test_bear_is_plus_25bps_at_next_hold_meeting(self):
        """Bear: +25bps from next hold-priced meeting onward."""
        s = fed_path.scenarios(self.BASE)
        bear = s["bear"]
        pivot = datetime.date(2026, 4, 29)
        for d, v in bear.items():
            if d >= pivot:
                assert abs(v - (self.BASE[d] + 0.25)) < 1e-9
            else:
                assert v == self.BASE[d]

    def test_all_cuts_path_no_hold_meeting_uses_last_meeting(self):
        """If no hold meeting found, apply shift to last meeting only."""
        all_cuts = {
            datetime.date(2026, 1, 29): 4.50,
            datetime.date(2026, 3, 18): 4.25,
            datetime.date(2026, 4, 29): 4.00,
        }
        s = fed_path.scenarios(all_cuts)
        # Bull: -25bps at last meeting (Apr-29)
        assert abs(s["bull"][datetime.date(2026, 4, 29)] - 3.75) < 1e-9
        # Bear: +25bps at last meeting
        assert abs(s["bear"][datetime.date(2026, 4, 29)] - 4.25) < 1e-9

    def test_empty_path_returns_empty_scenarios(self):
        s = fed_path.scenarios({})
        assert s == {"base": {}, "bull": {}, "bear": {}}

    def test_base_scenario_is_not_mutated_copy(self):
        """scenarios() must not mutate the input dict."""
        original = dict(self.BASE)
        fed_path.scenarios(self.BASE)
        assert self.BASE == original

    def test_bull_bear_all_float_values(self):
        s = fed_path.scenarios(self.BASE)
        for scenario in ("bull", "bear"):
            for v in s[scenario].values():
                assert isinstance(v, float)


# ---------------------------------------------------------------------------
# Day-weighting edge cases
# ---------------------------------------------------------------------------

class TestDayWeightingEdgeCases:

    def test_meeting_on_first_day_of_month(self):
        """
        If an FOMC meeting were on day 1 (days_before=0), the new rate is the
        whole-month rate (avg = new_rate, no prior influence).
        This cannot happen in 2026 but the math must not divide by zero or error.
        We test with a synthetic meeting date injected via _day_weighted_rate.
        """
        # Call the pure helper directly
        avg_rate = 3.64
        prior_rate = 4.50
        meeting_day = 1
        days_in_month = 31
        result = fed_path._day_weighted_rate(avg_rate, prior_rate,
                                             meeting_day, days_in_month)
        # days_before = 0, days_from = 31
        # expected = (3.64*31 - 0*4.50) / 31 = 3.64
        assert abs(result - avg_rate) < 1e-9

    def test_meeting_on_last_day_of_month(self):
        """
        Meeting on last day: days_from = 1. New rate absorbs almost nothing of month.
        days_before = days_in_month - 1 = 30, days_from = 1.
        expected = avg*31 - 30*prior  (entire month worth of impact)
        """
        avg_rate = 3.64
        prior_rate = 4.00
        days_in_month = 31
        meeting_day = 31
        result = fed_path._day_weighted_rate(avg_rate, prior_rate,
                                             meeting_day, days_in_month)
        expected = (avg_rate * days_in_month - (days_in_month - 1) * prior_rate)
        assert abs(result - expected) < 1e-9

    def test_day_weighted_rate_symmetric_check(self):
        """
        When prior_rate == new_rate (flat), avg must equal that rate regardless of
        meeting day. Verify by round-tripping: set avg from known new_rate, check.
        """
        prior_rate = 3.64
        new_rate = 3.64
        meeting_day = 18
        days_in_month = 31
        # avg = (days_before * prior + days_from * new) / total
        days_before = meeting_day - 1  # 17
        days_from = days_in_month - meeting_day + 1  # 14
        avg = (days_before * prior_rate + days_from * new_rate) / days_in_month
        result = fed_path._day_weighted_rate(avg, prior_rate, meeting_day, days_in_month)
        assert abs(result - new_rate) < 1e-9
