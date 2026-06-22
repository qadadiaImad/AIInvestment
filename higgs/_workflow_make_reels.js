export const meta = {
  name: 'make-all-reels',
  description: 'Assemble N narrated 9:16 stock reels in parallel from a manifest of pre-resolved Higgsfield asset URLs, via the deterministic make_reel.py pipeline. MCP hero/voice generation is done by the orchestrator BEFORE this runs; this fans out only the no-gate render+assemble stages. Pass args = [{tk, hero, voice}, ...].',
  phases: [{ title: 'Assemble', detail: 'render frames + download hero/voice + ffmpeg mux, one agent per reel' }],
}

// args = [{ tk, hero, voice }, ...]  (also tolerates a JSON string or a {reels:[...]} object)
let parsed = args
if (typeof parsed === 'string') { try { parsed = JSON.parse(parsed) } catch (e) { parsed = [] } }
const REELS = Array.isArray(parsed) ? parsed : (parsed && Array.isArray(parsed.reels) ? parsed.reels : [])
if (!REELS.length) return { error: 'no reels in args; pass [{tk,hero,voice},...] (array or JSON string)' }

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
    'Working directory: C:/Users/imadq/AIInvestment',
    'Command (Bash tool, timeout 300000):',
    `  cd "C:/Users/imadq/AIInvestment" && python higgs/make_reel.py ${r.tk} "${r.hero}" "${r.voice}"`,
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
