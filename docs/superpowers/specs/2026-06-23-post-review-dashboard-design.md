# Post-Review Dashboard — design spec

*Date: 2026-06-23 · Status: approved-for-planning · Educational/research tooling — not financial advice.*

## 1. Goal

A **standalone local web app** the owner opens to **review the generated social posts** (the
narrated reels and the image carousels), read **the audio/narration script that was pushed to
Higgsfield**, and **attach comments** to each post. Comments are persisted in a documented store so
that **when a post is later regenerated** (via Claude / the existing generation skills), the
regeneration **reads those comments and folds them into the prompt**.

The dashboard only **captures** feedback and displays content. It does **not** regenerate anything
itself — regeneration stays in the existing Claude/terminal/skill flow, which consumes the store.

## 2. Non-goals (YAGNI / explicit cuts)

- **No in-app regeneration / "Regenerate" button.** No Higgsfield calls, no MCP, no pipeline runs
  from the dashboard. (Decided 2026-06-23.)
- **No auth / multi-user / hosting.** Local single-user, `localhost` only.
- **No editing of posts or media** in the app (read-only on media; comments are the only writes).
- **Not part of the `web/` investing site** (static public Vercel deploy, wrong fit) and **not part
  of the AI STACK STUDIO** Electron app (owner chose a browser-based standalone app).

## 3. Architecture

A small **Python + Flask** backend serving a **no-build static frontend** (vanilla HTML/JS/CSS in
the house dark-emerald style). Python is chosen because the consumers of the comments on
regeneration are Python/skill-driven (the reel engine, `stock-carousel`, `higgsfield-ugc`), and the
project's tested codebase is Python (`pytest`); the comment store + `load_for_post()` helper live in
the same language as the regenerator, and the pure logic is TDD'd like the rest of `scripts/`.

```
review/                         ← new standalone app (its own dir)
  app.py            Flask routes: /api/posts, /api/comments (GET/POST/PATCH/DELETE), /media/<path>
  index.py          PURE: higgs/ + content/ filenames -> post bundles (by date->ticker)
  captions.py       PURE: parse reels_/posts_<date>.txt -> { TICKER: caption text }
  comments.py       PURE store ops + load_for_post(); thin file IO wrappers
  paths.py          repo-root / higgs / content / feedback path resolver
  requirements.txt  flask (+ pytest for dev)
  static/
    index.html      the dashboard shell
    app.js          fetches /api/posts, renders gallery + detail + comments, posts comments
    styles.css      house dark-emerald theme
  tests/
    test_index.py · test_captions.py · test_comments.py · test_api.py
  README.md
feedback/
  post_comments.json   the comment store (git-TRACKED so feedback travels)
```

Run: `cd review && pip install -r requirements.txt && python app.py` → serves
`http://localhost:5005` (a distinct port from the :3000 investing site and :5173/Studio).

**Working directory / paths:** `paths.py` resolves `REPO_ROOT` from `review/`'s parent; `HIGGS`,
`CONTENT`, `FEEDBACK` derive from it. The app only **reads** `higgs/` + `content/` and **reads/writes**
`feedback/post_comments.json`.

## 4. The post model (indexer)

`index.py` is a pure function `build_index(higgs_files, content_files) -> list[Post]` that groups
filenames into **post bundles**, mirroring the established naming (same grouping rules as the Studio's
indexer, re-expressed in Python):

- `higgs/reel_<tk>_<date>.mp4` → a **reel** post; its slide PNGs `reel_<tk>_{hook,data,takeaway}.png`
  attach as media.
- `higgs/v4_<tk>_{1_hook,2_data,3_takeaway}.png` → a **carousel** post for `<tk>`.
- `content/carousel_<date>/<TK>/slide_*.html` (+ `brief.md`) → an **HTML carousel** post.
- `higgs/reels_<date>.txt` and `higgs/posts_<date>.txt` → caption sheets (sectioned by ticker),
  attached to that date's posts.
