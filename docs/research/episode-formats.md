# Episode Formats — Non-Valuation Finance Reel Catalog

A companion catalog to [`viral-cheatsheet.md`](viral-cheatsheet.md) /
[`storytelling.md`](storytelling.md), which cover the **Myth-Bust / Contrarian Flip**
structure we've built episodes around so far (stock over/undervalued vs. a fundamental
model). This file is everything **beyond** that: mechanism explainers, macro storytelling,
historical parallels, investigations, rankings, scenarios, one-chart pieces, and the
recurring-segment wrappers that turn any of them into a series.

Grounded in a 2026-08 research pass across viral finance short-form (Kyla Scanlon, How
Money Works, Odd Lots, Coffeezilla, Josh Brown/The Compound, Unusual Whales, TBPN) — see
**Sources** at the bottom. Figures cited inline are **perishable**; re-verify before
scripting per this repo's Rule #1.

---

## 0. Our rig, in this catalog's terms

Every format below maps onto the same four rig elements (`halal-reels/src/QuarterlyReport.tsx`
+ `halal-reels/src/toon/studio.tsx` + `halal-reels/src/toon/host.tsx`). Read a format's
"Rig mapping" row against this table:

| Rig element | Component | What it's for in this catalog |
|---|---|---|
| **Anchor** | `<PremiumHost>` + a `HostTheme` (`HOST_ANCHOR` rose/pink, `HOST_ANALYST` blue, `HOST_QUANT` green+glasses) | The narrator. Swap theme to cast a second "character" for two-hander formats (bull vs. bear, detective vs. subject) without a new rig. |
| **Back-wall video wall** | `<NewsStudio wall={...}>` — the 992×1000 panel behind the anchor, currently a dotted world-map field + spotlight | The single-surface real estate for: a diagram (mechanism, loop, map/route), the historical-parallel split-screen, the tier-list board, or the "one chart." This is the format's real payoff surface — most formats below live or die on what goes here. |
| **Floating main screen** | the `screen` prop (currently `NVDA / 1.8× / UNDER a model`) | The punchy stat card — a single number, a countdown, a rank badge, a leaderboard row. |
| **Scrolling LIVE ticker** | the `ticker` string prop | A second read of the payoff for skimmers, or repurposed as a running leaderboard crawl / countdown text for series formats. |
| **Caption block** | `<Caption text hot>` word-highlight | Carries the hook/turn/button line; `hot` prop punches the one number or phrase. |
| **Title card + ep. counter** | `TitleCard` (`V&V` bug, "ep. N" subtitle) | Series branding — the ritual/numbering hook for recurring-segment overlays (§9). |

Beat-timing convention below follows `short-form-scripting`'s template (Hook 0-2s → Setup
2-6s → Turn 6-12s → Button 12-16s → CTA 16-20s) adapted per format; treat as a starting
allocation, not a hard rule.

---

## 1. Mechanism Explainer

**When to use:** the topic is "how does X actually work" — a system, not a stock call.
No ticker verdict; the payoff is a piece of machinery the viewer didn't understand before.

**Hook pattern:** cold open on a deceptively simple question, answered with a physical
analogy (pipes, a factory line, a loop) instead of jargon — e.g. *"How does the Fed
actually create money?"* or, for the 2026 AI-capex cycle, *"Nvidia sells a chip. The buyer
pays for it... with Nvidia's own money. Here's how."*

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | The naive question, on-screen | Anchor mid-scene, caption pops with VO word 1 |
| Setup | 2-6s | Name the 2-3 parties/steps | Back-wall starts drawing step 1 of the diagram |
| Turn | 6-12s | The mechanism completes — the counterintuitive twist | Back-wall diagram closes the loop/chain; floating screen shows the one number that proves it |
| Button | 12-16s | One reframing line ("so the same dollar just paid for itself twice") | Caption `hot`-highlights the punch phrase |
| CTA | 16-18s | Save (chart-dense) | Ticker repeats the mechanism in one line |

**Example in the wild:** Kyla Scanlon's whiteboard-style Shorts (Fed/labor mechanics);
Bloomberg's "AI Circular Deals" graphics piece for the Nvidia→OpenAI→Microsoft loop.

---

## 2. Market Plumbing / Liquidity Explainer

**When to use:** a specialized Mechanism Explainer for the unglamorous back-end — repo,
clearinghouses, dealer balance sheets, the reverse repo facility — where the payoff is
"why did markets suddenly freak out over something I'd never heard of."

