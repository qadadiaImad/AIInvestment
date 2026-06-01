"""Gently backfill the historical fundamental-value SERIES for a list of tickers.

    python fundamental_backfill.py NVDA MSFT GOOGL ...

For each ticker: fetch (fresh browser, natural render for the value + capture the chart-data
XHR for the series when it returns 200), save with merge-protect (never downgrades), then
sleep a randomized 8-14s. Gentle pacing keeps the chart API under its rate limit so it serves
200s (the series) instead of 403s. Designed to run a slice per workflow agent.

NOTE (histo series): in practice this local-headless path gets a chart-API 403 for every
ticker even with gentle serial pacing (the gated fundamental source IP-throttles sessionless
headless). Recover the series via the Playwright MCP browser per
references/playwright-mcp-protocol.md (Mode B) — the MCP real-browser session gets 200.
"""
from __future__ import annotations

import random
import sys
import time

import fundamental_fetch as ff


def main(argv=None):
    tickers = [t.upper() for t in (argv if argv is not None else sys.argv[1:])]
    if not tickers:
        print("usage: python fundamental_backfill.py SYM1 SYM2 ...")
        return 2
    got_series = 0
    for i, sym in enumerate(tickers):
        try:
            rec = ff.fetch(sym)
            ff.save(sym, rec)
            n = len(rec.get("fundamental_value_series") or [])
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: ERROR {e}")
            n = 0
            rec = {"fundamental_value": None}
        if n:
            got_series += 1
        print(f"  {sym}: value={rec.get('fundamental_value')} series={n}", flush=True)
        if i < len(tickers) - 1:
            time.sleep(random.uniform(6, 10))  # gentle pacing between tickers
    print(f"done: {got_series}/{len(tickers)} got a historical series", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
