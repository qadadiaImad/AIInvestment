import { injectToTerminal } from './Terminal'
const ACTIONS = [
  { name: 'refresh-data', label: 'Refresh data' },
  { name: 'build-carousel', label: 'Build carousel' },
  { name: 'make-reels', label: 'Make reels' }
]
export default function QuickActions() {
  return (
    <div className="flex gap-2 px-3 py-2 border-b border-white/10 font-mono text-xs">
      {ACTIONS.map(a => (
        <button key={a.name} onClick={() => injectToTerminal(window.studio.quickCmd(a.name))}
          className="bg-white/5 hover:bg-emerald-500/20 px-3 py-1 rounded">{a.label}</button>
      ))}
      <span className="ml-auto text-white/30 self-center">type <b>claude</b> to chat ↓</span>
    </div>
  )
}
