# Studio Kit Comments + Regenerate-with-comments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comment panels to the Studio's Kit page (per planned reel) and a "Regenerate with comments" button that composes the open comments into a `claude "…"` command typed into the embedded terminal.

**Architecture:** A pure TypeScript comment-store module (`comments.ts`, ports `review/comments.py` + adds `composeRegenPrompt`, TDD'd with Vitest) reads/writes the shared `feedback/post_comments.json`; IPC handlers expose CRUD + compose; a `KitComments` panel in `KitView` captures comments and a button types the composed prompt into the terminal via a new no-auto-submit `typeIntoTerminal` hook.

**Tech Stack:** Electron 42, electron-vite, React 19, Tailwind v4, Vitest 3, TypeScript 5 (the existing `studio/` app).

**Spec:** `docs/superpowers/specs/2026-06-24-studio-kit-comments-design.md`

## Global Constraints

- All changes under `studio/`. Tests: `cd studio && npx vitest run`. Build: `cd studio && npx electron-vite build`.
- Additive only — do not change existing Posts/Detail/Kit/Terminal/QuickActions behavior. `injectToTerminal` (appends `\r`, used by QuickActions) stays unchanged.
- Comment store = the SHARED `feedback/post_comments.json` (repo root): `{ "version":1, "comments":[ {id,post_id,part,text,created_at,resolved} ] }`. `post_id = "<date>_<TICKER>_reel"`. Comment id = `"c_" + 8 hex chars`. Writes are atomic (tmp + rename).
- `VALID_PARTS = ["script","hook","data","takeaway","hero","general"]` — `addComment` validates the added part against this; `loadForPost` does NOT validate parts (so web-dashboard comments with other parts still load).
- `composeRegenPrompt(date, ticker, open)` returns a single-line `claude "…"` command; sanitize every interpolated string (newlines → space, `"` → `'`) so the value contains no inner double-quotes; return `""` when `open` is empty.
- `typeIntoTerminal(cmd)` types WITHOUT the trailing `\r` (no auto-submit; owner reviews + presses Enter).
- House colors: bg `#0A0D12`, accent emerald `#34D399`, text `#E8EDF2`. Tailwind inline.

---

## Task 1: `comments.ts` store + `composeRegenPrompt` (TDD) + `FEEDBACK_FILE` path

**Files:**
- Modify: `studio/src/main/paths.ts`
- Create: `studio/src/main/comments.ts`
- Create: `studio/test/comments.test.ts`

**Interfaces:**
- Produces: `paths.FEEDBACK_FILE`; and from `comments.ts`: `emptyStore`, `addComment(store,postId,part,text,now,_id?) -> {store,comment}`, `setResolved(store,id,bool) -> Store`, `deleteComment(store,id) -> Store`, `loadForPost(store,postId,onlyOpen=true) -> Comment[]`, `readStore(path) -> Store`, `writeStore(path,store)`, `composeRegenPrompt(date,ticker,open) -> string`, plus `VALID_PARTS`, types `Comment`/`Store`.

- [ ] **Step 1: Add `FEEDBACK_FILE` to `studio/src/main/paths.ts`**

Append after the `DATA` line:
```ts
export const FEEDBACK_FILE = join(REPO_ROOT, 'feedback', 'post_comments.json')
```

- [ ] **Step 2: Write the failing test `studio/test/comments.test.ts`**

```ts
import { describe, it, expect } from 'vitest'
import { mkdtempSync } from 'fs'
import { join } from 'path'
import { tmpdir } from 'os'
import {
  emptyStore, addComment, setResolved, deleteComment, loadForPost,
  readStore, writeStore, composeRegenPrompt,
} from '../src/main/comments'

describe('comment store ops', () => {
  it('adds and loads for a post', () => {
    const { store, comment } = addComment(emptyStore(), '2026-06-23_NBIS_reel', 'data',
      'lead with fair value', '2026-06-24T00:00:00Z', 'c_00000001')
    expect(comment.id).toBe('c_00000001')
    expect(comment.part).toBe('data')
    expect(comment.resolved).toBe(false)
    expect(loadForPost(store, '2026-06-23_NBIS_reel').length).toBe(1)
  })
  it('rejects bad part and empty text', () => {
    expect(() => addComment(emptyStore(), 'p', 'bogus', 'x', 'now')).toThrow()
    expect(() => addComment(emptyStore(), 'p', 'data', '  ', 'now')).toThrow()
  })
  it('resolve hides from open load', () => {
    let { store } = addComment(emptyStore(), 'p1', 'general', 'fix', 'now', 'c_aaaa0001')
    store = setResolved(store, 'c_aaaa0001', true)
    expect(loadForPost(store, 'p1', true)).toEqual([])
    expect(loadForPost(store, 'p1', false).length).toBe(1)
  })
  it('delete works; missing id throws', () => {
    let { store } = addComment(emptyStore(), 'p1', 'hook', 'x', 'now', 'c_aaaa0002')
    store = deleteComment(store, 'c_aaaa0002')
    expect(loadForPost(store, 'p1', false)).toEqual([])
    expect(() => setResolved(store, 'c_missing', true)).toThrow()
  })
  it('write then read roundtrip; missing file -> empty', () => {
    const p = join(mkdtempSync(join(tmpdir(), 'kitc-')), 'feedback', 'post_comments.json')
    expect(readStore(p)).toEqual(emptyStore())
    const { store } = addComment(emptyStore(), 'p1', 'script', 'hi', 'now', 'c_aaaa0003')
    writeStore(p, store)
    expect(readStore(p).comments[0].text).toBe('hi')
  })
})

describe('composeRegenPrompt', () => {
  it('folds open comments + rails into a claude command with no inner double-quotes', () => {
    const open = [
      { id: 'c1', post_id: '2026-06-23_NBIS_reel', part: 'data', text: 'lead with "fair value"', created_at: 'now', resolved: false },
      { id: 'c2', post_id: '2026-06-23_NBIS_reel', part: 'script', text: 'slow the open', created_at: 'now', resolved: false },
    ]
    const cmd = composeRegenPrompt('2026-06-23', 'NBIS', open)
    expect(cmd.startsWith('claude "')).toBe(true)
    expect(cmd.endsWith('"')).toBe(true)
    expect(cmd).toContain('2026-06-23 NBIS reel')
    expect(cmd).toContain('[data]')
    expect(cmd).toContain('slow the open')
    expect(cmd).toContain('mark these comments resolved')
    expect((cmd.match(/"/g) || []).length).toBe(2)   // only the 2 wrapper quotes; inner ones sanitized
  })
  it('returns empty string when no open comments', () => {
    expect(composeRegenPrompt('2026-06-23', 'NBIS', [])).toBe('')
  })
})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd studio && npx vitest run test/comments.test.ts`
Expected: FAIL — cannot find module `../src/main/comments`.

- [ ] **Step 4: Implement `studio/src/main/comments.ts`**

```ts
// Comment store for the Studio Kit page — shared feedback/post_comments.json.
// Pure ops (unit-tested) + atomic file IO. composeRegenPrompt builds the terminal command.
import { readFileSync, writeFileSync, renameSync, mkdirSync, existsSync } from 'fs'
import { dirname } from 'path'
import { randomBytes } from 'crypto'

export type Comment = {
  id: string; post_id: string; part: string; text: string; created_at: string; resolved: boolean
}
export type Store = { version: number; comments: Comment[] }

export const VALID_PARTS = ['script', 'hook', 'data', 'takeaway', 'hero', 'general']

export function emptyStore(): Store {
  return { version: 1, comments: [] }
}

function newId(): string {
  return 'c_' + randomBytes(4).toString('hex')
}

export function addComment(
  store: Store, postId: string, part: string, text: string, now: string, _id?: string,
): { store: Store; comment: Comment } {
  if (!VALID_PARTS.includes(part)) throw new Error(`bad part ${part}; must be one of ${VALID_PARTS.join(', ')}`)
  if (!text || !text.trim()) throw new Error('comment text is empty')
  const comment: Comment = {
    id: _id || newId(), post_id: postId, part, text: text.trim(), created_at: now, resolved: false,
  }
  return { store: { ...store, comments: [...store.comments, comment] }, comment }
}

function find(store: Store, id: string): Comment {
  const c = store.comments.find((x) => x.id === id)
  if (!c) throw new Error(`comment not found: ${id}`)
  return c
}

export function setResolved(store: Store, id: string, resolved: boolean): Store {
  find(store, id)
  return { ...store, comments: store.comments.map((c) => (c.id === id ? { ...c, resolved } : c)) }
}

export function deleteComment(store: Store, id: string): Store {
  find(store, id)
  return { ...store, comments: store.comments.filter((c) => c.id !== id) }
}

export function loadForPost(store: Store, postId: string, onlyOpen = true): Comment[] {
  return store.comments.filter((c) => c.post_id === postId && (!onlyOpen || !c.resolved))
}

export function readStore(path: string): Store {
  if (!existsSync(path)) return emptyStore()
  try {
    const data = JSON.parse(readFileSync(path, 'utf-8'))
    return { version: data.version ?? 1, comments: data.comments ?? [] }
  } catch {
    return emptyStore()
  }
}

export function writeStore(path: string, store: Store): void {
  mkdirSync(dirname(path), { recursive: true })
  const tmp = path + '.tmp'
  writeFileSync(tmp, JSON.stringify(store, null, 2), 'utf-8')
  renameSync(tmp, path)
}

const sanitize = (s: string): string => s.replace(/[\r\n]+/g, ' ').replace(/"/g, "'").trim()

export function composeRegenPrompt(date: string, ticker: string, open: Comment[]): string {
  if (!open.length) return ''
  const notes = open.map((c) => `[${c.part}] ${sanitize(c.text)}`).join('; ')
  const inner =
    `Regenerate the ${date} ${ticker} reel honoring these review comments — ${notes}. ` +
    `Update higgs/reels_${date}.txt + reels_${date}_kit.md per the comments; keep the rails ` +
    `(no first person; reportedly, never name the outlet; congress = transparency not accusation; thin footer NFA). ` +
    `Then mark these comments resolved.`
  return `claude "${sanitize(inner)}"`
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd studio && npx vitest run test/comments.test.ts`
Expected: PASS (7 tests).

- [ ] **Step 6: Run the full Studio suite (no regressions)**

Run: `cd studio && npx vitest run`
Expected: all existing tests + the 7 new ones pass.

- [ ] **Step 7: Commit**

```bash
git add studio/src/main/paths.ts studio/src/main/comments.ts studio/test/comments.test.ts
git commit -m "feat(studio): comment store (shared feedback) + composeRegenPrompt, TDD"
```

---

## Task 2: IPC — `comments:list/add/setResolved/delete/composePrompt`

**Files:**
- Modify: `studio/src/main/api.ts`
- Modify: `studio/src/preload/index.ts`
- Modify: `studio/src/renderer/src/global.d.ts`

**Interfaces:**
- Consumes: `comments.ts` ops + `FEEDBACK_FILE` (Task 1); the existing `_now()` in `api.ts`.
- Produces: IPC `comments:*`; `window.studio.comments.{list,add,setResolved,delete,composePrompt}`.

- [ ] **Step 1: Add imports + handlers to `studio/src/main/api.ts`**

Add `FEEDBACK_FILE` to the existing paths import (change `import { HIGGS, CONTENT, DATA } from './paths'` to include it) and add a comments import near the other module imports:
```ts
import { HIGGS, CONTENT, DATA, FEEDBACK_FILE } from './paths'
import * as comments from './comments'
```
Inside `registerApi()`, after the existing `kit:get` handler, add:
```ts
  ipcMain.handle('comments:list', (_e, postId: string) =>
    comments.loadForPost(comments.readStore(FEEDBACK_FILE), postId, false))

  ipcMain.handle('comments:add', (_e, postId: string, part: string, text: string) => {
    const { store, comment } = comments.addComment(comments.readStore(FEEDBACK_FILE), postId, part, text, _now())
    comments.writeStore(FEEDBACK_FILE, store)
    return comment
  })

  ipcMain.handle('comments:setResolved', (_e, id: string, resolved: boolean) => {
    comments.writeStore(FEEDBACK_FILE, comments.setResolved(comments.readStore(FEEDBACK_FILE), id, resolved))
    return { ok: true }
  })

  ipcMain.handle('comments:delete', (_e, id: string) => {
    comments.writeStore(FEEDBACK_FILE, comments.deleteComment(comments.readStore(FEEDBACK_FILE), id))
    return { ok: true }
  })

  ipcMain.handle('comments:composePrompt', (_e, date: string, ticker: string) => {
    const tk = ticker.toUpperCase()
    const open = comments.loadForPost(comments.readStore(FEEDBACK_FILE), `${date}_${tk}_reel`, true)
    return comments.composeRegenPrompt(date, tk, open)
  })
```

- [ ] **Step 2: Expand `studio/src/preload/index.ts`** — add to the `studio` object exposed via `contextBridge`:
```ts
  comments: {
    list: (postId: string) => ipcRenderer.invoke('comments:list', postId),
    add: (postId: string, part: string, text: string) => ipcRenderer.invoke('comments:add', postId, part, text),
    setResolved: (id: string, resolved: boolean) => ipcRenderer.invoke('comments:setResolved', id, resolved),
    delete: (id: string) => ipcRenderer.invoke('comments:delete', id),
    composePrompt: (date: string, ticker: string) => ipcRenderer.invoke('comments:composePrompt', date, ticker),
  },
```

- [ ] **Step 3: Extend `studio/src/renderer/src/global.d.ts`** — add to the `studio` interface:
```ts
      comments: {
        list(postId: string): Promise<Array<{ id: string; post_id: string; part: string; text: string; created_at: string; resolved: boolean }>>
        add(postId: string, part: string, text: string): Promise<{ id: string; post_id: string; part: string; text: string; created_at: string; resolved: boolean }>
        setResolved(id: string, resolved: boolean): Promise<{ ok: boolean }>
        delete(id: string): Promise<{ ok: boolean }>
        composePrompt(date: string, ticker: string): Promise<string>
      }
```

- [ ] **Step 4: Build to verify the IPC + types compile**

Run: `cd studio && npx electron-vite build`
Expected: main + preload + renderer build with no TypeScript errors.

- [ ] **Step 5: Smoke — confirm the app still starts**

Run: `cd studio && npm run dev` in the BACKGROUND ~30s, capture the log, confirm Electron starts with no crash / no error from `registerApi`. Kill it. (The comment IPC is exercised visually in Task 3 / by the owner; the store ops are unit-tested.)

- [ ] **Step 6: Commit**

```bash
git add studio/src/main/api.ts studio/src/preload/index.ts studio/src/renderer/src/global.d.ts
git commit -m "feat(studio): comments IPC — list/add/setResolved/delete/composePrompt"
```

---

## Task 3: `KitComments` panel + Regenerate button + `typeIntoTerminal`

**Files:**
- Modify: `studio/src/renderer/src/components/Terminal.tsx`
- Modify: `studio/src/renderer/src/components/KitView.tsx`

**Interfaces:**
- Consumes: `window.studio.comments.*` (Task 2); the new `typeIntoTerminal` export.
- Produces: the comments UI on the Kit detail; `typeIntoTerminal` (no-auto-submit terminal typing).

- [ ] **Step 1: Add `typeIntoTerminal` to `studio/src/renderer/src/components/Terminal.tsx`**

Add a module-level export next to the existing `injectToTerminal` declaration:
```tsx
export let typeIntoTerminal: (cmd: string) => void = () => {}
```
Inside the existing mount `useEffect`, right after the line that sets `injectToTerminal = …`, add:
```tsx
    typeIntoTerminal = (cmd: string) => { window.studio.term.input(cmd) }
```
(Do NOT change `injectToTerminal` — it keeps its trailing `\r`.)

- [ ] **Step 2: Add the `KitComments` component to `studio/src/renderer/src/components/KitView.tsx`**

Add the import at the top of the file (next to the existing React import):
```tsx
import { typeIntoTerminal } from './Terminal'
```
Add this component definition above `KitDetailPanel` (it uses the already-imported `useEffect`/`useState`):
```tsx
const COMMENT_PARTS = ['general', 'script', 'hook', 'data', 'takeaway', 'hero']
type Cmt = Awaited<ReturnType<typeof window.studio.comments.list>>[number]

function KitComments({ date, ticker }: { date: string; ticker: string }) {
  const postId = `${date}_${ticker}_reel`
  const [list, setList] = useState<Cmt[]>([])
  const [part, setPart] = useState('general')
  const [text, setText] = useState('')
  const [hint, setHint] = useState('')
  const refresh = () => window.studio.comments.list(postId).then(setList)
  useEffect(() => { refresh() }, [postId])
  const add = async () => {
    if (!text.trim()) return
    await window.studio.comments.add(postId, part, text.trim())
    setText(''); setHint(''); refresh()
  }
  const open = list.filter((c) => !c.resolved)
  const regenerate = async () => {
    const cmd = await window.studio.comments.composePrompt(date, ticker)
    if (!cmd) { setHint('No open comments to fold in.'); return }
    typeIntoTerminal(cmd)
    setHint('Typed into the terminal below — review and press Enter to run.')
  }
  return (
    <div>
      <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">COMMENTS</div>
      <div className="space-y-2 mb-3">
        {list.length === 0 && <div className="text-white/30 text-sm">No comments yet.</div>}
        {list.map((c) => (
          <div key={c.id} className={`border border-white/10 rounded-lg p-2 ${c.resolved ? 'opacity-40' : ''}`}>
            <div className="flex items-center gap-2 text-xs text-white/40 font-mono">
              <span className="bg-emerald-500/15 text-emerald-300 px-1.5 rounded">{c.part}</span>
              <span>{c.created_at}</span>
              <span className="ml-auto flex gap-2">
                <button className="hover:text-white" onClick={() => window.studio.comments.setResolved(c.id, !c.resolved).then(refresh)}>{c.resolved ? 'reopen' : 'resolve'}</button>
                <button className="hover:text-rose-300" onClick={() => window.studio.comments.delete(c.id).then(refresh)}>delete</button>
              </span>
            </div>
            <div className="text-sm mt-1 whitespace-pre-wrap">{c.text}</div>
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex gap-2 items-center">
          <select value={part} onChange={(e) => setPart(e.target.value)} className="bg-white/5 border border-white/10 rounded px-2 py-1 text-sm font-mono">
            {COMMENT_PARTS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <button onClick={regenerate} disabled={open.length === 0}
            className="ml-auto font-mono text-xs px-3 py-1.5 rounded bg-emerald-500/20 text-emerald-300 disabled:opacity-40">
            Regenerate with comments
          </button>
        </div>
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Add a comment…"
          className="bg-white/5 border border-white/10 rounded p-2 text-sm h-20" />
        <button onClick={add} className="self-start font-mono text-xs px-3 py-1.5 rounded bg-white/10 hover:bg-white/20">Add comment</button>
      </div>
      {hint && <div className="text-emerald-400/70 text-xs mt-2">{hint}</div>}
    </div>
  )
}
```

- [ ] **Step 3: Render `KitComments` in `KitDetailPanel`**

In `KitView.tsx`, inside `KitDetailPanel`'s returned JSX, add the comments panel as the LAST child of the outer `<div className="max-w-3xl space-y-5">` (after the hero/news sections):
```tsx
      <KitComments date={d.date} ticker={d.ticker} />
```

- [ ] **Step 4: Build to verify it compiles**

Run: `cd studio && npx electron-vite build`
Expected: renderer compiles clean, no TS errors.

- [ ] **Step 5: Smoke test (adapt — no visual inspection)**

Run: `cd studio && npm run dev` in the BACKGROUND ~30s, capture the log; confirm the renderer dev server is up + Electron starts with NO crash / NO React render error. Kill it. Paste the relevant log lines into your report. Note that the visual confirmation — opening the **Kit** tab, selecting a reel, adding a comment (it persists to `feedback/post_comments.json`), resolve/delete, and "Regenerate with comments" typing the `claude "…"` command into the terminal without auto-running — is reserved for the owner at the live window.

- [ ] **Step 6: Commit**

```bash
git add studio/src/renderer/src/components/Terminal.tsx studio/src/renderer/src/components/KitView.tsx
git commit -m "feat(studio): Kit comments panel + Regenerate-with-comments (types into terminal)"
```

---

## Self-Review

**Spec coverage:**
- §3 architecture (comments.ts + paths + IPC + KitView panel + typeIntoTerminal) → Tasks 1,2,3.
- §4 store (shared feedback file, schema, `post_id=<date>_<TICKER>_reel`, VALID_PARTS, part-agnostic reads) → Task 1 (ops) + Task 2 (handlers use `FEEDBACK_FILE` + the reel post_id).
- §5 composeRegenPrompt (claude wrapper, sanitize, "" when empty) → Task 1.
- §6 IPC (list/add/setResolved/delete/composePrompt) → Task 2.
- §7 renderer (typeIntoTerminal no-`\r`; comments list with section chip + resolve/delete; add form; Regenerate button → composePrompt → typeIntoTerminal; disabled when no open) → Task 3.
- §8 testing (Vitest pure ops + composeRegenPrompt; manual smoke) → Tasks 1,3.
- §9 decisions (comments = the editable mechanism; shared store; compose+type no auto-run; ports comments.py minus editComment) → honored.

**Placeholder scan:** All steps contain concrete code/commands. No TBD/TODO.

**Type consistency:** `Comment`/`Store` + the op signatures (Task 1) match the handler calls (Task 2) and the `global.d.ts` comment shape (Task 2) and `Cmt`/the `window.studio.comments.*` usage (Task 3). `post_id = "<date>_<TICKER>_reel"` identical in Task 2 (`comments:composePrompt`) and Task 3 (`KitComments` postId). `composeRegenPrompt(date,ticker,open)` signature identical across Tasks 1,2. `typeIntoTerminal` defined in Task 3 Terminal.tsx and consumed in Task 3 KitView.

**Known follow-ups (acceptable):** the Kit add-form parts are kit-section-aligned (script/hook/data/takeaway/hero/general); web-dashboard comments on the same reel (parts caption/audio/visual/general) still load and display read-only (loadForPost is part-agnostic) — intended per spec §4. `editComment` is intentionally not ported (YAGNI). The composed prompt assumes a PowerShell terminal (the Studio's shell) — `claude "…"` with all inner double-quotes sanitized to single, which PowerShell accepts.
