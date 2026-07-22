# Generate the Karim VO for InfraCountdown — run this on your laptop

Why here and not in the cloud session: generating audio needs the Chatterbox
voice-clone model, which loads from `huggingface.co` on first run — that host
(and the edge-tts endpoint, checked as a fallback) is blocked by this cloud
sandbox's network policy (confirmed via the proxy's own relay-failure log,
403 on both). Everything else — scripts, timing, the Remotion wiring — is
already done and pushed; this is the one step that has to happen locally.

## 0. One-time setup (skip if you already have the chatterbox venv)

Per `course/persona/VOICE.md`, the canonical venv lives at
`C:\Users\Amsegt\.venvs\chatterbox`. If it doesn't exist yet:

```
python -m venv C:\Users\Amsegt\.venvs\chatterbox
C:\Users\Amsegt\.venvs\chatterbox\Scripts\pip install torch chatterbox-tts torchaudio
```

(First run of the generator below also downloads the Chatterbox base model
from Hugging Face — a few hundred MB — that's the part that can't happen in
the cloud session.)

## 1. Pull the latest branch

```
git checkout claude/refresh-data-import-stock-story-svya0l
git pull
```

## 2. Generate the 5 clips

Run from the repo root, using the **chatterbox venv's** Python (not your
system Python — it needs `torch` + `chatterbox-tts` installed):

```
C:\Users\Amsegt\.venvs\chatterbox\Scripts\python.exe scripts\voice\infra_countdown_voice.py
```

This reuses the exact same voice, seed, and delivery settings as the rest of
the channel (`course/persona/voice/karim_sample.wav`, seed 7, exaggeration
0.4, cfg_weight 0.5 — see `VOICE.md`), but skips the halal-card lint gate
since this reel isn't a halal screen.

It writes:
```
remotion/public/audio/infra_countdown/voice_cien.wav
remotion/public/audio/infra_countdown/voice_anet.wav
remotion/public/audio/infra_countdown/voice_avgo.wav
remotion/public/audio/infra_countdown/voice_smci.wav
remotion/public/audio/infra_countdown/voice_outro.wav
remotion/public/audio/infra_countdown/durations.json
```

**Check the console output** — it prints each clip's actual duration and
flags any ticker clip that runs past its 5.1667s (155-frame) on-screen
window with `<-- OVER BUDGET, trim the script`. If that happens, shorten the
matching `.txt` file in `voice/` and re-run.

The five scripts being spoken (edit these `.txt` files directly if you want
different wording, then re-run step 2):

| File | Text |
|---|---|
| `voice/CIEN.txt` | Ciena builds the optical networks moving data across the world's data centers. |
| `voice/ANET.txt` | Arista builds the high speed switches inside the world's biggest data centers. |
| `voice/AVGO.txt` | Broadcom designs custom chips and networking silicon for the largest cloud providers. |
| `voice/SMCI.txt` | Super Micro builds the servers that pack AI chips into deployable racks. |
| `voice/OUTRO.txt` | Educational commentary only — not financial advice. |

## 3. Enable the voice track and re-render

Open `remotion/src/fixtures/infra_countdown_2026-07-22.json` and change:
```
"withVoice": false,
```
to:
```
"withVoice": true,
```

Then, from `remotion/`:
```
npm install          # first time only
npx remotion render InfraCountdown ../content/carousel_2026-07-22/INFRA_COUNTDOWN/infra_countdown_voiced.mp4
```

## 4. Push it back

```
git add remotion/public/audio/infra_countdown remotion/src/fixtures/infra_countdown_2026-07-22.json content/carousel_2026-07-22/INFRA_COUNTDOWN/infra_countdown_voiced.mp4
git commit -m "feat(infra-countdown): add Karim voiceover"
git push
```

Or just hand the five `.wav` files (or the finished render) back to this
session and it'll be finished and committed from here.
