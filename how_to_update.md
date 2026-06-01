# How to update AIInvestment

How the data refreshes and the live site rebuilds. **The scripts do everything end-to-end —
no agent (Claude) is required to update the data or the web app.** An agent is only for
optional, qualitative work (see §4).

Educational/research only — not investment advice.

---

## 1. The two commands

```bash
cd scripts

# DAILY — fundamentals, prices, graph, resiliency, screener, news  (+ rebuild & ship)
python refresh_daily.py --deploy

# MONTHLY — congressional trades + party/ideology/policy enrichment  (+ rebuild & ship)
python refresh_congress.py --deploy
```

`--deploy` runs `vercel --prod --yes` from `web/` at the end, which makes Vercel **rebuild
every page from the freshly-written JSON** and publish it. Omit `--deploy` to refresh the
local data only (inspect before shipping).

Other flags: `--dry-run` (print the plan, run nothing), `--keep-going` (don't abort on a
failed step), `--with-backtest` (daily only; include the heavy `/strategies` backtest, off by
default).

---

## 2. What `refresh_daily.py` refreshes (and which page it feeds)

Ordered pipeline (each step a subprocess):

| # | Step | Writes | Page(s) |
|---|------|--------|---------|
| 1 | `pull_ai_stack.py` | AI-stack fundamentals incl. `fundamental_value` | `/`, `/stocks/[t]`, `/screener` |
| 2 | `pull_prices.py` | 5y daily prices | `/stocks/[t]`, `/strategies` |
| 3 | `merge_enriched.py` | validated AI-extracted relationship edges | `/map` |
| 4 | `build_capital_web.py` | capital-web graph (curated + enriched) | `/map` |
| 5 | `run_graph_analysis.py` | `graph_analysis.json` — health, SPOFs, macro stress, edge stress, cascades, **fed_path**, **vulnerability** | `/resiliency`, `/map` |
| 6 | `run_backtest.py` *(only with `--with-backtest`)* | `backtests.json` | `/strategies` |
| 7 | `export_site.py` | `site.json` (the main bundle) | `/`, `/stocks/[t]`, `/map` |
| 8 | `build_screener.py` | screener bundle | `/screener` |
| 9 | `pull_news.py` | `news.json` — news for all ~1,251 tickers (108 AI ∪ congress), ticker-tagged, certainty-labeled, graph-linked + candidate-edge queue | `/news` |
| 10 | `vercel --prod` *(only with `--deploy`)* | — | rebuilds & ships the whole site |

**News transport:** Yahoo keyless RSS by default; set `FINNHUB_API_KEY` in the environment to
upgrade to Finnhub's categorized company news automatically.

---

## 3. What `refresh_congress.py` refreshes (separate, monthly)

PTR filings move slowly, so congress is **not** in the daily script.

| # | Step | Writes |
|---|------|--------|
| 1–2 | `pull_congress.py --year 2025 / 2026` | `data/congress/house_{year}.json` (House STOCK Act PTRs) |
| 3 | `pull_conflict.py` | `conflict_signals.json` (correlational committee/sector overlap) |
| 4 | `pull_member_profiles.py` | `member_profiles.json` (party, **DW-NOMINATE ideology** via Voteview, **policy areas** via committee jurisdiction; sponsored bills if `CONGRESS_GOV_API_KEY` set) |
| 5 | `export_congress.py` | `congress.json` | `/congress` |
| 6 | `vercel --prod` *(only with `--deploy`)* | rebuilds & ships |

Optional keys: `FINNHUB_API_KEY` (richer `/news`), `CONGRESS_GOV_API_KEY` (sponsored-bills
layer on `/congress`). Both are picked up automatically when present; absent, the feature
degrades gracefully and says so.

---

## 4. Where an agent (Claude) fits — optional, qualitative only

The refresh scripts produce data **and** ship the site by themselves. Ask an agent only for
work that is not scriptable:

- **Narrative analysis** — "what changed and why does it matter" write-ups.
- **Relationship discovery** — reading filings/news to find *new* `/map` edges
  (the `edge-enricher` workflow) and curating them into `capital_web`.
- **Reviewing the news candidate-edge queue** — `/news` flags possible new deals as
  `unverified`; an agent decides which to promote into the graph (never auto-added).

```
DAILY:     python refresh_daily.py --deploy      # data + site — automatic, no agent
MONTHLY:   python refresh_congress.py --deploy    # congress    — automatic, no agent
ON DEMAND: ask Claude to analyze / curate edges   # agent only  — optional, qualitative
```

> Caveat: `vercel --prod` rebuilds pages from whatever JSON is on disk at deploy time — it
> does **not** itself re-pull data. The pulling is the script's earlier steps; the deploy just
> bundles the result. Always run the pull steps (the script does) before/with `--deploy`.

---

## 5. Scheduling (optional)

To run unattended on Windows, register two Task Scheduler jobs:

```powershell
# Daily at 06:00
schtasks /Create /TN "AIInvest-Daily" /SC DAILY /ST 06:00 ^
  /TR "cmd /c cd /d C:\Users\imadq\AIInvestment\scripts && python refresh_daily.py --deploy"

# Monthly on the 1st at 07:00
schtasks /Create /TN "AIInvest-Congress" /SC MONTHLY /D 1 /ST 07:00 ^
  /TR "cmd /c cd /d C:\Users\imadq\AIInvestment\scripts && python refresh_congress.py --deploy"
```
