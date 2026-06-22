# Reel engine — narrated 9:16 social videos

Turns the terminal's fresh fundamentals into short narrated reels: **animated AI hero + AI voiceover + Ken-Burns data slides**, one per stock/story. Static image carousels share the same heroes/logos (`_build_v4.py`).

## Pieces

| File | Role |
|---|---|
| `_build_v4.py` | Static 4:5 carousel slides (hero + logo + big ticker + data). Free, local. |
| `_build_reel_stock.py <TK>` | 9:16 reel **frames** for a stock (hook overlay + data slide + takeaway). Config-driven (`CFG` dict). Free, local. |
| `_build_reel_congress.py` | 9:16 reel frames for the congress story (own template: basket card, no logo). |
| `make_reel.py <TK> <hero_url> <voice_url>` | Assembles one reel end-to-end: frames → download hero+voice → silence-based cuts → ffmpeg (corrected idiom) → mux voice → verify. Free, local. |
| `_workflow_make_reels.js` | `make-all-reels` workflow — assembles N reels **in parallel** from a manifest. |
| `reels_manifest.json` | The reels to build: `[{tk, hero, voice}]` with resolved Higgsfield URLs. |

## Run flow (after a data refresh)

The pipeline is a **2-phase hybrid** because Higgsfield generation is MCP and orchestrator-owned (the
MCP connection is a shared resource — kept serial, like the gated-source contract). Assembly is no-gate → parallel workflow.

**Phase 1 — orchestrator (Claude), serial MCP** — for each story:
1. Pick the hottest on-scope names + numbers from `web/public/data/{site,quantum,congress}.json`
   (most undervalued AI/software, quantum price-vs-model outlier, a committee-relevant congress trade).
2. `generate_image` (recraft-v4-1, 4:5, emerald palette) → thematic hero. Animate it: `generate_video`
   (kling3_0, 9:16, 5s, sound off). Fetch the real logo: `financialmodelingprep.com/image-stock/<TK>.png`.
3. `generate_audio` (text2speech_v2_elevenlabs, voice "Harrison") with the catchy, de-cringed script
   (rails: no first person, no outlet named → "reportedly", congress = transparency not accusation, thin footer NFA).
4. Poll job_status, collect the hero-MP4 + voice-MP3 URLs into `reels_manifest.json`.

**Phase 2 — workflow, parallel (no gate):**
```
Workflow({ scriptPath: "higgs/_workflow_make_reels.js", args: <the reels array from reels_manifest.json> })
```
Each reel runs `make_reel.py` (frames + download + ffmpeg) concurrently → `reel_<tk>_<date>.mp4`.

Then write the caption sheet (`reels_<date>.txt`) and review voice pacing.

## ffmpeg safety (learned the hard way)
Ken-burns MUST use `-loop 1` **without** `-t` on input + `-frames:v N` cap (else zoompan multiplies frames into a
multi-hundred-MB runaway). Always `-crf` rate control + `-preset veryfast`. `make_reel.py` encodes this correctly;
do not hand-roll ffmpeg in agents. Output sanity check: a ~30s reel is ~5–7 MB; >40MB = encode bug.

## Costs (Higgsfield)
Per reel ≈ 8 (hero image) + 7.5 (animate) + ~3 (voice) ≈ **~18 credits**. Carousel-only (no video) ≈ 8.
Assembly (ffmpeg) is free/local. Voice only; add music in your editor.

## Add a new stock reel
1. Add a `CFG["TK"]` block in `_build_reel_stock.py` (hero filename, logo, ex-label, hook/data/takeaway copy, `mode` = `mult` or `disc`, `rows`).
2. Phase 1 to make its hero+voice; append to `reels_manifest.json`; run the workflow.
