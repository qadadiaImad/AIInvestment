"""Find the fastest delivery that is still intelligible, and prove it.

The owner, on the Shorts cut: "stack more information and maybe speed up
prononciation". Speeding up a TTS voice has an obvious failure mode - it
slurs - and "sounds fine to me" is not a gate, so this measures both halves:

  SPEED         syllables per second of actual audio
  INTELLIGIBLE  faster-whisper transcribes it back, word error rate vs the
                text that went in

A setting only wins if it is faster AND transcribes clean. Without the
second half this script would happily recommend the setting that produces
the fastest mush.

WHY NOT TIME-STRETCH THE FINISHED AUDIO. WSOLA smears speech and leaves a
metallic edge - that is written down in make_all_vo_local.py as the reason
pitch correction was turned off by default. Asking the model to speak faster
is not the same operation as playing a recording faster.

  <chatterbox-venv-python> scripts/vector/pace_ab.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import torch
import torchaudio

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "vector"))
OUT = REPO / "content/probe/pace_ab"
REFS = REPO / "remotion/public/audio/voice_refs"
SEED = 1234

# cfg_weight is the pacing control in Chatterbox; exaggeration is held at the
# per-voice value the owner already picked so this measures ONE variable.
SWEEP = [0.20, 0.30, 0.40, 0.50]
BASE = {"rex": dict(exaggeration=0.35, temperature=0.7),
        "sol": dict(exaggeration=0.5, temperature=0.8)}

# Representative of what the short actually says: a long informational line
# and a short reaction, per voice.
CASES = [
    ("sol", "The last bubble took fifteen years to get back to even."),
    ("sol", "Four parts. No villain. Every single time."),
    ("rex", "Fifteen YEARS?!"),
    ("rex", "So who's the villain?"),
]

VOWELS = re.compile(r"[aeiouy]+", re.I)


def syllables(text: str) -> int:
    """Crude but consistent - only used to compare settings with each other."""
    n = 0
    for w in re.findall(r"[A-Za-z']+", text):
        g = len(VOWELS.findall(w))
        if w.lower().endswith("e") and g > 1:
            g -= 1
        n += max(1, g)
    return n


def norm(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def wer(ref: str, hyp: str) -> float:
    """Levenshtein over words, normalised by reference length."""
    a, b = norm(ref), norm(hyp)
    if not a:
        return 0.0
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[len(b)] / len(a)


def main() -> None:
    from chatterbox.tts import ChatterboxTTS
    from faster_whisper import WhisperModel

    OUT.mkdir(parents=True, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tts = ChatterboxTTS.from_pretrained(device=dev)
    stt = WhisperModel("small.en", compute_type="int8")

    rows = {}
    for cfg in SWEEP:
        tot_syl = tot_sec = 0.0
        werr = []
        for voice, text in CASES:
            torch.manual_seed(SEED)
            if dev == "cuda":
                torch.cuda.manual_seed_all(SEED)
            np.random.seed(SEED)
            wav = tts.generate(text,
                               audio_prompt_path=str(REFS / ("voice_ref_" + voice + ".wav")),
                               cfg_weight=cfg, **BASE[voice])
            p = OUT / ("cfg%02d_%s_%s.wav" % (int(cfg * 100), voice, text[:14]
                                              .strip().replace(" ", "_").replace("?", "")))
            torchaudio.save(str(p), wav, tts.sr)
            secs = wav.shape[-1] / tts.sr
            segs, _ = stt.transcribe(str(p), beam_size=5)
            hyp = " ".join(s.text for s in segs)
            e = wer(text, hyp)
            werr.append(e)
            tot_syl += syllables(text)
            tot_sec += secs
            print("  cfg %.2f  %-3s  %5.2fs  %4.1f syl/s  wer %.2f  | %s"
                  % (cfg, voice, secs, syllables(text) / secs, e, hyp.strip()[:52]))
        rows[cfg] = (tot_syl / tot_sec, float(np.mean(werr)), float(np.max(werr)))
        print("  cfg %.2f  ==> %.2f syl/s overall, mean wer %.3f, worst %.3f\n"
              % (cfg, *rows[cfg]))

    print("%-6s %10s %9s %9s" % ("cfg", "syl/s", "mean wer", "worst"))
    for cfg, (sps, mw, xw) in rows.items():
        print("%-6.2f %10.2f %9.3f %9.3f%s"
              % (cfg, sps, mw, xw, "   <-- slurs" if xw > 0.15 else ""))
    ok = [(sps, cfg) for cfg, (sps, mw, xw) in rows.items() if xw <= 0.15]
    if ok:
        best = max(ok)
        base = rows[0.50][0]
        print("\nfastest setting that still transcribes clean: cfg_weight=%.2f "
              "at %.2f syl/s (%+.0f%% vs cfg 0.50)"
              % (best[1], best[0], 100 * (best[0] / base - 1)))
    else:
        print("\nno setting cleared the intelligibility gate - do not speed up")
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
