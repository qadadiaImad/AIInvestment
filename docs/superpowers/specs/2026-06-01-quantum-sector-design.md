# Quantum sector vertical — design

**Date:** 2026-06-01  **Status:** approved-pending-spec-review (brainstorming gate)
Universe research: `2026-06-01-quantum-universe-research.md`.

**Decisions:** Architecture = **hybrid** (separate quantum pipeline → merged into combined views).
UI = **single combined screener + graph with a sector filter** (no separate /quantum routes).
Bridge names tagged **both** AI+Quantum. Giants = **graph-only** (not screener). Applications =
**full screener members**. Universe provided via web research (this build).

Educational/research only — not investment advice. Never reference GuruFocus (use `fundamental_value`).

## 1. Architecture (keeps the live AI pipeline byte-identical)
- New **separate quantum pipeline** mirrors the AI one; the AI Python path is untouched.
- The **web data loader merges** `site.json` (AI) + `quantum.json` (Quantum), assigning each stock/node a
  `sectors: string[]` (a bridge ticker present in both → `["AI","Quantum"]`). The existing screener / map /
  value-chain components consume the merged dataset and gain a **sector filter** (`All / AI / Quantum`).

## 2. Universe — `scripts/aiinvest/quantum_stack.py` (NEW, mirrors ai_stack.py)
- `LAYERS` = the SCREENER-pulled tickers only (TradingView america scanner, `EXCHANGE:SYMBOL`):
  - **Q1-hardware (pure-play):** NYSE:IONQ, NASDAQ:RGTI, NYSE:QBTS, NASDAQ:QUBT, NYSE:INFQ, NASDAQ:XNDU
  - **Q3-software (pure-play):** NASDAQ:HQ
  - **Q4-security (pure-play):** NASDAQ:ARQQ, NASDAQ:LAES, NASDAQ:WKEY, AMEX:QNC, NASDAQ:BTQ
  - **Q5-applications (demand-side, US-listed):** NASDAQ:AZN, NYSE:GSK, NASDAQ:MRNA, NYSE:JPM, NYSE:GS, NYSE:BCS, NYSE:BBVA, NYSE:HSBC
  - (exchange prefixes are best-effort; the pull verifies each via the live scan and reports misses, like pull_ai_stack.)
- `PENDING` = {NASDAQ:QNT (Quantinuum)} — attempted on each pull; included automatically once it resolves live.
- `GIANT_NODES` = diversified bridges/suppliers, **graph-only** (id, name, layer, note): IBM, GOOGL, MSFT, AMZN,
  NVDA, INTC, HON, AMAT, TSM, COHR, CSCO, AMD, NOK, BAH, LDOS, NOC, LMT, ACN, FORM, KEYS, MKSI, IPGP, LITE, APH, STM.
- `PRIVATE_NODES` / `FOREIGN_NODES` = watch-list graph nodes (PsiQuantum, Quantinuum, IQM, Pasqal, QuEra, Atom,
  Alice&Bob, Quandela, OQC, SEEQC, Bluefors, Quantum Machines, Qblox, Classiq, Q-CTRL, Riverlane, SandboxAQ,
  ID Quantique, Qunnect, Aliro, PQShield, …; foreign OXIG, 6965, Toshiba, Fujitsu, NEC, QuantumCTek, Exail, …).
- `all_tickers()`, `layer_of()` — same API as ai_stack. `SECTOR = "Quantum"`.

## 3. Curated quantum graph — `scripts/aiinvest/quantum_capital_web.py` (NEW, mirrors capital_web.py)
- `build_graph()` → nodes (screener tickers as public + GIANT_NODES + PRIVATE/FOREIGN nodes) + curated `EDGES`,
  reusing capital_web's `_e()/validate()/edges_*` helpers (import them; don't duplicate).
