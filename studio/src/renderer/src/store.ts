import { createContext, useContext, useEffect, useState, type ReactNode, createElement } from 'react'

export type Post = Awaited<ReturnType<typeof window.studio.posts.list>>[number]

type StudioCtx = {
  posts: Post[]
  loading: boolean
  refresh(): void
  selected: Post | null
  select(p: Post | null): void
  filterTicker: string
  setFilterTicker(t: string): void
  filterDate: string
  setFilterDate(d: string): void
}

const Ctx = createContext<StudioCtx | null>(null)

export function StudioProvider({ children }: { children: ReactNode }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Post | null>(null)
  const [filterTicker, setFilterTicker] = useState('')
  const [filterDate, setFilterDate] = useState('all')

  function refresh() {
    setLoading(true)
    window.studio.posts.list().then(setPosts).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { refresh() }, [])

  const value: StudioCtx = {
    posts, loading, refresh,
    selected, select: setSelected,
    filterTicker, setFilterTicker,
    filterDate, setFilterDate
  }

  return createElement(Ctx.Provider, { value }, children)
}

export function useStudio(): StudioCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useStudio must be used inside StudioProvider')
  return ctx
}
