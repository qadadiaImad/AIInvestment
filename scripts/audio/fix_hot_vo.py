"""Pull back VO lines that were mastered too hot, without re-recording them.

The owner heard "a weird sound" at 1:18 of ep.2, on "So they caught them. /
No!". Measured rather than guessed: `e14_sol_nope.wav` - the single word
"No." - peaks at 32767, the absolute digital ceiling, carries 20 hard-
clipped samples, and its loudest 200 ms is 1.40x the episode median while
being the shortest line in the show. A short word slammed into the ceiling
directly after a quiet one is exactly what reads as an artifact.

The cause is peak normalisation applied per file. Normalising a 0.58 s word
and a 7.65 s sentence to the same PEAK leaves the word far louder to the
ear, because loudness is about sustained energy, not the single tallest
sample.

So this rebalances by MEASURED LOUDNESS instead: the loudest 200 ms window
of each file is compared against the episode median and the gain is trimmed
to bring outliers into line. The performance is untouched - same take, same
timing, same delivery, just not shouting. Originals are copied to
`_hot_originals/` first; nothing is destroyed.

A short fade in and out is applied at the same time, because a clipped file
that starts at full amplitude on sample zero can click.

  python scripts/audio/fix_hot_vo.py [ep2|ep1] [--check]
"""
from __future__ import annotations

import math
import shutil
import statistics
import struct
import sys
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIRS = {
    "ep1": REPO / "remotion/public/audio/fairmarket",
    "ep2": REPO / "remotion/public/audio/fairmarket_ep2",
}

# Deliberately surgical. The read is owner-approved, and speech is SUPPOSED
# to vary - most of the spread here is emphasis, not error. Only two things
# count as broken: a file that actually clips, or one so far above the
# median that it jumps out of the mix (1.38x is about +2.8 dB). Everything
# else is left exactly as recorded. A treated file is pulled to the median
# rather than to some ceiling, because the lines that trip this are short
# ones that should sit level with the read, not tower over it.
TREAT_ABOVE = 1.38
CLIP_SAMPLES = 10
FADE_S = 0.006


def read(p: Path):
    with wave.open(str(p), "rb") as w:
        params = w.getparams()
        raw = w.readframes(w.getnframes())
    return params, list(struct.unpack("<%dh" % (len(raw) // 2), raw))


def loud200(d, sr, ch):
    win = max(1, int(sr * 0.2) * ch)
    best = 0.0
    for i in range(0, max(1, len(d) - win), max(1, win // 2)):
        seg = d[i:i + win]
        best = max(best, math.sqrt(sum(x * x for x in seg) / len(seg)))
    return best or 1.0


def main() -> None:
    ep = next((a for a in sys.argv[1:] if a in DIRS), "ep2")
    check = "--check" in sys.argv
    src = DIRS[ep]
    backup = src / "_hot_originals"

    files = sorted(p for p in src.glob("*.wav") if p.parent == src)
    stats = {}
    for p in files:
        params, d = read(p)
        stats[p] = (params, d, loud200(d, params.framerate, params.nchannels))

    med = statistics.median(s[2] for s in stats.values())
    limit = med * TREAT_ABOVE
    print("%s: %d files, median loud200ms=%.0f, treat above %.0f or on clipping"
          % (ep, len(files), med, limit))

    fixed = 0
    for p, (params, d, loud) in sorted(stats.items(), key=lambda kv: -kv[1][2]):
        peak = max(abs(x) for x in d) or 1
        clipped = sum(1 for x in d if abs(x) >= 32700)
        if loud <= limit and clipped < CLIP_SAMPLES:
            continue
        gain = min(med / loud, 32000 / peak)
        print("  %-24s loud=%.0f (%.2fx med) peak=%d clipped=%d -> gain %.3f"
              % (p.stem, loud, loud / med, peak, clipped, gain))
        if check:
            continue
        backup.mkdir(exist_ok=True)
        if not (backup / p.name).exists():
            shutil.copy2(p, backup / p.name)
        sr, ch = params.framerate, params.nchannels
        fade = max(1, int(sr * FADE_S)) * ch
        out = []
        n = len(d)
        for i, x in enumerate(d):
            g = gain
            if i < fade:
                g *= i / fade
            elif i > n - fade:
                g *= max(0.0, (n - i) / fade)
            out.append(max(-32768, min(32767, int(round(x * g)))))
        with wave.open(str(p), "wb") as w:
            w.setparams(params)
            w.writeframes(struct.pack("<%dh" % len(out), *out))
        fixed += 1

    print("check only" if check else "rebalanced %d file(s); originals in %s"
          % (fixed, backup.name))


if __name__ == "__main__":
    main()
