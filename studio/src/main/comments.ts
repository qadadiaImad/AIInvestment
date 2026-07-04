// Comment store for the Studio Kit page — shared feedback/post_comments.json.
// Pure ops (unit-tested) + atomic file IO. composeRegenPrompt builds the terminal command.
import { readFileSync, writeFileSync, renameSync, mkdirSync, existsSync } from 'fs'
import { dirname } from 'path'
import { randomBytes } from 'crypto'

export type Comment = {
  id: string; post_id: string; part: string; text: string; created_at: string; resolved: boolean
}
export type Store = { version: number; comments: Comment[] }

export const VALID_PARTS = ['script', 'hook', 'data', 'takeaway', 'hero', 'general']

export function emptyStore(): Store {
  return { version: 1, comments: [] }
}

function newId(): string {
  return 'c_' + randomBytes(4).toString('hex')
}

export function addComment(
  store: Store, postId: string, part: string, text: string, now: string, _id?: string,
): { store: Store; comment: Comment } {
  if (!VALID_PARTS.includes(part)) throw new Error(`bad part ${part}; must be one of ${VALID_PARTS.join(', ')}`)
  if (!text || !text.trim()) throw new Error('comment text is empty')
  const comment: Comment = {
    id: _id || newId(), post_id: postId, part, text: text.trim(), created_at: now, resolved: false,
  }
  return { store: { ...store, comments: [...store.comments, comment] }, comment }
}

function find(store: Store, id: string): Comment {
  const c = store.comments.find((x) => x.id === id)
  if (!c) throw new Error(`comment not found: ${id}`)
  return c
}

export function setResolved(store: Store, id: string, resolved: boolean): Store {
  find(store, id)
  return { ...store, comments: store.comments.map((c) => (c.id === id ? { ...c, resolved } : c)) }
}

export function deleteComment(store: Store, id: string): Store {
  find(store, id)
  return { ...store, comments: store.comments.filter((c) => c.id !== id) }
}

export function loadForPost(store: Store, postId: string, onlyOpen = true): Comment[] {
  return store.comments.filter((c) => c.post_id === postId && (!onlyOpen || !c.resolved))
}

export function readStore(path: string): Store {
  if (!existsSync(path)) return emptyStore()
  try {
    const data = JSON.parse(readFileSync(path, 'utf-8'))
    return { version: data.version ?? 1, comments: data.comments ?? [] }
  } catch {
    return emptyStore()
  }
}

export function writeStore(path: string, store: Store): void {
  mkdirSync(dirname(path), { recursive: true })
  const tmp = path + '.tmp'
  writeFileSync(tmp, JSON.stringify(store, null, 2), 'utf-8')
  renameSync(tmp, path)
}

// Make a string safe to embed inside the PowerShell double-quoted `claude "…"`:
// no newlines, no inner double-quotes (breakout), and neutralize `` ` `` (PS escape char)
// and `$` (PS interpolation: $var / $(...)) by backtick-escaping — `$278` stays literal.
const sanitize = (s: string): string =>
  s.replace(/[\r\n]+/g, ' ')
    .replace(/"/g, "'")
    .replace(/`/g, '``')
    .replace(/\$/g, '`$')
    .trim()

export function composeRegenPrompt(date: string, ticker: string, open: Comment[]): string {
  if (!open.length) return ''
  const notes = open.map((c) => `[${c.part}] ${sanitize(c.text)}`).join('; ')
  const inner =
    `Regenerate the ${date} ${ticker} reel honoring these review comments — ${notes}. ` +
    `Update higgs/reels_${date}.txt + reels_${date}_kit.md per the comments; keep the rails ` +
    `(no first person; reportedly, never name the outlet; congress = transparency not accusation; thin footer NFA). ` +
    `Then mark these comments resolved.`
  return `claude "${sanitize(inner)}"`
}
