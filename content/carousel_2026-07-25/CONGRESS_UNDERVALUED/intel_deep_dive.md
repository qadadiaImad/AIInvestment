# Intel deep dive — the Pelosi filing, corrected, + the bull case

Supplements `brief.md`'s slide 1. Two things prompted this: (1) the original
slide oversimplified the filing — it's more specific and more interesting
than a flat stock purchase, and (2) there's a real, well-sourced positive
catalyst stack behind Intel right now that's worth telling alongside the
congress angle, not just the raw trade.

## The filing, corrected

Local `congress.json` (stamped 2026-07-11) recorded this as a plain "P"
(purchase), amount $1,000,001–$5,000,000. Fresher reporting (web, dated
late June 2026) fills in detail the local bundle doesn't have:

- It's **call options**, not common stock: 200 contracts, $50 strike,
  expiring March 19, 2027 — the right to acquire 20,000 Intel shares.
- It's filed under Nancy Pelosi's name (standard for congressional
  disclosure), but multiple outlets specify the trade was **executed by her
  husband, Paul Pelosi** — same filing, same day, alongside an identical
  options structure on Uber.
- Timing: transaction date May 29, 2026; filed June 23, 2026 — one day
  after a wave of Intel news (government-stake/Google/Tesla coverage, see
  below) broke around June 22.
- Context worth noting on-screen: Intel stock was already **up ~238% year-
  to-date** by the time this filing posted (Benzinga/Motley Fool) — this
  wasn't a contrarian bet, it rode a stock already in the middle of a huge
  re-rating.

**Dollar range, reconciled:** some outlets (Benzinga/Moneywise/TheStreet)
report "up to $6.00M" — but while building the rendered carousel it turned
out this exact filing was **already vetted in this repo**, in an untouched
`carousel_2026-07-22/INTC` slide from a prior session
(`remotion/src/fixtures/carousel_2026-07-22/intc_6_news.json`), which uses
the PTR-filed **$1M–$5M** range (200 calls, $50 strike, exp 3/19/2027 — same
details, independently arrived at). Going with **$1M–$5M** as the primary
figure since it matches the actual disclosed PTR bucket and was already
cross-confirmed once; the "$6M" figure some outlets cite most likely
aggregates this Intel position with the identical-structure Uber options
filed the same day. Noting the discrepancy here rather than silently picking
one.

**Corrected slide 1 script:** "Congress just filed it — Paul Pelosi bought
one to five million dollars in Intel call options." (14 words, ~5.8s)

Compliance note unchanged from `brief.md`: public record, dated, transparency
framing only — this describes what was filed, not a recommendation to mirror
it, and it's disclosing a spousal trade, not personally trading by the member.

## The Intel bull case (for the "why this matters" / positive-catalyst beat)

All items below are **reported/filed as of their cited dates** — label them
that way on-screen, don't flatten to "fact."

1. **US government took a 9.9% equity stake (Aug 2025), now worth ~$36B.**
   The Trump administration converted $8.9B of unpaid CHIPS Act grants +
   Secure Enclave program funds into 433.3M primary shares at $20.47/share —
   passive ownership, no board seat, votes with Intel's board on shareholder
   matters. Combined with CHIPS grants already paid, total US investment is
   $11.1B. The stake's mark-to-market value has roughly quadrupled to ~$36B
   as Intel's stock re-rated. *(Intel Newsroom; Manufacturing Dive; The Next
   Web, "US government's Intel stake is now worth $36 billion")*
