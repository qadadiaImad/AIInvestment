import { createContext, useContext, useEffect, useState, type ReactNode, createElement } from 'react'

export type Post = {
  date: string
  ticker: string
  kind: string
  media: string[]
  poster?: string
  captionFile?: string
}

type StudioCtx = {
  posts: Post[]
  loading: boolean
  refresh(): void
  selected: Post | null
  select(p: Post | null): void
  filterTicker: string
  setFilterTicker(t: string): void
  filterKind: string
  setFilterKind(k: string): void
}

const Ctx = createContext<StudioCtx | null>(null)

export function StudioProvider({ children }: { children: ReactNode }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Post | null>(null)
  const [filterTicker, setFilterTicker] = useState('')
  const [filterKind, setFilterKind] = useState('')

  function refresh() {
    setLoading(true)
    window.studio.posts.list().then(data => {
      setPosts(data as Post[])
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => { refresh() }, [])

  const value: StudioCtx = {
    posts, loading, refresh,
    selected, select: setSelected,
    filterTicker, setFilterTicker,
    filterKind, setFilterKind
  }

  return createElement(Ctx.Provider, { value }, children)
}

export function useStudio(): StudioCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useStudio must be used inside StudioProvider')
  return ctx
}
