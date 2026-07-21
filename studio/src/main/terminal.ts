import { ipcMain, WebContents } from 'electron'
import * as pty from 'node-pty'
import { join } from 'path'

const REPO_ROOT = join(__dirname, '..', '..', '..') // studio/out/main -> repo root
const SHELL = process.platform === 'win32' ? 'powershell.exe' : (process.env.SHELL || 'bash')

export function registerTerminal(): void {
  let term: pty.IPty | null = null
  let wc: WebContents | null = null

  ipcMain.on('term:start', (e, cols: number, rows: number) => {
    wc = e.sender // (re)point output at the current renderer; survives a renderer hot-reload/reload
    if (term) return
    term = pty.spawn(SHELL, [], {
      name: 'xterm-color',
      cols: cols || 100,
      rows: rows || 24,
      cwd: REPO_ROOT,
      env: process.env as { [k: string]: string }
    })
    term.onData((d) => { if (wc && !wc.isDestroyed()) wc.send('term:data', d) })
    term.onExit(() => { term = null })
  })

  ipcMain.on('term:input', (_e, data: string) => term?.write(data))
  ipcMain.on('term:resize', (_e, cols: number, rows: number) => { try { term?.resize(cols, rows) } catch {} })
}