2. **New hyperscaler/customer wins reported alongside the stake news.**
   Coverage around June 22, 2026 ties the government-stake story to Intel
   "landing Google and Tesla deals" — reported, not yet independently
   verified against a filing in this repo; flag as reported when used.
   *(Yahoo Finance, "Intel (INTC) Lands Google And Tesla Deals As U.S. Takes
   Equity Stake")*
3. **Apple confirmed as an 18A foundry customer (mid-January 2026).** Intel's
   US fabs are set to produce 18A silicon for Apple's entry-level Mac and
   iPad lines — a genuine foundry win from a marquee customer, not a rumor
   anymore (our own `capital_web.json` still had this tagged "rumored" as of
   its last edge update; treat the Apple relationship as upgraded to
   reported/filed per this later coverage). *(FinancialContent/Token Ring,
   CES 2026 coverage)*
4. **Panther Lake / Intel 18A shipped (CES 2026).** First commercial chips on
   Intel 18A — the company's most advanced node, designed and manufactured
   in the US. 180 TOPS AI performance, 50 TOPS NPU meeting the 2026
   "Copilot+" bar. Real caveat to keep in the room: 18A yields are still
   below profitable levels per reporting, not expected to hit target cost
   until "end of 2026 at the earliest" — this is a turnaround in progress,
   not a victory lap. *(Intel Newsroom; Winbuzzer, "Intel's 18A and 14A Bets
   Face Make-or-Break Year")*
5. **NVIDIA is now both a customer-partner and an equity holder.** Already in
   `capital_web.json`: NVIDIA's equity investment in Intel common stock
   completed December 2025, alongside a co-design deal for Intel to build
   NVIDIA-custom x86 CPUs/SOCs integrating NVIDIA RTX GPU chiplets. Two of
   the industry's biggest names are now financially and technically tied to
   Intel's outcome.
6. **Quantum computing — genuine research lead, not vaporware.** Intel's
   Tunnel Falls chip (12-qubit silicon spin-qubit device) is out in the
   research community; the Qubits for Computing Foundry program runs with
   Sandia National Labs, the University of Rochester, University of
   Wisconsin-Madison and others; Intel partnered with Japan's AIST on a
   next-gen quantum computer; Intel Capital backed Dutch quantum-chip
   startup QuantWare's €152M raise in 2026. Silicon spin qubits are Intel's
   specific bet — leverages the same fabs/expertise as its chip business,
   unlike competitors building exotic hardware from scratch. *(Intel
   Newsroom; DatacenterDynamics; Bloomberg)*
7. **Altera (Intel's FPGA unit) returned to growth on AI/robotics demand** —
   already surfaced in this repo's own `news.json` bundle (2026-07-11 stamp).

## Built as slide 2 (rendered)

This became its own carousel slide rather than folding into slide 1's
subtext: `slide_2_intel_bullcase_news.png`, kick "WHY IT'S IN THE NEWS",
4 news items (gov stake, Apple deal, NVIDIA, quantum), from
`remotion/src/fixtures/carousel_2026-07-25/slide_2_intel_bullcase_news.json`
via the `KurzSlide`/`kind: "news"` engine — same template as slide 1.

## Sources

- [Intel and Trump Administration Reach Historic Agreement](https://www.intc.com/news-events/press-releases/detail/1748/intel-and-trump-administration-reach-historic-agreement-to)
- [US government's Intel stake is now worth $36 billion](https://thenextweb.com/news/us-government-intel-stake-36-billion-chips-act)
- [US government to take 10% stake in Intel with CHIPS funding](https://www.manufacturingdive.com/news/us-government-10-percent-stake-intel-chips-funding-8-9-billion/758518/)
- [Intel (INTC) Lands Google And Tesla Deals As U.S. Takes Equity Stake](https://finance.yahoo.com/technology/ai/articles/intel-intc-lands-google-tesla-161236472.html)
- [Intel's 18A Era: Panther Lake Debuts at CES 2026 as Apple Joins the Intel Foundry Fold](https://markets.financialcontent.com/wral/article/tokenring-2026-1-15-intels-18a-era-panther-lake-debuts-at-ces-2026-as-apple-joins-the-intel-foundry-fold)
- [Intel Unveils Panther Lake Architecture: First AI PC Platform Built on 18A](https://newsroom.intel.com/client-computing/intel-unveils-panther-lake-architecture-first-ai-pc-platform-built-on-18a)
- [Intel's 18A and 14A Bets Face Make-or-Break Year](https://winbuzzer.com/2026/03/17/intels-18a-14a-roadmap-2026-foundry-panther-lake-xcxwbn/)
- [Intel Takes Next Step Toward Building Scalable Silicon-Based Quantum Processors](https://www.intc.com/news-events/press-releases/detail/1693/intel-takes-next-step-toward-building-scalable)
- [Intel partners with Japanese research institution for next-generation quantum computer](https://www.datacenterdynamics.com/en/news/intel-partners-with-japanese-research-institution-for-next-generation-quantum-computer/)
- [Intel's VC Arm Backs QuantWare](https://www.bloomberg.com/news/articles/2026-05-05/intel-capital-backs-quantum-computing-chips-startup-quantware)
- [California Rep. Nancy Pelosi Bought Up to $6.00M Worth of Intel Stock — Benzinga](https://www.benzinga.com/government/26/06/60073978/california-rep-nancy-pelosi-bought-6-00m-worth-intel-stock)
- [Nancy Pelosi's Husband Just Bought Jim Cramer's Favorite AI Chip Stock — Motley Fool](https://www.fool.com/investing/2026/06/26/nancy-pelosi-just-bought-jim-cramers-favorite-arti/)
- [Nancy Pelosi has new call options of up to $6M on Intel and Uber — Moneywise](https://moneywise.com/investing/stocks/nancy-pelosi-call-options-intel-uber)

## Compliance reminder

This section is written to inform a "why is Intel in the news" narrative —
it is **not** a recommendation. Every claim above is labeled reported/filed;
the 18A yield caveat is kept in deliberately so the bull case isn't one-
sided. Keep the "educational only, not financial advice — DYOR" disclaimer
on whatever slide/caption uses this material.
