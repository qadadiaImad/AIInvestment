"""Synthesise a phonk bed for the Habits reel — fully in Python.

No music-generation service is reachable from this environment (Higgsfield
audio is speech-only, grok-cli is TTS-only), and rule 10.4 already puts reel
sound in Python. Side benefit: a synthesized bed is license-free.

The tempo is chosen so the music grid IS the cut grid: 141.176 BPM makes one
4/4 bar exactly 1.7 s — one cut unit — so all 18 bars land every cut on a
downbeat and the total is 30.6 s to the sample.

Sections mirror the shot arc (bar index = cut unit index):
  bars 0-1   Maya doubt      hiss + low-passed cowbell, snare-roll build
  bars 2-3   hook            drop 1: full kit + sub 808
  bars 4-9   habit stills    groove, riff variants alternating
  bars 10-11 rain interrupt  breakdown: no drums, dark riff + drone + riser
  bars 12-16 payoff          drop 2: octave cowbell layer + open hats
  bar  17    ender           half-time, low-pass sweep down; loops into bar 0

Usage:
    python scripts/audio/make_phonk.py
Writes content/probe/phonk_bed.wav (48 kHz stereo 16-bit) and prints
peak/RMS so the result is verifiable without ears.
"""
import os
import struct
import wave

import numpy as np
from scipy.signal import butter, lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "content", "probe", "phonk_bed.wav")

RATE = 48000
BAR = 1.7                 # seconds — one cut unit of the reel
BARS = 18
S16 = BAR / 16            # one sixteenth note
TOTAL = int(round(BARS * BAR * RATE))  # 1_468_800 samples = 30.6 s

D4 = 293.66               # riff root; sub bass plays 3 octaves down


def t(n):
    return np.arange(n) / RATE


def env_exp(n, decay):
    return np.exp(-t(n) / decay)


def bp(x, lo, hi):
    b, a = butter(2, [lo / (RATE / 2), hi / (RATE / 2)], btype="band")
    return lfilter(b, a, x)


def lp(x, cut):
    b, a = butter(2, cut / (RATE / 2), btype="low")
    return lfilter(b, a, x)


def hp(x, cut):
    b, a = butter(2, cut / (RATE / 2), btype="high")
    return lfilter(b, a, x)


def cowbell(freq, dur=0.22, bright=1.0):
    """808 cowbell: two square partials (540:800 ratio), band-passed pluck."""
    n = int(dur * RATE)
    r1, r2 = freq, freq * 800.0 / 540.0
    x = np.sign(np.sin(2 * np.pi * r1 * t(n))) + np.sign(np.sin(2 * np.pi * r2 * t(n)))
    x = bp(x, r1 * 0.8, r2 * 4.0 * bright)
    return x * env_exp(n, 0.055) * 0.5


def sub808(freq, dur, drive=2.2):
    """Sine sub with a 30 ms pitch drop and tanh saturation for harmonics."""
    n = int(dur * RATE)
    tt = t(n)
    glide = freq * (1 + 0.6 * np.exp(-tt / 0.03))
    ph = 2 * np.pi * np.cumsum(glide) / RATE
    x = np.tanh(np.sin(ph) * drive) * env_exp(n, dur * 0.55)
    return x * 0.9


def kick():
    n = int(0.28 * RATE)
    tt = t(n)
    f = 45 + 110 * np.exp(-tt / 0.045)
    body = np.sin(2 * np.pi * np.cumsum(f) / RATE) * env_exp(n, 0.09)
    click = hp(np.random.default_rng(7).standard_normal(n), 2500) * env_exp(n, 0.004) * 0.5
    return np.tanh((body + click) * 1.8) * 0.95


