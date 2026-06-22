"""pull_news.py — pull company news across the universe -> web/public/data/news.json.

REST-first per CLAUDE.md, Mode A (keyed JSON API / ungated RSS). Pipeline:

    1. assemble the universe = union(site.json stocks keys, congress.json distinct
       tickers), bare-symbolled (NYSE:VST -> VST).
    2. build a name_index from the capital-web nodes (id / name / ticker aliases) so
       entities like ``anthropic``, ``openai``, ``GOOGL`` tag in headlines.
    3. per ticker: Finnhub company-news IF FINNHUB_API_KEY is set, else Yahoo keyless
       RSS. Parse -> aiinvest.news.normalize_article (stamp + tag + certainty) ->
       aiinvest.news_graph.annotate (curated graph_edges + candidate_edges).
    4. per-ticker cap = top 10 most-recent; global dedupe by URL; sort published desc.
    5. write the page-ready contract with HONEST coverage (covered/requested) and the
       list of http_failed tickers.

Honesty rails (spec section 5):
- Every article stamped retrieved_at (UTC ISO) / source / published / source_class
  (news-api | news-rss). Certainty labelled filed / reported / rumored (brief Rule #5).
- Graph-edge badges carry the CURATED edge's own certainty + source_url (never upgraded).
- Candidate edges are ALWAYS unverified=true and are NEVER auto-added to the graph.
- Coverage reported honestly; no fabricated articles or links.

Runs cleanly with NO FINNHUB_API_KEY (key_mode 'yahoo', source_class 'news-rss').

Usage:
    python pull_news.py                          # full universe, Yahoo unless key set
    python pull_news.py --limit 20               # debug: first 20 tickers
    python pull_news.py --window-days 7 --delay 0.3
    python pull_news.py --out ../web/public/data/news.json

Educational/research only -- not investment advice.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import time

import requests

from aiinvest import news, news_graph

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SITE_PATH = REPO / "web" / "public" / "data" / "site.json"
CONGRESS_PATH = REPO / "web" / "public" / "data" / "congress.json"
OUT_PATH = REPO / "web" / "public" / "data" / "news.json"

_UA = ("AIInvestment-research/1.0 (educational; data-acquisition; "
       "contact easyresumeai@outlook.fr)")

_FINNHUB_URL = "https://finnhub.io/api/v1/company-news"
_YAHOO_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"

_PER_TICKER_CAP = 10
_FINNHUB_DELAY = 1.1   # ~55/min, under the 60/min free limit
_YAHOO_DELAY = 0.2

_DISCLAIMER = (
    "Educational/research only -- not investment advice. News is labelled "
    "filed / reported / rumored; a rumor is never laundered into a fact. "
    "Candidate edges are unverified and are NOT in the graph -- they are "
    "surfaced only for /map review."
)


def _utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_universe(site_doc, congress_doc):
    """union(site.json stocks keys, congress.json distinct tickers) -> sorted bare symbols."""
    syms = set()
    for k in (site_doc.get("stocks") or {}).keys():
        b = news.bare_symbol(k)
        if b:
            syms.add(b)
    for t in (congress_doc.get("trades") or []):
        b = news.bare_symbol(t.get("ticker"))
        if b:
            syms.add(b)
    return sorted(syms)


def build_name_index(site_doc):
    """Build {alias_lower: label} from capital-web nodes (id / name / bare ticker)."""
    nodes = ((site_doc.get("capital_web") or {}).get("nodes")) or []
    aliases = {}
    for n in nodes:
        label = n.get("id") or n.get("name")
        if not label:
            continue
        al = aliases.setdefault(label, set())
        if n.get("id"):
            al.add(n["id"])
        if n.get("name"):
            al.add(n["name"])
        bt = news.bare_symbol(n.get("ticker"))
        if bt:
            al.add(bt)
    # Drop common-word / too-short aliases (e.g. "AI", "ON", "SO") that would
    # false-tag free text; the queried ticker is still tagged directly downstream.
    return news.build_name_index(
        {k: sorted(a for a in v if news.is_safe_alias(a)) for k, v in aliases.items()})


def _published_key(article):
    """Sort key: ISO published descending (None last)."""
    p = article.get("published")
    return p or ""


def fetch_finnhub(symbol, api_key, window_days, session):
    """GET Finnhub company-news for `symbol`. Returns (raw_items, ok). ok=False on HTTP error."""
    to = datetime.date.today()
    frm = to - datetime.timedelta(days=window_days)
    params = {
        "symbol": symbol,
        "from": frm.isoformat(),
        "to": to.isoformat(),
        "token": api_key,
    }
    try:
        r = session.get(_FINNHUB_URL, params=params, timeout=20)
        if r.status_code != 200:
            return [], False
        return news.parse_finnhub(r.json()), True
    except (requests.RequestException, ValueError):
        return [], False


def fetch_yahoo(symbol, session):
    """GET Yahoo keyless headline RSS for `symbol`. Returns (raw_items, ok)."""
    params = {"s": symbol, "region": "US", "lang": "en-US"}
    try:
        r = session.get(_YAHOO_URL, params=params, timeout=20)
        if r.status_code != 200:
            return [], False
        return news.parse_yahoo_rss(r.text), True
    except requests.RequestException:
        return [], False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull company news across the universe.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Debug: only process the first N tickers.")
    ap.add_argument("--window-days", type=int, default=14,
                    help="Look-back window for Finnhub (default 14).")
    ap.add_argument("--delay", type=float, default=None,
                    help="Seconds between requests (default: API-appropriate).")
    ap.add_argument("--out", default=str(OUT_PATH), help="Output path for news.json.")
    args = ap.parse_args(argv)

    api_key = os.environ.get("FINNHUB_API_KEY")
    key_mode = "finnhub" if api_key else "yahoo"
    source_class = "news-api" if api_key else "news-rss"
    source_label = "finnhub.io company-news" if api_key else "Yahoo Finance RSS"
    delay = args.delay if args.delay is not None else (
        _FINNHUB_DELAY if api_key else _YAHOO_DELAY)

    site_doc = _load_json(SITE_PATH)
    congress_doc = _load_json(CONGRESS_PATH) if os.path.exists(str(CONGRESS_PATH)) else {}
    universe = build_universe(site_doc, congress_doc)
    name_index = build_name_index(site_doc)
    edge_index = news_graph.build_edge_index(
        ((site_doc.get("capital_web") or {}).get("edges")) or [])

    n_requested = len(universe)
    if args.limit is not None:
        universe = universe[:args.limit]

    print(f"news pull: key_mode={key_mode} source_class={source_class} "
          f"tickers={len(universe)}/{n_requested} window_days={args.window_days}")

    session = requests.Session()
    session.headers.update({"User-Agent": _UA})

    all_articles = []
    http_failed = []
    covered = set()

    for i, sym in enumerate(universe, 1):
        if api_key:
            raw_items, ok = fetch_finnhub(sym, api_key, args.window_days, session)
        else:
            raw_items, ok = fetch_yahoo(sym, session)
        if not ok:
            http_failed.append(sym)
            time.sleep(delay)
            continue

        retrieved_at = _utc_now_iso()
        arts = []
        for raw in raw_items:
            art = news.normalize_article(raw, retrieved_at, name_index)
            art["source_class"] = source_class  # api vs rss (override html default)
            if not art.get("source"):
                art["source"] = source_label
            # ensure THIS ticker is tagged even if no alias matched the headline text
            if sym not in art["tickers"]:
                art["tickers"] = sorted(set(art["tickers"]) | {sym})
            art = news_graph.annotate(art, edge_index)
            arts.append(art)

        # per-ticker cap: top N most-recent
        arts.sort(key=_published_key, reverse=True)
        arts = arts[:_PER_TICKER_CAP]
        if arts:
            covered.add(sym)
        all_articles.extend(arts)

        if i % 100 == 0:
            print(f"  ... {i}/{len(universe)} tickers, {len(all_articles)} articles so far")
        time.sleep(delay)

    # global dedupe by URL, then sort published desc
    articles = news.dedupe(all_articles)
    articles.sort(key=_published_key, reverse=True)

    # collect candidate edges across all articles (the review queue)
    candidate_edges = []
    cand_seen = set()
    for a in articles:
        for c in a.get("candidate_edges") or []:
            mk = (c.get("src"), c.get("dst"), c.get("url"))
            if mk in cand_seen:
                continue
            cand_seen.add(mk)
            candidate_edges.append(c)

    out = {
        "generated_at": _utc_now_iso(),
        "key_mode": key_mode,
        "source_class": source_class,
        "n_tickers_requested": n_requested,
        "n_tickers_covered": len(covered),
        "n_articles": len(articles),
        "http_failed": http_failed,
        "disclaimer": _DISCLAIMER,
        "window_days": args.window_days,
        "articles": articles,
        "candidate_edges": candidate_edges,
    }

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"wrote {out_path}")
    print(f"articles={out['n_articles']} covered={out['n_tickers_covered']}/{n_requested} "
          f"http_failed={len(http_failed)} candidate_edges={len(candidate_edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
