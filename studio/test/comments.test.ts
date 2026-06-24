import { describe, it, expect } from 'vitest'
import { mkdtempSync } from 'fs'
import { join } from 'path'
import { tmpdir } from 'os'
import {
  emptyStore, addComment, setResolved, deleteComment, loadForPost,
  readStore, writeStore, composeRegenPrompt,
} from '../src/main/comments'

describe('comment store ops', () => {
  it('adds and loads for a post', () => {
    const { store, comment } = addComment(emptyStore(), '2026-06-23_NBIS_reel', 'data',
      'lead with fair value', '2026-06-24T00:00:00Z', 'c_00000001')
    expect(comment.id).toBe('c_00000001')
    expect(comment.part).toBe('data')
    expect(comment.resolved).toBe(false)
    expect(loadForPost(store, '2026-06-23_NBIS_reel').length).toBe(1)
  })
  it('rejects bad part and empty text', () => {
    expect(() => addComment(emptyStore(), 'p', 'bogus', 'x', 'now')).toThrow()
    expect(() => addComment(emptyStore(), 'p', 'data', '  ', 'now')).toThrow()
  })
  it('resolve hides from open load', () => {
    let { store } = addComment(emptyStore(), 'p1', 'general', 'fix', 'now', 'c_aaaa0001')
    store = setResolved(store, 'c_aaaa0001', true)
    expect(loadForPost(store, 'p1', true)).toEqual([])
    expect(loadForPost(store, 'p1', false).length).toBe(1)
  })
  it('delete works; missing id throws', () => {
    let { store } = addComment(emptyStore(), 'p1', 'hook', 'x', 'now', 'c_aaaa0002')
    store = deleteComment(store, 'c_aaaa0002')
    expect(loadForPost(store, 'p1', false)).toEqual([])
    expect(() => setResolved(store, 'c_missing', true)).toThrow()
  })
  it('write then read roundtrip; missing file -> empty', () => {
    const p = join(mkdtempSync(join(tmpdir(), 'kitc-')), 'feedback', 'post_comments.json')
    expect(readStore(p)).toEqual(emptyStore())
    const { store } = addComment(emptyStore(), 'p1', 'script', 'hi', 'now', 'c_aaaa0003')
    writeStore(p, store)
    expect(readStore(p).comments[0].text).toBe('hi')
  })
})

describe('composeRegenPrompt', () => {
  it('folds open comments + rails into a claude command with no inner double-quotes', () => {
    const open = [
      { id: 'c1', post_id: '2026-06-23_NBIS_reel', part: 'data', text: 'lead with "fair value"', created_at: 'now', resolved: false },
      { id: 'c2', post_id: '2026-06-23_NBIS_reel', part: 'script', text: 'slow the open', created_at: 'now', resolved: false },
    ]
    const cmd = composeRegenPrompt('2026-06-23', 'NBIS', open)
    expect(cmd.startsWith('claude "')).toBe(true)
    expect(cmd.endsWith('"')).toBe(true)
    expect(cmd).toContain('2026-06-23 NBIS reel')
    expect(cmd).toContain('[data]')
    expect(cmd).toContain('slow the open')
    expect(cmd).toContain('mark these comments resolved')
    expect((cmd.match(/"/g) || []).length).toBe(2)   // only the 2 wrapper quotes; inner ones sanitized
  })
  it('returns empty string when no open comments', () => {
    expect(composeRegenPrompt('2026-06-23', 'NBIS', [])).toBe('')
  })
  it('neutralizes PowerShell interpolation (backtick / $()) in a comment', () => {
    const open = [
      { id: 'c1', post_id: '2026-06-23_NBIS_reel', part: 'general', text: 'fix $(rm x) and `code`', created_at: 'now', resolved: false },
    ]
    const cmd = composeRegenPrompt('2026-06-23', 'NBIS', open)
    expect((cmd.match(/"/g) || []).length).toBe(2)   // still only the 2 wrapper quotes
    expect(cmd).toContain('`$(rm x)')                // $ backtick-escaped (kept literal)
    expect(cmd).toContain('``code``')                // backticks doubled (kept literal)
    expect(cmd).not.toMatch(/[^`]\$\(/)              // no un-escaped $( remains
  })
})
