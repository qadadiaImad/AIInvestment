"""Lay the desk bed under a finished episode master. No re-render.

WHY THIS EXISTS. The bed is a separate stem, so it does NOT have to be
baked in at render time. Muxing it onto the finished h264 master copies the
video stream untouched and only re-encodes audio - seconds instead of the
ten minutes an episode takes to render. That means the music can be
auditioned, relevelled or dropped entirely without ever re-rendering, and
the picture is bit-identical across every version.

Level, measured on ep.2 rather than guessed: the bed alone sits at
-29.5 dBFS and the VO mix at about -23.9. At volume 0.55 the bed adds
+2.5 dB in the act gaps (where nobody is speaking, which is the whole
point) and +1.0 dB overall - present in the air, never over the dialogue.
An earlier pass at 0.30 measured +0.2 dB and was simply inaudible.

  python scripts/audio/mux_bed.py 1 2 3 4 5
  python scripts/audio/mux_bed.py 3 --vol 0.45

Reads   content/probe/ep<N>_panel.mp4
Writes  content/probe/ep<N>_panel_music.mp4
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

FFMPEG = next((p for p in (r"C:\ffmpeg\bin\ffmpeg.exe", "/c/ffmpeg/bin/ffmpeg",
                           "ffmpeg") if os.path.exists(p) or p == "ffmpeg"), "ffmpeg")


def mean_db(path, ss=None, t=None):
    cmd = [FFMPEG, "-hide_banner"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    if t is not None:
        cmd += ["-t", str(t)]
    cmd += ["-i", path, "-vn", "-af", "volumedetect", "-f", "null", os.devnull]
    r = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"mean_volume: ([-\d.]+)", r.stderr)
    return float(m.group(1)) if m else None


def mux(ep: str, vol: float) -> None:
    master = os.path.join(REPO, "content", "probe", f"ep{ep}_panel.mp4")
    bed = os.path.join(REPO, "remotion", "public", "audio", f"bed_ep{ep}.wav")
    out = os.path.join(REPO, "content", "probe", f"ep{ep}_panel_music.mp4")
    for p in (master, bed):
        if not os.path.exists(p):
            print(f"ep{ep}: MISSING {os.path.relpath(p, REPO)}")
            return

    before = mean_db(master)
    subprocess.run([
        FFMPEG, "-v", "error", "-i", master, "-i", bed,
        "-filter_complex",
        f"[1:a]volume={vol},aformat=channel_layouts=stereo[b];"
        "[0:a][b]amix=inputs=2:duration=first:normalize=0[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", out, "-y",
    ], check=True)
    after = mean_db(out)
    print(f"ep{ep}: vol {vol} · {before:+.1f} -> {after:+.1f} dB "
          f"({after - before:+.1f}) · {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("eps", nargs="+")
    ap.add_argument("--vol", type=float, default=0.55)
    a = ap.parse_args()
    for e in a.eps:
        mux(e, a.vol)
