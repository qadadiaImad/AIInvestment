"""Pull AI-stack fundamentals from TradingView's scanner (REST) and write the batch JSON.

REST-first per CLAUDE.md — no browser. Usage:
    python pull_ai_stack.py                # whole universe
    python pull_ai_stack.py --layer L1-chips
    python pull_ai_stack.py --out ../data  # custom output root
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

from aiinvest import ai_stack, report, tradingview


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull AI-stack fundamentals via TradingView REST.")
    ap.add_argument("--layer", choices=sorted(ai_stack.LAYERS), help="Restrict to one stack layer.")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"),
                    help="Output root directory (default: ../data).")
    args = ap.parse_args(argv)

    tickers = ai_stack.LAYERS[args.layer] if args.layer else ai_stack.all_tickers()
    if not tickers:
        print(f"No tradeable tickers in {args.layer} (likely private/pre-IPO).")
        return 0

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    records = tradingview.scan(tickers, retrieved_at=stamp)
    batch = report.assemble_batch(records, tickers, stamp)

    out_dir = pathlib.Path(args.out) / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"tradingview_ai-stack_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path = out_dir / fname
    out_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")

    md = batch["batch_metadata"]
    print(f"Wrote {out_path}")
    print(f"  requested={md['total_symbols_requested']} ok={md['successful_symbols']} "
          f"failed={md['failed_symbols']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
