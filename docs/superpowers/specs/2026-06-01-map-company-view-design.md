# /map per-company value-chain view — design

**Date:** 2026-06-01  **Status:** approved (brainstorming gate passed)
**Decisions:** 3-column Bloomberg-SPLC layout; entry via Global⇄By-company toggle + node dropdown +
click-a-node-to-drill + click-a-counterparty-to-recenter. Web-only; no data-pipeline change.

Educational/research only — not investment advice.

## 1. Goal
Add a second `/map` view: for a focal company, **[Inputs] → Company → [Outputs]** —
who it depends on / who can influence its stock (upstream + capital-in backers) and who depends on it /
which it influences (downstream + capital-out holdings). Complements (does not replace) the existing
global force graph. Like Bloomberg SPLC.

## 2. Data & classification (correctness core) — `web/lib/egograph.ts` (NEW, pure, client-safe)
Transforms the existing `capital_web` ({nodes, edges}) for a focal id. No new data.

`RELATION_SEMANTICS: Record<edgeType, {flow}>` is the single source of truth. For each edge incident to
the focal, classify the **other** endpoint as Input or Output by type (NOT by arrow direction):

| type | flow | focal = src | focal = dst |
|---|---|---|---|
| `customer`, `compute_commitment` | `src_buys_from_dst` | Input · kind=supply/compute (dst=supplier) | Output (src=customer) |
| `infra_partner` | `src_supplies_dst` | Output (dst=customer) | Input · supply (src=supplier) |
| `equity_stake`, `subsidiary`, `voting_power` | `capital` | Output · capital-out (dst=holding) | Input · capital-in (src=backer) |
| *(unknown type)* | `related` | Output (best-effort, labeled "related") | Input (best-effort) |

- `kind ∈ {supply, compute, capital, related}`; `side ∈ {input, output}`.
- Aggregate multiple edges between the same (focal, other) pair into ONE `Counterparty` with a
  `relations[]` list. A pair that is both input and output (rare) appears on both sides.
- Sort each side by salience: `attrs.usd` (or `*_usd`) desc if present, else relation count desc, then name.

Exports:
- types `Relation` ({type, kind, side, certainty, source_url, as_of, terms:string, raw:edge}),
  `Counterparty` ({id, name, layer, side, kind, relations:Relation[], score}),
  `EgoModel` ({focal:node, inputs:Counterparty[], outputs:Counterparty[], counts}).
- `RELATION_SEMANTICS`, `buildEgoModel(web, focalId): EgoModel`,
  `formatTerms(attrs): string` (compact: `$40B · 1.2 GW · 1M TPUs · <product>`; pick the few high-signal
  attr keys — usd/*_usd, power_gw/power_mw, gpus/tpus, pct/stake_pct, product/products, note/description —
  and omit the rest), `relationKindMeta(kind)` (label + color class).

## 3. UI
### 3.1 `web/components/MapExplorer.tsx` (EDIT — extend, don't rewrite)
- Add `viewMode: "global" | "company"` state (default "global"). Toggle in the selector bar:
  `[ Global graph | By company ]`.
- Keep `selectedId` as the SHARED focal (the existing "Drill into node" dropdown already sets it — reuse;
  relabel to double as the focal picker, and make it a searchable select if cheap, else keep optgroup select).
- Node click in global graph (`CapitalGraph onSelect`) sets `selectedId` AND switches `viewMode="company"`
  (drill-in). A `← Global graph` control returns to the graph (focal stays).
- Render:
  - `viewMode==="global"`: existing `CapitalGraph` (unchanged) in the center.
  - `viewMode==="company"` (and `selectedId`): `<CompanyValueChain web focalId onFocus={setSelectedId} resiliency />`
    in the center; if no focal, show a "pick a company" prompt.
  - **Keep the `NodeDetailPanel` aside in BOTH modes** (the "relationships at the right" the global view has).
- Color-by + macro-stress controls remain (they apply to the global graph; hide/disable them in company mode).

### 3.2 `web/components/CompanyValueChain.tsx` (NEW, client)
3-column flow from `buildEgoModel`:
- Left **INPUTS — "depends on · can influence its stock"**, grouped by kind (Supply · Compute · Capital-in),
  each counterparty a row: name (→ `/stocks/{id}` link AND a click that calls `onFocus(id)` to re-center),
  relation chips (`type · formatTerms · certainty`), source link.
- Center: focal company card — name, layer, link to `/stocks/{focal}`, and its resiliency stat
  (health/SPOF from `resiliency` if available); small "← Global graph" affordance handled by parent.
- Right **OUTPUTS — "depends on it · which it influences"**, grouped by kind (Supply · Compute · Capital-out).
- Connector styling left→center→right (CSS; arrows). Empty side → muted "no recorded …". Counts in headers.
- Honesty: each relation carries the edge's OWN `certainty` (reported/filed/rumored) + source; never upgraded.

### 3.3 `/map/page.tsx`
No change needed (already renders `MapExplorer` with web+resiliency+dffBase).

## 4. Testing
`egograph.ts` is parser-like → add **vitest** (`npm i -D vitest`, `"test":"vitest run"`, minimal config) and
`web/lib/egograph.test.ts` (TDD):
- `customer` NVDA→TSM ⇒ for NVDA, TSM is an **input/supply** (supplier); for TSM, NVDA is an **output**.
- `infra_partner` MSFT→openai ⇒ for openai, MSFT is an **input/supply**; for MSFT, openai is an **output**.
- `equity_stake` GOOGL→anthropic ⇒ for anthropic, GOOGL is **input/capital-in (backer)**; for GOOGL,
  anthropic is **output/capital-out (holding)**.
- aggregation: two edges between same pair ⇒ one Counterparty with 2 relations.
- `formatTerms` renders usd/power/gpus compactly; unknown edge type ⇒ kind "related", still placed.
If vitest install is not feasible, fall back to `npx tsx web/lib/egograph.smoke.ts` asserting the same.
Verify phase also runs `tsc --noEmit` + `next build`.

## 5. Orchestration
Workflow, disjoint slices against this contract:
- **EGO-CORE**: `web/lib/egograph.ts` + `egograph.test.ts` (+ vitest setup) — TDD.
- **EGO-UI**: `web/components/CompanyValueChain.tsx` (new) + `web/components/MapExplorer.tsx` (extend) — code
  against the egograph contract; must not break the global view or the NodeDetailPanel aside.
Then verify (vitest/tsx + tsc + next build). Integration real-data smoke (buildEgoModel for NVDA over the
live site.json) + final `vercel --prod` done by the orchestrator.