- **Excluded** (scratch, never shown): `hero_*`, `logo_*`, `maya_*`, `voice_*.mp3`, `_check*`,
  `*_anim.mp4`, `*.json`.

**Post identity:** `post_id = "<date>_<TICKER>_<kind>"` — e.g. `2026-06-22_NVDA_reel`,
`2026-06-03_CRM_carousel`. Stable, human-readable, used as the comment key.

**Post record (returned by `/api/posts`):**
```json
{ "post_id":"2026-06-22_NVDA_reel", "date":"2026-06-22", "ticker":"NVDA", "kind":"reel",
  "media":["/media/higgs/reel_nvda_2026-06-22.mp4", "/media/higgs/reel_nvda_data.png", ...],
  "caption":"Every AI chip stock looks expensive ...",
  "audio_script":"Every AI chip stock looks expensive ...",   // = caption for reels; null for carousels
  "comment_count": 2, "open_comment_count": 1 }
```
Sorted newest date first, then ticker.

**Audio script rule:** there is no separate TTS artifact; for **reels** `audio_script` = the post's
caption prose (the text narrated by Higgsfield's "Harrison" voice). For **carousels**
`audio_script = null` (no audio); the UI shows "no audio for this post".

## 5. Caption parser

`captions.py` `parse_captions(text) -> dict[TICKER, str]` splits a caption sheet on its
`=============== REEL n — TICKER (..) ===============` (and the `posts_` equivalent) section headers
and returns the caption/Hashtags block per ticker. (Same contract as the Studio's caption parser,
in Python.) **Sheet selection by kind:** a `reel` post reads `reels_<date>.txt`; a `carousel` post
reads `posts_<date>.txt`; if the kind-specific sheet is absent, fall back to the other sheet for that
date, else caption is `null`. The post's ticker keys into the parsed map.

## 6. Comment store & API

**Store file:** `feedback/post_comments.json`:
```json
{ "version": 1,
  "comments": [
    { "id":"c_ab12cd34", "post_id":"2026-06-22_NVDA_reel",
      "part":"audio", "text":"slow the open line down, less hype",
      "created_at":"2026-06-23T09:40:00Z", "resolved":false }
  ] }
```
- `part` ∈ `{"caption","audio","visual","general"}` (the part-tag).
- `resolved` defaults `false`; regeneration considers **open** (unresolved) comments; the UI can
  toggle resolved to mark a comment addressed.
- `id` = `"c_" + 8 hex chars`. Missing store file → treated as empty.

**Pure ops in `comments.py`** (operate on / return the store dict — no file IO, unit-tested):
- `add_comment(store, post_id, part, text, now) -> (store, comment)` — validates `part`, rejects
  empty `text`, appends.
- `set_resolved(store, comment_id, resolved) -> store`
- `edit_comment(store, comment_id, text) -> store`
- `delete_comment(store, comment_id) -> store`
- `load_for_post(store, post_id, only_open=True) -> list[comment]` — **the regeneration entry point.**

Thin IO wrappers `read_store(path)` / `write_store(path, store)` (atomic write) sit on top.

**HTTP API (`app.py`):**
| Method | Route | Body / params | Returns |
|---|---|---|---|
| GET | `/api/posts` | — | `Post[]` (with `comment_count`/`open_comment_count`) |
| GET | `/api/comments?post_id=…` | — | comments for the post (or all if omitted) |
| POST | `/api/comments` | `{post_id, part, text}` | created comment (400 on bad part / empty text) |
| PATCH | `/api/comments/<id>` | `{resolved?, text?}` | updated comment (404 if absent) |
| DELETE | `/api/comments/<id>` | — | `{ok:true}` (404 if absent) |
| GET | `/media/<path>` | — | the local file (range-enabled for video) |

**`/media/<path>` security:** resolve `REPO_ROOT/<path>`, normalize, and **reject (403) anything not
contained within `REPO_ROOT + os.sep`** (path-traversal guard). Serve via `send_file(..., conditional=True)`
so `<video>` seeking works. Only `higgs/` and `content/` paths are ever produced by the indexer.

## 7. Frontend (static, no build)

`static/index.html` + `app.js` + `styles.css`. Single page:
- **Header:** title + day/ticker filters (client-side over `/api/posts`).
- **Gallery:** post tiles grouped by date (newest first); reel tiles show the `<video>` first frame,
  image carousels (`v4_*`) show the first slide PNG, and HTML carousels (`content/`, no raster
  thumbnail) show a kind/ticker placeholder tile; each tile shows ticker + kind + an open-comment badge.
- **Detail panel (on tile click):**
  - Media: `<video controls>` for reels; slide image strip / linked HTML slides for carousels.
  - **Caption** block (read-only).
  - **Audio script (narration)** block — reels only; labelled "pushed to Higgsfield"; carousels show
    "no audio".
  - **Comments:** list (text · part-tag chip · timestamp · open/resolved toggle · delete); an add form
    (textarea + part-tag `<select>` + submit) that POSTs and refreshes.
- Pure vanilla `fetch`; no framework, no bundler.

## 8. The regeneration feedback loop (integration)

The dashboard writes; regeneration reads. Closing the loop is a **documented format + a helper + a
short instruction added to the generators** — not a rebuild of the generation pipeline:

1. `review/comments.py:load_for_post(store, post_id)` is the reusable reader (returns open comments).
   A tiny CLI `python -m review.comments <post_id>` prints a post's open comments (so Claude/skills or
   the owner can pull them in a terminal).