**Hook pattern:** *"is this why—"* framing: name the scary headline event first, then
promise the invisible plumbing that caused it. Durable/evergreen — old explainers
resurface every time the plumbing clogs again (2019 repo spike, SVB, 2023 regional-bank
stress).

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | The scary headline stat | Floating screen shows the stress indicator |
| Setup | 2-6s | "Liquidity is water; here's the pipe" analogy | Back-wall draws the pipe/pressure diagram |
| Turn | 6-13s | Trace the clog to the visible symptom | Back-wall animates the pressure moving through the system to the headline event |
| Button | 13-16s | "And that's why it happened" | Caption punch |
| CTA | 16-18s | Save | — |

**Example in the wild:** Bloomberg's *Odd Lots* (Weisenthal & Alloway) — repo markets,
Treasury basis trade, clearinghouse margin calls, clipped to vertical.

---

## 3. Historical-Parallel ("this happened before")

**When to use:** today's data pattern-matches a past era (1970s stagflation, 1999
dot-com, 1987) and the audience wants a mental shortcut — with a credibility-protecting
twist about what's actually different this time. Also the home for **macro storytelling**
that needs a "we've seen this movie" frame.

**Hook pattern:** split-screen chart overlay, narrated as inevitability, then punctured:
*"We've seen this movie before... but here's the one thing that's actually different."*

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | Split-screen chart, two eras | Back-wall shows a literal side-by-side (two chart panels) |
| Setup | 2-7s | Narrate the parallel | Anchor voice-over, floating screen ticks the "then" number |
| Turn | 7-13s | The twist — what's actually different | Floating screen flips to the "now" number; back-wall highlights the divergence point |
| Button | 13-16s | Reframed one-liner, hedged | Caption `hot`-highlights the hedge word ("but") |
| CTA | 16-18s | Debate prompt ("same movie, or not?") | — |

**Example in the wild:** the 2026 resurfacing of a 1978 inflation-prediction column run
against Cleveland Fed unanchored-expectations research, "1970s vs 2026" cut across
finance TikTok — explicitly hedged as "no period is a perfect match."

---

## 4. Follow-the-Money Investigation

**When to use:** a concrete, verifiable anomaly exists — a filing, a disclosed trade, a
timing coincidence — and the format is a paper trail, not an opinion. This is the format
for anything sourced from `congress.json`-style filing data.

**Hook pattern:** open on the receipt itself (a redlined document, a specific dollar
figure, a filing date), not a summary — *"[Name] sold [ticker]. The law gave [N] days to
disclose it. [Name] took [N×k] days."*

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | The receipt on screen | Floating screen shows the filing as a document card |
| Setup | 2-6s | Who / what / the rule being tested | Anchor states the rule (STOCK Act 45-day window) |
| Turn | 6-13s | Walk filing → entity → timing → the gap | Back-wall lays out a beat-by-beat trail (arrow-linked cards); countdown-timer overlay on the floating screen |
| Button | 13-16s | The reveal number, deadpan | Caption punches the lag number |
| CTA | 16-18s | Genuine debate prompt ("is this legal? it's disclosed — still bothers you?") | Ticker crawls "SELF-REPORTED · UNVERIFIED · NOT AN ACCUSATION" |

**Example in the wild:** Coffeezilla's on-screen-document trail technique; Unusual
Whales' `I Am The Senate` congressional-trade drops; the two Subversive Congressional
Trading ETFs built entirely on this premise.

**Compliance note:** always label *reported / filed*, never *insider trading* — the
`conflict_signal.rationale` field in our own `congress.json` is explicit that a
committee/sector overlap is "correlational only — not evidence of wrongdoing." Carry that
caveat into the script, spoken, not just in a disclaimer card.

---

## 5. "The One Chart That Explains Everything"

**When to use:** one number, chart, or stat stack IS the entire episode — no narrative
arc needed, just authority-by-simplicity. Best when the chart is inherently
screenshot/share-able on its own.

**Hook pattern:** the chart fills the frame from second 1; the only VO is 2-3 annotation
callouts and one closing causal sentence — *"This is why your rent doubled."*

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-1s | Full-frame chart, no host visible yet | Back-wall IS the whole frame (host cut or shrunk to a corner inset) |
| Annotate | 1-10s | 2-3 callouts land on the chart in sequence | Back-wall gets sequential annotation pins/arrows |
| Turn | 10-14s | The one causal sentence | Floating screen shows the single derived number |
| Button | 14-17s | Mirror the opening frame (loop bait) | Caption restates the causal line |
| CTA | 17-19s | Save | — |

