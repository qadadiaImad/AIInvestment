"""Prove the stings are actually IN the render, by A/B against a silent cut.

A missing <Audio> renders a perfectly valid file. "It rendered" and "the
audit passed" both only prove the composition SAYS the sound is there -
neither touches the mp4. So this measures it.

The control is the previous cut of the same episode, which has identical
beats and identical VO and no stings at all, so every difference in the
window around a scheduled frame is the sting and nothing else. Comparing
against silence in the same file would not work: these land on or just
after speech, and speech is not silent.

  python scripts/audio/check_stings_landed.py <before.mp4> <after.mp4> <Comp.tsx>

Reads the scheduled frames out of the composition rather than taking them
as arguments, so the check cannot drift from what was actually authored.
"""
from __future__ import annotations

import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
FF = REPO / "remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SR = 48000
FPS = 30
WIN = 0.30          # seconds after the scheduled frame
KIT = {"among_us", "core", "core_tiktok", "faah", "riser_metallic",
       "riser_suspense", "vine_boom", "vine_boom_bass", "whoosh",
       "whoosh_fire"}


def scheduled(tsx: Path):
    """(absolute frame, sound) for every emphasis sting in a composition."""
    src = tsx.read_text("utf-8")
    out = []
    for m in re.finditer(r"\n  \{at: (\d+),", src):
        at = int(m.group(1))
        nxt = re.search(r"\n  \{at: \d+,", src[m.end():])
        span = src[m.start():m.end() + (nxt.start() if nxt else 4000)]
        for e in re.finditer(
                r"\{at: (\d+), name: \"([a-z_0-9]+)\"(?:, vol: ([0-9.]+))?\}", span):
            if e.group(2) in KIT:
                out.append((at + int(e.group(1)), e.group(2)))
    return sorted(out)


def mono(mp4: Path) -> np.ndarray:
    wav = mp4.with_suffix(".probe.wav")
    subprocess.run([str(FF), "-v", "error", "-i", str(mp4), "-vn", "-ac", "1",
                    "-ar", str(SR), str(wav), "-y"], check=True)
    with wave.open(str(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()),
                          dtype=np.int16).astype(np.float64) / 32768.0
    wav.unlink(missing_ok=True)
    return x


def rms(x: np.ndarray, f0: int, secs: float) -> float:
    a = int(f0 / FPS * SR)
    b = a + int(secs * SR)
    seg = x[a:b]
    return float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0


def main() -> None:
    before, after, tsx = (Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    hits = scheduled(tsx)
    a, b = mono(before), mono(after)
    print("%-6s %-16s %8s %8s %7s" % ("frame", "sound", "before", "after", "delta"))
    missed = []
    for f, snd in hits:
        r0, r1 = rms(a, f, WIN), rms(b, f, WIN)
        gain = (r1 / r0) if r0 else float("inf")
        flag = "" if gain > 1.15 else "   <-- NOT AUDIBLE"
        if not flag == "":
            missed.append((f, snd))
        print("%-6d %-16s %8.4f %8.4f %6.2fx%s" % (f, snd, r0, r1, gain, flag))
    print("\n%d/%d stings raised the energy in their own window"
          % (len(hits) - len(missed), len(hits)))
    if missed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
