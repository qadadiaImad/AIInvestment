"""Calm Rex down. A/B the Chatterbox delivery controls before regenerating.

THE FINDING THIS ANSWERS. The owner hears Rex as "too high, like a child -
make him a teenager". Measured, that is NOT pitch:

    voice_ref_rex.wav   112.8 Hz      rendered Rex lines   ~121-125 Hz
    voice_ref_sol.wav   132.2 Hz      rendered Sol lines   ~132-137 Hz

Rex's source voice is already the DEEPER of the two, and their brightness
is within 3% of each other (753 vs 733 Hz). Pitch-shifting him down would
therefore not fix the impression and WOULD collapse the only cue that
separates the two speakers.

What differs is delivery: Rex's lines average 1.9-2.8s against Sol's 4.3s,
and most of them end in "!" or "?!". make_all_vo_local.py calls
model.generate(text, audio_prompt_path=...) and nothing else, so every line
ships at Chatterbox's defaults - exaggeration 0.5, cfg_weight 0.5,
temperature 0.8. On short exclamatory text that reads as yelping.

So the knobs, never previously touched:
  exaggeration  emotional intensity      lower = calmer
  cfg_weight    adherence/pacing         lower = slower, less clipped
  temperature   sampling variance        lower = steadier

This renders the same handful of Rex's most excitable lines at several
settings so the owner can HEAR the difference before 24 lines get
regenerated. Same seed everywhere, so the only variable is the setting.

  python scripts/vector/rex_voice_probe.py
Writes  content/probe/rex_voice/<setting>__<stem>.wav  and one A/B reel.
"""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "content/probe/rex_voice"
REF = REPO / "remotion/public/audio/voice_refs/voice_ref_rex.wav"
SEED = 20260804

# his most exclamatory lines - if these read calm, everything else will
LINES = [
    ("fundamentals", "Boss! It's all fundamentals, right?!"),
    ("what", "WHAT?!"),
    ("index", "They made it an INDEX?!"),
    ("copy", "Then I'll just copy them! Buy what they buy!"),
]

# A is today's shipping sound; the rest walk the delivery down
SETTINGS = [
    ("A_current", dict(exaggeration=0.5, cfg_weight=0.5, temperature=0.8)),
    ("B_calmer", dict(exaggeration=0.35, cfg_weight=0.4, temperature=0.7)),
    ("C_teen", dict(exaggeration=0.25, cfg_weight=0.3, temperature=0.65)),
    ("D_flat", dict(exaggeration=0.15, cfg_weight=0.25, temperature=0.6)),
]


def save_pcm16(path: Path, wav, sr: int) -> None:
    """torchaudio defaults to float32 WAV (format tag 3), which the stdlib
    `wave` module refuses and several downstream tools reject outright."""
    import torchaudio
    torchaudio.save(str(path), wav, sr,
                    encoding="PCM_S", bits_per_sample=16)


def pcm16(path: Path):
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(axis=1).astype(np.int16)
    return a, sr


def f0(a: np.ndarray, sr: int):
    x = a.astype(float)
    x /= (np.abs(x).max() or 1)
    hop, win = int(sr * 0.02), int(sr * 0.04)
    lo, hi = int(sr / 350), int(sr / 70)
    out = []
    for i in range(0, len(x) - win, hop):
        s = x[i:i + win]
        if np.sqrt((s ** 2).mean()) < 0.06:
            continue
        s = s - s.mean()
        c = np.correlate(s, s, "full")[win - 1:]
        if c[0] <= 0:
            continue
        seg = c[lo:hi]
        if not len(seg):
            continue
        p = int(np.argmax(seg)) + lo
        if c[p] / c[0] > 0.35:
            out.append(sr / p)
    return float(np.median(out)) if out else 0.0


def main() -> None:
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    OUT.mkdir(parents=True, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("loading chatterbox on " + dev)
    model = ChatterboxTTS.from_pretrained(device=dev)

    rows = []
    for tag, kw in SETTINGS:
        for stem, text in LINES:
            torch.manual_seed(SEED)
            if dev == "cuda":
                torch.cuda.manual_seed_all(SEED)
            np.random.seed(SEED)
            wav = model.generate(text, audio_prompt_path=str(REF), **kw)
            p = OUT / f"{tag}__{stem}.wav"
            save_pcm16(p, wav.cpu(), model.sr)
            a, sr = pcm16(p)
            rows.append({"setting": tag, "line": stem, **kw,
                         "seconds": round(len(a) / sr, 2),
                         "pitch_hz": round(f0(a, sr), 1)})
            print(f"  {tag:10s} {stem:14s} {len(a)/sr:4.1f}s  "
                  f"{rows[-1]['pitch_hz']:5.1f} Hz", flush=True)

    (OUT / "probe.json").write_text(json.dumps(rows, indent=1), "utf-8")

    # one reel: every setting of a line back to back, so the difference is
    # heard rather than read off a table
    reel, sr0 = [], None
    for stem, _ in LINES:
        for tag, _ in SETTINGS:
            a, sr = pcm16(OUT / f"{tag}__{stem}.wav")
            sr0 = sr0 or sr
            reel.append(a)
            reel.append(np.zeros(int(sr * 0.45), dtype=np.int16))
        reel.append(np.zeros(int(sr0 * 0.9), dtype=np.int16))
    out = np.concatenate(reel).astype(np.int16)
    with wave.open(str(OUT / "ab_reel.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr0)
        w.writeframes(out.tobytes())
    print("-> " + str(OUT / "ab_reel.wav"))


if __name__ == "__main__":
    main()
