import { describe, it, expect } from 'vitest'
import { joinStock, type Bundles } from '../src/main/datajoin'

const B: Bundles = {
  site: { stocks: { NVDA: { layer: 'L1-chips', valuation: { price: 210, fundamental_value: 345, fundamental_discount_pct: 39, fundamental_valuation: 'Undervalued' } } } },
  quantum: { stocks: { IONQ: { valuation: { price: 56, fundamental_value: 86, fundamental_discount_pct: 35 } } } },
  congress: { trades: [{ ticker: 'NVDA', politician: 'Jane Doe', txn_type: 'S', txn_date: '06/16/2026', amount_range_low: 1001, amount_range_high: 15000 }] }
}

describe('joinStock', () => {
  it('finds an AI-stack name in site and attaches congress trades', () => {
    const r = joinStock('NVDA', B)
    expect(r.found).toBe(true)
    expect(r.source).toBe('site')
    expect(r.valuation?.fundamental_discount_pct).toBe(39)
    expect(r.congress_trades.length).toBe(1)
  })
  it('falls back to quantum', () => {
    expect(joinStock('IONQ', B).source).toBe('quantum')
  })
  it('reports not found cleanly', () => {
    expect(joinStock('ZZZZ', B).found).toBe(false)
  })
})
