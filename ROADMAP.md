# ROADMAP — data-side gap audit

Tracks `ai-investing-project-instructions.md` (the full brief) against what's built.
Scope: **data side first** (owner's directive). Part A analyst behavior is deferred.
Status keys: ✅ done · 🟡 partial · 🟠 documented-only · ❌ not started · ⏸️ deferred.

## Data sources (Appendix)
- [x] ✅ TradingView scanner — REST, tested, live (46-name AI-stack pull) → `tradingview.py`
- [x] ✅ Yahoo — REST helper built + tested + verified live → `yahoo.py`
- [x] ✅ GuruFocus — extraction + gate-detection core tested; Mode-B fetch validated live → `gurufocus.py`
- [x] ✅ **SEC EDGAR** — REST helper, tested, live (NVDA 10-K resolved) → `edgar.py`
- [x] ✅ **FRED** — REST helper, tested, live keyless (10Y rate, electricity $/kWh) → `fred.py`
- [ ] 🟠 Keyed APIs (Finnhub/AlphaVantage/FMP/Tiingo/Polygon/Quandl) — optional REST helpers
- [ ] 🟠 Koyfin / Simply Wall St — Playwright Mode-B, only if owner is authorized

## Coverage & structure
- [x] ✅ Universe expanded to **97 live-validated US tickers** across L0/L1/L2/L4 (chips, EDA,
      memory, equipment, servers, networking, utilities, nuclear, software). Private/pre-IPO labs
      tracked as nodes. (Foreign listings & decentralized tokens still out — america-scanner only.)
- [x] ✅ Rich fundamentals — 17 new TradingView columns (margins, ROE/ROA/ROIC, growth, leverage,
      P/S, P/FCF, 1Y/YTD perf, beta) flow into dossiers + `fact_sheet.fundamentals/performance`.
- [x] ✅ Peer/"global" comparison — `peers.py` (industry scan + AI-stack-layer peers + percentile
      benchmarking); wired into dossier `peer_stats` and the dashboard's peer-comparison table.
- [x] ✅ Multi-year history — `history.py` via **Yahoo fundamentals-timeseries (keyless REST)** —
      revenue/net income/gross profit/FCF/EPS multi-year; wired into dossier `history` and rendered
      as SVG sparklines in the dashboard. (stockanalysis moved to SvelteKit; Yahoo timeseries cleaner.)
- [x] ✅ One-command runner `analyze.py SYMBOL` + `RUNBOOK.md` (full operating guide).
- [x] ✅ News-processing core (`news.py`) — tag entities, classify filed/reported/rumored, dedupe (fetch = Playwright)
- [x] ✅ Capital/relationship + capex web (Part C) — `capital_web.py` (JSON edge-list + queries
      + provenance/certainty) + interactive vis-network HTML (`build_capital_web.py`); rendering verified
- [x] ✅ Catalyst calendar (Part D) — `catalysts.py`: IPO trio + export-control/turbine/permitting
      watch + LIVE earnings dates via `from_tradingview_earnings`; `upcoming/by_entity/by_type`
- [x] ✅ GF Value wired into merge — `gurufocus.to_record` + `merge` canonical aliasing
      (close/price/current_price unify) → NVDA price cross-validated across TV+Yahoo+GuruFocus
- [x] ✅ Cross-source merge per symbol (`merge.py`) — collects sources, agreement flag
- [x] ✅ Freshness flagging (Rule #1) — `merge.is_stale` / per-metric `stale` flag
- [ ] ❌ Scheduled refresh (data decays) — optional cron/loop once helpers exist

## Capstone
- [x] ✅ One-ticker dossier (`dossier.py` + `pull_dossier.py`) — composes merged cross-source
      metrics + EDGAR filings + catalysts + capital-web relationships into one stamped object.
      Live-verified: NVDA & GOOGL (GOOGL surfaces its 14% Anthropic stake as lab_exposure).

## Analysis layer (Part A behavior)
- [x] ✅ Analyst/dashboard layer — `constraints.py` (Part D bottleneck knowledge),
      `analyst.fact_sheet` (valuation math, profitability, risk flags, verify-live),
      `dashboard.to_html` (per-ticker HTML), `screener` (whole-stack sortable table),
      `skills/analyst/SKILL.md` (Part A reasoning prompt). CLIs: build_factsheet / render_dashboard /
      build_screener. Live-verified end-to-end: NVDA dashboard (GF Value $334.32, 36.8% disc,
      value-trap flag, bull/base/bear scenarios, disclaimer).

## Priority order
1. **SEC EDGAR** (REST, TDD) ← now
2. **FRED** (REST, TDD)
3. **News extraction** (Playwright)
4. **GuruFocus batch** (Playwright Mode-B) + **Yahoo helper**
5. **Cross-source merge** + freshness flagging
6. Capital/relationship web + catalyst calendar
