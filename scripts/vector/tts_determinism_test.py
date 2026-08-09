"""Is a LOCAL clone actually deterministic? Prove it before rebuilding on it.

THE CLAIM being tested: with the model weights and the reference clip
both on disk, and the seed fixed, the same text produces the same voice
every time - so episode 12 can be generated a year from now and still
match episode 1. That is the property grok does not have and cannot be
given, because its identity lives on someone else's server.

THE TEST: generate one identical line three times, then compare.
  * bit-identical output      -> fully deterministic, consistency solved
  * different bytes, same f0  -> stable identity, acceptable
  * different f0              -> the local model drifts too; keep looking

This exists because the last two "fixes" were reasoned about instead of
measured. Pitch normalisation was applied to 70 files on the assumption
that matching median f0 would match the voice - it does not, because
timbre and formants carry identity and neither was touched.

  python scripts/vector/tts_determinism_test.py
"""
from __future__ import annotations

import hashlib
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "content" / "vector_char" / "cast" / "ep_fairmarket" / "tts_test"
REF = REPO / "remotion" / "public" / "audio" / "fairmarket_ep2" / "e3_rex_bullish.wav"
TEXT = "Okay. Big trade. Somebody's feeling bullish."
RUNS = 3
SEED = 1234


def f0_of(path: Path) -> float:
    # Chatterbox writes FLOAT32 wav (format tag 3), which the stdlib wave
    # module refuses outright - a known trap on this project.
    import torchaudio
    t, sr = torchaudio.load(str(path))
    x = t.mean(0).numpy().astype(float)
    v = x[np.abs(x) > 0.015]
    win, hop = int(sr * 0.045), int(sr * 0.0225)
    f0s = []
    for i in range(0, len(v) - win, hop):
        f = (v[i:i + win] - v[i:i + win].mean()) * np.hanning(win)
        if np.sqrt((f ** 2).mean()) < 0.04:
            continue
        ac = np.correlate(f, f, "full")[len(f) - 1:]
        lo, hi = int(sr / 320), int(sr / 70)
        if hi >= len(ac) or ac[lo:hi].max() <= 0.25 * ac[0]:
            continue
        f0s.append(sr / (lo + int(np.argmax(ac[lo:hi]))))
    return float(np.median(f0s)) if f0s else 0.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("device: " + dev)
    if dev == "cuda":
        free, total = torch.cuda.mem_get_info()
        print("vram: %.1f GB free of %.1f GB"
              % (free / 2**30, total / 2**30))
    print("reference: " + REF.name)
    print("text: " + TEXT + "\n")

    model = ChatterboxTTS.from_pretrained(device=dev)
    rows = []
    for i in range(RUNS):
        # fix every source of randomness before each run
        torch.manual_seed(SEED)
        if dev == "cuda":
            torch.cuda.manual_seed_all(SEED)
        np.random.seed(SEED)
        wav = model.generate(TEXT, audio_prompt_path=str(REF))
        p = OUT / ("run%d.wav" % i)
        torchaudio.save(str(p), wav, model.sr)
        digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        rows.append((p, digest, f0_of(p), p.stat().st_size))
        print("run %d  sha %s  f0 %6.1f Hz  %d bytes"
              % (i, digest, rows[-1][2], rows[-1][3]))

    digests = {r[1] for r in rows}
    f0s = [r[2] for r in rows]
    print()
    if len(digests) == 1:
        print("VERDICT: bit-identical across runs. Fully deterministic -")
        print("         a fixed seed + fixed reference + local weights is")
        print("         a voice that cannot drift. Consistency solved.")
    elif max(f0s) - min(f0s) < 3.0:
        print("VERDICT: bytes differ but pitch is stable (spread %.1f Hz)."
              % (max(f0s) - min(f0s)))
        print("         Identity holds; sampling noise only. Acceptable.")
    else:
        print("VERDICT: pitch spread %.1f Hz - this model drifts too."
              % (max(f0s) - min(f0s)))
        print("         Do NOT rebuild on it; try XTTS-v2 or F5-TTS.")
    print("\nfiles in " + str(OUT))


if __name__ == "__main__":
    main()
