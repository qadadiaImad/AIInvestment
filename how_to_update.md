# How to update AIInvestment

How the data refreshes and the live site rebuilds. **The scripts do everything end-to-end —
no agent (Claude) is required to update the data or the web app.** An agent is only for
optional, qualitative work (see §4).

Educational/research only — not investment advice.

---

## 0. Update EVERYTHING (the full "update all as of <date>" sequence)

```bash
cd scripts
# 1) scriptable refresh — run in order (no --deploy yet; one deploy at the end):
python refresh_daily.py              # AI fundamentals, prices, graph+resiliency, NEWS, QUANTUM, site, screener
python refresh_congress.py           # House PTR trades + conflict + party/ideology/policy
python pull_congress_stocks.py && python export_congress_stocks.py   # top-300 congress /stocks pages
python pull_kalray.py                # Kalray (+ any foreign names in pull_kalray.EXTRAS)

# 2) GF VALUES + GF HISTO — GATED, NOT scriptable. Ask Claude to run the Playwright-MCP
#    chart harvest (one fetch gives both the value and the historical series) for the full
#    universe, parse via aiinvest.fundamental.parse_valuation_chart, merge into
#    data/fundamental/<SYM>.json. See references/playwright-mcp-protocol.md (Mode B).

# 3) re-export so every bundle folds the fresh GF, then ship:
python export_site.py && python export_quantum.py && python export_congress_stocks.py && python pull_kalray.py
cd ../web && vercel --prod --yes
```
The GF step (2) is why there is no single command: the chart API blocks the local headless
path (403) and only the orchestrator-driven MCP browser gets through (Mode B, serial). Last
full run 2026-06-02: GF value 424 / series 404; 434 pages; site+congress stamped 06-02.

## 1. The two routine commands

