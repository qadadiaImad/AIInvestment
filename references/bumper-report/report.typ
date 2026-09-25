// Bumper Radar research report. Build: typst compile report.typ report.pdf
// Figures: cd scripts && python -m bumper.report_figs

#set document(title: "Bumper Radar: what predicts the next sector leader, and what does not", author: "AIInvestment research engine")
#set page(paper: "a4", margin: (x: 1.9cm, y: 2.1cm), fill: rgb("#0b0f17"), numbering: "1", number-align: center,
  header: context { if counter(page).get().first() > 1 [ #text(size: 8pt, fill: rgb("#6b7280"))[Bumper Radar · research report · 2026-09-25 · educational only] ] })
#set text(font: "Source Sans 3", size: 10.5pt, fill: rgb("#e5e7eb"), lang: "en")
#set par(justify: true, leading: 0.62em)
#set heading(numbering: "1.")
#show heading.where(level: 1): it => { pagebreak(weak: true); v(4pt); text(size: 20pt, weight: 700, fill: rgb("#22e07e"))[#it]; v(8pt) }
#show heading.where(level: 2): it => { v(9pt); text(size: 12.5pt, weight: 700, fill: rgb("#e5e7eb"))[#it]; v(3pt) }
#show figure.caption: set text(size: 8.5pt, fill: rgb("#9ca3af"))
#show link: set text(fill: rgb("#60a5fa"))
#set table(stroke: 0.4pt + rgb("#1f2937"), fill: (x, y) => if y == 0 { rgb("#111827") } else { none })

#let green = rgb("#22e07e")
#let red = rgb("#ff3b30")
#let amber = rgb("#f59e0b")
#let muted = rgb("#9ca3af")
#let card(title, body, color: green) = block(fill: rgb("#0e131d"), stroke: (left: 3pt + color), inset: (x: 11pt, y: 9pt), radius: 3pt, width: 100%)[
  #text(weight: 700, fill: color)[#title] #v(2pt) #body ]
#let stat(n, label) = box(width: 24%, inset: 6pt)[#align(center)[#text(size: 26pt, weight: 700, fill: green)[#n] #linebreak() #text(size: 8.5pt, fill: muted)[#label]]]

// ---------------------------------------------------------------- cover
#v(2.2cm)
#text(size: 11pt, fill: green, weight: 700)[AIINVESTMENT · RESEARCH]
#v(4pt)
#text(size: 30pt, weight: 700)[Bumper Radar]
#v(2pt)
#text(size: 16pt, fill: rgb("#cbd5e1"))[What predicts the next sector leader, and what does not]
#v(14pt)
#text(size: 10.5pt, fill: muted)[An empirical study of every US-listed name that multiplied since 2021, an 82-agent research workflow over the winners, the failures and the literature, and the detector design that follows. Compiled 25 September 2026. Educational research only; not investment advice.]
#v(1.4cm)
#align(center)[
  #stat("336", "winners: ≥5× in 5y or ≥3× in 3y, cap ≥ $1B")
  #stat("300", "industry-matched look-alikes")
  #stat("0.48", "AUC of R&D intensity: a coin flip")
  #stat("1.7%", "of IPOs return >500% in 3 years")
]
#v(1cm)
#card("The one-paragraph answer")[
  Three months before a run, nothing in the financial statements tells a future bumper apart from the company next to it that goes nowhere. R&D intensity, revenue growth, runway: all coin flips. The only ratios that separate at all are inverted: winners were lower-margin, cash-burning, diluting and beaten-down. The early information lived in filing _text_ and _relationships_: named customers with binding terms, capacity being built, insiders and strategics putting capital in, and a new story stated in a mandatory filing. But every one of those also appears in the graveyard, so the detector that survives scrutiny is one that _disqualifies first_ on the signals that separated collapses from survivors, promotes only on delivered evidence, and has a judge that narrates a band rather than inventing a probability.
]

// ---------------------------------------------------------------- 1
= The question, and why fundamentals cannot answer it alone

The owner's brief: find small caps that will lead a sector that is not yet profitable, as the 2020 AI names, Nebius or IonQ did, _before_ the market re-rates them. Fundamental analysis describes how a company behaves; it does not give the probability that it becomes the leader. This report tests that intuition on data, then asks what does carry information.

Two independent lines of work were run on the same day and only then combined:

- *Empirical study* (`scripts/bumper/`). Every US-exchange common stock that returned at least 5× over five years or 3× over three years and has a market cap of \$1B today (336 names), against 300 controls from the same industries whose five-year return sits between −80% and +100%. For each winner the run start is the _first_ 12-month window returning 2.5× (what a live screen could catch, not the best window in hindsight). Features come from the actual SEC XBRL filings available three months before that month; controls are measured at run months drawn from the winners' distribution so market regime does not leak in.
- *Research workflow* (82 Sonnet agents). Eighteen winner case studies built from opened filings, four cohorts of the 2020–22 names that collapsed, four literature sweeps, two data inventories, family-level adversarial verification, three detector designs and two independent judges.

