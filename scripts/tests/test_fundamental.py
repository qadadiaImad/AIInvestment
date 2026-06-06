"""RED tests for fundamental-value valuation logic (our own, generic — no GF wording)."""
from aiinvest import fundamental as fv


def test_undervalued_when_price_well_below_value():
    assert fv.valuation_tag(211.14, 334.32) == "Undervalued"


def test_overvalued_when_price_well_above_value():
    assert fv.valuation_tag(334.0, 300.0) == "Overvalued"


def test_fairly_valued_within_band():
    assert fv.valuation_tag(100.0, 100.0) == "Fairly Valued"
    assert fv.valuation_tag(105.0, 100.0) == "Fairly Valued"   # +5% within 10% band


def test_tag_none_on_bad_inputs():
    assert fv.valuation_tag(None, 100) is None
    assert fv.valuation_tag(100, None) is None
    assert fv.valuation_tag(100, 0) is None


def test_discount_pct_value_vs_price():
    assert fv.discount_pct(211.14, 334.32) == 36.8   # (334.32-211.14)/334.32*100


def test_discount_pct_none_on_bad_inputs():
    assert fv.discount_pct(100, None) is None
    assert fv.discount_pct(100, 0) is None


# --- parse_valuation_chart: the JSON valuation-chart endpoint ---

CHART = {
    "gf_value": 334.32, "iv": 334.32, "ms": 36.84,
    "medps": [["2024-01-31", 74.3], ["2025-01-31", 160.01], ["2026-04-30", 315.34],
              ["2029-01-01", None]],
    "price": [["2025-05-30", 135.13], ["2026-05-30", 211.14]],
}


def test_parse_chart_pulls_value_and_margin_of_safety():
    r = fv.parse_valuation_chart(CHART)
    assert r["fundamental_value"] == 334.32
    assert r["margin_of_safety_pct"] == 36.84


def test_parse_chart_fundamental_series_skips_nulls():
    r = fv.parse_valuation_chart(CHART)
    assert r["fundamental_value_series"] == [
        {"date": "2024-01-31", "value": 74.3},
        {"date": "2025-01-31", "value": 160.01},
        {"date": "2026-04-30", "value": 315.34},
    ]


def test_parse_chart_price_series():
    r = fv.parse_valuation_chart(CHART)
    assert r["price_series"][-1] == {"date": "2026-05-30", "value": 211.14}


def test_parse_chart_empty_is_safe():
    r = fv.parse_valuation_chart({})
    assert r["fundamental_value"] is None
    assert r["fundamental_value_series"] == []


def test_parse_chart_zero_value_is_treated_as_missing():
    # the source returns gf_value 0 when it has no value (recent IPO/ETF) — never a real value
    r = fv.parse_valuation_chart({"gf_value": 0, "iv": 0, "ms": None, "medps": None})
    assert r["fundamental_value"] is None
