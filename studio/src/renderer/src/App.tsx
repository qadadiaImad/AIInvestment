import { useState } from 'react'
import Terminal from './components/Terminal'
import Gallery from './components/Gallery'
import Detail from './components/Detail'
import QuickActions from './components/QuickActions'
import KitView from './components/KitView'
import { StudioProvider, useStudio } from './store'

function Shell() {
  const [view, setView] = useState<'posts' | 'kit'>('posts')
  const { refresh } = useStudio()
  return (
    <div className="h-screen flex flex-col">
      <header className="h-14 px-5 flex items-center justify-between border-b border-white/10">
        <span className="font-mono tracking-widest text-emerald-400">AI STACK STUDIO</span>
        <nav className="flex gap-1.5 font-mono text-xs">
          <button onClick={() => setView('posts')}
            className={`px-3 py-1 rounded ${view === 'posts' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 hover:bg-white/10'}`}>Posts</button>
          <button onClick={() => setView('kit')}
            className={`px-3 py-1 rounded ${view === 'kit' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 hover:bg-white/10'}`}>Kit</button>
        </nav>
        <button onClick={refresh} className="font-mono text-xs bg-white/5 hover:bg-white/10 px-3 py-1 rounded">Refresh</button>
      </header>
      <div className="flex-1 flex overflow-hidden">
        {view === 'posts' ? <><Gallery /><Detail /></> : <KitView />}
      </div>
      <footer className="h-64 border-t border-white/10 bg-[#0A0D12] flex flex-col">
        <QuickActions />
        <div className="flex-1 overflow-hidden"><Terminal /></div>
      </footer>
    </div>
  )
}
export default function App() { return <StudioProvider><Shell /></StudioProvider> }
