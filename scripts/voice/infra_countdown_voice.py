"""Karim VO for the InfraCountdown reel (content/carousel_2026-07-22/INFRA_COUNTDOWN/) —
same canonical voice/engine as scripts/voice/karim_tts.py (course/persona/VOICE.md),
same sample, same seed/exaggeration/cfg_weight, but WITHOUT the halal-card lint gate:
this reel is a general fundamentals comparison, not a halal screen, so the spoken
disclaimer text is a short standalone outro line instead of the halal-specific
"educational, not financial or religious advice" phrase lint_concept_script requires.

Run inside the chatterbox venv (torch + chatterbox-tts installed), NOT the repo python —
see course/persona/VOICE.md "Locked engine" for the venv path.

    <venv-python> scripts/voice/infra_countdown_voice.py

Reads the five .txt scripts in content/carousel_2026-07-22/INFRA_COUNTDOWN/voice/,
generates one WAV per file into remotion/public/audio/infra_countdown/, and writes
durations.json (seconds per clip) so the Remotion side can warn if any clip overruns
its 155-frame (5.1667s) display budget before you flip withVoice:true and re-render.
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

# ticker files -> output basename; OUTRO.txt is the closing disclaimer line
CLIPS = {
    "CIEN": "voice_cien",
    "ANET": "voice_anet",
    "AVGO": "voice_avgo",
    "SMCI": "voice_smci",
    "OUTRO": "voice_outro",
}

BUDGET_S = 155 / 30  # segment HOLD window, must not be exceeded by a ticker clip


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
        flag = "  <-- OVER BUDGET, trim the script" if name != "OUTRO" and dur > BUDGET_S else ""
        print(f"OK {dest.name}  {dur:.2f}s{flag}")

    (OUT_DIR / "durations.json").write_text(json.dumps(durations, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_DIR / 'durations.json'}")
    print("Next: set withVoice: true in remotion/src/fixtures/infra_countdown_2026-07-22.json")
    print("      and re-render: npx remotion render InfraCountdown out.mp4")


if __name__ == "__main__":
    main()
