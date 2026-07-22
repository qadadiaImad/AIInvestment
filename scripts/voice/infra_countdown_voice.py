"""Karim VO for the InfraCountdown reel (content/carousel_2026-07-22/INFRA_COUNTDOWN/) —
same canonical voice/engine as scripts/voice/karim_tts.py (course/persona/VOICE.md),
same sample, same seed/exaggeration/cfg_weight, but WITHOUT the halal-card lint gate:
this reel is a general fundamentals comparison, not a halal screen, so there's no
lint_concept_script call. The spoken outro line calls out the winner (SMCI) rather
than reading a disclaimer — the on-screen footer ("...educational, not financial
advice") renders for the whole video already, per owner direction 2026-07-22.

Run inside the chatterbox venv (torch + chatterbox-tts installed), NOT the repo python —
see course/persona/VOICE.md "Locked engine" for the venv path.

    <venv-python> scripts/voice/infra_countdown_voice.py

Reads the six .txt scripts in content/carousel_2026-07-22/INFRA_COUNTDOWN/voice/,
generates one WAV per file into remotion/public/audio/infra_countdown/, and writes
durations.json (seconds per clip) so the Remotion side can warn if any clip overruns
its display budget before you flip withVoice:true and re-render.

Per-clip budgets (see InfraCountdown.tsx timing constants — INTRO_END=70,
SEGMENT_LEN=200, COLLAPSE_START=155, COLLAPSE_LEN=40, so a ticker card is still
legible through local frame 195, not just the 155-frame hold). Chatterbox has a
~2-3s fixed per-utterance floor regardless of word count, so the INTRO line
can't fit inside the 70-frame intro card alone — it plays under the intro card
AND the first ticker's entrance, and CIEN's own VO is delayed to start right
after it (see TICKER0_VO_DELAY in InfraCountdown.tsx). Its budget below is
sized so that delay still leaves CIEN's clip finishing before ANET's segment
(and ANET's own VO) begins at frame 270 — re-check that constant if this
clip's measured duration or CIEN's script length changes:
  INTRO  — must land CIEN's delayed VO start early enough to finish by ~267: 92f
  ticker — card fades out by local frame 195, next segment starts at 200 (5f buffer): 185f
  OUTRO  — OUTRO_VO_DELAY (832, right after SMCI's line) to durationInFrames,
           minus a 15f tail buffer before the hard cut: 208f
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "course/persona/voice/karim_sample.wav"
SCRIPT_DIR = ROOT / "content/carousel_2026-07-22/INFRA_COUNTDOWN/voice"
OUT_DIR = ROOT / "remotion/public/audio/infra_countdown"
SEED = 7
EXAGGERATION = 0.4  # calm educator — same as VOICE.md canon
CFG_WEIGHT = 0.5

# script files -> output basename
CLIPS = {
    "INTRO": "voice_intro",
    "CIEN": "voice_cien",
    "ANET": "voice_anet",
    "AVGO": "voice_avgo",
    "SMCI": "voice_smci",
    "OUTRO": "voice_outro",
}

# per-clip budget in seconds (frame windows above, /30fps)
CLIP_BUDGETS_S = {
    "INTRO": 92 / 30,
    "CIEN": 185 / 30,
    "ANET": 185 / 30,
    "AVGO": 185 / 30,
    "SMCI": 185 / 30,
    "OUTRO": 208 / 30,
}


def wav_duration_s(path: pathlib.Path) -> float:
    # torchaudio.save writes 32-bit float PCM (format tag 3), which the stdlib
    # `wave` module can't parse — use torchaudio's own reader instead.
    import torchaudio

    info = torchaudio.info(str(path))
    return info.num_frames / info.sample_rate


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit(f"canonical sample missing: {SAMPLE}")
    missing = [name for name in CLIPS if not (SCRIPT_DIR / f"{name}.txt").exists()]
    if missing:
        raise SystemExit(f"missing script file(s): {missing}")

    import torch
    import torchaudio

    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading Chatterbox on {device} (first run downloads the model)...")
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    durations: dict[str, float] = {}
    for i, (name, out_base) in enumerate(CLIPS.items()):
        text = (SCRIPT_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()
        torch.manual_seed(SEED + i)
        wav = model.generate(
            text,
            audio_prompt_path=str(SAMPLE),
            exaggeration=EXAGGERATION,
            cfg_weight=CFG_WEIGHT,
        )
        audio = wav.cpu() if hasattr(wav, "cpu") else wav
        dest = OUT_DIR / f"{out_base}.wav"
        torchaudio.save(str(dest), audio, sr)
        dur = wav_duration_s(dest)
        durations[out_base] = round(dur, 3)
        budget = CLIP_BUDGETS_S[name]
        flag = f"  <-- OVER BUDGET ({budget:.2f}s), trim the script" if dur > budget else ""
        print(f"OK {dest.name}  {dur:.2f}s{flag}")

    (OUT_DIR / "durations.json").write_text(json.dumps(durations, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_DIR / 'durations.json'}")
    print("Next: set withVoice: true in remotion/src/fixtures/infra_countdown_2026-07-22.json")
    print("      and re-render: npx remotion render InfraCountdown out.mp4")


if __name__ == "__main__":
    main()
