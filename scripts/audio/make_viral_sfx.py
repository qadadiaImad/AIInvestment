"""The viral-transition SFX pack, synthesised. Rights-clean by construction.

WHY NOT JUST DOWNLOAD THEM. The reference reel names six sounds - Faah,
Riser, Whoosh, Among Us, Core, Vine Boom - and two of those are other
people's intellectual property, not genres:

  · "Among Us" is InnerSloth's game audio;
  · "Vine Boom" is a specific sampled hit that circulates without a clear
    licence chain;
  · "Faah" is a meme vocal, i.e. someone's recorded voice.

Everything else on that list is a CATEGORY, not a recording - a riser is a
riser. Those are synthesised here from the same primitives as make_tick.py,
which means no licence, no attribution, no Content ID, and no chance of a
platform muting an upload. They also cost nothing and can be retuned to the
episode instead of being whatever length a stock file happened to be.

Pixabay's library is the right fallback for the two IP ones if the owner
wants that exact sound (Pixabay Content Licence: free, commercial use, no
attribution) - but it cannot be fetched programmatically, its download URLs
are built client-side.

WHAT EACH SOUND IS FOR, from the reference reel's own captions:
  riser        make a transition feel smoother  (tension into a cut)
  whoosh       make a transition feel smoother  (the cut itself)
  reveal       reveal something unexpected      (the "Among Us" slot)
  core         make a statement more important  (weight under a claim)
  boom         make a statement more comedic    (the "Vine Boom" slot)
  sub_drop     land a hard cut                  (bass floor drops out)

Usage:
    python scripts/audio/make_viral_sfx.py
Writes 48kHz mono WAV + MP3 to remotion/public/audio/viral/
"""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_tick import one_pole_hp, one_pole_lp, write  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "audio", "viral")
RATE = 48000


def env(n, attack, decay, curve=2.0):
    """attack/decay in seconds, exponential-ish decay."""
    a = max(1, int(attack * RATE))
    out = []
    for i in range(n):
        if i < a:
            out.append((i / a) ** 0.6)
        else:
            t = (i - a) / max(1, decay * RATE)
            out.append(math.exp(-curve * t))
    return out


def riser(seed, dur=1.8, tonal=True):
    """Noise sweeping up in pitch and volume, with a rising tone under it.

    The classic pre-cut build. Filter cutoff climbs exponentially so the
    last third does most of the perceived work, which is what makes it feel
    like it is accelerating into the cut rather than just getting louder.
    """
    rng = random.Random(seed)
    n = int(RATE * dur)
    noise = [rng.uniform(-1, 1) for _ in range(n)]
    out = [0.0] * n
    # sweep a one-pole band by mixing progressively brighter filtered copies
    lo = one_pole_lp(noise, 900.0)
    hi = one_pole_hp(noise, 2400.0)
    for i in range(n):
        t = i / n
        k = t ** 2.2
        amp = 0.10 + 0.85 * (t ** 1.8)
        out[i] = (lo[i] * (1 - k) + hi[i] * k) * amp
    if tonal:
        ph = 0.0
        for i in range(n):
            t = i / n
            f = 220 * (2 ** (2.6 * t))        # ~2.6 octaves up
            ph += 2 * math.pi * f / RATE
            out[i] += math.sin(ph) * 0.22 * (t ** 2.4)
    # duck the last 25ms so it hands over cleanly to whatever lands on the cut
    tail = int(RATE * 0.025)
    for i in range(n - tail, n):
        out[i] *= (n - i) / tail
    return out


