import { ipcMain, shell, clipboard } from 'electron'
import { readFileSync, readdirSync, existsSync } from 'fs'
import { join } from 'path'
import { HIGGS, CONTENT, DATA, FEEDBACK_FILE } from './paths'
import { buildIndex } from './indexer'
import { parseCaptions } from './captions'
import { joinStock, type Bundles } from './datajoin'
import { parseScriptSheet, parseKitCfg, parseHeroPrompt, parseHeroImage, parseStory } from './kit'
import * as comments from './comments'

function walk(dir: string, base = ''): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const rel = base ? `${base}/${e.name}` : e.name
    if (e.isDirectory()) out.push(...walk(join(dir, e.name), rel))
    else out.push(rel)
  }
  return out
}

const readJson = (f: string) => {
  try { return JSON.parse(readFileSync(join(DATA, f), 'utf-8')) } catch { return undefined }
}

const _now = () => new Date().toISOString()

export function registerApi(): void {
  ipcMain.handle('posts:list', () => {
    const higgs = existsSync(HIGGS) ? readdirSync(HIGGS) : []
    const content = walk(CONTENT)
    // higgs/daily/<date>_<ticker>/ — new one-folder-per-day pipeline (daily_A.mp4/daily_B.mp4,
    // v4_*.png carousel slides, caption.txt, manifest.json). One level of subfolders; walk()
    // returns paths already relative to dailyDir, e.g. "2026-07-22_WKEY/daily_A.mp4".
    const dailyDir = join(HIGGS, 'daily')
    const daily = existsSync(dailyDir) ? walk(dailyDir) : []
    const dailyManifests: Record<string, { date?: string; ticker?: string }> = {}
    if (existsSync(dailyDir)) {
      for (const e of readdirSync(dailyDir, { withFileTypes: true })) {
        if (!e.isDirectory()) continue
        try {
          const m = JSON.parse(readFileSync(join(dailyDir, e.name, 'manifest.json'), 'utf-8'))
          dailyManifests[e.name] = { date: m.date, ticker: m.ticker }
        } catch { /* manifest.json missing/invalid — folder-name parsing is the primary path anyway */ }
      }
    }
    return buildIndex({ higgs, content, daily, dailyManifests })
  })

  ipcMain.handle('stock:get', (_e, ticker: string) => {
    const b: Bundles = {
      site: readJson('site.json'),
      quantum: readJson('quantum.json'),
      congress: readJson('congress.json')
    }
    return joinStock(ticker, b)
  })

  ipcMain.handle('caption:get', (_e, date: string, ticker: string) => {
    for (const name of [`reels_${date}.txt`, `posts_${date}.txt`]) {
      const p = join(HIGGS, name)
      if (existsSync(p)) {
        const c = parseCaptions(readFileSync(p, 'utf-8'))
        if (c[ticker.toUpperCase()]) return c[ticker.toUpperCase()]
      }
    }
    return ''
  })

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
    // Prefer the filename the kit CFG declares (MU/IONQ); fall back to the hero_<ticker>_<date>
    // convention for reels with no CFG block (e.g. congress). Only surface it once the PNG is
    // actually on disk, so an ungenerated reel shows its prompt, not a broken <img>.
    const heroFile = (md ? parseHeroImage(md, tk) : null) || `hero_${tk.toLowerCase()}_${date}.png`
    const hero_image = existsSync(join(HIGGS, heroFile)) ? heroFile : null
    // Rendered outputs, shown once generated: slide frames (hook/data|card/takeaway — congress
    // files use the "cong" stem) and the assembled reel MP4 (this kit's date, else newest).
    const tkl = tk === 'CONGRESS' ? 'cong' : tk.toLowerCase()
    const slide_images = ['hook', 'data', 'card', 'takeaway']
      .map((k) => `reel_${tkl}_${k}.png`)
      .filter((f) => existsSync(join(HIGGS, f)))
    let reel_video: string | null = `reel_${tkl}_${date}.mp4`
    if (!existsSync(join(HIGGS, reel_video))) {
      const mp4s = readdirSync(HIGGS).filter((f) => f.startsWith(`reel_${tkl}_`) && f.endsWith('.mp4')).sort()
      reel_video = mp4s.length ? mp4s[mp4s.length - 1] : null
    }
    return {
      id: `${date}_${tk}`, date, ticker: tk,
      theme: entry?.theme ?? '', script: entry?.script ?? '', hashtags: entry?.hashtags ?? '',
      slides: md ? parseKitCfg(md, tk) : null,
      hero_prompt: md ? parseHeroPrompt(md, tk) : null,
      hero_image,
      slide_images,
      reel_video,
      story: md ? parseStory(md, tk) : null,
      source: joinStock(tk, b),
    }
  })

  ipcMain.handle('brief:list', () => {
    const dir = join(CONTENT, 'daily_brief')
    if (!existsSync(dir)) return []
    return readdirSync(dir)
      .filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d) && existsSync(join(dir, d, 'brief.md')))
      .sort()
      .reverse()
  })

  ipcMain.handle('brief:get', (_e, date: string) => {
    const day = join(CONTENT, 'daily_brief', date)
    const md = join(day, 'brief.md')
    if (!existsSync(md)) return null
    let meta: Record<string, any> | null = null
    try { meta = JSON.parse(readFileSync(join(day, 'meta.json'), 'utf-8')) } catch { /* meta optional */ }
    const chart = meta?.chart && existsSync(join(day, meta.chart))
      ? `content/daily_brief/${date}/${meta.chart}` : null
    return { date, text: readFileSync(md, 'utf-8'), meta, chart }
  })

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

  ipcMain.on('reveal', (_e, rel: string) => shell.showItemInFolder(join(HIGGS, '..', rel)))
  ipcMain.on('copy', (_e, text: string) => clipboard.writeText(text))

  const QUICK: Record<string, string> = {
    // Full refresh: fair-value backfill (GuruFocus scalar, headless) -> daily AI/quantum/news
    // (export folds in the fresh fair values) -> congress. Heavy (~tens of minutes; 128-name
    // headless fair-value pass). See scripts/refresh_all.py (--fundamentals none to skip fair value).
    'refresh-data': 'cd scripts; python refresh_all.py; cd ..',
    // Phase-2 assembler: builds every reel in reels_manifest.json via make_reel.py. Phase-1
    // (Higgsfield hero+voice via MCP) must fill the manifest URLs first; placeholder entries
    // are skipped with a notice. (Parallel variant: higgs/_workflow_make_reels.js via Workflow.)
    'make-reels': 'python higgs/make_reels_from_manifest.py',
    'build-carousel': 'python higgs/_build_v4.py',
    // Unified SlideStoryReel factory (remotion/README_FACTORY.md): props builder picks
    // the next story-worthy ticker (--auto), then Remotion renders it straight to higgs/.
    // Zero Higgsfield spend (VO-less slide mode; bubbleClips stays [] until Phase 2b).
    'render-slide-reel': 'python scripts/build_reel_props.py --auto --out remotion/src/fixtures/generated.json; cd remotion; npx remotion render SlideStoryReel ../higgs/reel_slide_latest.mp4 --props=src/fixtures/generated.json'
  }

  ipcMain.on('quick:cmd', (e, name: string) => { e.returnValue = QUICK[name] || '' })
}
