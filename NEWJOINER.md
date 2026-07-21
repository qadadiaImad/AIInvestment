# NEWJOINER — onboarding to the AIInvestment research platform

> Read this first. It explains **what we're building, how the pieces fit, and how we work** so you
> can be productive on day one. When you're done here, read [`CLAUDE.md`](CLAUDE.md) (the engine's
> "soul" + operating rules) and [`references/investing-brief.md`](references/investing-brief.md)
> (the investing mission the data serves).
>
> *Educational / research only — **not investment advice.** Congress data is public-record
> transparency, not accusation.*

---

## 1. What this project is (the aim)

A **multi-sector quant-investing research assistant** focused on the **AI value chain**, plus
**quantum computing** and **US congressional trading** as adjacent sectors. The thesis: the numbers
that explain a stock's price are **perishable** — they must be pulled **fresh and date-stamped** from
live sources, cross-validated, and turned into something a human (or a social audience) can act on.

It is **four cooperating layers**, in dependency order:

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 1. DATA ENGINE (Python + Playwright MCP)                             │
 │    Pull fresh, stamped fundamentals/market/news/relationship data    │
 │    → writes JSON bundles to web/public/data/                         │
 └───────────────┬─────────────────────────────────────────────────────┘
                 │  web/public/data/{site,quantum,congress,news,...}.json
       ┌─────────┴───────────┬──────────────────────────┐
       ▼                     ▼                          ▼
 ┌───────────┐      ┌──────────────────┐      ┌──────────────────────┐
 │ 2. WEB     │      │ 3. SOCIAL CONTENT │      │ 4. AI STACK STUDIO    │
 │ Next.js    │      │ carousels + reels │      │ Electron desktop      │
 │ dashboard  │      │ (Higgsfield art)  │      │ cockpit (gallery +    │
 │ → Vercel   │      │ → TikTok/IG       │      │ data + terminal)      │
 └───────────┘      └──────────────────┘      └──────────────────────┘
```

1. **Data engine** — the core. A Python package (`scripts/aiinvest/`) + orchestrator scripts that
   retrieve data **REST-first**, falling back to a **real browser (Playwright MCP)** only for
   API-less / gated / news sources. Output is timestamped JSON.
2. **Web dashboard** (`web/`) — a Next.js site that renders the data bundles (valuations, congress
   trades, the capital-relationship map, news). Deployed to Vercel.
3. **Social-content layer** (`higgs/`, `content/`) — turns the freshest data into image carousels
   and narrated 9:16 video "reels" for TikTok/Instagram, using Higgsfield for art + voice.
4. **AI STACK STUDIO** (`studio/`) — a local Electron app: galleries the produced reels/posts,
   shows the data behind each, and embeds a real PowerShell terminal to drive the pipelines.

---

## 2. The mental model (three convictions — from CLAUDE.md)

Internalize these; they govern every decision in the data engine.

1. **Numbers are perishable.** Every price, multiple, valuation, deal size, or "current holder of X"
   must come from a **live retrieval** and carry a **UTC timestamp** + **source**. Your own prior
   output is stale.
2. **REST-first; the browser is the fallback, not the default.** If a source has a usable API, hit it
   with a direct REST call (fast, scriptable, parallel). **Playwright MCP is reserved for three cases
   only:** (a) pages with no API, (b) gated premium metrics (e.g. GuruFocus GF Value), (c) news
   extraction.
3. **Gates are physics, not magic.** A free-tier limit is a counter keyed on cookies/storage/IP. You
   don't "hack" it — you **deny it state to count with**: fresh context, wiped storage, rotate before
   the threshold. (See [`references/anti-gating-cookbook.md`](references/anti-gating-cookbook.md).)

**Always:** stamp every datum (`retrieved_at`, `source`, `source_class`); label fact vs rumor; end
deliverables with provenance + caveats + the not-financial-advice note.

---

## 3. Repo map

```
CLAUDE.md                      ← engine soul + non-negotiable operating rules (READ)
NEWJOINER.md                   ← you are here
RESUME.md                      ← session-to-session / machine-to-machine handoff (current state)
ROADMAP.md / RUNBOOK.md        ← direction + operational runbook
references/                    ← the "why" and the "how"
  investing-brief.md           ← the AI-stack mission (Parts A–D): what numbers matter & why they decay
  playwright-mcp-protocol.md   ← exact MCP tool sequences for Mode A & Mode B
  anti-gating-cookbook.md      ← stealth, state-wipe, rotation, gate detection recipes
  data-schema.md               ← canonical output schema + validation rules
  gurufocus-fundamental-playbook.md  ← the flagship gated case, end to end
providers/README.md            ← per-source gating classification + REST/Playwright playbooks (READ)
scripts/                       ← THE DATA ENGINE (Python, TDD with pytest)
  aiinvest/                    ← the library: one module per concern (40+ modules, see §5)
  tests/                       ← pytest suite (42 test files; run before you push)
  pull_*.py / refresh_*.py     ← orchestrators (CLI entry points that pull → stamp → write bundles)
