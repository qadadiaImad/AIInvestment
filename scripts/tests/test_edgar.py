"""RED tests for the SEC EDGAR REST helper (pure logic)."""
from aiinvest import edgar


# --- pad_cik(): EDGAR endpoints need a 10-digit zero-padded CIK ---

def test_pad_cik_from_int():
    assert edgar.pad_cik(1045810) == "0001045810"


def test_pad_cik_from_string():
    assert edgar.pad_cik("1045810") == "0001045810"


def test_pad_cik_already_padded():
    assert edgar.pad_cik("0001045810") == "0001045810"


# --- ticker_to_cik(): map a ticker via company_tickers.json ---

MAPPING = {
    "0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}


def test_ticker_to_cik_is_padded():
    assert edgar.ticker_to_cik("NVDA", MAPPING) == "0001045810"


def test_ticker_to_cik_is_case_insensitive():
    assert edgar.ticker_to_cik("nvda", MAPPING) == "0001045810"


def test_ticker_to_cik_unknown_returns_none():
    assert edgar.ticker_to_cik("ZZZZ", MAPPING) is None


# --- parse_submissions(): columnar "recent" arrays -> list of filing rows ---

SUBMISSIONS = {
    "cik": "1045810", "name": "NVIDIA CORP", "tickers": ["NVDA"],
    "filings": {"recent": {
        "accessionNumber": ["0001045810-24-000029", "0001045810-24-000010"],
        "filingDate": ["2024-02-21", "2024-01-05"],
        "form": ["10-K", "8-K"],
        "primaryDocument": ["nvda-20240128.htm", "ex.htm"],
    }},
}


def test_parse_submissions_returns_row_per_filing():
    rows = edgar.parse_submissions(SUBMISSIONS)
    assert len(rows) == 2
    assert rows[0] == {
        "accession": "0001045810-24-000029",
        "filing_date": "2024-02-21",
        "form": "10-K",
        "primary_document": "nvda-20240128.htm",
    }


def test_filter_filings_by_form():
    rows = edgar.parse_submissions(SUBMISSIONS)
    tenk = edgar.filter_filings(rows, {"10-K", "S-1"})
    assert len(tenk) == 1
    assert tenk[0]["form"] == "10-K"


# --- filing_url(): build the public Archives URL for a filing ---

def test_filing_url_strips_dashes_and_uses_int_cik():
    url = edgar.filing_url("0001045810", "0001045810-24-000029", "nvda-20240128.htm")
    assert url == ("https://www.sec.gov/Archives/edgar/data/1045810/"
                   "000104581024000029/nvda-20240128.htm")
