# Preview Page (script/kit monitoring) — design spec

*Date: 2026-06-23 · Status: approved-for-planning · Enhancement to the post-review dashboard (`review/`). Educational/research tooling — not financial advice.*

## 1. Goal

Add a **"Preview"** page to the post-review dashboard so the owner can monitor the **pre-creation
script/kit documents** in `higgs/` — *before* the reels are rendered. Specifically: see each
`reels_<date>.txt` (reel narration/caption sheet), `posts_<date>.txt` (carousel caption sheet), and
`reels_<date>_kit.md` (the reel build kit), with the `.txt` shown as formatted text and the `.md`
**rendered** as markdown (with a Raw toggle).

This complements the existing **Posts** gallery (which only shows *rendered* reels/carousels): the
Preview page surfaces the planning docs that exist even when no `.mp4` has been produced yet (e.g.
today's 2026-06-23 kit, which has scripts but no rendered reels).

## 2. Non-goals (YAGNI)

- **No editing** of the script/kit files in the app (read-only view).
- **No comments** on scripts (comments stay on rendered posts; this is a monitoring view).
- **No external markdown library / build step / network fetch** — a small built-in renderer only.
- **No new content endpoint** — file content is served by the existing `/media/` route.

## 3. Architecture

A pure listing module + one Flask route + a frontend Preview view with a built-in markdown renderer.
All additive; no existing behavior changes.

```
review/
  scripts.py          NEW (pure): classify+list higgs/ planning docs -> [{name,date,kind,media}]
  app.py              MODIFY: add GET /api/scripts
  static/
    index.html        MODIFY: Posts|Preview nav toggle + a #preview container
    app.js            MODIFY: Preview view (list + content panel) + a built-in markdown renderer
    styles.css        MODIFY: preview styling
  tests/
    test_scripts.py   NEW: pytest for list_scripts
    test_api.py       MODIFY: add a /api/scripts route test
```

## 4. The listing module (`scripts.py`, pure)

`list_scripts(higgs_files: list[str]) -> list[dict]` — classify the planning docs by filename and
return a sorted list. Each entry:
```json
{ "name": "reels_2026-06-23.txt", "date": "2026-06-23", "kind": "reel-script",
  "media": "/media/higgs/reels_2026-06-23.txt" }
```
- **Classification (only these three kinds are included; everything else ignored):**
  - `reels_<date>.txt` → `kind: "reel-script"`
  - `posts_<date>.txt` → `kind: "post-script"`
  - `reels_<date>_kit.md` → `kind: "kit"`
  - `<date>` is `YYYY-MM-DD`. Any file not matching these three patterns (e.g. `reels_manifest.json`,
    `make_reel.py`, `hero_*`) is excluded.
- **Sort:** newest `date` first; within a date, `kit` then `reel-script` then `post-script`, then name.
- `media` is the repo-root-relative `/media/higgs/<name>` URL (served by the existing route).

The `kit` md and its `reel-script` txt share a date, so they group together in the UI.

## 5. API (`app.py`)

Add one route:
- `GET /api/scripts` → `jsonify(list_scripts(<higgs filenames>))`, using the same `_list_higgs()`
  helper the posts route uses.

**Content** is fetched by the frontend from the **existing** `GET /media/<path>` route
(`/media/higgs/reels_2026-06-23.txt`, etc.) — already path-guarded to REPO_ROOT. No new endpoint.

## 6. Frontend

**Nav toggle (header):** two views — **Posts** (the existing gallery, default) and **Preview**.
Switching toggles which section is visible; the day/ticker filters and Refresh stay relevant to Posts.

**Preview view (`#preview`):**
- **Left:** the script list from `/api/scripts`, grouped by date (newest first); each row shows the
  file name + a kind chip (`kit` / `reel-script` / `post-script`).
- **Right (content panel):** on click, fetch the doc's content from its `media` URL (plain `fetch` →
  `res.text()`), then:
  - `.txt` → a formatted monospace block (`<pre>`, escaped) preserving the sheet layout.
  - `.md` → **rendered** via the built-in renderer, with a **Raw / Rendered** toggle (Raw = the
    escaped source in a `<pre>`).
- Show the file name + date + kind as a header above the content.

**Built-in markdown renderer (`renderMarkdown(src) -> htmlString`):** a small vanilla-JS function,
no external library. It **escapes HTML first** (so any `<br>`, `<em>`, or `<script>` in the source
renders as literal text, not injected markup), then applies markdown formatting for the elements the
kit uses: ATX headings `#`–`###`, `**bold**`, `*italic*`, inline `` `code` ``, fenced ```` ``` ````
code blocks, unordered lists (`-`/`*`), GitHub-style tables (`| a | b |` with a `---` separator row),
blockquotes (`>`), horizontal rule (`---`), and `[text](url)` links (rendered as anchors opening in a
new tab with `target="_blank" rel="noopener noreferrer"`). Unsupported syntax
falls through as escaped text. The renderer is the one piece doing string→HTML, so HTML-escaping
before formatting is the security boundary.

## 7. Data flow

Open Preview → `GET /api/scripts` → render the grouped list → click a doc → `fetch(media).then(text)`
→ render (`.txt` preformatted / `.md` rendered|raw). Switching back to Posts shows the gallery
unchanged.

## 8. Testing

- **Unit (pytest):** `scripts.list_scripts` — classifies the three kinds, parses dates, excludes
  non-planning files (manifest, scripts, scratch), sorts newest-first with the kind ordering.
- **API (Flask test client):** `GET /api/scripts` returns a list including the real
  `reels_2026-06-23.txt` (reel-script) and `reels_2026-06-23_kit.md` (kit).
- **Smoke (manual):** open Preview; the 2026-06-23 kit + script appear; clicking the `.md` renders
  formatted markdown; the Raw toggle shows source; clicking a `.txt` shows the formatted sheet;
  switching Posts/Preview works.
- The client-side markdown renderer is verified by manual smoke (the project's automated tests are
  pytest; no JS test runner is in scope).

## 9. Decisions locked

- Three doc kinds only: `reel-script` (`reels_<date>.txt`), `post-script` (`posts_<date>.txt`),
  `kit` (`reels_<date>_kit.md`). Grouped by date, newest first.
- Content served by the **existing** `/media/` route; no new content endpoint.
- Markdown rendered by a **built-in** vanilla-JS renderer (no external lib, no build, CSP-clean),
  **escape-then-format**, with a Raw toggle.
- Read-only; no comments on scripts.

## 10. Disclaimer

Personal content-monitoring tooling. Surfaced content is educational/market-commentary only — not
financial advice; congress content is public-record transparency, not accusation.
