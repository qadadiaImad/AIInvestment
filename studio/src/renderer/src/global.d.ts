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
    }
  }
}
