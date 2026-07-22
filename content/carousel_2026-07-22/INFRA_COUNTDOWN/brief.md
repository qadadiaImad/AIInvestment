# AI-infra countdown reel — 2026-07-22 (Part 2 of the face-off series)

`infra_countdown.mp4` — 9:16, ~35s. Built with `remotion/src/compositions/InfraCountdown.tsx`,
data fixture `remotion/src/fixtures/infra_countdown_2026-07-22.json`.

Four AI-infrastructure names, same sector, revealed worst-to-best by discount
to modeled fair value. Each ticker expands into a 5-stat table (Price, Fair
Value, Discount %, Net Margin, Debt/Equity), Chip points at it, then it
collapses into the ranked rail at the bottom — every new reveal is the new
best-so-far, so it always lands at the front and pushes the rest back.

Reveal order (worst → best): **CIEN → ANET → AVGO → SMCI**

| Rank | Ticker | Vs. fair value | Net margin | Debt/equity |
|---|---|---|---|---|
| #1 (best) | SMCI — Super Micro Computer | +67.9% undervalued | +3.7% | 1.21 |
| #2 | AVGO — Broadcom | −25.5% overvalued | +38.8% | 0.74 |
| #3 | ANET — Arista Networks | −33.2% overvalued | +38.3% | 0.00 |
| #4 (worst) | CIEN — Ciena | −372.7% overvalued | +7.9% | 0.55 |

## IG caption

Four AI-infrastructure names. Same sector. Four completely different prices vs. what the fundamentals actually support.

We ranked them worst to best — not by hype, by the gap between price and modeled fair value. Watch the numbers build, then watch the ranking flip in real time as a better name knocks the previous "best" down a spot.

Quick honesty check: cheapest-vs-fair-value isn't automatically "best stock." Ciena and Arista both post excellent margins — they're just priced well ahead of the model right now. Broadcom is the highest-margin name in the group, still overvalued by our numbers. Super Micro is the value name here, but it also carries the most leverage of the four. Read the whole table, not just the rank.

Part 1 of this series (CRDO vs NET) is a few posts back if you missed it. Save this one — it's the framework, not just the ranking.

Educational only, not financial advice — DYOR.

#SMCI #AVGO #ANET #CIEN #aiinfrastructure #aistocks #semiconductors #datacenters #fundamentalanalysis #investing #trading #stocktrading #stockmarket #wallstreet

## Provenance

All figures: `web/public/data/site.json`, generated 2026-07-11. Ranking
metric = `valuation.fundamental_discount_pct` (positive = undervalued,
negative = overvalued vs. `valuation.fundamental_value`). Net margin and
debt/equity from `fundamentals`. No figures invented; NBIS/CRWV excluded
from this lineup per the earlier data caveat (their fundamental_value ==
price exactly in this bundle — no distinct model estimate, not a genuine
"fairly valued" signal).

## Compliance

- Dated footer on every frame: "Figures as of July 11, 2026 — educational,
  not financial advice."
- Framed as a valuation snapshot (price vs. modeled fair value), not a buy/
  sell signal — the caption explicitly warns against reading "most
  undervalued" as "best stock" and calls out each name's real fundamentals.
- No company named without its number traced to the bundle.
