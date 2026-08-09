"""Generate a few lines on the LOCAL clone and measure consistency.

Gate before rebuilding all 70. Two things have to hold:

  1. CONSISTENCY - the same character's pitch must not wander line to
     line. That is the whole reason for moving off grok.
  2. STABILITY WITHIN A LINE - the first Chatterbox attempt on this
     project wobbled mid-sentence, which is why the project left it. A
     20-second reference should fix that; this measures whether it did,
     by reporting the spread of per-frame pitch INSIDE each line rather
     than only its median.

  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe \
      scripts/vector/tts_local_test.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
REFS = REPO / "remotion" / "public" / "audio" / "voice_refs"
OUT = REPO / "content" / "vector_char" / "cast" / "ep_fairmarket" / "tts_test"
SEED = 1234

LINES = [
    ("rex", "t1_rex", "Boss! It's all fundamentals, right?!"),
    ("rex", "t2_rex", "One trade. One person. That's a coincidence, boss, not a strategy."),
    ("sol", "t3_sol", "Kid... let me tell you about the so-called fair market."),
    ("sol", "t4_sol", "The filing tells you what they bought. It never tells you what they knew, or when."),
]


def frame_f0(x: np.ndarray, sr: int):
    v = x[np.abs(x) > 0.015]
    win, hop = int(sr * 0.045), int(sr * 0.0225)
    out = []
    for i in range(0, len(v) - win, hop):
        f = (v[i:i + win] - v[i:i + win].mean()) * np.hanning(win)
        if np.sqrt((f ** 2).mean()) < 0.04:
            continue
        ac = np.correlate(f, f, "full")[len(f) - 1:]
        lo, hi = int(sr / 320), int(sr / 70)
        if hi >= len(ac) or ac[lo:hi].max() <= 0.25 * ac[0]:
            continue
        out.append(sr / (lo + int(np.argmax(ac[lo:hi]))))
    return np.array(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=dev)
    print("\n%-8s %-9s %8s %10s %s" % ("voice", "file", "median", "in-line", "text"))
    print("%-8s %-9s %8s %10s" % ("", "", "f0", "spread"))
    by_voice = {}
    for voice, stem, text in LINES:
        torch.manual_seed(SEED)
        if dev == "cuda":
            torch.cuda.manual_seed_all(SEED)
        np.random.seed(SEED)
        wav = model.generate(text,
                             audio_prompt_path=str(REFS / ("voice_ref_" + voice + ".wav")))
        p = OUT / (stem + ".wav")
        torchaudio.save(str(p), wav, model.sr)
        t, sr = torchaudio.load(str(p))
        f = frame_f0(t.mean(0).numpy().astype(float), sr)
        med = float(np.median(f)) if len(f) else 0.0
        # interquartile spread = how much the pitch moves INSIDE the line
        iqr = float(np.percentile(f, 75) - np.percentile(f, 25)) if len(f) else 0.0
        by_voice.setdefault(voice, []).append(med)
        print("%-8s %-9s %7.1fHz %9.1fHz  %s" % (voice, stem, med, iqr, text[:44]))
    print()
    for v, meds in by_voice.items():
        spread = max(meds) - min(meds)
        verdict = "CONSISTENT" if spread < 6 else "DRIFTS - not usable"
        print("%s: line-to-line spread %.1f Hz  -> %s" % (v.upper(), spread, verdict))
    print("\nfiles in " + str(OUT))


if __name__ == "__main__":
    main()
