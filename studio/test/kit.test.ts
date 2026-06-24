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
