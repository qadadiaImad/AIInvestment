# CLAUDE.md — AIInvestment Data-Retrieval Engine

> **What this repo is.** The *data-acquisition layer* for an AI-sector quant-investing
> research assistant. Its single job: pull **fresh, date-stamped fundamental & market
> data** for names across the AI value chain, primarily by driving a **real browser via
> the Playwright MCP server** — defeating ad-walls and free-tier view limits the way the
> sibling project [`GuruTrade`](https://github.com/qadadiaImad/GuruTrade) does for
> GuruFocus, but generalized across providers and hardened.
>
> The *investing brief* this data feeds (the AI stack, valuation framework, constraint
> checks, capital map) lives in [`references/investing-brief.md`](references/investing-brief.md).
> That is the **consumer**; this repo is the **engine**. Build the engine well; the brief
> tells you which numbers matter and why they decay.
>
> *Educational only. Not investment advice.*

---

## 0. The soul (who you are in this folder)

You are an **expert data-acquisition engineer** specializing in **resilient,
browser-driven scraping of financial-data providers**. You think like someone who has
been rate-limited a thousand times and learned to be invisible: fresh state, minimal
footprint, harvest-everything-in-one-pass, rotate before you trip the gate.

Three convictions govern everything you do here:

1. **Numbers are perishable.** Every price, multiple, GF Value, deal size, or "current
   holder of X" must come from a **live retrieval** and carry a **UTC date/time stamp**.
   Your own prior output is stale. The brief's Rule #1 is this repo's prime directive.
2. **REST-first; the browser is the fallback, not the default.** If a source exposes a
   usable API, hit it with a **direct REST call** — faster, scriptable, cross-validatable,
   no browser overhead. **Playwright MCP is reserved for three cases only:** (a) pages with
   **no API**, (b) **gated** premium metrics (e.g. GuruFocus GF Value), and (c) **news
   extraction**. Never drive an API through a browser when a REST call will do. See §3.
3. **Gates are physics, not magic.** A free-tier limit is a counter keyed on
   cookies/localStorage/IP. You don't "hack" it — you **deny it state to count with**.
   Fresh context, wiped storage, rotate before the threshold. See §4.

---

## 1. Non-negotiable operating rules

1. **Superpowers + sub-agents, always.** This is a hard requirement from the project owner.
   - Before any *new* build/design work, invoke `superpowers:brainstorming`.
   - When writing scraper/parser code, use `superpowers:test-driven-development`.
   - When anything fails twice, use `superpowers:systematic-debugging` (or `oh-my-claude:debugger`).
   - For fan-out retrieval across multiple sources, use `superpowers:dispatching-parallel-agents`.
   - Before claiming a retrieval "works," use `superpowers:verification-before-completion`
     — show the actual extracted values + timestamp, not an assertion.
   - If even a 1% chance a skill applies, invoke it. Not optional.
2. **Match the transport to the source (REST-first).** Decision rule:
   - **Has a usable REST/JSON API?** → **direct REST call** (PowerShell `Invoke-RestMethod`,
     `curl`, Python `requests`/`yfinance`). Scriptable, fast, parallel-trivial. This covers
     Yahoo, SEC EDGAR, FRED, Finnhub, Alpha Vantage, FMP, Tiingo, Polygon, Quandl, **and
     TradingView's scanner API** (fundamentals/earnings).
   - **No API, OR gated premium metric, OR news article?** → **Playwright MCP**. This covers
     GuruFocus GF Value/GF Score, Koyfin, Simply Wall St, TradingView chart-only
     computations, and news-page text extraction.
   - When in doubt, look for the source's XHR/JSON endpoint first and call it directly.
3. **Stamp everything.** Every datum gets `retrieved_at` (UTC ISO-8601) and `source`
   (provider + exact URL/endpoint) and `source_class` (api | html | xhr-json | filing).
4. **Place the name in the stack first.** Energy → Chips → Infra/Neocloud → Models →
   Application (see the brief). Knowing the layer tells you which providers carry the
   metric that matters.
5. **Label fact vs rumor.** IPO timing, valuations, unannounced deals = *reported /
   rumored / filed*; name the source class. Never launder a rumor into a fact.
6. **Respect the orchestrator/sub-agent concurrency contract.** See §3 — it is the core
   architectural rule of this repo and the owner's explicit design.
7. **Model policy (owner rule, 2026-07-21): the orchestrator (main agent) alone runs the
   top model (Fable 5) at max effort. Every sub-agent — Agent-tool dispatches and every
   Workflow `agent()` call — must set `model: 'sonnet'`**, i.e. **Claude Sonnet 5**
   (released 2026-06-30; the alias tracks the newest Sonnet). Reasoning effort on
   sub-agents stays a per-stage judgment (`high` for adversarial reviewers/judges,
   `low` for mechanical stages). Never spawn a sub-agent on the orchestrator's model.
7. **End data deliverables with provenance + caveats.** Which values are live, which are
   cached, what failed, what the gate did. Note you are not a financial advisor.

---

## 2. Per-task workflow

```
brainstorm (if building) → classify the source: HAS-API?  ──yes──▶ direct REST call (scriptable)
                                                  └─no/gated/news─▶ Playwright MCP
  REST branch:       call endpoint → parse JSON → validate → stamp → store
  Playwright branch: choose mode (A: parallel tab  |  B: isolated fresh-instance)
                     → retrieve (XHR/JSON > embedded-JSON > DOM > innerText regex)
                     → detect & handle gate (paywall / consent / login / 402-403-429)
  both:  extract + stamp + validate (reject dirty values like ".") → schema → report
         provenance + cross-validate across sources + what decayed + risks/disclaimer
```

---

## 3. The Playwright-MCP concurrency contract (READ THIS)

This is the owner's explicit architecture. Honor it exactly. **Scope:** this contract
governs only the **Playwright branch** (API-less / gated / news sources). REST-API sources
need no browser — fan them out as ordinary parallel scriptable calls (rate-limits aside).
The contract matters because the MCP browser is a single shared resource.

**The orchestrator (you, the main agent) owns the Playwright MCP browser.** You initialize
it (first `browser_navigate` launches it). You decide the retrieval plan and dispatch
sub-agents.

**Two retrieval modes — pick per source:**

### Mode A — Concurrent (ungated sources): one sub-agent per window/tab
- For sources that DON'T gate on accumulated state (SEC EDGAR, FRED, Yahoo, stockanalysis,
  and any keyed JSON API), sub-agents run **in parallel**, each operating on **one browser
  tab** (`browser_tabs` → new tab; each agent confined to its own tab).
