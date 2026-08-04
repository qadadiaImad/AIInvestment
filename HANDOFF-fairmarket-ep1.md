# HANDOFF — FairMarketEp1 (vector character short)

Written 2026-08-04 for whoever picks this up next. Branch:
`feat/multi-sector-research-platform`. Everything below is verified this
session unless marked otherwise.

**What it is.** A 9:16 animated short — Sol (old market veteran) explains
to Rex (young analyst) that markets sometimes trade on politics, using
real congressional filings. All local generation ($0): Illustrious-XL +
`ana_cast_v1` LoRA on ComfyUI, vectorised to SVG, animated in Remotion.

**Current deliverable:** `content/vector_char/cast/ep_fairmarket/fairmarket_ep1_anime_v15.mp4`
(36.2s, 1080x1920, 26.8 MB). Every version v4→v15 is kept on disk and in
git — **never delete rendered media** (owner rule).

---

## 1. Where everything lives

| What | Path |
|---|---|
| Composition | `remotion/src/compositions/FairMarketEp1.tsx` |
| The set (room/desk/TV) | `remotion/src/motion/Set.tsx` |
| Interaction grammar | `remotion/src/motion/interact.ts` |
| Cartoon primitives | `remotion/src/motion/toon.ts`, `ToonFX.tsx` |
| Pose geometry | `remotion/src/fixtures/cast_ep1/pose_anchors.json` |
| Mouth drawings map | `remotion/src/fixtures/cast_ep1/visemes.json` |
| Per-frame speech amplitude | `remotion/src/fixtures/cast_ep1/mouth_tracks.json` |
| Head anchor for punch-ins | `remotion/src/fixtures/cast_ep1/head_focus.json` |
| Character SVGs | `remotion/public/characters/cast_ep1/` (+ `visemes/`) |
| Voice + SFX | `remotion/public/audio/fairmarket/`, `remotion/public/audio/sfx_*.wav` |
| Generation work dir | `content/vector_char/cast/ep_fairmarket/` |
| Python pipeline | `scripts/vector/`, `scripts/audio/`, `scripts/comfy/` |

## 2. Commands

```powershell
# render / single frame  (run from remotion/)
npx remotion render FairMarketEp1 ..\content\vector_char\cast\ep_fairmarket\out.mp4 --crf 18
npx remotion still  FairMarketEp1 out.png --frame=505

# tests (run from scripts/)
python -m pytest tests/test_visemes_ep1.py tests/test_vector_cells.py -q

# analysis tools (run from scripts/) — USE THESE, they exist for a reason
python -m vector.cut_sheet <video.mp4> <tag>   # assembly sheet + jump-cut + coverage report
python -m vector.head_scale                    # on-screen HEAD size per staging
python -m vector.phrase_cuts                   # cut points from VO silence
python -m vector.continuity_probe <video> <tag># frames at shot boundaries

# audio
python scripts/audio/make_toon_sfx.py                       # regenerate motion SFX
python scripts/audio/check_sfx_landed.py <before> <after>   # prove a hit is audible

# grok TTS (voices: sal = Sol, rex = Rex)
$e="$env:USERPROFILE\tools\grok-cli\grok-cli.exe"; $a="$env:USERPROFILE\.grok-cli\auth.json"
& $e tts --auth-file $a --voice-id sal --output line.wav --output-format wav "text here"
```

## 3. Gotchas — read this section before changing anything

Each of these cost at least one render cycle to find.

1. **ComfyUI `VAEEncode` floor-crops dimensions to multiples of 8.** An
   846x1101 base returned 840x1096 and every mask alignment was silently
   wrong. `visemes_ep1.pad8/unpad8` handles it. Always pad before staging.
2. **Composite the inpainted region back onto the base.** The VAE
   round-trip drifts ~8.6% of pixels OUTSIDE the mask; without the
   composite, "identical except the mouth" is false.
3. **BLINKS ARE A DEAD END for some poses — do not retry.** Five rounds
   (denoise 0.8 / 0.85 / 0.95 whole-band, a dozen phrasings, anti-wink
   negatives, and a two-pass single-eye variant that makes a wink
   structurally impossible) all failed the gate on sol_point,
   rex_shock_v1, sol_wink and sol_laugh. The model returns the base eyes
   or draws a wink. 7 of 15 poses got blinks; it is pose-dependent luck.
   Ship without, or cut to a sibling pose that has one.
4. **Restyling an open eye DOES work** (`scripts/vector/calm_eyes.py`) —
   Rex's star-glint pupils were replaced with ordinary ones first try.
   Closing an eye is the hard ask, not changing one.
5. **vtracer's default `filter_speckle=8` damages small features.** It is
   sized to drop anti-aliasing crumbs off big flat shapes; at mouth scale
   it ate and re-joined outlines and produced a stray black hook. Use
   `vectorize(..., detail=True)`.
6. **Do NOT posterise before tracing.** Tried at 40 colours on the theory
   vtracer wants flat colour; it shifted Sol's pink cheek blush to olive
   and drained his bow tie. `flatten_palette` stays in `cells.py`, OFF.
