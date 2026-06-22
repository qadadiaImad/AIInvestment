import Terminal from './components/Terminal'

export default function App() {
  return (
    <div className="h-screen flex flex-col">
      <header className="h-14 px-5 flex items-center border-b border-white/10 font-mono tracking-widest text-emerald-400">
        AI STACK STUDIO
      </header>
      <main className="flex-1 overflow-auto p-4 text-white/40">gallery (todo)</main>
      <footer className="h-56 border-t border-white/10 bg-[#0A0D12]">
        <Terminal />
      </footer>
    </div>
  )
}
