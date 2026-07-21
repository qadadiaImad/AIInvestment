"""Rank the hottest tickers/topics of the last N days from the local data bundles.

Inputs are the already-refreshed bundles (news.json articles, congress.json trades,
site/quantum screener rows) — no network calls. Congress data is public record,
dated; it boosts attention scoring only and is never framed as a signal.
"""
import math, re
from datetime import datetime, timezone, timedelta

_STOP = set("""a an and are as at be but by for from has have in into is it its of on or
reportedly says stock stocks shares this that the their these to vs was were will with
after amid over under new q1 q2 q3 q4 nyse nasdaq inc corp plc co what why how here
top best buy sell hold now today week month year""".split())

def parse_when(s):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        mo, d, y = (int(g) for g in m.groups())
        try:
            return datetime(y, mo, d, tzinfo=timezone.utc)
        except ValueError:
            return None
    return None

def _in_window(dt, now, days):
    return dt is not None and timedelta(0) <= (now - dt) <= timedelta(days=days)

def rank_hot(articles, trades, rows_by_ticker, days=30, now=None, top=15):
    now = now or datetime.now(timezone.utc)
    per = {}
    for a in articles or []:
        dt = parse_when((a or {}).get("published"))
        if not _in_window(dt, now, days):
            continue
        recency = 1.0 + (days - (now - dt).days) / days  # 1x (old) .. 2x (fresh)
        for tk in (a.get("tickers") or []):
            e = per.setdefault(tk, {"news_score": 0.0, "n_articles": 0, "latest": None, "top_headline": None})
            e["news_score"] += recency
            e["n_articles"] += 1
            if e["latest"] is None or dt > e["latest"]:
                e["latest"], e["top_headline"] = dt, a.get("title")
    cong = {}
    for t in trades or []:
        tk = (t or {}).get("ticker")
        dt = parse_when((t or {}).get("filing_date")) or parse_when((t or {}).get("txn_date"))
        low = t.get("amount_range_low") if isinstance(t.get("amount_range_low"), (int, float)) else 0
        if not tk or not _in_window(dt, now, days) or low < 15001:  # material, in-window filings only
            continue
        c = cong.setdefault(tk, {"n_filings": 0, "max_amount_low": 0, "politicians": set()})
        c["n_filings"] += 1
        c["max_amount_low"] = max(c["max_amount_low"], low)
        if t.get("politician"):
            c["politicians"].add(t["politician"])
    out = []
    for tk in set(per) | set(cong):
        e = per.get(tk, {"news_score": 0.0, "n_articles": 0, "latest": None, "top_headline": None})
        row = (rows_by_ticker or {}).get(tk) or {}
        perf = row.get("perf_1y") if isinstance(row.get("perf_1y"), (int, float)) else 0.0
        c = cong.get(tk)
        boost = (2.0 + math.log10(max(c["max_amount_low"], 10)) + c["n_filings"]) if c else 0.0
        score = e["news_score"] * (1.0 + min(abs(perf), 1000) / 100.0) + boost
        out.append({
            "ticker": tk, "score": round(score, 2), "n_articles": e["n_articles"],
            "top_headline": e["top_headline"],
            "latest_article": e["latest"].isoformat() if e["latest"] else None,
            "congress": ({"n_filings": c["n_filings"], "max_amount_low": c["max_amount_low"],
                          "politicians": sorted(c["politicians"])} if c else None),
            "perf_1y": row.get("perf_1y"), "layer": row.get("layer"),
        })
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:top]

def top_themes(articles, days=30, now=None, top=10):
    now = now or datetime.now(timezone.utc)
    counts = {}
    for a in articles or []:
        if not _in_window(parse_when((a or {}).get("published")), now, days):
            continue
        for w in re.findall(r"[a-z][a-z\-]{3,}", (a.get("title") or "").lower()):
            if w not in _STOP:
                counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top]
    return [{"term": w, "count": n} for w, n in ranked]
