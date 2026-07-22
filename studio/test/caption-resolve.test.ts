import { describe, it, expect } from 'vitest'
import { resolveCaption } from '../src/main/caption-resolve'

const norm = (p: string) => p.replace(/\\/g, '/')

describe('resolveCaption', () => {
  it('reads higgs/daily/<date>_<TICKER>/caption.txt when it exists (C1: daily-pipeline posts)', () => {
    const deps = {
      exists: (p: string) => norm(p).endsWith('daily/2026-07-22_WKEY/caption.txt'),
      readFile: (p: string) => {
        if (norm(p).endsWith('daily/2026-07-22_WKEY/caption.txt')) return 'WKEY caption text'
        throw new Error(`unexpected read: ${p}`)
      }
    }
    expect(resolveCaption('2026-07-22', 'wkey', deps)).toBe('WKEY caption text')
  })

  it('uppercases the ticker when building the daily-folder path (checked first, before any legacy sheet)', () => {
    const checkedPaths: string[] = []
    const deps = {
      exists: (p: string) => {
        checkedPaths.push(p)
        return false
      },
      readFile: () => ''
    }
    resolveCaption('2026-07-22', 'wkey', deps)
    expect(norm(checkedPaths[0])).toMatch(/higgs\/daily\/2026-07-22_WKEY\/caption\.txt$/)
  })

  it('falls back to the legacy reels_<date>.txt sheet when no daily caption.txt exists', () => {
    const sheet =
      '=============== REEL 1 — NVDA (AI CHIPS) ===============\nCaption:\nHello NVDA\nHashtags: #nvda'
    const deps = {
      exists: (p: string) => norm(p).endsWith('reels_2026-06-22.txt'),
      readFile: () => sheet
    }
    expect(resolveCaption('2026-06-22', 'NVDA', deps)).toContain('Hello NVDA')
  })

  it('falls back to posts_<date>.txt when reels_<date>.txt is absent', () => {
    const sheet =
      '=============== REEL 1 — GEV (ENERGY) ===============\nCaption:\nHello GEV\nHashtags: #gev'
    const deps = {
      exists: (p: string) => norm(p).endsWith('posts_2026-06-22.txt'),
      readFile: () => sheet
    }
    expect(resolveCaption('2026-06-22', 'GEV', deps)).toContain('Hello GEV')
  })

  it('daily-folder caption.txt takes priority over a same-date legacy sheet', () => {
    const sheet =
      '=============== REEL 1 — WKEY (ENERGY) ===============\nCaption:\nLegacy caption\nHashtags: #wkey'
    const deps = {
      exists: (p: string) =>
        norm(p).endsWith('daily/2026-07-22_WKEY/caption.txt') || norm(p).endsWith('reels_2026-07-22.txt'),
      readFile: (p: string) =>
        norm(p).endsWith('daily/2026-07-22_WKEY/caption.txt') ? 'Daily caption' : sheet
    }
    expect(resolveCaption('2026-07-22', 'WKEY', deps)).toBe('Daily caption')
  })

  it('returns empty string when nothing matches', () => {
    const deps = { exists: () => false, readFile: () => '' }
    expect(resolveCaption('2026-06-22', 'ZZZZ', deps)).toBe('')
  })

  it('an empty daily caption.txt falls through to the legacy sheets instead of returning empty', () => {
    const sheet =
      '=============== REEL 1 — WKEY (ENERGY) ===============\nCaption:\nLegacy caption\nHashtags: #wkey'
    const deps = {
      exists: (p: string) =>
        norm(p).endsWith('daily/2026-07-22_WKEY/caption.txt') || norm(p).endsWith('reels_2026-07-22.txt'),
      readFile: (p: string) => (norm(p).endsWith('daily/2026-07-22_WKEY/caption.txt') ? '' : sheet)
    }
    expect(resolveCaption('2026-07-22', 'WKEY', deps)).toContain('Legacy caption')
  })
})
