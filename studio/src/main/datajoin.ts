export type Bundles = { site?: any; quantum?: any; congress?: any }
export type StockView = {
  found: boolean
  source?: 'site' | 'quantum'
  layer?: string
  valuation?: any
  congress_trades: any[]
}

export function joinStock(ticker: string, b: Bundles): StockView {
  const t = ticker.toUpperCase()
  let rec: any, source: 'site' | 'quantum' | undefined
  if (b.site?.stocks?.[t]) { rec = b.site.stocks[t]; source = 'site' }
  else if (b.quantum?.stocks?.[t]) { rec = b.quantum.stocks[t]; source = 'quantum' }
  const trades = (b.congress?.trades || []).filter((x: any) => x.ticker === t)
  if (!rec) return { found: false, congress_trades: trades }
  return { found: true, source, layer: rec.layer, valuation: rec.valuation, congress_trades: trades }
}
