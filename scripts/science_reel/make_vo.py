"""Narration for the Science reel — timed to the shot grid, grok TTS (atlas).

Each line lands on its shot's cut. Copy rules: no first person, accusations
attributed ("they say / they call"), no income claims — the story is
accusation -> reveal -> the sciences -> the verdict.

    python scripts/science_reel/make_vo.py

Writes content/probe/science_vo.wav (30.6s, lines placed at offsets) and
prints per-line durations vs their windows so overruns are visible.
"""
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(REPO, "content", "probe", "science_vo")
OUT = os.path.join(REPO, "content", "probe", "science_vo.wav")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")

RATE = 48000
TOTAL_S = 30.6
VOICE = "atlas"

# (start_s, window_s, text)
LINES = [
    (0.0, 3.4, "They say trading isn't a real science."),
    (3.4, 3.4, "They call it gambling. Pure luck."),
    (6.8, 1.7, "Some even call it unethical."),
    (8.6, 1.6, "But here's what it actually runs on."),
    (10.2, 1.7, "Probability."),
    (11.9, 1.7, "Statistics."),
    (13.6, 1.7, "Stochastic calculus."),
    (15.3, 3.4, "The same random walks that move particles... move prices."),
    (18.7, 1.7, "Computer science."),
    (20.4, 1.7, "Algorithms."),
    (22.1, 1.7, "Game theory."),
    (23.8, 1.7, "Machine learning."),
    (25.5, 1.7, "And the science of human behavior."),
    (27.2, 1.8, "It isn't luck. It's mathematics."),
    (29.0, 1.6, "Study the science."),
]


def tts(text, dest):
    p = subprocess.run(
        [CLI, "tts", "--voice-id", VOICE, "--output-format", "wav",
         "--sample-rate", str(RATE), "--output", dest, "--text", text],
        capture_output=True, text=True, timeout=180,
    )
    if p.returncode != 0 or not os.path.exists(dest):
        raise RuntimeError(f"tts failed: {p.stderr[-300:]} {p.stdout[-300:]}")


def load(path):
    with wave.open(path, "rb") as w:
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        ch, sr = w.getnchannels(), w.getframerate()
    x = raw.astype(np.float64).reshape(-1, ch).mean(axis=1) / 32768.0
    if sr != RATE:  # cheap linear resample — narration, not music
        n = int(len(x) * RATE / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    return x


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    buf = np.zeros(int(TOTAL_S * RATE))
    for k, (start, window, text) in enumerate(LINES):
        dest = os.path.join(OUT_DIR, f"line{k:02d}.wav")
        if not os.path.exists(dest):
            tts(text, dest)
        x = load(dest)
        # trim leading/trailing silence below -46 dBFS
        loud = np.where(np.abs(x) > 0.005)[0]
        if len(loud):
            x = x[max(0, loud[0] - 480): loud[-1] + 2400]
        dur = len(x) / RATE
        flag = "OVERRUN" if dur > window + 0.6 else "ok"
        print(f"[{k:02d}] {start:5.1f}s +{dur:4.2f}s (window {window:.1f}s) {flag}  {text}")
        i = int(start * RATE)
        j = min(i + len(x), len(buf))
        buf[i:j] += x[: j - i]

    peak = np.max(np.abs(buf))
    buf *= (10 ** (-1.5 / 20)) / peak
    inter = np.repeat((buf * 32767).astype(np.int16), 2)
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(inter.tobytes())
    print(f"OK {OUT} {TOTAL_S}s peak -1.5 dBFS")


if __name__ == "__main__":
    main()
