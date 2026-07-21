# TERMINAL.md — AI STACK TERMINAL owner's manual

`/terminal/*` is a gated, personal Bloomberg-style workstation layered on top of the same
data `../how_to_update.md` describes pulling. This file is the route-by-route reference:
what feeds each page, where its capture card lives, and how to shoot that card.

Educational/research only — **not financial advice.** NFA on every capture surface.

---

## 1. The gate

`proxy.ts` (Next.js middleware — see the file-header note on the rename from
`middleware.ts`) matches `/terminal/:path*` only; nothing else in the app is gated.

- Set `TERMINAL_KEY` in Vercel's Project Settings → Environment Variables. If it's unset,
  `/terminal/*` is wide open — fine for local dev, never leave it unset in prod.
- A request is admitted if either the `terminal_key` cookie equals `TERMINAL_KEY`, or the
  query string carries `?key=<TERMINAL_KEY>`. A valid `?key=` sets an `httpOnly`,
  `sameSite=lax` cookie scoped to `/terminal`, `max-age` 400 days — so you paste the key once
  per device and every `/terminal/*` link works after that.
- Every response under `/terminal/*` gets `X-Robots-Tag: noindex, nofollow` and
  `Referrer-Policy: strict-origin` — the desks are not meant to be indexed or leak referrers.
- **Phone flow:** open `https://<your-deploy>/terminal?key=<TERMINAL_KEY>` once from your
  phone. The cookie sticks; bookmark `/terminal` after that.
- **Capture-mode header:** for any `/terminal/card/*` route requested with `?capture=1`,
  the proxy sets an `x-capture-mode: 1` request header on the way through (this exists so a
  server component could branch on capture mode from headers if ever needed; today the
  capture cards branch on the `capture` search param directly — see §3).

---

## 2. Routes, data source, capture card

| Route | Feeds from | Loader (`web/lib/*.ts`) | Capture card route |
|---|---|---|---|
| `/terminal` (TA desk landing) | `public/data/ta_desk.json` | `getTaDeskData()`, `getTaGroups()` | — (per-symbol card below) |
| `/terminal/[symbol]` | `public/data/ta_desk.json` | `getTaInstrument()` | `/terminal/card/[symbol]` |
| `/terminal/risk` | `public/data/risk.json` | `getRiskData()`, `getRiskStocksByLayer()` | `/terminal/card/risk` |
| `/terminal/macro` | `public/data/macro.json` | `getMacroData()`, `getMacroGroups()` | `/terminal/card/macro` |
| `/terminal/archetypes` | `public/data/archetypes.json` | `getArchetypeData()`, `getArchetypeRows()` | `/terminal/card/archetype/[symbol]` |
| `/terminal/portfolio` | `web/data/portfolio.json` (**not** `public/data/`) | `getPortfolioData()`, `isPortfolioEmpty()` | `/terminal/card/portfolio` |
| `/terminal/card/chokepoint/[id]` (capture only — no gated reader page; the public board is `/chokepoints`) | `public/data/chokepoints.json` | `getChokepointById()` (`web/lib/data.ts`) | itself |
| `/terminal/card/dcf/[symbol]` (capture only — the reader is the DCF panel on the public `/stocks/[symbol]` page) | `public/data/site.json` + `public/data/macro.json` (discount-rate default) | `buildDefaultDcfInputs()`/`runDcf()` (`web/lib/dcf.ts`) | itself |

`web/data/portfolio.json` deliberately breaks the `public/data/` convention every other desk
bundle uses — it is server-only, never shipped to the client bundle, never committed (see
§5). All other bundles above live under `web/public/data/` and are refreshed by
`scripts/refresh_daily.py` (TA desk is the one exception — its own `refresh_ta.py`; see
`../how_to_update.md` §2/§2b for the full pipeline step table).

