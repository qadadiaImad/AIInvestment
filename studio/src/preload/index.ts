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
  },
  posts: { list: () => ipcRenderer.invoke('posts:list') },
  stock: { get: (ticker: string) => ipcRenderer.invoke('stock:get', ticker) },
  caption: { get: (date: string, ticker: string) => ipcRenderer.invoke('caption:get', date, ticker) },
  reveal: (rel: string) => ipcRenderer.send('reveal', rel),
  copy: (text: string) => ipcRenderer.send('copy', text),
  quickCmd: (name: string) => ipcRenderer.sendSync('quick:cmd', name)
})
