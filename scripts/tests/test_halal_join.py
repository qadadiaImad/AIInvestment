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


# --- Regression tests: reviewed defects -------------------------------------

def test_business_line_paren_and_empty_basis():
    # FINDING 1: the trailing rstrip(" ()") ate the legitimate closing paren
    # whenever basis was non-empty (e.g. WULF rendered "...(Q1-2026 revenue mix").
    verdicts, _ = load_halal(FIX, now=NOW)
    card = screen_card_data(verdicts, "WULF")
    assert card["business_line"] == (
        "Business activity: crypto-mining — 38.2% impermissible (Q1-2026 revenue mix)"
    )
    # empty basis: no parens should be appended at all (no dangling "(" either)
    verdicts2 = json.loads(json.dumps(verdicts))
    verdicts2["WULF"]["business"]["impermissible_revenue_pct"]["basis"] = ""
    card2 = screen_card_data(verdicts2, "WULF")
    assert card2["business_line"] == "Business activity: crypto-mining — 38.2% impermissible"


def test_row_ignores_none_margin_and_falls_back_when_all_none():
    # FINDING 2: real engine output includes tests with status "unknown" and
    # margin: None. min(tests, key=lambda t: t.get("margin", 0)) raises
    # TypeError (float vs NoneType) since the key IS present, just None.
    verdicts_mixed = {
        "TEST1": {
            "overall": "questionable",
            "standards": {
                "AAOIFI": {
                    "status": "pass",
                    "tests": [
                        {"id": "debt_mcap", "label": "debt / market cap",
                         "ratio": 0.21, "threshold": 0.30, "margin": 0.09, "status": "pass"},
                        {"id": "revenue_test", "label": "revenue screen",
                         "ratio": None, "threshold": None, "margin": None, "status": "unknown"},
                    ],
                }
            },
            "business": {"status": "clean", "categories": [], "impermissible_revenue_pct": None},
            "purification": {"status": "insufficient"},
            "inputs_asof": "",
        }
    }
    card = screen_card_data(verdicts_mixed, "TEST1")
    row = card["standards_rows"][0]
    assert row["binding_label"] == "debt / market cap"
    assert row["ratio"] == "21.0%" and row["threshold"] == "30.0%" and row["margin"] == "+9.0pt"

    verdicts_all_none = {
        "TEST2": {
            "overall": "questionable",
            "standards": {
                "AAOIFI": {
                    "status": "pass",
                    "tests": [
                        {"id": "revenue_test", "label": "revenue screen",
                         "ratio": None, "threshold": None, "margin": None, "status": "unknown"},
                    ],
                }
            },
            "business": {"status": "clean", "categories": [], "impermissible_revenue_pct": None},
            "purification": {"status": "insufficient"},
            "inputs_asof": "",
        }
    }
    card2 = screen_card_data(verdicts_all_none, "TEST2")
    row2 = card2["standards_rows"][0]
    assert row2 == {"name": "AAOIFI", "ok": True, "binding_label": "activity",
                     "ratio": "—", "threshold": "—", "margin": "—"}


def test_stale_boundary_seven_days_one_hour_warns():
    # FINDING 3: (now - ts).days > 7 floors, so 7 days + 1 hour produced no
    # warning though the spec says "> 7 days".
    gen = "2026-07-21T13:07:37Z"
    ts = dt.datetime.fromisoformat(gen.replace("Z", "+00:00"))
    now = ts + dt.timedelta(days=7, hours=1)
    _, warnings = load_halal(FIX, now=now)
    assert any("older than 7 days" in w for w in warnings)