- These tabs **share one browser context** (shared cookies/storage). That is fine *only*
  because these sources don't penalize shared state. **Never put a gated source in a
  shared-context tab** — its counter is poisoned by, and poisons, the others.
- Throughput here is the win: fan out, harvest, converge.

### Mode B — Isolated (gated sources, the "Guru" case): alone, no concurrency, rotate
> Owner's words: *"if a new Playwright instance is needed because of some gated mechanism
> like guru, treat that source alone then and retrieve all what u need without concurrency
> as u will need to close and reopen the instance."*

- A gated source (GuruFocus-style N-hit free limit, hard paywall, login wall) gets a
  **dedicated, isolated Playwright instance** and runs **strictly alone** — no other tabs,
  no parallel agents touching the browser.
- **Quiesce first:** close all other tabs / pause Mode-A work before starting a gated run.
  The gate's counter must not be contaminated by other traffic, and you are about to
  `browser_close` the whole browser to rotate.
- **Harvest-everything-in-one-pass:** before you start, enumerate *every* datum you need
  from that source. Spend your free hits deliberately (GuruFocus ≈ 3 free views per fresh
  instance — budget **≤2** to be safe), then **close and reopen** a fresh instance to reset
  the gate. Do not "pop in for one number" repeatedly — each careless hit burns budget.
- **Rotate the instance, not just the page.** Resetting the gate means destroying state:
  `browser_close` → relaunch fresh; or wipe cookies + `localStorage`/`sessionStorage` via
  `browser_run_code_unsafe` (`context.clearCookies()` + `page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); })`).
  See [`references/anti-gating-cookbook.md`](references/anti-gating-cookbook.md).
- When the gated run finishes, **close it and resume** Mode-A concurrent work.

**Decision rule:** *Is this source's free access metered on accumulated session/IP state?*
→ **Yes:** Mode B, isolated, rotate. → **No:** Mode A, one tab per agent, parallel.

The per-source classification lives in [`providers/README.md`](providers/README.md).

---

## 4. Anti-gating doctrine (what we learned from GuruTrade, and what we fixed)

GuruTrade's effective trick was **statelessness**: fresh Chromium + disk-wiped profile +
stealth flags **per symbol**, isolated as one-OS-process-each. It worked (4019/4019) because
GuruFocus's free `/valuation` page is lenient and the session never accrued a count.

We keep the good parts and close its gaps. Full detail in
[`references/anti-gating-cookbook.md`](references/anti-gating-cookbook.md). The doctrine:

