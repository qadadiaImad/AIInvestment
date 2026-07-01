import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
type Post = Awaited<ReturnType<typeof window.studio.posts.list>>[number]
// `nonce` bumps on every refresh so views that load their own data (e.g. KitView)
// can re-fetch in response to the header Refresh button, not just on mount.
type Ctx = { posts: Post[]; refresh: () => void; nonce: number; selected: Post | null; select: (p: Post | null) => void }
const C = createContext<Ctx>(null as any)
export const useStudio = () => useContext(C)
export function StudioProvider({ children }: { children: ReactNode }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [nonce, setNonce] = useState(0)
  const [selected, select] = useState<Post | null>(null)
  const refresh = () => { window.studio.posts.list().then(setPosts); setNonce((n) => n + 1) }
  useEffect(() => { refresh() }, [])
  return <C.Provider value={{ posts, refresh, nonce, selected, select }}>{children}</C.Provider>
}
