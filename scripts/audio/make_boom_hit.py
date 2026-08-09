"""Turn the vine boom from a BED into a HIT.

The owner, on the shock take: "some effect voices when he says what there is
a background mp3 that i find toooo much". It is not a mixing complaint, it
is a description of the source file. `vine_boom_bass.wav` is 3.46 seconds
long at RMS 0.71 and it does not decay - its envelope is a flat plateau
above half-peak for ~2.9s and then a cliff. That is a sustained low-frequency
BED, and at 0.30 it runs 1.9 seconds underneath the next beat's dialogue.
Which is exactly what a background mp3 sounds like.

Every other sound in the kit is 0.6-1.0s with a real decay. This one is the
outlier, so the fix is the asset, not the mix.

WHY A NEW FILE. Ep.1 uses vine_boom_bass on its own shock take and the owner
has signed that cut off. Rewriting the original would silently change audio
that is already approved, which is not mine to do. The hit is written beside
it and only the bubbles episode points at the new name.

  python scripts/audio/make_boom_hit.py
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
AUDIO = REPO / "remotion/public/audio"
SRC = AUDIO / "vine_boom_bass.wav"
DST = AUDIO / "vine_boom_hit.wav"

HOLD = 0.09        # seconds at full level - the impact itself
TOTAL = 0.78       # seconds end to end, in family with core (0.70) and whoosh (0.98)
FLOOR_DB = -46.0   # how far down the tail has fallen by TOTAL

# Levelled by RMS, not by peak. Peak-normalising left it at 0.325 RMS - still
# the loudest thing in the kit after the original, and low frequency reads
# louder than its number anyway. The kit sits at 0.11-0.18 (faah 0.113,
# whoosh_fire 0.124, core 0.173); 0.20 keeps the hit the heaviest sound in
# the set without it being in a different weight class.
TARGET_RMS = 0.20
CEILING = 0.95


def read(p: Path):
    with wave.open(str(p)) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768.0
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    return x, sr


def profile(x: np.ndarray, sr: int, label: str) -> None:
    step = max(1, int(sr * 0.05))
    env = np.array([np.sqrt((x[i:i + step] ** 2).mean())
                    for i in range(0, max(1, len(x) - step), step)])
    pk = env.max() or 1.0
    bars = "".join("#" if v > pk * 0.5 else ("+" if v > pk * 0.15 else ".")
                   for v in env)
    print("%-18s %5.2fs  peak %.2f  rms %.4f  |%s|"
          % (label, len(x) / sr, np.abs(x).max(), np.sqrt((x ** 2).mean()), bars))


def main() -> None:
    x, sr = read(SRC)
    profile(x, sr, "source")

    # Start at the transient, not at the file's soft 0.2s ramp-in - an impact
    # that fades in is not an impact.
    onset = int(np.argmax(np.abs(x) > 0.15))
    y = x[onset:onset + int(sr * TOTAL)].copy()

    hold = int(sr * HOLD)
    tail = len(y) - hold
    env = np.ones(len(y))
    if tail > 0:
        # exponential, so the decay sounds like a room letting go rather than
        # like a fader being pulled
        env[hold:] = 10 ** (np.linspace(0, FLOOR_DB / 20.0, tail))
    y *= env

    # a 4ms lift on the very front kills the click from cutting into a
    # non-zero sample
    lift = int(sr * 0.004)
    y[:lift] *= np.linspace(0, 1, lift)

    y *= TARGET_RMS / (np.sqrt((y ** 2).mean()) or 1.0)
    pk = np.abs(y).max()
    if pk > CEILING:                       # keep the transient off the rails
        y *= CEILING / pk
    profile(y, sr, "hit")

    with wave.open(str(DST), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    print("\n-> %s" % DST)
    print("   %.2fs -> %.2fs, rms %.4f -> %.4f"
          % (len(x) / sr, len(y) / sr,
             np.sqrt((x ** 2).mean()), np.sqrt((y ** 2).mean())))


if __name__ == "__main__":
    main()
