"""Prove the stings are actually IN the render, by A/B against a silent cut.

A missing <Audio> renders a perfectly valid file. "It rendered" and "the
audit passed" both only prove the composition SAYS the sound is there -
neither touches the mp4. So this measures it.

The control is the previous cut of the same episode, which has identical
beats and identical VO and no stings at all, so every difference in the
window around a scheduled frame is the sting and nothing else. Comparing
against silence in the same file would not work: these land on or just
after speech, and speech is not silent.

  python scripts/audio/check_stings_landed.py \
      <before.mp4> <before.tsx> <after.mp4> <after.tsx>

Reads the scheduled frames out of the compositions rather than taking them
as arguments, so the check cannot drift from what was actually authored -
and takes BOTH compositions, because the two cuts are not frame-aligned.
Re-deriving the beat starts from measured audio moved 39 of ep.3's 50
beats by up to 4 frames, so comparing the same ABSOLUTE frame in each file
compares different moments: the first version of this check reported a
sting whose window had 12x LESS energy after it was added, which is not a
thing a sting can do and was the tell. Beats are matched by VO stem and
each side is measured against its own beat start.
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
# The window is the SOUND'S OWN LENGTH, not a constant. A fixed 0.30s
# window reported riser_metallic and vine_boom_bass as missing from a
# render that contains both: the riser does not get loud until 1.3s in and
# the boom peaks at 1.1s, so 0.30s of it is nearly silence sitting under a
# shouted line. Capped at 2.5s so a long tail does not dilute the delta
# into noise.
WIN_MAX = 2.5
KIT = {"among_us", "core", "core_tiktok", "faah", "riser_metallic",
       "riser_suspense", "vine_boom", "vine_boom_bass", "vine_boom_hit", "whoosh",
       "whoosh_fire"}


def beats(tsx: Path):
    """vo stem -> (beat start frame, [(offset, sound), ...])."""
    src = tsx.read_text("utf-8")
    out = {}
    for m in re.finditer(r"\n  \{at: (\d+),", src):
        at = int(m.group(1))
        nxt = re.search(r"\n  \{at: \d+,", src[m.end():])
        span = src[m.start():m.end() + (nxt.start() if nxt else 4000)]
        vo = re.search(r'vo: "([a-z_0-9]+)"', span)
        if not vo:
            continue
        stings = [(int(e.group(1)), e.group(2)) for e in re.finditer(
            r"\{at: (\d+), name: \"([a-z_0-9]+)\"(?:, vol: ([0-9.]+))?\}", span)
            if e.group(2) in KIT]
        out[vo.group(1)] = (at, stings)
    return out


def mono(mp4: Path) -> np.ndarray:
    wav = mp4.with_suffix(".probe.wav")
    subprocess.run([str(FF), "-v", "error", "-i", str(mp4), "-vn", "-ac", "1",
                    "-ar", str(SR), str(wav), "-y"], check=True)
    with wave.open(str(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()),
                          dtype=np.int16).astype(np.float64) / 32768.0
    wav.unlink(missing_ok=True)
    return x


def sound_secs(name: str) -> float:
    p = REPO / "remotion/public/audio" / (name + ".wav")
    with wave.open(str(p)) as w:
        return min(WIN_MAX, w.getnframes() / w.getframerate())


def rms(x: np.ndarray, f0: int, secs: float) -> float:
    a = int(f0 / FPS * SR)
    b = a + int(secs * SR)
    seg = x[a:b]
    return float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0


def main() -> None:
    bmp4, btsx, amp4, atsx = (Path(sys.argv[1]), Path(sys.argv[2]),
                              Path(sys.argv[3]), Path(sys.argv[4]))
    B, A = beats(btsx), beats(atsx)
    a, b = mono(bmp4), mono(amp4)
    print("%-22s %-16s %8s %8s %8s"
          % ("beat", "sound", "before", "after", "delta"))
    missed = []
    scored = [(s, v) for s, v in A.items() if v[1]]
    for stem, (at_a, stings) in sorted(scored, key=lambda kv: kv[1][0]):
        if stem not in B:
            print("%-22s (not in the control cut, skipped)" % stem)
            continue
        at_b = B[stem][0]
        for off, snd in stings:
            win = sound_secs(snd)
            r0, r1 = rms(a, at_b + off, win), rms(b, at_a + off, win)
            gain = (r1 / r0) if r0 else float("inf")
            # Three states, not two. A quiet riser under speech genuinely
            # lands at around +15% over its own length, and collapsing that
            # into the same verdict as "absent" invites tuning the threshold
            # until the test agrees with you - which is not a test.
            note = ("   <-- ABSENT" if gain <= 1.05
                    else "   (present, quiet by design)" if gain <= 1.15 else "")
            if gain <= 1.05:
                missed.append((stem, snd))
            print("%-22s %-16s %8.4f %8.4f %7.2fx%s"
                  % (stem, snd, r0, r1, gain, note))
    n = sum(len(v[1]) for v in A.values())
    print("\n%d/%d stings raised the energy in their own window" % (n - len(missed), n))
    if missed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
