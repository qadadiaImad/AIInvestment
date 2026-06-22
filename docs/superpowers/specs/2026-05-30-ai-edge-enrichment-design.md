# AI Edge-Enrichment Layer — Design Spec

**Date:** 2026-05-30
**Status:** Approved (build)
**Serves:** enrich the capital/relationship web with data that lives in unstructured text
(filings/news/transcripts) and can't be scraped deterministically — deal sizes, dates,
transaction history, and new relationships for isolated nodes.

> **Prime safety rule (Rule #5):** the AI may emit an edge ONLY if it can quote the exact
> supporting snippet from a fetched source. No source quote → the deterministic gate rejects
> it. Every edge carries `source_url` + `quote` + `certainty` (filed | reported | rumored).
> AI-extracted edges live in a SEPARATE store, visually distinct, never silently merged into
> curated facts.

## Components

### 1. The agent — `.claude/agents/edge-enricher.md`
A custom sub-agent (dispatchable via the Agent tool and the Claude CLI). Input: a target
company/node + fetched source text(s). Job: extract relationship edges
(`equity_stake | compute_commitment | customer | infra_partner | voting_power | subsidiary`)
with, for EACH edge: `src`, `dst` (company names + ticker if obvious), `type`, `attrs`
(incl. `transactions: [{date, amount, note}]` when stated), `certainty`, `source_class`,
`source_url`, and a mandatory exact `quote`. Output: a JSON list only. Hard rule: never emit
an edge you cannot quote; mark hedged language ("in talks", "could") as `rumored`; filings →
`filed`; news/PR → `reported`. Tools: Read, EDGAR/Bash, Playwright MCP, WebFetch.

### 2. The safety gate — `scripts/aiinvest/enrich.py` (deterministic, TDD)
- `validate_extracted_edge(edge, node_ids)` → list of issues; rejects unless: src & dst in
  node_ids, src≠dst, type ∈ VALID_EDGE_TYPES, certainty ∈ {filed,reported,rumored},
  non-empty `source_url`, non-empty `quote`.
- `accept_edges(edges, node_ids)` → `(accepted, rejected)` where rejected carries reasons.
- `resolve_node(name, name_index)` → map "Microsoft" → "MSFT" via a name→id index built from
  capital_web nodes + aliases; None if unresolvable.
- `merge_enriched(curated, enriched)` → tag origin (`curated` vs `ai-extracted`), dedupe by
  (src,dst,type) with curated winning; keep enriched-only edges + their transactions.
- `load_store(path)` / `save_store(path, edges)` for `capital_web_enriched.json`.

### 3. Render (capital_web.to_html)
Accept a merged graph; render `origin == "ai-extracted"` edges **dashed + dimmer**; edge
tooltip shows `quote`, `certainty`, `source_url`, and any `transactions`. Curated edges
unchanged. Edge thickness/label may reflect latest transaction amount.

### 4. Harness / flow
- `enrich_node.py SYMBOL` (or the CLI-invoked agent) → fetches sources, dispatches
  edge-enricher, writes candidate edges JSON.
- `merge_enriched.py` → runs `accept_edges` over candidates, appends accepted to
  `capital_web_enriched.json`, logs rejected with reasons.
- `build_capital_web.py` merges curated EDGES + the enriched store before rendering.

### 5. "Analyze all stocks in the graph"
Fan-out: for each graph ticker, `analyze.py` (data) then dispatch the `analyst` agent to
write the narrative + render the dashboard. Batched in parallel waves; heavy — run on demand.

## Testing (TDD)
enrich.py pure functions: gate accepts a good edge; rejects missing quote / unknown node /
bad certainty / self-loop; accept_edges splits; resolve_node maps name→id; merge_enriched
dedupes with curated winning and tags origin. Render: ai-extracted edge renders dashed;
tooltip carries the quote. The agent is exercised live (not in unit tests).

## Out of scope (now)
Auto-merging without the gate; numeric extraction without a quote; non-relationship facts.
