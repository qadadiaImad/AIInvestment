import { describe, it, expect } from 'vitest'
import { buildIndex, parseDailyFolderName, type Post } from '../src/main/indexer'

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

describe('parseDailyFolderName', () => {
  it('parses date + ticker from the daily pipeline folder convention', () => {
    expect(parseDailyFolderName('2026-07-22_WKEY')).toEqual({ date: '2026-07-22', ticker: 'WKEY' })
  })
  it('uppercases a lowercase ticker', () => {
    expect(parseDailyFolderName('2026-07-22_wkey')).toEqual({ date: '2026-07-22', ticker: 'WKEY' })
  })
  it('returns null for anything that does not match', () => {
    expect(parseDailyFolderName('not-a-folder')).toBeNull()
    expect(parseDailyFolderName('WKEY_2026-07-22')).toBeNull()
  })
})

describe('buildIndex — higgs/daily/<date>_<ticker>/ folders', () => {
  const dailyFiles = (folder: string) => [
    `${folder}/daily_A.mp4`,
    `${folder}/daily_B.mp4`,
    `${folder}/v4_wkey_1_hook.png`,
    `${folder}/v4_wkey_2_data.png`,
    `${folder}/v4_wkey_3_takeaway.png`,
    `${folder}/caption.txt`,
    `${folder}/manifest.json`,
    `${folder}/props_A.json`,
    `${folder}/props_B.json`,
    `${folder}/daily_a.txt`,
    `${folder}/daily_b.txt`,
    `${folder}/voice_daily_a.wav`,
    `${folder}/voice_daily_b.wav`,
    `${folder}/words_A.json`,
    `${folder}/words_B.json`,
  ]

  it('indexes a full daily folder as one reel post: A before B, then slides in order, caption attached', () => {
    const posts = buildIndex({ higgs: [], content: [], daily: dailyFiles('2026-07-22_WKEY') })
    expect(posts).toHaveLength(1)
    const p = posts[0]
    expect(p.date).toBe('2026-07-22')
    expect(p.ticker).toBe('WKEY')
    expect(p.kind).toBe('reel')
    expect(p.media).toEqual([
      'media://higgs/daily/2026-07-22_WKEY/daily_A.mp4',
      'media://higgs/daily/2026-07-22_WKEY/daily_B.mp4',
      'media://higgs/daily/2026-07-22_WKEY/v4_wkey_1_hook.png',
      'media://higgs/daily/2026-07-22_WKEY/v4_wkey_2_data.png',
      'media://higgs/daily/2026-07-22_WKEY/v4_wkey_3_takeaway.png',
    ])
    expect(p.captionFile).toBe('media://higgs/daily/2026-07-22_WKEY/caption.txt')
  })

  it('matches the real live fixture shape (higgs/daily/2026-07-22_WKEY, no caption.txt) without crashing', () => {
    // Mirrors the actual folder on disk today: manifest.json + daily_kit_WKEY.md but no
    // caption.txt yet. Missing caption.txt must not crash the indexer or fabricate a value.
    const posts = buildIndex({
      higgs: [],
      content: [],
      daily: [
        '2026-07-22_WKEY/daily_a.txt', '2026-07-22_WKEY/voice_daily_a.wav',
        '2026-07-22_WKEY/daily_b.txt', '2026-07-22_WKEY/voice_daily_b.wav',
        '2026-07-22_WKEY/words_A.json', '2026-07-22_WKEY/props_A.json',
        '2026-07-22_WKEY/words_B.json', '2026-07-22_WKEY/props_B.json',
        '2026-07-22_WKEY/daily_A.mp4', '2026-07-22_WKEY/daily_B.mp4',
        '2026-07-22_WKEY/daily_kit_WKEY.md',
        '2026-07-22_WKEY/v4_wkey_1_hook.png', '2026-07-22_WKEY/v4_wkey_2_data.png', '2026-07-22_WKEY/v4_wkey_3_takeaway.png',
        '2026-07-22_WKEY/manifest.json',
      ],
    })
    expect(posts).toHaveLength(1)
    expect(posts[0].captionFile).toBeUndefined()
    expect(posts[0].media).toHaveLength(5) // 2 mp4 + 3 png; the rest (txt/wav/json/md) excluded
  })

  it('carousel may be skipped (no v4_*.png yet) — still indexes the A/B reel', () => {
    const posts = buildIndex({
      higgs: [], content: [],
      daily: ['2026-07-21_ETN/daily_A.mp4', '2026-07-21_ETN/daily_B.mp4', '2026-07-21_ETN/manifest.json'],
    })
    expect(posts).toHaveLength(1)
    expect(posts[0].media).toEqual([
      'media://higgs/daily/2026-07-21_ETN/daily_A.mp4',
      'media://higgs/daily/2026-07-21_ETN/daily_B.mp4',
    ])
  })

  it('falls back to manifest.json when the folder name does not match the convention', () => {
    const posts = buildIndex({
      higgs: [], content: [],
      daily: ['round7_special/daily_A.mp4'],
      dailyManifests: { round7_special: { date: '2026-07-20', ticker: 'gev' } },
    })
    expect(posts).toHaveLength(1)
    expect(posts[0]).toMatchObject({ date: '2026-07-20', ticker: 'GEV' })
    expect(posts[0].media).toEqual(['media://higgs/daily/round7_special/daily_A.mp4'])
  })

  it('skips a folder gracefully when neither the name nor a manifest yields date+ticker', () => {
    const posts = buildIndex({ higgs: [], content: [], daily: ['garbage_folder/daily_A.mp4'] })
    expect(posts).toHaveLength(0)
  })

  it('missing manifest.json entirely does not crash — folder-name parsing still works', () => {
    const posts = buildIndex({ higgs: [], content: [], daily: ['2026-07-19_NVDA/daily_A.mp4'] })
    expect(posts).toHaveLength(1)
    expect(posts[0]).toMatchObject({ date: '2026-07-19', ticker: 'NVDA' })
  })

  it('daily folders never collide with legacy top-level reel_* bundles of a different post', () => {
    const posts = buildIndex({
      higgs: ['reel_wkey_2026-07-20.mp4'],
      content: [],
      daily: dailyFiles('2026-07-22_WKEY'),
    })
    expect(posts).toHaveLength(2)
    expect(posts.find(p => p.date === '2026-07-20')?.media).toEqual(['media://higgs/reel_wkey_2026-07-20.mp4'])
    expect(posts.find(p => p.date === '2026-07-22')?.media[0]).toBe('media://higgs/daily/2026-07-22_WKEY/daily_A.mp4')
  })
})
