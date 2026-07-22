export type Post = {
  date: string
  ticker: string
  kind: 'reel' | 'carousel' | 'post'
  media: string[]      // media:// URLs
  poster?: string
  captionFile?: string
}
export type FileSets = {
  higgs: string[]
  content: string[]
  // higgs/daily/<folder>/<file> — one entry per file, path relative to higgs/daily/
  // (as produced by a recursive walk of that dir). Optional so existing callers/tests
  // that only pass {higgs, content} keep working.
  daily?: string[]
  // folder name -> parsed manifest.json fields, best-effort (fs I/O lives in api.ts;
  // this stays a plain data bag so buildIndex remains a pure function of its inputs).
  dailyManifests?: Record<string, { date?: string; ticker?: string }>
}

const M = (rel: string) => `media://${rel}`
const EXCLUDE = /^(hero_|logo_|maya_|_)|\.json$/i

// "2026-07-22_WKEY" -> { date: '2026-07-22', ticker: 'WKEY' }. Pure + exported so it's
// unit-testable without touching the filesystem. Returns null on anything that doesn't
// match the daily-pipeline convention.
export function parseDailyFolderName(name: string): { date: string; ticker: string } | null {
  const m = name.match(/^(\d{4}-\d{2}-\d{2})_([A-Za-z0-9]+)$/)
  if (!m) return null
  return { date: m[1], ticker: m[2].toUpperCase() }
}

export function buildIndex(files: FileSets): Post[] {
  const v4slides: [string, string][] = []
  const byKey = new Map<string, Post>()
  const key = (d: string, t: string) => `${d}|${t}`

  const ensure = (date: string, ticker: string, kind: Post['kind']): Post => {
    const k = key(date, ticker)
    if (!byKey.has(k)) byKey.set(k, { date, ticker, kind, media: [] })
    return byKey.get(k)!
  }

  // captions by date (sectioned files) — attached to every bundle of that date
  const captionByDate = new Map<string, string>()

  for (const f of files.higgs) {
    if (EXCLUDE.test(f)) continue
    let m: RegExpMatchArray | null
    if ((m = f.match(/^reel_([a-z]+)_(\d{4}-\d{2}-\d{2})\.mp4$/i))) {
      const p = ensure(m[2], m[1].toUpperCase(), 'reel'); p.kind = 'reel'; p.media.unshift(M(`higgs/${f}`))
    } else if ((m = f.match(/^v4_([a-z]+)_\d_[a-z]+\.png$/i))) {
      // carousel slide; ticker known, date unknown here -> attach to that ticker's newest bundle later
      v4slides.push([m[1].toUpperCase(), f])
    } else if ((m = f.match(/^reels?_(\d{4}-\d{2}-\d{2})\.txt$/i)) || (m = f.match(/^posts?_(\d{4}-\d{2}-\d{2})\.txt$/i))) {
      captionByDate.set(m[1], `media://higgs/${f}`)
    }
  }

  // content/carousel_<date>/<TK>/...
  const contentSeen = new Set<string>()
  for (const f of files.content) {
    const m = f.match(/^carousel_(\d{4}-\d{2}-\d{2})\/([A-Za-z]+)\//)
    if (!m) continue
    const tk = m[2].toUpperCase() // normalize ticker like the higgs branch; keep original case in the path
    const ck = key(m[1], tk)
    if (contentSeen.has(ck)) continue
    contentSeen.add(ck)
    const p = ensure(m[1], tk, 'carousel'); if (p.kind !== 'reel') p.kind = 'carousel'
    p.media.push(M(`content/carousel_${m[1]}/${m[2]}/slide_1.html`))
  }

  // attach v4 slides to that ticker's bundle (any date for that ticker; prefer reel bundle).
  // Orphans (ticker has NO bundle at all — e.g. a carousel-only round like the halal posts)
  // become their own 'carousel' post, dated to the newest caption sheet (v4_* files always
  // belong to the newest render round; the builder overwrites them per round).
  const newestCaptionDate = [...captionByDate.keys()].sort().pop()
  for (const [ticker, file] of v4slides.sort((a, b) => a[1].localeCompare(b[1]))) {
    const target = [...byKey.values()].filter(p => p.ticker === ticker).sort((a, b) => b.date.localeCompare(a.date))[0]
    if (target) target.media.push(M(`higgs/${file}`))
    else if (newestCaptionDate) ensure(newestCaptionDate, ticker, 'carousel').media.push(M(`higgs/${file}`))
  }

  for (const p of byKey.values()) { const c = captionByDate.get(p.date); if (c) p.captionFile = c }

  // higgs/daily/<date>_<ticker>/ — the new one-folder-per-day pipeline. Each folder yields a
  // 'reel' bundle: A/B reel video variants + carousel slides + caption, mirroring the legacy
  // reel branch above but scoped to that folder's own files only. `ensure` keys on date+ticker,
  // so a same-day/ticker legacy reel_* bundle (unlikely, but possible) merges into one entry.
  const dailyByFolder = new Map<string, string[]>() // folder name -> filenames (folder-relative)
  for (const f of files.daily ?? []) {
    const slash = f.indexOf('/')
    if (slash < 0) continue // stray file directly under daily/, not in a per-post folder
    const folder = f.slice(0, slash)
    const rest = f.slice(slash + 1)
    if (rest.includes('/')) continue // ignore anything nested deeper than one level
    if (!dailyByFolder.has(folder)) dailyByFolder.set(folder, [])
    dailyByFolder.get(folder)!.push(rest)
  }

  for (const [folder, names] of [...dailyByFolder.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    const parsed = parseDailyFolderName(folder)
    const manifest = files.dailyManifests?.[folder]
    const date = parsed?.date ?? manifest?.date
    const ticker = (parsed?.ticker ?? manifest?.ticker)?.toUpperCase()
    if (!date || !ticker) continue // can't place this bundle (bad folder name + no/broken manifest) — skip, don't crash

    const p = ensure(date, ticker, 'reel')
    p.kind = 'reel'
    const mp4A = names.find((f) => /^daily_a\.mp4$/i.test(f))
    const mp4B = names.find((f) => /^daily_b\.mp4$/i.test(f))
    if (mp4A) p.media.push(M(`higgs/daily/${folder}/${mp4A}`))
    if (mp4B) p.media.push(M(`higgs/daily/${folder}/${mp4B}`))
    const slides = names.filter((f) => /^v4_.*\.png$/i.test(f)).sort((a, b) => a.localeCompare(b))
    for (const f of slides) p.media.push(M(`higgs/daily/${folder}/${f}`))
    const caption = names.find((f) => /^caption\.txt$/i.test(f))
    if (caption) p.captionFile = M(`higgs/daily/${folder}/${caption}`)
  }

  // Re-derive from byKey (not an earlier snapshot) so daily-folder bundles `ensure`d above
  // — whether newly created or merged into an existing date+ticker entry — are included.
  return [...byKey.values()].sort((a, b) => b.date.localeCompare(a.date) || a.ticker.localeCompare(b.ticker))
}