def snare(rng):
    n = int(0.22 * RATE)
    noise = bp(rng.standard_normal(n), 900, 7500)
    x = np.zeros(n)
    for k, (d, g) in enumerate([(0.0, 1.0), (0.011, 0.7), (0.021, 0.5)]):  # clap spread
        i = int(d * RATE)
        x[i:] += noise[: n - i] * g * env_exp(n - i, 0.045)
    body = np.sin(2 * np.pi * 185 * t(n)) * env_exp(n, 0.05) * 0.4
    return (x * 0.6 + body) * 0.9


def hat(rng, open_=False):
    dur = 0.16 if open_ else 0.045
    n = int(dur * RATE)
    return hp(rng.standard_normal(n), 8000) * env_exp(n, dur * 0.4) * (0.32 if open_ else 0.38)


def impact(rng):
    """Downbeat hit: noise crash + low boom, for the two drops."""
    n = int(0.9 * RATE)
    crash = hp(rng.standard_normal(n), 3000) * env_exp(n, 0.22) * 0.5
    boom = np.sin(2 * np.pi * 55 * t(n)) * env_exp(n, 0.3) * 0.7
    return crash + boom


def riser(dur):
    """Noise sweep with rising high-pass — tension into a drop."""
    n = int(dur * RATE)
    x = np.random.default_rng(11).standard_normal(n)
    out = np.zeros(n)
    steps = 24
    for k in range(steps):
        a, b_ = k * n // steps, (k + 1) * n // steps
        out[a:b_] = hp(x[a:b_], 300 + 6000 * (k / steps))[: b_ - a]
    return out * np.linspace(0.05, 0.55, n) ** 1.5


NOTE = {"D": 0, "C": -2, "Bb": -4, "A": -5, "F": 3, "G": 5}


def hz(name, oct_shift=0):
    return D4 * (2 ** ((NOTE[name] + 12 * oct_shift) / 12))


# One-bar riffs as (sixteenth index, note) — classic syncopated phonk cowbell.
RIFF_A = [(0, "D"), (2, "D"), (3, "F"), (5, "D"), (7, "C"), (8, "D"), (10, "A"), (12, "C"), (14, "D")]
RIFF_B = [(0, "D"), (2, "D"), (3, "F"), (5, "G"), (7, "F"), (8, "D"), (10, "C"), (12, "A"), (14, "C")]
BASS_ROOTS = ["D", "D", "Bb", "C"]  # i-i-VI-VII per 4-bar loop, 3 octaves down
KICKS = [0, 7, 10]
SNARES = [4, 12]


def add(buf, start_s, x, gain=1.0):
    i = int(round(start_s * RATE))
    j = min(i + len(x), TOTAL)
    if i < TOTAL:
        buf[i:j] += x[: j - i] * gain


