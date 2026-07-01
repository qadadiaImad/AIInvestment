import { describe, it, expect } from 'vitest'
import { parseCaptions } from '../src/main/captions'

const SAMPLE = `AI STACK — NARRATED REEL KIT (2026-06-22)
=============== REEL 1 — NVDA (AI CHIPS) ===============
File: reel_nvda_2026-06-22.mp4
Caption:
Every AI chip stock looks expensive except the biggest one.
Hashtags: #nvidia #nvda
=============== REEL 2 — IONQ (QUANTUM) ===============
Caption:
Quantum gets traded like one bet.
Hashtags: #ionq`

describe('parseCaptions', () => {
  it('returns caption text per ticker', () => {
    const c = parseCaptions(SAMPLE)
    expect(c.NVDA).toContain('biggest one')
    expect(c.NVDA).toContain('#nvidia')
    expect(c.IONQ).toContain('one bet')
  })
  it('returns {} for empty input', () => {
    expect(parseCaptions('')).toEqual({})
  })
})
