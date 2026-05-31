"""Export the public-site data bundle: web/public/data/site.json (GuruFocus-free).

Assembles the latest fact sheet + narrative per ticker, the relationship graph (curated +
ai-extracted), a lean screener, and the stack map — all run through the GuruFocus sanitizer.
Publishes OUR analysis; links to TradingView/Yahoo/SEC/FRED only. Educational, not advice.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib
import re

from aiinvest import ai_stack, capital_web, enrich, fundamental, siteexport

SOURCES = [
    {"name": "TradingView", "url": "https://www.tradingview.com/"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/"},
    {"name": "SEC EDGAR", "url": "https://www.sec.gov/edgar"},
    {"name": "FRED", "url": "https://fred.stlouisfed.org/"},
]
DISCLAIMER = ("Educational research only — not financial advice and not a recommendation to "
              "buy or sell any security. Figures are derived from public sources, are "
              "date-stamped, and decay; verify against primary sources before acting.")


def _latest_factsheets(data_root):
    by_sym = {}
    for p in sorted(glob.glob(str(data_root / "*" / "factsheet_*.json"))):
        m = re.search(r"factsheet_([A-Z0-9]+)_", pathlib.Path(p).name)
        if m:
            by_sym[m.group(1)] = p  # sorted asc -> newest wins
    return by_sym


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(repo / "web" / "public" / "data" / "site.json"))
    args = ap.parse_args(argv)
    data_root = pathlib.Path(args.data)
    narr_dir = data_root / "narratives"

    stocks = {}
    for sym, fpath in _latest_factsheets(data_root).items():
        fs = json.loads(pathlib.Path(fpath).read_text(encoding="utf-8"))
        narrative = {}
        npath = narr_dir / f"{sym}.json"
        if npath.exists():
            try:
                narrative = json.loads(npath.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                narrative = {}
        stocks[sym] = siteexport.sanitize_stock(fs, narrative)

    # fold in fundamental (intrinsic) values; compute OUR OWN valuation tag from live price
    fdir = data_root / "fundamental"
    n_fund = 0
    for sym, s in stocks.items():
        fpath = fdir / f"{sym}.json"
        if not fpath.exists():
            continue
        try:
            rec = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        fval = rec.get("fundamental_value")
        if fval is None:
            continue
        price = s.get("valuation", {}).get("price")
        s["valuation"]["fundamental_value"] = fval
        s["valuation"]["fundamental_valuation"] = fundamental.valuation_tag(price, fval)
        s["valuation"]["fundamental_discount_pct"] = fundamental.discount_pct(price, fval)
        s["valuation"]["margin_of_safety_pct"] = rec.get("margin_of_safety_pct")
        if rec.get("fundamental_value_series"):
            s["fundamental_value_series"] = rec["fundamental_value_series"]
        n_fund += 1

    # tv_symbol (for the TradingView widget) + price returns (from the prices files)
    full_by_bare = {t.split(":")[-1]: t for t in ai_stack.all_tickers()}
    pdir = repo / "web" / "public" / "data" / "prices"
    for sym, s in stocks.items():
        s["tv_symbol"] = full_by_bare.get(sym)
        pf = pdir / f"{sym}.json"
        if pf.exists():
            try:
                s["returns"] = json.loads(pf.read_text(encoding="utf-8")).get("returns")
            except Exception:  # noqa: BLE001
                pass

    # relationship graph: curated + ai-extracted, then defensively scrubbed
    graph = capital_web.build_graph()
    enriched = enrich.load_store(str(repo / "capital_web_enriched.json"))
    if enriched:
        graph["edges"] = enrich.merge_enriched(graph["edges"], enriched)
    graph = siteexport._clean(graph)

    layers = {layer: [t.split(":")[-1] for t in tickers]
              for layer, tickers in ai_stack.LAYERS.items()}

    # lean screener rows from sanitized stocks
    screener = []
    for sym, s in stocks.items():
        val = s.get("valuation", {})
        fund = s.get("fundamentals", {})
        perf = s.get("performance", {})
        cats = [c for c in s.get("catalysts", []) if c.get("date")]
        nxt = min(cats, key=lambda c: c["date"])["date"] if cats else None
        rets = s.get("returns") or {}
        screener.append({
            "symbol": sym, "layer": s.get("layer"),
            "price": val.get("price"), "pe": val.get("pe"),
            "fundamental_value": val.get("fundamental_value"),
            "fundamental_discount_pct": val.get("fundamental_discount_pct"),
            "net_margin": fund.get("net_margin"), "roe": fund.get("roe"),
            "rev_growth_yoy": fund.get("rev_growth_yoy"), "perf_1y": perf.get("perf_1y"),
            "ret_1y": rets.get("1y"), "ret_5y": rets.get("5y"),
            "next_catalyst": nxt,
        })
    screener.sort(key=lambda r: (r["roe"] is None, -(r["roe"] or 0)))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle = {
        "generated_at": now,
        "disclaimer": DISCLAIMER,
        "sources": SOURCES,
        "layers": layers,
        "stocks": stocks,
        "capital_web": graph,
        "screener": screener,
    }

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    leak = [t for t in ("guru", "gf value", "gf_value", "value trap")
            if t in json.dumps(bundle).lower()]
    print(f"Wrote {out}")
    print(f"  stocks={len(stocks)} (fundamental_value on {n_fund}) edges={len(graph['edges'])} "
          f"nodes={len(graph['nodes'])} screener={len(screener)}")
    print(f"  GuruFocus-leak check: {'CLEAN' if not leak else 'LEAK ' + str(leak)}")
    return 1 if leak else 0


if __name__ == "__main__":
    raise SystemExit(main())
