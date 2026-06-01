# Fed-Rate → Revaluation → Earnings → Price Propagation on the AI Capital Graph
## Rigorous Methodology, Honest Feasibility, and a Phased Build Plan

*Generated against `web/public/data/site.json` (97 stocks, 392 edges). Data coverage independently re-verified by the synthesis agent against the live file, not assumed. Educational/research only — not investment advice.*

> Produced by a 5-specialist research workflow + synthesis (wx1z9amya). The synthesis agent
> re-checked every coverage claim against the live data before writing this.

---

## 1. What Is Rigorously Possible vs. Data-Limited

### Verified data facts (re-checked in `site.json`)
- `fundamental_value` 97/97 — but **7 names are price-anchored** (FV==price): CRWV, NBIS, TLN, GEV, FIG, NNE, OKLO (pre-profitable → DCF reprice is mechanical, not real).
- `fundamental_value_series` 90/97 (quarterly intrinsic path; the 7 above lack it).
- `beta` 97/97 — **market beta, not rate-duration**.
- `debt_to_equity` 96/97 (DELL null); `fcf_margin` 94/97 (19 negative); `roe/roic` 97/97 (GAAP, depressed for high-SBC SaaS); `pfcf` 74/97 (null for negative-FCF names).
- `annualTotalRevenue` 97/97 — **TSM is in TWD** (3.81e12); currency-normalize before any revenue-fraction math.
- Edges 392: infra_partner 205, customer 135, equity_stake 25, compute_commitment 25, subsidiary 1, voting_power 1. Certainty: filed 141, reported 244, **rumored 7**.

### The graph-coverage reality (the binding constraint)
- 9 edges carry top-level `usd`/`usd_per_month`; **~72/392 (18%)** carry *some* dollar once `transactions[].amount` is included.
- **The constraint is semantic, not numeric:** almost every dollar is either an **equity stake** (NVDA→COHR $2B, NVDA→MRVL $2B) — which generates **zero revenue** for the recipient — or a **multi-year TCV with no per-year term** — which can't become annual revenue without an assumed term.
- Only **~6 edges** resolve to a clean annual-revenue concentration; only **2 names (ANET, IREN)** clear a rigorous ≥15% coverage with filed/reported evidence.
- The bellwethers — **NVDA, TSM, MSFT, AMZN, GOOGL, AMD — have near-zero graph coverage** (NVDA ≈ 0.31%) because 10-Ks disclose "a small number of customers," never named with dollars.

| Capability | Verdict |
|---|---|
| Realistic Fed-path scenarios (calendar + market-implied + dots) | **Rigorously possible today, free.** |
| Per-node direct DCF/WACC revaluation (90 names) | **Defensible** as a duration overlay; ±30–40% model error. |
| Cross-sectional vulnerability ranking (97 names) | **Defensible** as *relative* ranking. |
| Graph-derived **earnings** estimate per node | **~2–6 names only.** ~85 names → `INSUFFICIENT_GRAPH_COVERAGE`. |
| Full-graph dollar earnings cascade | **Not possible** (83% of edges dollar-blind = false precision). |

**The model is a screening/ranking tool with a small high-confidence core — not a price-target engine.**

---

## 2. Fed Path — replace the slider with the real expected path (all free)
- **FOMC calendar (static):** 2026 dates hard-coded; flag the 4 SEP meetings (Mar/Jun/Sep/Dec).
- **Tier 1 — market-implied (yfinance, free, EOD):** ZQ fed funds futures `ZQM26.CBT, ZQN26, ZQU26, ZQV26, ZQZ26…`; `implied_rate = 100 − price`; mid-month FOMC day-weighting `(days_in_month/days_after_meeting)·(deferred−prior)/100` → step path = **base scenario**.
- **Tier 2 — SEP dots (FRED):** `FEDTARMD/RH/RL/MDLR`. Mar-2026 SEP: median 3.4%, central tendency 3.1–3.6%, neutral 3.1%. Cross-check ZQ vs dots.
- **Tier 3 — T-bill forwards (FRED fallback):** `DGS3MO…DGS30`, `DFEDTARU/L`.
- **Scenario bands:** base = ZQ path; bull = −25bps at next hold-priced meeting; bear = +25bps — brackets the SEP 100bps corridor without paid probability data.
- **Free vs paid:** ZQ (Yahoo) free; FRED free (needs a free API key — `fredgraph.csv` now 403s bare WebFetch); **CME FedWatch (~$25/mo) NOT needed** — derive from ZQ.
- **⚠ A0 IMMEDIATE FIX:** `macro_stress.py` baselines are stale (`dff=4.50` vs actual ~3.64 → 86bps off), inflating every current stress score. Wire `fetch_macro_snapshot()` to live FRED before anything ships.

