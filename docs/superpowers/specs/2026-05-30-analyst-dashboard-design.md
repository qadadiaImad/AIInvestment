# Analyst / Dashboard Layer (Part A) — Design Spec

**Date:** 2026-05-30
**Status:** Approved (pending spec review)
**Serves:** `ai-investing-project-instructions.md` Part A (the analyst role + output style).
The consumer of the data side: reads a dossier, reasons over it, presents a dashboard.
**Educational only — not financial advice. No buy/sell recommendations.**

## Goal

Turn a per-ticker dossier (from `dossier.py`) into a scannable, interactive analysis:
valuation read, the one bottleneck that matters, relationship/capex map, catalysts,
scenarios, and risks — in Part A's dashboard style. Plus a whole-stack screener.

## Approach (decided)

- **Hybrid**: deterministic code computes the facts; the LLM (me, Claude Code, on demand
  via the `analyst` skill) writes the reasoning/narrative over those facts.
- **LLM execution**: no API wiring — I read the fact sheet in-session and produce the
  `narrative` dict, then render. Reproducible facts; interpretive narrative.
- **Output**: interactive HTML (per-ticker dashboard + stack screener).
- **Scope**: both single-ticker dashboard and whole-stack screener.

## Data flow
```
dossier.json ─(analyst.fact_sheet)→ factsheet.json ─(I read via 'analyst' skill)→
   narrative dict ─(dashboard.to_html)→ <ticker>_dashboard.html
batch dossiers ─(screener.screen)→ ranked rows ─(screener.to_screener_html)→ stack_screener.html
```

## Components

### 1. `constraints.py` — Part D knowledge (deterministic)
Curated `{physical_bottleneck, regulatory_bottleneck, lead_time_note}` keyed by layer and
by specific name. Examples:
- L0-energy: "gas-turbine backlog (GEV/Siemens); interconnection queues / transmission
  permitting" · SMR names (SMR/OKLO/NNE): "pre-commercial scale; NRC licensing risk".
- L1-chips: "CoWoS advanced packaging + HBM" · "US/China GPU export controls" · ASML "EUV
  sole-supplier".
- L2-infra: "power & cooling siting; behind-the-meter gas" · "local DC moratoria, tariffs".
- L3-models (labs): "compute access & power" · "antitrust on hyperscaler stakes; EU AI Act".
- L4-application: "GPU/inference cost pass-through" · "data-privacy / sector regulation".
API: `for_node(layer, symbol)` → the constraint record (name override beats layer default).
TDD'd; values sourced from brief Part D, provenance-noted.

### 2. `analyst.py` — `fact_sheet(dossier, now)` (deterministic)
Computes analyzable facts from a dossier:
- **valuation**: `price`, `gf_value`, `discount_pct` = (gf_value−price)/gf_value when both
  present, `pe`, `verdict` (GuruFocus), `profitability` flag (pre-revenue if private/no P/E
  or negative earnings → "venture bet, not value buy").
- **constraint**: from `constraints.for_node(layer, symbol)`.
- **relationships**: counterparties with `$`/type, `single_counterparty_flags` (e.g. 90-day
  termination), `lab_exposure`.
- **catalysts**: upcoming dated events for this ticker.
- **freshness**: per-metric `verify_live` derived from the merge `stale` flag.
- **risk_flags**: list (concentration, pre-revenue, short-termination lease, IPO/lockup).
Returns a plain dict (the fact sheet). TDD'd. Never invents numbers; missing → null + note.

### 3. `dashboard.py` — `to_html(fact_sheet, narrative)` (deterministic renderer)
Standalone styled HTML in Part A output style: header (ticker · name · layer · live price +
date · valuation verdict), the one bottleneck, key counterparties, calendar, then
narrative-filled sections (valuation prose, scenarios, risks). `narrative` is a dict:
`{valuation_take, bottleneck_rationale, scenarios: [...], risks: [...], synthesis}`.
"verify live" badges where `verify_live` is true. **Disclaimer footer always.** Tests assert
structure, that narrative sections render, and that stale metrics get the badge.

### 4. `screener.py` — `screen(dossiers)` + `to_screener_html(rows)`
`screen` → ranked rows across many dossiers: `{symbol, layer, price, pe, gf_discount_pct,
lab_exposure, next_catalyst, verify_live}`, sortable. `to_screener_html` → interactive
sortable HTML table, color-coded by layer (reuse capital_web palette). TDD'd.

### 5. `skills/analyst/SKILL.md` — the reasoning prompt
Encodes Part A: role, the per-query workflow, output style, and guardrails — **no buy/sell;
facts + framework only; carry rumor/reported/filed labels from the data; scenarios not point
predictions; always end with risks + "not a financial advisor".** Instructs me to read the
fact sheet, produce the `narrative` dict, and render via `dashboard.to_html`. Not Python.

## CLI / glue
- `build_factsheet.py <SYMBOL>` → reads/creates a dossier, writes `factsheet_<sym>.json`.
- `build_screener.py` → batch dossiers/factsheets across the universe → `stack_screener.html`.
- Per-ticker dashboard is produced when I'm asked to analyze (skill-driven), writing
  `<sym>_dashboard.html`.

## Testing (TDD)
Pure functions throughout: `constraints.for_node` (name override beats layer), `fact_sheet`
(discount math, profitability flag, risk flags, verify_live from stale), `dashboard.to_html`
(structure, narrative rendering, stale badge, disclaimer present), `screener.screen`
(ranking, fields) and `to_screener_html` (valid sortable table). Narrative is supplied as a
fixture dict in tests — the LLM is not invoked in tests.

## Guardrails (non-negotiable)
Educational, not advice. No buy/sell. Facts + framework only. Preserve certainty labels.
Disclaimer on every output. "verify live" on stale data.

## Out of scope (future)
API-wired unattended analysis, portfolio optimization, backtesting, alerts/scheduling.
