import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import { HIGGS } from './paths'
import { parseCaptions } from './captions'

// Deps injected so this is unit-testable without touching the real filesystem
// (see studio/test/caption-resolve.test.ts) -- default to the real fs at call sites.
export type CaptionFsDeps = { exists: (p: string) => boolean; readFile: (p: string) => string }
const REAL_FS_DEPS: CaptionFsDeps = { exists: existsSync, readFile: (p) => readFileSync(p, 'utf-8') }

// Resolves the caption text for a given (date, ticker) post. Checks the new
// one-folder-per-day pipeline first (higgs/daily/<date>_<TICKER>/caption.txt,
// written by daily_post.py -- see the C1 review fix), then falls back to the
// legacy dated caption sheets (reels_<date>.txt / posts_<date>.txt) that
// older reel/carousel rounds still use. Empty string if nothing matches
// either shape.
export function resolveCaption(
  date: string,
  ticker: string,
  deps: CaptionFsDeps = REAL_FS_DEPS
): string {
  const tk = ticker.toUpperCase()
  const dailyCaption = join(HIGGS, 'daily', `${date}_${tk}`, 'caption.txt')
  if (deps.exists(dailyCaption)) {
    try {
      const text = deps.readFile(dailyCaption)
      if (text) return text
    } catch { /* fall through to the legacy sheets below */ }
  }
  for (const name of [`reels_${date}.txt`, `posts_${date}.txt`]) {
    const p = join(HIGGS, name)
    if (deps.exists(p)) {
      const c = parseCaptions(deps.readFile(p))
      if (c[tk]) return c[tk]
    }
  }
  return ''
}
