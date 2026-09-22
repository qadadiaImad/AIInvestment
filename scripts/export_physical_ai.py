"""Export the public-site Physical-AI data bundle: web/public/data/physical_ai.json.

Mirrors export_quantum.py for the Physical-AI / rare-earth-magnet chain. Reads the latest
batch that pull_physical_ai.py wrote to data/physical_ai/, folds in fundamental
(intrinsic) values from data/fundamental/<SYM>.json, assembles sanitized per-stock
records (with currency, country and USD market cap), the curated relationship graph
(physical_ai_capital_web.build_graph()), the layer map, and a lean screener. Every stock
and graph node is stamped sector:"PhysicalAI". The bundle is run through the same
fundamental_value sanitizer as the AI export.

REST-first, educational/research only — not financial advice.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib

from aiinvest import fundamental, physical_ai_capital_web, physical_ai_stack as pas, siteexport

SECTOR = pas.SECTOR

SOURCES = [
    {"name": "TradingView", "url": "https://www.tradingview.com/"},
    {"name": "ECB reference rates (Frankfurter)", "url": "https://www.frankfurter.app/"},
    {"name": "SEC EDGAR", "url": "https://www.sec.gov/edgar"},
]
DISCLAIMER = ("Educational research only — not financial advice and not a recommendation "
              "to buy or sell any security. Many upstream rare-earth names are pre-revenue "
              "developers; missing figures are shown as nulls, never fabricated. Foreign "
              "listings are quoted in local currency with an ECB-rate USD market cap. Figures "
              "are date-stamped and decay; verify against primary sources before acting.")

_VAL, _FUND, _PERF = "valuation", "fundamentals", "performance"
_METRIC_MAP = {
    "close": (_VAL, "price"),
    "price_usd": (_VAL, "price_usd"),
    "price_earnings_ttm": (_VAL, "pe"),
    "price_book_fq": (_VAL, "pb"),
    "price_revenue_ttm": (_VAL, "ps"),
    "market_cap_basic": (_VAL, "market_cap_local"),
    "market_cap_usd": (_VAL, "market_cap"),
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
    return envelope.get("value") if isinstance(envelope, dict) else envelope


def local_price(price, currency):
    """LSE quotes arrive in pence (GBX) while every other figure for the name (GuruFocus
    value, market cap) is in pounds. Normalise so price and fundamental value share a unit."""
    if price is None:
        return None, currency
    if currency == "GBX":
        return price / 100.0, "GBP"
    return price, currency


def _stock_from_record(rec):
    metrics = rec.get("metrics", {}) or {}
    valuation, fundamentals, performance = {}, {}, {}
    bucket = {_VAL: valuation, _FUND: fundamentals, _PERF: performance}
    for col, (group, field) in _METRIC_MAP.items():
        if col in metrics:
            bucket[group][field] = _val(metrics[col])
    valuation["price"], valuation["currency"] = local_price(valuation.get("price"), rec.get("currency"))
    desc = _val(metrics.get("description")) if "description" in metrics else None
    nxt = _val(metrics.get("earnings_release_next_date")) if "earnings_release_next_date" in metrics else None
    catalysts = [{"date": nxt, "title": f"{rec.get('symbol')} earnings", "type": "earnings"}] if nxt else []
    return {
        "symbol": rec.get("symbol"),
        "name": desc or rec.get("symbol"),
        "layer": rec.get("stack_layer"),
        "country": rec.get("country"),
        "market": rec.get("market"),
        "as_of": rec.get("as_of"),
        "valuation": valuation,
        "fundamentals": fundamentals,
        "performance": performance,
        "catalysts": catalysts,
        "tv_symbol": rec.get("ticker"),
    }


def build(batch, fundamentals=None):
    """Assemble the physical_ai.json bundle (pure, no I/O)."""
    fundamentals = fundamentals or {}
    financial = (batch or {}).get("financial_data", {}) or {}

    stocks = {}
    for sym, rec in financial.items():
        s = siteexport._clean(_stock_from_record(rec))
        s["sector"] = SECTOR
        s["history"] = {}
        stocks[sym] = s

    for sym, s in stocks.items():
        # fundamentals are keyed by physical_ai_stack.fundamental_key (foreign listings are
        # namespaced EXCH_SYMBOL so they never collide with a US ticker of the same name).
        frec = fundamentals.get(pas.fundamental_key(s["tv_symbol"])) if s.get("tv_symbol") else None
        if not frec:
            continue
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

    graph = physical_ai_capital_web.build_graph()
    for n in graph["nodes"]:
        n["sector"] = SECTOR
    graph = siteexport._clean(graph)

    layers = {layer: [t.split(":")[-1] for t in tickers] for layer, tickers in pas.LAYERS.items()}

    screener = []
    for sym, s in stocks.items():
        val, fund, perf = s.get("valuation", {}), s.get("fundamentals", {}), s.get("performance", {})
        cats = [c for c in s.get("catalysts", []) if c.get("date")]
        nxt = min(cats, key=lambda c: c["date"])["date"] if cats else None
        screener.append({
            "symbol": sym, "layer": s.get("layer"), "sector": SECTOR,
            "country": s.get("country"), "currency": val.get("currency"),
            "price": val.get("price"), "pe": val.get("pe"), "market_cap": val.get("market_cap"),
            "fundamental_value": val.get("fundamental_value"),
            "fundamental_discount_pct": val.get("fundamental_discount_pct"),
            "net_margin": fund.get("net_margin"), "roe": fund.get("roe"),
            "rev_growth_yoy": fund.get("rev_growth_yoy"), "perf_1y": perf.get("perf_1y"),
            "next_catalyst": nxt,
        })
    screener.sort(key=lambda r: (r["market_cap"] is None, -(r["market_cap"] or 0)))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = (batch or {}).get("batch_metadata", {}) or {}
    return {
        "generated_at": now,
        "disclaimer": DISCLAIMER,
        "sources": SOURCES,
        "fx": meta.get("fx"),
        "layers": layers,
        "stocks": stocks,
        "capital_web": graph,
        "screener": screener,
    }


def _latest_batch(data_root):
    paths = sorted(glob.glob(str(data_root / "physical_ai" / "*" / "tradingview_physical_ai_*.json")))
    return json.loads(pathlib.Path(paths[-1]).read_text(encoding="utf-8")) if paths else None


def _load_fundamentals(data_root, tickers):
    """{fundamental_key: record} for every EXCHANGE:SYMBOL ticker with a record on disk."""
    out = {}
    for t in tickers:
        key = pas.fundamental_key(t)
        fpath = data_root / "fundamental" / f"{key}.json"
        if fpath.exists():
            try:
                out[key] = json.loads(fpath.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
    return out


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Export the public Physical-AI data bundle.")
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(repo / "web" / "public" / "data" / "physical_ai.json"))
    args = ap.parse_args(argv)
    data_root = pathlib.Path(args.data)

    batch = _latest_batch(data_root)
    if batch is None:
        print(f"No batch under {data_root / 'physical_ai'} — run pull_physical_ai.py first.")
        return 2
    tickers = [r["ticker"] for r in (batch.get("financial_data") or {}).values()]
    bundle = build(batch, _load_fundamentals(data_root, tickers))

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    leak = [t for t in ("guru", "gf value", "gf_value", "value trap", "gf score")
            if t in json.dumps(bundle).lower()]
    g = bundle["capital_web"]
    with_fv = sum(1 for s in bundle["stocks"].values() if s["valuation"].get("fundamental_value") is not None)
    print(f"Wrote {out}")
    print(f"  stocks={len(bundle['stocks'])} with_fundamental_value={with_fv} "
          f"edges={len(g['edges'])} nodes={len(g['nodes'])} screener={len(bundle['screener'])}")
    print(f"  fundamental_value-leak check: {'CLEAN' if not leak else 'LEAK ' + str(leak)}")
    return 1 if leak else 0


if __name__ == "__main__":
    raise SystemExit(main())