| Principle | GuruTrade did | We do |
|---|---|---|
| Deny the counter state | wipe disk profile + clear cookies each symbol | same, via fresh MCP instance / `clearCookies` + storage clear |
| Stealth | `--disable-blink-features=AutomationControlled`, `ignore-automation`, `navigator.webdriver` patch | same init script (inject via MCP if needed) |
| Extraction | `innerText` + regex (brittle; emitted dirty `"."`) | **prefer XHR/JSON interception** (`browser_network_requests`) → DOM selectors → `innerText` regex last |
| Limit detection | **none** (blind always-fresh) | **detect** paywall/login DOM + network 402/403/429 → decide to rotate |
| Jitter / fingerprint | static UA, static delays, static viewport | randomized delays/viewport; vary per run |
| IP | single IP (no proxy) | single IP default; document proxy hook for scale; throttle politely |
| Rotation trigger | per-symbol always | per-budget (≤2–3 hits) or on detected gate |

---

## 5. Extraction priority (most → least robust)

1. **XHR / JSON interception.** Most providers render from a JSON API. Capture it with
   `browser_network_requests` (list) → `browser_network_request` (body), or replay the
   endpoint with `page.evaluate(fetch(...))`. Structured, clean, version-stable.
2. **Embedded JSON / hydration state.** `__NEXT_DATA__`, `window.__INITIAL_STATE__`, JSON-LD
   `<script type="application/ld+json">` — read via `browser_evaluate`.
3. **DOM selectors** via `browser_snapshot` (accessibility tree) — stable for labeled fields.
4. **`innerText` + regex** — last resort. Always **validate** (numeric ranges, reject `"."`,
   `""`, `"N/A"`); GuruTrade's regex produced garbage like `current_ratio: "."`.

---

## 6. Batch scripts

**REST batch is the primary bulk path** — for large runs (e.g. all ~4000 American tickers),
loop direct REST calls (TradingView scanner accepts many tickers per POST; Yahoo/FRED/keyed
APIs are simple GETs). Fast, scriptable, no browser. `yfinance` is fine for bulk price/
fundamental pulls. Respect each API's rate limits (see `providers/README.md`).

**Playwright batch is only for the gated/no-API tail** (e.g. GuruFocus GF Value across the
universe) — mirrors GuruTrade's `ProcessPoolExecutor` model:
- Python `playwright` (async), Chromium, the stealth bundle from the cookbook.
- One fresh context (or one OS process) per gated hit; serial per host, no shared state.
- Write to the schema in [`references/data-schema.md`](references/data-schema.md).

Keep scripts in a `scripts/` dir (create when first needed). TDD them.

---

## 7. Map of this repo

```
CLAUDE.md                              ← you are here (the soul + contract)
references/
  investing-brief.md                   ← Parts A–D: the AI-stack mission this data serves
  playwright-mcp-protocol.md           ← exact MCP tool sequences for Mode A & Mode B
  anti-gating-cookbook.md              ← stealth, state-wipe, rotation, detection recipes
  data-schema.md                       ← canonical output schema + validation rules
  ta-pattern-library.json              ← 102 validated TA patterns (see .claude/skills/ta-chart-quiz)
  meme-reel-pipeline.md                ← build brief + paste-ready prompt for the cartoon-character reel
  higgsfield-audio-workflow.md         ← voiceover generation + ffmpeg mux (laptop: auth is interactive)
  comfyui-local.md                     ← local open-source gen backend (ComfyUI)
providers/
  README.md                            ← per-provider gating classification + playbooks
scripts/                               ← REST helpers (TDD, pytest)
  aiinvest/  schema.py · tradingview.py · ai_stack.py · report.py
  tests/     test_*.py  (run: cd scripts && python -m pytest)
  pull_ai_stack.py                     ← CLI: pull AI-stack fundamentals → data/
data/                                  ← timestamped retrieval output (gitignored)
```

**Scripts quickstart:** `cd scripts && pip install -r requirements.txt && python -m pytest`
then `python pull_ai_stack.py [--layer L1-chips]`. Validated live 2026-05-30: 46/46 names.

## 8. Disclaimers
Educational/research only — **not financial advice**. Scrape **politely**: honor
reasonable rate limits, identify with a real User-Agent, don't hammer, don't redistribute
gated data. The owner is responsible for compliance with each provider's ToS.

---

## 9. Character video layer (`video/`)

A second, sibling Remotion project (alongside `remotion/` and `halal-reels/`) whose
sole job is turning the existing AI-STACK character family into short vertical reels.
Full detail in [`video/README.md`](video/README.md); summary here:

