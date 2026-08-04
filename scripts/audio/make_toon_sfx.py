"""Synthesise the character-motion sound effects for FairMarketEp1.

The interaction pass gave Sol and Rex arrivals, exits and head turns —
all of them silent. A take whose sound lands two frames late reads as
dubbed, and a take with no sound at all reads as a graphic moving, so
every move in motion/interact.ts gets a hit here.

Built in plain Python for the same reason as make_tick.py: the ffmpeg
bundled with Remotion's compositor is a minimal build with no
highpass/lowpass, and an unfiltered whoosh is either a hiss or a beep.
The filter helpers are imported from that script rather than copied so
the two sets can never drift apart.

Four sounds, each matched to a primitive:
  sfx_whoosh  a body travelling across stage      (Move inL/inR/outL/outR)
  sfx_pop     a body arriving where it wasn't     (Move pop)
  sfx_poof    a body leaving the same way         (Move vanish)
  sfx_whip    a head snapping round               (Turn)

Usage:  python scripts/audio/make_toon_sfx.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_tick import RATE, one_pole_hp, write  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "audio")


def sweep_lp(xs, points):
    """One-pole low-pass whose cutoff moves. `points` is a list of
    (position 0..1, cutoff Hz) — a fixed-cutoff filter cannot make a
    whoosh, because the whole character of a whoosh is the cutoff
    travelling."""
    n = len(xs)
    out, prev = [], 0.0
    for i, x in enumerate(xs):
        t = i / max(1, n - 1)
        f = points[-1][1]
        for (t0, f0), (t1, f1) in zip(points, points[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / max(1e-9, t1 - t0)
                f = f0 + (f1 - f0) * u
                break
        a = math.exp(-2 * math.pi * f / RATE)
        prev = (1 - a) * x + a * prev
        out.append(prev)
    return out


def env(n, attack, decay, curve=2.0):
    """Attack/decay envelope in seconds, exponential decay."""
    a = max(1, int(RATE * attack))
    out = []
    for i in range(n):
        if i < a:
            out.append((i / a) ** 0.6)
        else:
            out.append(math.exp(-((i - a) / (RATE * decay)) ** curve))
    return out


def norm(xs, peak=0.8):
    m = max(abs(v) for v in xs) or 1.0
    return [v / m * peak for v in xs]


def whoosh(seed=3, dur=0.38):
    """Air moving past: broadband noise, cutoff rising then falling, so
    the body reads as approaching and passing rather than just hissing."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    noise = one_pole_hp([rng.uniform(-1, 1) for _ in range(n)], 260)
    body = sweep_lp(noise, [(0.0, 900), (0.45, 5200), (1.0, 700)])
    e = env(n, 0.09, 0.10, 1.4)
    return norm([v * g for v, g in zip(body, e)], 0.62)


def pop(seed=11, dur=0.16):
    """Arriving where you weren't: a fast upward pitch bloop with a click
    on the front, so it lands as an event rather than a fade-in."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    out, phase = [], 0.0
    for i in range(n):
        t = i / n
        f = 250 + 950 * (t ** 0.42)
        phase += 2 * math.pi * f / RATE
        out.append(math.sin(phase))
    click = one_pole_hp([rng.uniform(-1, 1) for _ in range(n)], 1800)
    e = env(n, 0.004, 0.045, 1.7)
    ce = env(n, 0.001, 0.010, 2.2)
    return norm([s * g * 0.9 + c * cg * 0.45
                 for s, g, c, cg in zip(out, e, click, ce)], 0.72)


def poof(seed=17, dur=0.30):
    """Leaving the same way: the pop's mirror — cutoff falls, pitch
    falls, softer attack. A vanish that used the pop would read as a
    second arrival."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    noise = one_pole_hp([rng.uniform(-1, 1) for _ in range(n)], 320)
    body = sweep_lp(noise, [(0.0, 5600), (1.0, 480)])
    out, phase = [], 0.0
    for i in range(n):
        t = i / n
        f = 620 - 380 * t
        phase += 2 * math.pi * f / RATE
        out.append(math.sin(phase))
    e = env(n, 0.012, 0.085, 1.5)
    return norm([b * g * 0.8 + s * g * 0.35
                 for b, s, g in zip(body, out, e)], 0.58)


def whip(seed=29, dur=0.15):
    """A head snapping round: short, bright, and gone. Long enough to
    hear, short enough that it cannot outlast the 3-frame smear it is
    sitting under."""
    rng = random.Random(seed)
    n = int(RATE * dur)
    noise = one_pole_hp([rng.uniform(-1, 1) for _ in range(n)], 1400)
    body = sweep_lp(noise, [(0.0, 3200), (0.4, 9000), (1.0, 2600)])
    e = env(n, 0.02, 0.045, 1.6)
    return norm([v * g for v, g in zip(body, e)], 0.55)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, samples in [("sfx_whoosh.wav", whoosh()),
                          ("sfx_pop.wav", pop()),
                          ("sfx_poof.wav", poof()),
                          ("sfx_whip.wav", whip())]:
        p = os.path.join(OUT, name)
        write(p, samples)
        print(f"{name}: {len(samples)/RATE*1000:.0f} ms -> "
              f"{os.path.relpath(p, REPO)}")


if __name__ == "__main__":
    main()