def main():
    rng = np.random.default_rng(42)
    mel = np.zeros(TOTAL)   # cowbell + pads (gets low-passed per section)
    drums = np.zeros(TOTAL)
    bass = np.zeros(TOTAL)

    full_bars = set(range(2, 10)) | set(range(12, 17))
    for bar in range(BARS):
        t0 = bar * BAR
        riff = RIFF_A if bar % 2 == 0 else RIFF_B

        dark = bar in (0, 1, 10, 11)
        half_time = bar == 17
        if not (bar in (10, 11) and False):
            for idx, name in riff:
                if dark and idx % 2 == 1:
                    continue  # thin the riff in dark sections
                note = cowbell(hz(name), bright=0.5 if dark else 1.0)
                add(mel, t0 + idx * S16, note, 0.8 if not dark else 0.55)
                if bar in range(12, 17):  # payoff: quiet octave-up layer
                    add(mel, t0 + idx * S16 + 0.008, cowbell(hz(name, 1), dur=0.15), 0.25)

        if bar in full_bars or half_time:
            root = BASS_ROOTS[bar % 4]
            add(bass, t0, sub808(hz(root, -3), 0.8))
            if not half_time:
                add(bass, t0 + 10 * S16, sub808(hz(root, -3), 0.5), 0.8)
            ks = [0, 8] if half_time else KICKS
            sn = [8] if half_time else SNARES
            for k in ks:
                add(drums, t0 + k * S16, kick())
            for s in sn:
                add(drums, t0 + s * S16, snare(rng))
            if not half_time:
                for h in range(16):
                    add(drums, t0 + h * S16, hat(rng), 1.0 if h % 4 == 0 else 0.6)
                if bar in range(12, 17):
                    for h in (2, 6, 10, 14):
                        add(drums, t0 + h * S16, hat(rng, open_=True))
                if bar % 4 == 3:  # 32nd hat roll into the next bar
                    for k32 in range(4):
                        add(drums, t0 + 14 * S16 + k32 * S16 / 2, hat(rng), 0.5 + 0.1 * k32)

        if bar in (10, 11):  # breakdown drone
            add(bass, t0, sub808(hz("D", -3), BAR, drive=1.2), 0.5)

    # builds into the two drops and out of the breakdown
    add(drums, 1 * BAR + 8 * S16, riser(8 * S16))
    for k in range(8):  # snare roll, rising
        add(drums, 1 * BAR + 8 * S16 + k * S16, snare(rng), 0.25 + 0.09 * k)
    add(drums, 11 * BAR + 8 * S16, riser(8 * S16))
    add(drums, 2 * BAR, impact(rng))
    add(drums, 12 * BAR, impact(rng))

    # section low-pass rides on the melodic layer: dark intro/breakdown, open drops
    out_mel = np.zeros(TOTAL)
    for bar in range(BARS):
        a, b_ = int(bar * BAR * RATE), min(int((bar + 1) * BAR * RATE), TOTAL)
        cut = 1400 if bar in (0, 1, 10, 11) else (9000 if bar != 17 else 3000)
        out_mel[a:b_] = lp(mel[a:b_], cut)[: b_ - a]

    # sidechain pump: everything but drums ducks ~120 ms after each kick
    duck = np.ones(TOTAL)
    for bar in range(BARS):
        if bar in full_bars or bar == 17:
            for k in ([0, 8] if bar == 17 else KICKS):
                i = int((bar * BAR + k * S16) * RATE)
                n = int(0.12 * RATE)
                j = min(i + n, TOTAL)
                duck[i:j] = np.minimum(duck[i:j], 0.35 + 0.65 * (np.arange(j - i) / n) ** 1.5)

    hiss = lp(rng.standard_normal(TOTAL), 6000) * 0.012  # vinyl bed, constant
    mix = (out_mel * duck) + (bass * duck) + drums + hiss
    mix = np.tanh(mix * 1.4)  # glue saturation
    mix *= (10 ** (-1.5 / 20)) / np.max(np.abs(mix))  # peak to -1.5 dBFS

    # slight width: melodic layer 9 ms Haas offset on the right channel
    right = np.copy(mix)
    d = int(0.009 * RATE)
    wide = out_mel * duck * 0.25
    right[d:] += wide[:-d]
    right *= (10 ** (-1.5 / 20)) / np.max(np.abs(right))

    peak_db = 20 * np.log10(np.max(np.abs(mix)))
    rms_db = 20 * np.log10(np.sqrt(np.mean(mix ** 2)))
    assert len(mix) == TOTAL == 1_468_800, len(mix)
    assert -2.0 < peak_db < -1.0, peak_db
    # phonk masters run hot: ~8 dB crest is genre-correct, so gate at -8
    assert -18 < rms_db < -8, rms_db

    inter = np.empty(TOTAL * 2, dtype=np.int16)
    inter[0::2] = (mix * 32767).astype(np.int16)
    inter[1::2] = (right * 32767).astype(np.int16)
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(inter.tobytes())
    print(f"OK {OUT}  {TOTAL / RATE:.3f}s  peak {peak_db:.1f} dBFS  rms {rms_db:.1f} dBFS")


if __name__ == "__main__":
    main()
