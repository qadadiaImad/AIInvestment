"""Export the public-site quantum data bundle: web/public/data/quantum.json.

Mirrors export_site.py / siteexport.py for the Quantum sector. Reads the latest
TradingView fundamentals batch that pull_quantum.py wrote to data/quantum/, folds in
fundamental (intrinsic) values, assembles sanitized per-stock records, the quantum
relationship graph (quantum_capital_web.build_graph()), the layer map, and a lean
screener. Every stock + capital_web node is stamped sector:"Quantum". The whole bundle
is run through the same fundamental_value sanitizer as the AI export — nothing leaks.

REST-first, educational/research only — not financial advice. Quantum pure-plays are
largely pre-revenue: the screener shows what's MISSING (nulls), never fabricated numbers.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib

from aiinvest import fundamental, quantum_capital_web, quantum_stack, siteexport

SECTOR = quantum_stack.SECTOR  # "Quantum"

SOURCES = [
    {"name": "TradingView", "url": "https://www.tradingview.com/"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/"},
    {"name": "SEC EDGAR", "url": "https://www.sec.gov/edgar"},
    {"name": "FRED", "url": "https://fred.stlouisfed.org/"},
]
DISCLAIMER = ("Educational research only — not financial advice and not a recommendation "
              "to buy or sell any security. Quantum pure-plays are largely pre-revenue and "
              "speculative; missing figures are shown as nulls, never fabricated. Figures "
              "are derived from public sources, are date-stamped, and decay; verify against "
              "primary sources before acting.")

# TradingView metric column id -> (valuation|fundamentals|performance, output field).
_VAL = "valuation"
_FUND = "fundamentals"
_PERF = "performance"
_METRIC_MAP = {
    "close": (_VAL, "price"),
    "price_earnings_ttm": (_VAL, "pe"),
    "price_book_fq": (_VAL, "pb"),
    "price_revenue_ttm": (_VAL, "ps"),
    "market_cap_basic": (_VAL, "market_cap"),
    "dividend_yield_recent": (_VAL, "dividend_yield"),
    "gross_margin_ttm": (_FUND, "gross_margin"),
    "operating_margin_ttm": (_FUND, "operating_margin"),
    "net_margin_ttm": (_FUND, "net_margin"),
    "free_cash_flow_margin_ttm": (_FUND, "fcf_margin"),
    "return_on_equity": (_FUND, "roe"),
    "return_on_assets": (_FUND, "roa"),
    "return_on_invested_capital": (_FUND, "roic"),
    "debt_to_equity": (_FUND, "debt_to_equity"),
    "current_ratio": (_FUND, "current_ratio"),
    "total_revenue_yoy_growth_ttm": (_FUND, "rev_growth_yoy"),
    "earnings_per_share_diluted_yoy_growth_ttm": (_FUND, "eps_growth_yoy"),
    "sector": (_FUND, "sector"),
    "industry": (_FUND, "industry"),
    "Perf.Y": (_PERF, "perf_1y"),
    "Perf.YTD": (_PERF, "perf_ytd"),
    "beta_1_year": (_PERF, "beta"),
}


def _val(envelope):
    """Pull the parsed value from a stamped envelope (or None)."""
    if isinstance(envelope, dict):
        return envelope.get("value")
    return envelope


def _stock_from_record(rec):
    """Turn one TradingView batch record into a publishable stock dict (pre-sanitize)."""
    metrics = rec.get("metrics", {}) or {}
    valuation, fundamentals, performance = {}, {}, {}
    bucket = {_VAL: valuation, _FUND: fundamentals, _PERF: performance}
    for col, (group, field) in _METRIC_MAP.items():
        if col in metrics:
            bucket[group][field] = _val(metrics[col])
    desc = _val(metrics.get("description")) if "description" in metrics else None
    nxt = _val(metrics.get("earnings_release_next_date")) \
        if "earnings_release_next_date" in metrics else None
    catalysts = [{"date": nxt, "title": f"{rec.get('symbol')} earnings", "type": "earnings"}] \
        if nxt else []
    return {
        "symbol": rec.get("symbol"),
        "name": desc or rec.get("symbol"),
        "layer": rec.get("stack_layer"),
        "as_of": rec.get("as_of"),
        "valuation": valuation,
        "fundamentals": fundamentals,
        "performance": performance,
        "catalysts": catalysts,
        "tv_symbol": rec.get("ticker"),
    }


def build(batch, fundamentals=None):
    """Assemble the quantum.json bundle from a TradingView batch + fundamental_value records.

    Pure (no I/O). `batch` mirrors what pull_quantum.py writes (report.assemble_batch
    shape). `fundamentals` maps bare symbol -> {fundamental_value, margin_of_safety_pct,
    fundamental_value_series}. Every stock + capital_web node is stamped sector:"Quantum"
    and the whole bundle is run through the fundamental_value sanitizer.
    """
    fundamentals = fundamentals or {}
    financial = (batch or {}).get("financial_data", {}) or {}

    stocks = {}
    for sym, rec in financial.items():
        s = siteexport._clean(_stock_from_record(rec))
        s["sector"] = SECTOR
        s["history"] = {}  # multi-year annual* history; folded from fundamentals below
        stocks[sym] = s

    # fold in fundamental (intrinsic) values; compute OUR OWN valuation tag from live price.
    for sym, s in stocks.items():
        frec = fundamentals.get(sym)
        if not frec:
            continue
        # multi-year annual history (mirrors siteexport: fs.get("history", {})).
        s["history"] = siteexport._clean(frec.get("history") or {})
        fval = frec.get("fundamental_value")
        if fval is None:
            continue
        price = s.get("valuation", {}).get("price")
        s["valuation"]["fundamental_value"] = fval
        s["valuation"]["fundamental_valuation"] = fundamental.valuation_tag(price, fval)
        s["valuation"]["fundamental_discount_pct"] = fundamental.discount_pct(price, fval)
        s["valuation"]["margin_of_safety_pct"] = frec.get("margin_of_safety_pct")
        if frec.get("fundamental_value_series"):
            s["fundamental_value_series"] = frec["fundamental_value_series"]

    # relationship graph from the curated quantum web; stamp sector on every node.
    graph = quantum_capital_web.build_graph()
    for n in graph["nodes"]:
        n["sector"] = SECTOR
    graph = siteexport._clean(graph)

    layers = {layer: [t.split(":")[-1] for t in tickers]
              for layer, tickers in quantum_stack.LAYERS.items()}

    # lean screener rows from sanitized stocks.
    screener = []
    for sym, s in stocks.items():
        val = s.get("valuation", {})
        fund = s.get("fundamentals", {})
        perf = s.get("performance", {})
        cats = [c for c in s.get("catalysts", []) if c.get("date")]
        nxt = min(cats, key=lambda c: c["date"])["date"] if cats else None
        screener.append({
            "symbol": sym, "layer": s.get("layer"), "sector": SECTOR,
            "price": val.get("price"), "pe": val.get("pe"),
            "fundamental_value": val.get("fundamental_value"),
            "fundamental_discount_pct": val.get("fundamental_discount_pct"),
            "net_margin": fund.get("net_margin"), "roe": fund.get("roe"),
            "rev_growth_yoy": fund.get("rev_growth_yoy"), "perf_1y": perf.get("perf_1y"),
            "next_catalyst": nxt,
        })
    screener.sort(key=lambda r: (r["roe"] is None, -(r["roe"] or 0)))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "generated_at": now,
        "disclaimer": DISCLAIMER,
        "sources": SOURCES,
        "layers": layers,
        "stocks": stocks,
        "capital_web": graph,
        "screener": screener,
    }


def _latest_quantum_batch(data_root):
    """Newest TradingView quantum batch under data/quantum/<date>/...json (or None)."""
    paths = sorted(glob.glob(str(data_root / "quantum" / "*" / "tradingview_quantum_*.json")))
    if not paths:
        # fall back to any json in the dated quantum dirs
        paths = sorted(glob.glob(str(data_root / "quantum" / "*" / "*.json")))
    if not paths:
        return None
    return json.loads(pathlib.Path(paths[-1]).read_text(encoding="utf-8"))


def _load_fundamentals(data_root, symbols):
    fdir = data_root / "fundamental"
    out = {}
    for sym in symbols:
        fpath = fdir / f"{sym}.json"
        if fpath.exists():
            try:
                out[sym] = json.loads(fpath.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
    return out


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Export the public Quantum data bundle.")
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(repo / "web" / "public" / "data" / "quantum.json"))
    args = ap.parse_args(argv)
    data_root = pathlib.Path(args.data)

    batch = _latest_quantum_batch(data_root)
    if batch is None:
        print(f"No quantum batch found under {data_root / 'quantum'} — run pull_quantum.py first.")
        return 2

    symbols = list((batch.get("financial_data") or {}).keys())
    fundamentals = _load_fundamentals(data_root, symbols)
    bundle = build(batch, fundamentals)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    leak = [t for t in ("guru", "gf value", "gf_value", "value trap", "gf score")
            if t in json.dumps(bundle).lower()]
    g = bundle["capital_web"]
    print(f"Wrote {out}")
    print(f"  stocks={len(bundle['stocks'])} edges={len(g['edges'])} "
          f"nodes={len(g['nodes'])} screener={len(bundle['screener'])}")
    print(f"  fundamental_value-leak check: {'CLEAN' if not leak else 'LEAK ' + str(leak)}")
    return 1 if leak else 0


if __name__ == "__main__":
    raise SystemExit(main())
