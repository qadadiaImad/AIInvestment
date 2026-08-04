"""Build a per-frame mouth track for every VO file that lacks one.

The composition drives the viseme swaps off mouth_tracks.json. A line
with no entry there is spoken with a SHUT MOUTH — silently, and without
any error — so this runs over the whole VO folder and fills every gap
rather than being hand-maintained per batch, which is how the 2-minute
cut's eleven new lines would otherwise have shipped mute.

Amplitude thresholds are relative to each line's own loud level, so a
quiet line still articulates instead of sitting closed.

  python scripts/vector/sync_mouth_tracks.py
"""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
VO = REPO / "remotion" / "public" / "audio" / "fairmarket"
FIX = REPO / "remotion" / "src" / "fixtures" / "cast_ep1"
FFMPEG = (REPO / "remotion" / "node_modules" / "@remotion"
          / "compositor-win32-x64-msvc" / "ffmpeg.exe")
FPS = 30


def pcm16(path: Path) -> Path:
    """Some generators emit float32 WAV (Chatterbox) or a placeholder
    header (grok). Decode through ffmpeg to a known-good temp file rather
    than trusting the header — a mis-read header silently produced a
    44,739-second duration on this project before."""
    tmp = path.with_name(f"_{path.stem}_probe.wav")
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(path),
                    "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
                    str(tmp), "-y"], check=True)
    return tmp


def amplitude_track(path: Path) -> tuple[list[int], float]:
    with wave.open(str(path)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    dur = n / sr
    step = max(1, sr // FPS)
    rms = np.array([float(np.sqrt((x[i:i + step] ** 2).mean()))
                    for i in range(0, len(x), step) if len(x[i:i + step])])
    ref = float(np.percentile(rms, 92)) or 1.0
    return [0 if v / ref < 0.16 else (1 if v / ref < 0.5 else 2)
            for v in rms], dur


def main() -> None:
    tracks = json.loads((FIX / "mouth_tracks.json").read_text("utf-8"))
    added = []
    for wav in sorted(VO.glob("*.wav")):
        if wav.stem.startswith("_"):
            continue
        if wav.stem in tracks:
            continue
        tmp = pcm16(wav)
        try:
            track, dur = amplitude_track(tmp)
        finally:
            tmp.unlink(missing_ok=True)
        tracks[wav.stem] = track
        added.append((wav.stem, dur, len(track)))
        print(f"{wav.stem:22s} {dur:5.2f}s  {len(track):4d} track frames")
    (FIX / "mouth_tracks.json").write_text(json.dumps(tracks), "utf-8")
    print(f"\nadded {len(added)}; mouth_tracks.json now has "
          f"{len(tracks)} entries")


if __name__ == "__main__":
    main()
