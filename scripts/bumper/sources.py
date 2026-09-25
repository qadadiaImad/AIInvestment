"""Network layer for the bumper study: TradingView scanner cohorts, Yahoo monthly closes,
SEC XBRL company facts. Every record carries retrieved_at + source_url (CLAUDE.md rule 3)."""
from __future__ import annotations

import datetime
import json
import pathlib
import time

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SEC_UA = "AIInvestment research (easyresumeai@outlook.fr)"
SCAN = "https://scanner.tradingview.com/america/scan"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=6y&interval=1mo"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

COLS = ["name", "description", "sector", "industry", "market_cap_basic", "Perf.5Y", "Perf.3Y",
        "Perf.Y", "total_revenue_ttm", "ipo_offer_date", "exchange", "type", "subtype"]


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan(filters, limit=500, sort_by="market_cap_basic"):
    payload = {"filter": filters, "options": {"lang": "en"}, "symbols": {"query": {"types": []}},
               "columns": COLS, "sort": {"sortBy": sort_by, "sortOrder": "desc"}, "range": [0, limit]}
    r = requests.post(SCAN, json=payload, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    rows = []
    for x in r.json().get("data", []):
        rec = dict(zip(COLS, x["d"]))
        rec["ticker"] = x["s"]
        rec["symbol"] = x["s"].split(":")[-1]
        rows.append(rec)
    return rows


def winners(min_5y_pct=400, min_3y_pct=200, min_cap=1e9):
    """US-exchange names that multiplied >= 5x over 5y OR >= 3x over 3y, cap >= $1B today."""
    base = [{"left": "market_cap_basic", "operation": "greater", "right": min_cap},
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "subtype", "operation": "in_range", "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range", "right": ["NYSE", "NASDAQ", "AMEX"]}]
    a = scan(base + [{"left": "Perf.5Y", "operation": "greater", "right": min_5y_pct}])
    b = scan(base + [{"left": "Perf.3Y", "operation": "greater", "right": min_3y_pct}])
    seen, out = set(), []
    for rec in a + b:
        if rec["ticker"] in seen:
            continue
        seen.add(rec["ticker"])
        out.append(rec)
    return out


def controls(industries, min_cap=2e8, max_cap=5e9, max_5y_pct=100, limit=600):
    """Same-industry names that did NOT multiply: -80% .. +100% over 5y, cap $0.2-5B."""
    filters = [{"left": "market_cap_basic", "operation": "in_range", "right": [min_cap, max_cap]},
               {"left": "type", "operation": "equal", "right": "stock"},
               {"left": "subtype", "operation": "in_range", "right": ["common", "foreign-issuer"]},
               {"left": "exchange", "operation": "in_range", "right": ["NYSE", "NASDAQ", "AMEX"]},
               {"left": "Perf.5Y", "operation": "in_range", "right": [-80, max_5y_pct]},
               {"left": "industry", "operation": "in_range", "right": sorted(industries)}]
    return scan(filters, limit=limit)


def yahoo_monthly(symbol, session=None):
    """[(YYYY-MM, close)] ascending, adjusted closes when available."""
    http = session or requests
    r = http.get(YAHOO.format(sym=symbol), headers={"User-Agent": UA}, timeout=30)
    if r.status_code != 200:
        return None
    res = (r.json().get("chart", {}).get("result") or [None])[0]
    if not res:
        return None
    ts = res.get("timestamp") or []
    ind = res.get("indicators", {})
    adj = (ind.get("adjclose") or [{}])[0].get("adjclose")
    raw = (ind.get("quote") or [{}])[0].get("close")
    closes = adj or raw or []
    out = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
        out.append((f"{d.year:04d}-{d.month:02d}", float(c)))
    # keep the last value per month label
    dedup = {}
    for k, v in out:
        dedup[k] = v
    return sorted(dedup.items())


_TICKER_MAP = None


def cik_for(symbol):
    global _TICKER_MAP
    if _TICKER_MAP is None:
        r = requests.get(SEC_TICKERS, headers={"User-Agent": SEC_UA}, timeout=30)
        r.raise_for_status()
        _TICKER_MAP = {v["ticker"].upper(): int(v["cik_str"]) for v in r.json().values()}
    return _TICKER_MAP.get(symbol.upper().replace(".", "-")) or _TICKER_MAP.get(symbol.upper())


# us-gaap concepts, in order of preference, per feature
CONCEPTS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "rnd": ["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"],
    "gross_profit": ["GrossProfit"],
    "ocf": ["NetCashProvidedByUsedInOperatingActivities"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "shares": ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic",
               "CommonStockSharesOutstanding"],
}
FLOW = {"revenue", "rnd", "gross_profit", "ocf"}


def companyfacts(cik):
    r = requests.get(SEC_FACTS.format(cik=cik), headers={"User-Agent": SEC_UA}, timeout=60)
    if r.status_code != 200:
        return None
    return r.json()


def quarterly_series(facts):
    """Turn a companyfacts payload into {feature: [(end, value)]} of QUARTERLY values.

    Flow concepts (revenue, R&D, OCF) are reported as YTD in 10-Qs and annual in 10-Ks; we
    keep only ~90-day periods (start->end <= 100 days) and derive Q4 = FY - 9M-YTD when a
    quarterly Q4 is absent. Stock concepts (cash, shares) are taken as reported per end date.
    """
    out = {}
    gaap = (facts or {}).get("facts", {}).get("us-gaap", {})
    for feat, names in CONCEPTS.items():
        pts = {}
        for name in names:
            units = gaap.get(name, {}).get("units", {})
            vals = units.get("USD") or units.get("shares") or []
            if not vals:
                continue
            for v in vals:
                end = v.get("end")
                val = v.get("val")
                if end is None or val is None:
                    continue
                if feat in FLOW:
                    start = v.get("start")
                    if not start:
                        continue
                    days = _days(start, end)
                    if days <= 100:
                        pts.setdefault(end, val)
                    elif 350 <= days <= 380 and v.get("fp") == "FY":
                        pts.setdefault(("FY", end), val)
                else:
                    pts.setdefault(end, val)
            if pts:
                break
        if feat in FLOW:
            # derive Q4 from FY minus the three quarterlies of that fiscal year
            fy = {e: val for (tag, e), val in [(k, v) for k, v in pts.items() if isinstance(k, tuple)]}
            q = {k: v for k, v in pts.items() if not isinstance(k, tuple)}
            for end, total in fy.items():
                if end in q:
                    continue
                y, m, d = map(int, end.split("-"))
                prior = [v for k, v in q.items() if _days(k, end) in range(60, 300)]
                if len(prior) == 3:
                    q[end] = total - sum(prior)
            pts = q
        out[feat] = sorted(pts.items())
    return out


def _days(a, b):
    ya, ma, da = map(int, a.split("-"))
    yb, mb, db = map(int, b.split("-"))
    return (datetime.date(yb, mb, db) - datetime.date(ya, ma, da)).days


def cache_json(path, producer):
    p = pathlib.Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    val = producer()
    if val is not None:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(val), encoding="utf-8")
    return val


def polite(seconds=0.15):
    time.sleep(seconds)
