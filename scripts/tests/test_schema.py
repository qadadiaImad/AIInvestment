"""RED tests for the data-schema helpers (references/data-schema.md)."""
from aiinvest import schema


# --- clean(): reject dirty sentinels GuruTrade let through ---

def test_clean_passes_through_a_real_value():
    assert schema.clean("32.33") == "32.33"


def test_clean_strips_whitespace():
    assert schema.clean("  Overvalued  ") == "Overvalued"


def test_clean_rejects_lone_dot():
    # GuruTrade's regex emitted current_ratio: "." — must become None
    assert schema.clean(".") is None


def test_clean_rejects_empty_and_na_and_dash():
    assert schema.clean("") is None
    assert schema.clean("N/A") is None
    assert schema.clean("--") is None
    assert schema.clean(None) is None


# --- parse_number(): handle commas, currency, percent, magnitude suffixes ---

def test_parse_number_plain_float():
    assert schema.parse_number("32.33") == 32.33


def test_parse_number_strips_commas_and_dollar():
    assert schema.parse_number("$5,109,587,985,229.0") == 5109587985229.0


def test_parse_number_percent_returns_bare_number():
    assert schema.parse_number("75%") == 75.0


def test_parse_number_magnitude_suffix_trillion():
    assert schema.parse_number("5.11T") == 5.11e12


def test_parse_number_returns_none_for_dirty():
    assert schema.parse_number(".") is None
    assert schema.parse_number("N/A") is None
    assert schema.parse_number(None) is None


# --- make_envelope(): stamped wrapper, infers dirty flag ---

def test_make_envelope_wraps_value_with_provenance():
    env = schema.make_envelope(
        value=32.33, raw="32.33", unit="ratio", source="tradingview",
        source_url="https://scanner.tradingview.com/america/scan",
        source_class="api", retrieved_at="2026-05-30T14:00:00Z",
    )
    assert env["value"] == 32.33
    assert env["raw"] == "32.33"
    assert env["unit"] == "ratio"
    assert env["source"] == "tradingview"
    assert env["source_class"] == "api"
    assert env["retrieved_at"] == "2026-05-30T14:00:00Z"
    assert env["dirty"] is False


def test_make_envelope_marks_dirty_when_raw_present_but_value_none():
    env = schema.make_envelope(
        value=None, raw=".", unit="ratio", source="gurufocus",
        source_url="x", source_class="innertext-regex", retrieved_at="t",
    )
    assert env["dirty"] is True


def test_make_envelope_not_dirty_when_value_and_raw_both_absent():
    # Field genuinely not reported (not an extraction failure) -> not dirty.
    env = schema.make_envelope(
        value=None, raw=None, unit="usd", source="tradingview",
        source_url="x", source_class="api", retrieved_at="t",
    )
    assert env["dirty"] is False