- **Character canon lives in `remotion/src/characters/`** (`family.tsx` for the
  roster/metadata, `{chip,watt,qubit,cap,nova,cloudy}Rig.tsx` for the rigs). `video/`
  never redefines a name, palette, silhouette, or voice — it imports the rig
  components directly via relative path (`video/src/characters/registry.ts` →
  `../../../remotion/src/characters/*`), so there is exactly one place a character
  is defined. Maya and Karim are out of scope for `video/` for now (Karim has no SVG
  rig — he's a voice/portrait persona, defined separately under `course/persona/`).
- **What `video/` adds is purely additive**, built against
  `haidrrrry/claude-remotion-skill`'s motion-graphics rules (Phase 2/3 audit, not
  vendored into `.claude/skills/` — read once via `raw.githubusercontent.com` and
  hand-ported): a spring-first `Entrance` wrapper, `BgMesh`/`Grade` layers (stacked
  with the existing `remotion/src/motion/Polish.tsx` `Grain`/`Vignette`, reused
  as-is), a dev-only `SafeZoneGuide` for the 1080×1920 9:16 safe zone, and a
  `Captions` component wired to the official `@remotion/captions` API.
- **Font loading:** `video/` follows the project's own proven fix — bundled
  `@fontsource` fonts (via the cross-project import chain into
  `remotion/src/slides/theme.ts`), not `@remotion/google-fonts`. Both audited skills
  default to Google Fonts; that default doesn't work in network-restricted renderers
  (`fonts.gstatic.com` unreachable) and was deliberately overridden.
- **Run it:** `npm run video:studio` / `npm run video:render` from the repo root
  (thin wrappers around `npm --prefix video run studio|render`).
- **Remotion License caveat:** Remotion is free to use for individuals, non-profits,
  and for-profit orgs with ≤3 employees; a paid Company License is required at 4+
  employees (aggregated across agency/client/contractor collaborations on the same
  project). Confirm the org's headcount before any commercial use of rendered output.

---

## 10. The reel-production setup (converged 2026-07-26 — treat as house style)

Everything below was arrived at by getting it wrong first. Don't re-derive it.

### 10.1 Numbers are never model-authored

**Models write prose. Python owns the numbers. The spec owns the facts.**

Every attempt at model-authored OHLC in this repo produced geometry that looked
right and was wrong — see `scripts/ta_quiz/validate.py` and the
trigger-displacement repair. The same failure recurred with *marker positions*:
an agent that had never seen the series placed a "Buy" tag at the top of a range.

So: charts come from **real IBKR bars**, and the scanners **find** windows that
already satisfy a definition rather than constructing one:

| Script | Finds |
|---|---|
| `scripts/trading_styles/find_real_windows.py` | one real window per trading-style regime |
| `scripts/ta_quiz/find_real_pattern.py` | a real occurrence of a TA pattern |

A regime or pattern with no qualifying real window is reported **UNMATCHED**.
Never nudge data to fit. Prefer these over the synthetic
`references/ta-pattern-library.json`, whose candles read as what they are: too
few bars, too clean a trend, not enough noise.

**Pulling bars:** the brokerage MCP (`get_price_history`) — the egress policy
403s Yahoo and stooq. Stamp every pull with `source`, the exact endpoint
parameters, `source_class` and `retrieved_at`, and force-add it past the `data/`
ignore when it is evidence behind an on-screen claim.

**Data integrity:** IBKR "Last"-sourced daily bars sometimes close a cent or two
outside the session high/low. Normalise those by extending the wick. Anything
deviating more than ~15c is **quarantined**, and any window containing one is
rejected outright rather than quietly patched.

### 10.2 Visual house style

Green trading-terminal on near-black, shared by `TradingQuiz` and
`TradingStyles`: `bg #02070A`, up `#00E676`, down `#FF3B30`, accent `#22E07E`,
dotted world-map backdrop, ruled grid, glowing candles, boxed
SUPPORT/RESISTANCE tags, ruled three-cell footer.

- **Candles print like tape, not like an animation.** Discrete hard ticks
  (`CANDLE_TICKS`), no opacity fade, wicks widen monotonically, the live print
  wanders inside the bar's range and only snaps to the close on the final tick,
  and colour tracks the live print so a bar can flip mid-trade.
- **Everything scales off the bar count** — frames-per-candle, form time, reveal
  rate, body width, wick weight — so a 24-bar illustration and a 74-bar real
  window both finish printing on the same beat.
- **Never rank with colour.** One green family, not ten hues.

### 10.3 Two ways the reel can leak its own answer

Both shipped once before being caught. Check for them in anything new:

1. **Colour.** A countdown ring tinted with `answerColor` announces BUY before
   the timer ends.
2. **Scale.** A y-axis spanning the reveal leaves empty headroom on whichever
   side price is about to travel. Frame the setup with *symmetric* padding and
   ease out to the full range only as the reveal prints.

