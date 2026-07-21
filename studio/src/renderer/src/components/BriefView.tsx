import { useEffect, useState } from 'react'
import { useStudio } from '../store'

type Brief = Awaited<ReturnType<typeof window.studio.brief.get>>

function Stat({ k, val }: { k: string; val: string }) {
  return <div><div className="text-white/40 text-xs">{k}</div><div className="text-base font-mono">{val}</div></div>
}

const pct = (v: any) => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${Math.round(v * 100) / 100}%` : '—')

export default function BriefView() {
  const { nonce } = useStudio()
  const [dates, setDates] = useState<string[]>([])
  const [sel, setSel] = useState<Brief | null>(null)
  const [copied, setCopied] = useState(false)
  // re-fetch on mount and on header Refresh, so a freshly generated brief shows up.
  useEffect(() => {
    window.studio.brief.list().then((ds) => {
      setDates(ds)
      if (ds.length && !sel) window.studio.brief.get(ds[0]).then(setSel)
      else if (sel) window.studio.brief.get(sel.date).then(setSel)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce])
  const open = (d: string) => window.studio.brief.get(d).then(setSel)
  const copy = () => {
    if (!sel) return
    window.studio.copy(sel.text)
    setCopied(true); setTimeout(() => setCopied(false), 1500)
  }
  const p = sel?.meta?.market_pulse
  return (
    <>
      <aside className="w-72 border-r border-white/10 overflow-auto p-3 shrink-0">
        <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">DAILY BRIEFS</div>
        {dates.map((d) => (
          <button key={d} onClick={() => open(d)}
            className={`w-full text-left rounded-lg border px-3 py-2 mb-1.5 font-mono text-sm ${sel?.date === d ? 'border-emerald-400' : 'border-white/10 hover:border-white/30'}`}>
            {d}
          </button>
        ))}
        {dates.length === 0 && <div className="text-white/30 text-xs">No briefs yet — run scripts/build_daily_brief.py.</div>}
      </aside>
      <section className="flex-1 overflow-auto p-5">
        {!sel ? (
          <div className="text-white/30 text-sm">Select a brief.</div>
        ) : (
          <div className="max-w-3xl space-y-5">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xl font-bold">Daily Brief · {sel.date}</span>
              {sel.meta?.rails_passed && <span className="font-mono text-xs px-2 py-1 rounded text-emerald-400 bg-emerald-500/15">rails ✓</span>}
              {sel.meta?.picks && (
                <span className="text-white/40 text-sm">AI: {sel.meta.picks.ai} · Quantum: {sel.meta.picks.quantum}</span>
              )}
              <button onClick={copy}
                className="ml-auto font-mono text-xs px-3 py-1.5 rounded bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30">
                {copied ? 'Copied ✓' : 'Copy post'}
              </button>
            </div>
            {p && (
              <div className="grid grid-cols-4 gap-3 bg-white/5 rounded-xl p-4 text-sm">
                <Stat k="S&P 500" val={pct(p.sp500?.change_pct)} />
                <Stat k="Nasdaq" val={pct(p.nasdaq?.change_pct)} />
                <Stat k="VIX" val={p.vix?.price != null ? String(p.vix.price) : '—'} />
                <Stat k="10-year" val={p.ten_year?.price != null ? `${p.ten_year.price}%` : '—'} />
              </div>
            )}
            <div>
              <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">POST</div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed bg-white/5 rounded-xl p-4">{sel.text}</p>
            </div>
            {sel.chart && (
              <div>
                <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">CHART OF THE DAY</div>
                <img src={`media://${sel.chart}`} alt="chart of the day"
                  className="rounded-xl border border-white/10 w-full max-w-sm" />
              </div>
            )}
            {sel.meta?.chart_error && (
              <div className="text-rose-300/80 text-xs font-mono">chart failed: {sel.meta.chart_error}</div>
            )}
            {sel.meta?.generated_at && (
              <div className="text-white/30 text-xs font-mono">generated {sel.meta.generated_at}</div>
            )}
          </div>
        )}
      </section>
    </>
  )
}
