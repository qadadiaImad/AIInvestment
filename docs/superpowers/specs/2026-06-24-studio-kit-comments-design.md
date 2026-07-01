# Studio Kit comments + "Regenerate with comments" — design spec

*Date: 2026-06-24 · Status: approved-for-planning · Phase 2 of the Studio Kit page (Phase 1 = read-only examination, shipped). Enhancement to the AI STACK STUDIO Electron app (`studio/`). Educational/research tooling — not financial advice.*

## 1. Goal

Make the Studio's Kit page actionable: let the owner **attach comments** to a planned reel (per
kit section), and **feed those comments into the next generation prompt** via a "Regenerate with
comments" button that composes the open comments into a regeneration instruction and **types it
into the Studio's embedded terminal** (where `claude` runs) for the owner to review and run.

The comments persist to the **shared `feedback/post_comments.json`** store — the same one the web
post-review dashboard and the generators' existing "Feedback loop" notes already use — so feedback
is unified across surfaces, and the regeneration loop already knows how to read it.

## 2. Non-goals

- **No direct text-editing** of the script/slide copy (the "editable" ask is satisfied by commenting).
- **No auto-run** of regeneration: the button TYPES the command into the terminal; the owner reviews
  and presses Enter. No Higgsfield spend or pipeline run is triggered by the Studio itself.
- **No new store format** — reuse the existing `feedback/post_comments.json` schema.

## 3. Architecture

A pure comment-store + prompt-composer module + IPC + a comment panel in the Kit view + a no-auto-submit
terminal-type hook. Reuses the Studio's `paths`/`api` patterns and the shared store.

```
studio/src/main/
  comments.ts       NEW (pure store ops + composeRegenPrompt) + atomic IO over feedback/post_comments.json
  paths.ts          MODIFY: add FEEDBACK_FILE = REPO_ROOT/feedback/post_comments.json
  api.ts            MODIFY: ipcMain.handle comments:list/add/setResolved/delete/composePrompt
studio/src/preload/index.ts        MODIFY: expose studio.comments.{list,add,setResolved,delete,composePrompt}
studio/src/renderer/src/
  global.d.ts       MODIFY: type studio.comments
  components/
    Terminal.tsx    MODIFY: add `typeIntoTerminal(cmd)` (types WITHOUT the auto-`\r` injectToTerminal uses)
    KitView.tsx     MODIFY: add a Comments panel + "Regenerate with comments" button to the detail
studio/test/comments.test.ts   NEW: TDD the pure store ops + composeRegenPrompt
```

## 4. Comment store (shared)

