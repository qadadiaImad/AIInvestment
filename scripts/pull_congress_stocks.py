"""Pull fundamentals + prices + history for the top-300 congress-only tickers (REST).

Mirrors pull_quantum.py: REST-first per CLAUDE.md — no browser, Mode A. The universe is
congress_stocks.top_tickers() (BARE symbols, see aiinvest.congress_stocks). Pipeline:

    1. Resolve each BARE congress symbol to a TradingView EXCHANGE:SYMBOL ticker via the
       /america scanner's ``name in_range`` market-scan (the same join pull_congress.py
       uses for sectors — bare symbols don't carry an exchange, so we let TradingView map
       them). Unresolved symbols are honestly reported and skipped, never guessed.
    2. Scan fundamentals for the resolved EXCHANGE:SYMBOL tickers (batched POSTs).
    3. Pull 5y daily prices into web/public/data/prices/<SYM>.json (reuse price_history),
       so every displayed name has a Price-vs-Fundamental-Value chart.
    4. Pull multi-year annual history (history.fetch_history) merged into
       data/fundamental/<SYM>.json (export folds it).
    5. Write the fundamentals batch to data/congress_stocks/<date>/ (mirrors pull_quantum).

Educational/research only — not financial advice. The universe is the tail of self-reported,
unverified congressional STOCK Act trades; not an accusation of wrongdoing against anyone.

Usage:
    python pull_congress_stocks.py                # full top-300 (slow)
    python pull_congress_stocks.py --limit 5      # smoke a small subset against live scans
    python pull_congress_stocks.py --out ../data  # custom output root
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

import requests

from aiinvest import congress_stocks, history, price_history, tradingview

# Bare-symbol resolver: the /america market scan keyed on ``name in_range`` returns the
# canonical EXCHANGE:SYMBOL (row "s") for each bare symbol — the same approach as
# pull_congress.lookup_sectors, but here we want the full ticker for a fundamentals scan.
_SCAN_URL = "https://scanner.tradingview.com/america/scan"
_SCAN_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _bare(ticker):
    """EXCHANGE:SYMBOL -> bare SYMBOL."""
    return ticker.split(":")[-1]


def resolve_tickers(bare_symbols, session=None, timeout=25, batch=200):
    """Resolve {bare -> EXCHANGE:SYMBOL} via the /america scanner ``name in_range`` scan.

    Returns (resolved_map, unresolved_list). Bare symbols that the scanner doesn't map
    (delisted, foreign-only, OTC) are reported as unresolved and skipped — never guessed.
    """
    http = session or requests
    syms = sorted({s for s in bare_symbols if s})
    resolved = {}
    for start in range(0, len(syms), batch):
        chunk = syms[start:start + batch]
        payload = {
            "filter": [{"left": "name", "operation": "in_range", "right": chunk}],
            "columns": ["name"],
            "range": [0, len(chunk)],
        }
        resp = http.post(_SCAN_URL, json=payload,
                         headers={"User-Agent": _SCAN_UA}, timeout=timeout)
        resp.raise_for_status()
        for row in resp.json().get("data", []):
            full = row.get("s")
            d = row.get("d", []) or []
            name = d[0] if d else (full.split(":")[-1] if full else None)
            if name and full and name not in resolved:
                resolved[name] = full
    unresolved = [s for s in syms if s not in resolved]
    return resolved, unresolved


def assemble_batch(records, requested_tickers, retrieved_at,
                   retrieval_mode="rest", providers=("tradingview",)):
    """Build the congress-stocks batch envelope (mirrors report.assemble_batch).

    No stack layers for this sector — stack_layer is None for every name.
    """
    financial_data = {}
    seen_tickers = set()
    for rec in records:
        seen_tickers.add(rec["ticker"])
        financial_data[rec["symbol"]] = {
            "symbol": rec["symbol"],
            "ticker": rec["ticker"],
            "stack_layer": None,
            "as_of": retrieved_at,
            "metrics": rec["metrics"],
        }
    failed = [t for t in requested_tickers if t not in seen_tickers]
    return {
        "batch_metadata": {
            "batch_timestamp": retrieved_at,
            "sector": congress_stocks.SECTOR,
            "total_symbols_requested": len(requested_tickers),
            "successful_symbols": len(financial_data),
            "failed_symbols": failed,
            "retrieval_mode": retrieval_mode,
            "providers_used": list(providers),
        },
        "financial_data": financial_data,
    }


def pull_history(symbols, data_root):
    """Fetch multi-year annual history per bare symbol -> data/fundamental/<SYM>.json.

    Merge-safe + idempotent (overwrites only "history"). Returns {symbol: bool}.
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


