import { typeIntoTerminal } from './Terminal'
const ACTIONS = [
  { name: 'refresh-data', label: 'Refresh data' },
  { name: 'build-carousel', label: 'Build carousel' },
  { name: 'make-reels', label: 'Make reels' }
]
export default function QuickActions() {
  // Type the command into the terminal WITHOUT auto-running it (no trailing Enter), so the
  // owner reviews/edits before pressing Enter — per the spec ("stays in control rather than
  // firing hidden jobs"). Matters especially now that Refresh data is a long, gated job and
  // Make reels carries placeholder args that must be filled in first.
  return (
    <div className="flex gap-2 px-3 py-2 border-b border-white/10 font-mono text-xs">
      {ACTIONS.map(a => (
        <button key={a.name} onClick={() => typeIntoTerminal(window.studio.quickCmd(a.name))}
          className="bg-white/5 hover:bg-emerald-500/20 px-3 py-1 rounded">{a.label}</button>
      ))}
      <span className="ml-auto text-white/30 self-center">click → review → <b>Enter</b> to run ↓</span>
    </div>
  )
}
