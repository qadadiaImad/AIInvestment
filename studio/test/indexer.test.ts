import { describe, it, expect } from 'vitest'
import { buildIndex, type Post } from '../src/main/indexer'

describe('buildIndex', () => {
  it('groups a reel + its slides + caption under one bundle by date+ticker', () => {
    const files = {
      higgs: [
        'reel_nvda_2026-06-22.mp4',
        'reel_nvda_data.png', 'reel_nvda_hook.png', 'reel_nvda_takeaway.png',
        'v4_nvda_1_hook.png', 'v4_nvda_2_data.png', 'v4_nvda_3_takeaway.png',
        'reels_2026-06-22.txt',
        'hero_nvda_2026-06-22.png', 'logo_NVDA.png', '_check_anim.png' // excluded
      ],
      content: ['carousel_2026-06-03/CRM/slide_1.html', 'carousel_2026-06-03/CRM/brief.md']
    }
    const out: Post[] = buildIndex(files)
    const nvda = out.find(p => p.ticker === 'NVDA' && p.date === '2026-06-22')!
    expect(nvda.kind).toBe('reel')
    expect(nvda.media.some(m => m.endsWith('reel_nvda_2026-06-22.mp4'))).toBe(true)
    expect(nvda.media.some(m => m.includes('v4_nvda_1_hook'))).toBe(true)
    // intermediates excluded
    expect(nvda.media.some(m => m.includes('hero_') || m.includes('logo_') || m.includes('_check'))).toBe(false)
    // content carousel becomes its own bundle
    expect(out.some(p => p.ticker === 'CRM' && p.date === '2026-06-03' && p.kind === 'carousel')).toBe(true)
  })

  it('sorts newest day first', () => {
    const out = buildIndex({ higgs: ['reel_ionq_2026-06-21.mp4', 'reel_nvda_2026-06-22.mp4'], content: [] })
    expect(out[0].date >= out[out.length - 1].date).toBe(true)
  })
})

it('carousel-only round: orphan v4 slides become a dated carousel post (halal round shape)', () => {
  const posts = buildIndex({
    higgs: ['v4_wulf_1_hook.png', 'v4_wulf_2_data.png', 'v4_wulf_3_takeaway.png', 'reels_2026-07-21.txt'],
    content: []
  })
  expect(posts).toHaveLength(1)
  const p = posts[0]
  expect(p.ticker).toBe('WULF')
  expect(p.kind).toBe('carousel')
  expect(p.date).toBe('2026-07-21')
  expect(p.media).toEqual([
    'media://higgs/v4_wulf_1_hook.png',
    'media://higgs/v4_wulf_2_data.png',
    'media://higgs/v4_wulf_3_takeaway.png'
  ])
  expect(p.captionFile).toBe('media://higgs/reels_2026-07-21.txt')
})

it('orphan v4 slides without any caption sheet stay dropped (legacy behavior)', () => {
  const posts = buildIndex({ higgs: ['v4_zzz_1_hook.png'], content: [] })
  expect(posts).toHaveLength(0)
})
