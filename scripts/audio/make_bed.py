"""Synthesise the music bed for the Hormuz reel.

Why synthesis and not a track: the bed must be rights-clean, and the Higgsfield
MCP has no music model (its own docs say to decline music requests rather than
fake them with a speech model). So the bed is built here from the same
primitives as make_tick.py — sines, filtered noise, one-pole filters.

Design, from measurement and the reel's own beat sheet:
- BPM 93.75 (beat = 0.64s) — measured off the competitor reel the owner likes:
  its kick landed exactly every 0.64s.
- The bed follows the STORY, not a loop. Sections switch on the reel's frame
  constants (converted to seconds), so a retimed beat moves its music with it.
- The oldest trick in trailer scoring is kept: total silence for ~0.8s at the
  moment of the shock. The sting that already lives in the SFX track owns that
  beat; music re-entering *after* it is what makes it land.

Usage:
    python scripts/audio/make_bed.py
Writes:
    content/probe/vo/bed_music.wav   (48kHz stereo, 46.06s)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_tick import one_pole_hp, one_pole_lp, write  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "content", "probe", "vo", "bed_music.wav")

RATE = 48000
FPS = 30
TOTAL_S = 46.06
N = int(RATE * TOTAL_S)

BPM = 93.75
BEAT = 60.0 / BPM  # 0.64s exactly

# Story anchors, in seconds (from HormuzReel.tsx frame constants / 30fps)
T_SHOCK = 366 / FPS      # 12.2  the sting + the mark
T_REENTER = T_SHOCK + 0.85
T_TRAP = 640 / FPS       # 21.3  push into the upper wick
T_COIL = 802 / FPS       # 26.7  inside-bar caption
T_TRIGGER = 908 / FPS    # 30.3  the trade frame lands
T_PAYOFF = 1040 / FPS    # 34.7  "Target: twice the risk" -> coin at 36.5
T_UNWIND = 1154 / FPS    # 38.5  premium unwinds
T_END = 1244 / FPS       # 41.5  the 24% card
T_FADE = 45.3            # everything gone before the last frame

# A natural minor. Root chosen low enough to be felt on phone speakers' second
# harmonic rather than heard directly.
A1, C2, E2, A2 = 55.0, 65.41, 82.41, 110.0


def sec(i):
    return i / RATE


def kick(n=None, punch=1.0):
    """Soft cinematic pulse-kick: sine swept 95->42Hz, no click on purpose —
    this is a heartbeat under narration, not a dance kick."""
    n = n or int(RATE * 0.30)
    out, phase = [], 0.0
    for i in range(n):
        t = i / n
        f = 95.0 * math.exp(-t * 3.2) + 42.0
        phase += 2 * math.pi * f / RATE
        env = math.exp(-i / (RATE * 0.085)) * min(1.0, i / (RATE * 0.004))
        out.append(math.sin(phase) * env * punch)
    return out


def sub_hit():
    """45Hz sine, <10ms attack, ~550ms decay — the floor giving way under the
    three hardest cuts. Layered UNDER the existing SFX sting, not replacing it."""
    n = int(RATE * 0.62)
    out = []
    for i in range(n):
        env = math.exp(-i / (RATE * 0.16)) * min(1.0, i / (RATE * 0.008))
        out.append(math.sin(2 * math.pi * 45.0 * i / RATE) * env)
    return out


def dub(rng):
    """The 'dub' of a lub-dub heartbeat: a high-passed tick ~180ms after the
    thump. Two events per beat is what reads as a pulse instead of a metronome."""
    n = int(RATE * 0.04)
    h = [rng.uniform(-1, 1) for _ in range(n)]
    h = one_pole_hp(one_pole_hp(h, 2200.0), 2200.0)
    return [v * math.exp(-i / (RATE * 0.010)) * 0.4 for i, v in enumerate(h)]


def hat(rng, n=None):
    n = n or int(RATE * 0.05)
    h = [rng.uniform(-1, 1) for _ in range(n)]
    h = one_pole_hp(one_pole_hp(h, 5500.0), 5500.0)
    return [v * math.exp(-i / (RATE * 0.012)) * 0.5 for i, v in enumerate(h)]


def add(buf, start_s, samples, gain=1.0):
    off = int(start_s * RATE)
    for i, v in enumerate(samples):
        j = off + i
        if 0 <= j < len(buf):
            buf[j] += v * gain


def drone_into(buf, f0, from_s, to_s, gain, detune=1.003, lfo_hz=0.11, seed=1):
    """A slow-breathing dyad: f0 + detuned copy + fifth above, with 300ms
    raised-cosine edges so sections never click."""
    i0, i1 = int(from_s * RATE), min(int(to_s * RATE), len(buf))
    edge = int(RATE * 0.3)
    p1 = p2 = p3 = 0.0
    for j in range(i0, i1):
        p1 += 2 * math.pi * f0 / RATE
        p2 += 2 * math.pi * f0 * detune / RATE
        p3 += 2 * math.pi * f0 * 1.5 / RATE
        v = math.sin(p1) + 0.7 * math.sin(p2) + 0.35 * math.sin(p3)
        breathe = 0.75 + 0.25 * math.sin(2 * math.pi * lfo_hz * sec(j) + seed)
        k = j - i0
        m = i1 - j
        env = min(1.0, k / edge, m / edge)
        buf[j] += v * gain * breathe * env * (1 / 2.05)


def riser_into(buf, from_s, to_s, gain, seed):
    """Filtered-noise sweep rising into a hit. Peaks at the END — a riser that
    peaks early is just wind."""
    rng = random.Random(seed)
    i0, i1 = int(from_s * RATE), min(int(to_s * RATE), len(buf))
    n = i1 - i0
    if n <= 0:
        return
    noise = [rng.uniform(-1, 1) for _ in range(n)]
    lo = one_pole_lp(one_pole_hp(noise, 250.0), 1200.0)
    hi = one_pole_lp(one_pole_hp(noise, 1500.0), 6500.0)
    for i in range(n):
        t = i / n
        v = lo[i] * (1 - t) + hi[i] * t          # band sweeps up
        buf[i0 + i] += v * gain * (t ** 2.2)      # loudness arrives late


def main():
    rng = random.Random(4242)
    bed = [0.0] * N

    # ---- drones: the harmonic floor, section by section -------------------
    drone_into(bed, A1, 0.0, T_SHOCK, 0.16, lfo_hz=0.09, seed=1)          # intrigue: bare root+5th
    drone_into(bed, A1, T_REENTER, T_COIL, 0.19, seed=2)                  # after the shock: root...
    drone_into(bed, C2, T_TRAP, T_COIL, 0.10, lfo_hz=0.13, seed=3)        # ...gains its minor third
    drone_into(bed, A1, T_COIL, T_PAYOFF, 0.21, seed=4)
    drone_into(bed, C2, T_COIL, T_PAYOFF, 0.12, seed=5)
    drone_into(bed, E2, T_TRIGGER, T_PAYOFF, 0.10, lfo_hz=0.17, seed=6)   # tension stacks a fifth
    drone_into(bed, A2, T_PAYOFF, T_UNWIND, 0.11, lfo_hz=0.2, seed=7)     # payoff lifts an octave
    drone_into(bed, A1, T_PAYOFF, T_UNWIND, 0.16, seed=8)
    drone_into(bed, A1, T_UNWIND, T_FADE, 0.14, lfo_hz=0.07, seed=9)      # unwind: thin back out
    drone_into(bed, E2, T_END, T_FADE, 0.07, lfo_hz=0.05, seed=10)

    # ---- the pulse ---------------------------------------------------------
    # Heartbeat until the shock (half-time), full-time after it, an extra
    # eighth-note kick under the build, stops dead on the end card: the 24%%
    # number lands in near-silence, which is the point.
    k_soft = kick(punch=0.55)
    k_full = kick(punch=0.95)
    b = 0.0
    beat_i = 0
    while b < T_UNWIND:  # percussion ends AT the unwind — the sober coda is drone-only
        on_shock_gap = T_SHOCK - 0.05 <= b < T_REENTER
        on_payoff_gap = T_PAYOFF - 0.62 <= b < T_PAYOFF
        if not (on_shock_gap or on_payoff_gap):
            if b < T_SHOCK:
                if beat_i % 2 == 0:                         # lub-dub heartbeat
                    add(bed, b, k_soft, 0.9)
                    add(bed, b + 0.18, dub(rng), 0.8)
            elif b < T_COIL:
                add(bed, b, k_full, 0.8 if beat_i % 2 == 0 else 0.55)
            elif b < T_PAYOFF:
                add(bed, b, k_full, 0.9 if beat_i % 2 == 0 else 0.6)
                if T_TRIGGER < b:                           # 8ths under the trigger hold
                    add(bed, b + BEAT / 2, k_soft, 0.4)
                add(bed, b + BEAT / 2, hat(rng), 0.5)       # offbeat hat from the coil
            else:
                add(bed, b, k_full, 0.8 if beat_i % 2 == 0 else 0.5)  # payoff rides out
        b += BEAT
        beat_i += 1

    # ---- sub-bass hits, frame-exact on the three hardest cuts -------------
    sh = sub_hit()
    add(bed, 0.10, sh, 0.65)   # cold open — the first frame is an event
    add(bed, T_SHOCK, sh, 1.0)
    add(bed, 415 / FPS, sh, 0.7)   # the gap bar printing (Monday opens)
    add(bed, T_PAYOFF, sh, 0.9)

    # ---- risers into the two biggest hits ---------------------------------
    riser_into(bed, T_SHOCK - 2.1, T_SHOCK - 0.05, 0.30, seed=11)      # into the shock
    riser_into(bed, T_PAYOFF - 2.4, T_PAYOFF - 0.62, 0.24, seed=12)    # into the payoff

    # ---- TRUE silence before the two biggest hits (trailer rule: the drop
    # lands harder after real nothing) ---------------------------------------
    def silence(from_s, to_s):
        g0, g1 = int(from_s * RATE), int(to_s * RATE)
        fade = int(RATE * 0.03)
        for j in range(max(0, g0), min(g1, N)):
            edge = (g0 + fade - j) / fade if j < g0 + fade else 0.0
            bed[j] *= max(0.0, min(1.0, edge))
        for j in range(g1, min(g1 + fade, N)):
            bed[j] *= (j - g1) / fade

    silence(T_SHOCK - 0.02, T_REENTER)      # the sting owns the shock
    silence(T_PAYOFF - 0.60, T_PAYOFF - 0.02)  # nothing, then the trigger

    # ---- final fade --------------------------------------------------------
    f0 = int(T_FADE * RATE)
    for j in range(f0, N):
        bed[j] *= max(0.0, 1.0 - (j - f0) / (N - f0))

    # gentle lowpass to keep the bed OUT of the voice's band, then normalise
    bed = one_pole_lp(bed, 5200.0)
    peak = max(abs(v) for v in bed) or 1.0
    bed = [v / peak * 0.72 for v in bed]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    write(OUT, bed)
    print(f"bed: {TOTAL_S}s at {BPM} BPM -> {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