**Sub-nav** (`components/terminal/TerminalSubNav.tsx`) lists TA DESK / RISK / MACRO /
ARCHETYPES / PORTFOLIO — it does not include the chokepoint capture card, since chokepoints
have no gated *reader* page (the reader is the public `/chokepoints` board and `/map`
overlay; only the shareable card is gated, matching the "gate the capture surface, not the
research" default for this module).

### Two independent degradation layers

1. **Pipeline side** (`refresh_daily.py`): an optional step (`build_risk.py`,
   `build_archetypes.py`, `build_portfolio.py`, `pull_macro.py`, `build_chokepoints.py`) is
   only added to the plan if the script file exists — a fresh clone missing one just skips
   that step, no error.
2. **Render side** (`web/lib/*.ts`): every loader independently guards with `existsSync()`
   on the *output* JSON, wraps `JSON.parse` in try/catch, and never throws — a missing or
   corrupt bundle caches a `null` singleton and the page renders an honest empty state
   ("TA desk data not generated yet. Run pull_ta.py on the owner's machine." is the pattern
   `/terminal` itself uses) instead of a 500.

These two layers guard different failure modes (script absent vs. output absent/corrupt) and
are both necessary.

---

## 3. Capture cards — what they are and how to shoot them

Every desk (plus chokepoints) has a **1080×1350 (4:5)** branded capture-card slide meant for
social posting, rendered server-side with **zero client JS on the capture path** — no
TradingView iframe, no async widget, nothing without a deterministic "finished painting"
signal.

**Construction discipline** (see `components/terminal/CaptureCard.tsx` and its siblings
`RiskCaptureCard.tsx`, `MacroCaptureCard.tsx`, `ArchetypeCaptureCard.tsx`,
`PortfolioCaptureCard.tsx`, `ChokepointCaptureCard.tsx`):

- The card's root element has `id="capture-canvas"` and `data-capture-ready="true"`, is
  exactly `1080×1350` px, and uses **only real px sizing** (never `rem`/`%`) so it never
  reflows regardless of host viewport or zoom.
- `CardScaleShell.tsx` wraps the card **only** for on-screen human preview at
  `/terminal/card/<domain>` (no `?capture=1`) — it applies a CSS `transform: scale(...)` so
  the 1080-wide card fits a phone screen. This transform is **irrelevant to the actual
  capture**: an element screenshot targets `#capture-canvas` at its native DOM pixel size and
  ignores an ancestor's CSS transform.
- `CaptureChromeStrip.tsx` renders only when `?capture=1` is present — it's a pure-CSS
  `<style>` block (no client JS, no hydration flash) that hides the site header/footer and
  kills all animations/transitions, so the screenshot is chrome-free and static.
- Every capture-card page route sets `export const dynamic = "force-dynamic"` — the backing
  JSON is owner-generated and gitignored, so these routes must never be statically
  prerendered at Vercel build time against data that may not exist yet.
- A missing bundle or unknown id/symbol calls `notFound()` → a real 404. That is the
  **correct** failure for a capture script to hit — never a broken or blank screenshot.

### Playwright capture recipe

1. Navigate to `https://<your-deploy>/terminal/card/<domain>[/<id>]?key=<TERMINAL_KEY>&capture=1`
   (key and `capture=1` together in one request — see `proxy.ts`'s cookie-plus-header-rewrite
   note for why both need to land on the same response).
2. Set the viewport to **1080×1350** (matches the card's native size; avoids any scaling
   ambiguity even though the element screenshot ignores viewport/zoom).
3. Wait for `[data-capture-ready="true"]` to be present (belt-and-suspenders — the card is
   server-rendered with no client JS, so it's actually ready on first paint, but this is the
   documented no-flake wait condition).
4. Screenshot the **element**, not the page: `page.locator("#capture-canvas").screenshot()`.
   A full-page or viewport screenshot will pick up whatever `CardScaleShell` transform or
   ambient chrome happens to be present — wrong output.
5. Save/name the PNG per the domain (symbol, "risk", "macro", chokepoint id, "portfolio").

Card routes:

| Domain | Card route |
|---|---|
| TA (per symbol) | `/terminal/card/[symbol]?key=...&capture=1` |
| Risk | `/terminal/card/risk?key=...&capture=1` |
| Macro | `/terminal/card/macro?key=...&capture=1` |
| Archetype (per symbol) | `/terminal/card/archetype/[symbol]?key=...&capture=1` |
| Portfolio | `/terminal/card/portfolio?key=...&capture=1` |
| Chokepoint (per id) | `/terminal/card/chokepoint/[id]?key=...&capture=1` |
| DCF (per symbol) | `/terminal/card/dcf/[symbol]?key=...&capture=1` |

---

## 4. Privacy notes

- **`web/data/portfolio.json` is server-only.** It lives outside `web/public/data/` on
  purpose — nothing under `web/data/` ships to the client bundle. It is built by
  `scripts/build_portfolio.py` from `data/portfolio/positions.json` (your real holdings,
  gitignored — see `data/portfolio/README.md`) plus `site.json`/prices, and is read only
  server-side by `/terminal/portfolio` and `/terminal/card/portfolio`.
- **The portfolio capture card is percentage/ratio-only, by construction, not by
  convention.** `PortfolioCaptureCard.tsx` takes a `PortfolioCardData` prop type
  (`web/lib/portfolio.ts`) that structurally **omits every `*_usd` field** — an accidental
  future wire-up that tries to pass a full dollar-figure object fails to typecheck rather
  than silently leaking a number onto a screenshot. The component must never render a `$`
  followed by a digit; this is grepped for in `lib/portfolio.test.ts`. Dollar amounts render
  **only** on the gated `/terminal/portfolio` page itself, behind the same key as every other
  desk.
- **`data/portfolio/positions.json` and `web/data/portfolio.json` are both gitignored.**
  Never commit real holdings. A missing `positions.json` degrades `build_portfolio.py` to an
  empty-state bundle (exit 0, not an error) — normal on a fresh clone.

---

## 5. NFA rails

- Every capture card renders a footer line — "Educational research only — not financial
  advice. NFA." — **unconditionally**, even outside `?capture=1`. This is a mandatory,
  capture-facing footer per the root `CLAUDE.md`; it is never gated behind capture mode
  because the whole point is that it must be on the screenshot.
- Chokepoint cards use fact-vs-reported claim labeling (`headlineClaim()` in
  `web/lib/chokepoints.ts` prefers a `fact` claim over `reported`) and a `card_tagline` field
  that is explicitly documented as capture-card flavor text, never a factual assertion —
  don't promote a tagline into prose elsewhere.
- Archetype verdicts (Graham/Buffett/Lynch) are rule-based toy models over available
  fundamentals, not investment recommendations — label them as such wherever they're
  surfaced outside this repo.
- `/terminal/*` carries `noindex, nofollow` — it is not meant to be publicly discoverable,
  which is a privacy control, not a claims-suppression one; the NFA language still applies to
  anything screenshotted out of it.
