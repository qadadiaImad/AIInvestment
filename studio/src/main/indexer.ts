export type Post = {
  date: string
  ticker: string
  kind: 'reel' | 'carousel' | 'post'
  media: string[]      // media:// URLs
  poster?: string
  captionFile?: string
}
export type FileSets = { higgs: string[]; content: string[] }

const M = (rel: string) => `media://${rel}`
const EXCLUDE = /^(hero_|logo_|maya_|_)|\.json$/i

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

  const out = [...byKey.values()]
  for (const p of out) { const c = captionByDate.get(p.date); if (c) p.captionFile = c }
  return out.sort((a, b) => b.date.localeCompare(a.date) || a.ticker.localeCompare(b.ticker))
}
