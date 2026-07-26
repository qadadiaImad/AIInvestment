"""Synthesise a mechanical clock tick for the quiz countdown.

Written in plain Python rather than shelled out to ffmpeg because the ffmpeg
bundled with Remotion's compositor is a minimal build with no highpass/lowpass
filters, and a tick without filtering is either a beep (pure sine) or a hiss
(pure noise).

A real escapement tick is two events a few milliseconds apart: the pallet
releasing and the tooth landing. Reproducing that double-transient is what makes
it read as a clock rather than a UI blip. Each transient is band-limited noise
with a fast exponential decay plus a damped resonance at the case frequency.

Tick and tock differ in pitch — a clock alternates, and five identical ticks in
a row sound like a metronome instead.

Usage:
    python scripts/audio/make_tick.py
"""
import math
import os
import random
import struct
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "audio")

RATE = 48000


def one_pole_hp(xs, cutoff):
    """Cheap first-order high-pass — enough to take the mud out of the noise."""
    a = math.exp(-2 * math.pi * cutoff / RATE)
    out, prev_x, prev_y = [], 0.0, 0.0
    for x in xs:
        y = a * (prev_y + x - prev_x)
        out.append(y)
        prev_x, prev_y = x, y
    return out


def one_pole_lp(xs, cutoff):
    a = math.exp(-2 * math.pi * cutoff / RATE)
    out, prev = [], 0.0
    for x in xs:
        prev = (1 - a) * x + a * prev
        out.append(prev)
    return out


def transient(rng, n, decay, resonance, res_amp):
    """One click: band-limited noise burst + a damped resonance."""
    noise = [rng.uniform(-1, 1) for _ in range(n)]
    noise = one_pole_lp(one_pole_hp(noise, 900), 7000)
    out = []
    for i, v in enumerate(noise):
        env = math.exp(-i / (RATE * decay))
        res = math.sin(2 * math.pi * resonance * i / RATE) * math.exp(-i / (RATE * decay * 0.7))
        out.append((v * 0.85 + res * res_amp) * env)
    return out


def build(seed, pitch):
    """A tick is two transients ~7ms apart, not one."""
    rng = random.Random(seed)
    n = int(RATE * 0.13)
    a = transient(rng, n, 0.014, 2300 * pitch, 0.30)
    b = transient(rng, n, 0.026, 1450 * pitch, 0.42)
    gap = int(RATE * 0.007)
    out = [0.0] * n
    for i, v in enumerate(a):
        out[i] += v * 0.75
    for i, v in enumerate(b):
        if i + gap < n:
            out[i + gap] += v
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.82 for v in out]


def write(path, samples):
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = b"".join(
            struct.pack("<hh", int(max(-1, min(1, s)) * 32767), int(max(-1, min(1, s)) * 32767))
            for s in samples
        )
        w.writeframes(frames)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, seed, pitch in [("tick.wav", 7, 1.0), ("tock.wav", 21, 0.86)]:
        s = build(seed, pitch)
        p = os.path.join(OUT, name)
        write(p, s)
        print(f"{name}: {len(s)} samples, {len(s)/RATE*1000:.0f} ms -> {os.path.relpath(p, REPO)}")


if __name__ == "__main__":
    main()
