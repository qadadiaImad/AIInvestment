import { useMemo, useState } from 'react'
import { useStudio } from '../store'

export default function Gallery() {
  const { posts, select } = useStudio()
  const [day, setDay] = useState('all'); const [tk, setTk] = useState('all')
  const days = useMemo(() => ['all', ...Array.from(new Set(posts.map(p => p.date)))], [posts])
  const tks = useMemo(() => ['all', ...Array.from(new Set(posts.map(p => p.ticker)))], [posts])
  const shown = posts.filter(p => (day === 'all' || p.date === day) && (tk === 'all' || p.ticker === tk))
  const grouped = useMemo(() => {
    const m = new Map<string, typeof shown>()
    for (const p of shown) { (m.get(p.date) ?? m.set(p.date, []).get(p.date)!).push(p) }
    return [...m.entries()]
  }, [shown])

  return (
    <div className="flex-1 overflow-auto p-5">
      <div className="flex gap-3 mb-5 font-mono text-sm">
        <select value={day} onChange={e => setDay(e.target.value)} className="bg-white/5 px-3 py-1 rounded">{days.map(d => <option key={d}>{d}</option>)}</select>
        <select value={tk} onChange={e => setTk(e.target.value)} className="bg-white/5 px-3 py-1 rounded">{tks.map(t => <option key={t}>{t}</option>)}</select>
      </div>
      {grouped.map(([date, items]) => (
        <div key={date} className="mb-7">
          <div className="font-mono text-xs tracking-widest text-emerald-400 mb-3">{date}</div>
          <div className="grid grid-cols-4 gap-4">
            {items.map((p, i) => {
              const mp4 = p.media.find(m => m.endsWith('.mp4'))
              const img = p.media.find(m => m.endsWith('.png'))
              return (
                <button key={i} onClick={() => select(p)} className="text-left rounded-xl overflow-hidden border border-white/10 hover:border-emerald-400/60 bg-white/5">
                  <div className="aspect-[4/5] bg-black/40 flex items-center justify-center">
                    {mp4 ? <video src={mp4} muted className="h-full w-full object-cover" /> :
                     img ? <img src={img} className="h-full w-full object-cover" /> :
                     <span className="text-white/30 text-xs">{p.kind}</span>}
                  </div>
                  <div className="px-3 py-2 font-mono text-sm flex justify-between">
                    <span className="font-bold">{p.ticker}</span><span className="text-white/40">{p.kind}</span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
