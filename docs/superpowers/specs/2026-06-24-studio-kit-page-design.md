# Studio "Kit" page (read-only pre-build examination) — design spec

*Date: 2026-06-24 · Status: approved-for-planning · Phase 1 of 2 (Phase 2 = in-app editing, scoped later). Enhancement to the AI STACK STUDIO Electron app (`studio/`). Educational/research tooling — not financial advice.*

## 1. Goal

Add a **read-only "Kit" page** to the AI STACK STUDIO so the owner can examine, *before a reel is
rendered*, everything that drives the post: the **script**, the **slide-by-slide descriptions**, and
the **functionally-relevant source data** (the fundamentals the slide numbers are built from). Native
in the Electron app (a `Posts | Kit` view toggle), presented so the important data is easy to spot.

This is the "pre-build" counterpart to the Studio's existing post-review gallery (which shows
*rendered* posts). The Studio already does post-review well; this phase adds only the pre-build view.

## 2. Non-goals (Phase 1)

- **No editing / write-back.** Read-only examination. (Phase 2 — in-app editing of the script/slide
  copy — is scoped separately after this is tested.)
- **No comments** (the Studio's post-review covers that need; not part of this page).
- **No new generation / rendering** triggered from the page.
- **No external markdown/parsing library** — small built-in parsers, consistent with the Studio.

## 3. Architecture

A pure parsing/assembly module + two IPC handlers + a new renderer view. All additive; reuses the
Studio's existing helpers (`paths`, `parseCaptions`, `joinStock`, `readJson`). No Python.

```
studio/src/main/
  kit.ts            NEW (pure parsers + assembly): kit files -> structured KitEntry/KitDetail
  api.ts            MODIFY: add ipcMain.handle 'kit:list' and 'kit:get'
  paths.ts          (reuse HIGGS, DATA)
studio/src/preload/index.ts   MODIFY: expose studio.kit.{list,get}
studio/src/renderer/src/
  global.d.ts       MODIFY: type studio.kit
  App.tsx           MODIFY: Posts|Kit nav toggle; show KitView when Kit active
  components/
    KitView.tsx     NEW: planned-reel list (by date) + structured detail panel
  test (vitest):
studio/test/kit.test.ts   NEW: TDD the pure parsers
```

## 4. Data sources & what a "kit entry" is

A planned reel for `<date>` is assembled from two files in `higgs/` plus the live data bundles:
- **`reels_<date>.txt`** — the script sheet, sectioned `=============== REEL n — TICKER (THEME) ===============`,
  each with a `Caption:` block (the narration/caption) and a `Hashtags:` line.
- **`reels_<date>_kit.md`** — the build kit: per reel a `"TICKER":{ ... }` **CFG block** (the slide
  copy), a hero-image-prompt blockquote, and a "Story + sources" line (the news angle). *May be
  absent for older dates* (e.g. 2026-06-22 has the `.txt` but no `_kit.md`) → those entries show the
  script only, with slides/hero marked "not in kit".
- **`web/public/data/{site,quantum,congress}.json`** — the live fundamentals, joined by ticker via
  the existing `joinStock` (price, GuruFocus fair value, discount %, valuation tag, P/E, P/S, growth,
  returns, layer).

**A "kit entry" = one `(date, ticker)` planned reel.** `id = "<date>_<TICKER>"`.

## 5. The pure parsers (`kit.ts`, TDD'd)

- `parseScriptSheet(text) -> Array<{ ticker, theme, script, hashtags }>` — split `reels_<date>.txt`
  on the `===… — TICKER (THEME) ===` headers; per section capture the `Caption:` body (script) and the
  `Hashtags:` line. (Generalizes the existing `parseCaptions`; this one also returns theme + hashtags
  split out.)
- `parseKitCfg(md, ticker) -> Slides | null` — locate the `"TICKER":{ … }` CFG block in the kit `.md`
  (from `"TICKER":{` to its matching closing `}`), then extract the known fields by name and map to
  three slides:
  - **hook:** `kick` (eyebrow), `head` (headline), `sub` (subhead), `ex` (exchange label)
  - **data:** `data_kick`, `data_title`, `data_cap`, `data_foot`, `rows` (raw string), `mode`
  - **takeaway:** `tk_kick`, `big`, `unit`, `tk_label`, `tk_body`
  Field values contain presentational HTML/entities (`<br>`, `<em …>`, `&mdash;`, `&rsquo;`); the
  parser **strips tags and decodes the common entities to plain text** for the examine view. Missing
  fields are omitted; a missing/unparseable block returns `null` (entry shows "slides not in kit").
- `parseHeroPrompt(md, ticker) -> string | null` and `parseStory(md, ticker) -> string | null` —
  pull the hero-prompt blockquote and the "Story + sources" line from that ticker's kit `.md` section.

These are pure (text in → data out) and are the unit-tested core.

## 6. Assembly + IPC (`api.ts`)

- `kit:list` → scan `higgs/` for `reels_<date>.txt` files; for each, `parseScriptSheet` → emit
  `{ id, date, ticker, theme }` per reel; sort newest-date-first, then ticker. (A date with a `.txt`
  but the captions unparseable is skipped.)
- `kit:get (date, ticker)` → assemble `KitDetail`:
  ```
  { id, date, ticker, theme,
    script, hashtags,
    slides: { hook, data, takeaway } | null,   // parseKitCfg
    hero_prompt: string | null,                // parseHeroPrompt
    story: string | null,                      // parseStory
    source: { found, valuation, source, layer } // joinStock(ticker, bundles)
  }
  ```
  Reuses the existing `readJson('site.json'|'quantum.json'|'congress.json')` + `joinStock`.

## 7. Renderer (`KitView.tsx` + `App.tsx` toggle)

- **Nav toggle** in the header: `Posts` (the existing gallery+detail, default) and `Kit`. Toggling
  swaps the middle section; the Terminal footer + quick-actions stay. (The Studio's `App.tsx` middle
  is `flex(Gallery + Detail)`; add a sibling `KitView` and show one at a time.)
- **KitView** (own local state; loads `kit.list()` on first open):
  - **Left:** planned reels grouped by date (newest first); each row = ticker + theme.
  - **Right (detail, on click → `kit.get`):** structured, scannable:
    - **Header:** `TICKER · theme · date` + a prominent **valuation tag badge**
      (Undervalued / Overvalued / Fairly Valued) when `source.valuation.fundamental_valuation` exists.
    - **Source data card (highlighted):** price, **GF fair value**, **discount %**, tag, P/E, P/S,
      rev-growth, 1y/5y return — the numbers the slides are built from (live, so drift is visible).
    - **Script:** the narration/caption text + the hashtags.
    - **Slides:** three cards — **Hook**, **Data**, **Takeaway** — each showing its parsed copy
      (and for Data, the `rows` + `mode`). If `slides` is null → "slides not in this date's kit".
    - **Hero prompt** + **News angle** (story), when present.
- House dark-emerald style; the valuation badge + the source-data card are the visual focal points
  ("important data easy to spot"). Text is rendered escaped (plain text from the parsers; no innerHTML
  of file content).

## 8. Testing

- **Unit (Vitest, TDD):** `parseScriptSheet` (sectioning, caption + hashtags + theme, empty input),
  `parseKitCfg` (field extraction → 3 slides, HTML/entity stripping, missing block → null),
  `parseHeroPrompt`/`parseStory` (extract per ticker; absent → null). Fixtures mirror the real
  2026-06-23 kit shape.
- **Smoke (manual):** `npm run dev`; the Kit toggle shows the planned reels; clicking NBIS shows the
  valuation badge (Fairly Valued) + source numbers (GF $278 vs $284), the script, the 3 slide cards;
  IONQ/QBTS show the quantum spread; a date with only a `.txt` shows script-only gracefully.

## 9. Decisions locked

- Native in the Studio (TS/Electron); reuse `parseCaptions`-style parsing, `joinStock`, `readJson`.
- `id = "<date>_<TICKER>"`; entries from `reels_<date>.txt`; slides/hero/story from `reels_<date>_kit.md`
  (absent → script-only).
- Slide copy shown as **plain text** (tags/entities stripped) for scannability.
- **Read-only** (Phase 1). Editing/write-back is Phase 2.
- Source fundamentals shown **live** from the bundles via `joinStock` (so kit-vs-live drift is visible).

## 10. Disclaimer

Personal content-prep tooling. Surfaced content is educational/market-commentary only — not financial
advice; congress content is public-record transparency, not accusation.
