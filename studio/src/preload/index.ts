import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('studio', {
  term: {
    start: (cols: number, rows: number) => ipcRenderer.send('term:start', cols, rows),
    input: (data: string) => ipcRenderer.send('term:input', data),
    resize: (cols: number, rows: number) => ipcRenderer.send('term:resize', cols, rows),
    onData: (cb: (d: string) => void) => {
      const h = (_: unknown, d: string) => cb(d)
      ipcRenderer.on('term:data', h)
      return () => ipcRenderer.removeListener('term:data', h)
    }
  }
})
