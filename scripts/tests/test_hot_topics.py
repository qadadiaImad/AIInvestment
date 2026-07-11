from datetime import datetime, timezone
from aiinvest.hot_topics import parse_when, rank_hot, top_themes

NOW = datetime(2026, 7, 7, 18, 0, tzinfo=timezone.utc)

def _art(title, published, tickers, certainty="reported"):
    return {"title": title, "published": published, "tickers": tickers, "certainty": certainty}

ARTICLES = [
    _art("MegaChip reportedly lands huge AI deal", "2026-07-06T10:00:00Z", ["MEGA"]),
    _art("MegaChip upgraded after deal news", "2026-07-05T09:00:00Z", ["MEGA"]),
    _art("MegaChip capacity expansion detailed", "2026-07-01T09:00:00Z", ["MEGA"]),
    _art("QuantumCo launches new system", "2026-06-20T12:00:00Z", ["QNTM"]),
    _art("Old stale story about SleepyCorp", "2026-05-01T12:00:00Z", ["SLPY"]),
    _art("No-ticker macro musing", "2026-07-06T08:00:00Z", []),
]

TRADES = [
    {"politician": "Jane Doe", "ticker": "QNTM", "txn_type": "P", "txn_date": "06/25/2026",
     "filing_date": "6/30/2026", "amount_range_low": 1000001, "amount_range_high": 5000000},
    {"politician": "John Roe", "ticker": "MEGA", "txn_type": "S", "txn_date": "01/10/2026",
     "filing_date": "2/1/2026", "amount_range_low": 1001, "amount_range_high": 15000},  # out of window
]

ROWS = {"MEGA": {"perf_1y": 120.0, "layer": "L1-chips"},
        "QNTM": {"perf_1y": -10.0, "layer": "Q1-hardware"},
        "SLPY": {"perf_1y": 5.0, "layer": "L5-application"}}

def test_parse_when_handles_iso_and_us_dates():
    assert parse_when("2026-07-06T10:00:00Z").day == 6
    assert parse_when("6/30/2026").month == 6
    assert parse_when(None) is None
    assert parse_when("garbage") is None

def test_rank_hot_window_and_ordering():
    ranked = rank_hot(ARTICLES, TRADES, ROWS, days=30, now=NOW, top=10)
    tickers = [r["ticker"] for r in ranked]
    assert "SLPY" not in tickers                 # only article is older than 30 days
    assert tickers[0] == "MEGA"                  # most articles, big perf multiplier
    assert "QNTM" in tickers                     # 1 article + material in-window filing
    mega = ranked[0]
    assert mega["n_articles"] == 3
    assert mega["top_headline"] == "MegaChip reportedly lands huge AI deal"
    assert mega["congress"] is None              # MEGA filing is out of window
    qntm = next(r for r in ranked if r["ticker"] == "QNTM")
    assert qntm["congress"]["n_filings"] == 1
    assert qntm["congress"]["max_amount_low"] == 1000001
    assert qntm["layer"] == "Q1-hardware"

def test_congress_boost_lifts_score():
    with_c = rank_hot(ARTICLES, TRADES, ROWS, days=30, now=NOW)
    without_c = rank_hot(ARTICLES, [], ROWS, days=30, now=NOW)
    s_with = next(r["score"] for r in with_c if r["ticker"] == "QNTM")
    s_without = next(r["score"] for r in without_c if r["ticker"] == "QNTM")
    assert s_with > s_without

def test_top_themes_extracts_window_keywords():
    themes = top_themes(ARTICLES, days=30, now=NOW, top=5)
    words = [t["term"] for t in themes]
    assert "megachip" in words                   # dominant term in window
    assert "sleepycorp" not in words             # stale article excluded
    assert all(t["count"] >= 1 for t in themes)

def test_rank_survives_missing_fields():
    dirty = [{"title": None, "published": None, "tickers": None},
             {"title": "x", "published": "2026-07-06T00:00:00Z", "tickers": ["ZZZ"]}]
    ranked = rank_hot(dirty, [{}], {}, days=30, now=NOW)
    assert [r["ticker"] for r in ranked] == ["ZZZ"]
