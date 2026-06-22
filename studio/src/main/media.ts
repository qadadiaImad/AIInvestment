import { protocol, net } from 'electron'
import { pathToFileURL } from 'url'
import { join, normalize, sep } from 'path'
import { REPO_ROOT } from './paths'

// media://higgs/reel_nvda_2026-06-22.mp4  ->  <repo>/higgs/reel_...mp4
export function registerMediaProtocol(): void {
  const root = normalize(REPO_ROOT)
  protocol.handle('media', (req) => {
    const rel = decodeURIComponent(new URL(req.url).href.replace(/^media:\/\//, ''))
    const abs = normalize(join(root, rel))
    // contain to repo root; the `+ sep` avoids a sibling-dir prefix match (e.g. <repo>-evil)
    if (abs !== root && !abs.startsWith(root + sep)) {
      return new Response('forbidden', { status: 403 })
    }
    return net.fetch(pathToFileURL(abs).toString()) // handles range requests for video
  })
}
export const PRIVILEGED = [{ scheme: 'media', privileges: { standard: true, secure: true, stream: true, supportFetchAPI: true } }]
