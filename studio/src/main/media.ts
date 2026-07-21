import { protocol, net } from 'electron'
import { pathToFileURL } from 'url'
import { join, normalize, sep, extname } from 'path'
import { createReadStream, promises as fsp } from 'fs'
import { Readable } from 'stream'
import { REPO_ROOT } from './paths'

const MIME: Record<string, string> = {
  '.mp4': 'video/mp4',
  '.mp3': 'audio/mpeg',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.html': 'text/html',
  '.txt': 'text/plain',
}

// media://higgs/reel_nvda_2026-06-22.mp4  ->  <repo>/higgs/reel_...mp4
export function registerMediaProtocol(): void {
  const root = normalize(REPO_ROOT)
  protocol.handle('media', async (req) => {
    const rel = decodeURIComponent(new URL(req.url).href.replace(/^media:\/\//, ''))
    const abs = normalize(join(root, rel))
    // contain to repo root; the `+ sep` avoids a sibling-dir prefix match (e.g. <repo>-evil)
    if (abs !== root && !abs.startsWith(root + sep)) {
      return new Response('forbidden', { status: 403 })
    }
    // Serve Range requests ourselves with real 206es — Chromium's <video> stalls a few
    // seconds in when a server ignores Range (net.fetch on file:// returns full 200s).
    const range = req.headers.get('range')
    if (range) {
      let size: number
      try {
        size = (await fsp.stat(abs)).size
      } catch {
        return new Response('not found', { status: 404 })
      }
      const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim())
      if (!m || (m[1] === '' && m[2] === '')) {
        return new Response('bad range', { status: 416, headers: { 'Content-Range': `bytes */${size}` } })
      }
      const start = m[1] === '' ? Math.max(0, size - Number(m[2])) : Number(m[1])
      const end = m[1] !== '' && m[2] !== '' ? Math.min(Number(m[2]), size - 1) : size - 1
      if (start >= size || start > end) {
        return new Response('bad range', { status: 416, headers: { 'Content-Range': `bytes */${size}` } })
      }
      const stream = Readable.toWeb(createReadStream(abs, { start, end })) as ReadableStream
      return new Response(stream, {
        status: 206,
        headers: {
          'Content-Type': MIME[extname(abs).toLowerCase()] ?? 'application/octet-stream',
          'Content-Range': `bytes ${start}-${end}/${size}`,
          'Content-Length': String(end - start + 1),
          'Accept-Ranges': 'bytes',
        },
      })
    }
    const res = await net.fetch(pathToFileURL(abs).toString())
    // advertise range support so the player asks us instead of guessing
    const headers = new Headers(res.headers)
    headers.set('Accept-Ranges', 'bytes')
    return new Response(res.body, { status: res.status, headers })
  })
}
export const PRIVILEGED = [{ scheme: 'media', privileges: { standard: true, secure: true, stream: true, supportFetchAPI: true } }]
