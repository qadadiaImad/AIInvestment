"""Pull Quantum-sector fundamentals from TradingView's scanner (REST) and write the batch.

Mirrors pull_ai_stack.py: REST-first per CLAUDE.md — no browser. Drives the same
aiinvest.tradingview + schema path over the quantum universe (quantum_stack.all_tickers()).
PENDING names (e.g. QNT / Quantinuum) are attempted on each pull and silently skipped if
they don't resolve live yet — honest miss-reporting lists every unresolved ticker.

Writes data/quantum/<date>/tradingview_quantum_<stamp>.json (same layout as the AI pull).

Usage:
    python pull_quantum.py                 # whole quantum universe (+ PENDING attempt)
    python pull_quantum.py --layer Q1-hardware
    python pull_quantum.py --limit 3       # smoke a small subset against the live scan
    python pull_quantum.py --no-pending    # skip the PENDING (QNT) attempt
    python pull_quantum.py --out ../data   # custom output root

Educational/research only — not financial advice. Quantum pure-plays are largely
pre-revenue/speculative; recent SPAC/IPO names must be re-verified live before a pull
treats them as fact.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

from aiinvest import history, quantum_stack, tradingview


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _bare(ticker):
    """EXCHANGE:SYMBOL -> bare SYMBOL (the key export_quantum reads under data/fundamental)."""
    return ticker.split(":")[-1]


def pull_history(symbols, data_root):
    """Fetch multi-year annual history per bare symbol and merge into data/fundamental/<SYM>.json.

    Keyless Yahoo timeseries (history.fetch_history). Merge-safe and idempotent: re-reads the
    existing fundamental record, overwrites only the "history" key, preserves everything else.
    Returns {symbol: bool} — True when a NON-EMPTY annual history was persisted.
    """
    fdir = data_root / "fundamental"
    fdir.mkdir(parents=True, exist_ok=True)
    results = {}
    for sym in symbols:
        try:
            hist = history.fetch_history(sym)
        except Exception as e:  # noqa: BLE001
            print(f"  history {sym}: FAILED ({e})")
            results[sym] = False
            continue
        non_empty = bool(hist) and any(hist.get(k) for k in history.DEFAULT_TYPES)
        fpath = fdir / f"{sym}.json"
        rec = {}
        if fpath.exists():
            try:
                rec = json.loads(fpath.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                rec = {}
        if not isinstance(rec, dict):
            rec = {}
        rec.setdefault("symbol", sym)
        rec["history"] = hist
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        results[sym] = non_empty
        print(f"  history {sym}: {'OK' if non_empty else 'empty'} -> {fpath}")
    return results


def assemble_batch(records, requested_tickers, retrieved_at,
                   retrieval_mode="rest", providers=("tradingview",)):
    """Build the quantum batch envelope (mirrors report.assemble_batch, quantum layers)."""
    financial_data = {}
    seen_tickers = set()
    for rec in records:
        seen_tickers.add(rec["ticker"])
        financial_data[rec["symbol"]] = {
            "symbol": rec["symbol"],
            "ticker": rec["ticker"],
            "stack_layer": quantum_stack.layer_of(rec["ticker"]),
            "as_of": retrieved_at,
            "metrics": rec["metrics"],
        }
    failed = [t for t in requested_tickers if t not in seen_tickers]
    return {
        "batch_metadata": {
            "batch_timestamp": retrieved_at,
            "sector": quantum_stack.SECTOR,
            "total_symbols_requested": len(requested_tickers),
            "successful_symbols": len(financial_data),
            "failed_symbols": failed,
            "retrieval_mode": retrieval_mode,
            "providers_used": list(providers),
        },
        "financial_data": financial_data,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull Quantum-sector fundamentals via TradingView REST.")
    ap.add_argument("--layer", choices=sorted(quantum_stack.LAYERS),
                    help="Restrict to one quantum stack layer.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Smoke a small subset (first N tickers) against the live scan.")
    ap.add_argument("--no-pending", action="store_true",
                    help="Skip attempting the PENDING (pre-IPO) tickers (e.g. QNT).")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"),
                    help="Output root directory (default: ../data).")
    args = ap.parse_args(argv)

    if args.layer:
        tickers = list(quantum_stack.LAYERS[args.layer])
    else:
        tickers = quantum_stack.all_tickers()
        if not args.no_pending:
            tickers = tickers + list(quantum_stack.PENDING)
    if args.limit is not None:
        tickers = tickers[:args.limit]

    if not tickers:
        print(f"No tradeable tickers in {args.layer} (likely private/pre-IPO).")
        return 0

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    records = tradingview.scan(tickers, retrieved_at=stamp)
    batch = assemble_batch(records, tickers, stamp)

    out_dir = pathlib.Path(args.out) / "quantum" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"tradingview_quantum_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path = out_dir / fname
    out_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")

    # multi-year annual history (keyless Yahoo) — merged into data/fundamental/<SYM>.json,
    # which export_quantum reads. Cover every bare symbol we requested (resolved or not).
    hist_symbols = sorted({_bare(t) for t in tickers})
    print(f"Fetching annual history for {len(hist_symbols)} symbols...")
    hist_results = pull_history(hist_symbols, pathlib.Path(args.out))
    hist_ok = sorted(s for s, ok in hist_results.items() if ok)
    print(f"  history: {len(hist_ok)}/{len(hist_results)} symbols got a non-empty annual history")

    md = batch["batch_metadata"]
    failed = md["failed_symbols"]
    pending_unresolved = [t for t in (quantum_stack.PENDING if not args.no_pending else []) if t in failed]
    print(f"Wrote {out_path}")
    print(f"  requested={md['total_symbols_requested']} ok={md['successful_symbols']} "
          f"failed={len(failed)}")
    if failed:
        print(f"  unresolved tickers (no live data — not treated as fact): {', '.join(failed)}")
    if pending_unresolved:
        print(f"  PENDING still pre-IPO/unresolved (skipped): {', '.join(pending_unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