```bash
cd scripts

# DAILY — fundamentals, prices, graph, resiliency, screener, news, quantum  (+ rebuild & ship)
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

Ordered pipeline (each step a subprocess; steps marked *conditional* are added by
`build_plan()` only when the corresponding script file exists on disk — a fresh clone
missing an optional script silently skips that step rather than failing):

| # | Step | Writes | Page(s) |
|---|------|--------|---------|
| 1 | `pull_ai_stack.py` | AI-stack fundamentals incl. `fundamental_value` | `/`, `/stocks/[t]`, `/screener` |
| 2 | `pull_prices.py` | 5y daily prices | `/stocks/[t]`, `/strategies` |
| 3 | `merge_enriched.py` | validated AI-extracted relationship edges | `/map` |
| 4 | `build_capital_web.py` | capital-web graph (curated + enriched) | `/map` |
| 5 | `run_graph_analysis.py` | `graph_analysis.json` — health, SPOFs, macro stress, edge stress, cascades, **fed_path**, **vulnerability** | `/resiliency`, `/map` |
| 6 | `build_chokepoints.py` *(conditional)* | `chokepoints.json` — supply-chain chokepoint layer, built off `build_capital_web.py`/`run_graph_analysis.py` output **before** the site export (not off `site.json`) | `/map` overlay, `/chokepoints`, `/terminal/card/chokepoint/[id]` |
| 7 | `run_backtest.py` *(only with `--with-backtest`)* | `backtests.json` | `/strategies` |
| 8 | `export_site.py` | `site.json` (the main bundle) | `/`, `/stocks/[t]`, `/map` |
| 9 | `build_risk.py` *(conditional)* | `risk.json` — stack heatmap, layer VaR/Sharpe, correlation matrix; runs **after** `export_site.py` | `/terminal/risk`, `/terminal/card/risk` |
| 10 | `build_archetypes.py` *(conditional)* | `archetypes.json` — Graham/Buffett/Lynch rule-based verdicts; a pure, zero-network computed step over `site.json`, runs after export | `/terminal/archetypes`, `/terminal/card/archetype/[symbol]` |
| 11 | `build_portfolio.py` *(conditional)* | `web/data/portfolio.json` — **not** `web/public/data/`, deliberately outside the public bundle convention since this is the owner's real, private holdings; degrades to an empty-state bundle if `data/portfolio/positions.json` is absent | `/terminal/portfolio`, `/terminal/card/portfolio` |
| 12 | `pull_macro.py` *(conditional)* | `macro.json` — FRED regime strip, 8-series dashboard; runs late, after the site export, before quantum/screener/news | `/terminal/macro`, `/terminal/card/macro` |
| 13 | `pull_quantum.py` *(conditional, quantum CLIs present)* | quantum fundamentals | quantum universe |
| 14 | `export_quantum.py` *(conditional)* | `quantum.json` | `/quantum` |
| 15 | `build_screener.py` | screener bundle | `/screener` |
| 16 | `pull_news.py` *(conditional)* | `news.json` — news for all ~1,251 tickers (108 AI ∪ congress), ticker-tagged, certainty-labeled, graph-linked + candidate-edge queue | `/news` |
| 17 | `vercel --prod` *(only with `--deploy`)* | — | rebuilds & ships the whole site |

**News transport:** Yahoo keyless RSS by default; set `FINNHUB_API_KEY` in the environment to
upgrade to Finnhub's categorized company news automatically.

**TA desk is a separate pipeline, not a `refresh_daily.py` step.** `web/public/data/ta_desk.json`
(feeds `/terminal` (the TA desk landing page), `/terminal/[symbol]`, and their capture cards) is
built by its own sibling orchestrator, `refresh_ta.py` — a one-real-step runner (`pull_ta.py` →
`ta_desk.json`, then optional `--deploy`). It is **not** wired into `build_plan()` in
`refresh_daily.py`; run it on its own schedule:

```bash
cd scripts
python refresh_ta.py --deploy       # pull_ta.py, then ship
python refresh_ta.py --dry-run      # print the plan, run nothing
```

**Two independent degradation layers guard every desk bundle**, and they are not redundant:

1. **Script-absence guard** (`refresh_daily.py`, orchestrator side) — `build_plan()` wraps
   each optional step in `os.path.exists()` on the *script file itself* (e.g.
   `build_risk.py`). If the script isn't present, the step is never added to the plan — no
   failure, just silently skipped.
2. **Output-absence/corruption guard** (`web/lib/*.ts`, page-render side) — each loader
   (`getRiskData`, `getMacroData`, `getArchetypeData`, `getPortfolioData`, `getTaDeskData`,
   `getChokepointsData`, …) independently checks `existsSync()` on the *output JSON*, wraps
   `JSON.parse` in try/catch, and **never throws** — a missing or malformed bundle caches a
   `null` singleton and the page renders its own empty state instead of a 500.

Together these mean a fresh clone with no scripts run yet, and a machine that ran the scripts
but produced a corrupt file, both degrade to the same honest "not generated yet" UI.

---

## 2b. TERMINAL — the gated `/terminal/*` desks

`/terminal/*` is a gated, personal Bloomberg-style workstation layered on top of the same
data this repo pulls — see [`web/TERMINAL.md`](web/TERMINAL.md) for the full owner's manual
(every route, what feeds it, capture-card ops). Quick reference for updating it:

- **Gate:** set `TERMINAL_KEY` in Vercel's environment variables (Project Settings →
  Environment Variables). `web/proxy.ts` matches `/terminal/:path*`; if `TERMINAL_KEY` is
  unset, `/terminal/*` is open (dev-only posture — always set it in prod). With it set, a
  request needs either the `terminal_key` cookie or `?key=<TERMINAL_KEY>` in the query
  string; a valid `?key=` sets a 400-day cookie scoped to `/terminal` so you only paste the
  key once per device.
- **Phone flow:** open `https://<your-deploy>/terminal?key=<TERMINAL_KEY>` once from your
  phone — the cookie sticks and every `/terminal/*` link works without the query param
  afterward.
- **Which bundle feeds which page:** TA desk (`ta_desk.json`, step out-of-band via
  `refresh_ta.py`) → `/terminal`, `/terminal/[symbol]`; risk (`risk.json`, step 9) →
  `/terminal/risk`; macro (`macro.json`, step 12) → `/terminal/macro`; archetypes
  (`archetypes.json`, step 10) → `/terminal/archetypes`; portfolio (`web/data/portfolio.json`,
  step 11) → `/terminal/portfolio`; chokepoints (`chokepoints.json`, step 6) feed the public
  `/map` overlay and `/chokepoints` board plus the gated
  `/terminal/card/chokepoint/[id]` capture card only (the board itself is not behind the key);
  DCF (no bundle of its own — computed client/server-side from `site.json` + `macro.json`) →
  the DCF panel on public `/stocks/[symbol]` pages plus the gated
  `/terminal/card/dcf/[symbol]` capture card.
- **Portfolio positions setup** (see also `data/portfolio/README.md`):
  ```bash
  cp data/portfolio/positions.example.json data/portfolio/positions.json
  # edit with real holdings, then:
  cd scripts && python build_portfolio.py
  ```
  `positions.json` is gitignored — never commit real holdings. Missing file degrades to an
  empty-state bundle, not an error.
- **`chokepoints_source.json` curation note:** this file lives at the **repo root**
  (`/home/user/AIInvestment/chokepoints_source.json`), is **committed** (unlike the generated
  `*.json` bundles under `web/public/data/`), and is **hand-curated** — `build_chokepoints.py`
  is network-free and only validates/joins/rolls it up against the already-built capital-web
  graph. Adding or editing a chokepoint means editing this source file directly, then
  re-running `python build_chokepoints.py` (or the full `refresh_daily.py`, which runs it as
  step 6) to regenerate `chokepoints.json`.

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
