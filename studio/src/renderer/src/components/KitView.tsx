import { useEffect, useState } from 'react'

type KitEntry = Awaited<ReturnType<typeof window.studio.kit.list>>[number]
type KitDetail = Awaited<ReturnType<typeof window.studio.kit.get>>

const fmt = (n: any, pre = '', suf = '') =>
  n == null ? '—' : `${pre}${typeof n === 'number' ? Math.round(n * 100) / 100 : n}${suf}`

function Stat({ k, val }: { k: string; val: string }) {
  return <div><div className="text-white/40 text-xs">{k}</div><div className="text-base">{val}</div></div>
}
function Section({ title, children }: { title: string; children: any }) {
  return <div><div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">{title}</div>{children}</div>
}
function SlideCard({ label, rows }: { label: string; rows: [string, any][] }) {
  return (
    <div className="border border-white/10 rounded-lg p-3">
      <div className="font-mono text-xs text-white/50 mb-2">{label}</div>
      <div className="space-y-1">
        {rows.filter(([, v]) => v).map(([k, v]) => (
          <div key={k} className="text-sm flex gap-2">
            <span className="text-white/40 w-20 shrink-0 text-xs pt-0.5">{k}</span>
            <span className="flex-1">{v}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function KitDetailPanel({ d }: { d: KitDetail }) {
  const v = d.source?.valuation || {}
  const tag = v.fundamental_valuation
  const tagColor = tag === 'Undervalued' ? 'text-emerald-400 bg-emerald-500/15'
    : tag === 'Overvalued' ? 'text-rose-400 bg-rose-500/15' : 'text-amber-300 bg-amber-500/15'
  const s = d.slides
  return (
    <div className="max-w-3xl space-y-5">
      <div className="flex items-center gap-3">
        <span className="font-mono text-xl font-bold">{d.ticker}</span>
        <span className="text-white/40">{d.theme} · {d.date}</span>
        {tag && <span className={`ml-auto font-mono text-xs px-2 py-1 rounded ${tagColor}`}>{tag}</span>}
      </div>
      {d.source?.found && (
        <div className="grid grid-cols-3 gap-3 bg-white/5 rounded-xl p-4 font-mono text-sm">
          <Stat k="Price" val={fmt(v.price, '$')} />
          <Stat k="GF fair value" val={fmt(v.fundamental_value, '$')} />
          <Stat k="Discount" val={fmt(v.fundamental_discount_pct, '', '%')} />
          <Stat k="P/E" val={fmt(v.pe)} />
          <Stat k="P/S" val={fmt(v.ps)} />
          <Stat k="Rev growth" val={fmt(v.rev_growth_yoy, '', '%')} />
        </div>
      )}
      <Section title="SCRIPT">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{d.script || '—'}</p>
        {d.hashtags && <p className="text-emerald-400/80 text-xs mt-2 font-mono break-words">{d.hashtags}</p>}
      </Section>
      <Section title="SLIDES">
        {!s ? (
          <p className="text-white/40 text-sm">No slide kit for this date (script-only, or a non-standard builder).</p>
        ) : (
          <div className="space-y-3">
            <SlideCard label="HOOK" rows={[['Eyebrow', s.hook.kick], ['Headline', s.hook.head], ['Subhead', s.hook.sub], ['Label', s.hook.ex]]} />
            <SlideCard label="DATA" rows={[['Kicker', s.data.kick], ['Title', s.data.title], ['Caption', s.data.cap], ['Rows', s.data.rows], ['Mode', s.data.mode], ['Footer', s.data.foot]]} />
            <SlideCard label="TAKEAWAY" rows={[['Kicker', s.takeaway.kick], ['Big', `${s.takeaway.big ?? ''}${s.takeaway.unit ?? ''}`.trim() || undefined], ['Label', s.takeaway.label], ['Body', s.takeaway.body]]} />
          </div>
        )}
      </Section>
      {d.hero_prompt && <Section title="HERO PROMPT"><p className="text-sm text-white/70 whitespace-pre-wrap">{d.hero_prompt}</p></Section>}
      {d.story && <Section title="NEWS ANGLE"><p className="text-sm text-white/70">{d.story}</p></Section>}
    </div>
  )
}

export default function KitView() {
  const [entries, setEntries] = useState<KitEntry[]>([])
  const [sel, setSel] = useState<KitDetail | null>(null)
  useEffect(() => { window.studio.kit.list().then(setEntries) }, [])
  const open = (e: KitEntry) => window.studio.kit.get(e.date, e.ticker).then(setSel)
  const byDate = new Map<string, KitEntry[]>()
  for (const e of entries) (byDate.get(e.date) ?? byDate.set(e.date, []).get(e.date)!).push(e)
  return (
    <>
      <aside className="w-72 border-r border-white/10 overflow-auto p-3 shrink-0">
        {[...byDate.entries()].map(([date, es]) => (
          <div key={date} className="mb-4">
            <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">{date}</div>
            {es.map((e) => (
              <button key={e.id} onClick={() => open(e)}
                className={`w-full text-left rounded-lg border px-3 py-2 mb-1.5 ${sel?.id === e.id ? 'border-emerald-400' : 'border-white/10 hover:border-white/30'}`}>
                <div className="font-mono text-sm font-bold">{e.ticker}</div>
                <div className="text-white/40 text-xs">{e.theme}</div>
              </button>
            ))}
          </div>
        ))}
        {entries.length === 0 && <div className="text-white/30 text-xs">No reel kits found in higgs/.</div>}
      </aside>
      <section className="flex-1 overflow-auto p-5">
        {!sel ? <div className="text-white/30 text-sm">Select a planned reel to examine its kit.</div> : <KitDetailPanel d={sel} />}
      </section>
    </>
  )
}