---

## 3. Transmission Model (closed-form; only fields verified present)
**Channel A — DCF intrinsic-value repricing (90 names):** `ΔFV% = −D_2stage · Δr · 100`, two-stage duration from `WACC = ke·E/V + kd(1−tax)·D/V`, `ke = rf + beta·ERP`. Params labeled: `N=7`, `g_terminal=3%`, `ERP=5.5%` [constant — understates high-beta], `rf`=live FRED, `kd` spread **tiered by leverage** (IG +50–80bps … project-finance +400–600bps; flat 150bps rejected). Utilities (beta<0.2): halve duration (PUC recovery proxy). Verified ordering: L0-energy most rate-sensitive, L1-chips least.
**Channel B — financing→EPS (worst-case):** `EPS% = (D/E·Δr·(1−tax))·floating_fraction/(ROE/100)`. `floating_fraction` default 1.0 (worst case); realistic IG 0.15, sub-IG 0.35 — **the largest knob**. Suppress when ROE≤0 (→ `financing_distress_flag`) or D/E<0.3.
**Channel C — multiple compression:** do **NOT** add to A (already in terminal duration); narrative only.
**Channel D — commitment revaluation:** §6; only the ~6 annual-$ edges; equity stakes contribute 0 earnings.
**Combine (no double-count):** `FV_adj = FV·(1+ΔFV%); Price_stressed = FV_adj·(1−EPS_haircut)`.
**Caveats that travel with every output:** FVS tracks earnings trajectory not discount rate (A is an *overlay*); beta≠duration; ERP constant; 7 price-anchored names get null+flag.

---

## 4. Vulnerability Score (relative fragility, from our fundamentals)
```
V = (0.20·S_DE + 0.25·S_FCF + 0.10·S_CR + 0.20·S_ROIC + 0.15·S_VAL + 0.10·S_GR) / Σ(available weights)
S_FCF = 1 − pctile(fcf_margin)        # highest weight; low/neg FCF → fragile
S_DE  = pctile(D/E, cap99)            # leverage
S_CR  = 1 − pctile(current_ratio)     # liquidity
S_ROIC= 1 − pctile(roic)             # below rate hurdle
S_VAL = mean(pctile(pe,ps,pfcf))      # rich multiples derate more
S_GR  = pctile(rev_growth_yoy)        # priced-in growth
```
Cap at 99th pctile (pre-revenue outliers); renormalize over non-null signals. **Verified anchors:** most vulnerable CRWV ~0.90, IREN ~0.81, NRG ~0.74; most resilient DUOL ~0.21, ANET ~0.23, NVDA ~0.25. Shock modulation `effective_beta = beta·(1+α·(V−0.5))`, **α=0.60 uncalibrated** until backtested vs the 2022 cycle. Caveats: GAAP ROIC overstates SaaS fragility; utility negative-FCF = regulated capex not distress; relative + static as-of date.

---

## 5. Graph-Coverage / Confidence Metric + Gating
```
coverage_pct(node) = Σ (ARR_i · certainty_w_i) / annualTotalRevenue
ARR_i = annual amount (disclosed annual customer edge) | TCV/term (if term known) | 0 (equity_stake) | EXCLUDED+flag (TCV no term)
certainty_w: filed 1.0, reported 0.85, rumored 0.50
```
**Hard gate:** emit a graph-derived earnings estimate ONLY IF `coverage_pct ≥ 15%` AND ≥1 contributing edge is filed/reported (never solely rumored). Else `INSUFFICIENT_GRAPH_COVERAGE`.
**Verified gate result:** Tier A (confident) **ANET, IREN**; Tier B (forward caveat) NBIS, CRWV, ENTG, ASML; weak DLR, SO; **INSUFFICIENT** for ~88 incl. NVDA/MSFT/GOOGL/AMZN/TSM/AMD → default to fundamentals-only. Watch-out: DUK's "$10B AMZN" is campus capex, not annual PPA — overstates coverage ~30×.

