"""Cut dead air off the front of a line, and report what it found.

The pipeline already strips leading silence (`trim_silence`, threshold
0.015). This catches what that threshold cannot: audio that is present and
INAUDIBLE - the quiet intake a [gasp] tag renders before the words.

Why it matters is timing, not tone. Rex's "More than HALF?!" carried 0.66s
of inhale in front of a 1.47s file, against a 0.04s median across the other
49 lines. With VO_DELAY on top, his shock take landed almost a second after
the cut to him, which is the difference between a take and a pause. None of
the other probes see it: leading_burst.py looks for a burst-then-gap and
there is no burst, and detect_spelled.py only sees that the line is long
for its syllable count, which a pause explains just as well.

A short pre-breath is performance and is kept. The default keeps 0.12s.
Trimming is done on a zero crossing with a 10ms fade so the cut cannot
click, and the file is only rewritten when there is more than a frame's
worth to remove.

  python scripts/vector/trim_lead.py b            # report only
  python scripts/vector/trim_lead.py b --write
"""
from __future__ import annotations

import re
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
DIRS = {"b": ("fairmarket_bubbles", "Bubbles"),
        "s": ("fairmarket_bshort", "BubblesShort"),
        "1": ("fairmarket", "FairMarketEp1"),
        "2": ("fairmarket_ep2", "FairMarketEp2")}
KEEP = 0.12         # seconds of pre-breath left in front of the first word
LIMIT = 0.25        # anything quieter for longer than this is dead air
FADE = 0.010


def read(p: Path):
    with wave.open(str(p)) as w:
        sr, n = w.getframerate(), w.getnframes()
        return np.frombuffer(w.readframes(n), dtype=np.int16).astype(
            np.float64) / 32768.0, sr


def lead_secs(x: np.ndarray, sr: int) -> float:
    """Time until the first energy worth calling speech."""
    step = max(1, int(sr * 0.01))
    env = np.array([np.sqrt((x[i:i + step] ** 2).mean())
                    for i in range(0, max(1, len(x) - step), step)])
    if not len(env):
        return 0.0
    return float(np.argmax(env > (env.max() or 1.0) * 0.20)) * 0.01


def main() -> None:
    ep = next((a for a in sys.argv[1:] if a in DIRS), "b")
    write = "--write" in sys.argv
    d, comp = DIRS[ep]
    src = (REPO / "remotion/src/compositions" / (comp + ".tsx")).read_text(
        "utf-8", errors="replace")
    stems = re.findall(r'vo: "([a-z_0-9]+)"', src)

    leads, cut = [], []
    for s in stems:
        p = REPO / "remotion/public/audio" / d / (s + ".wav")
        if not p.exists():
            continue
        x, sr = read(p)
        lead = lead_secs(x, sr)
        leads.append(lead)
        if lead <= LIMIT:
            continue
        drop = int((lead - KEEP) * sr)
        y = x[drop:].copy()
        f = int(sr * FADE)
        if f and len(y) > f:
            y[:f] *= np.linspace(0, 1, f)
        cut.append((s, lead, len(x) / sr, len(y) / sr))
        if write:
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr)
                w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())

    print("%s: %d lines, median lead %.3fs" % (comp, len(leads),
                                               float(np.median(leads or [0]))))
    for s, lead, d0, d1 in cut:
        print("  %-22s lead %.2fs  %.2fs -> %.2fs%s"
              % (s, lead, d0, d1, "  WRITTEN" if write else ""))
    if not cut:
        print("  nothing over %.2fs - no dead air to cut" % LIMIT)
    elif not write:
        print("\n  report only; pass --write to apply, then rebuild the mouth "
              "tracks and retime")


if __name__ == "__main__":
    main()
