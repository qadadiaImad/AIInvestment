"""Count syllable onsets at the START of a line, to catch a spelled word.

Duration alone cannot settle this. A line containing an ellipsis is long
because it PAUSES, not because the model spelled anything, so s/syllable
flags innocent lines and misses guilty short ones.

An initialism is different acoustically, not just longer: "aitch-ay" is
THREE vowel bursts where "hah" is ONE. So count energy onsets in the first
second and compare against a line known to be correct - episode 1's
"Hah! ... Fundamentals.", which the owner has signed off.

  python scripts/vector/onset_probe.py <wav> [<wav> ...]
"""
from __future__ import annotations

import math
import struct
import sys
import wave
from pathlib import Path

WIN = 0.02          # 20 ms analysis frames
HEAD = 1.0          # only the first second matters for a leading token


def envelope(path: Path, head: float = HEAD):
    with wave.open(str(path), "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        raw = w.readframes(min(n, int(sr * head)))
    d = struct.unpack("<%dh" % (len(raw) // 2), raw)
    if ch == 2:
        d = [(d[i] + d[i + 1]) / 2 for i in range(0, len(d) - 1, 2)]
    step = max(1, int(sr * WIN))
    return [math.sqrt(sum(x * x for x in d[i:i + step]) / step)
            for i in range(0, len(d) - step, step)], sr


def onsets(env, floor_frac: float = 0.22):
    """Rising edges through a threshold - one per vowel burst."""
    peak = max(env) or 1.0
    thr = peak * floor_frac
    n, above = 0, False
    for v in env:
        if v > thr and not above:
            n += 1
            above = True
        elif v < thr * 0.7:
            above = False
    return n


def main() -> None:
    for a in sys.argv[1:]:
        p = Path(a)
        if not p.exists():
            print("missing:", p)
            continue
        env, sr = envelope(p)
        n = onsets(env)
        bars = "".join("#" if v > (max(env) or 1) * 0.22 else "." for v in env)
        print("%-34s onsets_in_1s=%d" % (p.name, n))
        print("   %s" % bars)


if __name__ == "__main__":
    main()