def whoosh(seed, dur=0.45, rising=True):
    """Filtered noise swept across the stereo-less centre - a fast pass-by."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    noise = [rng.uniform(-1, 1) for _ in range(n)]
    lo = one_pole_lp(noise, 700.0)
    hi = one_pole_hp(noise, 1800.0)
    e = env(n, 0.05 * dur, dur * 0.5, curve=3.2)
    out = []
    for i in range(n):
        t = i / n
        k = (t if rising else 1 - t) ** 1.6
        out.append((lo[i] * (1 - k) + hi[i] * k) * e[i])
    return out


def boom(seed, dur=1.1, f0=132.0, f1=38.0):
    """A comedic low hit: fast pitch drop plus a click, the Vine-Boom shape.

    The drop is what makes it read as comic rather than cinematic - a
    constant-pitch bass note is a kick, a falling one is a punchline.
    """
    rng = random.Random(seed)
    n = int(RATE * dur)
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        t = i / n
        f = f1 + (f0 - f1) * math.exp(-7.0 * t)
        ph += 2 * math.pi * f / RATE
        out[i] = math.sin(ph) * math.exp(-3.4 * t)
        out[i] += math.sin(ph * 2) * 0.18 * math.exp(-7.0 * t)
    # the initial click gives it edge on phone speakers, which cannot
    # reproduce 40 Hz at all - without it the sound vanishes on mobile
    click = one_pole_hp([rng.uniform(-1, 1) for _ in range(int(RATE * 0.02))],
                        1800.0)
    for i, v in enumerate(click):
        out[i] += v * 0.5 * math.exp(-40.0 * i / RATE)
    return out


def core(seed, dur=1.6):
    """Weight under a claim: a low drone that swells and stops."""
    n = int(RATE * dur)
    out = [0.0] * n
    for mult, amp, det in ((1.0, 0.55, 1.0), (1.5, 0.22, 1.003),
                           (2.0, 0.16, 0.997)):
        ph = 0.0
        for i in range(n):
            ph += 2 * math.pi * (55.0 * mult * det) / RATE
            out[i] += math.sin(ph) * amp
    e = env(n, 0.16, dur * 0.42, curve=2.2)
    rng = random.Random(seed)
    air = one_pole_hp([rng.uniform(-1, 1) for _ in range(n)], 5000.0)
    for i in range(n):
        out[i] = out[i] * e[i] + air[i] * 0.05 * e[i]
    return out


def reveal(seed, dur=0.9):
    """Something unexpected: bright shimmer up, then a short bloom."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    out = [0.0] * n
    for k, (mult, amp) in enumerate(((1.0, 0.5), (1.5, 0.3), (2.0, 0.22),
                                     (3.0, 0.14))):
        ph = 0.0
        for i in range(n):
            t = i / n
            f = 520 * mult * (1 + 0.55 * t)
            ph += 2 * math.pi * f / RATE
            out[i] += math.sin(ph) * amp * math.exp(-2.6 * t) * min(1.0, t * 14)
    spark = one_pole_hp([rng.uniform(-1, 1) for _ in range(n)], 6500.0)
    for i in range(n):
        out[i] += spark[i] * 0.14 * math.exp(-5.5 * i / n)
    return out


def sub_drop(seed, dur=1.3):
    """The floor falling out - for a hard cut to a serious point."""
    n = int(RATE * dur)
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        t = i / n
        f = 90.0 * math.exp(-2.4 * t) + 26.0
        ph += 2 * math.pi * f / RATE
        out[i] = math.sin(ph) * math.exp(-1.9 * t)
    return out


PACK = [
    ("riser_short", lambda: riser(11, 1.2), "transition · smoother"),
    ("riser_long", lambda: riser(12, 2.4), "transition · smoother"),
    ("whoosh_fast", lambda: whoosh(13, 0.32), "transition · the cut"),
    ("whoosh_slow", lambda: whoosh(14, 0.62, rising=False), "transition · the cut"),
    ("boom_comedic", lambda: boom(15), "statement · comedic"),
    ("core_weight", lambda: core(16), "statement · important"),
    ("reveal_sting", lambda: reveal(17), "reveal · unexpected"),
    ("sub_drop", lambda: sub_drop(18), "hard cut"),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    ff = next((p for p in (r"C:\ffmpeg\bin\ffmpeg.exe", "ffmpeg")
               if os.path.exists(p) or p == "ffmpeg"), "ffmpeg")
    for name, fn, purpose in PACK:
        s = fn()
        peak = max(abs(v) for v in s) or 1.0
        s = [v / peak * 0.89 for v in s]
        wav = os.path.join(OUT, name + ".wav")
        write(wav, s)
        mp3 = os.path.join(OUT, name + ".mp3")
        subprocess.run([ff, "-v", "error", "-i", wav, "-codec:a", "libmp3lame",
                        "-q:a", "2", mp3, "-y"], check=True)
        print(f"  {name:14s} {len(s)/RATE:4.2f}s   {purpose}")
    print("-> " + os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
