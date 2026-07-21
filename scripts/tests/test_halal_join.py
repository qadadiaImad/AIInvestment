import datetime as dt
import json
import pathlib
import pytest
from aiinvest.halal_join import HalalDataMissing, load_halal, screen_card_data

FIX = pathlib.Path(__file__).parent / "fixtures" / "halal_fixture.json"
NOW = dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc)

def test_missing_file_raises():
    with pytest.raises(HalalDataMissing):
        load_halal(FIX.parent / "nope.json", now=NOW)

def test_load_fresh_no_warning():
    verdicts, warnings = load_halal(FIX, now=NOW)
    assert "WULF" in verdicts and warnings == []

def test_stale_warns():
    _, warnings = load_halal(FIX, now=NOW + dt.timedelta(days=10))
    assert any("older than 7 days" in w for w in warnings)

def test_card_missing_ticker_is_none():
    verdicts, _ = load_halal(FIX, now=NOW)
    assert screen_card_data(verdicts, "ZZZZ") is None

def test_card_binding_row_and_lines():
    verdicts, _ = load_halal(FIX, now=NOW)
    card = screen_card_data(verdicts, "WULF")
    assert card["overall"] == "questionable"
    assert card["badge"] == {"text": "AAOIFI SCREEN: REVIEW", "color": "#E0A23B"}
    aaoifi = next(r for r in card["standards_rows"] if r["name"] == "AAOIFI")
    assert aaoifi["binding_label"] == "debt / market cap"
    assert aaoifi["ratio"] == "21.0%" and aaoifi["threshold"] == "30.0%" and aaoifi["margin"] == "+9.0pt"
    assert "38.2%" in card["business_line"] and "crypto-mining" in card["business_line"]
    assert card["purification_line"] == "Purification (estimated): ~$0.13/share"
    assert card["inputs_asof"].startswith("2026-07-21")

def test_card_clean_name():
    verdicts, _ = load_halal(FIX, now=NOW)
    card = screen_card_data(verdicts, "GEV")
    assert card["badge"] == {"text": "AAOIFI SCREEN: PASS", "color": "#34D399"}
    assert card["business_line"] == "Business activity: clean"
    assert card["purification_line"] == "Purification (estimated): $0.00/share"
