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
remotion/public/audio/infra_countdown/voice_intro.wav
remotion/public/audio/infra_countdown/voice_cien.wav
remotion/public/audio/infra_countdown/voice_anet.wav
remotion/public/audio/infra_countdown/voice_avgo.wav
remotion/public/audio/infra_countdown/voice_smci.wav
remotion/public/audio/infra_countdown/voice_outro.wav
remotion/public/audio/infra_countdown/durations.json
```

**Check the console output** — it prints each clip's actual duration and
flags any clip that runs past its own on-screen/timing budget with
`<-- OVER BUDGET, trim the script`. Budgets differ per clip (see the
docstring in `scripts/voice/infra_countdown_voice.py`) because Chatterbox has
a ~2-3s fixed floor per utterance regardless of word count — a bare 4-word
intro line still costs ~3s, too long to fit inside the 70-frame intro card on
its own. If a clip trips the flag, shorten the matching `.txt` file in
`voice/` and re-run; if it's INTRO or CIEN specifically, also re-check
`TICKER0_VO_DELAY` in `InfraCountdown.tsx` (see its comment) since the two
are timed to hand off to each other without overlapping.

The six scripts being spoken (edit these `.txt` files directly if you want
different wording, then re-run step 2):

| File | Text |
|---|---|
| `voice/INTRO.txt` | Same sector wildly different prices |
| `voice/CIEN.txt` | Ciena builds optical networks for data centers, priced well above fair value. |
| `voice/ANET.txt` | Arista builds switches for AI data centers, still trading above fair value. |
| `voice/AVGO.txt` | Broadcom designs chips for major clouds, priced above fair value. |
| `voice/SMCI.txt` | Super Micro builds AI servers, and trades well below fair value. |
| `voice/OUTRO.txt` | Super Micro trades far below fair value — the one worth watching. |

No spoken disclaimer line (owner direction 2026-07-22) — the on-screen footer
("Figures as of July 11, 2026 — educational, not financial advice") renders
for the whole video already, so the outro line instead calls back to the
winner (SMCI) and why it stood out.

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
