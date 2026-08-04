"""Confirm every dialogue beat actually carries speech in a render.

A beat whose <Audio> failed to resolve still renders a perfectly valid
file, and a mis-timed beat plays its line over the wrong picture. This
samples the mix in a window just after each beat starts and reports which
ones are voiced, so "the render finished" is never mistaken for "the
dialogue is in it".

Usage:  python scripts/audio/check_beats_voiced.py <render.mp4>
"""
from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
FF = (REPO / "remotion" / "node_modules" / "@remotion" /
      "compositor-win32-x64-msvc" / "ffmpeg.exe")
FPS = 30

# (beat start frame, label) — mirrors BEATS in FairMarketEp1.tsx
BEATS = [
    (0, "v1 sol intro"), (110, "v2 rex fundamentals"), (195, "v3 sol ha"),
    (255, "v4 sol politics"), (345, "v5 rex what"), (400, "v6 sol exhibit"),
    (640, "v7 rex index"), (740, "v8 sol legal"),
    (895, "a2 rex copy"), (995, "a2 sol sixweeks"), (1090, "a2 rex six"),
    (1145, "a2 sol edge"), (1340, "a2 rex useless"), (1410, "a2 sol map"),
    (1565, "v9 rex filings"), (1625, "v10 sol learning"),
]


def main(video: str) -> int:
    wav = Path(video).with_suffix(".probe.wav")
    subprocess.run([str(FF), "-v", "error", "-i", video, "-vn", "-ac", "1",
                    "-ar", "8000", str(wav), "-y"], check=True)
    with wave.open(str(wav)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    print(f"{video}: {n / sr:.2f}s  rms {np.sqrt((x ** 2).mean()):.4f}  "
          f"peak {abs(x).max():.3f}\n")
    bad = 0
    for at, label in BEATS:
        a, b = int((at + 8) / FPS * sr), int((at + 44) / FPS * sr)
        seg = x[a:b]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0
        ok = r > 0.012
        bad += not ok
        print(f"  {label:22s} f{at:<5d} rms {r:.4f}  "
              f"{'voiced' if ok else 'SILENT  <-- check'}")
    wav.unlink(missing_ok=True)
    print(f"\n{len(BEATS) - bad}/{len(BEATS)} beats voiced")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
