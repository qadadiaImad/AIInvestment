"""XBRL extraction: pure parsing over a companyfacts-shaped fixture. No network."""
from aiinvest import xbrl

FACTS = {"cik": 320193, "facts": {"us-gaap": {
    "InvestmentIncomeInterest": {"units": {"USD": [
        {"end": "2024-09-28", "val": 3750000000, "fy": 2024, "fp": "FY", "form": "10-K", "accn": "0000320193-24-000123"},
        {"end": "2025-06-28", "val": 900000000, "fy": 2025, "fp": "Q3", "form": "10-Q", "accn": "0000320193-25-000077"},
        {"end": "2025-09-27", "val": 4100000000, "fy": 2025, "fp": "FY", "form": "10-K", "accn": "0000320193-25-000123"}]}},
    "AccountsReceivableNetCurrent": {"units": {"USD": [
        {"end": "2025-09-27", "val": 33410000000, "fy": 2025, "fp": "FY", "form": "10-K", "accn": "0000320193-25-000123"}]}},
}}}


def test_extract_picks_latest_annual_facts():
    out = xbrl.extract_facts(FACTS)
    assert out["interest_income"]["value"] == 4100000000
    assert out["interest_income"]["fy"] == 2025
    assert out["interest_income"]["tag"] == "InvestmentIncomeInterest"
    assert out["receivables"]["value"] == 33410000000
    assert out["interest_expense"] is None


def test_extract_bank_fallback_tag():
    bank = {"facts": {"us-gaap": {"InterestAndDividendIncomeOperating": {"units": {"USD": [
        {"end": "2025-12-31", "val": 9.9e10, "fy": 2025, "fp": "FY", "form": "10-K", "accn": "a"}]}}}}}
    out = xbrl.extract_facts(bank)
    assert out["interest_income"]["tag"] == "InterestAndDividendIncomeOperating"


def test_extract_empty_gives_all_none():
    out = xbrl.extract_facts({"facts": {}})
    assert out == {"interest_income": None, "interest_expense": None, "receivables": None}


def test_cik_for_pads_to_ten_digits():
    mapping = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
    assert xbrl.cik_for("AAPL", mapping) == "0000320193"
    assert xbrl.cik_for("ZZZZ", mapping) is None