7. **`bg_to_alpha` (corner-sampled) fails on bust closeups** where hair or
   skin reaches the corners — 9 poses were never keyed and composited as
   white rectangles. Use `white_bg_to_alpha` (border-connected near-white)
   for white backgrounds, `bg_to_alpha` for flat coloured ones.
8. **Head size, not body height, decides whether two characters look the
   same scale.** These drawings have wildly different head-to-body ratios;
   matched by ink height, Sol's head rendered 432px against rex_listen's
   128px. Run `vector.head_scale` after any staging change.
9. **A shot carrying `tx`/`ty` re-centres EVERY actor it draws** on that
   point, so multi-actor shots stack unless they use `only` or `show`.
10. **A VO track only covers the spoken word.** When it runs out the mouth
    state falls back to closed — which shut Rex's mouth mid-scream on a
    55-frame take fed by a 26-frame line. Use `Beat.holdMouth` on
    reaction beats where the drawing IS the performance.
11. **`boil()` reads as the picture VIBRATING** on large clean vectors. It
    is a 2-frame random offset. Replaced by `interact.idle()` — slow
    breath + weight shift. Do not reintroduce boil for idle motion.
12. **Remotion's bundled ffmpeg is a minimal build.** No `select` filter
    (use output seeking `-i in.mp4 -ss T -frames:v 1`), no highpass/
    lowpass (that is why SFX are synthesised in pure Python).
13. **grok-cli resolves its auth state relative to the CWD**, not `$HOME`.
    It reports `state_file_missing` from anywhere except `C:\Users\imadq`.
    Always pass `--auth-file`.
14. **Chatterbox writes 32-bit float WAV** (`wave` module cannot read it).
    Convert: `ffmpeg -i in.wav -acodec pcm_s16le -ar 24000 -ac 1 out.wav`.
15. **An `<Audio>` that fails to resolve still renders a valid file.**
    Never assume a sound landed — `check_sfx_landed.py` measures it.
16. **Sub-agent model policy:** orchestrator runs the top model; every
    sub-agent and workflow `agent()` call uses `model: 'sonnet'`.

## 4. Owner rules (hard constraints)

- **Never a static, fully-zoomed, face-only frame.** Throws away the set
  and has nowhere to go. Cap the reframe so the room stays visible; any
  shot held past ~1s must creep, cut, or contain motion.
- **No character on a little white card.** The old "panel" kind put a
  cream backing plate behind full-bleed drawings — rejected. Use
  clean-silhouette drawings that float, or put the image on the TV.
- **Never delete rendered media.** Cleanup means caches only.
- **No Higgsfield.** Local ComfyUI + grok-cli + Kaggle only.
- **Vision-gate every generated drawing before wiring it in**, with a
  sonnet sub-agent, and show the gated sheets before use.
- **Compliance:** parody / public record / educational, not advice, not an
  accusation. Caricatures are generic ARCHETYPES, never a likeness of a
  named individual; no on-screen text names a person; cards state only
  what the public filing states; footer on every frame.

## 5. State of play / open work

**Done and shipped (v15):** viseme mouth system (58 gated drawings across
15 poses); identity-gated pose selection; 21-shot edit at ~1 cut/1.6s;
interaction layer (entrances, exits, vanish/pop, foreshortened head turns,
startle, flinch, reaction cuts); motion SFX verified 6/6 landing; a real
set — one floor line, desk, and a studio TV that the exhibit cards and the
lawmaker caricature play on; Rex taller than Sol; `idle()` breathing
replacing the vibration.

**In flight / next:**

1. **60-second expansion.** Currently 36.2s. Five extra lines were cloned
   locally with Chatterbox as a stopgap while grok-cli was logged out —
   **the owner has since logged in, so regenerate ALL new dialogue with
   grok `sal`/`rex`** and discard the clones so the episode does not
   change narrator halfway through. Files:
   `remotion/public/audio/fairmarket/v11..v15_*.wav`.
2. **The script needs a second ACT, not more lines.** The current piece is
   one reveal stated three ways. What is missing is a turn where Rex acts
   on what he learned and is WRONG — he decides to copy the trades, and
   the disclosure delay means he is always buying old news. That earns the
   closer instead of asserting it.
3. **Wire Rex's calm eyes.** `scripts/vector/calm_eyes.py` has produced
   `rex_calm__*` candidates in `content/.../visemes/calm/`; a gate was
   running when this was written. Vectorise the survivors, register
   `rex_calm` in `pose_anchors.json`, use it as Rex's DEFAULT and keep the
   glint-eyed `rex_eager` only for peak-emotion beats.
4. **Kill the remaining static face-only shots** (Sol's "all legal" CU,
   the "WHAT?!" cover-frame, the exhibit kicker) per the owner rule above.
5. **Known cosmetic gap:** the caricature's line weight is softer than the
   cast — she is base-model output, not the cast LoRA. A small LoRA on her
   drawings would make her and any future politicians a consistent set.

## 6. Related docs

- `CLAUDE.md` §9–10 — the house style for this whole video layer.
- `references/comfyui-local.md` — local generation backend, benchmarks,
  the model-family-switch restart rule, nvidia-smi preflight.
- Memory: `vector-char-pipeline`, `congress-panels`, `comfyui-local-backend`.
