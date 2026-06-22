import { contextBridge } from 'electron'

// Expanded in later tasks (terminal, posts, stock, caption).
contextBridge.exposeInMainWorld('studio', {
  ping: () => 'pong'
})
