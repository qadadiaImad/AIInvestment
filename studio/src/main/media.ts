import { protocol, net } from 'electron'
import { pathToFileURL, fileURLToPath } from 'url'
import { join, normalize } from 'path'
import { REPO_ROOT } from './paths'

// media://higgs/reel_nvda_2026-06-22.mp4  ->  <repo>/higgs/reel_...mp4
export function registerMediaProtocol(): void {
  protocol.handle('media', (req) => {
    const rel = decodeURIComponent(new URL(req.url).href.replace(/^media:\/\//, ''))
    const abs = normalize(join(REPO_ROOT, rel))
    if (!abs.startsWith(normalize(REPO_ROOT))) {
      return new Response('forbidden', { status: 403 })
    }
    return net.fetch(pathToFileURL(abs).toString()) // handles range requests for video
  })
}
export const PRIVILEGED = [{ scheme: 'media', privileges: { standard: true, secure: true, stream: true, supportFetchAPI: true } }]
export { fileURLToPath } // (kept for tests if needed)
