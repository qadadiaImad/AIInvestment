"""Confirm each motion SFX actually lands on the frame it was scheduled.

An <Audio> that fails to resolve still renders a perfectly valid file, so
"it rendered" proves nothing. This measures the energy in a short window
around every scheduled hit in the new cut and compares it with the same
window in the previous cut, which had no effects — a hit that landed
shows up as a jump the silent version does not have.

Usage:  python scripts/audio/check_sfx_landed.py <before.wav> <after.wav>
"""
import sys
import wave

import numpy as np

RATE = 48000
FPS = 30

# (frame the sound should land on, label)
HITS = [
    (124, "b110 whip  (Rex turns to Sol)"),
    (213, "b195 whip  (Rex flinches)"),
    (259, "b255 whoosh (Sol slides in)"),
    (878, "b740 poof  (Sol vanishes)"),
    (947, "b895 pop   (Sol pops in)"),
    (955, "b895 whip  (Rex turns)"),
]


def load(path):
    w = wave.open(path)
    n = w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    if w.getnchannels() == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    return x


def rms(x, f0, f1):
    a, b = int(f0 / FPS * RATE), int(f1 / FPS * RATE)
    seg = x[max(0, a):min(len(x), b)]
    return float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0


def main(before_path, after_path):
    before, after = load(before_path), load(after_path)
    print(f"{'hit':34s} {'before':>8s} {'after':>8s} {'ratio':>7s}  verdict")
    ok = 0
    for f, label in HITS:
        b = rms(before, f, f + 8)
        a = rms(after, f, f + 8)
        ratio = a / max(1e-6, b)
        landed = ratio > 1.15 or (b < 0.002 and a > 0.005)
        ok += landed
        print(f"{label:34s} {b:8.4f} {a:8.4f} {ratio:7.2f}  "
              f"{'LANDED' if landed else 'NOT AUDIBLE'}")
    print(f"\n{ok}/{len(HITS)} hits landed")
    return 0 if ok == len(HITS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