---

## 6. Propagation (deterministic revaluation; SIR/threshold rejected)
94/97 have no near-term default risk → continuous DCF revaluation, not binary contagion (binary `financing_distress_flag` only for D/E>3 & FCF<0). Susceptibility `S_i = ⅓·min(D/E/5,1) + ⅓·(neg-FCF or pfcf/60) + ⅓·min(beta/4,1)`. Depth-1 propagation, three-tier transmission:
- **Tier 1** (annual $, ~6 edges) `w=annual$/rev_j` → HIGH-confidence earnings impact.
- **Tier 2** (multi-year $ + term) `w=(TCV/term)/rev_j` → MEDIUM (term-assumption risk).
- **Tier 3** (no $, 83%) `w=certainty·type_base` → **ORDINAL/DIRECTIONAL ONLY — never a $/% delta.**
`Δprice_j = −D_j·ΔWACC_j + PE_j·Δearnings_j`. **Graph Weakening Index** per layer = Σ S_i·|ΔFV/FV|·(out_degree/max). Structural facts (HIGH confidence regardless of $): 11 articulation points, 14 bridges → reliable cascade *ordering*. Caveats: TSM TWD; the largest edges (anthropic→GOOGL $200B, openai→MSFT $250B) are **private — unobservable as stocks**; depth-2 not computed.

---

## 7. Phased Build Plan (ship only what's defensible)
- **Phase A (ship first; HIGH confidence, no enrichment):** **A0** wire live FRED baselines (kills the 86bps-stale slider). **A1** FOMC calendar + ZQ-implied path + SEP cross-check → base/bull/bear scenarios replacing the slider. **A2** vulnerability score (§4) as a node attribute + ranking.
- **Phase B (single-node revaluation, 90 names):** Channels A & B with leverage-tiered kd, floating-fraction tiers, null+flag for price-anchored names; outputs at the realistic ZQ path + ±100/200/300. Enrichment to raise Channel B: EDGAR interest expense + fixed/floating split + maturity for the ~15 most-levered.
- **Phase C (graph propagation, HIGH-COVERAGE SUBGRAPH ONLY):** Tier-1 edges only (ANET←MSFT/META, ENTG←TSM, …); everything else `INSUFFICIENT_GRAPH_COVERAGE`. Highest-value enrichment: EDGAR 10-K customer-concentration for NVDA/TSM/AMD/AVGO/MU/ARM (lifts covered names ~9→20–30) + `term_years` on the 3 mega-TCV edges ($451.9B stranded for lack of a denominator).
- **Phase D (UI):** every number badged HIGH(filed)/MEDIUM(TCV-assumed)/LOW-STRUCTURAL/INSUFFICIENT; scenarios as **bands not points**; GWI per layer + articulation map. Deferred: Tier-2 full propagation, depth-2, private-node inference, α-calibration.

---

## 8. Discipline Rules (non-negotiable)
1. Never present a graph-derived number above its coverage confidence; <15% or rumored-only → `INSUFFICIENT_GRAPH_COVERAGE` (~88/97 incl. every bellwether).
2. Equity-stake $ ≠ revenue. 3. TCV ≠ ARR (never annualize w/o stated term; band ×0.6–1.4). 4. Tier-3 dollar-blind edges → ordinal stress only. 5. Currency-normalize TSM (TWD). 6. beta≠duration; ERP & α uncalibrated; price-anchored → null reprice. 7. Stamp `retrieved_at`/`source`/`source_class`; label fact/reported/rumored. 8. Survivorship: vulnerability is *relative to survivors*. 9. Static as-of date (blind to maturity walls). 10. Not investment advice; wide bands on sparse data.