**Example in the wild:** M2-vs-asset-prices "one chart" format; the 1970s-vs-2026 CPI
overlay used as both thumbnail and payoff in one frame.

---

## 6. Macro Myth-Bust

**When to use:** a widely-held belief needs dismantling with rapid counter-facts — this
is the **macro/structural** sibling of our existing valuation Myth-Bust, but the target is
a system-level assumption (index diversification, "printing money to pay debt"), not a
single stock's price. Use this, not the valuation Myth-Bust template, whenever there's no
ticker-specific fundamental model involved.

**Hook pattern:** state the belief as obvious common knowledge, then flip it —
*"Your S&P 500 fund = instant diversification. Except..."*

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | State the belief as fact | Anchor states it flat, no irony yet |
| Setup | 2-5s | One more sentence reinforcing the false comfort | Floating screen shows the "expected" number |
| Turn | 5-12s | 2-3 rapid counter-facts | Back-wall bar/pie animates collapsing to the real number |
| Button | 12-16s | Reframed one-liner | Caption `hot`-highlights the real number |
| CTA | 16-18s | Debate prompt | Ticker crawls the source stat |

**Example in the wild:** "you don't own 500 stocks, you own 7" Mag7-concentration
framing (CNBC advisor-rotation coverage, Motley Fool Jan-2026 "should investors worry");
Humphrey-Yang-style budgeting/debt myth-busts.

---

## 7. Scenario / "If X, Then Y"

**When to use:** a conditional macro trigger (rate cut, capex pullback, a bridge node
failing) needs to be walked to a relatable end-state through a short causal chain —
explicitly hedged as one plausible path, not a prediction. This is the natural format for
our own `graph_analysis.json` **cascade scenarios** (`hyperscaler_capex_cut`,
`energy_bridge_loss`, `tsm_disruption` — each already carries a seed set, a direction, and
an `affected_count`/`reach` we can put straight on screen).

**Hook pattern:** *"If [trigger], then [domino 1] → [domino 2] → [what it means for
you]."* Hedge explicitly: "one plausible path, not a forecast."

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | State the trigger | Floating screen shows the seed node(s) lighting up |
| Setup | 2-5s | "Here's what happens next, in order" | Back-wall primes the dependency map |
| Turn | 5-13s | Walk 3-4 dominoes, cascade lighting up node-by-node | Back-wall animates the cascade spreading across the graph; floating screen ticks the running "% of stack affected" |
| Button | 13-16s | Land on the relatable end-state | Caption punches the reach % |
| CTA | 16-18s | "Follow — we'll check back if this plays out" | Ticker crawls the hedge line |

**Example in the wild:** Fed-meeting-week "if the Fed cuts here, then your mortgage/rent/
401k" explainer shorts, run every FOMC cycle by macro accounts.

---

## 8. Ranking / Tier-List

**When to use:** multiple comparable things (assets, decades, CEOs, or — for us — the
**five AI-stack layers** or individual nodes) need a fast, opinionated ordering. Built-in
disagreement-bait; low cognitive load per entry keeps completion high even at 20-30s.

