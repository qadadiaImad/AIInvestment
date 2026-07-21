# Skool Monetization Roadmap — AI STACK

> **The thesis in one line:** Instagram carousels + reels are the *traffic engine*,
> the Vercel app is the *proof-of-work and lead magnet*, and Skool is the *capture
> and monetization layer*. You already own the hardest part — an automated content
> factory fed by live, stamped data. Almost nobody in fintwit/finsta has that.
>
> *Everything below inherits the repo's rails: educational only, not financial
> advice, fact vs. rumor labeled, NFA footer on every public asset.*

---

## 0. Why this can work (your unfair advantages)

Most finance creators screenshot someone else's terminal. You have:

| Asset | What it is today | Role in the funnel |
|---|---|---|
| **Data engine** (`scripts/`) | Live TradingView/Yahoo/GuruFocus/EDGAR/FRED pulls, dossiers, screener, freshness flags | The credibility moat — "every number is live and stamped" |
| **Vercel app** (`web/`) | Map (capital web), screener, per-stock pages, news, congress, quantum | Lead magnet + proof-of-work; the thing people screenshot |
| **Carousel generator** (`higgs/_build_v4.py`, `stock-carousel` skill) | 4:5 fundamental-value slides, free/local | Daily IG traffic at ~zero marginal cost |
| **Reel engine** (`higgs/make_reel.py` + workflow) | Narrated 9:16 reels, ~18 Higgsfield credits each | Reach engine (Reels/TikTok/Shorts, same file) |
| **Daily brief generator** (`content/daily_brief/`) | One-command daily market brief + chart | The paid-tier deliverable, already automated |
| **Congress + capital-web data** | Trades by committee, who-funds-whom graph | The viral hooks nobody else can generate on demand |
| **Review dashboard** (`review/`) | Comment/feedback loop per post | Built-in content-quality iteration |

The differentiator to hammer in every post: **"I don't repost headlines — I built a
terminal that pulls the numbers live."** That's the identity people join a Skool for.

---

## 1. Answer to the opening question

**Yes — but with the roles assigned correctly:**

