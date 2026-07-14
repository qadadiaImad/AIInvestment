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

*Roadmap for the project owner's content/community strategy. Educational project;
nothing here or in the content it produces is financial advice.*
