---
name: expressive-voiceover
description: >
  Generate natural, non-robotic reel voiceover with Chatterbox (Resemble AI, MIT) instead of
  flat parametric TTS. Core technique = PER-SENTENCE inflection: split each VO line into
  sentences, synthesize each with its own emotion/pacing (questions rise, number/reveal beats
  punch, trailing "…" thoughts soften) + a deterministic wiggle so no two neighbours match,
  then stitch with natural pauses — the cadence of a person explaining, not a monotone read.
  Includes the exact isolated-env setup on this machine. Use whenever generating or
  regenerating episode VO. Reference impl: halal-reels/gen_debt_chatterbox.py.
---

# Expressive Voiceover — Chatterbox, per-sentence inflection

**Why:** edge-tts / parametric neural voices are clean but emotionally flat — the owner calls it
"monotone… AI slop," and no rate/pitch tuning escapes it. **Chatterbox** (Resemble AI, MIT) is an
expressive autoregressive TTS (beat ElevenLabs in blind tests) that actually inflects and breathes.
Free, local. **Reproduce a STYLE, never clone a real identifiable narrator** (no Steve Taylor clips).

## Environment (hard-won — this machine)

No standalone torch (system python 3.14 has no wheels). Use ComfyUI's embedded python (3.13 + torch/CUDA):
`/c/Users/Amsegt/comfy/ComfyUI_windows_portable/python_embeded/python.exe`.

One-time install into an ISOLATED dir (keeps ComfyUI's stack clean):
```
$PYEMB -m pip install --target=C:\Users\Amsegt\chatterbox_env chatterbox-tts
$PYEMB -m pip install --target=C:\Users\Amsegt\chatterbox_env "setuptools<81"
```
Two gotchas the script must handle at runtime (see reference impl):
- **Strip ComfyUI's site-packages from `sys.path`**, keep stdlib, prepend the target dir — else its
  torch 2.13/cu130 torchvision clashes with the isolated CPU torch 2.6 → `torchvision::nms does not exist`.
- **`setuptools<81`** provides `pkg_resources`; without it the Perth watermarker silently becomes
  `None` → `TypeError: 'NoneType' object is not callable` on model load.

Run: `$PYEMB -s -E gen_<ep>_chatterbox.py` (CPU inference; a few min for a full episode).

## The technique (what makes it sound human)

1. **Split each line into sentences on TRUE enders ONLY** — `. ? !`, **never on `…` or `,`**
   (`re.findall(r"[^.?!]+[.?!]+|[^.?!]+$", text)`). This is critical: `…` is a *pause inside one
   thought*, not a sentence break. Splitting on it renders "That's just… renting it." as two
   disconnected fragments — the classic non-human artifact. Keep the clause whole.
2. **Normalize for synthesis** — replace `…` with a comma (`tts_norm`): Chatterbox reads a comma as a
   smooth in-clause pause, and the unicode `…` tends to be mishandled/over-clipped. Captions keep the
   original `…`; only the audio input is normalized (word tokens still match 1:1).
3. **Give each sentence its own inflection** via `style(sentence, i)` → `(exaggeration, cfg_weight, pause)`:

   | sentence type | exaggeration | cfg_weight | pause after |
   |---|---|---|---|
   | ends `?` (question) | ~0.70 (rises) | 0.40 (expressive) | 0.30s |
   | contains a number / "trillion/billion/hundred" | ~0.64 (punch) | 0.45 | 0.26s |
   | default | ~0.52 | 0.50 | 0.24s |

   Add a **deterministic ±0.06 wiggle** (`((i*37)%7-3)*0.02`) so adjacent sentences never share a
   contour — that variation is the "someone talking" feel. Clamp to [0.4, 0.8].
4. **Generate, then smooth the join** — `model.generate(tts_norm(s), …)`, then **level** each clip
   (peak-normalize to ~0.92 so stitched sentences don't jump in volume) and apply **8ms in/out fades**
   (so joins don't click). Stitch with `torch.zeros(1, int(sr*pause))` silence, `torch.cat(…, dim=1)`,
   save one `.wav` per line.
5. **Word timing:** Chatterbox emits no word boundaries → distribute each sentence's words
   proportionally within its known [start,end] window in the stitched timeline. Write
   `<ep>_captions.json` ({text, words:[{w,t0,t1}], dur, frames}) for the karaoke captions.

## Script cadence (write for the voice)

Short, wondering sentences. Rhetorical questions ("who on Earth…?"). `…` for a beat of suspense.
Front-load the number, then the payoff. More sentence boundaries = more inflection resets = less flat.
This is the Kurzgesagt / "In a Nutshell" shape — reproduce the *feel*, don't clone the narrator.

## Integration & dials

- The episode timeline must be **data-driven from caption durations** (`F(id)=dur*30`) so re-generating
  the VO re-times every beat automatically (see the `newsroom-reel` skill).
- Tune in `style()`: bigger question rise → raise exaggeration; more dramatic → longer `…` pause;
  punchier numbers → raise the numeric-branch exaggeration.
- **British/other accent:** clone from a ~10s **royalty-free** reference clip via `audio_prompt_path`
  (a generic narrator sample, never a real identifiable person).
- Output is `.wav` (24kHz); Remotion `<Audio>` plays it directly — reference `public/<ep>_dN.wav`.