2. Add a brief **"Feedback loop"** note to the regeneration entry points:
   - `higgs/README_reels.md` (reel engine),
   - the `stock-carousel` skill (`.claude/skills/stock-carousel/SKILL.md`),
   - the `higgsfield-ugc` agent (`.claude/agents/higgsfield-ugc.md`).
   The note: *"Before regenerating post `<date>_<TICKER>_<kind>`, load its open comments
   (`feedback/post_comments.json` / `python -m review.comments <post_id>`) and fold each into the
   generation prompt (respecting the part tag: caption/audio/visual). After regenerating, mark them
   resolved (`PATCH /api/comments/<id>` or edit the store)."*

This is the mechanism by which "comments are taken into account if a regeneration is requested."

## 9. Testing

- **Unit (pytest, TDD):** `index.build_index` (grouping, exclusions, post_id, audio_script rule),
  `captions.parse_captions`, and all pure `comments.py` ops (add/validate/resolve/edit/delete/
  load_for_post, empty-store handling).
- **API (Flask test client):** `/api/posts` shape; comment POST happy-path + 400 on bad part/empty
  text; PATCH resolve; DELETE; `/media` 200 for a real reel and **403 for a `../` traversal attempt**.
- **Smoke (manual):** launch `python app.py`; gallery lists the 4 reels + carousels; play a reel; read
  its audio script; add a comment, reload, see it persist in `feedback/post_comments.json`; resolve it.

## 10. Git artifact policy

- `review/` source is committed.
- `feedback/post_comments.json` is **git-tracked** (feedback is small, valuable, and should travel to
  another machine / be visible to regeneration there). Created on first comment.
- No new build artifacts to ignore (no node_modules; static frontend has no build step).

## 11. Decisions locked (don't re-litigate)

- Standalone **Flask + static** local web app under `review/`; port **5005**.
- Comments **captured only**; regeneration consumes them via the documented store — **no in-app
  regenerate**.
- **Per-post** comments with a **part tag** (`caption`/`audio`/`visual`/`general`); `resolved` flag so
  regeneration uses open comments.
- **Audio script = the caption prose** for reels (no separate TTS artifact); `null` for carousels.
- Comment store **git-tracked** at `feedback/post_comments.json`.

## 12. Disclaimer

Personal content-review tooling. The posts it surfaces are educational/market-commentary only — not
financial advice; congress content is public-record transparency, not accusation.
