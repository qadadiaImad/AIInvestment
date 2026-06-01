"""RED tests for the House Congress-trading PTR parser (aiinvest.congress).

PURE FUNCTIONS ONLY — no network. Parses already-fetched index bytes/text and
already-extracted PTR PDF text against the real fixtures saved under
tests/fixtures/congress/.

Honesty rails (CLAUDE.md + congress-trading-feasibility spec):
- House PTR amounts are RANGE BUCKETS, never exact -> amount_range_low/high.
- reporting_lag_days = filing_date - transaction_date.
- Scope HOUSE only, TEXT PDFs only; scanned (empty text) flagged + skipped.
- Reject dirty values ('.', '', 'N/A'). Stamp retrieved_at/source/source_class.
"""
import os

import pytest

from aiinvest import congress

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "congress")


def _read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# parse_amount_bucket(label) -> (low, high)
# --------------------------------------------------------------------------

def test_amount_bucket_smallest():
    assert congress.parse_amount_bucket("$1,001 - $15,000") == (1001, 15000)


def test_amount_bucket_mid():
    assert congress.parse_amount_bucket("$100,001 - $250,000") == (100001, 250000)


def test_amount_bucket_millions():
    assert congress.parse_amount_bucket("$1,000,001 - $5,000,000") == (1000001, 5000000)


def test_amount_bucket_open_ended_top_uses_none_high():
    # Top bucket prints with a space: "$50,000,001 +" ; high is open-ended.
    assert congress.parse_amount_bucket("$50,000,001 +") == (50000001, None)


def test_amount_bucket_tolerates_whitespace_and_reflow_join():
    # amount-high frequently wraps; after reflow we may get extra inner spaces.
    assert congress.parse_amount_bucket("$15,001 -   $50,000") == (15001, 50000)


def test_amount_bucket_rejects_garbage():
    for bad in (".", "", "N/A", "$abc - $def", None, "$3 - $4"):
        with pytest.raises((ValueError, TypeError)):
            congress.parse_amount_bucket(bad)


# --------------------------------------------------------------------------
# parse_fd_index(...) + PTR filter
# --------------------------------------------------------------------------

def test_parse_fd_index_txt_row_count_and_fields():
    rows = congress.parse_fd_index(_read("sample_index.txt"))
    # header + 12 data rows in the fixture
    assert len(rows) == 12
    aderholt = next(r for r in rows if r["DocID"] == "20032062")
    assert aderholt["Last"] == "Aderholt"
    assert aderholt["First"] == "Robert B."
    assert aderholt["FilingType"] == "P"
    assert aderholt["StateDst"] == "AL04"
    assert aderholt["FilingDate"] == "9/10/2025"


def test_parse_fd_index_xml_parses_members():
    rows = congress.parse_fd_index(_read("sample_index.xml"))
    docids = {r["DocID"] for r in rows}
    assert "20030316" in docids
    allen = next(r for r in rows if r["DocID"] == "20030316")
    assert allen["Last"] == "Allen"
    assert allen["FilingType"] == "P"
    assert allen["StateDst"] == "GA12"


def test_parse_fd_index_xml_handles_self_closing_prefix_as_none():
    rows = congress.parse_fd_index(_read("sample_index.xml"))
    aaron = next(r for r in rows if r["DocID"] == "40003749")
    # <Prefix /> is empty -> cleaned to None (not the literal empty string)
    assert aaron["Prefix"] is None
    assert aaron["FilingType"] == "D"


def test_filter_ptrs_keeps_only_filing_type_P_txt():
    rows = congress.parse_fd_index(_read("sample_index.txt"))
    ptrs = congress.filter_ptrs(rows)
    assert all(r["FilingType"] == "P" for r in ptrs)
    assert len(ptrs) == 1  # only Aderholt 20032062 is P in the txt fixture
    assert ptrs[0]["DocID"] == "20032062"


