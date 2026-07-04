export const meta = {
  name: 'make-all-reels',
  description: 'Assemble N narrated 9:16 stock reels in parallel from higgs/reels_manifest.json (or explicit args), via the deterministic make_reel.py pipeline. MCP hero/voice generation is done by the orchestrator BEFORE this runs; this fans out only the no-gate render+assemble stages. Args optional: [{tk, hero, voice}, ...] — omitted args = read the manifest automatically.',
  phases: [
    { title: 'Manifest', detail: 'read reels_manifest.json when no args passed' },
    { title: 'Assemble', detail: 'render frames + download hero/voice + ffmpeg mux, one agent per reel' },
  ],
}

// args = [{ tk, hero, voice }, ...]  (also tolerates a JSON string or a {reels:[...]} object).
// With NO args, the manifest is read by a subagent — zero per-round configuration.
let parsed = args
if (typeof parsed === 'string') { try { parsed = JSON.parse(parsed) } catch (e) { parsed = [] } }
let REELS = Array.isArray(parsed) ? parsed : (parsed && Array.isArray(parsed.reels) ? parsed.reels : [])

const MANIFEST_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    reels: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { tk: { type: 'string' }, hero: { type: 'string' }, voice: { type: 'string' } },
        required: ['tk', 'hero', 'voice'],
      },
    },
  },
  required: ['reels'],
}

if (!REELS.length) {
  phase('Manifest')
  const m = await agent(
    [
      'Read the file higgs/reels_manifest.json relative to your current working directory (the repo root).',
      'Return {reels:[{tk, hero, voice}, ...]} containing ONLY entries where BOTH hero and voice are real URLs',
      '(contain "://" and do not start with "<"). Exclude any entry whose tk is "CONG" — the congress reel',
      'uses its own builder and is not part of the stock pipeline. Do not modify any file.',
    ].join('\n'),
    { label: 'read-manifest', phase: 'Manifest', schema: MANIFEST_SCHEMA, effort: 'low' }
  )
  REELS = (m && m.reels) || []
}
REELS = REELS.filter(r => r && r.tk && String(r.tk).toUpperCase() !== 'CONG')
if (!REELS.length) return { error: 'no assemblable reels — manifest empty/placeholders, or pass [{tk,hero,voice},...]' }

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    ok: { type: 'boolean', description: 'true only if make_reel.py exited 0 and printed an OK line' },
    summary: { type: 'string', description: 'the OK line (filename, duration, size, audio, cuts) — or failure tail' },
    output_file: { type: 'string', description: 'path to reel_<tk>_*.mp4, or empty on failure' },
  },
  required: ['ok', 'summary', 'output_file'],
}

phase('Assemble')
const results = await parallel(REELS.map(r => () => agent(
  [
    'You are a deterministic pipeline-step runner. Run EXACTLY one command, then report. Do NOT edit files, do NOT improvise ffmpeg, do NOT run anything else except the verification the script already does.',
    '',
    'Working directory: your current working directory IS the repo root (it contains higgs/). Do not cd elsewhere.',
    'Command (Bash tool, timeout 300000):',
    `  python higgs/make_reel.py ${r.tk} "${r.hero}" "${r.voice}"`,
    '',
    '`python`/`ffmpeg`/`ffprobe` are on PATH. The script prints one "OK ..." line on success. On non-zero exit, capture the last ~15 lines of stderr.',
    'IMPORTANT: if it hangs past ~4 min OR any intermediate file exceeds ~100MB, report ok=false with what you saw; do NOT retry with your own ffmpeg flags.',
    '',
    'Report via schema: ok, summary (OK line or failure tail), output_file.',
  ].join('\n'),
  { label: `reel:${r.tk}`, phase: 'Assemble', schema: SCHEMA }
)))

const clean = results.filter(Boolean)
return {
  ok_count: clean.filter(x => x.ok).length,
  total: REELS.length,
  reels: clean.map(x => ({ ok: x.ok, file: x.output_file, summary: x.summary })),
}
