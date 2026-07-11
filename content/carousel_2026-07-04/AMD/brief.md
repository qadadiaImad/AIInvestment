# AMD — Carousel Brief (2026-07-04)

## Caption
AMD, up +282% in a year and ~140% YTD (reported 07-03), now trades at $517.82 — 116.8% above the $238.81 the analysts' model will underwrite. This carousel walks the gap: what the market is paying ~170x earnings for (AI-accelerator momentum, +34.97% revenue growth vs a 13.8% industry median), what the model anchors on (7.6% ROIC, 47.1% gross margin), and why, after a year like that, the multiple itself becomes the risk. Reported catalyst chatter is labeled as reported — none of it is confirmed, and none of this is a recommendation. Educational — not financial advice.

## Posting order
1. slide_1 — HOOK (soft): price curve + 1-year return + reported YTD/catalyst hook
2. slide_2 — SET-UP (dark): $517.82 vs $238.81 → +116.8% above the model (premium, not prediction)
3. slide_3 — BUILDING BLOCKS (dark): ratios vs semiconductor industry medians + top-factor call-out
4. slide_4 — WALKTHROUGH CONT. (dark): the 169.9x multiple decomposed vs 66.3x median; the risk sentence
5. slide_5 — NEWS + CLOSE (soft): two reported items (07-03) + educational/NFA/DYOR beat

## Walkthrough (third person, momentum-vs-model)
AMD closed July 3 at $517.82 after a +282.07% year, while the analysts' model pins fundamental value at $238.81 — the price sits 116.8% above what the model will underwrite. That gap is best read as a premium the market is paying, not a prediction either side has already won. The premium is not irrational on its face: revenue grew +34.97% year over year against a semiconductor industry median of +13.8%, EPS grew +123.35%, and gross margin at 47.1% clears the industry's 35.9% median. But the model anchors on what today's economics can carry — a 7.6% ROIC and current cash flows — and those inputs simply do not reach $517. The stock's 169.9x trailing earnings multiple runs about 2.6x the industry's own median of 66.3x, which quietly assumes the past year's growth keeps compounding rather than being one strong cycle. After a +282% run, the multiple itself is the primary risk: results can come in strong and the stock can still stall if they merely match what is priced in. Reported catalyst talk for 2026 remains exactly that — reported, not confirmed.

## Higgsfield hero prompt (4:5)
Editorial macro photograph of an AI accelerator die on dark silicon, extreme close-up of the chip's mirrored surface and micro-circuitry, lit by a single emerald light source (#34D399) against a near-black background (#0A0D12), shallow depth of field, faint green reflections tracing the interconnect lines, premium financial-editorial mood, high contrast, clean composition, no text, no logos, no people, 4:5 portrait.

## Sources
All figures verbatim from repo data files; no external figures used.

| Figure | Value | File | Timestamp |
|---|---|---|---|
| Price (07-03 close) | $517.82 | web/public/data/site.json stocks.AMD.valuation.price | as_of 2026-07-04T14:29:21Z |
| Fundamental value | $238.81 | site.json stocks.AMD.valuation.fundamental_value | 2026-07-04T14:29:21Z |
| Premium above model | 116.8% (fundamental_discount_pct -116.8) | site.json stocks.AMD.valuation | 2026-07-04T14:29:21Z |
| P/E (TTM) | 169.9x (169.94978...) | site.json stocks.AMD.valuation.pe | 2026-07-04T14:29:21Z |
| 1-year performance | +282.07% | site.json stocks.AMD.performance.perf_1y | 2026-07-04T14:29:21Z |
| YTD (headline "~140%") | +136.56% actual | site.json stocks.AMD.performance.perf_ytd | 2026-07-04T14:29:21Z |
| Revenue growth YoY | +34.97% | site.json stocks.AMD.fundamentals.rev_growth_yoy | 2026-07-04T14:29:21Z |
| EPS growth YoY | +123.35% | site.json stocks.AMD.fundamentals.eps_growth_yoy | 2026-07-04T14:29:21Z |
| Gross margin | 47.09% | site.json stocks.AMD.fundamentals.gross_margin | 2026-07-04T14:29:21Z |
| ROIC | 7.64% | site.json stocks.AMD.fundamentals.roic | 2026-07-04T14:29:21Z |
| Industry median P/E | 66.3x (66.3341..., n=65) | site.json stocks.AMD.peer_comparison.industry.price_earnings_ttm.median | 2026-07-04T14:29:21Z |
| Industry median gross margin | 35.9% (n=137) | site.json ...industry.gross_margin_ttm.median | 2026-07-04T14:29:21Z |
| Industry median ROIC | -2.13% (n=134) | site.json ...industry.return_on_invested_capital.median | 2026-07-04T14:29:21Z |
| Industry median revenue growth | +13.83% (n=136) | site.json ...industry.total_revenue_yoy_growth_ttm.median | 2026-07-04T14:29:21Z |
| Price curve | last 250 closes | web/public/data/prices/AMD.json | file as of 2026-07-04 |
| Headline + 2 news items | reported 07-03 | detect-stage deferred news (verbatim, "reportedly" framing) | 2026-07-04 |

Note: slide 3/4 use valuation.pe (169.9x, July-3 close) for the company; the peer table's own price_earnings_ttm.value (190.66x) is a different snapshot basis and was not mixed into the slides. Industry medians match aiinvest.peers.scan_industry("Semiconductors") output embedded in site.json.

Educational — not financial advice.