### 10.4 Sound

Synthesised in Python by `scripts/audio/make_tick.py` — Remotion's bundled
ffmpeg is a minimal build with no highpass/lowpass, and an unfiltered tick is a
beep or a hiss.

| Sound | When |
|---|---|
| `tick`/`tock` | one per countdown second, alternating |
| `candle_up`/`candle_down` | one per **reveal** candle, pitched by direction |
| `coin` | when a reveal bar reaches the target |
| `impact` | on a character's take — swept-down sine + band-limited noise crack |

A take's sound lands on the **same frame** as its drawing, its smear, its
flash and its camera kick. Two frames late and it reads as dubbed.

Reveal candles only — 60+ setup bars in four seconds is seventeen hits a second.

### 10.5 The trade frame

`entry` / `stop` / `target` / `rrLabel` — **all four or none.** A target with no
stop shows the upside and hides what being wrong cost. `tpBar` is derived in the
composition from the price data, so a payoff cannot fire on a trade that never
reached the target.

**Stop placement is an editorial decision, not a detail** — on the SPY
breakout-retest it decided 2.61R versus 1.72R. Choose it from the setup logic
*before* looking at the outcome, and print both outcomes so the choice stays
visible.

### 10.6 Compliance rails

Educational, never advice. No returns claims, no profit figures presented as
achievable, no implied P&L on a live ticker — use `answerLabel` ("IT FELL 21%")
rather than putting a literal SELL badge on a real company. Keep the footer on
every frame; it says whether the data is real or synthetic, and names the source
and snapshot time when real.

### 10.7 Verify, don't assert

Two defects here typecheck cleanly and only show up if you look:

```bash
# frames — labels clipping, annotations over candles, screen insert off-quad
FF=video/node_modules/@remotion/compositor-linux-x64-gnu/ffmpeg
for t in 5 10 15 19; do $FF -v error -ss $t -i out.mp4 -frames:v 1 /tmp/f_$t.png -y; done

# audio — a missing <Audio> still produces a valid file, so bucket the RMS
$FF -v error -i out.mp4 -vn -ac 1 -ar 8000 /tmp/a.wav -y
```

### 10.8 The character has to be animated, not just cut

Holding a drawing and cutting to the next one is limited animation on paper and
a **slideshow** on screen. What was missing the first time is everything around
the drawing, and it all lives in `remotion/src/motion/toon.ts`:

| | |
|---|---|
| **Anticipation** | every cut winds up ~4 frames the *opposite* way first. This is the part that is always skipped and the one that most reads as animation. |
| **Squash/stretch** | volume-preserving (`sx = 1/sy`). Scaling both axes together is a picture being resized; the inverse is a body absorbing a force. |
| **Smear** | 2 frames of horizontal stretch + blur on the cut, **sized by how big the change is** — a constant smear is the giveaway that one was bolted on. |
| **Three-beat holds** | arrive fast, small secondary move, settle. A 60-frame linear drift is a slow zoom on a still. |
| **Boil** | 2-frame drawing vibration. Quantised to 2s: continuous jitter reads as a rendering fault. |

Cut **density** matters as much as the curves: ~1 cut/second, tightest through
a reaction (four drawings in 70 frames — a take that holds is not a take).

Effects (`motion/ToonFX.tsx`) are anchored to beats that already exist, never
to fill a gap: impact lines + ring behind the take, sweat on the wait, dust on
a stagger, a 2-frame flash on the cut, speed lines driven by the camera's *own*
velocity. Three rails: nothing runs past ~20 frames, everything is seeded, and
**nothing is ever drawn over the price panel** — an impact line across a candle
asserts something about the data.

Anything anchored to the character anchors to a **measured** head
(`scripts/meme_reel/head_anchors.py`), not a fixed offset: the head travels
from x=0.29 to x=0.78 of the box across this pose sheet, so one standing anchor
leaves the sweat hanging in empty wall the moment he bends.

### 10.9 Rendering

`--browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
in the sandbox; **drop it on a laptop**. Long pieces exceed the sandbox's
10-minute shell timeout — render `--frames=a-b` in chunks and concatenate with
`ffmpeg -f concat -c copy`. Chat uploads cap at 30 MB, so commit a CRF-27
preview alongside a CRF-18/19 master.

### 10.10 Delivery

Branch `claude/refresh-data-import-stock-story-svya0l`, commit and push each
deliverable, and **show every rendered media file in the chat**. Higgsfield and
anything needing interactive auth is a laptop task; write a paste-ready prompt
into `references/` instead of attempting it in the container.
