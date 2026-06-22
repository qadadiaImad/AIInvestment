"""Pull 5y daily price history for every AI-stack ticker (Yahoo, keyless REST — ungated).

Writes web/public/data/prices/<SYM>.json = {symbol, series:[{date,close}], returns:{1y,3y,5y}}.
Used for the on-page price chart + return columns. Light thread pool; Yahoo is ungated.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime
import json
import pathlib

from aiinvest import ai_stack, price_history, quantum_stack


def _one(full_ticker, out_dir, now):
    sym = full_ticker.split(":")[-1]
    try:
        series = price_history.fetch_history(sym, range="5y", interval="1d")
    except Exception as e:  # noqa: BLE001
        return sym, 0, str(e)
    if not series:
        return sym, 0, "empty"
    rec = {"symbol": sym, "retrieved_at": now,
           "series": series, "returns": price_history.returns_summary(series)}
    (out_dir / f"{sym}.json").write_text(json.dumps(rec), encoding="utf-8")
    return sym, len(series), None


def main():
    repo = pathlib.Path(__file__).resolve().parent.parent
    out_dir = repo / "web" / "public" / "data" / "prices"
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Prices cover BOTH sectors so every displayed name (incl. quantum) has a
    # price file for the Price-vs-Fundamental-Value chart. De-dup bridge names.
    tickers = list(dict.fromkeys(ai_stack.all_tickers() + quantum_stack.all_tickers()))

    ok, fail = 0, []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_one, t, out_dir, now): t for t in tickers}
        for fut in cf.as_completed(futs):
            sym, n, err = fut.result()
            if err:
                fail.append(f"{sym}:{err}")
            else:
                ok += 1
    print(f"prices: {ok}/{len(tickers)} ok -> {out_dir}")
    if fail:
        print("  failed:", fail[:20])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
