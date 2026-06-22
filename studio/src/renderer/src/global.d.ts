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
      reveal(rel: string): void
      copy(text: string): void
      quickCmd(name: string): string
    }
  }
}
