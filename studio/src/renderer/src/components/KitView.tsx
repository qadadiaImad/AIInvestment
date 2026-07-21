import { useEffect, useState } from 'react'
import { typeIntoTerminal } from './Terminal'
import { useStudio } from '../store'

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

const COMMENT_PARTS = ['general', 'script', 'hook', 'data', 'takeaway', 'hero']
type Cmt = Awaited<ReturnType<typeof window.studio.comments.list>>[number]

function KitComments({ date, ticker }: { date: string; ticker: string }) {
  const postId = `${date}_${ticker}_reel`
  const [list, setList] = useState<Cmt[]>([])
  const [part, setPart] = useState('general')
  const [text, setText] = useState('')
  const [hint, setHint] = useState('')
  const refresh = () => window.studio.comments.list(postId).then(setList)
  useEffect(() => { refresh() }, [postId])
  const add = async () => {
    if (!text.trim()) return
    await window.studio.comments.add(postId, part, text.trim())
    setText(''); setHint(''); refresh()
  }
  const open = list.filter((c) => !c.resolved)
  const regenerate = async () => {
    const cmd = await window.studio.comments.composePrompt(date, ticker)
    if (!cmd) { setHint('No open comments to fold in.'); return }
    typeIntoTerminal(cmd)
    setHint('Typed into the terminal below — review and press Enter to run.')
  }
  return (
    <div>
      <div className="font-mono text-xs tracking-widest text-emerald-400 mb-2">COMMENTS</div>
      <div className="space-y-2 mb-3">
        {list.length === 0 && <div className="text-white/30 text-sm">No comments yet.</div>}
        {list.map((c) => (
          <div key={c.id} className={`border border-white/10 rounded-lg p-2 ${c.resolved ? 'opacity-40' : ''}`}>
            <div className="flex items-center gap-2 text-xs text-white/40 font-mono">
              <span className="bg-emerald-500/15 text-emerald-300 px-1.5 rounded">{c.part}</span>
              <span>{c.created_at}</span>
              <span className="ml-auto flex gap-2">
                <button className="hover:text-white" onClick={() => window.studio.comments.setResolved(c.id, !c.resolved).then(refresh)}>{c.resolved ? 'reopen' : 'resolve'}</button>
                <button className="hover:text-rose-300" onClick={() => window.studio.comments.delete(c.id).then(refresh)}>delete</button>
              </span>
            </div>
            <div className="text-sm mt-1 whitespace-pre-wrap">{c.text}</div>
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex gap-2 items-center">
          <select value={part} onChange={(e) => setPart(e.target.value)} className="bg-white/5 border border-white/10 rounded px-2 py-1 text-sm font-mono">
            {COMMENT_PARTS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <button onClick={regenerate} disabled={open.length === 0}
            className="ml-auto font-mono text-xs px-3 py-1.5 rounded bg-emerald-500/20 text-emerald-300 disabled:opacity-40">
            Regenerate with comments
          </button>
        </div>
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Add a comment…"
          className="bg-white/5 border border-white/10 rounded p-2 text-sm h-20" />
        <button onClick={add} className="self-start font-mono text-xs px-3 py-1.5 rounded bg-white/10 hover:bg-white/20">Add comment</button>
      </div>
      {hint && <div className="text-emerald-400/70 text-xs mt-2">{hint}</div>}
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
      {d.slide_images.length > 0 && (
        <Section title="RENDERED SLIDES">
          <div className="flex gap-3 overflow-x-auto pb-2">
            {d.slide_images.map((f) => (
              <img key={f} src={`media://higgs/${f}`} alt={f}
                className="rounded-lg border border-white/10 h-72 shrink-0 bg-black/40" />
            ))}
          </div>
        </Section>
      )}
      {d.reel_video && (
        <Section title="REEL">
          <video controls preload="metadata" src={`media://higgs/${d.reel_video}`}
            className="rounded-xl border border-white/10 w-full max-w-xs" />
          <div className="text-white/40 text-xs mt-1 font-mono">{d.reel_video}</div>
        </Section>
      )}
      {d.hero_image && (
        <Section title="HERO IMAGE">
          <img src={`media://higgs/${d.hero_image}`} alt={`${d.ticker} hero`}
            className="rounded-xl border border-white/10 w-full max-w-sm" />
        </Section>
      )}
      {d.hero_prompt && <Section title="HERO PROMPT"><p className="text-sm text-white/70 whitespace-pre-wrap">{d.hero_prompt}</p></Section>}
      {d.story && <Section title="NEWS ANGLE"><p className="text-sm text-white/70">{d.story}</p></Section>}
      <KitComments date={d.date} ticker={d.ticker} />
    </div>
  )
}

export default function KitView() {
  const { nonce } = useStudio()
  const [entries, setEntries] = useState<KitEntry[]>([])
  const [sel, setSel] = useState<KitDetail | null>(null)
  // re-fetch on mount AND whenever the header Refresh button bumps the nonce,
  // so newly generated kits (e.g. reels_2026-06-27.*) show without an app restart.
  useEffect(() => { window.studio.kit.list().then(setEntries) }, [nonce])
  // Also re-pull the currently-open kit on Refresh so its fundamentals/slides reflect
  // freshly-written data. `sel` is intentionally excluded from deps — we only want this
  // to fire on nonce; opening a kit already fetches via `open`.
  useEffect(() => {
    if (sel) window.studio.kit.get(sel.date, sel.ticker).then(setSel)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce])
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