def test_filter_ptrs_keeps_only_filing_type_P_xml():
    rows = congress.parse_fd_index(_read("sample_index.xml"))
    ptrs = congress.filter_ptrs(rows)
    assert all(r["FilingType"] == "P" for r in ptrs)
    # xml fixture has 5 P rows (Aderholt + 4 Allen)
    assert len(ptrs) == 5


# --------------------------------------------------------------------------
# parse_ptr_transactions(pdf_text)
# --------------------------------------------------------------------------

def test_ptr_single_clean_transaction_amount_on_one_line():
    # 20032062: one txn, amount fully on one line "$1,001 - $15,000"
    txns = congress.parse_ptr_transactions(_read("sample_ptr_20032062.txt"))
    assert len(txns) == 1
    t = txns[0]
    assert t["ticker"] == "GSK"
    assert t["txn_type"] == "S"
    assert t["txn_date"] == "07/28/2025"
    assert t["amount_label"] == "$1,001 - $15,000"
    assert "GSK plc American Depositary Shares" in t["asset_name"]
    # no dirty values
    assert t["ticker"] not in (".", "", "N/A")


def test_ptr_wrapped_amount_high_reflowed():
    # 20026537: amounts wrap; e.g. "$15,001 -" on one line, "$50,000" on next.
    txns = congress.parse_ptr_transactions(_read("sample_ptr_20026537.txt"))
    assert len(txns) == 4
    rol = next(t for t in txns if t["ticker"] == "ROL")
    assert rol["txn_type"] == "P"
    assert rol["txn_date"] == "12/12/2024"
    assert rol["amount_label"] == "$15,001 - $50,000"
    # a government-security txn with no ticker still parses an amount bucket
    note = next(t for t in txns if "4.375%" in t["asset_name"])
    assert note["amount_label"] == "$100,001 - $250,000"


def test_ptr_treasury_rows_without_ticker_have_none_ticker():
    txns = congress.parse_ptr_transactions(_read("sample_ptr_20026537.txt"))
    gs = [t for t in txns if "TREASU" in t["asset_name"].upper()]
    assert gs, "expected treasury rows"
    assert all(t["ticker"] is None for t in gs)


def test_ptr_owner_codes_and_partial_sale_and_many_txns():
    # 20033458 (Kevin Hern): 15 transactions incl S (partial), P, JT owner.
    txns = congress.parse_ptr_transactions(_read("sample_ptr_20033458.txt"))
    assert len(txns) == 15
    acn = next(t for t in txns if t["ticker"] == "ACN")
    assert acn["txn_type"] == "S"
    assert acn["amount_label"] == "$100,001 - $250,000"
    bsx = next(t for t in txns if t["ticker"] == "BSX")
    assert bsx["txn_type"] == "S (partial)"
    assert bsx["amount_label"] == "$15,001 - $50,000"
    # the $1,000,001-$5,000,000 bucket appears (BNP Paribas + RBC)
    labels = [t["amount_label"] for t in txns]
    assert "$1,000,001 - $5,000,000" in labels
    # tickers present in the doc
    tickers = {t["ticker"] for t in txns}
    for sym in ("ACN", "BSX", "CSX", "ETN", "HD", "MCD", "MSFT", "ORLY", "STX"):
        assert sym in tickers


def test_ptr_no_dirty_values_anywhere():
    txns = congress.parse_ptr_transactions(_read("sample_ptr_20030316.txt"))
    assert txns
    for t in txns:
        assert t["amount_label"] not in (".", "", "N/A", None)
        assert t["txn_type"] not in (".", "", "N/A", None)
        assert t["txn_date"] not in (".", "", "N/A", None)
        # ticker may legitimately be None (treasuries) but never a dirty string
        assert t["ticker"] != "."
        assert t["asset_name"] not in (".", "", "N/A", None)
        # every amount_label must map to a valid bucket
        low, high = congress.parse_amount_bucket(t["amount_label"])
        assert low >= 1001


def test_ptr_empty_text_is_scanned():
    assert congress.is_scanned("") is True
    assert congress.is_scanned("   \n\x00\x00  ") is True
    assert congress.is_scanned(_read("sample_ptr_20032062.txt")) is False


