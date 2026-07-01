import { useEffect, useState } from 'react'
import { useStudio } from '../store'

export default function Detail() {
  const { selected, select } = useStudio()
  const [data, setData] = useState<any>(null)
  const [caption, setCaption] = useState('')
  useEffect(() => {
    if (!selected) return
    window.studio.stock.get(selected.ticker).then(setData)
    window.studio.caption.get(selected.date, selected.ticker).then(setCaption)
  }, [selected])
  if (!selected) return null
  const mp4 = selected.media.find(m => m.endsWith('.mp4'))
  const imgs = selected.media.filter(m => m.endsWith('.png'))
  const v = data?.valuation
  return (
    <aside className="w-[420px] border-l border-white/10 overflow-auto p-5 bg-[#0B0E14]">
      <div className="flex justify-between items-center mb-4">
        <span className="font-mono text-lg font-bold">{selected.ticker} <span className="text-white/40 text-sm">{selected.date}</span></span>
        <button onClick={() => select(null)} className="text-white/40 hover:text-white">✕</button>
      </div>
      {mp4 ? <video src={mp4} controls className="w-full rounded-lg mb-4" /> :
        <div className="grid grid-cols-3 gap-2 mb-4">{imgs.map((s, i) => <img key={i} src={s} className="rounded" />)}</div>}
      {v && (
        <div className="font-mono text-sm bg-white/5 rounded-lg p-4 mb-4 space-y-1">
          <div className="text-emerald-400 tracking-widest text-xs mb-2">DATA · {data.source}</div>
          <Row k="Price" val={`$${v.price}`} /><Row k="Fundamental value" val={`$${v.fundamental_value}`} />
          <Row k="Discount" val={`${v.fundamental_discount_pct}%`} /><Row k="Tag" val={v.fundamental_valuation ?? '—'} />
          {data.layer && <Row k="Layer" val={data.layer} />}
          {data.congress_trades?.length > 0 && <Row k="Congress trades" val={String(data.congress_trades.length)} />}
        </div>
      )}
      {caption && (
        <div className="mb-3">
          <div className="text-emerald-400 tracking-widest text-xs font-mono mb-2">CAPTION</div>
          <textarea defaultValue={caption} className="w-full h-40 bg-white/5 rounded p-3 text-sm" />
        </div>
      )}
      <div className="flex gap-2 font-mono text-xs">
        <button onClick={() => window.studio.copy(caption)} className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 px-3 py-2 rounded">Copy caption</button>
        {mp4 && <button onClick={() => window.studio.reveal(mp4.replace('media://', ''))} className="bg-white/5 hover:bg-white/10 px-3 py-2 rounded">Reveal file</button>}
      </div>
    </aside>
  )
}
function Row({ k, val }: { k: string; val: string }) {
  return <div className="flex justify-between"><span className="text-white/40">{k}</span><span>{val}</span></div>
}
