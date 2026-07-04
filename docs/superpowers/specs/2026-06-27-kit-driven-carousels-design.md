# Kit-driven carousels — design (2026-06-27)

## Problem
`higgs/_build_v4.py` is bespoke per-cycle content: hard-coded tickers (ADBE/IONQ), hand-written
slide copy, date-stamped hero filenames, and a literal Van Epps 06/16 congress trade. It pulls
*current* numbers into that *old* copy, so the Studio "Build carousel" button silently rebuilds
the previous cycle's carousel rather than the current picks. Goal: make the carousel builder
**kit-driven** so it renders the current cycle from authored content.

## Decision: reuse the reel kit (no separate carousel kit)
Carousels are driven by the SAME `reels_<date>_kit.md` already authored for reels (and parsed by
the Studio Kit page). One authored kit → both 9:16 reels and 4:5 carousels. The reel CFG fields
map onto the existing carousel slide functions:

| Carousel slide | Reel CFG fields |
|---|---|
| `slide_hook` | `kick / head / sub` (+ `ex`, `logo`) |
| `slide_bars` | `data_kick / data_title / mode / rows / data_cap / data_foot` |
| `slide_takeaway` | `tk_kick / big / unit / tk_label / tk_body` |
| `slide_basket` (congress) | the congress section's "card fields" |

CFG string values keep their inline HTML (`<br>`, `<em>`, entities) — the carousel slides render
HTML, so the parser returns RAW values (only JSON `\"`/`\\` unescaped), unlike the Studio's
display parser which strips HTML.

## Components
1. **`scripts/aiinvest/kit_md.py`** — Python parser mirroring `studio/src/main/kit.ts`:
   - `parse_cfg(md, ticker)` → `{hero, logo, ex, src, hook{kick,head,sub}, data{kick,title,cap,foot,mode,rows[]}, takeaway{kick,big,unit,label,body}}` or `None`. `rows` parsed to a list of bare tickers (values filled from the bundle downstream, as reels do).
   - `parse_congress_card(md)` → `{hook_head, hook_sub, pill, name, subhead, chips[], meta[(k,v)], big, big_label, body, footer}` or `None`, from the congress section's card-field bullets.
   - Ports `balancedSpan` / `cfgBlock` (string-aware brace/bracket matching) from kit.ts.
   - Pure; TDD against the real `higgs/reels_2026-06-27_kit.md`.
2. **`_build_v4.py` rewrite** — split into:
   - the existing `slide_*` HTML functions (unchanged),
   - `build_slides(kit_md, site, quantum, congress_card, hero_map, logo_map)` → `{filename: html}` (pure, testable without Playwright; fills bar/takeaway numbers from `site/quantum.json`),
   - `main()` — select newest `higgs/reels_<date>_kit.md` (or `--date` / `--kit`), load bundles + hero/logo PNGs as base64 (missing hero → `None` → render on solid bg + warn), render via Playwright to `v4_<tk>_*.png`.
   - CLI: `python higgs/_build_v4.py [--date YYYY-MM-DD] [--kit <path>]`. Button command unchanged.

## Numbers
`rows` carry tickers only; `slide_bars` fills magnitudes from the bundle per `mode` (`disc` =
`fundamental_discount_pct`, `mult` = `price/fundamental_value`) — same convention as the reel CFG.
`src` ("site"|"quantum") selects the bundle.

## Hero art
Use the CFG `hero` filename; if the PNG is absent (Phase-1 not run), render on the solid dark
background and print a warning — the button must work before hero art exists, not crash.

## Testing
TDD `kit_md.py` (CFG fields, rows→tickers, congress card) against the real kit; TDD `build_slides`
(produces expected filenames; HTML contains key values; hero-missing path). Playwright render is a
thin smoke step (produces PNGs).

## Out of scope
No new kit format; no reel-pipeline changes; no automatic Phase-1 hero/voice generation.