Reuse `feedback/post_comments.json`: `{ "version": 1, "comments": [ {id, post_id, part, text, created_at, resolved} ] }`.
- `comments.ts` ports the pure ops from `review/comments.py`: `emptyStore`, `addComment(store, post_id, part, text, now, _id?) -> {store, comment}` (throws on bad part / empty text), `setResolved(store, id, bool)` (throws if absent), `deleteComment(store, id)` (throws if absent), `loadForPost(store, post_id, onlyOpen=true)`, `readStore(path)` (missing/corrupt → emptyStore), `writeStore(path, store)` (atomic: tmp + rename). (`editComment` is NOT ported — YAGNI for this panel.)
- **Comment id:** `"c_" + 8 hex chars`.
- **`post_id` = `"<date>_<TICKER>_reel"`** — the same id the regeneration loop and the web post-review use for a reel, so a Kit comment and a web post comment for that reel are the same record.
- **Parts (the Studio add form's vocabulary):** `VALID_PARTS = ["script","hook","data","takeaway","hero","general"]` (kit-section aligned). `addComment` validates the part is one of these. **Reading** (`loadForPost`) does NOT validate parts, so web-dashboard comments on the same reel (parts `caption`/`audio`/`visual`/`general`) still load and display.

## 5. `composeRegenPrompt` (the injected command)

Pure: `composeRegenPrompt(date, ticker, openComments) -> string`. Builds a single-line, PowerShell-safe
`claude "…"` command that folds the open comments + the rails into a regeneration instruction. Shape:

```
claude "Regenerate the <date> <TICKER> reel honoring these review comments — [<part>] <text>; [<part>] <text>. Update higgs/reels_<date>.txt + reels_<date>_kit.md per the comments; keep the rails (no first person; reportedly, never name the outlet; congress = transparency not accusation; thin footer NFA). Then mark these comments resolved."
```
- **Safety:** every interpolated string (comment text and the assembled inner prompt) is sanitized:
  newlines → spaces, and **double-quotes → single-quotes**, so the final value contains no inner `"`
  and is safe inside the outer PowerShell `"…"`. Returns `""` when there are no open comments.

## 6. IPC (`api.ts`)

Reuse the existing `_now()` + the new `FEEDBACK_FILE`. Handlers:
- `comments:list (postId)` → `loadForPost(readStore(FEEDBACK_FILE), postId, onlyOpen=false)` (all, so the UI can show resolved greyed).
- `comments:add (postId, part, text)` → read → `addComment(…, _now())` → write → return the comment. (Throws on bad part/empty text → the invoke rejects; the renderer guards.)
- `comments:setResolved (id, resolved)` → read → setResolved → write → `{ok:true}`.
- `comments:delete (id)` → read → deleteComment → write → `{ok:true}`.
- `comments:composePrompt (date, ticker)` → load open comments for `"<date>_<TICKER>_reel"` → `composeRegenPrompt(date, ticker, open)` → return the string (`""` if none).

Preload exposes `window.studio.comments.{list,add,setResolved,delete,composePrompt}`; `global.d.ts` types them.

## 7. Renderer (`KitView.tsx` + `Terminal.tsx`)

- **`Terminal.tsx`:** add `export let typeIntoTerminal: (cmd: string) => void = () => {}` and set it in the
  existing mount effect to `(cmd) => window.studio.term.input(cmd)` — i.e. types the text WITHOUT the
  trailing `\r` (so it does not auto-submit; the owner reviews then presses Enter). The existing
  `injectToTerminal` (which appends `\r`, used by QuickActions) is unchanged.
- **`KitView.tsx`:** add a **Comments panel** to the kit detail (a `KitComments` subcomponent keyed on
  `postId = "<date>_<TICKER>_reel"`, own state):
  - Loads `comments:list(postId)` on mount / when the selected reel changes.
  - **List:** each comment shows text · a **section chip** (its `part`) · timestamp · a resolve/reopen
    toggle · delete. Resolved comments render greyed.
  - **Add form:** a `part` `<select>` (script/hook/data/takeaway/hero/general) + textarea + Add button →
    `comments:add` → refresh.
  - **"Regenerate with comments" button:** → `comments:composePrompt(date, ticker)`; if non-empty,
    `typeIntoTerminal(prompt)` and show a hint ("Typed into the terminal — review and press Enter to run").
    If there are no open comments, the button is disabled / shows "no open comments".
  - House dark-emerald style, consistent with the existing detail panel.

## 8. Testing

- **Unit (Vitest, TDD):** all pure `comments.ts` ops (add + part/empty validation, setResolved, delete,
  loadForPost open-vs-all, readStore missing→empty, writeStore→readStore roundtrip) and
  `composeRegenPrompt` (includes ticker/date + each `[part] text`, the rails reminder, the
  `claude "…"` wrapper, NO inner double-quotes after sanitizing, `""` when no open comments).
- **Smoke (manual):** `npm run dev`; on a Kit reel, add a comment (e.g. part `data`, "lead with fair
  value"); it persists to `feedback/post_comments.json` and lists; resolve/delete work; "Regenerate
  with comments" types the `claude "…"` command into the terminal with the comment folded in (and does
  NOT auto-run). Confirm a comment added here also appears in the web dashboard for that reel
  (shared store).

## 9. Decisions locked

- Comments are the "editable" mechanism (no direct script text-editing).
- Shared `feedback/post_comments.json`, `post_id = <date>_<TICKER>_reel`; Studio add-parts are the kit
  sections, but reads are part-agnostic (web comments coexist).
- "Regenerate with comments" **composes + types** into the terminal (no auto-submit, no auto-run).
- `comments.ts` ports `review/comments.py` (minus `editComment`) + adds `composeRegenPrompt`.

## 10. Disclaimer

Personal content-prep tooling. Surfaced content is educational/market-commentary only — not financial
advice; congress content is public-record transparency, not accusation.
