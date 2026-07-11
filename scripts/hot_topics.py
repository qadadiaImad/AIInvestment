"""CLI: rank the hottest tickers + themes of the last N days from the local bundles.

Usage:  python hot_topics.py [--days 30] [--top 15] [--json]
Reads web/public/data/{news,congress,site,quantum}.json (refresh first for live data).
Educational only — not investment advice. Congress rows are public record, not signals.
"""
import argparse, json, pathlib
from datetime import datetime, timezone
from aiinvest.hot_topics import rank_hot, top_themes

def _load(base, name):
    return json.loads((pathlib.Path(base) / name).read_text(encoding="utf-8"))

def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--data-dir", default="../web/public/data")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    news, cong = _load(a.data_dir, "news.json"), _load(a.data_dir, "congress.json")
    rows = {}
    for name in ("site.json", "quantum.json"):
        b = _load(a.data_dir, name)
        for r in b.get("screener") or []:
            tk = r.get("symbol") or r.get("ticker")
            if tk:
                rows.setdefault(tk, r)
    now = datetime.now(timezone.utc)
    ranked = rank_hot(news.get("articles"), cong.get("trades"), rows, days=a.days, now=now, top=a.top)
    themes = top_themes(news.get("articles"), days=a.days, now=now, top=10)
    stamp = f"window={a.days}d retrieved_at={now.strftime('%Y-%m-%dT%H:%M:%SZ')} " \
            f"news_generated_at={news.get('generated_at')} congress_generated_at={cong.get('generated_at')}"
    if a.json:
        print(json.dumps({"stamp": stamp, "hot": ranked, "themes": themes}, indent=2))
        return
    print(f"HOT TOPICS - last {a.days} days   ({stamp})")
    print(f"{'#':>2} {'TICKER':7} {'SCORE':>8} {'ARTS':>4} {'PERF1Y':>8} {'LAYER':14} CONGRESS / TOP HEADLINE")
    for i, r in enumerate(ranked, 1):
        perf = f"{r['perf_1y']:+.0f}%" if isinstance(r["perf_1y"], (int, float)) else "n/a"
        cg = ""
        if r["congress"]:
            c = r["congress"]
            cg = f"[congress: {c['n_filings']} filing(s) >= ${c['max_amount_low']:,} - public record, not a signal] "
        print(f"{i:>2} {r['ticker']:7} {r['score']:>8.1f} {r['n_articles']:>4} {perf:>8} "
              f"{(r['layer'] or '-'):14} {cg}{(r['top_headline'] or '')[:80]}")
    print("\nTHEMES: " + ", ".join(f"{t['term']}({t['count']})" for t in themes))
    print("Educational only — not investment advice. Congress data = public record, dated, not accusations.")

if __name__ == "__main__":
    main()
