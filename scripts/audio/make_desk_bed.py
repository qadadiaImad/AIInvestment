"""Synthesise the music bed for a Market-Lessons desk episode.

WHY THIS IS NOT make_bed.py. That bed scores the Hormuz reel: 71s of
montage at 93.75 BPM with a kick on every beat. These episodes are the
opposite shape - 140-196s carrying 28-39 spoken beats and 30+ VO lines.
A kick every 0.64s under two and a half minutes of dialogue does not read
as energy, it reads as a ringtone you cannot turn off, and it fights every
consonant. Measured: the VO sits at about -22 dBFS mean; anything with
transients in that band competes with it.

So the desk bed is DRONE-FIRST and almost entirely percussion-free:

  * a low root that runs the whole episode, so the room has a floor;
  * a minor third that stacks in once the evidence starts and thins back
    out for the lesson, so the harmony follows the argument;
  * the music only ASSERTS itself in the act gaps - a soft sub-hit and a
    short riser land on each act boundary, where nobody is talking;
  * true silence into the final act, because the close is the punchline
    and the most reliable way to make a line land is to give it nothing
    to share the room with.

Act boundaries are parsed from the composition itself, so retiming a beat
moves the music with it and the two cannot drift apart.

Rights-clean by construction: every sample is generated here from sines and
filtered noise, same primitives as make_tick.py. Nothing is sampled, no
library licence applies, and it can ship anywhere.

Usage:
    python scripts/audio/make_desk_bed.py 3
    python scripts/audio/make_desk_bed.py 1 2 3 4 5
Writes:
    remotion/public/audio/bed_ep<N>.wav   (48kHz mono, episode length)
"""
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_tick import one_pole_lp, write            # noqa: E402
from make_bed import add, drone_into, riser_into, sub_hit  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RATE = 48000
FPS = 30

# episode length in frames, mirrored from the compositions
TOTAL = {"1": 5880, "2": 4500, "3": 5010, "4": 4200, "5": 4260}

# A minor, an octave below the voice so the bed never masks a consonant
A1, C2, E2 = 55.0, 65.41, 82.41

ACT_RE = re.compile(
    r"//\s*[═=]{3,}\s*(ACT[^\n═=]*|[A-Z][^\n═=]{3,40}?)\s*[═=]{3,}")


def acts_of(ep):
    """Act boundaries, in seconds, read from the composition."""
    p = os.path.join(REPO, "remotion", "src", "compositions",
                     f"FairMarketEp{ep}.tsx")
    with open(p, encoding="utf-8") as fh:
        s = fh.read()
    i = s.index("const BEATS")
    body = s[i:s.index("\n];", i)]
    out = []
    for m in ACT_RE.finditer(body):
        nxt = re.search(r"\{at: (\d+),", body[m.end():])
        if nxt:
            out.append(int(nxt.group(1)) / FPS)
    return sorted(set(out))


def build(ep):
    total_s = TOTAL[ep] / FPS
    n = int(RATE * total_s)
    bed = [0.0] * n
    acts = [a for a in acts_of(ep) if 0.5 < a < total_s - 4]
    end = total_s

    # ---- the floor: a root that never leaves ------------------------------
    drone_into(bed, A1, 0.0, end, 0.20, lfo_hz=0.06, seed=1)

    # ---- the argument: a third stacks in for the middle, out for the close
    # Acts 1..n-1 are the case being built; the last act is the lesson, and
    # the lesson is delivered over a thinner bed on purpose.
    if len(acts) >= 2:
        mid0, mid1 = acts[0], acts[-1]
        drone_into(bed, C2, mid0, mid1, 0.11, lfo_hz=0.13, seed=2)
        if len(acts) >= 4:
            # the fifth joins only for the densest stretch of evidence
            drone_into(bed, E2, acts[1], acts[-2], 0.07, lfo_hz=0.17, seed=3)
        drone_into(bed, E2, mid1, end, 0.05, lfo_hz=0.05, seed=4)

    # ---- the act gaps are the only place music is allowed to speak --------
    sh = sub_hit()
    for k, a in enumerate(acts):
        if a < 1.5:
            continue
        riser_into(bed, max(0.0, a - 1.6), a - 0.05, 0.17, seed=10 + k)
        add(bed, a, sh, 0.55)

    # ---- true silence into the close --------------------------------------
    # The last act is the lesson; hand it an empty room and let it re-enter
    # underneath. Same trick make_bed.py uses on the shock, for the same
    # reason.
    if acts:
        gap0, gap1 = acts[-1] - 0.85, acts[-1] - 0.03
        g0, g1 = int(gap0 * RATE), int(gap1 * RATE)
        fade = int(RATE * 0.04)
        for j in range(max(0, g0), min(g1, n)):
            edge = (g0 + fade - j) / fade if j < g0 + fade else 0.0
            bed[j] *= max(0.0, min(1.0, edge))
        for j in range(g1, min(g1 + fade, n)):
            bed[j] *= (j - g1) / fade

    # ---- head and tail -----------------------------------------------------
    lead = int(RATE * 1.2)
    for j in range(min(lead, n)):
        bed[j] *= j / lead
    tail = int(RATE * 3.5)
    for j in range(max(0, n - tail), n):
        bed[j] *= max(0.0, (n - j) / tail)

    # keep the bed out of the voice's band entirely, then leave headroom -
    # this is mixed UNDER dialogue, so it is normalised low on purpose
    bed = one_pole_lp(bed, 2600.0)
    peak = max(abs(v) for v in bed) or 1.0
    bed = [v / peak * 0.5 for v in bed]

    out = os.path.join(REPO, "remotion", "public", "audio", f"bed_ep{ep}.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write(out, bed)
    rms = math.sqrt(sum(v * v for v in bed) / len(bed))
    print(f"ep{ep}: {total_s:.0f}s, {len(acts)} act marks, "
          f"rms {20 * math.log10(rms or 1e-9):.1f} dBFS -> "
          f"{os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    for a in sys.argv[1:] or ["1", "2", "3", "4", "5"]:
        build(a)