#figure(image("fig/r01_cohort.png", width: 100%), caption: [The cohort. Runs cluster in 2023 and 2024: the sector wave decides the timing more than the company does. Green sectors are the emerging-technology subset used for the tighter comparisons.])

// ---------------------------------------------------------------- 2
= Three months before the run, the filings say nothing

#figure(image("fig/r02_auc.png", width: 100%), caption: [Area under the curve, winners versus matched look-alikes, per feature. 0.5 means a random winner is no more likely to score higher than a random control. Blue: all 336 winners. Green: technology names with a market cap under \$2B at run start, the population the owner cares about.]) <auc>

The headline is @auc. On the population that matters, technology small caps, revenue growth scores 0.51, revenue acceleration 0.48, R&D intensity 0.48 and cash runway 0.50. Share-count growth is the only feature above 0.55, and it says winners _raised more equity_. Below the line, the inversions: gross margin at 0.28 and operating cash flow at 0.35 mean the eventual winners were the lower-margin, cash-burning businesses; prior momentum at 0.33 and drawdown at 0.35 mean they were the beaten-down ones.

#figure(image("fig/r03_distributions.png", width: 100%), caption: [The distributions behind three of the numbers, technology subset. The R&D panel is the owner's hypothesis: identical shapes.])

#card("What this does and does not mean", color: amber)[
  It does not mean fundamentals are useless: they are the disqualifiers of chapter 4. It means a screen built on ratios will rank IonQ, QUBT and their eventual graveyard twins side by side, because at that stage they _are_ side by side. Two caveats. XBRL coverage is about 45% of the cohort (foreign issuers and pre-revenue names drop out), and the winner list is current listings only, so a name that ran and then delisted is not counted. The "beaten-down" pattern is regime-dependent: it holds for runs starting in 2022–23 and reverses for 2025 starts.
]

#figure(image("fig/r04_paths.png", width: 100%), caption: [Normalised price paths, technology subset: median and interquartile band, 24 months before to 12 months after run start. Winners spent two years flat to down, indistinguishable from the controls, before the run. The animated companion draws these paths in one by one.])

// ---------------------------------------------------------------- 3
= Where the early information lived

The eighteen case studies (NVDA 2015, AMD 2016, ENPH 2018, TSLA 2019, PLTR 2023, SMCI, VRT, NBIS, IREN, APLD, CRWV, IONQ, RGTI, QBTS, ASTS, RKLB, OKLO, SOUN) were built by opening the 10-Ks, 8-Ks, S-1s and press releases of the period and dating each observable signal. The pattern is consistent: the information was in text and relationships, and it was free.

#figure(image("fig/r05_families.png", width: 100%), caption: [Leading signal instances by family across the case studies, with the median lead before the run. Every instance was knowable from public sources at the time.])

#table(columns: (auto, 1fr, auto), align: (left, left, left),
  [*Family*], [*Typical instance (from opened filings)*], [*Lead*],
  [Anchor customer / contract], [NVDA names Facebook and Alibaba as Tesla-GPU users in its FY2016 10-K; VRT backlog; APLD hyperscaler leases], [9 mo],
  [Capacity / capex], [TSLA Shanghai from groundbreaking to production in under a year; NBIS, IREN, APLD GPU fleets; SMCI Taiwan plant], [8 mo],
  [Insider / institutional], [Strategic stakes and 13D filings; note that bare insider _selling_ preceded PLTR's and TSLA's runs, so direction alone misleads], [10 mo],
  [Financing / dilution], [Equity raised into a plan (TSLA May 2019 \$2.35B) versus equity raised to survive; the decomposition matters, not the amount], [9 mo],
  [Narrative in filings], [NVDA's FY2015 10-K already sells "deep learning"; the CEO reframes the company around four growth vectors nine months before the print], [9 mo],
  [Revenue inflection], [Mostly confirming, not leading: the quarter the market re-rates is the quarter growth shows up], [7 mo],
  [Price and flow], [Extreme short interest at the low (AMD ~25% of float at \$2, TSLA ~23%); regime-dependent], [6 mo],
)

// ---------------------------------------------------------------- 4
= The graveyard: what separated collapses from survivors

Every family above also appears in the names that lost 80 to 99%. Nikola had General Motors, Lordstown had Foxconn, Canoo had Walmart, Arrival had a UPS letter of intent with no deposit and no cancellation penalty. So the verification pass downgraded all ten families to "supporting". What did separate the collapses, while both cohorts still looked identical on price, is a short list of checkable facts:

