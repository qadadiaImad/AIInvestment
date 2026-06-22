import { useMemo } from 'react'
import { useStudio, type Post } from '../store'

export default function Gallery() {
  const { posts, loading, refresh, selected, select, filterTicker, setFilterTicker, filterDate, setFilterDate } = useStudio()

  const tickers = Array.from(new Set(posts.map(p => p.ticker))).sort()
  const dates = useMemo(() => ['all', ...Array.from(new Set(posts.map(p => p.date)))], [posts])

  const filtered = posts.filter(p =>
    (!filterTicker || p.ticker === filterTicker) &&
    (filterDate === 'all' || p.date === filterDate)
  )

  // Group by date then ticker
  const byDate = new Map<string, Map<string, Post[]>>()
  for (const p of filtered) {
    if (!byDate.has(p.date)) byDate.set(p.date, new Map())
    const byTicker = byDate.get(p.date)!
    if (!byTicker.has(p.ticker)) byTicker.set(p.ticker, [])
    byTicker.get(p.ticker)!.push(p)
  }
  const sortedDates = Array.from(byDate.keys()).sort((a, b) => b.localeCompare(a))

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Filter bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-white/10 font-mono text-xs shrink-0">
        <select
          value={filterTicker}
          onChange={e => setFilterTicker(e.target.value)}
          className="bg-white/5 border border-white/10 rounded px-2 py-1 text-white/80 focus:outline-none"
        >
          <option value="">All tickers</option>
          {tickers.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={filterDate}
          onChange={e => setFilterDate(e.target.value)}
          className="bg-white/5 border border-white/10 rounded px-2 py-1 text-white/80 focus:outline-none"
        >
          {dates.map(d => <option key={d} value={d}>{d === 'all' ? 'All dates' : d}</option>)}
        </select>
        <button
          onClick={refresh}
          disabled={loading}
          className="ml-auto bg-emerald-500/20 hover:bg-emerald-500/30 disabled:opacity-40 text-emerald-300 px-3 py-1 rounded"
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>
        <span className="text-white/30">{filtered.length} posts</span>
      </div>

      {/* Gallery grid */}
      <div className="flex-1 overflow-auto p-4">
        {sortedDates.length === 0 && !loading && (
          <div className="text-white/30 font-mono text-sm mt-8 text-center">
            No posts found. Run "Refresh data" to populate.
          </div>
        )}
        {sortedDates.map(date => {
          const byTicker = byDate.get(date)!
          return (
            <div key={date} className="mb-8">
              <div className="font-mono text-xs text-emerald-400 tracking-widest mb-3 px-1">
                {date}
              </div>
              <div className="flex flex-wrap gap-3">
                {Array.from(byTicker.entries()).map(([ticker, group]) => (
                  <BundleCard
                    key={`${date}-${ticker}`}
                    ticker={ticker}
                    group={group}
                    isSelected={selected?.date === date && selected?.ticker === ticker}
                    onSelect={() => {
                      const p = group[0]
                      select(selected?.date === date && selected?.ticker === ticker ? null : p)
                    }}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function BundleCard({ ticker, group, isSelected, onSelect }: {
  ticker: string
  group: Post[]
  isSelected: boolean
  onSelect(): void
}) {
  const post = group[0]
  const thumb = post.poster || post.media.find(m => m.endsWith('.png')) || post.media.find(m => m.endsWith('.mp4'))
  const hasVideo = group.some(p => p.media.some(m => m.endsWith('.mp4')))
  const kinds = Array.from(new Set(group.map(p => p.kind)))

  return (
    <button
      onClick={onSelect}
      className={[
        'relative w-36 rounded-lg overflow-hidden border text-left transition-all',
        isSelected
          ? 'border-emerald-400 ring-1 ring-emerald-400/50'
          : 'border-white/10 hover:border-white/30'
      ].join(' ')}
    >
      {/* Thumbnail */}
      <div className="w-full h-24 bg-white/5 overflow-hidden">
        {thumb ? (
          <img
            src={thumb}
            alt={ticker}
            className="w-full h-full object-cover"
            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-white/20 font-mono text-lg">
            {ticker[0]}
          </div>
        )}
      </div>

      {/* Labels */}
      <div className="px-2 py-1.5 bg-[#0B0E14]">
        <div className="font-mono text-xs font-bold text-white/90 truncate">{ticker}</div>
        <div className="font-mono text-[10px] text-white/40 flex items-center gap-1 mt-0.5">
          {kinds.map(k => (
            <span key={k} className="bg-white/10 px-1 rounded">{k}</span>
          ))}
          {hasVideo && <span className="text-emerald-400">▶</span>}
        </div>
      </div>
    </button>
  )
}
