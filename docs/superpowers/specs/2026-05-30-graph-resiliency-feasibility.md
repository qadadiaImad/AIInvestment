# Feasibility Report & Phased Plan — Graph Health & Resiliency (with Macro Stress)

**Feature:** Structural health, single-point-of-failure, and macro-stress overlay for the AI capital web on `/map`.
**Data sanity-checked against:** `web/public/data/site.json` and `scripts/aiinvest/capital_web.py` (live, 2026-05-30).
**Engine:** `networkx` (installed **3.3**), keyless FRED via `fred.py`.
*Educational/research only — not investment advice.*

> Produced by a 5-agent research workflow + synthesis; the synthesis agent re-ran the metrics
> live against `site.json` to verify the findings before writing this plan.

---

## 1. Verdict

**Feasible NOW for the structural/topology layer and a transparent Health Score. Partially feasible for macro stress (as an ordinal/indicative overlay, not a dollar-impairment estimate). Cascade simulation is feasible only as a structural-reachability + threshold model; true financial contagion (DebtRank/Eisenberg-Noe) needs data we do not have.**

Headline metrics reproduce cleanly against `site.json`:

| Metric | Live re-run | Status |
|---|---|---|
| Nodes / edges | 106 nodes; **342 directed** after DiGraph dedup (392 incl. parallel multi-edges) | ✅ |
| PageRank top | TSM 0.1744, ARM 0.0699, NVDA 0.0596 | ✅ |
| In-degree top | NVDA 38, AMZN 26 (DiGraph collapses parallels) | ⚠️ multigraph parallels inflate counts |
| Articulation points | 11 (`AMZN, KMI, SO, DELL, spacex, TSM, NVDA, META, MSFT, GEV, GOOGL`) | ✅ |
| Bridges | 14 | ✅ |
| Non-trivial SCCs | 31-node + 4-node | ✅ |
| USD-valued edges | **9 / 392** | ✅ |
| equity_stake w/ pct | 3 / 25 | ✅ |
| termination_days | 1 (`anthropic→spacex`) | ✅ |
| Isolated nodes | 7 (`CCJ, HUBB, OKE, PEG, SMR, TRGP, WDC`) | ✅ |
| Layers | L0=32, L1=27, L4=21, L2=20, private-lab=6; **no L3** | ✅ |
| certainty | reported 244, filed 141, rumored 7 | ✅ |

**Bottom line:** unweighted topology is analytically rich and shippable today. The single most
investment-relevant finding — **TSM's PageRank (0.174) ≈ 3× NVDA's (0.060)**, identifying TSM as the
*deeper* systemic hub behind NVDA — is real and reproducible. Anything needing per-edge dollars or
per-node balance sheets must be labeled "indicative / structural," not "economic / dollar loss."

---

## 2. Recommended Technique Stack

**Graph metrics (P1 — all `networkx`, computable now):** directed degree (in/out), PageRank (the
TSM-dominance headline), betweenness (chokepoints; NVDA dominant), eigenvector (undirected
projection), articulation points + bridges (SPOF list), k-core (×2: all-edges and capital-only =
`equity_stake`+`compute_commitment`), strongly-connected components (the 31-node loop = contagion
amplifier), targeted-vs-random percolation → **fragility ratio**, degree assortativity (−0.37, hub-and-spoke).

