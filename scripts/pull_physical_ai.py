"""Pull Physical-AI / magnet-chain fundamentals from TradingView's scanner (REST).

Mirrors pull_quantum.py but the universe spans ten scanner markets, so tickers are
grouped by market (physical_ai_stack.by_market) and scanned one POST per market. Every
record is stamped with its quote currency; market cap and price are additionally
converted to USD with ECB reference rates (aiinvest.fx) so the screener can compare a
Shenzhen magnet maker with a NYSE miner. The FX table itself is stored in the batch.

Writes data/physical_ai/<date>/tradingview_physical_ai_<stamp>.json.

Usage:
    python pull_physical_ai.py                 # whole universe
    python pull_physical_ai.py --layer P2-magnets
    python pull_physical_ai.py --market china  # one scanner market
    python pull_physical_ai.py --limit 5       # smoke subset

Multi-year Yahoo history is NOT pulled here (foreign tickers need Yahoo-style suffixes;
left for a later pass). Educational/research only — not investment advice.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

from aiinvest import fx, physical_ai_stack as pas, schema, tradingview

EXTRA_COLUMNS = ["currency"]


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _usd_envelope(value, raw_ccy, fxinfo, retrieved_at, unit):
    return schema.make_envelope(
        value=value, raw=f"{raw_ccy}->USD", unit=unit, source="tradingview+ecb",
        source_url=fxinfo.get("source_url", fx.FRANKFURTER), source_class="api",
        retrieved_at=retrieved_at,
    )


def add_usd_fields(record, fxinfo, retrieved_at):
    """Append market_cap_usd / price_usd envelopes to a scan record (pure)."""
    m = record["metrics"]
    ccy = (m.get("currency") or {}).get("value")
    rates = fxinfo.get("rates", {})
    for src, dst, unit in (("market_cap_basic", "market_cap_usd", "usd"),
                           ("close", "price_usd", "usd")):
        val = (m.get(src) or {}).get("value")
        m[dst] = _usd_envelope(fx.to_usd(val, ccy, rates), ccy, fxinfo, retrieved_at, unit)
    return record


def assemble_batch(records, requested_tickers, retrieved_at, fxinfo,
                   retrieval_mode="rest", providers=("tradingview", "frankfurter")):
    """Batch envelope keyed by bare symbol, with layer, market, country and currency."""
    financial_data, seen = {}, set()
    for rec in records:
        seen.add(rec["ticker"])
        t = rec["ticker"]
        financial_data[rec["symbol"]] = {
            "symbol": rec["symbol"],
            "ticker": t,
            "stack_layer": pas.layer_of(t),
            "market": pas.market_of(t),
            "country": pas.country_of(t),
            "currency": (rec["metrics"].get("currency") or {}).get("value"),
            "as_of": retrieved_at,
            "metrics": rec["metrics"],
        }
    failed = [t for t in requested_tickers if t not in seen]
    return {
        "batch_metadata": {
            "batch_timestamp": retrieved_at,
            "sector": pas.SECTOR,
            "total_symbols_requested": len(requested_tickers),
            "successful_symbols": len(financial_data),
            "failed_symbols": failed,
            "retrieval_mode": retrieval_mode,
            "providers_used": list(providers),
            "fx": fxinfo,
        },
        "financial_data": financial_data,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull Physical-AI chain fundamentals via TradingView REST.")
    ap.add_argument("--layer", choices=sorted(pas.LAYERS))
    ap.add_argument("--market", choices=sorted(set(pas.MARKET_OF_EXCHANGE.values())))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"))
    args = ap.parse_args(argv)

    tickers = list(pas.LAYERS[args.layer]) if args.layer else pas.all_tickers() + list(pas.PENDING)
    if args.market:
        tickers = [t for t in tickers if pas.market_of(t) == args.market]
    if args.limit is not None:
        tickers = tickers[:args.limit]
    if not tickers:
        print("Nothing to pull.")
        return 0

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    fxinfo = fx.fetch_rates()
    print(f"FX {fxinfo['as_of']}: " + ", ".join(f"{k} {v}" for k, v in fxinfo["rates"].items()))

    columns = list(tradingview.DEFAULT_COLUMNS) + EXTRA_COLUMNS
    records = []
    for market, group in pas.by_market(tickers).items():
        try:
            recs = tradingview.scan(group, columns=columns, market=market, retrieved_at=stamp)
        except Exception as e:  # noqa: BLE001
            print(f"  {market}: FAILED ({e})")
            continue
        for r in recs:
            add_usd_fields(r, fxinfo, stamp)
        records.extend(recs)
        print(f"  {market}: {len(recs)}/{len(group)} resolved")

    batch = assemble_batch(records, tickers, stamp, fxinfo)
    out_dir = pathlib.Path(args.out) / "physical_ai" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"tradingview_physical_ai_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")

    meta = batch["batch_metadata"]
    print(f"Wrote {out_path}")
    print(f"  resolved {meta['successful_symbols']}/{meta['total_symbols_requested']}; "
          f"failed: {meta['failed_symbols'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
