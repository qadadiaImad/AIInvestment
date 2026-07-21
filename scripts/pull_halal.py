"""Pull halal-screen balance-sheet inputs for the FULL universe (AI + Quantum)
via TradingView's scanner (REST) and write the batch.

One POST covers all ~128 tickers (bulk verified). SEPARATE from the AI/quantum
daily pulls so those stay byte-identical. Writes
data/halal/<date>/tradingview_halal_<stamp>.json.

Educational/research only — not financial advice, not religious rulings.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

from aiinvest import ai_stack, quantum_stack, tradingview


def universe_tickers():
    """AI + Quantum tradeable tickers, de-duplicated, order-stable."""
    seen, out = set(), []
    for t in ai_stack.all_tickers() + quantum_stack.all_tickers():
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def assemble_batch(records, requested_tickers, retrieved_at):
    """Batch envelope (mirrors pull_quantum.assemble_batch; scope 'halal')."""
    financial_data, seen = {}, set()
    for rec in records:
        seen.add(rec["ticker"])
        financial_data[rec["symbol"]] = {
            "symbol": rec["symbol"], "ticker": rec["ticker"],
            "as_of": retrieved_at, "metrics": rec["metrics"],
        }
    failed = [t for t in requested_tickers if t not in seen]
    return {
        "batch_metadata": {
            "batch_timestamp": retrieved_at, "scope": "halal",
            "total_symbols_requested": len(requested_tickers),
            "successful_symbols": len(financial_data),
            "failed_symbols": failed,
            "retrieval_mode": "rest", "providers_used": ["tradingview"],
        },
        "financial_data": financial_data,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull halal-screen inputs via TradingView REST.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Smoke a small subset (first N tickers).")
    ap.add_argument("--verify-columns", action="store_true",
                    help="Check every HALAL_COLUMNS id against GET /america/metainfo "
                         "(the scanner returns 200+null for unknown columns — this is "
                         "the only real validation) and exit.")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"))
    args = ap.parse_args(argv)

    if args.verify_columns:
        import requests
        meta = requests.get("https://scanner.tradingview.com/america/metainfo",
                            headers={"User-Agent": tradingview._UA}, timeout=25).json()
        known = {f.get("n") for f in meta.get("fields", [])}
        missing = [c for c in tradingview.HALAL_COLUMNS if c not in known]
        print(f"metainfo fields={len(known)}; HALAL_COLUMNS={len(tradingview.HALAL_COLUMNS)}; "
              f"missing={missing or 'none'}")
        return 1 if missing else 0

    tickers = universe_tickers()
    if args.limit is not None:
        tickers = tickers[:args.limit]

    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    records = tradingview.scan(tickers, columns=tradingview.HALAL_COLUMNS,
                               retrieved_at=stamp)
    batch = assemble_batch(records, tickers, stamp)

    out_dir = pathlib.Path(args.out) / "halal" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"tradingview_halal_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")

    md = batch["batch_metadata"]
    print(f"Wrote {out_path}")
    print(f"  requested={md['total_symbols_requested']} ok={md['successful_symbols']} "
          f"failed={len(md['failed_symbols'])}")
    if md["failed_symbols"]:
        print(f"  unresolved: {', '.join(md['failed_symbols'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
