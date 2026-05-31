"""RED tests for batch assembly (references/data-schema.md batch metadata)."""
from aiinvest import report


RECORDS = [
    {"symbol": "NVDA", "ticker": "NASDAQ:NVDA", "metrics": {}},
    {"symbol": "VST", "ticker": "NYSE:VST", "metrics": {}},
]
REQUESTED = ["NASDAQ:NVDA", "NYSE:VST", "NASDAQ:MU"]  # MU requested but no row came back


def test_assemble_tags_each_record_with_stack_layer():
    batch = report.assemble_batch(RECORDS, REQUESTED, "2026-05-30T14:00:00Z")
    assert batch["financial_data"]["NVDA"]["stack_layer"] == "L1-chips"
    assert batch["financial_data"]["VST"]["stack_layer"] == "L0-energy"


def test_assemble_keys_financial_data_by_symbol():
    batch = report.assemble_batch(RECORDS, REQUESTED, "t")
    assert set(batch["financial_data"].keys()) == {"NVDA", "VST"}


def test_assemble_metadata_counts_and_failures():
    batch = report.assemble_batch(RECORDS, REQUESTED, "2026-05-30T14:00:00Z")
    md = batch["batch_metadata"]
    assert md["total_symbols_requested"] == 3
    assert md["successful_symbols"] == 2
    assert md["failed_symbols"] == ["NASDAQ:MU"]
    assert md["retrieval_mode"] == "rest"
    assert md["providers_used"] == ["tradingview"]
    assert md["batch_timestamp"] == "2026-05-30T14:00:00Z"
