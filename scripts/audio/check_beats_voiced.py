"""Confirm every dialogue beat actually carries speech in a render.

A beat whose <Audio> failed to resolve still renders a perfectly valid
file, and a mis-timed beat plays its line over the wrong picture. This
samples the mix in a window just after each beat starts and reports which
ones are voiced, so "the render finished" is never mistaken for "the
dialogue is in it".

Usage:  python scripts/audio/check_beats_voiced.py <render.mp4>
"""
from __future__ import annotations

import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
FF = (REPO / "remotion" / "node_modules" / "@remotion" /
      "compositor-win32-x64-msvc" / "ffmpeg.exe")
COMP = REPO / "remotion" / "src" / "compositions" / "FairMarketEp1.tsx"
FPS = 30


def beats_from_composition() -> list[tuple[int, str]]:
    """Read the beat list OUT OF THE COMPOSITION rather than mirroring it
    here.

    This used to be a hand-copied literal — the same second-source-of-
    truth trap that left overlap_audit.py checking a set geometry two
    revisions old. A stale list here is worse than useless: it cheerfully
    reports "16/16 voiced" while sampling frames the episode no longer
    has.
    """
    src = COMP.read_text("utf-8")
    # NB: the first "[" after the declaration is the one in `Beat[]`, not
    # the array. Anchor on the assignment.
    i = src.index("= [", src.index("const BEATS: Beat[] = [")) + 2
    depth, body = 0, ""
    for j in range(i, len(src)):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                body = src[i + 1:j]
                break
    body = re.sub(r"//.*", "", body)          # comments carry stray brackets
    out: list[tuple[int, str]] = []
    depth, cur = 0, ""
    for ch in body:
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        cur += ch
        if depth == 0 and ch == "}":
            at = re.search(r"\bat:\s*(\d+)", cur)
            vo = re.search(r'\bvo:\s*"([a-z0-9_]+)"', cur)
            vo2 = re.search(r'\bvo2:\s*"([a-z0-9_]+)"', cur)
            at2 = re.search(r"\bat2:\s*(\d+)", cur)
            if at and vo:
                out.append((int(at.group(1)), vo.group(1)))
            if at and vo2:
                out.append((int(at.group(1)) + (int(at2.group(1)) if at2 else 0),
                            vo2.group(1)))
            cur = ""
    if len(out) < 5:
        raise SystemExit(f"parsed only {len(out)} voiced beats — the parser "
                         f"is broken, not the render. A green tick over "
                         f"nothing is the failure this tool exists to catch.")
    return sorted(out)


def main(video: str) -> int:
    beats = beats_from_composition()
    wav = Path(video).with_suffix(".probe.wav")
    subprocess.run([str(FF), "-v", "error", "-i", video, "-vn", "-ac", "1",
                    "-ar", "8000", str(wav), "-y"], check=True)
    with wave.open(str(wav)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    print(f"{video}: {n / sr:.2f}s  rms {np.sqrt((x ** 2).mean()):.4f}  "
          f"peak {abs(x).max():.3f}\n")
    bad = 0
    for at, label in beats:
        a, b = int((at + 8) / FPS * sr), int((at + 44) / FPS * sr)
        seg = x[a:b]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0
        ok = r > 0.012
        bad += not ok
        print(f"  {label:22s} f{at:<5d} rms {r:.4f}  "
              f"{'voiced' if ok else 'SILENT  <-- check'}")
    wav.unlink(missing_ok=True)
    print(f"\n{len(beats) - bad}/{len(beats)} beats voiced")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
