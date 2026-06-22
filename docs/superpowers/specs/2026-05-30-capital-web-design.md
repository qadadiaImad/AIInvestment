# Capital & Relationship Web (Part C) — Design Spec

**Date:** 2026-05-30
**Status:** Approved (pending spec review)
**Serves:** `ai-investing-project-instructions.md` Part C ("a web, not a chain") and the
brief's central question — *who has pricing power*. Closes the largest open data-side gap
in `ROADMAP.md`.

## Goal

Represent the AI capital web — who invests in whom, who leases compute from whom, the
dollar size / duration / termination of those ties — as **queryable, provenance-stamped
data** plus a **beautiful interactive HTML visualization**. Facts and queries only; the
analyst interpretation layer (Part A) stays out.

## 1. Data model — versioned JSON edge-list

Seed data: `scripts/aiinvest/capital_web.json` (curated **source** data → versioned in git,
NOT under the gitignored `data/`).

### Node
```json
{ "id": "anthropic", "name": "Anthropic", "type": "private",
  "ticker": null, "layer": "L3-models", "note": "IPO reported ~Oct 2026" }
{ "id": "GOOGL", "name": "Alphabet", "type": "public",
  "ticker": "NASDAQ:GOOGL", "layer": "L2-infra", "note": "" }
```
- `id`: bare ticker symbol for public names (e.g. `GOOGL`), slug for private (`anthropic`).
- `type`: `public | private | subsidiary`.
- `layer`: one of the five stack layers (or `private-lab`).
- **Node set** = all 46 universe tickers (from `ai_stack.all_tickers()`, bare symbols) +
  private/pre-IPO labs (OpenAI, Anthropic, xAI, Mistral, Cohere, Crusoe, Lambda) + key orgs.
  Most nodes start edgeless — acceptable.

### Edge
```json
{ "src": "GOOGL", "dst": "anthropic", "type": "equity_stake",
  "attrs": { "pct": 14, "cap_pct": 15 },
  "certainty": "reported", "source_class": "news-html",
  "source_url": "https://...", "as_of": "2026-05", "retrieved_at": "2026-05-30T12:00:00Z" }
```
- `type`: `equity_stake | compute_commitment | customer | voting_power | subsidiary | infra_partner`.
- `attrs` (type-dependent, all optional): `pct`, `cap_pct`, `usd`, `usd_per_month`,
  `power_gw`, `power_mw`, `gpus`, `tpus`, `duration`, `until`, `termination_days`, `annualized_usd`.
- `certainty`: `filed | reported | rumored` (validated against `news.classify_certainty`
  vocabulary). Rule #5 — never launder a rumor into a fact.
- Provenance: `source_class`, `source_url`, `as_of`, `retrieved_at` required on every edge.

### Seed edges (from brief Part C, each provenance-stamped)
- `GOOGL --equity_stake 14% (cap 15%)--> anthropic`
- `anthropic --compute_commitment $200B, ~1 GW, ~1M TPUs--> GOOGL`
- `AMZN --equity_stake ~$13B--> anthropic`
- `anthropic --compute_commitment up to ~5 GW, $100B+/decade--> AMZN`
- `anthropic --compute_commitment $1.25B/mo to 2029-05, 300 MW, ~220k GPUs, termination_days 90--> spacex`
- `MSFT --infra_partner / equity + Azure--> openai`
- `ORCL --infra_partner (Stargate)--> openai`
- `xai --subsidiary--> spacex` (xAI folded into SpaceX); `musk --voting_power 85%--> spacex`
- (extend as news/EDGAR surface more; mark certainty honestly)

## 2. Module — `scripts/aiinvest/capital_web.py`

Pure logic, TDD-able. Functions:
- `load(path=DEFAULT)` → `{"nodes": [...], "edges": [...]}`.
- `validate(graph)` → raises/returns issues: every edge `src`/`dst` references a defined
  node; `certainty` ∈ {filed, reported, rumored}; provenance fields present.
- `edges_from(graph, node_id)`, `edges_to(graph, node_id)`.
- `investors_of(graph, node_id)`, `investees_of(graph, node_id)` (equity_stake edges).
- `exposure_to_labs(graph, ticker)` → list of `{lab, type, pct/usd, certainty}` — a public
  ticker's direct stakes in private labs (e.g. GOOGL → Anthropic 14%).
- `counterparty_concentration(graph, node_id)` → inbound/outbound grouped by counterparty
  with `$` sums — surfaces single-counterparty risk.
- `termination_risk(graph, max_days=180)` → compute_commitment edges with short
  `termination_days` (e.g. the 90-day SpaceX exit).
- `to_html(graph, title=...)` → standalone interactive HTML string (see §3).

## 3. Visualization — standalone interactive HTML

`to_html(graph)` returns one self-contained HTML file (`capital_web.html`):
- **vis-network** from CDN (`https://unpkg.com/vis-network/...`); nodes/edges JSON embedded
  inline — no build step, no local install.
- **Nodes** colored by stack layer (L0–L4 distinct colors + private-lab color), sized by degree.
- **Edges** labeled by `type`; **solid** = filed/reported, **dashed** = rumored; arrowheads
  show direction of money/control.
- **Hover tooltip** per edge: `$ size · duration · termination · certainty · source · retrieved_at`.
- Interactive: drag, zoom, click-to-focus a node's neighborhood.
- Output path: repo root `capital_web.html` (regenerable; may be gitignored).

## 4. Testing (TDD)

All pure functions, fixture-driven:
- `validate` catches a dangling edge (src/dst not a node) and an invalid certainty.
- Query functions on a small fixture: `investors_of`, `exposure_to_labs` returns
  GOOGL→Anthropic 14%, `termination_risk` flags the 90-day edge,
  `counterparty_concentration` sums by counterparty.
- `to_html` embeds the right node/edge counts, includes the vis-network CDN, and renders a
  rumored edge as dashed.
- **Integrity test over the real `capital_web.json`**: `validate` passes — every edge
  references a defined node, every edge carries provenance + valid certainty.

## Module boundaries
`capital_web.json` (data) · `capital_web.py` (load + validate + query + to_html) ·
`tests/test_capital_web.py`. CLI `scripts/build_capital_web.py` regenerates the HTML.
The analyst interpretation ("who has pricing power") is NOT in scope — this supplies facts
and queries only.

## Out of scope (future)
Catalyst calendar (Part D), automated edge extraction from news/EDGAR (edges are curated
now; automation can append later, always certainty-stamped), Part A analyst behavior.
