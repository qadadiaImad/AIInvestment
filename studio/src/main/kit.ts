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
    .replace(/<br\s*\/?>/gi, ` `)
    .replace(/<[^>]+>/g, ``)
    .replace(/&mdash;/g, `—`).replace(/&rsquo;/g, `’`)
    .replace(/&ldquo;/g, `"`).replace(/&rdquo;/g, `"`)
    .replace(/&nbsp;/g, ` `).replace(/&amp;/g, `&`).replace(/&lt;/g, `<`).replace(/&gt;/g, `>`)
    .replace(/\s+/g, ` `).trim()
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

// isolate the `"TICKER":{ ... }` CFG block. Brace-match while respecting double-quoted
// string values (so a `}` inside a value — CSS, text — never truncates the block early).
function cfgBlock(md: string, ticker: string): string | null {
  const key = `"${ticker.toUpperCase()}":{`
  const start = md.indexOf(key)
  if (start < 0) return null
  const open = md.indexOf('{', start)
  if (open < 0) return null
  let depth = 0
  let inStr = false
  for (let i = open; i < md.length; i++) {
    const c = md[i]
    if (inStr) {
      if (c === '\\') i++          // skip the escaped char
      else if (c === '"') inStr = false
    } else if (c === '"') inStr = true
    else if (c === '{') depth++
    else if (c === '}') { depth--; if (depth === 0) return md.slice(open + 1, i) }
  }
  return null
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
