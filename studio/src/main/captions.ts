// Parses the reel/post caption sheets: sections headed "=== ... — TICKER (..) ===",
// returns { TICKER: "caption + hashtags block" }.
export function parseCaptions(text: string): Record<string, string> {
  const out: Record<string, string> = {}
  if (!text.trim()) return out
  const blocks = text.split(/^={3,}.*$/m)
  const heads = text.match(/^={3,}.*$/gm) || []
  for (let i = 0; i < heads.length; i++) {
    const tk = heads[i].match(/—\s*([A-Z]{1,6})\b/)?.[1]
    if (!tk) continue
    const body = (blocks[i + 1] || '').trim()
    if (body) out[tk] = body
  }
  return out
}
