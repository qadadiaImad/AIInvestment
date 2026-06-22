import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
type Post = Awaited<ReturnType<typeof window.studio.posts.list>>[number]
type Ctx = { posts: Post[]; refresh: () => void; selected: Post | null; select: (p: Post | null) => void }
const C = createContext<Ctx>(null as any)
export const useStudio = () => useContext(C)
export function StudioProvider({ children }: { children: ReactNode }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [selected, select] = useState<Post | null>(null)
  const refresh = () => window.studio.posts.list().then(setPosts)
  useEffect(() => { refresh() }, [])
  return <C.Provider value={{ posts, refresh, selected, select }}>{children}</C.Provider>
}
