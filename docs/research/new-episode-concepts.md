# New Episode Concepts — Beyond the Valuation Myth-Bust

> Educational/research only — not financial advice. Format decisions are grounded in
> [`episode-formats.md`](episode-formats.md); every fact below is either (a) a *live*
> field in our own committed data bundles (`web/public/data/congress.json`,
> `web/public/data/graph_analysis.json` — both timestamped `2026-08-05`) or (b) a cited
> outside figure, marked as such. Re-verify anything outside-cited against a primary
> source before scripting/VO — see this repo's Rule #1. Every concept below deliberately
> uses a **different catalog format** than our existing valuation-model Myth-Bust
> episodes (NVDA vs. a fundamental model, etc.) and than each other.

---

## Concept 1 — "The Loop That Pays For Itself"

| | |
|---|---|
| **Format** | Mechanism Explainer — Circular-Loop variant (`episode-formats.md` §1) |
| **Cold-open hook** | *"Microsoft invests in OpenAI. OpenAI spends it on Microsoft's cloud. Nvidia invests in OpenAI. OpenAI spends it on Nvidia's chips. Nobody's lying. It's just... circular."* |
| **Cast character** | `HOST_QUANT` (glasses, green blazer) — the numbers-person persona, delivered flat/deadpan |
| **Data source** | `web/public/data/graph_analysis.json → edge_stress`: `MSFT→openai` (`equity_stake`, weight 1.4) + `openai→MSFT` (`compute_commitment`, weight 2.1); `NVDA→openai` (`equity_stake`, weight 0.6) + `openai→NVDA` (`compute_commitment`, weight 2.1) — the loop is a real, structured pair of edges in our own dependency graph, not an illustration borrowed from an article. Capper stat: `top_spofs` lists NVDA (betweenness 0.113) and MSFT (0.072) as the two single points of failure with the highest structural centrality in the whole 117-node graph. |

**Structure (beat sheet):**
1. **Hook (0-2s):** the two-sentence loop, spoken flat, back-wall starts drawing arrow 1 (MSFT→OpenAI).
2. **Setup (2-6s):** arrow 2 completes the loop (OpenAI→MSFT) on the back-wall — a closed circle now visibly on screen.
3. **Turn (6-13s):** repeat the pattern for NVDA↔OpenAI (second closed loop, back-wall now shows two interlocking circles); floating screen shows the two betweenness numbers as "these two names are structurally impossible to route around."
4. **Button (13-16s):** *"That's not a scandal. That's just what a supply chain looks like when there are only three buyers."* — deliberately declines to call it a bubble or a fraud.
5. **CTA (16-18s):** save (chart-dense); ticker crawls "STRUCTURAL, NOT A DOLLAR-LOSS ESTIMATE — SEE graph_analysis.json DISCLAIMER."

**Why different from our valuation myth-busts:** zero ticker verdict, zero "over/undervalued vs. a model." The entire payoff is *showing the machinery* of how three counterparties' money and compute move in a circle — the audience leaves informed about a mechanism, not told to buy or sell anything.

**Why it works:** this is the single most-cited 2026 "is this a bubble" narrative in the outside research (Bloomberg's *AI Circular Deals* graphic, Cramer's dot-com comparison, Motley Fool/Yahoo debt-bubble pieces) — but we can render it from our *own* structured graph data instead of citing someone else's diagram, which is a genuine differentiator only an AI-stack-literate, graph-modeling channel can do.

**Caveat:** `graph_analysis.json`'s own disclaimer calls these edges "structural/indicative; not a dollar-loss estimate" — say that on screen, don't imply the stress_score is a probability of default.

---

## Concept 2 — "917 Days Late"

| | |
|---|---|
| **Format** | Follow-the-Money Investigation (`episode-formats.md` §4) |
| **Cold-open hook** | *"The law says 45 days. He took 917."* |
| **Cast character** | `HOST_ANALYST` (blue blazer) — plays the detective/narrator walking the paper trail |
| **Data source** | `web/public/data/congress.json → trades`: Rep. Richard Dean "Dr." McCormick (GA-06) bought MSFT on 2023-03-15, filed 2025-09-17 — a `reporting_lag_days` of **917** against the STOCK Act's 45-day disclosure window. Second beat, same file: Rep. Lisa McClain (MI-09) bought NVDA, AMD, and TSM on the *same day* (2024-03-11), filed 2025-08-13 — a 520-day lag, and all three names are core AI-stack tickers this channel covers. |