- **Instagram carousels/reels = traffic.** Skool communities grow almost entirely
  from short-form content → profile → link-in-bio → community. Carousels are the
  right format for fundamental breakdowns (saves + shares = IG's favorite signals).
- **The Vercel app ≠ traffic.** Nobody discovers a web app organically at this
  stage. Its job is (a) screenshots/screen-recordings *inside* the content
  ("here's my own AI-stack map"), and (b) the free goodie that makes joining the
  community a no-brainer.
- **Skool from day one, free.** Don't wait for an audience to "be ready." Open the
  free community before the first post goes out so every view from post #1 has
  somewhere to land. Monetize only after the free tier is alive (Phase 4).

Order of operations: **positioning → content cadence → free Skool → app as magnet
→ paid tier.** Not the reverse.

---

## 2. Phase 0 — Positioning & offer (Week 1, before posting)

1. **Niche statement** (bio, Skool about page, every CTA):
   > *"Data-driven investing across the AI value chain — energy → chips → clouds →
   > models → apps. Live numbers, no hype, no advice."*
   The stack framing (from `references/investing-brief.md`) IS the brand. It's a
   mental model people can't get from a generic "stocks" page.
2. **The transformation you sell** (Skool is bought for outcomes, not content):
   *"Learn to read an AI stock like an analyst: where it sits in the stack, what
   the fundamentals say, where the capital flows."*
3. **One persona, everywhere.** You already enforce a consistent creator persona in
   the UGC pipeline (`higgsfield-ugc`) and an emerald visual palette. Lock the
   handle/name/avatar across IG, TikTok, Skool, and the app header.
4. **Compliance rails, verbatim and always:** educational / not financial advice
   footer (already in the reel script rails), congress content framed as
   *transparency, not accusation*, rumors labeled *reported/filed* (CLAUDE.md rule
   #5). Finance niches get reported; the rails are also protection.
5. **Set up the funnel plumbing now:** link-in-bio → free Skool; Skool about page
   → app link; app header → "Join the community" button. Add UTM params so you can
   see which content converts.

**Exit criteria:** bio live, free Skool created (even with 5 seed posts), app has a
visible join CTA.

---

## 3. Phase 1 — The traffic engine (Weeks 1–6): Instagram first

### Cadence (all of it is already automated — this is the moat)

| Content | Source pipeline | Frequency | Marginal cost |
|---|---|---|---|
| Fundamental-value carousel (hottest stock) | `stock-carousel` skill / `_build_v4.py` | 4–5×/week | ~8 credits (hero) or 0 if reusing heroes |
| Narrated reel (stock or congress story) | `make_reel.py` + workflow | 2–3×/week | ~18 credits |
| Capital-web map post ("who funds whom") | screenshot/animation of `web/app/map` | 1×/week | 0 |
| Daily brief story/post | `content/daily_brief/` generator | daily (Stories) | 0 |

That's ~60–80 credits/week — budget it, and post *daily* something. Consistency
beats brilliance on IG; you're one of the few who can sustain daily without burnout
because the factory does the work.

### Content pillars (mapped to what performs in finance short-form)

1. **"Explain the price"** — the stock-carousel format: sector-relevant ratios vs.
   industry, one subjective walkthrough of the top factor. Saves magnet.
2. **Congress trades** — highest raw-engagement hook in the niche; you generate it
   from your own data, framed as transparency. 1–2/week max (don't become "the
   Pelosi page").
3. **Capital web** — "Microsoft → OpenAI → CoreWeave → NVIDIA: follow the money."
   The map page renders this visually; nobody else has this asset. Most shareable
   pillar and the most brand-defining.
4. **Quantum outliers** — smaller audience, fiercely engaged, low competition.
5. **Build-in-public** — occasional reel of the terminal/app itself ("I built my
   own Bloomberg for the AI stack"). This pillar converts followers → community
   members better than any other, because the app is the thing they want access to.

### Mechanics that matter

- **Every post ends with the same CTA:** "Full breakdown + the live screener in the
  free community — link in bio." One CTA, always the same destination.
- **First slide = hook only** (number + tension: "NVDA at 36% below GF Value — trap
  or gift?"). Your generators already produce the data slide; make slide 1 hook-only.
- **Cross-post reels to TikTok + YouTube Shorts unedited** — they're already 9:16.
  Zero extra work, 2–3× the surface area.
- **Use the review dashboard** weekly: keep what got saves/shares, kill what didn't.
  You built a feedback loop; point it at engagement metrics, not just copy quality.

**Exit criteria:** 6 weeks of unbroken cadence, ≥1 pillar clearly outperforming,
first ~50–100 community members from content alone.

---

## 4. Phase 2 — The Vercel app as lead magnet (parallel, Weeks 2–6)

The app's job: make "join free" feel like getting a $50/mo product for $0.

1. **Ship a `/join` page** on the app: what the community is, screenshot tour, one
   button → Skool. All bio links point *here or directly to Skool* (test both).
2. **Feature the app in content, don't wait for organic discovery.** Screen-record
   the map, the screener sort, a dossier page. "This is what members use."
3. **Light gating, later:** keep map/news public (shareable), but once traffic is
   real (Phase 4), gate the screener and full dossiers behind free signup →
   that signup lives in Skool. Free tier keeps the goods; the *gate* is community
   membership, not money.
4. **Analytics:** Vercel Analytics + UTM on every bio/caption link. You need to
   know: content → app → Skool click-through, or content → Skool direct.

**Deliberately NOT now:** accounts/auth, paid app subscriptions, mobile app. The
app is a magnet, not the product. Don't let engineering joy (the easy part for you)
displace posting (the part that actually grows this).

---

## 5. Phase 3 — Free Skool community (open Week 1, structured by Week 6)

### Structure (seeded almost entirely from existing repo assets)

- **Classroom (courses tab):**
  - *The AI Stack 101* — the investing brief (`references/investing-brief.md`)
    rewritten as 5 short modules: energy → chips → infra → models → apps.
  - *Read a Stock Like an Analyst* — the dossier/fact-sheet methodology
    (`RUNBOOK.md` + `skills/analyst/SKILL.md`) as a walkthrough course.
  - *Follow the Money* — capital-web explainer.
- **Rituals (what makes a Skool feel alive):**
  - Weekly **"Stack Heat Check"** — top screener movers, posted from your pipeline.
  - **Congress trade of the week** thread.
  - Member stock-request thread → next week's carousel (content flywheel: the
    community now feeds the content engine).
- **Gamification:** unlock course modules at Skool levels — drives the daily
  activity Skool's algorithm and discovery page reward.

### Rules of thumb

- Post in the community daily even when it's 12 people. Ghost towns never convert.
- DM every new member a one-line welcome + "what stock are you watching?" —
  activation, and market research for content.

**Exit criteria for monetizing:** ~200–500 free members, real daily conversation,
people asking "do you have more of this?"

---

## 6. Phase 4 — Monetize (Months 2–4)

### Recommended model: free community + paid tier inside it

Free stays the top of funnel forever. Paid tier: **$29–49/mo** (start $29, raise
with proof). The paid deliverables are things your pipeline *already produces*:

| Paid perk | Source | Your marginal effort |
|---|---|---|
| **Daily AI-stack brief** (the flagship) | `content/daily_brief/` generator | ~0 — already one command |
| Full dossiers on request (2–3/week) | `pull_dossier.py` + dashboard | minutes |
| Live screener + capital-web access (gated app features) | `web/` | one-time build |
| Monthly live "analyze it with me" session | you + the terminal | 1–2 h/month |
| *Build-your-own-terminal* course (the engine methodology) | this repo's docs | one-time packaging |

That last one is a sleeper: there are two audiences here — **investors** (want the
data) and **builders** (want the pipeline: Playwright scraping, carousel automation,
AI content factory). The builder angle can be its own course or higher tier later;
don't split focus before Phase 5.

### Realistic math (so expectations stay sane)

- Short-form → free community: expect roughly 1–3% of *engaged* followers.
- Free → paid: 2–5% is typical for a healthy Skool.
- So: ~20k followers → ~500 free members → 15–25 paid → **$450–1,200/mo** at $39.
  Doubling follower count roughly doubles this. Compounding, not lottery.
- Churn is the real boss fight: the daily brief is your retention weapon —
  a *daily* reason to stay subscribed, and it costs you nothing to produce.

### Pricing discipline

- Never discount; add perks instead.
- Founding-member launch: first 20 paid at a locked lower price, 72-hour window,
  announced to the free community only. Creates the initial testimonial base.

---

## 7. Phase 5 — Scale (Months 4+)

1. **YouTube long-form** — weekly 8–12 min "state of the AI stack" built from the
   daily briefs. YT is the only platform with durable search traffic; it de-risks
   IG dependence.
2. **Newsletter (Beehiiv/Substack) as second capture** — the daily/weekly brief in
   email form; free tier feeds Skool, and it's an owned list no algorithm controls.
3. **Higher tier ($99–199/mo, small cap)** — small-group monthly deep-dive +
   dossier priority. Only after the base tier retains well.
4. **Builder product** — package the content-factory methodology (this repo's
   pattern: data → carousels → reels → briefs) for the AI-automation audience.
   Possibly a second Skool; decide only when tier 1 runs itself.

---

## 8. 90-day checklist

| Weeks | Do | Done when |
|---|---|---|
| 1 | Positioning, handles, free Skool opened, `/join` CTA on app, UTM links | Funnel plumbing live |
| 1–2 | Seed Skool: 5 posts + AI Stack 101 module 1; first 5 carousels queued | Content buffer exists |
| 2–6 | Post daily (carousel/reel/brief-story mix), cross-post to TikTok/Shorts, weekly review-dashboard pass | 6-week unbroken streak |
| 4–6 | Rituals running (Heat Check, congress thread); DM-welcome habit | Daily community activity without you forcing it |
| 6–8 | Gate screener/dossiers behind free membership; double down on winning pillar | Content → member conversion measured |
| 8–12 | Founding-member paid launch ($29, first 20, 72h) with daily brief as flagship | First paid revenue; testimonials collected |
| 12+ | Raise to $39–49 for new members; start YouTube long-form | Retention >90% month over month |

---

## 9. Risks & honest caveats

- **The bottleneck is publishing, not producing.** The factory removes the usual
  creator failure mode (burnout), but *someone* still has to post, reply to
  comments, and DM welcomes daily. Automate generation; never automate the human
  replies — that's what people pay a community for.
- **Platform risk:** finance content gets throttled/reported. Rails on every asset
  (NFA, no performance promises, no "buy this"), and build the email list early.
- **Don't launder rumors** (repo rule #5) — one credibility hit costs more than a
  month of posts. The "live, stamped data" brand only works if it's never wrong
  about what's fact vs. reported.
- **Skool payouts** run via Stripe — verify availability/tax handling for your
  country of residence before the paid launch, not after.
- **Higgsfield credit budget** (~60–80/week at full cadence) is a real cost line —
  track it against revenue from day one.
- Engagement/conversion percentages above are niche norms, not guarantees.

---

## 10. Earnings model — first 90 days (researched 2026-07-14)

### What real trading Skools look like (live comparables)

The distribution is brutally skewed. SEO-blog benchmarks profile the winners
("typical" $5K MRR = 120–260 members at $19–39/mo, 68–74% 90-day retention);
actual trading communities visible on Skool right now are mostly tiny:
Options Day Trading = 22 members at $298/yr (~$550 MRR); WM Investing = $40/mo
(discounted to $20); Rule-Based Trading = $9/mo founding pricing. Pricing bands
across paid Skools: ~41% at $9–19, ~36% at $29–49, ~17% at $79–199, ~6% at $200+.
Trading tolerates the higher bands; the *median* trading Skool earns closer to
$0–500/mo than $5k. (Sources: communipass.com benchmarks 2026, skoolco.com
pricing guide, skool.com community about-pages — blogs treated as indicative
bands, not ground truth.)

### 3-month scenarios (from zero, daily multi-platform posting, founding launch ~week 10 at $29→$39)

Funnel assumptions: 1–3% followers→free members; 3–8% free→paid at founding launch.

| Scenario (subjective probability) | Followers d90 | Free | Paid m3 | Month-3 MRR | 3-mo gross |
|---|---|---|---|---|---|
| Conservative — consistent, no breakout (~50%) | 3–8k | 100–250 | 5–12 | $150–400 | $200–600 |
| Base — strong execution + 1 semi-viral reel (~35%) | 15–35k | 400–900 | 20–50 | $700–1,800 | $1–2.5k |
| Aggressive — 1–2 viral reels, top ~10% (~10–15%) | 75–150k+ | 1.5–3k | 75–180 | $3–7k | $4–9k |

Costs against that: Skool Pro $99/mo (+2.9% fees), all-out Higgsfield at 3–5
posts/day ≈ $200–400/mo. **Median case is break-even-ish over the first 90 days;
the payoff window is months 4–9**, when a retained funnel typically 3–5x's.

### What "all-out AI budget" actually buys

Budget moves the **ceiling and the floor, not the funnel percentages** — trust
converts, and trust takes time. Spend it on:
1. **Volume** (3–5 posts/day × 3 platforms ≈ 4× the viral lottery tickets) —
   highest-leverage line item.
2. **Speed** (congress filing / earnings print → reel within hours; first-mover
   with a data-backed take beats polish).
3. **Not** on ever-prettier heroes — past good-enough, polish has ~zero marginal
   return on short-form; volume and hooks have all of it.

Plan around **$500–2,000 total gross in the first 90 days** ($400–1,800 month-3
MRR with full execution); treat >$3k MRR as the happy tail. The 90-day goal is a
converting funnel with retention data, not income.

---

## 11. Two-community architecture (owner direction, 2026-07-14)

Target end-state: **two separate Skools, two brands, one shared content factory.**

| | Community A — "AI Stack" | Community B — "Technicals Desk" |
|---|---|---|
| Niche | Fundamentals + congress trades, AI value chain | Day-trading technical analysis: commodities & FX |
| Audience | Patient investors, research-minded | Active day traders, faster decisions |
| Data engine | This repo (dossiers, screener, capital web, congress) | **TradingView MCP** (charts, indicators, scanner) |
| Content | Value carousels, capital-web maps, congress reels, daily brief | Chart-markup posts, setup-of-the-day, session recaps (London/NY), levels-to-watch |
| Pricing gravity | $29–49/mo | $49–99/mo (day-trading tolerates higher; churns faster) |
| Compliance heat | Moderate | **High** — strictly "levels and structure, not signals"; never "enter here" |

Why split (correct): the audiences barely overlap — mixing them dilutes both
feeds, and Skool's algorithm + about-page conversion reward a sharp single
promise. Why *not* in parallel from day one: two communities double the human
layer (posting, replies, DM welcomes — the part that can't be automated) and
split audience-building across two personas before either has momentum.

### Sequencing

1. **Months 1–3 — Community A only** (this roadmap unchanged). It's the
   differentiated moat; nobody else can generate capital-web/congress content
   on demand. Meanwhile, build the TA pipeline quietly: TradingView MCP →
   chart-snapshot generator → same carousel/reel factory, new template set.
2. **Month 2–3 — demand test before building B:** run 1–2 TA posts/week
   (commodities/FX levels) on a **separate handle** (or as a test pillar) and
   measure saves/follows vs. Community A content. Data decides, not vibes.
3. **Months 4–6 — launch B** only if (a) Community A's funnel is converting and
   its rituals run without daily firefighting, and (b) the TA test showed pull.
   B gets its own persona/handle/palette (dark/terminal aesthetic vs. A's
   emerald), its own free Skool, same founding-launch playbook.
4. **Shared infrastructure, separate brands:** one factory (`higgs/` templates ×2,
   one review dashboard, one daily-brief generator per community), zero
   cross-posting. Cross-*promote* only sparingly (A's about page may mention B).

### Engineering prerequisites for B (build during months 2–3)

- TradingView MCP wired as a data source (charts, indicators, multi-timeframe
  snapshots for XAUUSD, EURUSD, WTI, etc.).
- `_build_v4`-style template for chart posts: chart + marked levels + one-line
  structure read + NFA footer.
- Session-recap generator (analog of the daily brief): pre-London and pre-NY
  "levels to watch" — this becomes B's paid-tier retention hook, same role the
  daily brief plays in A.

---

## 12. Identity & story (decided 2026-07-15)

### The founder story (proof artifact, not audience filter)

The founder is a working engineer with a day job who got tired of paying for — or
being blocked by — paywalled financial data, and built his own terminal instead:
live TradingView/Yahoo/GuruFocus/EDGAR/FRED pulls, a capital-web map, a screener,
congress-trade tracking, daily briefs, all stamped with `retrieved_at`/`source` so
nothing is a stale screenshot. That story is **real, checkable, and stays exactly
as it is** — it's the credibility asset, the thing no lifestyle-flex or fake-P&L
competitor in this niche can fake (`docs/trading-brand-playbook.md` Rule 2 and
Part II's fake-proof case ledger). What changes is what the story is *for*: it
proves the terminal is trustworthy. It is not, and should never be written as, a
description of who the community is for.

### The corrected buyer avatar

Not "engineers" or "AI-stack builders." The buyer is the **mass-market, time-poor,
9-to-5 retail investor/trader** — often a **second-attempt trader**: tried
investing or trading before, alone or via a guru/course, got burned by losses or
hype, and now wants structure and someone/something to trust rather than more raw
information. Three things pull in the same direction:

- **Time-poor by default, not by exception.** Most retail accounts trade only
  about once a month on average — trading is a side activity for most people, not
  a full-time occupation (Stanford GSB research). Roughly 39% of working
  Americans — about 80 million people — report income on the side (BLS-cited).
  Design cadence, session length, and "catch-up" mechanics for evenings and
  weekends, not a trader who watches four screens all day.
- **Second attempts are close to the statistical default, not an edge case.**
  Independent studies out of Brazil, Taiwan, and the EU/UK's own mandated
  CFD-loss disclosures all land in the same range: the large majority of people
  who trade persistently lose money. First-attempt failure is closer to the
  default outcome than the exception — assume it in copy, don't tiptoe around it.
- **Burned traders don't come back on hype — they come back on a credible "this
  time is different."** Investors are meaningfully less likely to repurchase
  something they lost money on than something that made them money
  (Strahilevitz, Odean & Barber, *Journal of Marketing Research*, 2011) — regret
  from a loss creates real reluctance unless something about the situation has
  visibly changed. That "something different" is the terminal, the timestamp,
  the visible Failure File — never a bigger promise.

Full trigger-stack, objection-stack, and sourcing detail lives in
`docs/trading-brand-playbook.md` Part 0 — treat that section as this roadmap's
psychology appendix; don't re-derive it from memory.

### The bridge line

Every piece of founder-story copy should resolve to some version of this line
before the CTA:

> *"You don't need to be an engineer — I already did that part. You just show up,
> the terminal's already prepped the numbers, and you follow the process."*

That's the entire founder-identity-vs-buyer-avatar distinction in one sentence:
his competence is spent so the member's time doesn't have to be. Use it (or a
close paraphrase) on the `/join` page (Phase 2), in the founding-member launch
copy (Phase 4), and in any "build-in-public" pillar content (Phase 1) — it's the
line that converts "impressive, but not for me" into "then this is for me."

### Villain rules: systems, never names

Unchanged from, and now formally shared with, the playbook's Rule 4 and
Anti-Rule 9: the foil is always a structural enemy — gatekept institutional
tooling, the paywalled-Bloomberg-terminal model, hustle-guru culture, "another
course that's just information you can get free" — **never** a named competitor,
creator, or brand, even implicitly, even as a "here's what not to do" example.
This is hygiene, not a growth lever (every brand the playbook studied, including
every enforcement-action case, already avoids naming rivals) — but it's
non-negotiable: it can't be defamation-tested, it can't hand a rival a rebuttal
moment, and the content well never runs dry because new examples of the
*system's* failure keep appearing on their own.

### Per-community sharpening

| | Community A — AI Stack | Community B — Technicals Desk |
|---|---|---|
| Corrected filter | *"the time-poor investor who wants Bloomberg-grade fundamentals without needing to be the engineer who builds the terminal"* | *"the day-job trader who needs session-scoped setups that fit around a 9-to-5, not a full trading-floor screen commitment"* (already correctly aimed — A now matches this model) |
| Founder's role in the copy | Proof only: "I built the pipeline so you don't have to read a 10-K to know where a name sits in the stack." | Proof only: "I built the session-level data feed so you don't have to watch four screens through London and NY open." |
| Buyer's felt need | Clarity without the CNBC noise; a reusable mental model (the stack), not a pile of raw filings. | A process that fits around a day job; structure at session open/close, not a full-time trading-floor commitment. |
| Second-attempt framing | "You've read the headlines and still didn't know if a name was cheap or expensive — that's not a you problem, that's a missing-tool problem." | "You've watched a level break with no plan for it before your shift started — that's the gap this closes." |
| Compliance register | Moderate heat — never let a fundamentals read imply a price target or "buy." | High heat — structure and levels-to-watch only, never "enter here" (playbook Anti-Rule 11). |

### Hook bank — 10 hooks written for the corrected avatar

All ten follow Part 0's trigger stack (hope channeled into process, belonging,
borrowed competence, loss-framed on time not profit, real scarcity only) and stay
inside the playbook's SAFE column (Part 0.5) — no dollar figures, no win rates, no
"guru," nothing a second-attempt trader would pattern-match to what already
burned them.

1. "You don't have time to read a 10-K before work. The terminal already did —
   here's what it found." *(time-poor, borrowed competence)*
2. "Tried trading before and it didn't stick? You're not the exception — you're
   the majority. Here's what's actually different this time." *(second-attempt,
   honesty-as-trust)*
3. "I got tired of paying for data I couldn't verify, so I built a terminal that
   stamps every number with when and where it came from. You don't have to build
   one — just use mine." *(founder-as-proof, bridge line)*
4. "No guru calls, no 'buy this now.' Just the stack, the numbers, and the
   timestamp — you decide." *(trust via transparency, not hype)*
5. "Where does NVDA actually sit in the AI stack — chips, infra, or both? Most
   people guess. Here's the number." *(curiosity hook, process not outcome)*
6. "Session opens in nine minutes and you're still in a meeting. Here's what to
   have open when you get out." *(day-job trader, time-poor)*
7. "The paywalled terminal costs more than your rent. Here's the same read, built
   from scratch, without the four-figure monthly bill." *(system villain, never a
   name)*
8. "You don't need to become an engineer to get engineer-grade data. That part's
   already done — you just show up." *(bridge line, direct)*
9. "Congress just filed a trade in a name you've never heard of. Here's what it
   actually means — not a headline, the filing." *(curiosity + transparency)*
10. "Burned once by a course that promised more than it delivered? Come see what
    happens when the process is the product, not the promise." *(second-attempt,
    ethical hope)*

### See also

The full evidence base for this section — every stat's fact/reported label and
source, the trigger stack, the objection stack, and the SAFE/LINE-RISK conversion
rules the hook bank above is built to stay inside — lives in
`docs/trading-brand-playbook.md` Part 0 (Buyer psychology), and Part 0.5
specifically for anything copy-adjacent. Read that before writing new
founder-story or hook copy; don't re-derive it from memory.

---

*Roadmap for the project owner's content/community strategy. Educational project;
nothing here or in the content it produces is financial advice.*
