# Phase 2 Briefing — Halal-Indicator Social Posts with the Karim Persona (2026-07-21)

> Synthesis of a 4-reader recon (reel engine · Studio app · strategy docs · halal data surface)
> preparing phase 2: social posts from halal indicators, fronted by the Karim persona, funneling
> to a future Skool formation. Recon agents ran on Sonnet. This is know-how + decisions — no
> build has started (brainstorming/design gate applies before implementation).

## 1. The machine as it exists

**Carousel/reel pipeline (`higgs/`)** — 2-phase:
- *Phase 1 (serial, Higgsfield):* hero image (recraft 4:5) → animated hero (kling 9:16 5s) →
  logo (financialmodelingprep) → ElevenLabs voice "Harrison" (preset `573e5163…`) → URLs into
  `higgs/reels_manifest.json`. *Phase 2 (parallel):* `make_reel.py <TK> <hero> <voice>` — ffmpeg
  ken-burns (hook/data/takeaway), `-loop 1` + `-frames:v N` mandatory, >40MB hard-fails.
  ~18 credits/reel.
- **Carousels are fully kit-driven** (`_build_v4.py` reads `higgs/reels_<date>_kit.md` via
  `scripts/aiinvest/kit_md.py`) → `v4_<tk>_{1_hook,2_data,3_takeaway}.png` 1080×1350, ≈0 credits.
  **Reels are NOT kit-driven** — `_build_reel_stock.py` has a hard-coded CFG dict (MU/IONQ/NVDA/
  ADBE only); congress reel is hard-coded with no scripted assembler (known gaps).
- Design system: `#0A0D12` base, `#34D399` emerald accent, gold `#E0A23B`, Fraunces/Inter/JetBrains
  (Google-Fonts network dependency at Playwright render).

**Studio (Electron)** — read-only cockpit. Gallery/Kit index `higgs/` + `content/` purely by
filename conventions → **new posts named `reel_<tk>_<date>.mp4` / `v4_<tk>_*.png` appear with
zero Studio changes**. Kit comments (`feedback/post_comments.json`, parts: script/hook/data/
takeaway/hero/general) → "Regenerate with comments" composes a sanitized `claude "…"` command and
types it into the embedded terminal (owner presses Enter). Posting is manual by design: copy
caption + reveal file. `datajoin.ts` merges site/quantum/congress — **halal.json not yet merged**
(one small add mirrors the quantum pattern).

**Halal data (`web/public/data/halal.json`)** — 128 verdicts (82 halal / 8 questionable /
38 not_halal / 0 insufficient), generated 2026-07-21T13:07Z. Per ticker: overall (AAOIFI basis),
3 standards (AAOIFI/FTSE/MSCI) with per-test numerator/denominator/ratio/threshold/**margin** +
clause citations, business-activity evidence (quote + source + date), purification $/share,
`inputs_asof` stamps. Regeneration = `pull_halal.py` + `export_halal.py` (manual; **not in
refresh_all.py yet**). Mandatory framing baked into the bundle: *computed methodology results,
NOT fatwas* — "passes the AAOIFI screen," never "is halal."

**Ready-made post hooks in today's data:**
- NRG: debt/market-cap **84.8%** vs 30% AAOIFI cap (2.8× over)
- ETN: **passes AAOIFI, fails FTSE & MSCI** — same company, opposite verdicts
- WULF: **38.2%** of revenue from bitcoin mining; purification would strip **$0.1296/share**; trajectory improving
- JPM: **52.3%** of revenue is interest income; GS conservative floor 23.3%
- GEV: debt/market-cap **0.99%** — cleanest sweep in the universe
- APP: gambling exposure **undisclosed → honestly unknowable** (the "we don't pretend" post)

**Strategy docs (merged today):** `docs/skool-monetization-roadmap.md` = full phase 0-5 funnel
plan (IG traffic engine ~60-80 credits/wk, free Skool with rituals, paid tier $29→49 founding-20
72h launch, earnings scenarios $150-1,800 MRR at 90 days). `docs/trading-brand-playbook.md` =
15 rules / 11 anti-rules (each tied to an FTC case) + SAFE-vs-LINE-RISK copy filter + buyer
psychology Part 0. Both were written for the *general* AI-stack lane — no halal layer exists yet.

## 2. Decisions to resolve before building (owner input needed)

1. **Persona: Karim replaces Maya for the halal lane.** The pipeline's existing persona
   (@StackedWithMaya, avatar `0932dd65…`) is an *unlabeled* synthetic — the playbook's own audit
   flags that as a "cosplay-identity" risk. Karim (avatar `65141281…`, `course/persona/`,
   RULES.md, disclosed-AI policy) is the compliant answer for halal content. (Recon note: one
   reader claimed `course/persona/` doesn't exist — false; it's untracked in git, which is also
   an argument to commit it.)
2. **Rails conflict — "attention-first, zero CTA" (agent/skill files) vs roadmap Phase 1
   "every post CTAs to the free community."** For the NEW halal handle the funnel is the point →
   adopt the roadmap posture (CTA live from day one), and write an explicit exit-trigger note
   into the agent/skill files for the general lane.
3. **First-person rule:** stock-carousel forbids "I/my"; a persona-fronted brand can't. Proposed
   resolution: Karim speaks first-person as a *disclosed AI presenter*, but data attribution
   stays impersonal ("the screen shows," "AAOIFI math says") — never "my ruling."
4. **New handle** (@thehalalstack candidate) — separate from any general-lane handle.
5. **Voice for Karim reels:** pilot used Marketing-Studio generated voice; ElevenLabs preset à la
   "Harrison" is the alternative. Must be locked once (RULES.md rule).

## 3. Least-change build plan (pending design approval)

1. `_build_v4.py`: load `halal.json` (tolerate-missing) → verdict badge in `header()` (reuses
   pill CSS) + a new **"screen card" slide type** rendering the worked per-standard math
   (HalalCard.tsx is the visual precedent). No kit-format change for the badge.
2. New content formats: **"Does X pass the halal screen?"** per-ticker carousel (the programmatic-
   SEO query, in carousel form) · **"The Weekly Halal Screen"** ritual post (movers/margins) ·
   **"Standards disagree"** series (ETN/BWXT) · **purification-math explainers** (WULF).
3. Karim reels: swap Phase-1 hero generation for Marketing-Studio calls with the Karim avatar +
   desk-set start frame (engine is subject-agnostic; only the Phase-1 call + kit hero section change).
4. Studio: add `halal.json` to `datajoin.ts` merge so verdicts show in Detail/Kit panels; posts
   index for free via naming conventions.
5. Wire `pull_halal`/`export_halal` into `refresh_all.py` (fresh screens every refresh).
6. Halal rails layer (new file, referenced by kit/captions): cite-never-rule, standards-disagree
   honesty, "estimated" purification wording, non-fatwa footer line, AI-persona disclosure in bio.

**Constraint:** Higgsfield balance is 20.05 credits — roadmap cadence needs ~60-80/week → top-up
or plan-upgrade decision before content production starts.

*Sources: recon briefs in the wf_8b7c5217 journal; docs cited inline. Not financial or religious advice.*
