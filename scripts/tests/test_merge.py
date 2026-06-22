"""RED tests for cross-source merge + freshness flagging (Rule #1)."""
from aiinvest import merge


# --- cross_check(): do numeric values from different sources agree? ---

def test_cross_check_agrees_within_tolerance():
    assert merge.cross_check([211.14, 211.14]) is True


def test_cross_check_flags_disagreement():
    assert merge.cross_check([211.14, 250.0]) is False


def test_cross_check_ignores_none():
    assert merge.cross_check([None, 211.14, None]) is True


# --- is_stale(): freshness flag for Rule #1 ("verify live") ---

def test_is_stale_true_when_older_than_max_age():
    assert merge.is_stale("2026-05-29T00:00:00Z", "2026-05-30T12:00:00Z", max_age_hours=24) is True


def test_is_stale_false_when_fresh():
    assert merge.is_stale("2026-05-30T10:00:00Z", "2026-05-30T12:00:00Z", max_age_hours=24) is False


# --- merge_symbol(): combine per-source records into one cross-validated record ---

YAHOO = {"metrics": {"current_price": {"value": 211.14, "retrieved_at": "2026-05-30T12:00:00Z"}}}
TV = {"metrics": {"current_price": {"value": 211.14, "retrieved_at": "2026-05-30T12:00:00Z"}}}
GURU = {"metrics": {"gf_value": {"value": 334.32, "retrieved_at": "2026-05-30T12:00:00Z"}}}


def test_merge_normalizes_price_aliases_across_sources():
    # TradingView calls it "close", Yahoo "current_price", GuruFocus "price" -> one field.
    tv = {"metrics": {"close": {"value": 211.14, "retrieved_at": "2026-05-30T12:00:00Z"}}}
    yh = {"metrics": {"current_price": {"value": 211.14, "retrieved_at": "2026-05-30T12:00:00Z"}}}
    rec = merge.merge_symbol("NVDA", {"tradingview": tv, "yahoo": yh}, now="2026-05-30T12:30:00Z")
    price = rec["metrics"]["current_price"]
    assert set(price["sources"]) == {"tradingview", "yahoo"}
    assert price["agree"] is True


def test_merge_collects_sources_per_metric():
    rec = merge.merge_symbol("NVDA", {"yahoo": YAHOO, "tradingview": TV, "gurufocus": GURU},
                             now="2026-05-30T12:30:00Z")
    price = rec["metrics"]["current_price"]
    assert price["value"] == 211.14
    assert set(price["sources"]) == {"yahoo", "tradingview"}
    assert price["agree"] is True
    assert price["stale"] is False
    assert rec["metrics"]["gf_value"]["value"] == 334.32
