# Studio Kit Page (read-only pre-build examination) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A read-only "Kit" page in the AI STACK STUDIO Electron app that lets the owner examine, per planned reel, the script + slide-by-slide descriptions + the source fundamentals that drive it.

**Architecture:** A pure TypeScript parser/assembly module (`kit.ts`, TDD'd with Vitest) turns the `higgs/` planning files (`reels_<date>.txt` + `reels_<date>_kit.md`) into structured data; two IPC handlers (`kit:list`, `kit:get`) assemble it and join the live fundamentals via the existing `joinStock`; a new `KitView` renderer component + a `Posts | Kit` header toggle present it. All additive, reuses Studio helpers, no Python.

**Tech Stack:** Electron 42, electron-vite, React 19, Tailwind v4, Vitest 3, TypeScript 5 (the existing `studio/` app).

**Spec:** `docs/superpowers/specs/2026-06-24-studio-kit-page-design.md`

## Global Constraints

- All changes under `studio/`. Run tests with `cd studio && npx vitest run`. Build with `cd studio && npx electron-vite build`.
- Additive only — do NOT change the existing Posts gallery / Detail / Terminal / QuickActions behavior. The Terminal + QuickActions footer must remain.
- Parser outputs (exact shapes):
  - `parseScriptSheet(text) -> Array<{ ticker, theme, script, hashtags }>` (all strings; ticker uppercase).
  - `parseKitCfg(md, ticker) -> { hook:{kick,head,sub,ex}, data:{kick,title,cap,foot,rows,mode}, takeaway:{kick,big,unit,label,body} } | null` (each field `string | undefined`; `null` if the ticker's CFG block is absent).
  - `parseHeroPrompt(md, ticker) -> string | null`, `parseStory(md, ticker) -> string | null`.
- Slide/prompt text is returned as **plain text**: strip HTML tags (`<br>` → space, others removed) and decode the entities `&mdash; &rsquo; &ldquo; &rdquo; &amp; &lt; &gt; &nbsp;`; collapse whitespace.
- `id = "<date>_<TICKER>"`. Entries come from `reels_<date>.txt`; slides/hero/story from `reels_<date>_kit.md` (absent → `null`, page shows script-only).
- IPC: `kit:list` → `Array<{id,date,ticker,theme}>` (newest date first, then ticker); `kit:get(date,ticker)` → the assembled `KitDetail`. Preload exposes `window.studio.kit.{list,get}`.
- Read-only — no write-back (Phase 2). Source fundamentals come **live** from the bundles via `joinStock` (reuse the existing `readJson` + `joinStock` in `api.ts`).
- House colors: bg `#0A0D12`, accent emerald `#34D399`, text `#E8EDF2`. Tailwind inline (no new CSS file).

---

## Task 1: `kit.ts` pure parsers (TDD with Vitest)

**Files:**
- Create: `studio/src/main/kit.ts`
- Create: `studio/test/kit.test.ts`

**Interfaces:**
- Produces: `parseScriptSheet`, `parseKitCfg`, `parseHeroPrompt`, `parseStory` (signatures in Global Constraints). Types `ScriptEntry` and `Slides` exported.

- [ ] **Step 1: Write the failing test `studio/test/kit.test.ts`**

```ts
import { describe, it, expect } from 'vitest'
import { parseScriptSheet, parseKitCfg, parseHeroPrompt, parseStory } from '../src/main/kit'

const SCRIPT = `AI STACK — NARRATED REEL KIT (2026-06-23)
=============== REEL 1 — NBIS (AI NEOCLOUD / INFRA) ===============
File: reel_nbis_2026-06-23.mp4   | hero: GPU hall
Caption:
The market sold AI chips — but the renter got promoted.
Near 101x sales, yet near fair value.
Hashtags: #nebius #nbis #aistocks
=============== REEL 2 — QBTS (QUANTUM) ===============
Caption:
The model says quantum names aren't alike.
Hashtags: #quantum #qbts
NOTES
- ignore me`

const KIT = `# Reel KIT — 2026-06-23

## REEL 1 — NBIS (AI neocloud / infrastructure)

**Story + sources.** Nebius joined the Nasdaq-100 this week; fair value ~$278 vs ~$284.

**Hero image prompt (4:5, no text in image):**
> Editorial photo of a vast AI data-center hall at night, emerald light, no text, 4:5.

**CFG block:**
\`\`\`python
 "NBIS":{"hero":"hero_neo.png","logo":"logo_NBIS.png","ex":"AI NEOCLOUD · NASDAQ",
   "kick":"AI INFRA · PRICE vs THE MODEL",
   "head":"They sold the chips.<br><em style='color:#34D399'>who rents them out.</em>",
   "sub":"Near 101x sales &mdash; yet right on the model.",
   "data_kick":"PRICE vs FUNDAMENTAL VALUE","data_title":"Where each sits",
   "mode":"disc","rows":[("NVDA",None),("NBIS",None)],
   "data_cap":"Nebius ~2% above fair value.","data_foot":"% vs GF value · NFA",
   "tk_kick":"FAIRLY VALUED","big":"~278","unit":"","tk_label":"GF FAIR VALUE",
   "tk_body":"The most expensive-looking neocloud, near fair value.",
   "src":"site"},
\`\`\`
`

describe('parseScriptSheet', () => {
  it('returns ticker, theme, script, hashtags per reel', () => {
    const out = parseScriptSheet(SCRIPT)
    expect(out.length).toBe(2)
    const nbis = out.find(e => e.ticker === 'NBIS')!
    expect(nbis.theme).toBe('AI NEOCLOUD / INFRA')
    expect(nbis.script).toContain('renter got promoted')
    expect(nbis.script).not.toContain('Hashtags')
    expect(nbis.hashtags).toContain('#nebius')
    expect(out.find(e => e.ticker === 'QBTS')!.script).toContain("aren't alike")
  })
  it('empty input -> []', () => { expect(parseScriptSheet('')).toEqual([]) })
})

describe('parseKitCfg', () => {
  it('parses the CFG block into 3 slides, HTML/entities stripped', () => {
    const s = parseKitCfg(KIT, 'NBIS')!
    expect(s.hook.head).toContain('They sold the chips')
    expect(s.hook.head).not.toContain('<br>')
    expect(s.hook.head).not.toContain('<em')
    expect(s.hook.ex).toBe('AI NEOCLOUD · NASDAQ')
    expect(s.hook.sub).toContain('—')            // &mdash; decoded
    expect(s.data.title).toBe('Where each sits')
    expect(s.data.mode).toBe('disc')
    expect(s.data.rows).toContain('NVDA')
    expect(s.takeaway.big).toBe('~278')
    expect(s.takeaway.kick).toBe('FAIRLY VALUED')
  })
  it('missing ticker block -> null', () => { expect(parseKitCfg(KIT, 'ZZZZ')).toBeNull() })
})

describe('parseHeroPrompt / parseStory', () => {
  it('extracts hero prompt + story for a ticker', () => {
    expect(parseHeroPrompt(KIT, 'NBIS')).toContain('data-center hall')
    expect(parseStory(KIT, 'NBIS')).toContain('Nasdaq-100')
  })
  it('absent ticker -> null', () => { expect(parseHeroPrompt(KIT, 'ZZZZ')).toBeNull() })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd studio && npx vitest run test/kit.test.ts`
Expected: FAIL — cannot find module `../src/main/kit`.

- [ ] **Step 3: Implement `studio/src/main/kit.ts`**

```ts
// Pure parsers for the pre-build "Kit" page: turn higgs/ planning files into structured data.
export type ScriptEntry = { ticker: string; theme: string; script: string; hashtags: string }
export type Slides = {
  hook: { kick?: string; head?: string; sub?: string; ex?: string }
  data: { kick?: string; title?: string; cap?: string; foot?: string; rows?: string; mode?: string }
  takeaway: { kick?: string; big?: string; unit?: string; label?: string; body?: string }
}

// strip presentational HTML + decode the entities used in the kit, collapse whitespace.
function clean(s: string): string {
  return s
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/&mdash;/g, '—').replace(/&rsquo;/g, '’')
    .replace(/&ldquo;/g, '“').replace(/&rdquo;/g, '”')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ').trim()
}

export function parseScriptSheet(text: string): ScriptEntry[] {
  if (!text.trim()) return []
  const heads = text.match(/^={5,}.*$/gm) || []
  const blocks = text.split(/^={5,}.*$/m)
  const out: ScriptEntry[] = []
  for (let i = 0; i < heads.length; i++) {
    const m = heads[i].match(/—\s*([A-Za-z0-9.]{1,16})\s*\(([^)]*)\)/)
    if (!m) continue
    const ticker = m[1].toUpperCase()
    const theme = m[2].trim()
    const body = blocks[i + 1] ?? ''
    const capM = body.match(/Caption:[^\n]*\n([\s\S]*?)(?:\n\s*Hashtags:|$)/)
    const htM = body.match(/^\s*Hashtags:\s*(.*)$/m)
    const script = capM ? capM[1].trim() : ''
    const hashtags = htM ? htM[1].trim() : ''
    if (script || hashtags) out.push({ ticker, theme, script, hashtags })
  }
  return out
}

// isolate the `"TICKER":{ ... }` CFG block (values contain no braces, so the first `}` closes it).
function cfgBlock(md: string, ticker: string): string | null {
  const key = `"${ticker.toUpperCase()}":{`
  const start = md.indexOf(key)
  if (start < 0) return null
  const open = md.indexOf('{', start)
  const close = md.indexOf('}', open)
  if (open < 0 || close < 0) return null
  return md.slice(open + 1, close)
}

export function parseKitCfg(md: string, ticker: string): Slides | null {
  const block = cfgBlock(md, ticker)
  if (block === null) return null
  const field = (name: string): string | undefined => {
    const m = block.match(new RegExp(`"${name}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)"`))
    return m ? clean(m[1]) : undefined
  }
  const rowsM = block.match(/"rows"\s*:\s*(\[[^\]]*\])/)
  return {
    hook: { kick: field('kick'), head: field('head'), sub: field('sub'), ex: field('ex') },
    data: {
      kick: field('data_kick'), title: field('data_title'), cap: field('data_cap'),
      foot: field('data_foot'), rows: rowsM ? rowsM[1] : undefined, mode: field('mode'),
    },
    takeaway: {
      kick: field('tk_kick'), big: field('big'), unit: field('unit'),
      label: field('tk_label'), body: field('tk_body'),
    },
  }
}

// the kit .md has one `## REEL n — TICKER (...)` section per reel; scope to the ticker's section.
function sectionFor(md: string, ticker: string): string | null {
  for (const s of md.split(/^## /m)) {
    const first = s.split('\n')[0]
    if (new RegExp(`\\b${ticker.toUpperCase()}\\b`).test(first.toUpperCase())) return s
  }
  return null
}

export function parseHeroPrompt(md: string, ticker: string): string | null {
  const sec = sectionFor(md, ticker)
  if (!sec) return null
  const m = sec.match(/Hero image prompt[^\n]*\n((?:>\s?.*\n?)+)/i)
  if (!m) return null
  const text = m[1].replace(/^>\s?/gm, ' ')
  const out = clean(text)
  return out || null
}

export function parseStory(md: string, ticker: string): string | null {
  const sec = sectionFor(md, ticker)
  if (!sec) return null
  const m = sec.match(/\*\*Story \+ sources\.?\*\*\s*([\s\S]*?)(?:\n\s*\n|\n\*\*Hero)/i)
  if (!m) return null
  const out = clean(m[1])
  return out || null
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd studio && npx vitest run test/kit.test.ts`
Expected: PASS (6 tests).

- [ ] **Step 5: Run the full Studio vitest suite (no regressions)**

Run: `cd studio && npx vitest run`
Expected: all existing tests + the 6 new ones pass.

- [ ] **Step 6: Commit**

```bash
git add studio/src/main/kit.ts studio/test/kit.test.ts
git commit -m "feat(studio): kit parsers (script/CFG-slides/hero/story), TDD"
```

---

## Task 2: IPC — `kit:list` / `kit:get`

**Files:**
- Modify: `studio/src/main/api.ts`
- Modify: `studio/src/preload/index.ts`
- Modify: `studio/src/renderer/src/global.d.ts`

**Interfaces:**
- Consumes: `kit.ts` parsers (Task 1); the existing `readJson`, `joinStock`, `HIGGS` in `api.ts`.
- Produces: IPC `kit:list` / `kit:get`; `window.studio.kit.{list,get}`. `KitDetail` shape (typed in global.d.ts).

- [ ] **Step 1: Add imports + the two handlers to `studio/src/main/api.ts`**

Add to the import block at the top (alongside the existing `import { joinStock, type Bundles } from './datajoin'`):
```ts
import { parseScriptSheet, parseKitCfg, parseHeroPrompt, parseStory } from './kit'
```
Add `readFileSync` to the existing `fs` import (the line `import { readFileSync, readdirSync, existsSync } from 'fs'` already includes it — leave as is). Then, inside `registerApi()`, after the existing `caption:get` handler, add:
```ts
  ipcMain.handle('kit:list', () => {
    const files = existsSync(HIGGS) ? readdirSync(HIGGS) : []
    const dates = files
      .map((f) => f.match(/^reels_(\d{4}-\d{2}-\d{2})\.txt$/)?.[1])
      .filter((d): d is string => !!d)
    const out: Array<{ id: string; date: string; ticker: string; theme: string }> = []
    for (const date of dates) {
      const text = readFileSync(join(HIGGS, `reels_${date}.txt`), 'utf-8')
      for (const e of parseScriptSheet(text)) {
        out.push({ id: `${date}_${e.ticker}`, date, ticker: e.ticker, theme: e.theme })
      }
    }
    out.sort((a, b) => b.date.localeCompare(a.date) || a.ticker.localeCompare(b.ticker))
    return out
  })

  ipcMain.handle('kit:get', (_e, date: string, ticker: string) => {
    const tk = ticker.toUpperCase()
    const txtPath = join(HIGGS, `reels_${date}.txt`)
    const entry = existsSync(txtPath)
      ? parseScriptSheet(readFileSync(txtPath, 'utf-8')).find((e) => e.ticker === tk)
      : undefined
    const mdPath = join(HIGGS, `reels_${date}_kit.md`)
    const md = existsSync(mdPath) ? readFileSync(mdPath, 'utf-8') : ''
    const b: Bundles = {
      site: readJson('site.json'), quantum: readJson('quantum.json'), congress: readJson('congress.json'),
    }
    return {
      id: `${date}_${tk}`, date, ticker: tk,
      theme: entry?.theme ?? '', script: entry?.script ?? '', hashtags: entry?.hashtags ?? '',
      slides: md ? parseKitCfg(md, tk) : null,
      hero_prompt: md ? parseHeroPrompt(md, tk) : null,
      story: md ? parseStory(md, tk) : null,
      source: joinStock(tk, b),
    }
  })
```

- [ ] **Step 2: Expand `studio/src/preload/index.ts`** — add to the `studio` object exposed via `contextBridge`:
```ts
  kit: {
    list: () => ipcRenderer.invoke('kit:list'),
    get: (date: string, ticker: string) => ipcRenderer.invoke('kit:get', date, ticker),
  },
```

- [ ] **Step 3: Extend `studio/src/renderer/src/global.d.ts`** — add to the `studio` interface:
```ts
      kit: {
        list(): Promise<Array<{ id: string; date: string; ticker: string; theme: string }>>
        get(date: string, ticker: string): Promise<{
          id: string; date: string; ticker: string; theme: string
          script: string; hashtags: string
          slides: {
            hook: { kick?: string; head?: string; sub?: string; ex?: string }
            data: { kick?: string; title?: string; cap?: string; foot?: string; rows?: string; mode?: string }
            takeaway: { kick?: string; big?: string; unit?: string; label?: string; body?: string }
          } | null
          hero_prompt: string | null
          story: string | null
          source: { found: boolean; source?: string; layer?: string; valuation?: any; congress_trades: any[] }
        }>
      }
```

- [ ] **Step 4: Build to verify the IPC + types compile**

Run: `cd studio && npx electron-vite build`
Expected: main + preload + renderer build with no TypeScript errors.

- [ ] **Step 5: Smoke — confirm `kit:list` returns real reels**

Run: `cd studio && npm run dev` in the BACKGROUND ~30s, capture the log, confirm Electron starts with no crash / no error from `registerApi`. Then kill it. (The `kit:list`/`kit:get` data is exercised visually in Task 3 / by the owner; the parsers are already unit-tested against the kit shape. The real `higgs/reels_2026-06-23.txt` + `reels_2026-06-23_kit.md` exist, so the handlers have real data.)

- [ ] **Step 6: Commit**

```bash
git add studio/src/main/api.ts studio/src/preload/index.ts studio/src/renderer/src/global.d.ts
git commit -m "feat(studio): kit IPC — kit.list / kit.get (joins live fundamentals)"
```

---

## Task 3: `KitView` renderer + `Posts | Kit` toggle

**Files:**
- Create: `studio/src/renderer/src/components/KitView.tsx`
- Modify: `studio/src/renderer/src/App.tsx`

**Interfaces:**
- Consumes: `window.studio.kit.{list,get}` (Task 2).
- Produces: the Kit view + the header nav toggle. No exported JS interface.

- [ ] **Step 1: Create `studio/src/renderer/src/components/KitView.tsx`**

```tsx
import { useEffect, useState } from 'react'

type KitEntry = Awaited<ReturnType<typeof window.studio.kit.list>>[number]
type KitDetail = Awaited<ReturnType<typeof window.studio.kit.get>>

const fmt = (n: any, pre = '', suf = '') =>
  n == null ? '—' : `${pre}${typeof n === 'number' ? Math.round(n * 100) / 100 : n}${suf}`

function Stat({ k, val }: { k: string; val: string }) {
  return <div><div className="text-white/40 text-xs">{k}</div><div className="text-base">{val}</div></div>
}
function Section({ title, children }: { title: string; children: any }) {
  return <div><div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">{title}</div>{children}</div>
}
function SlideCard({ label, rows }: { label: string; rows: [string, any][] }) {
  return (
    <div className="border border-white/10 rounded-lg p-3">
      <div className="font-mono text-xs text-white/50 mb-2">{label}</div>
      <div className="space-y-1">
        {rows.filter(([, v]) => v).map(([k, v]) => (
          <div key={k} className="text-sm flex gap-2">
            <span className="text-white/40 w-20 shrink-0 text-xs pt-0.5">{k}</span>
            <span className="flex-1">{v}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function KitDetailPanel({ d }: { d: KitDetail }) {
  const v = d.source?.valuation || {}
  const tag = v.fundamental_valuation
  const tagColor = tag === 'Undervalued' ? 'text-emerald-400 bg-emerald-500/15'
    : tag === 'Overvalued' ? 'text-rose-400 bg-rose-500/15' : 'text-amber-300 bg-amber-500/15'
  const s = d.slides
  return (
    <div className="max-w-3xl space-y-5">
      <div className="flex items-center gap-3">
        <span className="font-mono text-xl font-bold">{d.ticker}</span>
        <span className="text-white/40">{d.theme} · {d.date}</span>
        {tag && <span className={`ml-auto font-mono text-xs px-2 py-1 rounded ${tagColor}`}>{tag}</span>}
      </div>
      {d.source?.found && (
        <div className="grid grid-cols-3 gap-3 bg-white/5 rounded-xl p-4 font-mono text-sm">
          <Stat k="Price" val={fmt(v.price, '$')} />
          <Stat k="GF fair value" val={fmt(v.fundamental_value, '$')} />
          <Stat k="Discount" val={fmt(v.fundamental_discount_pct, '', '%')} />
          <Stat k="P/E" val={fmt(v.pe)} />
          <Stat k="P/S" val={fmt(v.ps)} />
          <Stat k="Rev growth" val={fmt(v.rev_growth_yoy, '', '%')} />
        </div>
      )}
      <Section title="SCRIPT">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{d.script || '—'}</p>
        {d.hashtags && <p className="text-emerald-400/80 text-xs mt-2 font-mono break-words">{d.hashtags}</p>}
      </Section>
      <Section title="SLIDES">
        {!s ? (
          <p className="text-white/40 text-sm">No slide kit for this date (script-only, or a non-standard builder).</p>
        ) : (
          <div className="space-y-3">
            <SlideCard label="HOOK" rows={[['Eyebrow', s.hook.kick], ['Headline', s.hook.head], ['Subhead', s.hook.sub], ['Label', s.hook.ex]]} />
            <SlideCard label="DATA" rows={[['Kicker', s.data.kick], ['Title', s.data.title], ['Caption', s.data.cap], ['Rows', s.data.rows], ['Mode', s.data.mode], ['Footer', s.data.foot]]} />
            <SlideCard label="TAKEAWAY" rows={[['Kicker', s.takeaway.kick], ['Big', `${s.takeaway.big ?? ''}${s.takeaway.unit ?? ''}`.trim() || undefined], ['Label', s.takeaway.label], ['Body', s.takeaway.body]]} />
          </div>
        )}
      </Section>
      {d.hero_prompt && <Section title="HERO PROMPT"><p className="text-sm text-white/70 whitespace-pre-wrap">{d.hero_prompt}</p></Section>}
      {d.story && <Section title="NEWS ANGLE"><p className="text-sm text-white/70">{d.story}</p></Section>}
    </div>
  )
}

export default function KitView() {
  const [entries, setEntries] = useState<KitEntry[]>([])
  const [sel, setSel] = useState<KitDetail | null>(null)
  useEffect(() => { window.studio.kit.list().then(setEntries) }, [])
  const open = (e: KitEntry) => window.studio.kit.get(e.date, e.ticker).then(setSel)
  const byDate = new Map<string, KitEntry[]>()
  for (const e of entries) (byDate.get(e.date) ?? byDate.set(e.date, []).get(e.date)!).push(e)
  return (
    <>
      <aside className="w-72 border-r border-white/10 overflow-auto p-3 shrink-0">
        {[...byDate.entries()].map(([date, es]) => (
          <div key={date} className="mb-4">
            <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">{date}</div>
            {es.map((e) => (
              <button key={e.id} onClick={() => open(e)}
                className={`w-full text-left rounded-lg border px-3 py-2 mb-1.5 ${sel?.id === e.id ? 'border-emerald-400' : 'border-white/10 hover:border-white/30'}`}>
                <div className="font-mono text-sm font-bold">{e.ticker}</div>
                <div className="text-white/40 text-xs">{e.theme}</div>
              </button>
            ))}
          </div>
        ))}
        {entries.length === 0 && <div className="text-white/30 text-xs">No reel kits found in higgs/.</div>}
      </aside>
      <section className="flex-1 overflow-auto p-5">
        {!sel ? <div className="text-white/30 text-sm">Select a planned reel to examine its kit.</div> : <KitDetailPanel d={sel} />}
      </section>
    </>
  )
}
```

- [ ] **Step 2: Wire the `Posts | Kit` toggle into `studio/src/renderer/src/App.tsx`**

Open `studio/src/renderer/src/App.tsx` and apply these three edits, preserving everything else (the Refresh button, Gallery, Detail, the QuickActions + Terminal footer):

(a) Add imports at the top:
```tsx
import { useState } from 'react'
import KitView from './components/KitView'
```
(b) Inside the `Shell` component, add view state as the first line of the function body:
```tsx
  const [view, setView] = useState<'posts' | 'kit'>('posts')
```
(c) In the `<header>`, add a nav toggle between the `AI STACK STUDIO` brand span and the Refresh button:
```tsx
        <nav className="flex gap-1.5 font-mono text-xs">
          <button onClick={() => setView('posts')}
            className={`px-3 py-1 rounded ${view === 'posts' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 hover:bg-white/10'}`}>Posts</button>
          <button onClick={() => setView('kit')}
            className={`px-3 py-1 rounded ${view === 'kit' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 hover:bg-white/10'}`}>Kit</button>
        </nav>
```
(d) Replace the middle row `<div className="flex-1 flex overflow-hidden"><Gallery /><Detail /></div>` with a conditional on `view`:
```tsx
      <div className="flex-1 flex overflow-hidden">
        {view === 'posts' ? <><Gallery /><Detail /></> : <KitView />}
      </div>
```

- [ ] **Step 3: Build to verify it compiles**

Run: `cd studio && npx electron-vite build`
Expected: renderer compiles clean, no TS errors.

- [ ] **Step 4: Smoke test (adapt — no visual inspection)**

Run: `cd studio && npm run dev` in the BACKGROUND ~30s, capture the log; confirm the renderer dev server is up + Electron starts with no crash / no React render error. Kill it. Paste the relevant log lines into your report. Note that the visual confirmation — clicking **Kit**, seeing the planned reels (NBIS/QBTS/CONGRESS for 2026-06-23), clicking one to see the valuation badge + source numbers + script + 3 slide cards, and the Posts/Kit toggle — is reserved for the owner at the live window.

- [ ] **Step 5: Commit**

```bash
git add studio/src/renderer/src/components/KitView.tsx studio/src/renderer/src/App.tsx
git commit -m "feat(studio): Kit view — pre-build script/slides/source-data, Posts|Kit toggle"
```

---

## Self-Review

**Spec coverage:**
- §3 architecture (kit.ts + IPC + KitView, reuse joinStock/readJson) → Tasks 1,2,3.
- §4 data sources / `id = <date>_<TICKER>` / graceful when `_kit.md` absent → Task 2 (`kit:list`/`kit:get` use `reels_<date>.txt`; `md ? … : null`).
- §5 pure parsers (parseScriptSheet/parseKitCfg/parseHeroPrompt/parseStory; HTML+entity stripping) → Task 1.
- §6 assembly + IPC (KitDetail shape) → Task 2.
- §7 renderer (Posts|Kit toggle; list by date; valuation badge; highlighted source-data card; script; 3 slide cards; hero/news; slides-null fallback) → Task 3.
- §8 testing (Vitest pure parsers; manual smoke) → Tasks 1,3.
- §9 decisions (read-only; plain-text slides; live source data) → honored.

**Placeholder scan:** All steps contain concrete code/commands. No TBD/TODO.

**Type consistency:** `ScriptEntry`/`Slides` shapes (Task 1) match the `kit:get` assembly (Task 2) and the `KitDetail` type in global.d.ts (Task 2) and the `KitView` consumption (Task 3). `id = "<date>_<TICKER>"` identical across Tasks 2,3. Parser names `parseScriptSheet`/`parseKitCfg`/`parseHeroPrompt`/`parseStory` identical across Tasks 1,2.

**Known follow-ups (acceptable):** the congress reel uses a non-CFG builder, so `parseKitCfg('CONGRESS')` returns `null` → its entry shows script + source + "no slide kit" (the congress card details are in the story prose). 2026-06-22 has a `.txt` but no `_kit.md` → script-only. Both are the intended graceful-degrade per spec §4. The slide `rows` is shown as its raw `[("NVDA",None),…]` string (the model fills actual numbers at build time) — intentional for a pre-build examine view.