- Seed `EDGES` (provenance-stamped, certainty-labeled, from the research) — examples:
  - `IONQ →acquired→ Oxford Ionics` (Sep'25, ~$1.075B); `IONQ →owns→ ID Quantique/Qubitekk/Lightsynq`
  - `QBTS →acquired→ Quantum Circuits Inc` (Jan'26, $550M)
  - `HON →owns→ Quantinuum` (~majority); `Quantinuum →customer→ JPM/BMW/Airbus/Mitsui`
  - `IONQ →cloud_on→ AWS/Azure/GCP`; `QuEra →cloud_on→ AWS`; `Atom Computing →partner→ MSFT`; `Pasqal →cloud_on→ Azure`
  - `RGTI →partner→ NVDA` (NVQLink); `Alice&Bob ←invest← NVDA (NVentures)`; `SEEQC ←invest← BAH`
  - `IONQ →supplier→ NKT Photonics (lasers)`; builders `→supplier→ Bluefors (cryo) / Quantum Machines (control)`
  - `SandboxAQ ←spinout← GOOGL`; `WKEY →owns→ LAES`
  - edge types reuse the existing taxonomy where possible: `customer, infra_partner, equity_stake, subsidiary,
    compute_commitment` + new `acquired`, `cloud_on`, `supplier`, `spinout` (added to RELATION_SEMANTICS so the
    value-chain view classifies them: acquired/subsidiary/spinout=capital; supplier=src supplies dst; cloud_on=src buys from dst).
- All edges carry `source_url`, `as_of`, `certainty` (reported/filed/rumored). Validate() must pass (no dangling ids).

## 4. Pull + export (reuse AI machinery)
- `scripts/pull_quantum.py` — pull fundamentals + `fundamental_value` for `quantum_stack.all_tickers()` via the same
  `tradingview`/`schema` path as `pull_ai_stack.py` (parameterize by universe). Prices reuse `pull_prices` over the
  quantum tickers. Honest miss-reporting (unresolved tickers listed, like the AI pull).
- `scripts/export_quantum.py` — mirror `export_site.py`/`siteexport.py` to write `web/public/data/quantum.json`
  (keys: generated_at, disclaimer, sources, layers, stocks, capital_web, screener) with `sector:"Quantum"` stamped.
  Runs the same fundamental_value sanitizer (no "GuruFocus" leak).
- `scripts/refresh_daily.py` — add guarded steps `pull_quantum.py` + `export_quantum.py` (after the AI export);
  update build_plan + test_refresh.

## 5. Web (merge + sector filter; reuse components)
- `web/lib/data.ts` — extend the loader: read `quantum.json` (if present) and **merge** into the working dataset —
  stocks/nodes get `sectors: string[]` (union for bridge tickers); capital_web nodes+edges unioned (dedupe edges by
  src+dst+type). Types gain `sectors?`. Absent quantum.json → AI-only (unchanged).
- `web/components/Screener*` — add a **sector filter** (All / AI / Quantum) + a `sectors` chip column; default All.
- `web/components/MapExplorer` — add a sector filter / color-tint (All / AI / Quantum); the combined graph shows
  bridges connecting the two chains. The value-chain (egograph) already works on any node; new edge types added to
  `RELATION_SEMANTICS` (web/lib/egograph.ts) so quantum edges classify correctly.
- Dashboard/layers UI: show Quantum layers (Q0–Q5) when the Quantum sector is selected (reuse layer rendering).
- No new routes; no separate /quantum pages.

## 6. Honesty / rails
- fundamental_value relabeled; sanitizer enforced. Quantum pure-plays are largely pre-revenue/speculative — the
  screener must show what's missing (nulls), not fabricate. Pending IPOs (QNT) and recent SPACs (INFQ/XNDU/HQ/BTQ)
  flagged; never pulled as fact if unresolved. Private/foreign = nodes only, labeled. Relationships reported/filed/
  rumored with source. Educational only — not investment advice.

## 7. Testing (TDD)
- `tests/test_quantum_stack.py` — all_tickers dedupe, layer_of, SCREENER vs GIANT/PRIVATE separation, no overlap leaks.
- `tests/test_quantum_capital_web.py` — build_graph validates (no dangling edges), bridge nodes present, edge provenance.
- `tests/test_export_quantum.py` — quantum.json schema + sector stamping + no GuruFocus leak.
- `tests/test_refresh.py` — new steps ordering (guarded).
- web: extend egograph vitest for the new edge types (acquired/cloud_on/supplier/spinout) classification; tsc + next build.

## 8. Orchestration (phased — large build)
- **Phase 1 (data foundation):** quantum_stack + quantum_capital_web + pull_quantum + export_quantum + refresh wiring
  + Python tests. Verify a real fundamentals pull for the pure-plays; produce quantum.json.
- **Phase 2 (web):** merge loader + sectors tagging + sector filter on screener & map + egograph edge-type extension.
  tsc + next build. Then orchestrator runs real pull → build → deploy.
Workflow per phase (parallel slices where files are disjoint). Integration + deploy by the orchestrator.