**Contagion (P3):** primary **Independent Cascade Model** with certainty-mapped transmission probs,
traversed **reverse** for demand shocks / **forward** for supply shocks; **Linear Threshold** complement;
weighted directed reachability (BFS/DFS) baseline ships in P1. **Rejected for cause:** Eisenberg-Noe
(debt-clearing semantics don't fit commitment/stake edges), GNN/TOPSIS-entropy (no failure labels);
**DebtRank deferred** pending dollar/equity enrichment.

**Macro overlay (P2):** keyless FRED (`DFF`, `DGS10`, `APU000072610`) → rule-based per-edge-type
elasticity multipliers (hand-calibrated betas, not regressed — the graph has no time series).

**UI (P4):** reuse the existing `vis-network` HTML in `capital_web.to_html()` — modulate edge
color/opacity by `stress_score`, node size/badge by health score.

---

## 3. "Graph Health & Resiliency Score" — Definition

Two-tier, **[0,100]**, higher = healthier. Tier shown in UI so readers know structural vs. economic.

### Tier 1 — Topology Score (all 99 connected nodes, no enrichment)
```
Score_topo(node) =
    30 * Concentration   # 1 − HHI_indegree/10000  (edge-count HHI of inbound counterparties)
  + 30 * SPOF            # 1.0 if NOT an articulation point; else max(0, 1 − 5*BC_norm)
  + 25 * Redundancy      # log1p(in_degree)/log1p(max_in_degree)
  + 15 * Certainty       # mean incident-edge certainty weight {filed:1.0, reported:0.7, rumored:0.3}
```
Each sub-component normalized to [0,1] **within its layer**, weighted, ×100.
**Guardrails:** SCC-31 members capped at 85/100 (peer shock can arrive via the cycle); single-in-edge
nodes floored at 40/100 + flagged `topology estimate`; isolates → `no data`, excluded from aggregates.
**Companion:** Effective Number of Suppliers `ENS = 10000/HHI` (e.g. anthropic HHI≈5672 → ENS≈1.8).

### Tier 2 — Economic Score (~30 nodes with $; rest after enrichment)
Replace Concentration with dollar-weighted, certainty-discounted HHI:
`dollar_HHI = Σ (certainty_w·usd_i/total_usd)² · 10000`, then macro multiplier (§4):
`Score_final = Score_econ · (1 − clamp(stress_delta, −0.15, +0.15))`.

### Per-layer & Overall
Per-layer mean + band + tier counts (indicative: L4-app ≈57, L0-energy ≈58 most fragile; L1/L2 ≈68).
Overall = node scores weighted by `(in_degree+out_degree)` so hub health dominates. Bands: red<50, amber 50–70, green>70.

---

## 4. Macro → Edge-Weight Stress Mechanism

Three channels, each a keyless FRED series, returned as a **separate overlay dict** (never mutate the
source graph). Per edge: `stress_score ∈ [0,1]` (1=unstressed) + `stressed_weight` + provenance.

Base weight for the 383 unsized edges (proxy, not a dollar substitute):
`w_base = certainty_w × type_base_weight`, `type_base_weight = {compute_commitment:3, equity_stake:2, voting_power:2, subsidiary:2, customer:1, infra_partner:1}`.

**Channel 1 — Rates (`DFF`,`DGS10`):** `stress = max(0, 1 − beta·Δrate_bps/100)`, betas per +100bps:

| Edge type / source | beta | Rationale |
|---|---|---|
| compute_commitment, neocloud (CRWV/NBIS/IREN) | 0.12 | floating-rate private credit; heavy off-B/S leases |
| compute_commitment, hyperscaler (MSFT/AMZN/GOOGL/META) | 0.03 | IG, huge FCF |
| equity_stake (corp → private lab) | 0.08 | high multiples compress on higher discount rate |
| customer | 0.02 | indirect via buyer capex |
| infra_partner | 0.01 | structural, long-dated |

Termination amplifier: `termination_days ≤ 90` → ×1.5 on `(1−stress)`; 91–180 → ×1.2.
**Channel 2 — Electricity (`APU000072610`):** L2-infra stressed by `gamma·Δelec_pct` (gamma 0.15);
L0-energy outbound margin-*positive*; propagated via the 26 L0↔L2 power edges.
**Channel 3 — Rate-regime trigger:** `DFF ≥ 5.5%` → extra −0.15 on all `rumored` edges.
Baselines: DFF 4.50, DGS10 4.25, ELEC 0.142 $/kWh. Unit scenario +100bps; headline +200bps / +30% elec.
> Honest limit: electricity is *residential* avg (proxy, not DC PPA); with 9 dollar edges all macro output is an **indicative ordinal** signal, never a dollar loss.

---

## 5. Phased Plan

- **P1 — Static metrics + Tier-1 score (now, zero new data):** `scripts/aiinvest/graph_metrics.py` (DiGraph + undirected projection from `site.json`; degree/PageRank/betweenness/eigenvector; APs/bridges; k-core ×2; SCCs; assortativity; targeted-vs-random percolation) + `health_score.py` (Tier-1) + reachability baseline. TDD on synthetic fixtures. **Deliverable:** per-node/layer/overall scores + SPOF list + fragility ratio.
- **P2 — Macro overlay:** `macro_stress.py` (`fetch_macro_snapshot()` + `stress_graph()` 3 channels) → Tier-2 multiplier. TDD: neocloud commitment impairs > hyperscaler at equal Δrate.
- **P3 — Cascade:** `contagion.py` ICM (filed 0.85 / reported 0.6 / rumored 0.25) + LTM; scenario presets (TSM disruption forward; hyperscaler capex cut reverse; GEV energy-bridge loss).
- **P4 — UI on `/map`:** extend `to_html()` — edge color/opacity ← stress, node badge ← health, ring SPOFs, flag SCC-31, per-node breakdown tooltip + ENS + tier, overall gauge + FRED stress-scenario toggle.

---

## 6. Data Gaps & Enrichment

| Gap (verified) | Impact | Enrichment |
|---|---|---|
| 9/392 edges have USD (0/135 customer, 0/205 infra_partner) | no dollar-weighted metrics | add `usd` to ~20 top edges (hyperscaler→NVDA capex; compute/equity from 8-K/press) |
| 3/25 equity_stake have pct | no voting-weighted eigenvector | ownership % from filings |
| 1/25 compute_commitment has termination_days | `termination_risk()` near-empty | extract exit clauses from filings |
| no per-node fundamentals | macro betas stay blunt per-layer | pull mcap/rev via `tradingview.py`; power intensity for L0/L2 |
| private nodes have no equity | DebtRank undefined | reported valuations as "soft equity" |
| no L3-models layer | app-layer model contagion unrepresentable | relabel labs into L3 or document proxy |
| single timestamp, no edge validity windows | no temporal analysis; 90-day & 10-yr edges identical | time-slice builder; use `transactions[]` dated records |
| 7 isolates | contribute nothing | exclude from aggregates (recommended) |
| DiGraph collapses parallels (392→342) | in-degree overstated (NVDA 46→38) | decide MultiDiGraph vs DiGraph; document |

---

## 7. Risks & Caveats (surface in UI)

1. **Small, curated, survivorship-biased graph** (~3.5% density). Absence of an edge ≠ absence of a relationship; score overstates hub resilience and peripheral fragility.
2. **Uneven dollar coverage (2.3%)** — weighted outputs dominated by 9 edges. Present as "indicative," never "dollar loss"; keep Tier-1 unweighted as the honest default.
3. **No edge timestamps/durations** — locked long contracts treated like 90-day-exit edges; rate stress hits refinancing, not locked price.
4. **Macro betas are analyst priors, not measured** (no time series → no regression). Certainty weights uncalibrated.
5. **SPOF flags coverage-sensitive** — one missing alt-supplier edge can fabricate an articulation point.
6. **DiGraph vs MultiDiGraph + networkx 3.3** — pin version + edge convention before locking thresholds.
7. **Rejected models rejected for cause** — Eisenberg-Noe / SIR are semantic mismatches; would launder meaningless numbers.

---

## 8. Rough Effort

| Phase | Effort |
|---|---|
| P1 static metrics + Tier-1 score (~250–350 LOC) | 2–3 days |
| P2 macro overlay (~150–200 LOC) | 1.5–2 days |
| P3 cascade ICM+LTM (~150–250 LOC) | 2–3 days |
| P4 `/map` UI | 2–3 days |
| Enrichment (parallel; gates Tier-2/DebtRank quality) | 3–5 days, ongoing |

**Core P1–P4 ≈ 8–11 days; P1 alone ships an honest "structural health" view in 2–3 days.**

*Provenance: metrics re-run live against `site.json` on 2026-05-30 (networkx 3.3); all headline figures confirmed against real data. Not financial advice.*
