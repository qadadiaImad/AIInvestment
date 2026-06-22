import { StudioProvider, useStudio } from './store'
import Gallery from './components/Gallery'
import Detail from './components/Detail'
import Terminal from './components/Terminal'

function Shell() {
  const { selected } = useStudio()
  return (
    <div className="h-screen flex flex-col bg-[#0A0D12] text-[#E8EDF2]">
      <header className="h-14 px-5 flex items-center border-b border-white/10 font-mono tracking-widest text-emerald-400 shrink-0">
        AI STACK STUDIO
      </header>
      <main className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <Gallery />
        </div>
        {selected && <Detail />}
      </main>
      <footer className="h-56 border-t border-white/10 bg-[#0A0D12] shrink-0">
        <Terminal />
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <StudioProvider>
      <Shell />
    </StudioProvider>
  )
}
