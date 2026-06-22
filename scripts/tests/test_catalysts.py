"""RED tests for the catalyst calendar (Part D)."""
from aiinvest import catalysts as cal


def test_build_passes_validation():
    cats = cal.build()
    assert cal.validate(cats) == []


def test_ipo_trio_present_by_type():
    cats = cal.build()
    ipos = cal.by_type(cats, "ipo")
    entities = {e for c in ipos for e in c["entities"]}
    assert {"anthropic", "openai", "spacex"}.issubset(entities)


def test_upcoming_is_date_sorted_and_in_window():
    cats = cal.build()
    up = cal.upcoming(cats, now="2026-05-30", horizon_days=220)
    dates = [c["date"] for c in up]
    assert dates == sorted(dates)
    assert all("2026-05-30" <= d for d in dates)


def test_upcoming_excludes_undated_catalysts():
    cats = [
        {"id": "a", "date": "2026-10-01", "type": "ipo", "entities": [], "certainty": "reported",
         "source_class": "x", "source_url": "x", "retrieved_at": "t"},
        {"id": "b", "date": None, "type": "export_control", "entities": [], "certainty": "reported",
         "source_class": "x", "source_url": "x", "retrieved_at": "t"},
    ]
    up = cal.upcoming(cats, now="2026-05-30", horizon_days=365)
    assert [c["id"] for c in up] == ["a"]


def test_by_entity_filters():
    cats = cal.build()
    hits = cal.by_entity(cats, "anthropic")
    assert any(c["type"] == "ipo" for c in hits)


def test_validate_flags_bad_type_and_certainty():
    bad = [{"id": "x", "date": "2026-10-01", "type": "party", "entities": [], "certainty": "fact",
            "source_class": "x", "source_url": "x", "retrieved_at": "t"}]
    issues = cal.validate(bad)
    assert any("type" in i for i in issues)
    assert any("certainty" in i for i in issues)


def test_from_tradingview_earnings_builds_dated_catalysts():
    recs = [{"symbol": "NVDA", "ticker": "NASDAQ:NVDA",
             "metrics": {"earnings_release_next_date": {"value": "2026-08-20"}}}]
    cats = cal.from_tradingview_earnings(recs, "2026-05-30T12:00:00Z")
    assert cats[0]["type"] == "earnings"
    assert cats[0]["entities"] == ["NVDA"]
    assert cats[0]["date"] == "2026-08-20"


def test_from_tradingview_earnings_handles_unix_timestamp():
    # TradingView's scanner returns earnings dates as unix seconds, not ISO strings.
    recs = [{"symbol": "NVDA", "ticker": "NASDAQ:NVDA",
             "metrics": {"earnings_release_next_date": {"value": 1767225600}}}]  # 2026-01-01 UTC
    cats = cal.from_tradingview_earnings(recs, "t")
    assert cats[0]["date"] == "2026-01-01"


def test_from_tradingview_earnings_handles_numeric_string_timestamp():
    # The scanner column is parsed as text, so the unix value arrives as a digit-string.
    recs = [{"symbol": "NVDA", "ticker": "NASDAQ:NVDA",
             "metrics": {"earnings_release_next_date": {"value": "1767225600"}}}]
    cats = cal.from_tradingview_earnings(recs, "t")
    assert cats[0]["date"] == "2026-01-01"
