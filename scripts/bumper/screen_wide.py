"""Bumper Radar screen over the WHOLE US market, not the repo's curated lists.

    cd scripts && python -m bumper.screen_wide [--no-sec]

A bumper is by definition not on anyone's list yet, so the universe is built by the
scanner, not by hand: every NYSE/NASDAQ/AMEX common stock with cap $50M-$3B and negative
free cash flow, minus sectors whose pre-profit names play a different game (biotech/pharma
binary trials, banks, retail, consumer, SPAC shells). Then the same gates as screen_today:
runway < 2y (numeric), going-concern language in 10-K/10-Q/20-F and listing notices in
8-K bodies over the last 12 months (SEC full-text search, one CIK at a time).

Output: data/bumper/<day>/screen_wide.json + markdown summary on stdout.
"""
from __future__ import annotations

import json
import sys

import requests

from . import sources as S
from .screen_today import D, efts_hits

COLS = ["name", "description", "sector", "industry", "exchange", "market_cap_basic", "total_revenue_ttm", "total_revenue_yoy_growth_ttm",
        "research_and_dev_ttm", "free_cash_flow_ttm", "cash_n_short_term_invest_fq", "total_debt_fq", "gross_margin_ttm",
        "Perf.Y", "Perf.6M", "ipo_offer_date", "number_of_employees"]
EXCLUDE_SECTORS = {"Health Technology", "Health Services", "Finance", "Retail Trade", "Consumer Non-Durables", "Consumer Services",
                   "Distribution Services", "Miscellaneous"}
FILTERS = [{"left": "market_cap_basic", "operation": "in_range", "right": [5e7, 3e9]},
           {"left": "free_cash_flow_ttm", "operation": "less", "right": 0},
           {"left": "type", "operation": "equal", "right": "stock"},
           {"left": "subtype", "operation": "in_range", "right": ["common", "foreign-issuer"]},
           {"left": "exchange", "operation": "in_range", "right": ["NYSE", "NASDAQ", "AMEX"]}]


def scan_all(page=500):
    rows, start = [], 0
    while True:
        payload = {"filter": FILTERS, "options": {"lang": "en"}, "symbols": {"query": {"types": []}}, "columns": COLS,
                   "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}, "range": [start, start + page]}
        r = requests.post(S.SCAN, json=payload, headers={"User-Agent": S.UA}, timeout=60)
        r.raise_for_status()
        data = r.json().get("data", [])
        for x in data:
            rec = dict(zip(COLS, x["d"]))
            rec["ticker"] = x["s"]
            rows.append(rec)
        if len(data) < page:
            return rows
        start += page
        S.polite(0.5)


def main(argv):
    stamp = S.now()
    raw = scan_all()
    by_sector = {}
    for r in raw:
        by_sector[r["sector"]] = by_sector.get(r["sector"], 0) + 1
    kept = [r for r in raw if r["sector"] not in EXCLUDE_SECTORS]
    out = []
    for v in kept:
        cap, fcf, cash, rev, rd = v["market_cap_basic"], v["free_cash_flow_ttm"], v["cash_n_short_term_invest_fq"], v["total_revenue_ttm"], v["research_and_dev_ttm"]
        rec = {"ticker": v["ticker"], "name": v["description"], "sector": v["sector"], "industry": v["industry"], "market_cap_usd": cap,
               "fcf_ttm": fcf, "cash": cash, "revenue_ttm": rev, "rev_growth_yoy": v["total_revenue_yoy_growth_ttm"],
               "rnd_to_rev": (abs(rd) / rev if rev and rd is not None else None), "rnd_ttm": rd, "gross_margin": v["gross_margin_ttm"],
               "perf_1y": v["Perf.Y"], "ipo": v["ipo_offer_date"], "employees": v["number_of_employees"],
               "runway_years": (cash / -fcf) if (fcf and fcf < 0 and cash) else None,
               "retrieved_at": stamp, "source": "TradingView scanner /america/scan", "source_class": "api"}
        reasons, flags = [], []
        if rec["runway_years"] is None:
            flags.append("no cash figure (runway unknown)")
        elif rec["runway_years"] < 2:
            reasons.append(f"runway {rec['runway_years']:.1f}y < 2y")
        rec["reasons"], rec["flags"] = reasons, flags
        out.append(rec)
    survivors = [r for r in out if not r["reasons"]]
    print(f"scanner universe: {len(raw)} pre-profit names cap $50M-$3B; sectors: {dict(sorted(by_sector.items(), key=lambda kv: -kv[1]))}")
    print(f"after sector exclusions: {len(kept)}; runway >= 2y or unknown: {len(survivors)}")
    if "--no-sec" not in argv:
        for i, rec in enumerate(survivors):
            cik = S.cik_for(rec["ticker"].split(":")[-1])
            rec["cik"] = cik
            if not cik:
                rec["flags"].append("no CIK (text gates not run)")
                continue
            n, docs = efts_hits(cik, '"substantial doubt" "going concern"', ["10-K", "10-Q", "20-F"])
            rec["going_concern_hits"], rec["going_concern_docs"] = n, docs
            if n:
                rec["flags"].append(f"going-concern language in {n} filing(s) last 12m")
            n2, docs2 = efts_hits(cik, '"minimum bid price" OR "Listing Rule 5550" OR "Listing Rule 5450" OR "notice of noncompliance"', ["8-K"], body_only=True)
            rec["listing_notice_hits"], rec["listing_notice_docs"] = n2, docs2
            if n2:
                rec["reasons"].append(f"exchange listing notice in {n2} 8-K(s) last 12m")
            if i % 50 == 49:
                print(f"  sec text gates {i + 1}/{len(survivors)}", flush=True)
    for rec in out:
        rec["stage"] = "DISQUALIFIED" if rec["reasons"] else ("FLAGGED" if rec["flags"] else "not disqualified")
        rec["binding_demand"] = "UNVERIFIED"
    (D / "screen_wide.json").write_text(json.dumps({"generated_at": stamp, "scanner_total": len(raw), "sectors_seen": by_sector,
                                                    "excluded_sectors": sorted(EXCLUDE_SECTORS), "rows": out}, indent=1), encoding="utf-8")
    clean = [r for r in out if r["stage"] == "not disqualified"]
    print(f"\nnot disqualified: {len(clean)} · flagged: {sum(r['stage'] == 'FLAGGED' for r in out)} · disqualified: {sum(r['stage'] == 'DISQUALIFIED' for r in out)}")
    bysec = {}
    for r in clean:
        bysec.setdefault(r["sector"], []).append(r)
    for sec, rs in sorted(bysec.items(), key=lambda kv: -len(kv[1])):
        print(f"\n### {sec} ({len(rs)})")
        print("| ticker | industry | cap $B | runway y | R&D/rev | rev growth | 1y perf |\n|---|---|---|---|---|---|---|")
        for r in sorted(rs, key=lambda r: -(r["rnd_to_rev"] or 0))[:12]:
            f = lambda x, nd=1, m=1, s="": "-" if x is None else f"{x * m:.{nd}f}{s}"
            print(f"| {r['ticker']} | {r['industry']} | {f(r['market_cap_usd'], 2, 1e-9)} | {f(r['runway_years'])} | {f(r['rnd_to_rev'], 2)} | {f(r['rev_growth_yoy'], 0, 1, '%')} | {f(r['perf_1y'], 0, 1, '%')} |")


if __name__ == "__main__":
    main(sys.argv[1:])
