import { useEffect, useRef } from 'react'
import { Terminal as Xterm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

export let injectToTerminal: (cmd: string) => void = () => {}
export let typeIntoTerminal: (cmd: string) => void = () => {}

export default function Terminal() {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const term = new Xterm({
      fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
      theme: { background: '#0A0D12', foreground: '#E8EDF2', cursor: '#34D399' },
      cursorBlink: true
    })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.open(ref.current)
    fit.fit()
    window.studio.term.start(term.cols, term.rows)
    const off = window.studio.term.onData((d) => term.write(d))
    term.onData((d) => window.studio.term.input(d))
    injectToTerminal = (cmd: string) => { window.studio.term.input(cmd + '\r') }
    typeIntoTerminal = (cmd: string) => { window.studio.term.input(cmd) }
    const onResize = () => { fit.fit(); window.studio.term.resize(term.cols, term.rows) }
    window.addEventListener('resize', onResize)
    return () => { off(); window.removeEventListener('resize', onResize); term.dispose() }
  }, [])
  return <div ref={ref} className="h-full w-full" />
}