#card("Disqualifiers, all dated and filed", color: red)[
  - Binding contracts with deposits and delivered units, versus orders, pre-orders and letters of intent. Read the risk-factor language, not the press release.
  - A disclosed runway number and its rate of compression (cash divided by trailing-quarter burn), not the cash balance.
  - Share-count trajectory: more than 25 to 40% annual growth funding losses is structural.
  - Customer-as-financier and related-party structures: revenue that is circular.
  - Going-concern or material-weakness language in a filing: a bright line, searchable on EDGAR full text.
  - Executive departures tied to a funding gap or an audit-committee investigation (Item 5.02), versus "personal reasons".
  - Exchange-compliance notices and late filings (Item 3.01, NT 10-K): the market's own tripwire.
  - What management does after its first credibility hit: Hyliion killed its own unproven product and survived; Nikola did not.
]

// ---------------------------------------------------------------- 5
= Base rates and the literature

#figure(image("fig/r06_base_rates.png", width: 100%), caption: [Three-year buy-and-hold outcomes of 9,195 US IPOs, from Jay Ritter's tables opened during the workflow. The bumper outcome is the thin right tail.])

The base rate for the exact population the owner targets is poor: unprofitable-at-IPO issuers return −30.7% market-adjusted over three years, de-SPAC mergers −74.7%, and only about 1.7% of IPOs exceed +500%. Bessembinder's finding that the best 4% of listed companies account for all net wealth creation is the same fact from the other side.

Of the published signals, two point the right way and were actually opened: opportunistic insider _purchases_ (Cohen, Malloy and Pomorski 2012, about 80 basis points a month in-sample, since decayed) and customer–supplier economic links (Cohen and Frazzini 2008), which is precisely what this repository's capital-web graph encodes. Attention and lottery signals point the wrong way: extreme daily moves (Bali, Cakici and Whitelaw 2011), high idiosyncratic volatility, retail herding and search-volume spikes all predict worse returns. McLean and Pontiff (2016) find that published predictors lose about half their power after publication; any signal here will decay once systematised.

// ---------------------------------------------------------------- 6
= The detector both judges chose

Three designs were produced from different angles and scored independently by a quant-researcher judge and a fundamental-PM judge. Both chose the evidence-first, disqualification-first design, because it is the only one whose architecture follows from the study's own finding that no core signal exists.

#figure(image("fig/r07_funnel.png", width: 100%), caption: [Bumper Radar. Gates cap the score; promoters are conditional on delivered evidence; supporting signals are capped; the judge narrates a band and never overrides the number.])

== The judge agent

*Inputs:* the deterministic score and every gate flag; the supporting-signal values with their measured AUC; the base-rate table; data coverage for the name; the graveyard-versus-winner discriminator library. *Output:* one of four bands (abstain on thin data; avoid, matches a failure pattern; watch, thin evidence; watch, favourable but unvalidated) and exactly three reasons, each a one-sentence claim with a filing URL and retrieval date, labelled filed, reported or rumoured. *Guardrails:* educational framing only; cite or abstain; no override authority over the score; no brokerage data ever enters the pipeline. A devil's-advocate pass briefed only on the graveyard runs before any band is final.

== Validation before forecasting

The backtest follows the repository's edge-detection method: a point-in-time universe from filings accepted on or before each date; gate thresholds fitted once on a training era and frozen; filings clustered into independent events (three 10-Qs showing one compressing runway are one event); the three gates of separation, detection lag and edge survival; four eras (pre-2019, the 2019–21 boom, the 2022–23 bust, the 2024–25 AI-infrastructure boom); and the number of variants tried recorded as the denominator of any significance claim.

// ---------------------------------------------------------------- 7
= Today's screen

#figure(image("fig/r08_today.png", width: 100%), caption: [Quantum, physical-AI and AI-infrastructure names on 25 September 2026: R&D intensity against cash runway, bubble sized by market cap. The runway gate at two years is the only line the study supports; the horizontal position, the owner's R&D hypothesis, carries no information on its own.])

The chart is a description, not a ranking. IonQ spends 1.8 dollars on research per dollar of revenue with about four years of runway; Rigetti 5.5 with four and a half; QUBT 2.7 with eighteen, after its raises. Serve Robotics and SoundHound sit below the runway gate; CoreWeave sits far below it on free cash flow but is financed by debt against contracted revenue, which is exactly the kind of case the binding-demand check exists to adjudicate rather than a ratio.

= Next steps

Two weeks of work, in the order the judges scored highest: the point-in-time universe builder; the going-concern, runway-compression, governance and exchange-notice gates as pure functions with fixture pairs (Nikola against Enphase) in the tests; the binding-demand check that only credits a contract once a later filing shows delivered units; the scorer; the backtest harness on the winners and the graveyard; the judge as a Sonnet sub-agent; then an adversarial review hunting look-ahead paths before any live name is scored.

#v(8pt)
#text(size: 8.5pt, fill: muted)[Provenance. Empirical study: TradingView scanner cohorts, Yahoo monthly adjusted closes, SEC XBRL companyfacts; code and tests in `scripts/bumper`, outputs in `data/bumper/2026-09-25`. Workflow result and every cited URL in `data/bumper/2026-09-25/workflow_result.json`. Base rates from Ritter's IPO tables (University of Florida, August 2026 edition). Not financial advice; small-cap and pre-profit names carry a large probability of permanent loss.]
