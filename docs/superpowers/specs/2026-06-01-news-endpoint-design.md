# /news endpoint + graph linkage — design

**Date:** 2026-06-01  **Status:** approved (brainstorming gate passed)
**Owner decisions:** (1) transport = **Finnhub** company-news (free key) primary, **Yahoo keyless RSS**
fallback when no key; (2) coverage = **everything daily** (all 1,251 tickers); (3) linkage = **annotate
existing capital-web edges + flag candidate NEW deals into a review queue** for `/map` (never auto-added).

Educational/research only — not investment advice. Label **filed / reported / rumored**; never launder a
rumor into a fact (brief Rule #5).

## 1. Universe
`union(site.json stocks keys = 108 AI, congress.json distinct tickers = 1,235) = 1,251` bare symbols.
Strip exchange prefixes (`NYSE:VST`→`VST`). Both Finnhub and Yahoo take bare symbols.

## 2. Sources (verified live 2026-06-01)
- **Finnhub** (primary, needs `FINNHUB_API_KEY`): `GET https://finnhub.io/api/v1/company-news?symbol={S}&from={YYYY-MM-DD}&to={YYYY-MM-DD}&token={KEY}` → `[{category,datetime(epoch),headline,id,related,source,summary,url}]`. 401 without key (confirmed). 60 req/min.
- **Yahoo** (keyless fallback): `GET https://feeds.finance.yahoo.com/rss/2.0/headline?s={S}&region=US&lang=en-US` → RSS `<item>{title,link,pubDate,description}`. Confirmed 20 items/NVDA.
- Pick per run: `key_mode = "finnhub" if FINNHUB_API_KEY else "yahoo"`. Stamp each article's `source`/`source_class` accordingly (`news-api` vs `news-rss`).

## 3. Code units (TDD, pure-first)

### 3.1 `scripts/aiinvest/news.py` (extend; keep pure)
Existing: `classify_certainty`, `build_name_index`, `tag_entities`, `normalize_article`, `dedupe`. Add:
- `parse_finnhub(items) -> [raw{title,url,source,published(ISO from epoch),summary}]`
- `parse_yahoo_rss(xml_text) -> [raw{...}]` (stdlib `xml.etree`; tolerate missing fields)
- `bare_symbol(ticker) -> str` (strip `EXCH:` prefix, upper)

### 3.2 `scripts/aiinvest/news_graph.py` (NEW, pure)
- `build_edge_index(edges) -> {frozenset({src,dst}): [edge,...]}` plus a directed map for badge direction.
- `link_article(tagged_entities, edge_index) -> [graph_edge_ref]` where ref =
  `{src,dst,type,attrs,certainty,source_url,as_of}` from the matched curated edge (certainty NOT upgraded).
- `DEAL_KEYWORDS` (supply, deal, invest, stake, partnership, contract, agreement, acquire, commitment, …).
- `detect_candidate_edges(tagged_entities, title_summary, edge_index) -> [candidate]` where candidate =
  `{src,dst,type_guess,evidence_title,certainty('reported'|'rumored'),url,detected_at}` — ONLY when ≥2
  distinct entities are tagged, a deal keyword is present, AND no curated edge already exists for that pair.
  Always `unverified=true`. Never asserts a relationship.
- `annotate(article, edge_index) -> article + {graph_edges:[...], candidate_edges:[...]}`.

### 3.3 `scripts/pull_news.py` (CLI)
Assemble universe (site.json + congress.json). Build name_index from capital-web nodes
(id/name/ticker aliases) so entities like `anthropic`,`openai`,`GOOGL` tag. Per ticker: Finnhub (if key)
else Yahoo → parse → `normalize_article` (stamp+tag+certainty) → `annotate`. Per-ticker cap = top 10
recent; global `dedupe` by URL; sort published desc. Polite throttle (Finnhub ≤60/min; Yahoo small delay).
Honest coverage: count `http_failed`. Write `web/public/data/news.json`:
```json
{ "generated_at": "<UTC>", "key_mode": "finnhub|yahoo", "source_class": "news-api|news-rss",
  "n_tickers_requested": 1251, "n_tickers_covered": 0, "n_articles": 0, "http_failed": [],
  "disclaimer": "<educational; filed/reported/rumored; candidate edges unverified>",
  "window_days": 14,
  "articles": [ {"title","url","source","published","summary","tickers":[...],"certainty",
                 "retrieved_at","source_class","graph_edges":[...],"candidate_edges":[...]} ],
  "candidate_edges": [ {src,dst,type_guess,evidence_title,certainty,url,detected_at,unverified:true} ] }
```
Flags: `--limit` (debug), `--window-days` (default 14), `--delay`, `--out`.

### 3.4 `scripts/refresh_daily.py`
Add a guarded `pull_news.py` step (after `build_screener`). Update `build_plan` (+ test if present).

## 4. Web
- `web/lib/news.ts` (client-safe): `NewsArticle`, `GraphEdgeRef`, `CandidateEdge` types; `certaintyMeta(c)`
  (label+color for filed/reported/rumored); `edgeBadge(ref)` (e.g. `compute_commitment · $40B · reported`).
- `web/lib/data.ts`: `getNewsData()` loader (build-time fs, like getCongressData).
- `web/app/news/page.tsx` (server): load news.json; header strip (n_articles, coverage n/1251, key_mode,
  window); disclaimer banner; render `<NewsInteractive>`; a **"Candidate edges from news (unverified —
  review for /map)"** section listing `candidate_edges` (clearly labeled not-yet-in-graph).
- `web/components/NewsInteractive.tsx` (client): searchable/filterable feed (by ticker, by certainty, and a
  "graph-linked only" toggle), paginated. Each item: title→source link, source, date, certainty chip, ticker
  chips (→`/stocks/{t}`), and **graph-edge badges** (`A→B · type · deal terms · certainty`, link to `/map`),
  plus a candidate-edge flag when present ("possible new deal · unverified").
- `web/components/Header.tsx`: add `{ href: "/news", label: "NEWS" }`.

## 5. Honesty / legal rails
- Every article stamped (retrieved_at, source, published, source_class). Certainty filed/reported/rumored.
- Candidate edges are ALWAYS `unverified:true`, certainty reported|rumored, **never auto-added to the graph**;
  page copy says "candidate — review for /map," educational only.
- Graph-edge badges carry the curated edge's OWN certainty + source_url; do not upgrade certainty from news.
- Coverage reported honestly (covered/requested, http_failed). No fabricated articles/links.
- Disclaimer: educational/research only, not investment advice.

## 6. Testing (TDD)
- `scripts/tests/test_news.py` (extend): parse_finnhub (epoch→ISO), parse_yahoo_rss (missing fields),
  bare_symbol, certainty, dedupe.
- `scripts/tests/test_news_graph.py` (new): build_edge_index, link_article (match + direction),
  detect_candidate_edges (fires only with ≥2 entities + deal keyword + no existing edge; suppressed when
  edge exists), annotate shape.
- `scripts/tests/test_refresh.py` (extend if refresh_daily.build_plan is tested): news step ordering.

## 7. Orchestration
Workflow, disjoint slices coded against this contract concurrently:
- **NEWS-CORE**: news.py extend + news_graph.py + pull_news.py + refresh_daily step + the two test files (TDD).
- **WEB-NEWS**: news.ts + data.ts loader + /news page + NewsInteractive + Header link.
Then verify (pytest + tsc). Integration (run `pull_news.py` over 1,251 tickers — Yahoo keyless since no
Finnhub key — then `next build`) + final `vercel --prod` done by the orchestrator.