def pull_prices(symbols, repo_root, now):
    """Fetch 5y daily prices per bare symbol -> web/public/data/prices/<SYM>.json."""
    out_dir = repo_root / "web" / "public" / "data" / "prices"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for sym in symbols:
        try:
            series = price_history.fetch_history(sym, range="5y", interval="1d")
        except Exception as e:  # noqa: BLE001
            print(f"  prices {sym}: FAILED ({e})")
            results[sym] = False
            continue
        if not series:
            print(f"  prices {sym}: empty")
            results[sym] = False
            continue
        rec = {"symbol": sym, "retrieved_at": now, "series": series,
               "returns": price_history.returns_summary(series)}
        (out_dir / f"{sym}.json").write_text(json.dumps(rec), encoding="utf-8")
        results[sym] = True
        print(f"  prices {sym}: {len(series)} pts -> {out_dir / (sym + '.json')}")
    return results


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description="Pull top-300 congress-only fundamentals/prices/history via TradingView REST.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Smoke a small subset (first N congress tickers) against live scans.")
    ap.add_argument("--out", default=str(repo / "data"),
                    help="Output root directory (default: ../data).")
    args = ap.parse_args(argv)

    bare = congress_stocks.top_tickers(n=300)
    if args.limit is not None:
        bare = bare[:args.limit]
    if not bare:
        print("No congress-only tickers derived from congress.json.")
        return 0

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    session = requests.Session()

    # 1: resolve bare congress symbols -> EXCHANGE:SYMBOL
    print(f"Resolving {len(bare)} bare congress symbols via /america name in_range ...")
    resolved, unresolved = resolve_tickers(bare, session=session)
    full_tickers = [resolved[s] for s in bare if s in resolved]
    print(f"  resolved={len(full_tickers)} unresolved={len(unresolved)}")
    if unresolved:
        print(f"  unresolved (skipped, not guessed): {', '.join(unresolved)}")

    if not full_tickers:
        print("No congress tickers resolved to live TradingView symbols.")
        return 0

    # 2: fundamentals scan
    records = tradingview.scan(full_tickers, retrieved_at=stamp, session=session)
    batch = assemble_batch(records, full_tickers, stamp)

    out_dir = pathlib.Path(args.out) / "congress_stocks" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"tradingview_congress_stocks_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path = out_dir / fname
    out_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")

    # 3 + 4: prices (web/public/data/prices) + annual history (data/fundamental)
    hist_symbols = sorted({_bare(t) for t in full_tickers})
    print(f"Fetching 5y prices for {len(hist_symbols)} symbols...")
    price_results = pull_prices(hist_symbols, repo, stamp)
    price_ok = sum(1 for ok in price_results.values() if ok)
    print(f"Fetching annual history for {len(hist_symbols)} symbols...")
    hist_results = pull_history(hist_symbols, pathlib.Path(args.out))
    hist_ok = sum(1 for ok in hist_results.values() if ok)

    md = batch["batch_metadata"]
    failed = md["failed_symbols"]
    print(f"Wrote {out_path}")
    print(f"  requested(resolved)={md['total_symbols_requested']} "
          f"ok={md['successful_symbols']} failed={len(failed)} "
          f"unresolved_bare={len(unresolved)}")
    print(f"  prices: {price_ok}/{len(hist_symbols)} ok; "
          f"history: {hist_ok}/{len(hist_symbols)} non-empty")
    if failed:
        print(f"  fundamentals miss (no live row): {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
