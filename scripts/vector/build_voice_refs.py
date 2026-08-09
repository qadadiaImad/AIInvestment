"""Build the permanent reference clip for each character.

THE POINT. A local clone's identity comes entirely from its reference
audio. Store that reference in the repo and the voice becomes an asset
you own, not a service that can be re-versioned - which is exactly what
went wrong with grok twice.

WHY LONGER REFERENCES. The first Chatterbox attempt on this project was
conditioned on a single short line and wobbled audibly WITHIN a
sentence, which is why the project moved to grok in the first place. A
zero-shot clone infers speaker identity from whatever it is given; three
seconds of one sentence carries one intonation contour and little of the
speaker's range. Concatenating several clean takes into 12-20 seconds
gives it the whole voice instead of one phrase of it.

SOURCE TAKES are the ones the owner picked by ear from the A/B test -
e3_rex_bullish for Rex, v1_sol_intro for Sol - plus the longest clean
lines from the same character, so the reference is dominated by the
approved timbre.

  python scripts/vector/build_voice_refs.py
"""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
A1 = REPO / "remotion" / "public" / "audio" / "fairmarket"
A2 = REPO / "remotion" / "public" / "audio" / "fairmarket_ep2"
OUT = REPO / "remotion" / "public" / "audio" / "voice_refs"
FFMPEG = (REPO / "remotion" / "node_modules" / "@remotion"
          / "compositor-win32-x64-msvc" / "ffmpeg.exe")

# owner-approved take FIRST, then the longest clean lines from the same
# character. Order matters a little: the model weights early context.
REFS = {
    "rex": [(A2, "e3_rex_bullish"),      # <- owner's pick
            (A1, "a7_rex_oilthing"),
            (A1, "a3_rex_onetrade"),
            (A1, "a2_rex_copy"),
            (A2, "e7_rex_coincidence")],
    "sol": [(A1, "v1_sol_intro"),        # <- owner's pick
            (A1, "v6_sol_exhibit"),
            (A2, "e15_sol_sitwith"),
            (A1, "a3_sol_beating"),
            (A2, "e27_sol_newsfirst")],
}
TARGET_SECONDS = 20.0


def load(p: Path):
    with wave.open(str(p)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64)
    return x / 32768.0, sr


def trim_silence(x: np.ndarray, sr: int, thresh: float = 0.012) -> np.ndarray:
    """Drop leading/trailing silence so the reference is all voice - dead
    air teaches the model nothing and eats the budget."""
    idx = np.nonzero(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    pad = int(sr * 0.05)
    return x[max(0, idx[0] - pad):min(len(x), idx[-1] + pad)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for voice, parts in REFS.items():
        chunks, sr0, total = [], None, 0.0
        for d, stem in parts:
            p = d / (stem + ".wav")
            if not p.exists():
                print("  missing, skipped: " + stem)
                continue
            x, sr = load(p)
            sr0 = sr0 or sr
            if sr != sr0:
                print("  rate mismatch, skipped: " + stem)
                continue
            x = trim_silence(x, sr)
            # normalise each take to the same peak so one loud line does
            # not dominate what the model thinks the voice sounds like
            pk = np.abs(x).max()
            if pk > 0:
                x = x * (0.85 / pk)
            chunks.append(x)
            chunks.append(np.zeros(int(sr * 0.18)))   # a breath between
            total += len(x) / sr
            print("  + %-22s %5.2fs  (running %5.2fs)" % (stem, len(x) / sr, total))
            if total >= TARGET_SECONDS:
                break
        if not chunks:
            print(voice + ": no source takes found")
            continue
        y = np.concatenate(chunks)
        out = OUT / ("voice_ref_" + voice + ".wav")
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr0)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
        print("%s reference: %.1fs @ %d Hz -> %s\n"
              % (voice.upper(), len(y) / sr0, sr0, out.name))


if __name__ == "__main__":
    main()
