"""A/B one line with and without its PERFORM tag, at a fixed seed.

The owner hears a stray "T" at the start of some sentences. The prime
suspect is a PERFORM tag being partially VOCALISED rather than interpreted -
"[clear_throat]" is the obvious candidate, since a leaked "th" reads as a
"T". Correlation over the finished episode was inconclusive (ep.1 shows the
same rate of leading bursts and the owner is happy with ep.1), so the only
way to settle it is a controlled generation: identical text, identical
seed, tag toggled.

Writes each variant beside its label so the difference is audible, and
prints the head-of-line envelope so it is also measurable.

  chatterbox-venv/Scripts/python.exe scripts/vector/tag_ab.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import torch
import torchaudio

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "vector"))
OUT = REPO / "content/probe/tag_ab"
REFS = REPO / "remotion/public/audio/voice_refs"
SEED = 1234

CASES = [
    ("clear_throat", "sol", "That's the tower losing its bottom block."),
    ("sigh",         "sol", "Fifteen years, kid."),
    ("whisper",      "sol", "No. It cost you TIME."),
    ("gasp",         "rex", "More than HALF?!"),
]
DELIVERY = {"rex": dict(exaggeration=0.35, cfg_weight=0.4, temperature=0.7),
            "sol": dict(exaggeration=0.5, cfg_weight=0.5, temperature=0.8)}


def head(wav: np.ndarray, sr: int, look=0.6, win=0.01):
    n = int(sr * look)
    d = wav[:n]
    step = max(1, int(sr * win))
    return [float(np.sqrt(np.mean(np.square(d[i:i + step]))))
            for i in range(0, max(1, len(d) - step), step)]


def bars(env):
    pk = max(env) or 1.0
    return "".join("#" if v > pk * 0.30 else ("+" if v > pk * 0.12 else ".")
                   for v in env)


def main() -> None:
    from chatterbox.tts import ChatterboxTTS
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=dev)
    OUT.mkdir(parents=True, exist_ok=True)

    for tag, voice, text in CASES:
        for label, prompt in (("plain", text), (tag, "[%s] %s" % (tag, text))):
            torch.manual_seed(SEED)
            np.random.seed(SEED)
            wav = model.generate(
                prompt,
                audio_prompt_path=str(REFS / ("voice_ref_" + voice + ".wav")),
                **DELIVERY[voice])
            p = OUT / ("%s__%s.wav" % (tag, label))
            torchaudio.save(str(p), wav, model.sr)
            a = wav.squeeze(0).numpy()
            print("%-14s %-14s %5.2fs  %s"
                  % (tag, label, len(a) / model.sr, bars(head(a, model.sr))))
        print()
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
