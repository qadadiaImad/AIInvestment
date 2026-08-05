---
name: finance-reel-formats
description: >
  Pick a NON-valuation finance-reel FORMAT for a V&V Quarterly Report episode (we already
  over-use over/undervalued myth-busts). Catalog: mechanism-explainer, market-plumbing,
  historical-parallel, follow-the-money investigation, one-chart, macro-myth-bust,
  scenario/cascade, ranking/tier-list, money-story — each mapped to our anchor + broadcast
  studio + back-wall chart + ticker + our own data (congress.json, graph_analysis.json).
  Use BEFORE writing a new episode that isn't a valuation call. Triggers: "new episode",
  "episode idea", "different format", "not valuation", "reel concept", "what format".
---

# Finance Reel Formats — beyond valuation

Use this to choose a format for a new **V&V Quarterly Report** episode, then hand off to
`short-form-scripting` (beats) + `viral-voiceover-audio` (VO). We've done valuation
myth-busts (ep1/ep2), a news-jack (ep3), and a human-stakes story (Korea) — this catalog is
the *rest*. Full beat sheets + sources: [`docs/research/episode-formats.md`](../../../docs/research/episode-formats.md). New concepts: [`docs/research/new-episode-concepts.md`](../../../docs/research/new-episode-concepts.md).

## Our rig = the format's surfaces
- **Anchor** `<PremiumHost theme=…>` — HOST_ANCHOR (plum) / HOST_ANALYST (navy) / HOST_QUANT (green+glasses). Swap theme = a second character for two-hander formats (bull vs bear, detective vs subject).
- **Back-wall** `<NewsStudio wall={…}>` — the payoff surface: a diagram, split-screen, tier board, cascade map, or the "one chart." Most formats live or die here.
- **Floating LIVE screen** (`screen` prop) — the punch stat / countdown / rank badge.
- **Ticker** (`ticker` prop) — a second read for skimmers, or a running leaderboard/countdown.
- **Caption** word-highlight + **title card "ep. N"** for series ritual.

## Pick a format

| # | Format | Use when | Hook pattern | Our data source |
|---|---|---|---|---|
| 1 | **Mechanism Explainer** | "how does X actually work" — a system, no ticker call | naive question → physical analogy (pipes/loop/factory) | `graph_analysis.json` edge_stress (e.g. the circular AI deals) |
| 2 | **Market-Plumbing** | back-end (repo, clearing, liquidity) freaked markets out | "is *this* why—" name the scary event, reveal the plumbing | macro/liquidity headlines |
| 3 | **Historical-Parallel** | today pattern-matches a past era, with a "what's different" twist | split-screen two eras → puncture it | a chart + a dated past analog |
| 4 | **Follow-the-Money** | a verifiable filing/trade/timing anomaly — a paper trail | open on the *receipt* (doc + exact number), not a summary | `congress.json` trades + `reporting_lag_days` |
| 5 | **One-Chart** | one chart IS the whole episode (share-able alone) | full-frame chart from sec 1, 2-3 annotations, one causal line | any single strong series |
| 6 | **Macro Myth-Bust** | a system-level belief needs dismantling (not a stock) | state the belief as obvious → flip with rapid counter-facts | e.g. "you own 7 stocks, not 500" (concentration) |
| 7 | **Scenario / If-X-Then-Y** | a conditional trigger → cascade → what it means for you | "if [trigger], then domino→domino→you" (hedged) | `graph_analysis.json` cascades (seeds, affected_count, reach) |
| 8 | **Ranking / Tier-List** | order N comparable things fast; built-in debate-bait | "rank the AI stack by who breaks first. Go." | `graph_analysis.json` layers (health) + top_spofs |
| 9 | **Money-Story** | one named/composite person's decision + consequence (behavioral) | cold open on the decision, no macro until the person lands | a named case (like the Korea leverage trader) |

## Borrowable devices (graft one on for texture, not structure)
Napkin-math analogy hook (Kyla Scanlon) · skeptical-question cold open (How Money Works) ·
deadpan-vs-absurd contrast (Patrick Boyle — matches our VO) · visible-citation no-hype
(The Plain Bagel) · cinematic map/route on the back wall (Johnny Harris) · multi-part
evidence drip / Part 1-2 (Coffeezilla) · build-a-case verdict (Wall Street Millennial).

## Series overlays (turn a one-off into a returning segment)
Ritual rapid-fire segment · persistent leaderboard (floating screen = standing scoreboard) ·
insider-trade tracker crawl (ticker) · fixed-cadence "ep. N" drop · sequential numbered
mechanism series (CTA = "Part 2: ___").

## Compliance (non-negotiable, esp. Follow-the-Money)
Label everything **reported / filed**, never "insider trading" — our own `congress.json`
`conflict` fields say overlaps are "correlational only — not evidence of wrongdoing." Carry
that **spoken**, not just on a card. Ticker crawls "SELF-REPORTED · NOT AN ACCUSATION."
Late-filing = a disclosure-timing fact (legal but slow), not an allegation of a crime.
Numbers are perishable — re-pull the data file and re-verify figures right before scripting.
