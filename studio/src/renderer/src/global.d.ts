export {}
declare global {
  interface Window {
    studio: {
      term: {
        start(cols: number, rows: number): void
        input(data: string): void
        resize(cols: number, rows: number): void
        onData(cb: (d: string) => void): () => void
      }
      posts: { list(): Promise<Array<{ date: string; ticker: string; kind: string; media: string[]; poster?: string; captionFile?: string }>> }
      stock: { get(ticker: string): Promise<{ found: boolean; source?: string; layer?: string; valuation?: any; congress_trades: any[] }> }
      caption: { get(date: string, ticker: string): Promise<string> }
      kit: {
        list(): Promise<Array<{ id: string; date: string; ticker: string; theme: string }>>
        get(date: string, ticker: string): Promise<{
          id: string; date: string; ticker: string; theme: string
          script: string; hashtags: string
          slides: {
            hook: { kick?: string; head?: string; sub?: string; ex?: string }
            data: { kick?: string; title?: string; cap?: string; foot?: string; rows?: string; mode?: string }
            takeaway: { kick?: string; big?: string; unit?: string; label?: string; body?: string }
          } | null
          hero_prompt: string | null
          hero_image: string | null
          story: string | null
          source: { found: boolean; source?: string; layer?: string; valuation?: any; congress_trades: any[] }
        }>
      }
      comments: {
        list(postId: string): Promise<Array<{ id: string; post_id: string; part: string; text: string; created_at: string; resolved: boolean }>>
        add(postId: string, part: string, text: string): Promise<{ id: string; post_id: string; part: string; text: string; created_at: string; resolved: boolean }>
        setResolved(id: string, resolved: boolean): Promise<{ ok: boolean }>
        delete(id: string): Promise<{ ok: boolean }>
        composePrompt(date: string, ticker: string): Promise<string>
      }
      reveal(rel: string): void
      copy(text: string): void
      quickCmd(name: string): string
    }
  }
}