**Hook pattern:** *"Ranking the AI stack by who breaks first."* Fast-cut tier reveal, one
punchy justifying line per entry — no deep dive on any single one.

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | Empty tier board, the premise | Back-wall shows an empty S/A/B/F (or numbered) board |
| Reveal | 2-14s | Each entry slots in with one line | Back-wall board fills in, tier by tier; floating screen shows that entry's one justifying number |
| Turn | 14-17s | The controversial placement (the one that'll get argued) | Caption punches the surprising entry |
| Button | 17-19s | Deadpan close | — |
| CTA | 19-20s | Explicit debate prompt ("fight me in the comments") | — |

**Example in the wild:** "ranking the worst market crashes" / "ranking every Fed chair"
finance-history shorts; mirrors the tier-list format's broader 2025-2026 short-form
dominance.

---

## 9. Money-Story / Human-Interest (covers behavioral/psychology content)

**When to use:** the topic is a single real (named or composite) person's decision and
consequence — this is the format for **behavioral/psychology finance content**: identify
the emotional stakes, not the data. Best when a stat alone would be forgettable but a
named person makes it stick.

**Hook pattern:** cold open mid-scene on the person's decision point — *"He took out a
50-million-won loan against his apartment to trade leveraged ETFs."* No macro framing
until after the person is established.

| Beat | Time | Content | Rig mapping |
|---|---|---|---|
| Hook | 0-2s | The decision, cold | Anchor introduces the person by name/role, no chart yet |
| Setup | 2-6s | What they did, in their own stakes | Floating screen shows their number (the loan, the loss, the gain) |
| Turn | 6-13s | The consequence | Back-wall shows the outcome as a single dramatic beat (a red/green number, a before/after) |
| Button | 13-16s | The universal lesson, understated | Caption lands flat, no moralizing |
| CTA | 16-18s | Debate / "would you have done the same" | — |

**Example in the wild:** Zach Yadegari's own cap-table/exit numbers posted as personal-
stakes content; the Fortune "retail sold into the rebound while institutions bought"
divergence (a two-character version: institution vs. retail trader).

---

## Cross-cutting: borrowable devices (not full formats — grafts onto any of the above)

These are single techniques lifted from named creators; use one per episode as a texture
layer, not a structure of its own.

| Device | Source creator | Grafts onto | How |
|---|---|---|---|
| **Napkin-math analogy hook** | Kyla Scanlon | Mechanism Explainer, Market Plumbing | Open on a tactile everyday analogy (concert-ticket resale = P/E ratio) before naming the real term |
| **Skeptical-question cold open** | How Money Works | Macro Myth-Bust, Follow-the-Money | Frame the whole episode as one incredulous rhetorical question ("why is X still allowed to...") |
| **Deadpan-tone-vs-absurd-content contrast** | Patrick Boyle | any | Flat delivery over an outrageous number is the joke — matches our existing deadpan sketch VO already |
| **Visible-citation, no-hype walkthrough** | The Plain Bagel | Mechanism Explainer, One-Chart | Show the source on screen; never end on a buy/sell verdict — buys evergreen re-share life |
| **Cinematic map/route animation** | Johnny Harris | Scenario, Mechanism Explainer | Physically "travel" the viewer through geography/supply-chain instead of talking-head explanation — our back-wall + `wall` prop can host a literal route diagram |
| **Multi-part evidence drip** | Coffeezilla | Follow-the-Money | Split one investigation into Part 1/2 with a cliffhanger tease, evidence-card cold opens each part |
| **Build-a-legal-case verdict structure** | Wall Street Millennial | Ranking, Follow-the-Money | Bull case → systematic dismantling → explicit contrarian verdict line |

---

## 10. Series & recurring-segment overlays (wrap any format above)

These don't replace a format — they turn a one-off into a returning segment. Add the
overlay device to whichever format above you're producing.

| Overlay | Mechanism | Rig mapping | Best paired with |
|---|---|---|---|
| **Ritual rapid-fire segment** | Same name, same graphic, same host catchphrase every time (Cramer's Lightning Round) | Title card gets a fixed segment bug in addition to the `V&V` bug | Ranking, Follow-the-Money quick-hits |
| **Persistent leaderboard** | A named, running list that gets revisited episode to episode with score-keeping ("up 40% since we added it in March") | Floating screen becomes a standing scoreboard card, reused verbatim across episodes | Ranking / Tier-List |
| **Insider-trade tracker leaderboard** | Continuously-updated "who traded what, did it move before news" dashboard | Ticker crawl becomes the running tracker text; floating screen shows this episode's new entrant | Follow-the-Money |
| **Fixed-cadence drop** | Same release day every week/cycle, same recurring cast | Title card's "ep. N" counter is the visible cadence marker | any, especially Historical-Parallel and Scenario (tied to Fed-day/earnings-day calendar) |
| **Sequential mechanism-explainer series** | Numbered Ep.1/2/3 building one mental model, each "the part nobody tells you" | End card's CTA becomes "Part 2: ___" instead of generic follow | Mechanism Explainer, Market Plumbing |

---

## Sources

- https://www.diyinvestor.net/finance-tiktok-report-card-75-of-viral-investing-videos-misleading-across-2025-2026/
- https://www.youtube.com/@KylaScanlon/shorts
- https://omny.fm/shows/odd-lots/lots-more-with-kyla-scanlon-on-the-economic-vibes
- https://www.indexbox.io/blog/inflations-second-wave-are-we-reliving-the-1970s/
- https://gizmodo.com/these-1970s-predictions-for-inflation-in-2026-show-things-could-be-a-lot-worse-2000735135
- https://www.johnrothe.com/p/are-we-headed-for-a-1970s-style-second
- https://www.youtube.com/@PBoyle
- https://outlierkit.com/resources/youtube-finance-niche-creators/
- https://creatorsagency.co/top-youtube-creators/finance
- https://www.opus.pro/blog/short-form-video-trends-reshaping-creator-marketing-2026
- https://www.bloomberg.com/graphics/2026-ai-circular-deals/
- https://www.cnbc.com/2026/07/27/jim-cramer-warns-ai-circular-financing-echoes-dot-com-bubble.html
- https://www.fool.com/investing/2026/07/11/is-the-ai-data-center-boom-creating-a-debt-bubble/
- https://finance.yahoo.com/technology/ai/articles/ai-data-center-boom-creating-163500585.html
- https://unusualwhales.com/congress-trading-report-2025
- https://unusualwhales.com/politics/insider_trades
- https://www.forbes.com/sites/investor-hub/article/what-is-unusual-whales/
- https://247wallst.com/investing/2026/03/17/will-legislation-finally-end-congressional-insider-trading-for-pelosi-and-others/
- https://www.morningstar.com/funds/2-etfs-that-track-congressional-stock-trades
- https://www.cnbc.com/2025/12/12/stocks-market-risks-investors-portfolios-2026.html
- https://www.fool.com/investing/2026/01/05/should-investors-be-worried-that-the-magnificent-s/
- https://www.investmentnews.com/equities/mag-7-for-tomorrow/264753
- https://www.ainvest.com/news/0dte-volatility-drives-market-strategies-2026-2602/
- https://harbourfronttechnologies.wordpress.com/2026/08/02/retail-participation-in-the-0dte-options-market/
- https://www.hooked.so/trends/tiktok/finance
- https://www.hooked.so/viral-videos/tiktok/finance
- https://www.thestreet.com/investing/kyla-scanlon-gen-z-economic-commentator
- https://variety.com/2026/tv/news/cnn-kyla-scanlon-financial-analyst-creators-1236781955/
- https://every.to/napkin-math/vibes-are-a-legitimate-economic-indicator
- https://fortune.com/2024/06/26/kyla-scanlon-tiktok-youtube-newsletter-economist-vibecession
- https://outlierkit.com/channel/howmoneyworks
- https://www.youtube.com/@HowMoneyWorks
- https://news.ycombinator.com/item?id=37503192
- https://www.theplainbagel.com/faq
- https://glasp.co/youtube/channel/UCFCEuCsyWP0YkP3CZ3Mr01Q
- https://en.wikipedia.org/wiki/Johnny_Harris_(journalist)
- https://aescripts.com/learn/post/how-johnny-harris-makes-maps
- https://www.dehek.com/general/scam-fraud-investigations/coffeezilla-exposes-a-300m-scam-this-is-what-real-investigative-journalism-looks-like/
- https://creatordb.app/creatorstats/coffeezilla/
- https://www.youtube.com/@wallstreetmillennial
- https://podcasts.apple.com/us/podcast/wall-street-millennial/id1616239843
- https://contentworks.agency/6-instagram-finance-reels-ideas-to-try-this-year/
- https://www.tiktok.com/channel/cramer-lightning-round?lang=en
- https://www.cnbc.com/2026/06/22/winners-win-josh-brown-on-three-winning-best-stocks-to-keep-riding.html
- https://www.cnbc.com/2026/05/11/these-capital-markets-names-on-josh-browns-list-have-been-big-winners-where-theyre-going-next.html
- https://unusualwhales.com/i_am_the_senate/senate
- https://www.tiktok.com/@quiverquant/video/7462056726465105198
- https://en.wikipedia.org/wiki/TBPN
- https://talkingbiznews.com/media-news/whats-behind-the-success-of-tbpn/
- https://shortyawards.com/18th/morning-brew-daily
- https://thereformedbroker.com/podcast/

**Internal:** rig components referenced above live at `halal-reels/src/QuarterlyReport.tsx`,
`halal-reels/src/toon/studio.tsx`, `halal-reels/src/toon/host.tsx`. Data sources referenced
in the mapping notes: `web/public/data/congress.json` (STOCK Act filings), `web/public/data/
graph_analysis.json` (AI-stack dependency graph, articulation points, cascade scenarios).
