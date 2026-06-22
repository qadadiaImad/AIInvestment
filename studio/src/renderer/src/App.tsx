import Terminal from './components/Terminal'
import Gallery from './components/Gallery'
import Detail from './components/Detail'
import { StudioProvider, useStudio } from './store'

function Shell() {
  const { refresh } = useStudio()
  return (
    <div className="h-screen flex flex-col">
      <header className="h-14 px-5 flex items-center justify-between border-b border-white/10">
        <span className="font-mono tracking-widest text-emerald-400">AI STACK STUDIO</span>
        <button onClick={refresh} className="font-mono text-xs bg-white/5 hover:bg-white/10 px-3 py-1 rounded">Refresh</button>
      </header>
      <div className="flex-1 flex overflow-hidden">
        <Gallery />
        <Detail />
      </div>
      <footer className="h-56 border-t border-white/10 bg-[#0A0D12]"><Terminal /></footer>
    </div>
  )
}
export default function App() { return <StudioProvider><Shell /></StudioProvider> }
