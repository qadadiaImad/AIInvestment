"""RED tests for the halal pull CLI (pure assembly logic only — no network)."""
import pull_halal


def test_universe_is_ai_plus_quantum_deduped():
    tickers = pull_halal.universe_tickers()
    assert "NASDAQ:NVDA" in tickers and "NYSE:JPM" in tickers
    assert len(tickers) == len(set(tickers))
    assert len(tickers) >= 120           # 108 AI + 20 quantum minus overlaps


def test_assemble_batch_shapes_and_miss_reporting():
    records = [{"symbol": "NVDA", "ticker": "NASDAQ:NVDA", "metrics": {}}]
    batch = pull_halal.assemble_batch(records, ["NASDAQ:NVDA", "NYSE:ZZZ"],
                                      "2026-07-21T14:00:00Z")
    md = batch["batch_metadata"]
    assert md["total_symbols_requested"] == 2
    assert md["successful_symbols"] == 1
    assert md["failed_symbols"] == ["NYSE:ZZZ"]
    assert md["scope"] == "halal"
    assert batch["financial_data"]["NVDA"]["as_of"] == "2026-07-21T14:00:00Z"
