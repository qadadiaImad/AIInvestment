"""Pull a full one-ticker dossier: REST sources live + filings + catalysts + relationships.

Usage:  python pull_dossier.py NVDA
GuruFocus GF Value is a Playwright/MCP step (no REST); pass a saved page via --gf-text-file
to fold it in, otherwise it's omitted with a note.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

from aiinvest import (ai_stack, capital_web, catalysts as cal, dossier, edgar,
                      gurufocus, history, peers, tradingview, yahoo)

FILING_FORMS = {"S-1", "S-1/A", "424B4", "10-K", "10-Q", "8-K"}


def _full_ticker(symbol):
    for t in ai_stack.all_tickers():
        if t.split(":")[-1] == symbol:
            return t
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol", help="Bare ticker, e.g. NVDA")
    ap.add_argument("--ticker", help="Full EXCHANGE:SYMBOL (if not in the universe).")
    ap.add_argument("--gf-text-file", help="Path to saved GuruFocus /valuation page text.")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"))
    args = ap.parse_args(argv)

    sym = args.symbol.upper()
    full = args.ticker or _full_ticker(sym)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sources, notes = {}, []

    # --- REST sources (live) ---
    if full:
        try:
            recs = tradingview.scan([full], retrieved_at=now)
            if recs:
                sources["tradingview"] = recs[0]
        except Exception as e:
            notes.append(f"tradingview failed: {e}")
    else:
        notes.append("no full ticker -> skipped TradingView")
    try:
        yh = yahoo.fetch_chart(sym, retrieved_at=now)
        if yh:
            sources["yahoo"] = yh
    except Exception as e:
        notes.append(f"yahoo failed: {e}")

    # --- GuruFocus (optional, from saved page text) ---
    if args.gf_text_file:
        text = pathlib.Path(args.gf_text_file).read_text(encoding="utf-8")
        url = f"https://www.gurufocus.com/stock/{sym}/valuation"
        sources["gurufocus"] = gurufocus.to_record(text, sym, url, now)
    else:
        notes.append("GuruFocus omitted (GF Value needs the Playwright/MCP fetch)")

    # --- EDGAR filings (live) ---
    filings = []
    try:
        cik = edgar.ticker_to_cik(sym, edgar.fetch_company_tickers())
        if cik:
            rows, _ = edgar.fetch_submissions(cik)
            filings = edgar.filter_filings(rows, FILING_FORMS)[:5]
        else:
            notes.append(f"no CIK for {sym} (private/foreign?) -> no filings")
    except Exception as e:
        notes.append(f"edgar failed: {e}")

    # --- catalysts (seed + live earnings) + relationship graph ---
    cats = cal.build()
    if "tradingview" in sources or full:
        try:
            erecs = tradingview.scan([full], columns=["earnings_release_next_date"], retrieved_at=now)
            cats += cal.from_tradingview_earnings(erecs, now)
        except Exception as e:
            notes.append(f"earnings pull failed: {e}")
    graph = capital_web.build_graph()

    # --- peer benchmarking: industry + AI-stack layer ---
    peer_stats = {}
    tv_rec = sources.get("tradingview")
    if tv_rec:
        compare = ["net_margin_ttm", "gross_margin_ttm", "return_on_equity",
                   "return_on_invested_capital", "price_earnings_ttm", "total_revenue_yoy_growth_ttm"]
        tgt = {m: (tv_rec["metrics"].get(m) or {}).get("value") for m in compare}
        industry = (tv_rec["metrics"].get("industry") or {}).get("value")
        layer = ai_stack.layer_of(full) if full else None
        try:
            if industry:
                ind = peers.scan_industry(industry, compare)
                peer_stats["industry"] = peers.peer_stats(tgt, ind, compare)
        except Exception as e:
            notes.append(f"industry peers failed: {e}")
        try:
            if layer:
                lay = peers.layer_peers(sym, layer, compare)
                peer_stats["layer"] = peers.peer_stats(tgt, lay, compare)
        except Exception as e:
            notes.append(f"layer peers failed: {e}")

    # --- multi-year fundamentals history (keyless Yahoo timeseries) ---
    hist = {}
    try:
        hist = history.fetch_history(sym)
    except Exception as e:
        notes.append(f"history failed: {e}")

    d = dossier.build_dossier(sym, sources, filings, cats, graph, now)
    d["peer_stats"] = peer_stats
    d["history"] = hist
    d["notes"] = notes

    out_dir = pathlib.Path(args.out) / now[:10]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"dossier_{sym}_{now.replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(d, indent=2), encoding="utf-8")

    px = d["metrics"].get("current_price", {})
    print(f"Dossier {sym} [{d['layer']}] -> {path}")
    print(f"  price={px.get('value')} sources={px.get('sources')} agree={px.get('agree')}")
    print(f"  filings={len(d['filings'])}  catalysts={len(d['catalysts'])}  "
          f"edges_in={len(d['relationships']['edges_to'])} edges_out={len(d['relationships']['edges_from'])}")
    for n in notes:
        print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