**Structure (beat sheet):**
1. **Hook (0-2s):** the receipt — a filing-document card on the floating screen: "MSFT · BUY · 03/15/2023."
2. **Setup (2-6s):** state the rule — STOCK Act, 45 days, on-screen as a countdown-timer graphic that immediately blows past its own deadline.
3. **Turn (6-13s):** the filing date lands — 09/17/2025 — countdown overlay reads "917 DAYS." Second card cuts in: Lisa McClain, same-day buy of NVDA + AMD + TSM, 520-day lag — "the whole chip stack, one filing, a year and a half late."
4. **Button (13-16s):** *"Both fully disclosed. Both fully legal. Neither one in a hurry."*
5. **CTA (16-18s):** genuine debate prompt — "legal ≠ comfortable — where's your line?"; ticker crawls "SELF-REPORTED · UNVERIFIED STOCK ACT FILINGS · NOT AN ACCUSATION OF WRONGDOING."

**Why different from our valuation myth-busts:** this is an accountability/transparency story about *disclosure timing*, not a fundamentals-vs-price argument — there is no model, no multiple, no "undervalued" claim anywhere in it.

**Why it works:** matches the most established finance-content genre outside valuation takes (Unusual Whales' congressional trackers, the two Subversive Congressional Trading ETFs) — but ours is sourced from our *own* scraped filing dataset with an exact, real, almost-absurd lag number as the hook, rather than a generic "Congress trades stocks" framing.

**Caveat:** `congress.json`'s own `disclaimer` and `conflict_signal.rationale` fields are explicit — amounts are reported ranges, filings are self-reported/unverified, and any committee/sector overlap is "correlational only, not evidence of wrongdoing." Say the "not an accusation" line on screen, not just in a caption card.

---

## Concept 3 — "If Big Tech Blinks"

| | |
|---|---|
| **Format** | Scenario / "If X, Then Y" (`episode-formats.md` §7) |
| **Cold-open hook** | *"If the four biggest AI spenders cut their budgets 10% tomorrow, here's what happens to the other names you own — in order."* |
| **Cast character** | `HOST_ANCHOR` (narrator) handing off to `HOST_QUANT` for the "and here's the number" beat — a two-hander |
| **Data source** | `web/public/data/graph_analysis.json → cascades`: scenario `hyperscaler_capex_cut`, seeds `["MSFT","AMZN","GOOGL","META"]`, direction `reverse`, `affected_count: 66`, `reach: 0.493` — i.e. **49% of the tracked 117-node AI-stack graph** sits downstream of a hyperscaler capex pullback. Optional second seed for a follow-up episode: `energy_bridge_loss` (seed `GEV`, forward, `affected_count: 55`, `reach: 0.342`). |

**Structure (beat sheet):**
1. **Hook (0-2s):** the trigger stated as a conditional, floating screen lights up the four seed logos (MSFT/AMZN/GOOGL/META).
2. **Setup (2-5s):** "here's what happens next, in order" — back-wall primes the dependency map (nodes dimmed, waiting).
3. **Turn (5-13s):** cascade animates outward from the four seeds, nodes lighting up one tier at a time; floating screen ticks a running counter up to "66 names · 49% of the stack."
4. **Button (13-16s):** *"That's not a forecast. That's just what 'downstream' means when four companies are the whole demand side."*
5. **CTA (16-18s):** "follow — we'll check back if capex guidance actually moves"; ticker crawls "ONE MODELED SCENARIO, NOT A PREDICTION."

**Why different from our valuation myth-busts:** forward-looking and conditional rather than a snapshot judgment on today's price — the entire content is "if trigger, then propagation," with the payoff being a structural reach percentage, not a verdict on any single ticker's valuation.

**Why it works:** mirrors the proven Fed-meeting-week "if the Fed cuts here, then your mortgage/rent/401k" causal-chain format that recurs every FOMC cycle — except our seed event and cascade math are computed from our own dependency graph instead of a general macro narrative, which is a claim a generalist finance account can't back up with real data.

**Caveat:** cascade `reach`/`affected_count` are graph-connectivity measures (how much of the tracked universe sits downstream), not a dollar-impact or probability estimate — say so explicitly in the button beat.

---

## Concept 4 — "Rank the AI Stack: Who Breaks First"

| | |
|---|---|
| **Format** | Ranking / Tier-List (`episode-formats.md` §8), with the Wall-Street-Millennial "build-a-case" device grafted on as a two-hander debate |
| **Cold-open hook** | *"Five layers hold up the entire AI trade. Rank them by who breaks first. Go."* |
| **Cast character** | `HOST_ANALYST` vs. `HOST_QUANT` — the two blazer themes stage an on-screen disagreement over placement |
| **Data source** | `web/public/data/graph_analysis.json → layers` mean health scores across our own AI-stack taxonomy (CLAUDE.md §0.4's Energy→Chips→Infra→Models→App): `L4-application` 53.6 (lowest), `L0-energy` 58.0, `L1-chips` 65.2, `private-lab` 66.4, `L2-infra` 66.7 (highest) — plus `top_spofs` for the single-point-of-failure name inside each tier (NVDA for chips, MSFT/AMZN/GOOGL for infra, GEV for energy). |

**Structure (beat sheet):**
1. **Hook (0-2s):** empty five-slot tier board on the back-wall, premise stated.
2. **Reveal (2-14s):** each layer slots in, worst-health first — Application (53.6) drops into the bottom tier, then Energy (58.0), then Chips (65.2), then private labs (66.4), then Infra (66.7) takes the top tier; floating screen shows each layer's mean-health number and its one SPOF name as the justifying line.
3. **Turn (14-17s):** the controversial placement — Infra (Microsoft/Amazon/Google's own cloud layer) ranks *healthiest*, not Chips (Nvidia) — flagged as the one viewers will argue with.
4. **Button (17-19s):** `HOST_ANALYST` and `HOST_QUANT` land on opposite one-liners, deadpan, no resolution.
5. **CTA (19-20s):** explicit debate prompt — "fight it out in the comments — which layer actually breaks first?"

**Why different from our valuation myth-busts:** it's cross-sectional and structural — ranking five layers of a value chain against each other — rather than a single stock's price against a fundamental model; there's no "over/undervalued" claim anywhere, only a relative-health ordering.

**Why it works:** tier-lists are a native, low-cognitive-load, built-in-disagreement format (2025-26's dominant short-form structure per the creator-marketing trend research); pairing it with our own proprietary layer taxonomy and health scores means the ranking itself is content only this channel can produce — a generalist finance account has no equivalent dataset to rank against.

**Caveat:** layer "health" is our own composite score (concentration/SPOF/redundancy/certainty components per `graph_analysis.json`), not a market-standard metric — define it on screen in one clause so the ranking doesn't read as an external rating agency's view.

---

## Recommendation — Build First: Concept 2 ("917 Days Late")

**Build Concept 2 first.**

1. **Single most concrete, least-hedged fact of the four.** A `reporting_lag_days` of 917
   against a hard 45-day legal deadline is a real number pulled straight from our own
   `congress.json`, with a primary-source PDF link already in the record — nothing here
   needs re-verification against an outside article before scripting, unlike the Bloomberg-
   sourced circular-financing figures in Concept 1.
2. **Zero valuation-adjacent compliance risk.** It makes no price, multiple, or buy/sell
   claim at all — the safest concept to publish while we're still establishing a
   non-valuation format, and the easiest to keep clearly labeled *reported/filed, not an
   accusation*.
3. **Fastest to produce.** Needs one document-card graphic + one countdown-timer overlay
   on the existing `NewsStudio` rig — no new diagram type, no cascade-animation build (unlike
   Concepts 1 and 3), no two-host debate blocking (unlike Concept 4).
4. **Proven format, fresh data.** Congressional-trade content is the most established
   non-valuation finance-content genre in the research; ours is the first version of it
   built on our *own* scraped filing dataset rather than a third-party tracker screenshot.

**Sequencing after that:** Concept 1 (circular loop) next — it rides the single hottest
2026 "AI bubble" narrative and is the strongest differentiator once the team is ready to
build the two-interlocking-loop back-wall diagram; Concept 4 (tier-list) third, since it
needs the two-host debate blocking worked out; Concept 3 (cascade scenario) last — it is
the most technically ambitious back-wall animation (node-by-node cascade lighting) and
benefits from having Concepts 1's diagram-drawing techniques already built.

**Before building anything:** both `congress.json` and `graph_analysis.json` are
timestamped `2026-08-05` — re-pull fresh copies immediately before scripting per this
repo's Rule #1 (numbers are perishable), and confirm the specific `reporting_lag_days`
and cascade `reach` figures cited above still match the live file.
