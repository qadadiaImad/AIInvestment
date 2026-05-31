"""Assemble scanner records into the schema's batch envelope (data-schema.md)."""
from __future__ import annotations

from . import ai_stack


def assemble_batch(records, requested_tickers, retrieved_at,
                   retrieval_mode="rest", providers=("tradingview",)):
    """Build the batch dict: tag layers, key by symbol, compute success/failure counts."""
    financial_data = {}
    seen_tickers = set()
    for rec in records:
        seen_tickers.add(rec["ticker"])
        financial_data[rec["symbol"]] = {
            "symbol": rec["symbol"],
            "ticker": rec["ticker"],
            "stack_layer": ai_stack.layer_of(rec["ticker"]),
            "as_of": retrieved_at,
            "metrics": rec["metrics"],
        }
    failed = [t for t in requested_tickers if t not in seen_tickers]
    return {
        "batch_metadata": {
            "batch_timestamp": retrieved_at,
            "total_symbols_requested": len(requested_tickers),
            "successful_symbols": len(financial_data),
            "failed_symbols": failed,
            "retrieval_mode": retrieval_mode,
            "providers_used": list(providers),
        },
        "financial_data": financial_data,
    }
