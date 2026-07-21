# Karim Voice Canon

## Locked voice (the ONLY voice for Karim VO)
- Source sample: `voice/karim_sample.wav` — extracted from `video/intro_desk.mp4` (the owner-validated pilot).
- Clone (one-time, owner, Higgsfield web UI): create a cloned voice from the sample; it then
  appears in `higgsfield voices list` with Voice Type `element`. Record its id in
  `higgsfield-ids.json` → `voice.id` (and `created` date). CLI cannot create clones (verified
  2026-07-21: `voices` supports list/get only).
- Usage (all VO): `higgsfield generate create text2speech_v2 --prompt "<script>"
  --variant elevenlabs --voice_id <voice.id> --voice_type element --wait`
- Fallback (if clone QA fails): pick the nearest preset from `higgsfield voices list`, set
  `voice.type = "preset"` + the preset id. Pipeline code reads the config either way.

## Delivery canon (calm educator, English)
- ~150 wpm; short declarative sentences; one idea per sentence.
- Micro-pause (comma or "...") immediately BEFORE each key number.
- Numbers spoken with unit and date ("thirty percent cap", "as of July twenty-first").
- No hype inflection, no exclamation stacks, no slang. Warm, unhurried, certain.
- Script text is written to be heard: digits as words where natural; no URLs; ticker letters
  spelled out only when ambiguous.
- Every script ends with the spoken line: "Educational, not financial or religious advice."