web/                           ← Next.js dashboard (NON-standard Next — see web/AGENTS.md) → Vercel
  app/                         ← routes: home, about, congress, map, news, resiliency, screener,
  public/data/*.json           ←   stocks/[symbol], strategies   |   data bundles it reads (gitignored)
higgs/                         ← social VIDEO reels engine (ffmpeg + Higgsfield); README_reels.md
content/                       ← social image carousels (HTML/CSS slides + briefs)
studio/                        ← AI STACK STUDIO Electron app (gallery + data + terminal)
docs/superpowers/              ← design specs + implementation plans (how features were designed/built)
  specs/  plans/
.claude/  .agents/  skills/    ← project skills & subagents (carousel, higgsfield, edge-enricher, …)
data/                          ← raw timestamped retrieval output (gitignored; regenerate)
```

**What does NOT travel in git** (regenerate locally): `web/public/data/*.json`, `data/`, and
Higgsfield scratch art (`higgs/hero_*`, `logo_*`, `voice_*.mp3`, `*_anim.mp4`). The **final**
deliverables (`higgs/reel_*.mp4`, carousels) **are** committed. See `higgs/.gitignore`.

---

## 4. How data flows (the pipeline)

```
sources ──(classify)──▶ REST call           ──┐
            │            (TradingView,         │
            │             Yahoo, EDGAR,        ├─▶ parse → VALIDATE (reject dirty values like ".")
            │             FRED, keyed APIs)    │      → STAMP (retrieved_at/source/source_class)
            └──no API/   ▶ Playwright MCP     ──┘      → schema (references/data-schema.md)
              gated/news   (GuruFocus, news, Koyfin)         │
                                                              ▼
                              aiinvest.siteexport / export_* ─▶ web/public/data/*.json
                                                              │
                        ┌─────────────────────────────────────┼───────────────────────┐
                        ▼                                     ▼                         ▼
                  web/ dashboard                      social carousels/reels       studio/ gallery
```

- **Orchestrators** (`scripts/refresh_daily.py`, `refresh_congress.py`, `pull_*.py`) run the no-gate
  REST stages in parallel, then the **gated GuruFocus stage serially via Playwright MCP**.
- The **classification of every source** (REST vs Playwright Mode A vs Mode B) lives in
  [`providers/README.md`](providers/README.md). **Flagship REST source = the TradingView scanner**
  (one POST returns many tickers × columns). **Flagship gated source = GuruFocus** (fundamental
  value), which needs Playwright Mode B + instance rotation.
- The engine also builds a **capital-relationship graph** (`capital_web*.json`) — who invests in /
  supplies / leases compute from / buys from whom, with deal sizes + dates — enriched from filings,
  news, and transcripts by the `edge-enricher` subagent.

---

## 5. The `aiinvest` library (data-engine internals)

`scripts/aiinvest/` is a pure-Python package, one module per concern. The ones you'll touch most:

| Module | Purpose |
|---|---|
| `tradingview.py` | **Flagship**: `scan(tickers, columns=…)` → fundamentals/ratios/sector (REST scanner). Generic, all sectors. |
| `yahoo.py`, `fred.py`, `edgar.py` | REST clients for prices, macro series, SEC filings. |
| `gurufocus.py`, `fundamental.py` | GuruFocus GF Value (gated) + valuation-chart parsing. |
| `ai_stack.py`, `quantum_stack.py` | Build the AI value-chain / quantum universes (layered). |
| `congress.py`, `congress_stocks.py`, `member_profile.py` | Congressional trade disclosures + member committees. |
| `capital_web.py`, `quantum_capital_web.py`, `enrich.py`, `news_graph.py` | Relationship-graph construction + enrichment. |
| `graph_metrics.py`, `contagion.py`, `vulnerability.py`, `macro_stress.py` | Graph/resiliency analytics. |
| `schema.py` | Canonical stamped-envelope schema + validation (the thing every value passes through). |
| `siteexport.py`, `report.py`, `dashboard.py` | Export to the `web/public/data/*.json` bundles the site reads. |

**Everything is TDD'd.** `scripts/tests/` has a matching `test_*.py` per module. Run the suite before
you push: `cd scripts && python -m pytest`.

---

## 6. How we work here (the dev workflow — important)

This project mandates a specific engineering discipline (see CLAUDE.md §1). **Follow it.**

- **Superpowers skills are not optional.** Before any new build/design work, use
  `superpowers:brainstorming`. When writing scraper/parser code, use
  `superpowers:test-driven-development`. When something fails twice, use
  `superpowers:systematic-debugging`. Before claiming a retrieval "works," use
  `superpowers:verification-before-completion` — **show the actual extracted values + timestamp**,
  not an assertion.
- **Multi-agent orchestration for scale.** For fan-out retrieval or large multi-step builds, prefer
  the **Workflow** tool / `superpowers:dispatching-parallel-agents` (no-gate stages parallel; gated
  MCP stays serial). Plans are executed with `superpowers:subagent-driven-development` (a fresh
  implementer subagent per task + an independent review after each + a whole-branch review at the
  end). See `docs/superpowers/plans/` for examples.
- **Respect the Playwright-MCP concurrency contract** (CLAUDE.md §3) — the single MCP browser is a
  shared resource:
  - **Mode A (ungated sources):** one sub-agent per tab, run in parallel (SEC, FRED, Yahoo, etc.).
  - **Mode B (gated, e.g. GuruFocus):** isolated instance, **strictly alone**, harvest-everything-in-
    one-pass within the free-hit budget (≈2 views), then **close & reopen** to reset the gate.
- **Extraction priority** (most→least robust): XHR/JSON interception → embedded JSON/hydration →
  DOM selectors → `innerText` + regex (last resort, always validate).
- **Stamp & cite.** Deliverables end with provenance, what decayed, what failed, and the disclaimer.

---

## 7. Getting started (setup)

```bash
# 1. Data engine (Python)
cd scripts
pip install -r requirements.txt
python -m pytest                       # confirm the suite is green
python refresh_daily.py                # regenerate web/public/data/*.json (no-gate REST stages)
#   gated GuruFocus fundamentals: ask Claude "update GuruFocus fundamentals" (Playwright MCP, serial)

# 2. Web dashboard (Next.js — read web/AGENTS.md first; this is a non-standard Next build)
cd ../web
npm install
npm run dev                            # http://localhost:3000   (prod: Vercel)

# 3. AI STACK STUDIO (Electron desktop cockpit)
cd ../studio
npm install                            # node-pty loads via NAPI prebuilds — no native rebuild needed
npm run dev                            # launches the app; npm run dist builds an installer
```

**Secrets:** API keys go in a **gitignored `.env`**, read at runtime — never hardcoded or committed.

---

## 8. The AI value chain (the layers you'll hear about)

The investing brief organizes names into a **stack** — knowing a name's layer tells you which metrics
matter. From the bottom up:

```
L0 Energy ─▶ L1 Chips ─▶ L2 Infra / Neocloud ─▶ L3 Models ─▶ L4 Application
(power,        (NVDA,       (compute capacity,      (OpenAI,      (software that
 nuclear,       AVGO,        data centers,           Anthropic)    sells AI features)
 grid)          chips)       neoclouds)
```

Full framework, valuation rules, and constraint checks (e.g. the energy ceiling on compute) are in
[`references/investing-brief.md`](references/investing-brief.md). Quantum and congressional-trading
are parallel sectors with their own universes.

---

## 9. Gotchas & conventions (save yourself an hour)

- **`web/` is a non-standard Next.js** with breaking changes vs. what you may know. **Read
  `web/AGENTS.md`** and `node_modules/next/dist/docs/` before writing site code.
- **TradingView scanner requires the exchange prefix** (`NASDAQ:WMT`, not `WMT` or `NYSE:WMT`) — a
  wrong/missing prefix returns an **empty array silently**, not an error.
- **GuruFocus current value vs historical series use different transports**: the scalar can be fetched
  locally; the historical **chart series returns 200 only through the Playwright MCP session**
  (sessionless = 403). Stored generically as `fundamental_value` — never named in output.
- **Validate extracted values** — reject `"."`, `""`, `"N/A"`. (Legacy regex scraping once emitted
  `current_ratio: "."`; the schema layer exists to stop that.)
- **Social-content rails:** no first person (analyst/anchor voice); never name the news outlet →
  "reportedly"; congress = transparency, **not** accusation; thin footer disclaimers only.
- **Studio node-pty:** do **not** try to rebuild it from source (the winpty gyp chain fails without VS
  C++ tools). It ships ABI-agnostic NAPI prebuilds that load under Electron directly; packaging uses
  `npmRebuild: false`. (Memory: `studio-node-pty-electron`.)
- **Ticker renames (2026):** BK→BNY, FI→FISV; K/DAY delisted; CTRA dead on GF; ALKAL needs `XPAR:`;
  GF `gf_value=0` is a "no value" sentinel; GF chart API version drifts — read it from the page each run.

---

## 10. Where to go next

1. [`CLAUDE.md`](CLAUDE.md) — the operating rules in full (mandatory).
2. [`references/investing-brief.md`](references/investing-brief.md) — the mission the data serves.
3. [`providers/README.md`](providers/README.md) — per-source playbooks.
4. [`RESUME.md`](RESUME.md) — the **current state** of work (what's built, what's next).
5. `docs/superpowers/` — design specs + plans, to see how features are scoped and executed.
6. Skim `scripts/aiinvest/schema.py` + a couple of `scripts/tests/test_*.py` to see the
   stamp-and-validate pattern in practice.

Welcome aboard. Pull fresh, stamp everything, cite your sources — and remember it's educational
research, not financial advice.
