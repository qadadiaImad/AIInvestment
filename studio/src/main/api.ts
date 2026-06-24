import { ipcMain, shell, clipboard } from 'electron'
import { readFileSync, readdirSync, existsSync } from 'fs'
import { join } from 'path'
import { HIGGS, CONTENT, DATA } from './paths'
import { buildIndex } from './indexer'
import { parseCaptions } from './captions'
import { joinStock, type Bundles } from './datajoin'
import { parseScriptSheet, parseKitCfg, parseHeroPrompt, parseStory } from './kit'

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

export function registerApi(): void {
  ipcMain.handle('posts:list', () => {
    const higgs = existsSync(HIGGS) ? readdirSync(HIGGS) : []
    const content = walk(CONTENT)
    return buildIndex({ higgs, content })
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
    return {
      id: `${date}_${tk}`, date, ticker: tk,
      theme: entry?.theme ?? '', script: entry?.script ?? '', hashtags: entry?.hashtags ?? '',
      slides: md ? parseKitCfg(md, tk) : null,
      hero_prompt: md ? parseHeroPrompt(md, tk) : null,
      story: md ? parseStory(md, tk) : null,
      source: joinStock(tk, b),
    }
  })

  ipcMain.on('reveal', (_e, rel: string) => shell.showItemInFolder(join(HIGGS, '..', rel)))
  ipcMain.on('copy', (_e, text: string) => clipboard.writeText(text))

  const QUICK: Record<string, string> = {
    'refresh-data': 'cd scripts; python refresh_daily.py; cd ..',
    'make-reels': 'python higgs/make_reel.py NVDA <hero_url> <voice_url>  # edit args / see README_reels.md',
    'build-carousel': 'python higgs/_build_v4.py'
  }

  ipcMain.on('quick:cmd', (e, name: string) => { e.returnValue = QUICK[name] || '' })
}
