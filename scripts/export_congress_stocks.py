"""Export the public-site congress-stocks data bundle: web/public/data/congress_stocks.json.

Mirrors export_quantum.py for the Congress sector (the top-300 most-traded congress-only
tickers, see aiinvest.congress_stocks). Reads the latest TradingView fundamentals batch
that pull_congress_stocks.py wrote to data/congress_stocks/, folds in fundamental
(intrinsic) values + multi-year history, assembles sanitized per-stock records and a lean
screener. Every stock is stamped sector:"Congress". There is no curated capital_web graph
for this slice, so capital_web is omitted (empty). The whole bundle is run through the same
fundamental_value sanitizer as the AI/Quantum exports — nothing gated ever leaks.

REST-first, educational/research only — not financial advice. These names are the tail of
disclosed congressional trades, NOT a recommendation; missing figures are nulls, never faked.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib

from aiinvest import congress_stocks, fundamental, siteexport

SECTOR = congress_stocks.SECTOR  # "Congress"

SOURCES = [
    {"name": "U.S. House Clerk (STOCK Act PTRs)",
     "url": "https://disclosures-clerk.house.gov/"},
    {"name": "TradingView", "url": "https://www.tradingview.com/"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/"},
    {"name": "SEC EDGAR", "url": "https://www.sec.gov/edgar"},
    {"name": "FRED", "url": "https://fred.stlouisfed.org/"},
]
DISCLAIMER = ("Educational research only — not financial advice and not a recommendation "
              "to buy or sell any security. This universe is the tail of self-reported, "
              "unverified congressional STOCK Act trades and is not an accusation of "
              "wrongdoing against any individual. Missing figures are shown as nulls, never "
              "fabricated. Figures are derived from public sources, are date-stamped, and "
              "decay; verify against primary sources before acting.")

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
    "sector": (_FUND, "tv_sector"),
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
    """Assemble the congress_stocks.json bundle from a TradingView batch + fundamental_value records.

    Pure (no I/O). `batch` mirrors what pull_congress_stocks.py writes (report.assemble_batch
    shape). `fundamentals` maps bare symbol -> {fundamental_value, margin_of_safety_pct,
    fundamental_value_series, history}. Every stock is stamped sector:"Congress" and the whole
    bundle is run through the fundamental_value sanitizer. No capital_web graph for this slice.
    """
    fundamentals = fundamentals or {}
    financial = (batch or {}).get("financial_data", {}) or {}

    stocks = {}
    for sym, rec in financial.items():
        s = siteexport._clean(_stock_from_record(rec))
        s["sector"] = SECTOR
        s["history"] = {}  # multi-year annual history; folded from fundamentals below
        stocks[sym] = s

    # fold in fundamental (intrinsic) values + multi-year history; compute OUR OWN
    # valuation tag from the live price.
    for sym, s in stocks.items():
        frec = fundamentals.get(sym)
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

    # lean screener rows from sanitized stocks.
    screener = []
    for sym, s in stocks.items():
        val = s.get("valuation", {})
        fund = s.get("fundamentals", {})
        perf = s.get("performance", {})
        cats = [c for c in s.get("catalysts", []) if c.get("date")]
        nxt = min(cats, key=lambda c: c["date"])["date"] if cats else None
        screener.append({
            "symbol": sym, "sector": SECTOR,
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
        "stocks": stocks,
        "capital_web": {"nodes": [], "edges": []},
        "screener": screener,
    }


def _latest_congress_batch(data_root):
    """Newest TradingView congress-stocks batch under data/congress_stocks/<date>/...json."""
    paths = sorted(glob.glob(
        str(data_root / "congress_stocks" / "*" / "tradingview_congress_stocks_*.json")))
    if not paths:
        paths = sorted(glob.glob(str(data_root / "congress_stocks" / "*" / "*.json")))
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
    ap = argparse.ArgumentParser(description="Export the public Congress-stocks data bundle.")
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(
        repo / "web" / "public" / "data" / "congress_stocks.json"))
    args = ap.parse_args(argv)
    data_root = pathlib.Path(args.data)

    batch = _latest_congress_batch(data_root)
    if batch is None:
        print(f"No congress_stocks batch found under {data_root / 'congress_stocks'} "
              f"— run pull_congress_stocks.py first.")
        return 2

    symbols = list((batch.get("financial_data") or {}).keys())
    fundamentals = _load_fundamentals(data_root, symbols)
    bundle = build(batch, fundamentals)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    leak = [t for t in ("guru", "gf value", "gf_value", "value trap", "gf score")
            if t in json.dumps(bundle).lower()]
    print(f"Wrote {out}")
    print(f"  stocks={len(bundle['stocks'])} screener={len(bundle['screener'])}")
    print(f"  fundamental_value-leak check: {'CLEAN' if not leak else 'LEAK ' + str(leak)}")
    return 1 if leak else 0


if __name__ == "__main__":
    raise SystemExit(main())
