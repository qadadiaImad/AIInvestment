"""Pull Kalray SA (Euronext Growth Paris, EURONEXT:ALKAL / Yahoo ALKAL.PA) — a foreign
AI-compute (DPU/MPPA) chipmaker — into web/public/data/extra_stocks.json.

Foreign names are outside the US `america` scanner, so we hit TradingView's FRANCE scanner
for fundamentals and Yahoo (ALKAL.PA) for 5y prices + multi-year history. The historical
fundamental_value SERIES (gated) is recovered separately via the Playwright MCB browser per
references/playwright-mcp-protocol.md and merged into data/fundamental/ALKAL.json.

extra_stocks.json mirrors the quantum/congress bundle schema (stocks{} + screener[]) so the
web loader can merge it like the others; every entry carries its own `sector`.

Educational/research only — not financial advice.
"""
from __future__ import annotations

import datetime
import json
import pathlib

import requests

from aiinvest import fundamental, history, price_history, siteexport
import export_quantum as eq  # reuse _stock_from_record + _METRIC_MAP

_SCAN_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_FR_SCAN = "https://scanner.tradingview.com/france/scan"

# One row per foreign add: (bare symbol, TV ticker, Yahoo symbol, sector, layer, name).
EXTRAS = [
    ("ALKAL", "EURONEXT:ALKAL", "ALKAL.PA", "AI", "L1-chips", "Kalray SA"),
]


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fr_scan(tv_tickers, session):
    cols = list(eq._METRIC_MAP) + ["description", "earnings_release_next_date"]
    payload = {"symbols": {"tickers": tv_tickers, "query": {"types": []}}, "columns": cols}
    r = session.post(_FR_SCAN, json=payload, headers={"User-Agent": _SCAN_UA}, timeout=30)
    r.raise_for_status()
    out = {}
    for row in r.json().get("data", []):
        d = row.get("d", []) or []
        out[row.get("s")] = {cols[i]: d[i] for i in range(min(len(cols), len(d)))}
    return out, cols


def main():
    repo = pathlib.Path(__file__).resolve().parent.parent
    now = _now()
    session = requests.Session()
    tv_tickers = [e[1] for e in EXTRAS]
    scanned, _cols = _fr_scan(tv_tickers, session)

    prices_dir = repo / "web" / "public" / "data" / "prices"
    prices_dir.mkdir(parents=True, exist_ok=True)
    fdir = repo / "data" / "fundamental"
    fdir.mkdir(parents=True, exist_ok=True)

    stocks, screener = {}, []
    for sym, tv, yh, sector, layer, name in EXTRAS:
        metrics = scanned.get(tv)
        if not metrics:
            print(f"  {sym}: NO TradingView france row for {tv} — skipped")
            continue
        rec = {"symbol": sym, "ticker": tv, "stack_layer": layer,
               "as_of": now, "metrics": metrics}
        s = siteexport._clean(eq._stock_from_record(rec))
        s["name"] = name
        s["sector"] = sector
        s["layer"] = layer
        # prices (Yahoo ALKAL.PA) -> prices/<SYM>.json
        try:
            series = price_history.fetch_history(yh, range="5y", interval="1d")
            if series:
                (prices_dir / f"{sym}.json").write_text(json.dumps(
                    {"symbol": sym, "retrieved_at": now, "series": series,
                     "returns": price_history.returns_summary(series)}), encoding="utf-8")
                print(f"  {sym}: prices {len(series)} pts")
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: prices FAILED ({e})")
        # multi-year history (Yahoo ALKAL.PA)
        hist = {}
        try:
            hist = history.fetch_history(yh) or {}
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: history FAILED ({e})")
        s["history"] = siteexport._clean(hist)
        # fold any already-saved fundamental_value + series (from the MCP step)
        frec = {}
        fpath = fdir / f"{sym}.json"
        if fpath.exists():
            try:
                frec = json.loads(fpath.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                frec = {}
        # always persist history into the fundamental record so the MCP step won't drop it
        frec.setdefault("symbol", sym)
        frec["history"] = hist
        fpath.write_text(json.dumps(frec, indent=2), encoding="utf-8")
        fval = frec.get("fundamental_value")
        if fval is not None:
            price = s.get("valuation", {}).get("price")
            s["valuation"]["fundamental_value"] = fval
            s["valuation"]["fundamental_valuation"] = fundamental.valuation_tag(price, fval)
            s["valuation"]["fundamental_discount_pct"] = fundamental.discount_pct(price, fval)
            s["valuation"]["margin_of_safety_pct"] = frec.get("margin_of_safety_pct")
        if frec.get("fundamental_value_series"):
            s["fundamental_value_series"] = frec["fundamental_value_series"]

        stocks[sym] = s
        val, fund, perf = s.get("valuation", {}), s.get("fundamentals", {}), s.get("performance", {})
        screener.append({
            "symbol": sym, "layer": layer, "sector": sector,
            "price": val.get("price"), "pe": val.get("pe"),
            "fundamental_value": val.get("fundamental_value"),
            "fundamental_discount_pct": val.get("fundamental_discount_pct"),
            "net_margin": fund.get("net_margin"), "roe": fund.get("roe"),
            "rev_growth_yoy": fund.get("rev_growth_yoy"), "perf_1y": perf.get("perf_1y"),
            "next_catalyst": None,
        })
        print(f"  {sym}: ok price={val.get('price')} sector={sector} history={len(hist)} fv={val.get('fundamental_value')}")

    bundle = {
        "generated_at": now,
        "disclaimer": ("Educational research only — not financial advice. Foreign/curated additions; "
                       "figures from public sources, date-stamped, and decay."),
        "sources": [{"name": "TradingView", "url": "https://www.tradingview.com/"},
                    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/"}],
        "stocks": stocks,
        "screener": screener,
    }
    out = repo / "web" / "public" / "data" / "extra_stocks.json"
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    leak = [t for t in ("guru", "gf value", "gf_value", "gf score") if t in json.dumps(bundle).lower()]
    print(f"Wrote {out}  stocks={len(stocks)}  leak={'CLEAN' if not leak else leak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
