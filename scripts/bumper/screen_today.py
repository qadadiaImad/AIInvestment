"""Today's Bumper Radar screen: the gates that can be run from live public data.

    cd scripts && python -m bumper.screen_today

Universe: the repo's own US-listed names across quantum, physical AI and the AI stack
(scripts/aiinvest/*_stack.py LAYERS), plus the 30 names in data/bumper_scan_<day>.json.
Stages that run here (all REST, all free):
  1. point-in-time universe   cap $50M-$3B, pre-profit (free cash flow < 0)
  2. disqualifying gates      runway < 2 years; going-concern language in a 10-K/10-Q filed in
                              the last 12 months; an exchange bid-price / listing-rule notice
                              (8-K text) in the last 12 months  -- both via SEC full-text search
Stages that do NOT run here and are reported as UNVERIFIED: binding-demand check, dilution
buyer identity, 13D stakes, governance self-dealing, funding-gap departures, judge narration.
Output: data/bumper/<day>/screen_today.json + a markdown table on stdout.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

import requests

from . import sources as S
from aiinvest import ai_stack, physical_ai_stack, quantum_stack

ROOT = pathlib.Path(__file__).resolve().parents[2]
DAY = "2026-09-25"
D = ROOT / "data" / "bumper" / DAY
EFTS = "https://efts.sec.gov/LATEST/search-index"
COLS = ["name", "description", "industry", "market_cap_basic", "total_revenue_ttm", "total_revenue_yoy_growth_ttm",
        "research_and_dev_ttm", "free_cash_flow_ttm", "cash_n_short_term_invest_fq", "total_debt_fq", "gross_margin_ttm",
        "net_income_ttm", "Perf.Y", "Perf.6M", "float_shares_percent_current", "number_of_employees"]
US = {"NYSE", "NASDAQ", "AMEX"}


def universe():
    out = {}
    for tag, mod in [("AI stack", ai_stack), ("quantum", quantum_stack), ("physical AI", physical_ai_stack)]:
        for layer, names in mod.LAYERS.items():
            for t in names:
                t = t if isinstance(t, str) else t[0]
                if t.split(":")[0] in US:
                    out[t] = (tag, layer)
    scan = json.load(open(ROOT / "data" / f"bumper_scan_{DAY}.json", encoding="utf-8"))
    for t in scan:
        out.setdefault(t, ("today-screen", "-"))
    return out


def fetch(tickers):
    payload = {"symbols": {"tickers": tickers, "query": {"types": []}}, "columns": COLS, "options": {"lang": "en"}}
    r = requests.post(S.SCAN, json=payload, headers={"User-Agent": S.UA}, timeout=60)
    r.raise_for_status()
    rows = {}
    for x in r.json().get("data", []):
        rows[x["s"]] = dict(zip(COLS, x["d"]))
    return rows


def efts_hits(cik, q, forms, days=365):
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    params = {"q": q, "ciks": f"{cik:010d}", "forms": ",".join(forms), "dateRange": "custom",
              "startdt": start.isoformat(), "enddt": end.isoformat()}
    r = requests.get(EFTS, params=params, headers={"User-Agent": S.SEC_UA}, timeout=60)
    S.polite(0.2)
    if r.status_code != 200:
        return None, []
    j = r.json()
    hits = j.get("hits", {}).get("hits", [])
    docs = [{"form": h["_source"].get("form"), "filed": h["_source"].get("file_date"), "id": h["_id"]} for h in hits[:5]]
    return j.get("hits", {}).get("total", {}).get("value", len(hits)), docs


def main():
    uni = universe()
    rows = fetch(sorted(uni))
    out, stamp = [], S.now()
    for t, (tag, layer) in sorted(uni.items()):
        v = rows.get(t)
        if not v:
            out.append({"ticker": t, "sector": tag, "layer": layer, "stage": "no data"})
            continue
        cap, fcf, cash, rev, rd = v["market_cap_basic"], v["free_cash_flow_ttm"], v["cash_n_short_term_invest_fq"], v["total_revenue_ttm"], v["research_and_dev_ttm"]
        rec = {"ticker": t, "name": v["description"], "sector": tag, "layer": layer, "industry": v["industry"], "market_cap_usd": cap,
               "fcf_ttm": fcf, "cash": cash, "revenue_ttm": rev, "rev_growth_yoy": v["total_revenue_yoy_growth_ttm"],
               "rnd_to_rev": (abs(rd) / rev if rev and rd is not None else None), "gross_margin": v["gross_margin_ttm"],
               "perf_1y": v["Perf.Y"], "employees": v["number_of_employees"], "retrieved_at": stamp,
               "source": "TradingView scanner /america/scan", "source_class": "api"}
        rec["runway_years"] = (cash / -fcf) if (fcf is not None and fcf < 0 and cash) else None
        # stage 1: universe
        if cap is None or not (5e7 <= cap <= 3e9):
            rec["stage"] = "outside universe"
            rec["why"] = f"cap {cap / 1e9:.1f}B not in $50M-$3B" if cap else "no cap"
        elif fcf is None or fcf >= 0:
            rec["stage"] = "outside universe"
            rec["why"] = "already FCF-positive (not pre-profit)" if fcf is not None else "no FCF"
        else:
            rec["stage"] = "in universe"
        out.append(rec)
    # stage 2 gates, only for names in the universe (SEC full-text search, one CIK at a time)
    for rec in out:
        if rec.get("stage") != "in universe":
            continue
        reasons = []
        if rec["runway_years"] is not None and rec["runway_years"] < 2:
            reasons.append(f"runway {rec['runway_years']:.1f}y < 2y")
        cik = S.cik_for(rec["ticker"].split(":")[-1])
        rec["cik"] = cik
        if cik:
            n, docs = efts_hits(cik, '"substantial doubt" "going concern"', ["10-K", "10-Q", "20-F"])
            rec["going_concern_hits"], rec["going_concern_docs"] = n, docs
            if n:
                reasons.append(f"going-concern language in {n} filing(s) last 12m")
            n2, docs2 = efts_hits(cik, '"minimum bid price" OR "Listing Rule 5550" OR "Listing Rule 5450" OR "notice of noncompliance"', ["8-K"])
            rec["listing_notice_hits"], rec["listing_notice_docs"] = n2, docs2
            if n2:
                reasons.append(f"exchange listing notice in {n2} 8-K(s) last 12m")
        else:
            rec["going_concern_hits"] = rec["listing_notice_hits"] = None
            reasons.append("no CIK found (text gates not run)")
        rec["stage"] = "DISQUALIFIED" if reasons else "not disqualified (numeric + text gates)"
        rec["why"] = "; ".join(reasons) if reasons else "runway >= 2y, no going-concern language, no listing notice"
        rec["binding_demand"] = "UNVERIFIED"
    (D / "screen_today.json").write_text(json.dumps({"generated_at": stamp, "gates_run": ["universe", "runway", "going_concern", "listing_notice"],
                                                     "gates_not_run": ["binding_demand", "dilution_buyer", "13D", "governance", "5.02_departures", "judge"],
                                                     "rows": out}, indent=1), encoding="utf-8")
    # stdout table
    def f(x, nd=1, mult=1, suf=""):
        return "-" if x is None else f"{x * mult:.{nd}f}{suf}"
    for stage in ["not disqualified (numeric + text gates)", "DISQUALIFIED"]:
        print(f"\n## {stage}")
        print("| ticker | sector | cap $B | runway y | R&D/rev | rev growth | 1y perf | why |\n|---|---|---|---|---|---|---|---|")
        for r in sorted([r for r in out if r.get("stage") == stage], key=lambda r: r["market_cap_usd"] or 0, reverse=True):
            print(f"| {r['ticker']} | {r['sector']} {r['layer']} | {f(r['market_cap_usd'], 2, 1e-9)} | {f(r['runway_years'])} | {f(r['rnd_to_rev'], 2)} | "
                  f"{f(r['rev_growth_yoy'], 0, 1, '%')} | {f(r['perf_1y'], 0, 1, '%')} | {r['why']} |")
    n_out = sum(r.get("stage") == "outside universe" for r in out)
    print(f"\nuniverse {len(out)} names: {n_out} outside ($50M-$3B pre-profit), "
          f"{sum(r.get('stage') == 'DISQUALIFIED' for r in out)} disqualified, "
          f"{sum(r.get('stage', '').startswith('not disq') for r in out)} not disqualified, {sum(r.get('stage') == 'no data' for r in out)} no data")


if __name__ == "__main__":
    main()
