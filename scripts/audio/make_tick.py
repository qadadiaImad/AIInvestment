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


# --------------------------------------------------------------- quiz sounds
# Candle blips and the coin chime. Kept in the same file because they share the
# filter helpers, and because one script regenerating every asset means the set
# can never drift out of sync.

def blip(seed, f0, f1, dur=0.10, bright=1.0):
    """A short pitched tone that glides f0 -> f1. Up-candles rise, down fall."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    out, phase = [], 0.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * (t ** 0.7)
        phase += 2 * math.pi * f / RATE
        env = math.exp(-i / (RATE * dur * 0.30)) * min(1.0, i / (RATE * 0.004))
        # a little second harmonic for body, a touch of noise for attack
        v = math.sin(phase) + 0.28 * bright * math.sin(phase * 2)
        if i < RATE * 0.004:
            v += rng.uniform(-0.4, 0.4)
        out.append(v * env)
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.7 for v in out]


def coin(seed):
    """Metallic chime: inharmonic partials, fast attack, long-ish ring."""
    rng = random.Random(seed)
    dur = 0.85
    n = int(RATE * dur)
    partials = [(1.0, 1.00, 0.30), (0.62, 2.76, 0.24), (0.44, 5.40, 0.18),
                (0.30, 8.93, 0.13), (0.22, 13.3, 0.09)]
    base = 1180.0
    out = [0.0] * n
    for amp, ratio, decay in partials:
        f = base * ratio * rng.uniform(0.995, 1.005)
        for i in range(n):
            out[i] += amp * math.sin(2 * math.pi * f * i / RATE) * math.exp(-i / (RATE * decay))
    for i in range(int(RATE * 0.003)):          # soften the very front edge
        out[i] *= i / (RATE * 0.003)
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.8 for v in out]


def impact(seed):
    """The take. A cartoon hit is three things landing on the same frame:

      body   a low sine swept DOWN in pitch - the thump you feel rather than
             hear. Sweeping down is what separates an impact from a drum note.
      crack  a short noise burst, band-limited by the one-pole pair, for the
             leading edge. Without it the hit is soft and lands late.
      ring   a brief mid tone so it reads as cartoon rather than as a gunshot.

    Kept to ~0.35s: an impact that outlasts the drawing it punctuates stops
    reading as a hit and starts reading as music.
    """
    rng = random.Random(seed)
    dur = 0.36
    n = int(RATE * dur)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        t = i / n
        f = 150.0 * math.exp(-t * 2.4) + 42.0      # 192Hz -> 46Hz
        phase += 2 * math.pi * f / RATE
        out[i] += math.sin(phase) * math.exp(-i / (RATE * 0.12)) * 1.0

    crack = [rng.uniform(-1, 1) * math.exp(-i / (RATE * 0.020)) for i in range(n)]
    crack = one_pole_lp(one_pole_hp(crack, 700.0), 5200.0)
    for i in range(n):
        out[i] += crack[i] * 0.85

    for i in range(n):
        out[i] += math.sin(2 * math.pi * 320 * i / RATE) * math.exp(-i / (RATE * 0.045)) * 0.35

    for i in range(int(RATE * 0.0015)):            # kill the click on frame 0
        out[i] *= i / (RATE * 0.0015)
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.92 for v in out]


# ------------------------------------------------------- cinematic reel set
# Sounds the Hormuz reel needs that the quiz didn't: a keyboard for the typed
# captions, air for the camera moves, and a sting for the crisis mark.

def key_click(seed, pitch=1.0):
    """One mechanical keyswitch.

    A keyboard is NOT a click — it is a click and then a *bottom-out*, two
    events ~9ms apart, and the second one is the louder. Rendering only the
    first is what makes UI 'typing' sound like a Geiger counter. The stem
    resonance sits high (3-5kHz) because the sound is plastic hitting plastic
    in a tiny cavity, not wood.

    Kept under 55ms: at 22 chars/sec the tails would otherwise overlap into a
    single rattle.
    """
    rng = random.Random(seed)
    n = int(RATE * 0.055)
    out = [0.0] * n

    # the downstroke: bright, very short
    top = [rng.uniform(-1, 1) for _ in range(n)]
    top = one_pole_lp(one_pole_hp(top, 1800.0), 9000.0 * pitch)
    for i in range(n):
        out[i] += top[i] * math.exp(-i / (RATE * 0.0035)) * 0.55

    # the bottom-out ~9ms later: lower, fuller, this is the one you hear
    gap = int(RATE * 0.009)
    bot = [rng.uniform(-1, 1) for _ in range(n)]
    bot = one_pole_lp(one_pole_hp(bot, 700.0), 5200.0 * pitch)
    for i in range(n - gap):
        out[i + gap] += bot[i] * math.exp(-i / (RATE * 0.0075))

    # case resonance so it sits in a body rather than in free air
    for i in range(n - gap):
        out[i + gap] += (
            math.sin(2 * math.pi * 3400 * pitch * i / RATE)
            * math.exp(-i / (RATE * 0.004))
            * 0.22
        )

    for i in range(int(RATE * 0.0008)):
        out[i] *= i / (RATE * 0.0008)
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.55 for v in out]


def whoosh(seed, dur=0.55, rising=True):
    """Air for a camera move.

    Filtered noise whose passband SWEEPS — that sweep is the whole effect. A
    static noise burst with a volume envelope is wind; a moving band is
    something travelling past the microphone. Rising = push in, falling =
    pull out, so the ear knows which way the camera went even off-screen.

    The amplitude envelope peaks ~60% through rather than at the start: a
    whoosh that is loudest on frame 0 reads as an impact instead.
    """
    rng = random.Random(seed)
    n = int(RATE * dur)
    noise = [rng.uniform(-1, 1) for _ in range(n)]

    # sweep by crossfading three fixed bands — cheaper than a time-varying
    # filter and indistinguishable once the envelope is on it
    bands = [
        one_pole_lp(one_pole_hp(noise, 180.0), 900.0),
        one_pole_lp(one_pole_hp(noise, 700.0), 2600.0),
        one_pole_lp(one_pole_hp(noise, 2200.0), 7000.0),
    ]
    out = []
    for i in range(n):
        t = i / n
        pos = (t if rising else 1.0 - t) * 2.0        # 0..2 across three bands
        k = int(pos)
        frac = pos - k
        if k >= 2:
            k, frac = 1, 1.0
        v = bands[k][i] * (1 - frac) + bands[k + 1][i] * frac
        env = math.sin(math.pi * (t ** 0.72)) ** 1.4   # late peak, soft tails
        out.append(v * env)

    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.42 for v in out]


def crisis_sting(seed):
    """The mark landing on the chart when the shock hits.

    Three layers on one frame: a sub that drops an octave (the floor giving
    way), a dissonant fifth-plus-tritone pad that holds under it (unease
    without a horror-film cliche), and a short noise crack for the edge.
    1.6s, because it has to still be ringing while the gap candle prints.
    """
    rng = random.Random(seed)
    dur = 1.6
    n = int(RATE * dur)
    out = [0.0] * n

    phase = 0.0
    for i in range(n):
        t = i / n
        f = 88.0 * math.exp(-t * 1.6) + 33.0           # 121Hz -> 34Hz
        phase += 2 * math.pi * f / RATE
        out[i] += math.sin(phase) * math.exp(-i / (RATE * 0.55)) * 1.1

    for f, amp, dec in ((110.0, 0.30, 0.75), (165.0, 0.22, 0.70), (155.6, 0.16, 0.60)):
        for i in range(n):
            att = min(1.0, i / (RATE * 0.05))
            out[i] += math.sin(2 * math.pi * f * i / RATE) * amp * att * math.exp(-i / (RATE * dec))

    crack = [rng.uniform(-1, 1) * math.exp(-i / (RATE * 0.035)) for i in range(n)]
    crack = one_pole_lp(one_pole_hp(crack, 500.0), 4200.0)
    for i in range(n):
        out[i] += crack[i] * 0.55

    for i in range(int(RATE * 0.002)):
        out[i] *= i / (RATE * 0.002)
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak * 0.90 for v in out]


def extras():
    write(os.path.join(OUT, "candle_up.wav"), blip(11, 520, 900, bright=1.0))
    write(os.path.join(OUT, "candle_down.wav"), blip(12, 470, 250, bright=0.5))
    write(os.path.join(OUT, "coin.wav"), coin(33))
    write(os.path.join(OUT, "impact.wav"), impact(77))
    for f in ("candle_up.wav", "candle_down.wav", "coin.wav", "impact.wav"):
        print(f"{f} -> {os.path.relpath(os.path.join(OUT, f), REPO)}")


def reel_extras():
    """Three variants of the keyswitch so a typed line isn't a machine gun."""
    for i, (name, seed, pitch) in enumerate(
        [("key_click.wav", 101, 1.0), ("key_click2.wav", 102, 1.07), ("key_click3.wav", 103, 0.93)]
    ):
        write(os.path.join(OUT, name), key_click(seed, pitch))
    write(os.path.join(OUT, "whoosh_in.wav"), whoosh(201, 0.55, rising=True))
    write(os.path.join(OUT, "whoosh_out.wav"), whoosh(202, 0.70, rising=False))
    write(os.path.join(OUT, "crisis.wav"), crisis_sting(303))
    for f in ("key_click.wav", "key_click2.wav", "key_click3.wav",
              "whoosh_in.wav", "whoosh_out.wav", "crisis.wav"):
        p = os.path.join(OUT, f)
        print(f"{f} -> {os.path.relpath(p, REPO)}")


if __name__ == "__main__":
    main()
    extras()
    reel_extras()