def test_ptr_scanned_returns_empty_list():
    assert congress.parse_ptr_transactions("") == []
    assert congress.parse_ptr_transactions("\x00\x00   \n  ") == []


def test_ptr_strips_nul_bytes_in_title():
    # Title renders as "P\x00\x00 T\x00\x00 R" in real extracts; must not crash
    text = _read("sample_ptr_20032062.txt").replace("P T R", "P\x00\x00 T\x00\x00 R")
    txns = congress.parse_ptr_transactions(text)
    assert len(txns) == 1
    assert txns[0]["ticker"] == "GSK"


# --------------------------------------------------------------------------
# reporting_lag_days(txn_date, filing_date)
# --------------------------------------------------------------------------

def test_reporting_lag_days_basic():
    # GSK txn 07/28/2025, Aderholt index FilingDate 9/10/2025
    assert congress.reporting_lag_days("07/28/2025", "9/10/2025") == 44


def test_reporting_lag_days_same_day_zero():
    assert congress.reporting_lag_days("01/16/2025", "01/16/2025") == 0


def test_reporting_lag_days_accepts_padded_and_unpadded():
    assert congress.reporting_lag_days("4/11/2025", "05/07/2025") == 26


# --------------------------------------------------------------------------
# to_record(...) canonical congress_trade dict
# --------------------------------------------------------------------------

def _aderholt_filing():
    rows = congress.parse_fd_index(_read("sample_index.txt"))
    return next(r for r in rows if r["DocID"] == "20032062")


def test_to_record_shape_and_values():
    filing = _aderholt_filing()
    txn = congress.parse_ptr_transactions(_read("sample_ptr_20032062.txt"))[0]
    url = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20032062.pdf"
    rec = congress.to_record(
        filing, txn, sector="Healthcare",
        retrieved_at="2026-05-31T00:00:00Z", source_url=url,
    )
    assert rec["politician"] == "Robert B. Aderholt"
    assert rec["chamber"] == "House"
    assert rec["state"] == "AL04"
    assert rec["party"] is None
    assert rec["ticker"] == "GSK"
    assert rec["sector"] == "Healthcare"
    assert rec["asset"].startswith("GSK plc")
    assert rec["txn_type"] == "S"
    assert rec["txn_date"] == "07/28/2025"
    assert rec["filing_date"] == "9/10/2025"
    assert rec["reporting_lag_days"] == 44
    assert rec["amount_range_low"] == 1001
    assert rec["amount_range_high"] == 15000
    assert rec["source"] == url
    assert rec["source_class"] == "filing"
    assert rec["retrieved_at"] == "2026-05-31T00:00:00Z"


def test_to_record_open_ended_high_is_none():
    filing = _aderholt_filing()
    txn = {
        "ticker": "XYZ", "asset_name": "Some Asset", "txn_type": "P",
        "txn_date": "01/02/2025", "amount_label": "$50,000,001 +",
    }
    rec = congress.to_record(
        filing, txn, sector=None,
        retrieved_at="2026-05-31T00:00:00Z",
        source_url="https://example/x.pdf",
    )
    assert rec["amount_range_low"] == 50000001
    assert rec["amount_range_high"] is None


def test_to_record_rejects_dirty_txn():
    filing = _aderholt_filing()
    bad = {
        "ticker": ".", "asset_name": "", "txn_type": "S",
        "txn_date": "01/02/2025", "amount_label": "$1,001 - $15,000",
    }
    with pytest.raises(ValueError):
        congress.to_record(
            filing, bad, sector=None,
            retrieved_at="2026-05-31T00:00:00Z",
            source_url="https://example/x.pdf",
        )


def test_to_record_requires_stamp():
    filing = _aderholt_filing()
    txn = congress.parse_ptr_transactions(_read("sample_ptr_20032062.txt"))[0]
    with pytest.raises(ValueError):
        congress.to_record(filing, txn, sector=None, retrieved_at="", source_url="")
